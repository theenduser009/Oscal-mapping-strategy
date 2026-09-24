# COMMIT NOW — Source One SSP Level-355 implemented-requirements first batch
# Date: 2026-09-24
#
# INTENTIONAL WRITE CELL.
# Run only after the accepted PREVIEW in the SAME notebook session.
#
# Accepted PREVIEW:
#   source-one / SSP only
#   nodes = 250845
#   edges = 248032
#   source_records = 2813
#   DIM  = 130309 inserts / 0 updates / 120536 unchanged
#   FACT = 130309 inserts / 0 updates / 117723 unchanged
#
# Delta reconciliation:
#   2,813 control-implementation parent nodes
# + 127,496 implemented-requirements child nodes
# = 130,309 new DIM rows and 130,309 new CONTAINS edges.
#
# This first Level-355 batch maps:
#   ALLOCATED_CONTROL_ID -> collection instance identity
#   CONTROL_NUMBER       -> implemented-requirement.control-id

import json

ROUTE = ("source-one", "SSP")

if not isinstance(PIPELINE_REPORT, dict):
    raise ValueError("Accepted PREVIEW report is unavailable")
if PIPELINE_REPORT.get("mode") != "PREVIEW":
    raise ValueError("Current pipeline report must be PREVIEW")
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
    raise ValueError("Commit helper requires source-one / SSP as the only selected route")

group = next(
    (g for g in PIPELINE_REPORT.get("groups", [])
     if g.get("source") == ROUTE[0] and g.get("model") == ROUTE[1]),
    None,
)
if group is None:
    raise ValueError("Accepted Source One SSP PREVIEW group is missing")

load = group["load"]
expected_dim = {"INSERTS": 130309, "UPDATES": 0, "UNCHANGED": 120536}
expected_fact = {"INSERTS": 130309, "UPDATES": 0, "UNCHANGED": 117723}
changes = load.get("expected_changes") or {}

if load.get("status") != "PREVIEW_PASSED_NO_TARGET_DML":
    raise ValueError("Accepted SSP route is not a successful PREVIEW")
if load.get("nodes") != 250845 or load.get("edges") != 248032:
    raise ValueError("Graph counts differ from the accepted Level-355 PREVIEW")
if load.get("source_records") != 2813:
    raise ValueError("Source-record count differs from the accepted PREVIEW")
if (changes.get("D") or {}) != expected_dim:
    raise ValueError("DIM delta differs from the accepted PREVIEW")
if (changes.get("F") or {}) != expected_fact:
    raise ValueError("FACT delta differs from the accepted PREVIEW")
if load.get("target_dml_attempted") is not False or load.get("writes_executed") is not False:
    raise ValueError("Accepted PREVIEW must have no target DML")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Shared EXECUTE_WRITES must remain False")

print("SOURCE_ONE_SSP_LEVEL355_COMMIT_AUTHORIZED_BY_ACCEPTED_PREVIEW")
print("PREVIEW_NODES =", load.get("nodes"))
print("PREVIEW_EDGES =", load.get("edges"))
print("PREVIEW_DIM_CHANGES =", changes.get("D"))
print("PREVIEW_FACT_CHANGES =", changes.get("F"))
print("Running existing guarded pipeline in COMMIT mode...")

MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(
    SOURCE_INPUTS,
    MAPPING_CONTEXTS,
    "COMMIT",
)

print("OSCAL_PIPELINE_REPORT")
print(json.dumps(PIPELINE_REPORT, indent=2, default=str))

commit_group = next(
    (g for g in PIPELINE_REPORT.get("groups", [])
     if g.get("source") == ROUTE[0] and g.get("model") == ROUTE[1]),
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
    raise ValueError("Level-355 SSP COMMIT did not return COMMITTED_AND_VERIFIED")

print("RESULT: SOURCE_ONE_SSP_LEVEL355_FIRST_BATCH_COMMIT_AND_READBACK_VERIFIED")
