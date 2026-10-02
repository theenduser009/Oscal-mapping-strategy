# %% Read-only SSP CIA validation: Matillion ResolvedValues -> OSCAL security-impact-level
# Date: 2026-10-02
# Run after Cells 1-7 PREVIEW succeeds in the SAME Snowflake notebook session.
# No DML / DDL. Uses only SOURCE_INPUTS + MODEL_GRAPHS already built in memory.
#
# IMPORTANT:
# security-impact-level is an atomic optional object. The mapper emits it only
# when every registry-required CIA member is present. One/two populated
# objectives are intentionally NOT emitted as a partial OSCAL object.
#
# Purpose:
#   Prove the clean v10 boundary:
#     CURATED_JSON.ValuesListIds + ResolvedValues
#       -> notebook OSCAL-only normalization
#       -> complete security-impact-level security-objective-* payload
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
impact_spec = ctx["compiled_plan"]["elements"][impact_path]
required_members = tuple(impact_spec["parameters"].get("required_members", ()))
if not required_members:
    raise ValueError("security-impact-level must have registry-required members")

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

source_records_checked = 0
populated_field_occurrences = 0
resolved_occurrences = 0
canonical_occurrences = 0
legacy_occurrences = 0
complete_records = 0
incomplete_records = 0
complete_comparisons = 0
mismatches = []
unexpected_partial_nodes = []
missing_complete_nodes = []
source_conflicts = []
label_counts = Counter()
field_counts = Counter()
samples = []
incomplete_samples = []

for record in source_df.to_local_iterator():
    source_records_checked += 1
    source_id = record["SOURCE_RECORD_ID"]
    source = _metadata_parse(record, ctx)

    # Build the exact per-record CIA member values that the mapper would assign.
    values_by_member = {}
    sources_by_member = {}
    record_populated = 0

    for mapping in cia_rows:
        field = mapping["SOURCE_FIELD_NAME"]
        raw = resolve_json_path(source, field, default=SKIP_VALUE)
        if raw is SKIP_VALUE or not _has_value(raw):
            continue

        record_populated += 1
        populated_field_occurrences += 1
        field_counts[field] += 1

        resolved_labels = _resolved_select_labels(raw)
        if resolved_labels is not None:
            resolved_occurrences += 1
            if len(resolved_labels) != 1:
                raise ValueError("CIA field must have exactly one resolved select label")
            resolved_label = resolved_labels[0]
        else:
            resolved_label = _single_curated_label(raw)

        expected = _metadata_transform(mapping, raw, ctx)
        if expected is SKIP_VALUE:
            raise ValueError("Populated CIA source unexpectedly transformed to SKIP_VALUE")

        target_member = mapping["FIELD_RELATIVE_PATH"]
        previous = values_by_member.get(target_member, SKIP_VALUE)
        if previous is not SKIP_VALUE and previous != expected:
            source_conflicts.append({
                "SOURCE_RECORD_ID": source_id,
                "TARGET_MEMBER": target_member,
                "FIRST_VALUE": previous,
                "CONFLICTING_VALUE": expected,
                "CONFLICTING_SOURCE_FIELD": field,
            })
        else:
            values_by_member[target_member] = expected
            sources_by_member.setdefault(target_member, []).append(field)

        label_counts[(target_member, str(resolved_label), str(expected))] += 1
        if str(expected).lower() in {"low", "moderate", "high"}:
            canonical_occurrences += 1
        else:
            legacy_occurrences += 1

        if len(samples) < 20:
            raw_py = _to_python(raw)
            source_ids = None
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
                "EXPECTED_VALUE": expected,
            })

    complete = all(_has_value(values_by_member.get(member)) for member in required_members)
    candidate = candidate_by_record.get(source_id)

    if complete:
        complete_records += 1
        if candidate is None:
            missing_complete_nodes.append(source_id)
            continue

        for member in required_members:
            expected = values_by_member[member]
            actual = candidate.get(member)
            complete_comparisons += 1
            if actual != expected:
                mismatches.append({
                    "SOURCE_RECORD_ID": source_id,
                    "TARGET_MEMBER": member,
                    "SOURCE_FIELDS": sources_by_member.get(member, []),
                    "EXPECTED_OSCAL_VALUE": expected,
                    "ACTUAL_OSCAL_VALUE": actual,
                })
    else:
        # Atomic-assembly contract: incomplete CIA source may be populated, but
        # no partial security-impact-level node is allowed.
        if record_populated:
            incomplete_records += 1
            if len(incomplete_samples) < 20:
                incomplete_samples.append({
                    "CONTENT_ID": source_id,
                    "PRESENT_MEMBERS": sorted(values_by_member),
                    "MISSING_REQUIRED_MEMBERS": sorted(
                        set(required_members) - set(values_by_member)
                    ),
                })
        if candidate is not None:
            unexpected_partial_nodes.append(source_id)

