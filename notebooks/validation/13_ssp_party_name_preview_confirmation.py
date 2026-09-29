# %% Read-only confirmation: SSP party-name PREVIEW delta
# Date: 2026-09-29
# Run AFTER Cell 7 PREVIEW in the same notebook session.
# No DML / DDL / writes.
#
# Purpose:
#   Confirm that the pending DIM updates from ResolvedUser enrichment are exactly
#   the existing OSCAL party nodes that gained a name, while graph identity and
#   FACT relationships remain unchanged.

from snowflake.snowpark import functions as F

ROUTE = ("source-one", "SSP")
PARTY_ELEMENT_TYPE = "parties"

if MODEL_GRAPHS is None or PIPELINE_REPORT is None:
    raise ValueError("Run Cell 7 PREVIEW before this confirmation")

graph = MODEL_GRAPHS.get(ROUTE)
if graph is None:
    raise ValueError("Source One / SSP graph is not available from the current PREVIEW")

group = next(
    (
        item for item in PIPELINE_REPORT.get("groups", [])
        if item.get("source") == ROUTE[0] and item.get("model") == ROUTE[1]
    ),
    None,
)
if group is None:
    raise ValueError("Source One / SSP PREVIEW report is missing")

load = group["load"]
if load.get("status") != "PREVIEW_PASSED_NO_TARGET_DML":
    raise ValueError("Current Source One / SSP result is not an accepted PREVIEW")

nodes = graph["nodes"]
party_nodes = nodes.filter(F.col("ELEMENT_TYPE") == F.lit(PARTY_ELEMENT_TYPE))

party_count = party_nodes.count()
named_party_count = party_nodes.filter(
    F.col("METADATA_JSON").contains('"name"')
).count()

identity_mismatch_count = party_nodes.filter(
    F.col("OSCAL_UUID") != F.col("INSTANCE_KEY")
).count()

dim_changes = load["expected_changes"]["D"]
fact_changes = load["expected_changes"]["F"]

print("PARTY_NAME_PREVIEW_CONFIRMATION")
print({
    "PARTY_NODES": party_count,
    "PARTY_NODES_WITH_NAME": named_party_count,
    "PARTY_UUID_INSTANCE_KEY_MISMATCHES": identity_mismatch_count,
    "EXPECTED_DIM_INSERTS": dim_changes["INSERTS"],
    "EXPECTED_DIM_UPDATES": dim_changes["UPDATES"],
    "EXPECTED_FACT_INSERTS": fact_changes["INSERTS"],
    "EXPECTED_FACT_UPDATES": fact_changes["UPDATES"],
    "STATUS": (
        "PARTY_NAME_PREVIEW_COUNTS_RECONCILE"
        if dim_changes["INSERTS"] == 0
        and dim_changes["UPDATES"] == named_party_count
        and fact_changes["INSERTS"] == 0
        and fact_changes["UPDATES"] == 0
        and identity_mismatch_count == 0
        else "REVIEW_BEFORE_COMMIT"
    ),
})
