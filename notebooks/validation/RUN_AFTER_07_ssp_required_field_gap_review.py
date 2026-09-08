# Read-only OSCAL SSP v1.2.3 security/status cardinality review
#
# Run this temporary Snowflake Python cell after Mapper V1 Cell 7. It compares
# configured source candidates with generated security-impact/status payloads,
# using aggregate counts only. It never prints record IDs, Archer field names,
# source values, or payloads. It creates no objects and performs no writes.
#
# OSCAL v1.2.3 is a provisional diagnostic target until the project pins an
# OSCAL version in CONFIG. Under v1.2.3, security-impact-level is optional, but
# when emitted all three security-objective child fields are required. Status
# and status.state are required. This cell does not claim whole-SSP conformance.

from collections import Counter, defaultdict
import itertools
import json


PROVISIONAL_OSCAL_VERSION = "1.2.3"

required_review_objects = {
    "CONFIG": globals().get("CONFIG"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "final_edges_df": globals().get("final_edges_df"),
    "source_df": globals().get("source_df"),
    "run_result": globals().get("run_result"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "TRANSIENT_SOURCE_FIELDS": globals().get("TRANSIENT_SOURCE_FIELDS"),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
    "_target_field_name": globals().get("_target_field_name"),
    "col": globals().get("col"),
}
missing_review_objects = [
    name for name, value in required_review_objects.items() if value is None
]
if missing_review_objects:
    raise RuntimeError(
        "Run Mapper V1 Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_review_objects)
    )
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running this review."
    )
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
configured_oscal_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
if (
    configured_oscal_version
    and configured_oscal_version != PROVISIONAL_OSCAL_VERSION
):
    raise RuntimeError(
        "This diagnostic implements OSCAL SSP 1.2.3 cardinality. "
        "CONFIG pins a different OSCAL_VERSION; use a version-specific review."
    )


SECURITY_PATH = (
    "system-security-plan.system-characteristics.security-impact-level"
)
STATUS_PATH = "system-security-plan.system-characteristics.status"
SECURITY_TARGETS = (
    ("security-objective-confidentiality", "C"),
    ("security-objective-integrity", "I"),
    ("security-objective-availability", "A"),
)
SECURITY_FIELDS = tuple(name for name, _ in SECURITY_TARGETS)
STATUS_ALLOWED = {
    "operational",
    "under-development",
    "under-major-modification",
    "disposition",
    "other",
}
SECURITY_ALLOWED_VALUES = {
    "low",
    "moderate",
    "high",
    "fips-199-low",
    "fips-199-moderate",
    "fips-199-high",
    "legacy-loe-a",
    "legacy-loe-b",
    "legacy-loe-c",
    "legacy-loe-c-+-dfars",
    "legacy-loe-d",
    "legacy-loe-d-+-dfars",
}
ALL_MASKS = [
    f"C{c}/I{i}/A{a}"
    for c, i, a in itertools.product((0, 1), repeat=3)
]


def _review_present(value):
    """Treat 0/False as present and blank/empty containers as absent."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _review_security_token(value):
    # Security objectives are strings; normalize only to recognize the
    # explicitly reviewed standard/legacy source label family.
    return "-".join(str(value).strip().lower().replace("_", "-").split())


def _review_payload(value):
    try:
        if value is None:
            return {}, False
        if hasattr(value, "as_dict"):
            value = value.as_dict(recursive=True)
        if isinstance(value, dict):
            return value, False
        if isinstance(value, str):
            parsed = json.loads(value)
            return (parsed, False) if isinstance(parsed, dict) else ({}, True)
        return {}, True
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}, True


def _review_mapping_is_eligible(mapping):
    source_field = str(mapping.get("SOURCE_FIELD_NAME") or "").strip()
    mapping_type = str(mapping.get("MAPPING_TYPE") or "Direct").lower()
    mapping_status = str(mapping.get("STATUS") or "").lower()
    return (
        bool(source_field)
        and source_field not in TRANSIENT_SOURCE_FIELDS
        and "tbd" not in mapping_type
        and "more information" not in mapping_status
    )


def _review_mask(present_fields):
    return "/".join(
        label + ("1" if field in present_fields else "0")
        for field, label in SECURITY_TARGETS
    )


def _print_mask_counter(title, counter):
    print("\n===", title, "===")
    for mask in ALL_MASKS:
        print(mask, "=", counter[mask])


# Group eligible mapping rows by their generated target. Source field names are
# deliberately retained only in memory and are never printed.
target_source_paths = defaultdict(list)
target_mapping_rows = Counter()
for review_mapping in CANONICAL_MAPPING_ROWS:
    if not _review_mapping_is_eligible(review_mapping):
        continue
    owner = str(review_mapping.get("OWNER_ELEMENT_PATH") or "").strip()
    target = _target_field_name(review_mapping)
    key = (owner, target)
    if key not in [
        *((SECURITY_PATH, field) for field in SECURITY_FIELDS),
        (STATUS_PATH, "state"),
    ]:
        continue
    source_path = str(
        review_mapping.get("SOURCE_FIELD_NAME") or ""
    ).strip()
    target_mapping_rows[key] += 1
    if source_path not in target_source_paths[key]:
        target_source_paths[key].append(source_path)


target_population = defaultdict(Counter)
source_present_records = defaultdict(set)
source_pattern_counts = Counter()
source_ids = set()
source_rows_seen = 0
blank_source_ids = 0
duplicate_source_rows = 0
source_parse_errors = 0
source_resolution_errors = 0
source_error_records = set()

for source_row in source_df.to_local_iterator():
    source_rows_seen += 1
    raw_record_id = source_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_record_id is None else str(raw_record_id).strip()
    if not record_id:
        blank_source_ids += 1
        continue
    if record_id in source_ids:
        duplicate_source_rows += 1
        continue
    source_ids.add(record_id)

    try:
        source_object = _parse_source_json(source_row)
    except (TypeError, ValueError, json.JSONDecodeError):
        source_parse_errors += 1
        source_error_records.add(record_id)
        source_object = {}

    unique_paths = {
        path
        for paths in target_source_paths.values()
        for path in paths
    }
    path_presence = {}
    for source_path in unique_paths:
        try:
            path_presence[source_path] = _review_present(
                resolve_json_path(source_object, source_path)
            )
        except (TypeError, ValueError, KeyError, IndexError):
            source_resolution_errors += 1
            source_error_records.add(record_id)
            path_presence[source_path] = False

    for target_key, source_paths in target_source_paths.items():
        populated_candidates = sum(
            1 for path in source_paths if path_presence.get(path, False)
        )
        bucket = (
            "zero-populated-candidates"
            if populated_candidates == 0
            else (
                "one-populated-candidate"
                if populated_candidates == 1
                else "multiple-populated-candidates"
            )
        )
        target_population[target_key][bucket] += 1
        if populated_candidates:
            source_present_records[target_key].add(record_id)

    source_fields_present = {
        field
        for field in SECURITY_FIELDS
        if record_id in source_present_records[(SECURITY_PATH, field)]
    }
    source_pattern_counts[_review_mask(source_fields_present)] += 1


if blank_source_ids or duplicate_source_rows:
    raise RuntimeError(
        "Source identity check failed without displaying IDs: "
        f"blank IDs={blank_source_ids}, duplicate rows={duplicate_source_rows}."
    )


# Ask Snowflake for distinct graph record IDs so the local diagnostic does not
# collect all 51,000+ nodes solely to calculate record coverage.
graph_ids = set()
blank_graph_ids = 0
for graph_row in final_nodes_df.select("SOURCE_RECORD_ID").distinct().to_local_iterator():
    raw_record_id = graph_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_record_id is None else str(raw_record_id).strip()
    if record_id:
        graph_ids.add(record_id)
    else:
        blank_graph_ids += 1


security_payload_by_record = {}
status_payload_by_record = {}
security_node_key_by_record = {}
security_node_counts = Counter()
status_node_counts = Counter()
payload_parse_errors = Counter()
security_payload_error_records = set()
status_payload_error_records = set()

for output_row in final_nodes_df.select(
    "SOURCE_RECORD_ID",
    "NODE_KEY",
    "ELEMENT_PATH",
    "METADATA_JSON",
).filter(
    col("ELEMENT_PATH").in_([SECURITY_PATH, STATUS_PATH])
).to_local_iterator():
    raw_record_id = output_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_record_id is None else str(raw_record_id).strip()
    path = str(output_row["ELEMENT_PATH"])
    payload, parse_error = _review_payload(output_row["METADATA_JSON"])
    if parse_error:
        payload_parse_errors[path] += 1
    if path == SECURITY_PATH:
        security_node_counts[record_id] += 1
        security_payload_by_record.setdefault(record_id, payload)
        security_node_key_by_record.setdefault(record_id, output_row["NODE_KEY"])
        if parse_error:
            security_payload_error_records.add(record_id)
    elif path == STATUS_PATH:
        status_node_counts[record_id] += 1
        status_payload_by_record.setdefault(record_id, payload)
        if parse_error:
            status_payload_error_records.add(record_id)


duplicate_security_nodes = sum(
    count - 1 for count in security_node_counts.values() if count > 1
)
duplicate_status_nodes = sum(
    count - 1 for count in status_node_counts.values() if count > 1
)
if duplicate_security_nodes or duplicate_status_nodes:
    raise RuntimeError(
        "Singleton node check failed without displaying IDs: "
        f"duplicate security nodes={duplicate_security_nodes}, "
        f"duplicate status nodes={duplicate_status_nodes}."
    )


generated_present_records = defaultdict(set)
generated_pattern_counts = Counter()
empty_optional_security_records = set()
complete_security_records = set()
partial_security_records = set()
missing_security_node_records = source_ids - set(security_node_counts)
invalid_security_assembly_records = set(security_payload_error_records)
partial_missing_by_objective = Counter()
partial_source_candidate_gaps = Counter()
partial_output_gaps = Counter()
invalid_security_value_occurrences = 0
missing_status_records = set()
invalid_status_records = set()

for record_id in source_ids:
    security_payload = security_payload_by_record.get(record_id, {})
    output_fields_present = set()
    for field in SECURITY_FIELDS:
        value = security_payload.get(field)
        if isinstance(value, str) and bool(value.strip()):
            output_fields_present.add(field)
            generated_present_records[(SECURITY_PATH, field)].add(record_id)
            if _review_security_token(value) not in SECURITY_ALLOWED_VALUES:
                invalid_security_value_occurrences += 1
                invalid_security_assembly_records.add(record_id)
        elif field in security_payload and value not in (None, ""):
            invalid_security_value_occurrences += 1
            invalid_security_assembly_records.add(record_id)

    generated_pattern_counts[_review_mask(output_fields_present)] += 1
    if record_id in missing_security_node_records:
        pass
    elif record_id in security_payload_error_records:
        pass
    elif not security_payload:
        empty_optional_security_records.add(record_id)
    else:
        if not output_fields_present:
            # A non-empty object with no valid objective is an emitted,
            # invalid partial assembly—not optional absence.
            invalid_security_assembly_records.add(record_id)
        if len(output_fields_present) == len(SECURITY_FIELDS):
            complete_security_records.add(record_id)
        else:
            partial_security_records.add(record_id)
            for field in SECURITY_FIELDS:
                if field in output_fields_present:
                    continue
                partial_missing_by_objective[field] += 1
                source_key = (SECURITY_PATH, field)
                if record_id in source_present_records[source_key]:
                    partial_output_gaps[field] += 1
                else:
                    partial_source_candidate_gaps[field] += 1

    status_payload = status_payload_by_record.get(record_id, {})
    status_state = status_payload.get("state")
    if record_id not in status_node_counts:
        missing_status_records.add(record_id)
    elif record_id in status_payload_error_records:
        invalid_status_records.add(record_id)
    elif not isinstance(status_state, str) or not status_state.strip():
        missing_status_records.add(record_id)
    else:
        valid_other_remarks = (
            status_state != "other"
            or (
                isinstance(status_payload.get("remarks"), str)
                and bool(status_payload.get("remarks").strip())
            )
        )
        if status_state not in STATUS_ALLOWED or not valid_other_remarks:
            invalid_status_records.add(record_id)


security_output_gap_records = set()
for field in SECURITY_FIELDS:
    security_output_gap_records.update(
        source_present_records[(SECURITY_PATH, field)]
        - generated_present_records[(SECURITY_PATH, field)]
    )

status_source_records = source_present_records[(STATUS_PATH, "state")]
status_generated_records = (
    source_ids - missing_status_records - invalid_status_records
)
status_output_gap_records = status_source_records - status_generated_records

missing_security_occurrences = sum(partial_missing_by_objective.values())
missing_status_occurrences = len(missing_status_records)
missing_required_occurrences = (
    missing_security_occurrences + missing_status_occurrences
)
conformance_blocking_records = (
    partial_security_records
    | missing_status_records
    | invalid_status_records
    | invalid_security_assembly_records
    | missing_security_node_records
    | security_output_gap_records
    | status_output_gap_records
    | source_error_records
    | (source_ids - graph_ids)
    | (graph_ids - source_ids)
)
narrow_scope_ready_records = source_ids - conformance_blocking_records

omittable_node_keys = {
    security_node_key_by_record[record_id]
    for record_id in empty_optional_security_records
    if security_node_key_by_record.get(record_id) is not None
}
omittable_incoming_edges = 0
for edge_row in final_edges_df.select(
    "FK_TARGET_ELEMENT_HASH"
).to_local_iterator():
    if edge_row["FK_TARGET_ELEMENT_HASH"] in omittable_node_keys:
        omittable_incoming_edges += 1


print("=" * 78)
print("READ-ONLY OSCAL SSP SECURITY/STATUS CARDINALITY REVIEW")
print("Provisional evaluation target: OSCAL SSP", PROVISIONAL_OSCAL_VERSION)
print("CONFIG-pinned OSCAL version:", CONFIG.get("OSCAL_VERSION", "<not pinned>"))
print("No record IDs, Archer field names, source values, or payloads are shown.")
print("=" * 78)

print("\n=== UNIQUE RECORD OVERLAP ===")
print("Source rows:", source_rows_seen)
print("Unique source records:", len(source_ids))
print("Unique graph records:", len(graph_ids))
print("Source/graph intersection:", len(source_ids & graph_ids))
print("Source-only records:", len(source_ids - graph_ids))
print("Graph-only records:", len(graph_ids - source_ids))
print("Blank graph record IDs:", blank_graph_ids)
print("Unique security-node records:", len(security_node_counts))
print("Source records without a security node:", len(source_ids - set(security_node_counts)))
print("Orphan security-node records:", len(set(security_node_counts) - source_ids))
print("Duplicate security nodes:", duplicate_security_nodes)
print("Duplicate status nodes:", duplicate_status_nodes)
print("Source JSON parse errors:", source_parse_errors)
print("Source path resolution errors:", source_resolution_errors)
print("Security payload parse errors:", payload_parse_errors[SECURITY_PATH])
print("Status payload parse errors:", payload_parse_errors[STATUS_PATH])

print("\n=== CONFIGURED TARGET SOURCE POPULATION ===")
for owner, target in [
    *((SECURITY_PATH, field) for field in SECURITY_FIELDS),
    (STATUS_PATH, "state"),
]:
    key = (owner, target)
    population = target_population[key]
    print(
        "owner=", owner,
        "| target=", target,
        "| configured_mapping_rows=", target_mapping_rows[key],
        "| unique_candidate_paths=", len(target_source_paths[key]),
        "| zero=", population["zero-populated-candidates"],
        "| one=", population["one-populated-candidate"],
        "| multiple=", population["multiple-populated-candidates"],
    )

_print_mask_counter("SECURITY SOURCE PRESENCE PATTERNS", source_pattern_counts)
_print_mask_counter("SECURITY GENERATED PRESENCE PATTERNS", generated_pattern_counts)

print("\n=== SECURITY SOURCE/OUTPUT OVERLAP ===")
for field, label in SECURITY_TARGETS:
    source_set = source_present_records[(SECURITY_PATH, field)]
    output_set = generated_present_records[(SECURITY_PATH, field)] & source_ids
    print(
        label,
        "configured_mapping_rows=", target_mapping_rows[(SECURITY_PATH, field)],
        "| unique_candidate_paths=", len(target_source_paths[(SECURITY_PATH, field)]),
        "| source_present=", len(source_set),
        "| generated_present=", len(output_set),
        "| both=", len(source_set & output_set),
        "| source_only=", len(source_set - output_set),
        "| output_only=", len(output_set - source_set),
        "| neither=", len(source_ids - source_set - output_set),
    )

print("\n=== OSCAL 1.2.3 CARDINALITY CLASSIFICATION ===")
print("Optional absent security-impact assemblies:", len(empty_optional_security_records))
print("Complete security-impact assemblies:", len(complete_security_records))
print("Partial security-impact assemblies:", len(partial_security_records))
print("Missing security structural nodes:", len(missing_security_node_records))
print("Malformed/invalid security assemblies:", len(invalid_security_assembly_records))
for field, label in SECURITY_TARGETS:
    print(label, "missing child occurrences in partial assemblies:", partial_missing_by_objective[field])
    print(label, "with no populated source candidate:", partial_source_candidate_gaps[field])
    print(label, "with source candidate but no generated value:", partial_output_gaps[field])
print("Missing required security-objective occurrences:", missing_security_occurrences)
print("Invalid security value occurrences:", invalid_security_value_occurrences)
print("Missing required status.state occurrences:", missing_status_occurrences)
print("Invalid populated status assemblies:", len(invalid_status_records))
print("Missing required field occurrences in emitted/required assemblies:", missing_required_occurrences)

print("\n=== UNIQUE RECORD IMPACT ===")
print("Records with partial security-impact assembly:", len(partial_security_records))
print("Records with missing required status.state:", len(missing_status_records))
print("Records in both of those groups:", len(partial_security_records & missing_status_records))
print("Records with a security source/output discrepancy:", len(security_output_gap_records))
print("Records with a status source/output discrepancy:", len(status_output_gap_records))
print("Unique records requiring review in this narrow check:", len(conformance_blocking_records))
print("Records ready within only this narrow check:", len(narrow_scope_ready_records))
print("Records with source parse/resolution errors:", len(source_error_records))

run_nodes = int(run_result.get("nodes", 0) or 0)
run_edges = int(run_result.get("edges", 0) or 0)
print("\n=== OPTIONAL-OMISSION PROJECTION ONLY ===")
print("Current graph nodes:", run_nodes)
print("Current graph edges:", run_edges)
print("No-objective security nodes eligible for final-output omission:", len(empty_optional_security_records))
print("Actual incoming edges to those nodes:", omittable_incoming_edges)
print("Projected nodes if graph policy also omits them:", run_nodes - len(omittable_node_keys))
print("Projected edges if graph policy also omits them:", run_edges - omittable_incoming_edges)
print("The mapper currently materializes structural {} nodes; this is not a requested graph change.")

print("\n=== INTERPRETATION GATES ===")
print("1. Empty security-impact is optional under provisional OSCAL 1.2.3 and is not a required-field gap.")
print("2. If security-impact is emitted, all C/I/A children are required; partial assemblies need remediation or whole-assembly omission.")
print("3. status.state is required; missing or invalid states block the affected record.")
print("4. Source-only means mapping/transform review; output-only may be a legitimate derived value.")
print("5. This narrow check does not prove whole-document SSP conformance or write readiness.")
print("6. The repository must pin its OSCAL version before production conformance decisions.")

print("\n=== SAFETY RESULT ===")
print("EXECUTE_WRITES =", CONFIG.get("EXECUTE_WRITES", False))
print("No DIM/FACT writes or permanent objects were created.")
if blank_graph_ids or conformance_blocking_records or missing_required_occurrences:
    print("RESULT: REVIEW REQUIRED; WRITES REMAIN BLOCKED")
else:
    print("RESULT: NARROW SECURITY/STATUS CHECK PASSED; FULL SSP REVIEW STILL REQUIRED")