print("CIA_MAPPING_FIELDS =", len(cia_rows))
print("REQUIRED_CIA_MEMBERS =", required_members)
print("SOURCE_RECORDS_CHECKED =", source_records_checked)
print("SECURITY_IMPACT_NODES =", len(candidate_rows))
print("POPULATED_CIA_FIELD_OCCURRENCES =", populated_field_occurrences)
print("RESOLVEDVALUES_OCCURRENCES =", resolved_occurrences)
print("CANONICAL_LOW_MODERATE_HIGH_OCCURRENCES =", canonical_occurrences)
print("REVIEWED_LEGACY_OCCURRENCES =", legacy_occurrences)
print("COMPLETE_CIA_RECORDS =", complete_records)
print("INCOMPLETE_CIA_RECORDS_SKIPPED_BY_DESIGN =", incomplete_records)
print("COMPLETE_TARGET_COMPARISONS =", complete_comparisons)
print("SOURCE_TARGET_CONFLICTS =", len(source_conflicts))
print("MISSING_COMPLETE_NODES =", len(missing_complete_nodes))
print("UNEXPECTED_PARTIAL_NODES =", len(unexpected_partial_nodes))
print("MISMATCHES =", len(mismatches))

print("\nCIA COUNTS BY SOURCE FIELD")
for field in sorted(row["SOURCE_FIELD_NAME"] for row in cia_rows):
    print(f"  {field}: {field_counts[field]}")

print("\nRESOLVED LABEL -> OSCAL VALUE COUNTS")
for (member, label, expected), count in sorted(label_counts.items()):
    print(f"  {member} | {label} -> {expected}: {count}")

print("\nSAMPLE RESOLVED FIELD TRACE")
for item in samples:
    print(
        f'{item["CONTENT_ID"]} | {item["SOURCE_FIELD"]} | '
        f'{item["VALUE_IDS"]} -> {item["RESOLVED_LABEL"]} -> '
        f'{item["TARGET_MEMBER"]}={item["EXPECTED_VALUE"]}'
    )

print("\nSAMPLE INCOMPLETE CIA RECORDS SKIPPED BY ATOMIC ASSEMBLY")
for item in incomplete_samples:
    print(
        f'{item["CONTENT_ID"]} | present={item["PRESENT_MEMBERS"]} | '
        f'missing={item["MISSING_REQUIRED_MEMBERS"]}'
    )

if source_conflicts:
    print("\nFIRST SOURCE TARGET CONFLICT =", source_conflicts[0])
    raise ValueError("Multiple CIA source fields resolve conflicting values for one OSCAL member")

if missing_complete_nodes:
    print("\nFIRST MISSING COMPLETE NODE =", missing_complete_nodes[0])
    raise ValueError("Complete CIA source record did not emit security-impact-level")

if unexpected_partial_nodes:
    print("\nFIRST UNEXPECTED PARTIAL NODE =", unexpected_partial_nodes[0])
    raise ValueError("Incomplete CIA source record emitted a partial security-impact-level")

if mismatches:
    print("\nFIRST COMPLETE-PAYLOAD MISMATCH =", mismatches[0])
    raise ValueError("Complete CIA ResolvedValues do not match candidate OSCAL security-impact payload")

if resolved_occurrences == 0:
    raise ValueError("No Matillion ResolvedValues were observed for populated CIA fields")

if len(candidate_rows) != complete_records:
    raise ValueError("security-impact-level node count does not equal complete CIA source-record count")

print("\nCIA_RESOLVED_VALUES_VALIDATED = True")
