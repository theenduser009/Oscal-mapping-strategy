# Read-only SSP scope and mapping-coverage validation
#
# Copy this file into a temporary Snowflake Python cell and run it only after
# Mapper V1 Cell 7 completes.  This is a diagnostic checkpoint, not Cell 8 of
# the production notebook.  It creates no permanent objects and performs no
# DIM or FACT writes.

from snowflake.snowpark.functions import col, lit


if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running scope validation."
    )

required_objects = {
    "final_nodes_df": final_nodes_df,
    "final_edges_df": final_edges_df,
    "mapping_coverage_df": mapping_coverage_df,
    "run_result": run_result,
}

missing_objects = [
    name for name, value in required_objects.items() if value is None
]
if missing_objects:
    raise RuntimeError(
        "Run Mapper V1 Cells 1 through 7 first. Missing: "
        + ", ".join(missing_objects)
    )


# -------------------------------------------------------------------------
# 1. Core graph reconciliation
# -------------------------------------------------------------------------

node_count = final_nodes_df.count()
edge_count = final_edges_df.count()
source_record_count = (
    final_nodes_df.select("SOURCE_RECORD_ID").distinct().count()
)

root_nodes_df = final_nodes_df.filter(
    col("ELEMENT_PATH") == lit("system-security-plan")
)
root_count = root_nodes_df.count()
root_source_count = (
    root_nodes_df.select("SOURCE_RECORD_ID").distinct().count()
)
bad_root_source_count = (
    root_nodes_df.group_by("SOURCE_RECORD_ID")
    .count()
    .filter(col("COUNT") != lit(1))
    .count()
)

# A connected tree for every source record has one fewer edge than nodes.
expected_tree_edge_count = node_count - source_record_count

core_checks = {
    "Cell 7 graph validation passed": bool(
        run_result.get("validation_passed", False)
    ),
    "Cell 7 pre-write validation passed": bool(
        run_result.get("pre_write_validation_passed", False)
    ),
    "Writes were not executed": not bool(
        run_result.get("writes_executed", True)
    ),
    "Graph contains nodes": node_count > 0,
    "Graph contains source records": source_record_count > 0,
    "Exactly one SSP root per source record": (
        root_count == source_record_count
        and root_source_count == source_record_count
        and bad_root_source_count == 0
    ),
    "Tree edge count reconciles": edge_count == expected_tree_edge_count,
}

print("=" * 72)
print("SSP READ-ONLY SCOPE VALIDATION")
print("=" * 72)
print("Nodes:", node_count)
print("Edges:", edge_count)
print("Source records:", source_record_count)
print("SSP roots:", root_count)
print("Expected tree edges:", expected_tree_edge_count)

for check_name, passed in core_checks.items():
    print(("PASS" if passed else "FAIL") + " - " + check_name)

failed_core_checks = [
    name for name, passed in core_checks.items() if not passed
]
if failed_core_checks:
    raise ValueError(
        "SSP scope validation failed: "
        + "; ".join(failed_core_checks)
    )


# -------------------------------------------------------------------------
# 2. Registry-to-mapping ownership scope
# -------------------------------------------------------------------------

registered_paths = sorted(set(active_registry_paths))
mapped_owner_paths = sorted(set(MAPPINGS_BY_ELEMENT_PATH))
unmapped_registry_paths = sorted(
    set(registered_paths) - set(mapped_owner_paths)
)

print("\n=== REGISTRY AND MAPPING SCOPE ===")
print("Active registry paths:", len(registered_paths))
print("Mapped registry owner paths:", len(mapped_owner_paths))
print("Structural paths without owned field mappings:", len(unmapped_registry_paths))

if unmapped_registry_paths:
    print("\nStructural/unmapped registry paths (review, not automatic failure):")
    for path in unmapped_registry_paths:
        print(" -", path)


# -------------------------------------------------------------------------
# 3. Generated element/path populations and payload presence
# -------------------------------------------------------------------------

print("\n=== GENERATED NODE COUNTS BY ELEMENT TYPE ===")
(
    final_nodes_df.group_by("ELEMENT_TYPE")
    .count()
    .sort(col("ELEMENT_TYPE"))
    .show(100, 250)
)

print("\n=== GENERATED NODE COUNTS BY REGISTRY PATH ===")
(
    final_nodes_df.group_by("ELEMENT_PATH")
    .count()
    .sort(col("ELEMENT_PATH"))
    .show(100, 250)
)

empty_payload_count = final_nodes_df.filter(
    col("METADATA_JSON") == lit("{}")
).count()
nonempty_payload_count = node_count - empty_payload_count

print("\n=== PAYLOAD PRESENCE ===")
print("Non-empty payload nodes:", nonempty_payload_count)
print("Structural/empty payload nodes:", empty_payload_count)
(
    final_nodes_df.with_column(
        "IS_EMPTY_PAYLOAD",
        col("METADATA_JSON") == lit("{}"),
    )
    .group_by("ELEMENT_TYPE", "IS_EMPTY_PAYLOAD")
    .count()
    .sort(col("ELEMENT_TYPE"), col("IS_EMPTY_PAYLOAD"))
    .show(200, 250)
)


# -------------------------------------------------------------------------
# 4. Field-level mapping coverage already computed by Cell 7
# -------------------------------------------------------------------------

coverage_row_count = mapping_coverage_df.count()
coverage_with_data_count = mapping_coverage_df.filter(
    col("HAS_SOURCE_DATA") == lit(True)
).count()
coverage_without_data_count = mapping_coverage_df.filter(
    col("HAS_SOURCE_DATA") == lit(False)
).count()
coverage_percent = (
    round(100.0 * coverage_with_data_count / coverage_row_count, 2)
    if coverage_row_count
    else 0.0
)

print("\n=== FIELD-LEVEL MAPPING COVERAGE ===")
print("Canonical mapping rows:", coverage_row_count)
print("Mappings with source data:", coverage_with_data_count)
print("Mappings without source data:", coverage_without_data_count)
print("Mappings with source data percent:", coverage_percent)

if coverage_row_count == 0:
    raise ValueError(
        "Mapping coverage is empty; do not proceed toward writes."
    )

print("\n=== COVERAGE SUMMARY BY TYPE / STATUS / DATA ===")
(
    mapping_coverage_df.group_by(
        "MAPPING_TYPE",
        "STATUS",
        "HAS_SOURCE_DATA",
    )
    .count()
    .sort(
        col("MAPPING_TYPE"),
        col("STATUS"),
        col("HAS_SOURCE_DATA"),
    )
    .show(200, 250)
)

print("\n=== MAPPINGS WITHOUT SOURCE DATA ===")
(
    mapping_coverage_df.filter(
        col("HAS_SOURCE_DATA") == lit(False)
    )
    .select(
        "ARCHER_FIELD",
        "OSCAL_ELEMENT",
        "MAPPING_TYPE",
        "STATUS",
    )
    .sort(col("OSCAL_ELEMENT"), col("ARCHER_FIELD"))
    .show(500, 250)
)

print("\nSSP READ-ONLY SCOPE VALIDATION PASSED")
print("Review the displayed element/path and coverage tables before writes.")

