# RUN NOW — Diagnose Source One SSP PREVIEW failure
# Date: 2026-09-24
# READ ONLY. No registry, DIM, FACT, mapping, or source DML.
#
# The 2026-09-24 fresh SSP PREVIEW stopped with:
#   status = FAILED_BEFORE_COMMIT
#   writes_executed = false
#   commit_attempted = false
#   failed_route = ("source-one", "SSP")
#   error_type = ValueError
#
# Cell 7 intentionally hides the underlying ValueError message inside PipelineError.
# This helper reruns only the graph-build stage and prints the original exception.
# It does NOT call validate_and_load_oscal and therefore cannot write targets.

import copy
import traceback

ROUTE = ("source-one", "SSP")

print("SOURCE_ONE_SSP_PREVIEW_FAILURE_DIAGNOSTIC")
print("PIPELINE_STATUS =", (PIPELINE_REPORT or {}).get("status") if isinstance(PIPELINE_REPORT, dict) else None)
print("WRITES_EXECUTED =", (PIPELINE_REPORT or {}).get("writes_executed") if isinstance(PIPELINE_REPORT, dict) else None)
print("COMMIT_ATTEMPTED =", (PIPELINE_REPORT or {}).get("commit_attempted") if isinstance(PIPELINE_REPORT, dict) else None)

contexts = [
    c for c in MAPPING_CONTEXTS
    if (c["source_key"], c["config"]["OSCAL_MODEL"]) == ROUTE
]

print("MATCHING_CONTEXTS =", len(contexts))
if len(contexts) != 1:
    raise ValueError("Expected exactly one source-one / SSP mapping context")

context = copy.deepcopy(contexts[0])
source = SOURCE_INPUTS[ROUTE[0]]
context["lookups"] = source.get("lookups", {})

print("ROUTING_STATUS =", context["routing_report"].get("STATUS"))
print("SELECTED_MAPPING_ROWS =", len(context.get("mapping_rows") or []))
print("SOURCE_SELECTED_ROWS =", source.get("selection", {}).get("SELECTED_ROWS"))
print("EXECUTE_WRITES =", context["config"].get("EXECUTE_WRITES"))
print("STORAGE_CONTRACT_VERIFIED =", (context["config"].get("STORAGE_CONTRACT") or {}).get("VERIFIED"))

# Surface intentional populated-value guards before graph construction.
guard_rows = [
    row for row in (context.get("mapping_rows") or [])
    if row.get("APPROVAL_STATUS") == "BLOCKED_IF_POPULATED"
       or row.get("EXECUTION_STATUS") == "BLOCKED_IF_POPULATED"
]
print("POPULATED_VALUE_GUARDS =", [
    (row.get("SOURCE_FIELD_NAME"), row.get("RULE_ID"))
    for row in guard_rows
])

print()
print("BUILD_GRAPH_DIAGNOSTIC")
try:
    nodes, edges = build_oscal_graph(
        source["source_df"],
        None,
        None,
        context["config"]["OSCAL_MODEL"],
        context["config"]["SOURCE_SYSTEM_NAME"],
        context["config"]["SOURCE_TABLE_NAME"],
        context=context,
    )
    print("GRAPH_BUILD = PASS")
    print("NODES =", nodes.count())
    print("EDGES =", edges.count())
    print("RESULT: SSP_GRAPH_BUILD_PASSED_DIAGNOSTIC")
except Exception as error:
    print("GRAPH_BUILD = FAILED")
    print("UNDERLYING_ERROR_TYPE =", type(error).__name__)
    print("UNDERLYING_ERROR_MESSAGE =", str(error))
    report = context.get("graph_report") or {}
    print("GRAPH_REPORT_STATUS =", report.get("STATUS"))
    print("GRAPH_REPORT =", report)
    print("RESULT: SSP_GRAPH_BUILD_FAILURE_IDENTIFIED")
