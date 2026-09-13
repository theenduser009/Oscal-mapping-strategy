# %% Cell 7 - Run the mapping
OSCAL_LOAD_MODE = "PREVIEW"  # Change to COMMIT only for a verified destination.


class PipelineError(ValueError):
    def __init__(self, report):
        super().__init__("OSCAL pipeline stopped; inspect OSCAL_PIPELINE_REPORT")
        self.report = report


def run_oscal_mapping(source_df, canonical_mapping_df, element_registry_df, config, context=None):
    """Build the graph, validate it, and load only when this run enables writes."""
    nodes, edges = build_oscal_graph(
        source_df, canonical_mapping_df, element_registry_df, config["OSCAL_MODEL"],
        config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"], context=context,
    )
    config = dict(config)
    if "EXPECTED_SOURCE_RECORDS" not in config:
        config["EXPECTED_SOURCE_RECORDS"] = source_df.count()
    result = validate_and_load_oscal(nodes, edges, config)
    return nodes, edges, result


def run_oscal_pipeline(source_inputs, mapping_contexts, load_mode="PREVIEW"):
    """Preview every route before the first commit. Transactions are per route."""
    report = {"mode": load_mode, "status": "RUNNING", "groups": [],
              "writes_executed": False, "commit_attempted": False}
    graphs, active = {}, None
    try:
        if load_mode not in {"PREVIEW", "COMMIT"} or not mapping_contexts:
            raise ValueError("Choose PREVIEW or COMMIT and at least one mapping route")
        if getattr(validate_and_load_oscal, "_oscal_loader_release", None) != "oscal-lean-daily-v3":
            raise ValueError("Run the matching Cell 6 before Cell 7")
        routes = {}
        for context in mapping_contexts:
            config = context["config"]
            active = (context["source_key"], config["OSCAL_MODEL"])
            if active in routes or active[0] not in source_inputs:
                raise ValueError("Duplicate mapping route or missing source input")
            if context["routing_report"]["STATUS"] != "READY" or not context["mapping_rows"]:
                raise ValueError("Mapping route is blocked or has no approved rows")
            if config.get("EXECUTE_WRITES") is not False:
                raise ValueError("Keep shared EXECUTE_WRITES false; choose the Cell 7 load mode")
            if load_mode == "COMMIT" and (config.get("STORAGE_CONTRACT") or {}).get("VERIFIED") is not True:
                raise ValueError("Every selected route needs a verified destination before COMMIT")
            routes[active] = context
        for active, original in routes.items():
            context = copy.deepcopy(original)
            source = source_inputs[active[0]]
            context["lookups"] = source.get("lookups", {})
            expected = source.get("selection", {}).get("SELECTED_ROWS")
            if expected is not None:
                context["config"]["EXPECTED_SOURCE_RECORDS"] = expected
            nodes, edges, result = run_oscal_mapping(source["source_df"], None, None, context["config"], context)
            graphs[active] = {"nodes": nodes, "edges": edges, "context": context}
            report["groups"].append({"source": active[0], "model": active[1], "load": result})
        if load_mode == "COMMIT":
            for group in report["groups"]:
                active = (group["source"], group["model"])
                graph = graphs[active]
                report["commit_attempted"] = True
                result = validate_and_load_oscal(graph["nodes"], graph["edges"],
                                                dict(graph["context"]["config"], EXECUTE_WRITES=True))
                group["load"] = result
                report["writes_executed"] |= result["writes_executed"]
        report["status"] = "COMMITTED_AND_VERIFIED" if load_mode == "COMMIT" else "PREVIEW_COMPLETE"
        return graphs, report
    except BaseException as error:
        details = getattr(error, "details", {})
        report.update(status="COMMIT_FAILED_REVIEW_REQUIRED" if report["commit_attempted"] else "FAILED_BEFORE_COMMIT",
                      failed_route=active, error_type=type(error).__name__, load_error=details)
        report["writes_executed"] |= details.get("writes_executed") is True
        raise PipelineError(report) from None


MODEL_GRAPHS = PIPELINE_REPORT = None
try:
    MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(SOURCE_INPUTS, MAPPING_CONTEXTS, OSCAL_LOAD_MODE)
except PipelineError as error:
    PIPELINE_REPORT = error.report
    raise
finally:
    print("OSCAL_PIPELINE_REPORT")
    print(json.dumps(PIPELINE_REPORT, indent=2, default=str))
