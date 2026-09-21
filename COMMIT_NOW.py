# COMMIT NOW — Source One SSP authorization-decision batch
# Date: 2026-09-21
#
# INTENTIONAL WRITE CELL.
# Run only after the accepted PREVIEW + RUN_NOW.py reconciliation in the SAME session.
# This uses the existing guarded Cell 6/7 loader and commits only source-one / SSP.
#
# Expected accepted PREVIEW:
#   nodes = 89629
#   edges = 86816
#   DIM  = 2308 inserts / 0 updates / 87321 unchanged
#   FACT = 2308 inserts / 0 updates / 84508 unchanged
#
# On success, the existing loader must return COMMITTED_AND_VERIFIED.

import json

ROUTE = ("source-one", "SSP")

if not isinstance(PIPELINE_REPORT, dict):
    raise ValueError("Accepted PREVIEW report is unavailable")

if PIPELINE_REPORT.get("mode") != "PREVIEW":
    raise ValueError("Current pipeline report must be PREVIEW before this commit helper")
if PIPELINE_REPORT.get("status") != "PREVIEW_COMPLETE":
    raise ValueError("Accepted PREVIEW did not complete successfully")
if PIPELINE_REPORT.get("writes_executed") is not False:
    raise ValueError("Accepted PREVIEW unexpectedly executed writes")
if PIPELINE_REPORT.get("commit_attempted") is not False:
    raise ValueError("Accepted PREVIEW unexpectedly attempted a commit")

routes = {
    (c["source_key"], c["config"]["OSCAL_MODEL"])
    for c in MAPPING_CONTEXTS
}
if routes != {ROUTE}:
    raise ValueError("Commit helper requires source-one / SSP to be the only selected route: " + repr(routes))

group = next(
    (
        g for g in PIPELINE_REPORT.get("groups", [])
        if g.get("source") == ROUTE[0] and g.get("model") == ROUTE[1]
    ),
    None,
)
if group is None:
    raise ValueError("Accepted Source One SSP PREVIEW group is missing")

load = group["load"]
expected_changes = load.get("expected_changes") or {}
expected_dim = {"INSERTS": 2308, "UPDATES": 0, "UNCHANGED": 87321}
expected_fact = {"INSERTS": 2308, "UPDATES": 0, "UNCHANGED": 84508}

if load.get("status") != "PREVIEW_PASSED_NO_TARGET_DML":
    raise ValueError("Accepted SSP route is not a successful no-DML PREVIEW")
if load.get("nodes") != 89629 or load.get("edges") != 86816:
    raise ValueError("SSP graph counts differ from the accepted PREVIEW")
if (expected_changes.get("D") or {}) != expected_dim:
    raise ValueError("DIM delta differs from the accepted PREVIEW")
if (expected_changes.get("F") or {}) != expected_fact:
    raise ValueError("FACT delta differs from the accepted PREVIEW")
if load.get("target_dml_attempted") is not False or load.get("writes_executed") is not False:
    raise ValueError("Accepted PREVIEW must have no target DML")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Shared EXECUTE_WRITES must remain False")

print("SOURCE_ONE_SSP_COMMIT_AUTHORIZED_BY_ACCEPTED_PREVIEW")
print("ROUTE =", ROUTE)
print("PREVIEW_NODES =", load.get("nodes"))
print("PREVIEW_EDGES =", load.get("edges"))
print("PREVIEW_DIM_CHANGES =", expected_changes.get("D"))
print("PREVIEW_FACT_CHANGES =", expected_changes.get("F"))
print("Running existing guarded pipeline in COMMIT mode...")

MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(
    SOURCE_INPUTS,
    MAPPING_CONTEXTS,
    "COMMIT",
)

print("OSCAL_PIPELINE_REPORT")
print(json.dumps(PIPELINE_REPORT, indent=2, default=str))

commit_group = next(
    (
        g for g in PIPELINE_REPORT.get("groups", [])
        if g.get("source") == ROUTE[0] and g.get("model") == ROUTE[1]
    ),
    None,
)
if (
    PIPELINE_REPORT.get("status") != "COMMITTED_AND_VERIFIED"
    or commit_group is None
    or commit_group["load"].get("status") != "COMMITTED_AND_VERIFIED"
    or commit_group["load"].get("writes_executed") is not True
    or commit_group["load"].get("persisted") is not True
    or commit_group["load"].get("committed") is not True
):
    raise ValueError("SSP COMMIT did not return COMMITTED_AND_VERIFIED")

print("RESULT: SOURCE_ONE_SSP_COMMIT_AND_READBACK_VERIFIED")
