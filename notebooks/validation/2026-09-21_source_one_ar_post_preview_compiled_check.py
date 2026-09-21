# Source One Assessment Results — post-preview compiled-mapping check
# Date: 2026-09-21
# READ ONLY. Run after Cells 1-7 in the same Snowflake notebook session.
#
# Purpose:
# 1) prove the 12 newly approved Source One AR mappings were compiled by Cell 3;
# 2) show exact transform/path chosen for each;
# 3) count present/null/populated source values without printing private values;
# 4) echo the Source One AR PREVIEW result already held in PIPELINE_REPORT.
#
# This file intentionally does NOT query a Snowflake ARCHER_OSCAL_MAPPINGS table.
# The runtime mapping source is Mapping/ARCHER_OSCAL_MAPPINGS.csv loaded by Cell 2.

import json

FIELDS = (
    "AVG_SECURITY_COMPLIANCE_REPORTING_SCORE",
    "AVG_SECURITY_COMPLIANCE_SCORE",
    "TOTAL_PACKAGE_INHERENT_RISK",
    "RISK_ACCEPTANCE_RBDS",
    "RISK_ASSESSMENT_REPORT",
    "WORKFLOW_CURRENT_NODE",
    "WORKFLOW_PROCESS_VERSION",
    "WORKFLOW_JOB_STATUS",
    "WORKFLOW_STATUS",
    "DUE_DATE",
    "WORKFLOW_CURRENT_NODE_HRTN",
    "WORKFLOW_STATUS_CHANGED",
)

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "ASSESSMENT_RESULTS"
    ),
    None,
)
if context is None:
    raise ValueError("Source One Assessment Results mapping context is not loaded; rerun Cells 1-3.")

compiled = {
    row["SOURCE_FIELD_NAME"]: row
    for row in context["mapping_rows"]
    if row["SOURCE_FIELD_NAME"] in FIELDS
}
missing = [field for field in FIELDS if field not in compiled]
if missing:
    raise ValueError(
        "New Source One AR mappings are not all compiled. Missing: " + ", ".join(missing)
    )

print("SOURCE_ONE_AR_COMPILED_MAPPING_CHECK")
print("ROUTE_STATUS:", context["routing_report"]["STATUS"])
print("SELECTED_ROWS_TOTAL:", context["routing_report"]["SELECTED_ROWS"])
print("NEW_FIELDS_COMPILED:", len(compiled))
for field in FIELDS:
    row = compiled[field]
    print(
        field,
        "|",
        row["TRANSFORM_ID"],
        "|",
        row["CANONICAL_ELEMENT_PATH"],
    )

source_df = SOURCE_INPUTS["source-one"]["source_df"]
counts = {
    field: {"PRESENT": 0, "NULL": 0, "POPULATED": 0}
    for field in FIELDS
}

for record in source_df.to_local_iterator():
    payload = record["CURATED_JSON"]
    if hasattr(payload, "as_dict"):
        payload = payload.as_dict(recursive=True)
    elif isinstance(payload, str):
        payload = json.loads(payload)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Source One CURATED_JSON must resolve to an object")

    for field in FIELDS:
        if field not in payload:
            continue
        counts[field]["PRESENT"] += 1
        value = payload[field]
        if value is None:
            counts[field]["NULL"] += 1
        elif value not in ("", [], {}):
            counts[field]["POPULATED"] += 1

print("SOURCE_ONE_AR_SOURCE_POPULATION_COUNTS")
for field in FIELDS:
    c = counts[field]
    print(
        field,
        "| PRESENT=", c["PRESENT"],
        "| NULL=", c["NULL"],
        "| POPULATED=", c["POPULATED"],
    )

group = next(
    (
        g for g in (PIPELINE_REPORT or {}).get("groups", [])
        if g.get("source") == "source-one"
        and g.get("model") == "ASSESSMENT_RESULTS"
    ),
    None,
)
if group is None:
    print("PREVIEW_GROUP: NOT_FOUND")
else:
    load = group["load"]
    print("SOURCE_ONE_AR_PREVIEW")
    print("STATUS:", load.get("status"))
    print("NODES:", load.get("nodes"))
    print("EDGES:", load.get("edges"))
    print("EXPECTED_CHANGES:", load.get("expected_changes"))
    print("TARGET_DML_ATTEMPTED:", load.get("target_dml_attempted"))
    print("WRITES_EXECUTED:", load.get("writes_executed"))
