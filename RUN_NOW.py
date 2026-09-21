# RUN NOW — Source One SSP System Characteristics final compile check
# Date: 2026-09-21
# READ ONLY. Run after replacing ARCHER_OSCAL_MAPPINGS.csv and rerunning Cells 1-3 with SSP selected.
#
# Expected:
# - AUTHORIZATION_DECISION compiles as archer-select -> system-characteristics.props[]
# - FULL_CONTROL_ASSESSMENT_HELPER is EXCLUDED / not compiled
# - selected SSP runtime rows increase from 53 to 54

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "SSP"
    ),
    None,
)
if context is None:
    raise ValueError("Source One SSP context is not loaded; select SSP and rerun Cells 1-3.")

rows = {row["SOURCE_FIELD_NAME"]: row for row in context["mapping_rows"]}

print("SOURCE_ONE_SSP_SYSTEM_CHARACTERISTICS_FINAL_COMPILE_CHECK")
print("ROUTE_STATUS:", context["routing_report"]["STATUS"])
print("SELECTED_ROWS_TOTAL:", context["routing_report"]["SELECTED_ROWS"])

row = rows.get("AUTHORIZATION_DECISION")
if row is None:
    raise ValueError("AUTHORIZATION_DECISION is not compiled")

actual = (
    row["TRANSFORM_ID"],
    row["CANONICAL_ELEMENT_PATH"],
)
expected = (
    "archer-select",
    "system-security-plan.system-characteristics.props[]",
)
if actual != expected:
    raise ValueError("AUTHORIZATION_DECISION compiled differently: " + repr(actual))

print("AUTHORIZATION_DECISION |", actual[0], "|", actual[1])

if "FULL_CONTROL_ASSESSMENT_HELPER" in rows:
    raise ValueError("FULL_CONTROL_ASSESSMENT_HELPER must be excluded from runtime compilation")

if context["routing_report"]["SELECTED_ROWS"] != 54:
    raise ValueError(
        "Expected 54 executable Source One SSP mappings after the System Characteristics decision; got "
        + str(context["routing_report"]["SELECTED_ROWS"])
    )

print("FULL_CONTROL_ASSESSMENT_HELPER | EXCLUDED | NOT_COMPILED")
print("RESULT: SSP_SYSTEM_CHARACTERISTICS_READY_FOR_PREVIEW")
