# %% Read-only SSP CIA validation: Matillion ResolvedValues -> OSCAL security-impact-level
# Date: 2026-10-01
# Run after Cells 1-7 PREVIEW succeeds in the SAME Snowflake notebook session.
# No DML / DDL. Uses only SOURCE_INPUTS + MODEL_GRAPHS already built in memory.
#
# Purpose:
#   Prove the clean v10 boundary:
#     CURATED_JSON.ValuesListIds + ResolvedValues
#       -> notebook OSCAL-only normalization
#       -> security-impact-level security-objective-* payload
#
# This validation does NOT query ARCHER_META_VALUE and does NOT write targets.

import json
from collections import Counter
from snowflake.snowpark.functions import col, lit

route = ("source-one", "SSP")
graph = MODEL_GRAPHS[route]
ctx = graph["context"]
source_df = SOURCE_INPUTS["source-one"]["source_df"]

impact_path = "system-security-plan.system-characteristics.security-impact-level"

cia_rows = [
    row for row in ctx["mapping_rows"]
    if row["TRANSFORM_ID"] == "security-objective"
       and row["OWNER_ELEMENT_PATH"] == impact_path
]
if len(cia_rows) != 11:
    raise ValueError(f"Expected 11 SSP CIA/security-objective mappings, found {len(cia_rows)}")

# Candidate security-impact-level payload by Archer source record.
candidate_rows = graph["nodes"].filter(
    col("ELEMENT_PATH") == lit(impact_path)
).select(
    "SOURCE_RECORD_ID",
    "METADATA_JSON",
).collect()

candidate_by_record = {}
for row in candidate_rows:
    source_id = row["SOURCE_RECORD_ID"]
    if source_id in candidate_by_record:
        raise ValueError("Duplicate security-impact-level node for one source record")
    payload = json.loads(row["METADATA_JSON"])
    if not isinstance(payload, dict):
        raise ValueError("security-impact-level payload must be an object")
    candidate_by_record[source_id] = payload

populated = 0
resolved_occurrences = 0
canonical_occurrences = 0
legacy_occurrences = 0
comparisons = 0
mismatches = []
label_counts = Counter()
field_counts = Counter()
samples = []

for record in source_df.to_local_iterator():
    source_id = record["SOURCE_RECORD_ID"]
    source = _metadata_parse(record, ctx)

    for mapping in cia_rows:
        field = mapping["SOURCE_FIELD_NAME"]
        raw = resolve_json_path(source, field, default=SKIP_VALUE)
        if raw is SKIP_VALUE or not _has_value(raw):
            continue

        populated += 1
        field_counts[field] += 1

        resolved_labels = _resolved_select_labels(raw)
        if resolved_labels is not None:
            resolved_occurrences += 1
            if len(resolved_labels) != 1:
                raise ValueError("CIA field must have exactly one resolved select label")
            resolved_label = resolved_labels[0]
        else:
            # Direct text remains supported for compatibility, but current Archer
            # select containers must already have ResolvedValues or Cell 4 fails.
            resolved_label = _single_curated_label(raw)

        expected = _metadata_transform(mapping, raw, ctx)
        if expected is SKIP_VALUE:
            raise ValueError("Populated CIA source unexpectedly transformed to SKIP_VALUE")

        target_member = mapping["FIELD_RELATIVE_PATH"]
        payload = candidate_by_record.get(source_id)
        actual = None if payload is None else payload.get(target_member)

        comparisons += 1
        label_counts[(target_member, str(resolved_label), str(expected))] += 1

        if str(expected).lower() in {"low", "moderate", "high"}:
            canonical_occurrences += 1
        else:
            legacy_occurrences += 1

        if actual != expected:
            mismatches.append({
                "SOURCE_RECORD_ID": source_id,
                "SOURCE_FIELD_NAME": field,
                "TARGET_MEMBER": target_member,
                "RESOLVED_LABEL": resolved_label,
                "EXPECTED_OSCAL_VALUE": expected,
                "ACTUAL_OSCAL_VALUE": actual,
            })

        if len(samples) < 20:
            source_ids = None
            raw_py = _to_python(raw)
            if isinstance(raw_py, dict):
                for key in ("ValuesListIds", "ValueListIds"):
                    if key in raw_py and _has_value(raw_py[key]):
                        source_ids = raw_py[key]
                        break
            samples.append({
                "CONTENT_ID": source_id,
                "SOURCE_FIELD": field,
                "VALUE_IDS": source_ids,
                "RESOLVED_LABEL": resolved_label,
                "TARGET_MEMBER": target_member,
                "CANDIDATE_VALUE": actual,
            })

print("CIA_MAPPING_FIELDS =", len(cia_rows))
print("SOURCE_RECORDS_CHECKED =", source_df.count())
print("SECURITY_IMPACT_NODES =", len(candidate_rows))
print("POPULATED_CIA_FIELD_OCCURRENCES =", populated)
print("RESOLVEDVALUES_OCCURRENCES =", resolved_occurrences)
print("CANONICAL_LOW_MODERATE_HIGH_OCCURRENCES =", canonical_occurrences)
print("REVIEWED_LEGACY_OCCURRENCES =", legacy_occurrences)
print("TARGET_COMPARISONS =", comparisons)
print("MISMATCHES =", len(mismatches))

print("\nCIA COUNTS BY SOURCE FIELD")
for field in sorted(row["SOURCE_FIELD_NAME"] for row in cia_rows):
    print(f"  {field}: {field_counts[field]}")

print("\nRESOLVED LABEL -> OSCAL VALUE COUNTS")
for (member, label, expected), count in sorted(label_counts.items()):
    print(f"  {member} | {label} -> {expected}: {count}")

print("\nSAMPLE TRACE")
for item in samples:
    print(
        f'{item["CONTENT_ID"]} | {item["SOURCE_FIELD"]} | '
        f'{item["VALUE_IDS"]} -> {item["RESOLVED_LABEL"]} -> '
        f'{item["TARGET_MEMBER"]}={item["CANDIDATE_VALUE"]}'
    )

if mismatches:
    print("\nFIRST MISMATCH =", mismatches[0])
    raise ValueError("CIA ResolvedValues do not match candidate OSCAL security-impact payload")

if resolved_occurrences == 0:
    raise ValueError("No Matillion ResolvedValues were observed for populated CIA fields")

print("\nCIA_RESOLVED_VALUES_VALIDATED = True")
