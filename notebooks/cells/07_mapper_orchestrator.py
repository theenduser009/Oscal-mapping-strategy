# %% Cell 7 - OSCAL mapper orchestrator

import json

# PREVIEW validates and reports changes without target DML.
# COMMIT explicitly enables this run's guarded SSP DEV upserts only.
# Keep Cell 1 CONFIG["EXECUTE_WRITES"] = False; do not run a separate reload.
SSP_LOAD_MODE = "PREVIEW"


def _oscal_run_config(config, load_mode):
    if load_mode not in ("PREVIEW", "COMMIT"):
        raise ValueError("SSP_LOAD_MODE must be PREVIEW or COMMIT")
    if config.get("EXECUTE_WRITES") is not False:
        raise ValueError("Keep the shared CONFIG EXECUTE_WRITES false; select the Cell 7 load mode")
    if load_mode == "COMMIT" and config.get("OSCAL_MODEL") != "SSP":
        raise ValueError("Cell 7 COMMIT is enabled only for the reviewed SSP DEV contract")
    if getattr(globals().get("validate_and_load_oscal"), "_oscal_loader_release", None) != "ssp-daily-upsert-v1":
        raise ValueError("Run the matching updated Cell 6 before this Cell 7")
    run_config = dict(config)
    run_config["EXECUTE_WRITES"] = load_mode == "COMMIT"
    return run_config


def _oscal_source_count(source_df):
    if "SOURCE_RECORD_ID" not in source_df.columns:
        raise ValueError("Source input must expose SOURCE_RECORD_ID")
    if source_df.filter("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0").count():
        raise ValueError("Source input has missing record identities; no write attempted")
    count = source_df.count()
    if count == 0:
        raise ValueError("Empty source input is not authorization to change SSP targets")
    return count


def run_oscal_mapping(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    config,
    load_mode="PREVIEW",
):
    # Validate intent before constructing data or consulting target tables.
    run_config = _oscal_run_config(config, load_mode)
    run_config["EXPECTED_SOURCE_RECORDS"] = _oscal_source_count(source_df)
    print("=" * 70)
    print("OSCAL MAPPING RUN")
    print("Model:", config["OSCAL_MODEL"])
    print("Run ID:", config["RUN_ID"])
    print("Load mode:", load_mode)
    print("=" * 70)

    nodes_df, edges_df = build_oscal_graph(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"],
        source_table=config["SOURCE_TABLE_NAME"],
    )

    # A coverage error must occur before any target write, never after COMMIT.
    coverage_df = None
    if config.get("BUILD_COVERAGE_REPORT", False):
        coverage_df = build_mapping_coverage(
            source_df,
            CANONICAL_MAPPING_ROWS,
        )

    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df,
        canonical_edges_df=edges_df,
        config=run_config,
    )

    print("OSCAL MAPPING RUN COMPLETE")
    print("Nodes:", result["nodes"])
    print("Edges:", result["edges"])
    print("Writes:", result["writes_executed"])
    print("Load status:", result.get("status", "VALIDATED"))
    print("OSCAL_LOAD_REPORT")
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return nodes_df, edges_df, coverage_df, result


# Invalidate outputs before executing. A failed run must not leave an old
# accepted run_result or old graph exposed as the result of this attempt.
final_nodes_df = final_edges_df = mapping_coverage_df = run_result = None
final_nodes_df, final_edges_df, mapping_coverage_df, run_result = (
    run_oscal_mapping(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        config=CONFIG,
        load_mode=SSP_LOAD_MODE,
    )
)
