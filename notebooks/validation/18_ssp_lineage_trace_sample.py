# %% Read-only trace: Archer Content ID + source field -> mapped OSCAL target
# Run after Cells 1-7 PREVIEW. Uses the in-memory SSP graph/context only.
import json

route = ("source-one", "SSP")
graph = MODEL_GRAPHS[route]
ctx = graph["context"]

target_by_source = {
    row["SOURCE_FIELD_NAME"]: row["CANONICAL_ELEMENT_PATH"]
    for row in ctx["mapping_rows"]
    if row.get("LINEAGE_REQUIRED_FLAG")
}

props = graph["nodes"].filter(
    col("ELEMENT_PATH") == lit("system-security-plan.system-characteristics.props[]")
).select(
    "SOURCE_RECORD_ID",
    "METADATA_JSON",
).collect()

shown = 0
for row in props:
    payload = json.loads(row["METADATA_JSON"])
    if payload.get("name") != "source-field":
        continue

    source_field = payload.get("value")
    print(
        f'{row["SOURCE_RECORD_ID"]} | '
        f'{source_field} -> '
        f'{target_by_source.get(source_field)}'
    )
    shown += 1
    if shown == 20:
        break

print("TRACE_ROWS_SHOWN =", shown)
