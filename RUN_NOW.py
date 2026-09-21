# RUN NOW — Source One SSP responsible-party run-state + reconciliation
# Date: 2026-09-21
# READ ONLY. Run in the same Snowflake notebook session.
#
# This replaces the earlier PREVIEW-only checker.
# It first reports what Cell 7 ACTUALLY ran (PREVIEW vs COMMIT), then reconciles
# the four newly approved responsible-party roles. It performs no target DML.

import json
from collections import Counter

ROUTE = ("source-one", "SSP")

EXPECTED = {
    "senior-information-systems-security-officer": 2104,
    "information-system-security-engineer": 257,
    "information-system-administrator": 257,
    "authorizing-official-designated-representative": 65,
}

if not isinstance(PIPELINE_REPORT, dict):
    raise ValueError("PIPELINE_REPORT is unavailable; do not rerun anything yet")
if ROUTE not in MODEL_GRAPHS:
    raise ValueError("Source One SSP graph is unavailable in the current session")

group = next(
    (
        g for g in PIPELINE_REPORT.get("groups", [])
        if g.get("source") == "source-one"
        and g.get("model") == "SSP"
    ),
    None,
)
if group is None:
    raise ValueError("Source One SSP group is not present in PIPELINE_REPORT")

load = group["load"]

print("SOURCE_ONE_SSP_RUN_STATE")
print("PIPELINE_MODE =", PIPELINE_REPORT.get("mode"))
print("PIPELINE_STATUS =", PIPELINE_REPORT.get("status"))
print("LOAD_MODE =", load.get("mode"))
print("LOAD_STATUS =", load.get("status"))
print("WRITES_EXECUTED =", load.get("writes_executed"))
print("PERSISTED =", load.get("persisted"))
print("COMMITTED =", load.get("committed"))
print("TARGET_DML_ATTEMPTED =", load.get("target_dml_attempted"))
print("NODES =", load.get("nodes"))
print("EDGES =", load.get("edges"))
print("EXPECTED_CHANGES =", load.get("expected_changes"))
print("VERIFICATION =", load.get("verification"))

nodes = MODEL_GRAPHS[ROUTE]["nodes"]
role_counts = Counter()
assignment_counts = Counter()
party_count = 0

for row in nodes.select("ELEMENT_PATH", "METADATA_JSON").to_local_iterator():
    path = row["ELEMENT_PATH"]
    payload = row["METADATA_JSON"]
    payload = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(payload, dict):
        continue

    if path == "system-security-plan.metadata.roles[]":
        role_id = payload.get("id")
        if isinstance(role_id, str):
            role_counts[role_id] += 1
    elif path == "system-security-plan.metadata.responsible-parties[]":
        role_id = payload.get("role-id")
        if isinstance(role_id, str):
            assignment_counts[role_id] += 1
    elif path == "system-security-plan.metadata.parties[]":
        party_count += 1

print()
print("SOURCE_ONE_SSP_RESPONSIBLE_PARTY_RECONCILIATION")
problems = []
for role_id, expected in EXPECTED.items():
    role_actual = role_counts.get(role_id, 0)
    assignment_actual = assignment_counts.get(role_id, 0)
    print(role_id, "| ROLES =", role_actual, "| ASSIGNMENTS =", assignment_actual, "| EXPECTED =", expected)
    if role_actual != expected or assignment_actual != expected:
        problems.append((role_id, role_actual, assignment_actual, expected))

print("PARTY_NODES_TOTAL =", party_count)

if problems:
    print("RESULT: REVIEW_RESPONSIBLE_PARTY_COUNTS")
    for problem in problems:
        print("MISMATCH:", problem)
elif (
    PIPELINE_REPORT.get("mode") == "PREVIEW"
    and load.get("status") == "PREVIEW_PASSED_NO_TARGET_DML"
    and load.get("writes_executed") is False
    and load.get("target_dml_attempted") is False
):
    print("RESULT: SSP_RESPONSIBLE_PARTY_PREVIEW_RECONCILED")
elif (
    PIPELINE_REPORT.get("mode") == "COMMIT"
    and load.get("status") == "COMMITTED_AND_VERIFIED"
    and load.get("writes_executed") is True
    and load.get("persisted") is True
    and load.get("committed") is True
):
    print("RESULT: SSP_RESPONSIBLE_PARTY_COMMIT_ALREADY_VERIFIED")
    print("ACTION: DO_NOT_RERUN_COMMIT")
else:
    print("RESULT: REVIEW_SSP_RUN_STATE_BEFORE_ANY_RERUN")
