# %% Cell 7 - OSCAL mapper orchestrator

import copy
import json

# One runner for all configured source/model routes. No daily truncate.
# Keep Cell 1 EXECUTE_WRITES=False. COMMIT needs every selected storage contract
# verified; the shipped AR route has no verified destination, so use PREVIEW.
OSCAL_LOAD_MODE = "PREVIEW"


class PipelineError(ValueError):
    def __init__(self, message, report):
        super().__init__(message)
        self.report = report
        self.details = report


def _oscal_run_config(config, load_mode):
    if load_mode not in ("PREVIEW", "COMMIT"):
        raise ValueError("OSCAL_LOAD_MODE must be PREVIEW or COMMIT")
    if config.get("EXECUTE_WRITES") is not False:
        raise ValueError("Keep the shared CONFIG EXECUTE_WRITES false; select the Cell 7 load mode")
    if getattr(globals().get("validate_and_load_oscal"), "_oscal_loader_release", None) != "oscal-shared-daily-upsert-v2":
        raise ValueError("Run the matching updated Cell 6 before this Cell 7")
    if load_mode == "COMMIT" and (config.get("STORAGE_CONTRACT") or {}).get("VERIFIED") is not True:
        raise ValueError("Every selected source/model route needs a verified storage contract before COMMIT")
    return {**config, "EXECUTE_WRITES": load_mode == "COMMIT"}


def _oscal_source_count(source_df):
    if "SOURCE_RECORD_ID" not in source_df.columns:
        raise ValueError("Source input must expose SOURCE_RECORD_ID")
    if source_df.filter("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0").count():
        raise ValueError("Source input has missing record identities; no write attempted")
    count = source_df.count()
    if count == 0:
        raise ValueError("Empty source input is not authorization to change targets")
    return count


def run_oscal_mapping(
    source_df, canonical_mapping_df, element_registry_df, config,
    load_mode="PREVIEW", context=None,
):
    run_config = _oscal_run_config(config, load_mode)
    run_config["EXPECTED_SOURCE_RECORDS"] = _oscal_source_count(source_df)
    nodes_df, edges_df = build_oscal_graph(
        source_df=source_df, canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df, model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"], source_table=config["SOURCE_TABLE_NAME"],
        context=context,
    )
    coverage_df = None
    if config.get("BUILD_COVERAGE_REPORT", False):
        mapping_rows = context["mapping_rows"] if context is not None else CANONICAL_MAPPING_ROWS
        coverage_df = build_mapping_coverage(source_df, mapping_rows)
    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df, canonical_edges_df=edges_df, config=run_config,
    )
    return nodes_df, edges_df, coverage_df, result


