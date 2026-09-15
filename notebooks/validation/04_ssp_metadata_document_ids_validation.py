# %% SSP Validation 04 - Metadata document IDs
# Date: 2026-09-15
# READ ONLY. Run in the same Snowflake notebook session after Cells 1-7.
# Requires SELECTED_MODELS=("SSP",), EXECUTE_WRITES=False, Cell 7 PREVIEW.
#
# Goal:
#   Validate the currently generated SSP metadata.document-ids[] nodes mechanically:
#   - mapping rows compile to the document-ids target with identifier transform;
#   - generated identifier values are scalar and nonblank;
#   - no duplicate document identifier exists within the same SSP source record;
#   - preserve samples for source-to-generated review.
#
# This is mechanical/shape validation only. It does not by itself prove that the
# chosen Archer business field is the semantically correct document identifier.

if tuple(SELECTED_MODELS) != ("SSP",):
    raise ValueError("Validation 04 requires SELECTED_MODELS = ('SSP',)")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Validation 04 requires EXECUTE_WRITES = False")
if OSCAL_LOAD_MODE != "PREVIEW":
    raise ValueError("Validation 04 requires Cell 7 OSCAL_LOAD_MODE = 'PREVIEW'")

ssp_context = next((c for c in MAPPING_CONTEXTS if c["config"]["OSCAL_MODEL"] == "SSP"), None)
if ssp_context is None:
    raise ValueError("Compiled SSP context is missing")

# Use the actual compiled mapping contract rather than hardcoding a source field name.
doc_target = "system-security-plan.metadata.document-ids[].identifier"
doc_mappings = [
    r for r in ssp_context["mapping_rows"]
    if r.get("CANONICAL_ELEMENT_PATH") == doc_target
]

mapping_failures = []
if not doc_mappings:
    mapping_failures.append(("NO_EXECUTABLE_MAPPING", doc_target))
for row in doc_mappings:
    if not str(row.get("SOURCE_FIELD_NAME") or "").strip():
        mapping_failures.append(("MISSING_SOURCE_FIELD", row.get("RULE_ID")))
    if row.get("TRANSFORM_ID") != "identifier":
        mapping_failures.append(("UNEXPECTED_TRANSFORM", row.get("SOURCE_FIELD_NAME"), row.get("TRANSFORM_ID")))

# Bind to the actual Cell 7 preview graph.
graph_key = (ssp_context["source_key"], "SSP")
if not isinstance(MODEL_GRAPHS, dict) or graph_key not in MODEL_GRAPHS:
    raise ValueError("Cell 7 SSP PREVIEW graph is missing from MODEL_GRAPHS")
nodes_df = MODEL_GRAPHS[graph_key]["nodes"]

# Registry uses ELEMENT_TYPE=document-ids for this collection node.
doc_rows = [
    r.as_dict(recursive=True)
    for r in nodes_df.filter(col("ELEMENT_TYPE") == lit("document-ids")).collect()
]

invalid_shape = []
generated = []
for row in doc_rows:
    payload = row.get("METADATA_JSON")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = None
    identifier = None
    if isinstance(payload, dict):
        identifier = payload.get("identifier")
    valid = (
        identifier is not None
        and not isinstance(identifier, (dict, list, bool))
        and str(identifier).strip() != ""
    )
    item = (row.get("SOURCE_RECORD_ID"), identifier, row.get("PK_ELEMENT_HASH"), row.get("OSCAL_UUID"))
    generated.append(item)
    if not valid:
        invalid_shape.append(item)

# Duplicate identifier inside the same SSP source record.
seen = set()
duplicates = []
for source_record_id, identifier, pk_hash, oscal_uuid in generated:
    if identifier is None:
        continue
    key = (str(source_record_id), str(identifier).strip())
    if key in seen:
        duplicates.append((source_record_id, identifier))
    else:
        seen.add(key)

# Source evidence from the exact executable source field(s).
source_fields = sorted({r["SOURCE_FIELD_NAME"] for r in doc_mappings if r.get("SOURCE_FIELD_NAME")})
source_df = SOURCE_INPUTS[ssp_context["source_key"]]["source_df"]
source_samples = []
for source_row in source_df.limit(25).collect():
    record_id = source_row["SOURCE_RECORD_ID"]
    payload = source_row["CURATED_JSON"]
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = None
    if not isinstance(payload, dict):
        continue
    for field in source_fields:
        if field in payload and payload[field] is not None:
            source_samples.append((record_id, field, payload[field]))

print("=== SSP VALIDATION 04 ===")
print("VALIDATION: SSP_METADATA_DOCUMENT_IDS")
print("SOURCE_FIELDS:", source_fields)
print("MAPPING_ROWS_CHECKED:", len(doc_mappings))
print("MAPPING_FAILURES:", len(mapping_failures))
print("DOCUMENT_ID_NODE_ROWS:", len(doc_rows))
print("INVALID_IDENTIFIER_SHAPES:", len(invalid_shape))
print("DUPLICATE_IDENTIFIERS_WITHIN_SOURCE_RECORD:", len(duplicates))
print("SOURCE_SAMPLES:", source_samples[:12])
print("GENERATED_SAMPLES:", generated[:12])
print("INVALID_SAMPLES:", invalid_shape[:12])
print("DUPLICATE_SAMPLES:", duplicates[:12])

status = "PASS" if not mapping_failures and doc_rows and not invalid_shape and not duplicates else "FAIL"
print("STATUS:", status)
if status == "PASS":
    print("VALIDATION 04 PASSED: generated SSP Metadata document identifiers are populated scalar values with no duplicate identifier per source record.")
elif not doc_rows:
    print("FAILURE: no generated document-ids nodes were available; document-ID validation is not proven.")
