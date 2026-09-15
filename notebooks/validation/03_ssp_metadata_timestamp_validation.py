# %% SSP Validation 03 - Metadata timestamp semantics
# Date: 2026-09-15
# READ ONLY. Run in the same Snowflake notebook session after Cells 1-7.
# Requires SELECTED_MODELS=("SSP",), EXECUTE_WRITES=False, and Cell 7 PREVIEW.
#
# Scope: currently executable SSP Metadata timestamp mappings.
# Validates source mapping contract plus generated metadata published/last-modified
# lexical shape. No target-table reads and no writes.

import re

if tuple(SELECTED_MODELS) != ("SSP",):
    raise ValueError("Validation 03 requires SELECTED_MODELS = ('SSP',)")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Validation 03 requires EXECUTE_WRITES = False")
if OSCAL_LOAD_MODE != "PREVIEW":
    raise ValueError("Validation 03 requires Cell 7 OSCAL_LOAD_MODE = 'PREVIEW'")

ssp_context = next((c for c in MAPPING_CONTEXTS if c["config"]["OSCAL_MODEL"] == "SSP"), None)
if ssp_context is None:
    raise ValueError("Compiled SSP context is missing")

expected = {
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED": "system-security-plan.metadata.published",
    "FIRST_PUBLISHED": "system-security-plan.metadata.published",
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED": "system-security-plan.metadata.last-modified",
    "LAST_UPDATED": "system-security-plan.metadata.last-modified",
}
compiled = [r for r in ssp_context["mapping_rows"] if r.get("SOURCE_FIELD_NAME") in expected]

mapping_contract_failures = []
for field, target in expected.items():
    matches = [r for r in compiled if r.get("SOURCE_FIELD_NAME") == field]
    if len(matches) != 1:
        mapping_contract_failures.append((field, "COMPILED_ROW_COUNT", len(matches)))
        continue
    row = matches[0]
    if row.get("CANONICAL_ELEMENT_PATH") != target:
        mapping_contract_failures.append((field, "TARGET", row.get("CANONICAL_ELEMENT_PATH")))
    if row.get("TRANSFORM_ID") != "timestamp":
        mapping_contract_failures.append((field, "TRANSFORM", row.get("TRANSFORM_ID")))

# Cell 7's actual contract is MODEL_GRAPHS[(source_key, model)]["nodes"].
graph_key = (ssp_context["source_key"], "SSP")
if not isinstance(MODEL_GRAPHS, dict) or graph_key not in MODEL_GRAPHS:
    raise ValueError("Cell 7 SSP PREVIEW graph is missing from MODEL_GRAPHS")
candidate_nodes = MODEL_GRAPHS[graph_key]["nodes"]

# Keep the data in Snowpark; only collect the small Metadata subset.
metadata_df = candidate_nodes.filter(col("ELEMENT_TYPE") == lit("metadata"))
metadata_rows = [r.as_dict(recursive=True) for r in metadata_df.collect()]

rfc3339_tz = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")

generated = []
invalid_generated = []
for row in metadata_rows:
    payload = row.get("METADATA_JSON")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = None
    if not isinstance(payload, dict):
        continue
    for member in ("published", "last-modified"):
        value = payload.get(member)
        if value is None:
            continue
        text = str(value)
        generated.append((row.get("SOURCE_RECORD_ID"), member, text))
        if not rfc3339_tz.fullmatch(text):
            invalid_generated.append((row.get("SOURCE_RECORD_ID"), member, text))

# Source samples from the same frozen input used by the preview.
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
    for field in expected:
        if field in payload and payload[field] is not None:
            source_samples.append((record_id, field, payload[field]))

print("=== SSP VALIDATION 03 ===")
print("VALIDATION: SSP_METADATA_TIMESTAMPS")
print("MAPPING_ROWS_CHECKED:", len(compiled))
print("MAPPING_CONTRACT_FAILURES:", len(mapping_contract_failures))
print("METADATA_NODE_ROWS:", len(metadata_rows))
print("GENERATED_TIMESTAMP_VALUES:", len(generated))
print("INVALID_GENERATED_TIMESTAMP_VALUES:", len(invalid_generated))
print("SOURCE_TIMESTAMP_SAMPLE_COUNT:", len(source_samples))
print("SOURCE_TIMESTAMP_SAMPLES:", source_samples[:12])
print("GENERATED_TIMESTAMP_SAMPLES:", generated[:12])
print("INVALID_GENERATED_SAMPLES:", invalid_generated[:12])

status = "PASS" if not mapping_contract_failures and generated and not invalid_generated else "FAIL"
print("STATUS:", status)
if status == "PASS":
    print("VALIDATION 03 PASSED: populated generated Metadata timestamps have timezone-bearing OSCAL date-time shape.")
elif not generated:
    print("FAILURE: no populated generated Metadata timestamp values were available; semantic timestamp validation is not proven.")
