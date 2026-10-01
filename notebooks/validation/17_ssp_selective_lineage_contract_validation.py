# %% Read-only validation of every SSP selective-lineage prop
# Run after Cells 1-7 PREVIEW. Uses only the in-memory candidate graph/context.
import json
from collections import Counter
from snowflake.snowpark.functions import col, lit

route = ("source-one", "SSP")
graph = MODEL_GRAPHS[route]
ctx = graph["context"]
plan = ctx["compiled_plan"]

expected = {row["SOURCE_FIELD_NAME"] for row in plan["mappings"] if row.get("LINEAGE_REQUIRED_FLAG")}
if len(expected) != 12:
    raise ValueError(f"Expected 12 selective SSP lineage fields, found {len(expected)}")

expected_ns = "urn:company:oscal:lineage:v1"
if ctx["config"].get("LINEAGE_PROPERTY_NS") != expected_ns:
    raise ValueError("Unexpected SSP lineage namespace")

lineage = graph["nodes"].filter(col("METADATA_JSON").contains(lit(expected_ns)))
rows = lineage.select("SOURCE_RECORD_ID", "ELEMENT_PATH", "METADATA_JSON").collect()

invalid, seen, duplicates, counts = [], set(), [], Counter()
for row in rows:
    payload = json.loads(row["METADATA_JSON"])
    source_field = payload.get("value")
    valid = (
        row["ELEMENT_PATH"] == "system-security-plan.system-characteristics.props[]"
        and set(payload) == {"name", "ns", "value"}
        and payload.get("name") == "source-field"
        and payload.get("ns") == expected_ns
        and source_field in expected
    )
    if not valid:
        invalid.append({"SOURCE_RECORD_ID": row["SOURCE_RECORD_ID"], "ELEMENT_PATH": row["ELEMENT_PATH"], "METADATA_JSON": payload})
        continue
    identity = (row["SOURCE_RECORD_ID"], source_field)
    if identity in seen:
        duplicates.append(identity)
    else:
        seen.add(identity)
    counts[source_field] += 1

reported = ctx["graph_report"].get("LINEAGE_PROPS")
print("EXPECTED LINEAGE FIELDS =", len(expected))
print("LINEAGE NODES =", len(rows))
print("REPORTED LINEAGE PROPS =", reported)
print("INVALID LINEAGE PROPS =", len(invalid))
print("DUPLICATE LINEAGE PROPS =", len(duplicates))
print("LINEAGE COUNTS BY SOURCE FIELD =")
for field in sorted(expected):
    print(f"  {field}: {counts[field]}")
if reported != len(rows):
    raise ValueError("Candidate lineage node count does not match PREVIEW lineage report")
if invalid:
    print("FIRST INVALID =", invalid[0])
    raise ValueError("Selective SSP lineage contract validation failed")
if duplicates:
    print("FIRST DUPLICATE =", duplicates[0])
    raise ValueError("Duplicate selective SSP lineage props found")
print("LINEAGE_CONTRACT_VALIDATED = True")
