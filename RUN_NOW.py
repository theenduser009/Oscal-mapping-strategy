# RUN NOW — Source One SSP responsible-party PREVIEW reconciliation
# Date: 2026-09-21
# READ ONLY. Run AFTER Cell 7 PREVIEW in the same Snowflake notebook session.
#
# Purpose:
# Verify the four newly approved SSP responsible-party roles materialize with the
# exact source-population counts observed during the pre-mapping shape check.
# No target DML.

import json
from collections import Counter

ROUTE = ("source-one", "SSP")

EXPECTED = {
    "senior-information-systems-security-officer": 2104,
    "information-system-security-engineer": 257,
    "information-system-administrator": 257,
    "authorizing-official-designated-representative": 65,
}

if ROUTE not in MODEL_GRAPHS:
    raise ValueError("Run Source One SSP PREVIEW through Cell 7 first")

group = next(
    (
        g for g in (PIPELINE_REPORT or {}).get("groups", [])
        if g.get("source") == "source-one"
        and g.get("model") == "SSP"
    ),
    None,
)
if group is None:
    raise ValueError("Source One SSP PREVIEW group not found")

load = group["load"]
if load.get("status") != "PREVIEW_PASSED_NO_TARGET_DML":
    raise ValueError("Expected a successful no-DML SSP PREVIEW")
if load.get("target_dml_attempted") is not False or load.get("writes_executed") is not False:
    raise ValueError("Reconciliation requires a no-write PREVIEW")

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

print("SOURCE_ONE_SSP_RESPONSIBLE_PARTY_PREVIEW_RECONCILIATION")

problems = []
for role_id, expected in EXPECTED.items():
    role_actual = role_counts.get(role_id, 0)
    assignment_actual = assignment_counts.get(role_id, 0)
    print(role_id, "| ROLES =", role_actual, "| ASSIGNMENTS =", assignment_actual, "| EXPECTED =", expected)
    if role_actual != expected or assignment_actual != expected:
        problems.append((role_id, role_actual, assignment_actual, expected))

expected_changes = load.get("expected_changes") or {}
print("PREVIEW_NODES =", load.get("nodes"))
print("PREVIEW_EDGES =", load.get("edges"))
print("PARTY_NODES_TOTAL =", party_count)
print("EXPECTED_DIM_CHANGES =", expected_changes.get("D"))
print("EXPECTED_FACT_CHANGES =", expected_changes.get("F"))
print("TARGET_DML_ATTEMPTED =", load.get("target_dml_attempted"))
print("WRITES_EXECUTED =", load.get("writes_executed"))

if problems:
    print("RESULT: REVIEW_RESPONSIBLE_PARTY_COUNTS_BEFORE_COMMIT")
    for problem in problems:
        print("MISMATCH:", problem)
else:
    print("RESULT: SSP_RESPONSIBLE_PARTY_PREVIEW_RECONCILED")
