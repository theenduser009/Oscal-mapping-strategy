# %% Cell 7 - OSCAL mapper orchestrator

def run_oscal_mapping(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    config,
):
    print("=" * 70)
    print("OSCAL MAPPING RUN")
    print("Model:", config["OSCAL_MODEL"])
    print("Run ID:", config["RUN_ID"])
    print("=" * 70)

    nodes_df, edges_df = build_oscal_graph(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"],
        source_table=config["SOURCE_TABLE_NAME"],
    )

    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df,
        canonical_edges_df=edges_df,
        config=config,
    )

    coverage_df = None
    if config.get("BUILD_COVERAGE_REPORT", False):
        coverage_df = build_mapping_coverage(
            source_df,
            CANONICAL_MAPPING_ROWS,
        )

    print("OSCAL MAPPING RUN COMPLETE")
    print("Nodes:", result["nodes"])
    print("Edges:", result["edges"])
    print("Writes:", result["writes_executed"])
    return nodes_df, edges_df, coverage_df, result


final_nodes_df, final_edges_df, mapping_coverage_df, run_result = (
    run_oscal_mapping(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        config=CONFIG,
    )
)
