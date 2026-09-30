# READ ONLY: inspect generated SSP security-impact lineage props after Cell 7 PREVIEW.
# Run after Cells 1-7 with SELECTED_MODELS = ("SSP",) and EXECUTE_WRITES = False.

graph = MODEL_GRAPHS[("source-one", "SSP")]["nodes"]

lineage_rows = (
    graph
    .filter(
        (col("ELEMENT_TYPE") == lit("props"))
        & col("METADATA_JSON").like('%"ns":"urn:company:oscal:lineage:v1"%')
    )
    .select("SOURCE_RECORD_ID", "ELEMENT_PATH", "METADATA_JSON")
    .sort("SOURCE_RECORD_ID", "METADATA_JSON")
    .limit(100)
    .collect()
)

print("Lineage prop sample:", len(lineage_rows))
for row in lineage_rows:
    print(row["SOURCE_RECORD_ID"], row["ELEMENT_PATH"], row["METADATA_JSON"])
