# RUN NOW — Diagnose why AUTHORIZATION_DECISION did not compile
# Date: 2026-09-21
# READ ONLY. Run in the CURRENT notebook session. Do not rerun Cells 1-3 first.
#
# This tells us whether the notebook loaded a stale CSV or whether Cell 3 routed
# the current row out for a registry/metadata reason.

FIELD = "AUTHORIZATION_DECISION"

source_rows = MAPPING_INPUTS.get("source-one", [])
matches = [row for row in source_rows if row.get("SOURCE_FIELD_NAME") == FIELD]

print("AUTHORIZATION_DECISION_COMPILE_DIAGNOSTIC")
print("RAW_MAPPING_ROWS_FOUND =", len(matches))

for row in matches:
    print("RAW_EXECUTION_STATUS =", row.get("EXECUTION_STATUS"))
    print("RAW_TRANSFORM_ID =", row.get("TRANSFORM_ID"))
    print("RAW_OSCAL_ELEMENT_PATH =", row.get("OSCAL_ELEMENT_PATH"))
    print("RAW_RUNTIME_TARGET_PATH =", row.get("RUNTIME_TARGET_PATH"))
    print("RAW_RULE_ID =", row.get("RULE_ID"))

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "SSP"
    ),
    None,
)
if context is None:
    raise ValueError("Source One SSP context is not loaded")

compiled = [
    row for row in context["mapping_rows"]
    if row.get("SOURCE_FIELD_NAME") == FIELD
]

print("COMPILED_ROWS_FOUND =", len(compiled))
print("ROUTE_STATUS =", context["routing_report"].get("STATUS"))
print("SELECTED_ROWS_TOTAL =", context["routing_report"].get("SELECTED_ROWS"))
print("DEFERRED_ROWS =", context["routing_report"].get("DEFERRED_ROWS"))
print("EXCLUDED_ROWS =", context["routing_report"].get("EXCLUDED_ROWS"))
print("BLOCKED_ROWS =", context["routing_report"].get("BLOCKED_ROWS"))
print("REASON_COUNTS =", context["routing_report"].get("REASON_COUNTS"))

issues = [
    issue for issue in context["routing_report"].get("ISSUES", [])
    if issue.get("field") == FIELD
]
print("FIELD_ISSUES =", issues)

if compiled:
    row = compiled[0]
    print("COMPILED_TRANSFORM_ID =", row.get("TRANSFORM_ID"))
    print("COMPILED_CANONICAL_PATH =", row.get("CANONICAL_ELEMENT_PATH"))
    print("RESULT: AUTHORIZATION_DECISION_IS_COMPILED")
elif matches and matches[0].get("EXECUTION_STATUS") != "APPROVED":
    print("RESULT: NOTEBOOK_HAS_STALE_MAPPING_CSV")
elif issues:
    print("RESULT: CURRENT_ROW_ROUTED_OUT_BY_CELL3")
else:
    print("RESULT: REVIEW_CURRENT_MAPPING_INPUT_STATE")
