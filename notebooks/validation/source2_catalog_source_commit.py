# %% Source 2 Catalog Source COMMIT helper
# Run this in a new Python cell AFTER the Source 2 Catalog PREVIEW and
# read-only inspection have passed in the same notebook session.
# This cell performs target DIM/FACT DML through the existing guarded Cell 6/7 loader.

import json

route = ("source-two-source", "CATALOG")

if not isinstance(PIPELINE_REPORT, dict):
    raise ValueError("Run the Source 2 Catalog PREVIEW through Cell 7 first")
if PIPELINE_REPORT.get("status") != "PREVIEW_COMPLETE":
    raise ValueError("Prior pipeline status must be PREVIEW_COMPLETE before COMMIT")
if PIPELINE_REPORT.get("writes_executed") is not False:
    raise ValueError("Prior PREVIEW must have writes_executed = false")
if PIPELINE_REPORT.get("commit_attempted") is not False:
    raise ValueError("Prior PREVIEW must have commit_attempted = false")
if route not in MODEL_GRAPHS:
    raise ValueError("Expected Source 2 Catalog graph is not available")

preview_nodes = MODEL_GRAPHS[route]["nodes"].count()
preview_edges = MODEL_GRAPHS[route]["edges"].count()

if preview_nodes != 1549 or preview_edges != 1401:
    raise ValueError(
        f"Preview graph changed from the accepted checkpoint: nodes={preview_nodes}, edges={preview_edges}"
    )

print("SOURCE2_CATALOG_SOURCE_COMMIT_AUTHORIZED")
print("PREVIEW_NODES =", preview_nodes)
print("PREVIEW_EDGES =", preview_edges)
print("Re-running guarded route in COMMIT mode: PREVIEW first, then target DML/read-back verification.")

MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(
    SOURCE_INPUTS,
    MAPPING_CONTEXTS,
    "COMMIT",
)

print("OSCAL_PIPELINE_REPORT")
print(json.dumps(PIPELINE_REPORT, indent=2, default=str))

if PIPELINE_REPORT.get("status") != "COMMITTED_AND_VERIFIED":
    raise ValueError("Commit did not finish as COMMITTED_AND_VERIFIED; inspect OSCAL_PIPELINE_REPORT")

print("SOURCE2_CATALOG_SOURCE_COMMIT_AND_READBACK_VERIFIED")
