# RUN NOW — Source One Assessment Results mapping verification
# Date: 2026-09-21
# READ ONLY. Run after replacing ARCHER_OSCAL_MAPPINGS.csv and rerunning Cells 1-3.
#
# Expected current state:
# - 43 executable Source One Assessment Results mapping rows.
# - RISK_ACCEPTANCE_RBDS -> reference-ids -> results[].props[]
# - WORKFLOW_JOB_STATUS -> archer-select -> results[].props[]
# - RISK_ASSESSMENT_REPORT -> DEFERRED (attachment exception; not compiled)

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "ASSESSMENT_RESULTS"
    ),
    None,
)
if context is None:
    raise ValueError("Source One Assessment Results context is not loaded; rerun Cells 1-3.")

rows = {row["SOURCE_FIELD_NAME"]: row for row in context["mapping_rows"]}

expected = {
    "RISK_ACCEPTANCE_RBDS": (
        "reference-ids",
        "assessment-results.results[].props[]",
    ),
    "WORKFLOW_JOB_STATUS": (
        "archer-select",
        "assessment-results.results[].props[]",
    ),
}

print("SOURCE_ONE_AR_FINAL_MAPPING_CHECK")
print("ROUTE_STATUS:", context["routing_report"]["STATUS"])
print("SELECTED_ROWS_TOTAL:", context["routing_report"]["SELECTED_ROWS"])

for field, (transform, path) in expected.items():
    row = rows.get(field)
    if row is None:
        raise ValueError(field + " is not compiled")
    actual = (row["TRANSFORM_ID"], row["CANONICAL_ELEMENT_PATH"])
    if actual != (transform, path):
        raise ValueError(field + " compiled differently: " + repr(actual))
    print(field, "|", actual[0], "|", actual[1])

if "RISK_ASSESSMENT_REPORT" in rows:
    raise ValueError("RISK_ASSESSMENT_REPORT must remain deferred until a valid current-runtime attachment contract exists")

if context["routing_report"]["SELECTED_ROWS"] != 43:
    raise ValueError(
        "Expected 43 executable Source One AR mappings after the attachment deferral; got "
        + str(context["routing_report"]["SELECTED_ROWS"])
    )

print("RISK_ASSESSMENT_REPORT | DEFERRED | NOT_COMPILED")
print("RESULT: SOURCE_ONE_AR_FINAL_MAPPING_READY_FOR_PREVIEW")
