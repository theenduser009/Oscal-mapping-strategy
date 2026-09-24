# RUN NOW — Diagnose Level-355 SSP graph failure after joined-record changes
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Current Cell 7 report showed:
#   mode = COMMIT
#   status = FAILED_BEFORE_COMMIT
#   writes_executed = false
#   commit_attempted = false
#   failed_route = source-one / SSP
#
# This helper calls graph construction only so the hidden underlying ValueError
# is printed directly. It does NOT call validate_and_load_oscal and cannot write
# target DIM/FACT rows.

import copy

ROUTE = ("source-one", "SSP")

print("LEVEL355_SSP_GRAPH_FAILURE_DIAGNOSTIC")
print("PIPELINE_MODE =", (PIPELINE_REPORT or {}).get("mode") if isinstance(PIPELINE_REPORT, dict) else None)
print("PIPELINE_STATUS =", (PIPELINE_REPORT or {}).get("status") if isinstance(PIPELINE_REPORT, dict) else None)
print("WRITES_EXECUTED =", (PIPELINE_REPORT or {}).get("writes_executed") if isinstance(PIPELINE_REPORT, dict) else None)
print("COMMIT_ATTEMPTED =", (PIPELINE_REPORT or {}).get("commit_attempted") if isinstance(PIPELINE_REPORT, dict) else None)

contexts = [
    c for c in MAPPING_CONTEXTS
    if (c["source_key"], c["config"]["OSCAL_MODEL"]) == ROUTE
]

print("MATCHING_CONTEXTS =", len(contexts))
if len(contexts) != 1:
    raise ValueError("Expected exactly one source-one / SSP context")

context = copy.deepcopy(contexts[0])
source = SOURCE_INPUTS[ROUTE[0]]
context["lookups"] = source.get("lookups", {})

print("ROUTING_STATUS =", context["routing_report"].get("STATUS"))
print("SELECTED_MAPPING_ROWS =", len(context.get("mapping_rows") or []))
print("SOURCE_SELECTED_ROWS =", source.get("selection", {}).get("SELECTED_ROWS"))
print("JOINED_LOOKUP_KEYS =", sorted((source.get("lookups", {}).get("joined_sources", {}) or {}).keys()))

joined = source.get("lookups", {}).get("joined_sources", {}).get("allocated-controls")
if joined is not None:
    print("ALLOCATED_CONTROLS_JOINED_ROWS =", joined.count())
else:
    print("ALLOCATED_CONTROLS_JOINED_ROWS = MISSING")

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
    print("GRAPH_REPORT =", context.get("graph_report"))
    print("RESULT: LEVEL355_SSP_GRAPH_BUILD_PASSED")
except Exception as error:
    print("GRAPH_BUILD = FAILED")
    print("UNDERLYING_ERROR_TYPE =", type(error).__name__)
    print("UNDERLYING_ERROR_MESSAGE =", str(error))
    print("GRAPH_REPORT =", context.get("graph_report"))
    print("RESULT: LEVEL355_SSP_GRAPH_FAILURE_IDENTIFIED")
