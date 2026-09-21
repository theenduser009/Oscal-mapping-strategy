# RUN NOW — Source One Assessment Results PREVIEW insert reconciliation
# Date: 2026-09-21
# READ ONLY. Run AFTER Cell 7 PREVIEW in the same Snowflake notebook session.
#
# Purpose:
# Reconcile the 16,485 proposed Source One DIM inserts / 16,485 FACT inserts to
# the 11 newly executable September 21 mappings. No target DML.

import json
from collections import Counter

ROUTE = ("source-one", "ASSESSMENT_RESULTS")

EXPECTED_NAMES = (
    "avg-security-compliance-reporting-score",
    "avg-security-compliance-score",
    "total-package-inherent-risk",
    "risk-acceptance-rbds",
    "workflow-current-node",
    "workflow-process-version",
    "workflow-job-status",
    "workflow-status",
    "due-date",
    "workflow-current-node-hrtn",
    "workflow-status-changed",
)

if ROUTE not in MODEL_GRAPHS:
    raise ValueError("Run Source One Assessment Results PREVIEW through Cell 7 first")

group = next(
    (
        g for g in (PIPELINE_REPORT or {}).get("groups", [])
        if g.get("source") == "source-one"
        and g.get("model") == "ASSESSMENT_RESULTS"
    ),
    None,
)
if group is None:
    raise ValueError("Source One Assessment Results PREVIEW group not found")

load = group["load"]
if load.get("status") != "PREVIEW_PASSED_NO_TARGET_DML":
    raise ValueError("Expected a successful no-DML PREVIEW before reconciliation")
if load.get("target_dml_attempted") is not False or load.get("writes_executed") is not False:
    raise ValueError("Reconciliation requires a no-write PREVIEW")

nodes = MODEL_GRAPHS[ROUTE]["nodes"]

counts = Counter()

for row in nodes.select("ELEMENT_PATH", "METADATA_JSON").to_local_iterator():
    path = row["ELEMENT_PATH"]
    if path not in {
        "assessment-results.results[].observations[]",
        "assessment-results.results[].props[]",
    }:
        continue

    payload = row["METADATA_JSON"]
    payload = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(payload, dict):
        continue

    if path.endswith("observations[]"):
        props = payload.get("props") or []
        if isinstance(props, list):
            for prop in props:
                if isinstance(prop, dict) and isinstance(prop.get("name"), str):
                    counts[prop["name"]] += 1
    else:
        name = payload.get("name")
        if isinstance(name, str):
            counts[name] += 1

expected_changes = load.get("expected_changes") or {}
dim_inserts = int((expected_changes.get("D") or {}).get("INSERTS") or 0)
fact_inserts = int((expected_changes.get("F") or {}).get("INSERTS") or 0)

print("SOURCE_ONE_AR_PREVIEW_INSERT_RECONCILIATION")
new_total = 0
for name in EXPECTED_NAMES:
    value = counts.get(name, 0)
    new_total += value
    print(name, "=", value)

print("NEW_MAPPING_NODE_TOTAL =", new_total)
print("EXPECTED_DIM_INSERTS =", dim_inserts)
print("EXPECTED_FACT_INSERTS =", fact_inserts)
print("DIM_DELTA_NOT_ATTRIBUTED =", dim_inserts - new_total)
print("FACT_DELTA_NOT_ATTRIBUTED =", fact_inserts - new_total)

if new_total == dim_inserts == fact_inserts:
    print("RESULT: SOURCE_ONE_AR_INSERTS_FULLY_RECONCILED")
else:
    print("RESULT: REVIEW_UNATTRIBUTED_PREVIEW_DELTA_BEFORE_COMMIT")