def run_oscal_pipeline(source_inputs, mapping_contexts, load_mode="PREVIEW"):
    """Validate every selected route before commits; never swap model globals.

    Commits are per source/model transaction, not one distributed transaction.
    A later commit failure reports prior committed groups and stops; no retry.
    """
    report = {"status": "NOT_RUN", "mode": load_mode, "writes_executed": False,
              "commit_attempted": False, "groups": []}
    graphs, routes = {}, {}
    context = None
    phase = "routing"
    try:
        if not mapping_contexts:
            raise ValueError("No configured mapping routes")
        for original in mapping_contexts:
            key = (original["source_key"], original["config"]["OSCAL_MODEL"])
            report["active_group"] = {"source": key[0], "model": key[1]}
            report["active_routing"] = copy.deepcopy(original["routing_report"])
            if key in routes:
                raise ValueError("Duplicate source/model route")
            routes[key] = original
            if key[0] not in source_inputs:
                raise ValueError("Missing selected source input")
            if original["routing_report"].get("STATUS") != "READY":
                raise ValueError("Mapping routing has blocked rows")
            if not original["mapping_rows"]:
                raise ValueError("Selected route has no approved mappings")
            _oscal_run_config(original["config"], load_mode)
        # Build and validate every candidate before the first target commit.
        phase = "preview"
        for key, original in routes.items():
            context = copy.deepcopy(original)
            report["active_group"] = {"source": key[0], "model": key[1]}
            context["lookups"] = dict(source_inputs[key[0]].get("lookups", {}))
            nodes, edges, coverage, result = run_oscal_mapping(
                source_inputs[key[0]]["source_df"], None, None, context["config"],
                load_mode="PREVIEW", context=context,
            )
            if result.get("validation_passed") is not True:
                raise ValueError("Candidate graph validation did not pass")
            if result.get("writes_executed") is not False:
                raise ValueError("Preview reported an unexpected target write")
            context["config"]["EXPECTED_SOURCE_RECORDS"] = result.get(
                "source_records", context.get("graph_report", {}).get("SOURCE_RECORDS")
            )
            graphs[key] = {"nodes": nodes, "edges": edges, "coverage": coverage, "context": context}
            report["groups"].append({
                "source": key[0], "model": key[1], "status": result.get("status", "VALIDATED"),
                "routing": copy.deepcopy(context["routing_report"]),
                "graph": copy.deepcopy(context.get("graph_report", {})), "load": result,
            })
        if load_mode == "COMMIT":
            phase = "commit"
            for group in report["groups"]:
                report["active_group"] = {"source": group["source"], "model": group["model"]}
                graph = graphs[(group["source"], group["model"])]
                context = graph["context"]
                cfg = _oscal_run_config(context["config"], "COMMIT")
                report["commit_attempted"] = True
                result = validate_and_load_oscal(
                    canonical_nodes_df=graph["nodes"], canonical_edges_df=graph["edges"], config=cfg,
                )
                group.update(status=result.get("status", "UNKNOWN"), load=result)
                report["writes_executed"] = report["writes_executed"] or result.get("writes_executed", False)
                if (result.get("writes_executed") is not True or result.get("persisted") is not True
                        or not str(result.get("status", "")).endswith("_COMMITTED_AND_VERIFIED")
                        or not isinstance(result.get("verification"), dict)):
                    raise ValueError("Commit requires confirmed persistence and read-back verification")
            report["status"] = "ALL_SELECTED_GROUPS_COMMITTED_AND_VERIFIED"
        else:
            pending = any(group["load"].get("storage_verified") is False for group in report["groups"])
            report["status"] = ("PREVIEW_WITH_TARGET_CONTRACTS_PENDING" if pending
                                else "ALL_SELECTED_GROUPS_PREVIEW_VERIFIED")
        report.pop("active_group", None)
        report.pop("active_routing", None)
        return graphs, report
    except BaseException as exc:
        report["status"] = ("PIPELINE_COMMIT_FAILED_REVIEW_REQUIRED" if report["commit_attempted"]
                            else "PIPELINE_FAILED_NO_TARGET_DML")
        report["failed_phase"] = phase
        report["error_type"] = type(exc).__name__
        if phase == "routing":
            report["error_reason"] = str(exc)
        elif context is not None:
            report["active_routing"] = copy.deepcopy(context["routing_report"])
        if context is not None and "graph_report" in context:
            report["active_graph_report"] = copy.deepcopy(context["graph_report"])
        # Loader reports carry only approved diagnostics; never print source payloads.
        load_report = getattr(exc, "report", getattr(exc, "details", None))
        if isinstance(load_report, dict):
            report["failed_load_report"] = load_report
            report["writes_executed"] = report["writes_executed"] or load_report.get("writes_executed") is True
        if report["commit_attempted"]:
            report["failed_commit_outcome"] = "REVIEW_REQUIRED_NO_AUTOMATIC_RETRY"
        raise PipelineError("OSCAL pipeline stopped; inspect OSCAL_PIPELINE_REPORT", report) from None


# Clear old outputs first. A failed run must not expose the previous graph as new.
MODEL_GRAPHS = PIPELINE_REPORT = None
final_nodes_df = final_edges_df = mapping_coverage_df = run_result = None
try:
    MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(
        SOURCE_INPUTS, MAPPING_CONTEXTS, load_mode=OSCAL_LOAD_MODE,
    )
except PipelineError as error:
    PIPELINE_REPORT = error.report
    raise
finally:
    print("OSCAL_PIPELINE_REPORT")
    print(json.dumps(PIPELINE_REPORT, indent=2, sort_keys=True, default=str))
# Compatibility outputs refer only to the explicitly configured default group.
_default_key = (SOURCE_PROFILES[0]["SOURCE_KEY"], CONFIG["OSCAL_MODEL"])
if _default_key in MODEL_GRAPHS:
    _graph = MODEL_GRAPHS[_default_key]
    final_nodes_df, final_edges_df = _graph["nodes"], _graph["edges"]
    mapping_coverage_df = _graph["coverage"]
    run_result = next(group["load"] for group in PIPELINE_REPORT["groups"]
                      if (group["source"], group["model"]) == _default_key)
