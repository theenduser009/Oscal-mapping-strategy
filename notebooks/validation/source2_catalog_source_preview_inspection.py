# %% Read-only Source 2 Catalog Source PREVIEW inspection
# Run this in a new Python cell AFTER Cell 7 has completed successfully.
# This cell performs no target DML and does not change EXECUTE_WRITES.

from collections import Counter
import json

from snowflake.snowpark.functions import col, lit

route = ("source-two-source", "CATALOG")
if route not in MODEL_GRAPHS:
    raise ValueError("Run the Source 2 Catalog PREVIEW through Cell 7 first")

nodes = MODEL_GRAPHS[route]["nodes"]

print("NODE COUNTS BY PATH")
nodes.group_by("ELEMENT_PATH").count().sort("ELEMENT_PATH").show()

metadata_rows = (
    nodes
    .filter(col("ELEMENT_PATH") == lit("catalog.metadata"))
    .select("SOURCE_RECORD_ID", "METADATA_JSON")
    .collect()
)

missing_required = []
for row in metadata_rows:
    payload = json.loads(row["METADATA_JSON"])
    if not payload.get("title") or not payload.get("version"):
        missing_required.append(row["SOURCE_RECORD_ID"])

print("METADATA_ROWS =", len(metadata_rows))
print("MISSING_TITLE_OR_VERSION =", len(missing_required))

prop_rows = (
    nodes
    .filter(col("ELEMENT_PATH") == lit("catalog.metadata.props[]"))
    .select("METADATA_JSON")
    .collect()
)

property_names = Counter(
    json.loads(row["METADATA_JSON"]).get("name")
    for row in prop_rows
)

print("PROPERTY_ROWS =", len(prop_rows))
print("PROPERTY_NAME_COUNTS")
print(json.dumps(dict(sorted(property_names.items())), indent=2))

expected_paths = {
    "catalog": 148,
    "catalog.metadata": 148,
    "catalog.metadata.props[]": len(prop_rows),
}

print("EXPECTED_ROOT_AND_METADATA_COUNTS")
print(json.dumps(expected_paths, indent=2))

if len(metadata_rows) != 148:
    raise ValueError("Expected 148 catalog.metadata nodes from the verified Source snapshot")
if missing_required:
    raise ValueError("One or more Catalog metadata nodes is missing required title/version")

print("SOURCE2_CATALOG_SOURCE_PREVIEW_INSPECTION_PASSED")
