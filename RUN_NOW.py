# RUN NOW — Source One SSP authorization-decision PREVIEW reconciliation
# Date: 2026-09-21
# READ ONLY. Run AFTER Cell 7 PREVIEW in the same Snowflake notebook session.
#
# Purpose:
# Verify the newly approved AUTHORIZATION_DECISION mapping materializes as exactly
# 2,308 authorization-decision properties and reconcile that with the loader delta.
# FULL_CONTROL_ASSESSMENT_HELPER is excluded and should emit nothing.
#
# No target DML.

import json

ROUTE = ("source-one", "SSP")
EXPECTED_AUTHORIZATION_DECISION_COUNT = 2308

if not isinstance(PIPELINE_REPORT, dict):
    raise ValueError("PIPELINE_REPORT is unavailable")
if ROUTE not in MODEL_GRAPHS:
    raise ValueError("Run Source One SSP PREVIEW through Cell 7 first")

group = next(
    (
        g for g in PIPELINE_REPORT.get("groups", [])
        if g.get("source") == "source-one"
        and g.get("model") == "SSP"
    ),
    None,
)
if group is None:
    raise ValueError("Source One SSP PREVIEW group not found")

load = group["load"]

print("SOURCE_ONE_SSP_AUTHORIZATION_DECISION_PREVIEW")
print("PIPELINE_MODE =", PIPELINE_REPORT.get("mode"))
print("PIPELINE_STATUS =", PIPELINE_REPORT.get("status"))
print("LOAD_STATUS =", load.get("status"))
print("WRITES_EXECUTED =", load.get("writes_executed"))
print("TARGET_DML_ATTEMPTED =", load.get("target_dml_attempted"))
print("NODES =", load.get("nodes"))
print("EDGES =", load.get("edges"))
print("EXPECTED_CHANGES =", load.get("expected_changes"))

count = 0
helper_nodes = 0

for row in MODEL_GRAPHS[ROUTE]["nodes"].select("ELEMENT_PATH", "METADATA_JSON").to_local_iterator():
    path = row["ELEMENT_PATH"]
    payload = row["METADATA_JSON"]
    payload = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(payload, dict):
        continue

    if path == "system-security-plan.system-characteristics.props[]":
        if payload.get("name") == "authorization-decision":
            count += 1
        if payload.get("name") == "full-control-assessment-helper":
            helper_nodes += 1

print("AUTHORIZATION_DECISION_PROPERTY_COUNT =", count)
print("EXPECTED_AUTHORIZATION_DECISION_COUNT =", EXPECTED_AUTHORIZATION_DECISION_COUNT)
print("FULL_CONTROL_ASSESSMENT_HELPER_PROPERTY_COUNT =", helper_nodes)

expected_changes = load.get("expected_changes") or {}
dim = expected_changes.get("D") or {}
fact = expected_changes.get("F") or {}

if (
    PIPELINE_REPORT.get("mode") == "PREVIEW"
    and load.get("status") == "PREVIEW_PASSED_NO_TARGET_DML"
    and load.get("writes_executed") is False
    and load.get("target_dml_attempted") is False
    and count == EXPECTED_AUTHORIZATION_DECISION_COUNT
    and helper_nodes == 0
):
    print("DIM_CHANGES =", dim)
    print("FACT_CHANGES =", fact)
    print("RESULT: SSP_SYSTEM_CHARACTERISTICS_PREVIEW_RECONCILED")
else:
    print("RESULT: REVIEW_SSP_SYSTEM_CHARACTERISTICS_BEFORE_COMMIT")
