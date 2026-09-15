# %% SSP Validation 03 - Metadata timestamp semantics
# Date: 2026-09-15
# READ ONLY. Run in the same Snowflake notebook session after Cells 1-7.
# Requires SELECTED_MODELS=("SSP",) and EXECUTE_WRITES=False.
#
# Scope: ONLY the currently executable SSP Metadata timestamp mappings:
#   ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED -> metadata.published
#   FIRST_PUBLISHED                                      -> metadata.published
#   ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED   -> metadata.last-modified
#   LAST_UPDATED                                         -> metadata.last-modified
#
# Goal: inspect the actual source values and generated Metadata payload values,
# and mechanically verify that populated generated values are RFC3339-style
# OSCAL date-time strings containing a timezone (Z or +/-HH:MM).
# This does not resolve semantic precedence if two source fields populate the
# same OSCAL target; it exposes that evidence for review.

import re
from collections import Counter

if tuple(SELECTED_MODELS) != ("SSP",):
    raise ValueError("Validation 03 requires SELECTED_MODELS = ('SSP',)")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Validation 03 requires EXECUTE_WRITES = False")

ssp_context = next(
    (c for c in MAPPING_CONTEXTS if c["config"]["OSCAL_MODEL"] == "SSP"),
    None,
)
if ssp_context is None:
    raise ValueError("Compiled SSP context is missing")

expected = {
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED": "system-security-plan.metadata.published",
    "FIRST_PUBLISHED": "system-security-plan.metadata.published",
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED": "system-security-plan.metadata.last-modified",
    "LAST_UPDATED": "system-security-plan.metadata.last-modified",
}

compiled = [
    r for r in ssp_context["mapping_rows"]
    if r.get("SOURCE_FIELD_NAME") in expected
]

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

# Locate the in-memory candidate node collection produced by the current Cells 1-7.
# The mapper versions used in this project have exposed candidate nodes under one
# of these names. Do not query/write target tables for this validation.
candidate_nodes = None
for name in ("ALL_NODES", "CANDIDATE_NODES", "NODES", "nodes"):
    value = globals().get(name)
    if value is not None:
        candidate_nodes = value
        break

# Convert common candidate representations to Python dictionaries.
def _rows(value):
    if value is None:
        return []
    if hasattr(value, "collect"):
        value = value.collect()
    if isinstance(value, dict):
        value = list(value.values())
    result = []
    for row in value:
        if hasattr(row, "as_dict"):
            row = row.as_dict(recursive=True)
        if isinstance(row, dict):
            result.append({str(k).upper(): v for k, v in row.items()})
    return result

node_rows = _rows(candidate_nodes)
metadata_rows = [
    r for r in node_rows
    if str(r.get("ELEMENT_TYPE") or "").lower() == "metadata"
]

# If the current orchestrator keeps candidates inside result/context objects,
# report that precisely rather than inventing a target-table fallback.
if not node_rows:
    print("=== SSP VALIDATION 03 ===")
    print("STATUS: NEEDS_CANDIDATE_HANDLE")
    print("MAPPING_CONTRACT_FAILURES:", mapping_contract_failures)
    print("The four timestamp mappings compiled, but this notebook session does not expose")
    print("candidate nodes under ALL_NODES/CANDIDATE_NODES/NODES/nodes.")
    print("Do NOT query target tables as a substitute. Send this output so the validator")
    print("can be bound to the exact Cell 7 result handle.")
else:
    # OSCAL date-time uses RFC3339-style lexical form. Require date + time + timezone.
    rfc3339_tz = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
    )

    generated = []
    invalid_generated = []
    for row in metadata_rows:
        payload = row.get("METADATA_JSON")
        if payload is None:
            payload = row.get("PAYLOAD") or row.get("ELEMENT_JSON")
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

    # Inspect raw source values for the same four source fields from the frozen source input.
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
    print("CANDIDATE_NODE_ROWS:", len(node_rows))
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
        print("VALIDATION 03 PASSED: populated generated Metadata timestamps have OSCAL-compatible timezone-bearing date-time shape.")
    elif not generated:
        print("FAILURE: no populated generated Metadata timestamp values were available to validate; do not claim semantic timestamp validation yet.")
