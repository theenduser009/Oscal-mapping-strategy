# Read-only OSCAL SSP v1.2.3 minimum-required-scope audit
#
# Run this temporary Snowflake Python cell after Mapper V1 Cell 7. It checks
# the generated graph against the minimum required SSP structure and fields
# identified in the NIST OSCAL 1.2.3 metaschemas. It reports aggregate counts
# only: no source record IDs, Archer field names, source values, or payloads.
# It creates no objects and performs no DIM or FACT writes.
#
# This is a first-tier contract audit, not assembled-document validation.
# Passing it would not replace OSCAL JSON schema and constraint validation.

from collections import Counter, defaultdict
import json
import uuid


EXPECTED_OSCAL_VERSION = "1.2.3"

required_audit_objects = {
    "CONFIG": globals().get("CONFIG"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "final_edges_df": globals().get("final_edges_df"),
    "source_df": globals().get("source_df"),
    "run_result": globals().get("run_result"),
    "active_registry_paths": globals().get("active_registry_paths"),
    "MAPPINGS_BY_ELEMENT_PATH": globals().get("MAPPINGS_BY_ELEMENT_PATH"),
    "col": globals().get("col"),
}
missing_audit_objects = [
    name for name, value in required_audit_objects.items() if value is None
]
if missing_audit_objects:
    raise RuntimeError(
        "Run Mapper V1 Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_audit_objects)
    )
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running this audit."
    )
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", False):
    raise RuntimeError("This audit requires a Cell 7 read-only run.")

configured_oscal_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
if (
    configured_oscal_version
    and configured_oscal_version != EXPECTED_OSCAL_VERSION
):
    raise RuntimeError(
        "This audit implements OSCAL SSP 1.2.3, but CONFIG pins a different "
        "OSCAL_VERSION. Use a validator for the configured version."
    )


ROOT_PATH = "system-security-plan"
METADATA_PATH = ROOT_PATH + ".metadata"
IMPORT_PROFILE_PATH = ROOT_PATH + ".import-profile"
CHARACTERISTICS_PATH = ROOT_PATH + ".system-characteristics"
SYSTEM_IDS_PATH = CHARACTERISTICS_PATH + ".system-ids[]"
SYSTEM_INFORMATION_PATH = CHARACTERISTICS_PATH + ".system-information"
INFORMATION_TYPES_PATH = SYSTEM_INFORMATION_PATH + ".information-types[]"
SECURITY_IMPACT_PATH = CHARACTERISTICS_PATH + ".security-impact-level"
STATUS_PATH = CHARACTERISTICS_PATH + ".status"
AUTHORIZATION_BOUNDARY_PATH = CHARACTERISTICS_PATH + ".authorization-boundary"
SYSTEM_IMPLEMENTATION_PATH = ROOT_PATH + ".system-implementation"
COMPONENTS_PATH = SYSTEM_IMPLEMENTATION_PATH + ".components[]"
CONTROL_IMPLEMENTATION_PATH = ROOT_PATH + ".control-implementation"
IMPLEMENTED_REQUIREMENTS_PATH = (
    CONTROL_IMPLEMENTATION_PATH + ".implemented-requirements[]"
)

EXACT_ONE_PATHS = (
    ROOT_PATH,
    METADATA_PATH,
    IMPORT_PROFILE_PATH,
    CHARACTERISTICS_PATH,
    SYSTEM_INFORMATION_PATH,
    STATUS_PATH,
    AUTHORIZATION_BOUNDARY_PATH,
    SYSTEM_IMPLEMENTATION_PATH,
    CONTROL_IMPLEMENTATION_PATH,
)
ONE_OR_MORE_PATHS = (
    SYSTEM_IDS_PATH,
    INFORMATION_TYPES_PATH,
    COMPONENTS_PATH,
    IMPLEMENTED_REQUIREMENTS_PATH,
)
REQUIRED_PATHS = EXACT_ONE_PATHS + ONE_OR_MORE_PATHS

SYSTEM_STATUS_ALLOWED = {
    "operational",
    "under-development",
    "under-major-modification",
    "disposition",
    "other",
}
COMPONENT_STATUS_ALLOWED = {
    "under-development",
    "operational",
    "disposition",
    "other",
}


def _audit_payload(value):
    """Return (object, error); only JSON objects are valid node payloads."""
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


def _nested_value(payload, dotted_name):
    current = payload
    for token in dotted_name.split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def _nonblank_text(value):
    return isinstance(value, str) and bool(value.strip())


def _uuid_text(value):
    if not _nonblank_text(value):
        return False
    try:
        uuid.UUID(value.strip())
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _system_status_state(value):
    return _nonblank_text(value) and value.strip() in SYSTEM_STATUS_ALLOWED


def _component_status_state(value):
    return _nonblank_text(value) and value.strip() in COMPONENT_STATUS_ALLOWED


def _pinned_version(value):
    return _nonblank_text(value) and value.strip() == EXPECTED_OSCAL_VERSION


# field name -> validator. UUID is read from the graph column; every other
# field is read from METADATA_JSON, including nested fields such as status.state.
FIELD_RULES = {
    ROOT_PATH: (("OSCAL_UUID", _uuid_text, "column"),),
    METADATA_PATH: (
        ("title", _nonblank_text, "payload"),
        ("last-modified", _nonblank_text, "payload"),
        ("version", _nonblank_text, "payload"),
        ("oscal-version", _pinned_version, "payload"),
    ),
    IMPORT_PROFILE_PATH: (("href", _nonblank_text, "payload"),),
    CHARACTERISTICS_PATH: (
        ("system-name", _nonblank_text, "payload"),
        ("description", _nonblank_text, "payload"),
    ),
    SYSTEM_IDS_PATH: (("id", _nonblank_text, "payload"),),
    INFORMATION_TYPES_PATH: (
        ("title", _nonblank_text, "payload"),
        ("description", _nonblank_text, "payload"),
    ),
    STATUS_PATH: (("state", _system_status_state, "payload"),),
    AUTHORIZATION_BOUNDARY_PATH: (
        ("description", _nonblank_text, "payload"),
    ),
    COMPONENTS_PATH: (
        ("OSCAL_UUID", _uuid_text, "column"),
        ("type", _nonblank_text, "payload"),
        ("title", _nonblank_text, "payload"),
        ("description", _nonblank_text, "payload"),
        ("status.state", _component_status_state, "payload"),
    ),
    CONTROL_IMPLEMENTATION_PATH: (
        ("description", _nonblank_text, "payload"),
    ),
    IMPLEMENTED_REQUIREMENTS_PATH: (
        ("OSCAL_UUID", _uuid_text, "column"),
        ("control-id", _nonblank_text, "payload"),
    ),
}


# Source identity is retained only in memory. Nothing below prints an ID.
source_ids = set()
source_rows = 0
blank_source_ids = 0
duplicate_source_rows = 0
for source_row in source_df.select("SOURCE_RECORD_ID").to_local_iterator():
    source_rows += 1
    raw_id = source_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_id is None else str(raw_id).strip()
    if not record_id:
        blank_source_ids += 1
    elif record_id in source_ids:
        duplicate_source_rows += 1
    else:
        source_ids.add(record_id)

if blank_source_ids or duplicate_source_rows or not source_ids:
    raise RuntimeError(
        "Source identity check failed without displaying IDs: "
        f"rows={source_rows}, unique={len(source_ids)}, "
        f"blank={blank_source_ids}, duplicate={duplicate_source_rows}."
    )

graph_ids = set()
blank_graph_ids = 0
for graph_row in (
    final_nodes_df.select("SOURCE_RECORD_ID").distinct().to_local_iterator()
):
    raw_id = graph_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_id is None else str(raw_id).strip()
    if record_id:
        graph_ids.add(record_id)
    else:
        blank_graph_ids += 1


node_counts_by_path = Counter()
records_by_path = defaultdict(set)
record_node_counts = defaultdict(Counter)
payload_errors_by_path = Counter()
payload_error_records = defaultdict(set)
field_counts = defaultdict(lambda: Counter(valid=0, missing=0, invalid=0))
field_block_records = defaultdict(set)
fully_valid_node_counts = defaultdict(Counter)

required_nodes_df = final_nodes_df.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "OSCAL_UUID",
    "METADATA_JSON",
).filter(col("ELEMENT_PATH").in_(list(REQUIRED_PATHS)))

for node_row in required_nodes_df.to_local_iterator():
    raw_id = node_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_id is None else str(raw_id).strip()
    path = str(node_row["ELEMENT_PATH"] or "").strip()
    if not record_id or path not in REQUIRED_PATHS:
        continue

    node_counts_by_path[path] += 1
    records_by_path[path].add(record_id)
    record_node_counts[path][record_id] += 1
    payload, payload_error = _audit_payload(node_row["METADATA_JSON"])
    if payload_error:
        payload_errors_by_path[path] += 1
        payload_error_records[path].add(record_id)

    node_is_fully_valid = not payload_error
    for field_name, validator, location in FIELD_RULES.get(path, ()):
        value = (
            node_row[field_name]
            if location == "column"
            else _nested_value(payload, field_name)
        )
        is_present = value is not None and (
            not isinstance(value, str) or bool(value.strip())
        )
        if not is_present:
            field_counts[(path, field_name)]["missing"] += 1
            field_block_records[path].add(record_id)
            node_is_fully_valid = False
        elif validator(value):
            field_counts[(path, field_name)]["valid"] += 1
        else:
            field_counts[(path, field_name)]["invalid"] += 1
            field_block_records[path].add(record_id)
            node_is_fully_valid = False

    if path == STATUS_PATH and payload.get("state") == "other":
        conditional_field = "remarks (required when state=other)"
        if _nonblank_text(payload.get("remarks")):
            field_counts[(path, conditional_field)]["valid"] += 1
        else:
            field_counts[(path, conditional_field)]["missing"] += 1
            field_block_records[path].add(record_id)
            node_is_fully_valid = False

    if payload_error:
        field_block_records[path].add(record_id)
    if node_is_fully_valid:
        fully_valid_node_counts[path][record_id] += 1


registered_paths = set(str(path).strip() for path in active_registry_paths)
mapped_owner_paths = set(str(path).strip() for path in MAPPINGS_BY_ELEMENT_PATH)
registry_missing_paths = set(REQUIRED_PATHS) - registered_paths
mapping_owner_missing_paths = set(REQUIRED_PATHS) - mapped_owner_paths

identity_gate_passed = (
    not blank_graph_ids
    and not (source_ids - graph_ids)
    and not (graph_ids - source_ids)
)
contract_block_records = set(source_ids - graph_ids)
path_block_records = defaultdict(set)

for path in EXACT_ONE_PATHS:
    for record_id in source_ids:
        if record_node_counts[path][record_id] != 1:
            path_block_records[path].add(record_id)
    contract_block_records.update(path_block_records[path])

for path in ONE_OR_MORE_PATHS:
    for record_id in source_ids:
        if record_node_counts[path][record_id] < 1:
            path_block_records[path].add(record_id)
        elif fully_valid_node_counts[path][record_id] < record_node_counts[path][record_id]:
            # Every emitted member of a required collection must itself be valid.
            field_block_records[path].add(record_id)
    contract_block_records.update(path_block_records[path])

for path in REQUIRED_PATHS:
    contract_block_records.update(field_block_records[path])
    contract_block_records.update(payload_error_records[path])
    if path in registry_missing_paths:
        contract_block_records.update(source_ids)

ready_records = source_ids - contract_block_records
contract_passed = (
    identity_gate_passed and len(ready_records) == len(source_ids)
)


print("=" * 78)
print("READ-ONLY OSCAL SSP 1.2.3 MINIMUM-REQUIRED-SCOPE AUDIT")
print("Validator contract: OSCAL SSP", EXPECTED_OSCAL_VERSION)
print(
    "Session CONFIG OSCAL version:",
    configured_oscal_version or "<session predates repository pin>",
)
print("No record IDs, Archer field names, source values, or payloads are shown.")
print("=" * 78)

print("\n=== RUN AND IDENTITY GATES ===")
print("Cell 7 graph validation passed:", bool(run_result.get("validation_passed")))
print(
    "Cell 7 pre-write validation passed:",
    bool(run_result.get("pre_write_validation_passed")),
)
print("Writes executed:", bool(run_result.get("writes_executed", False)))
print("Source rows:", source_rows)
print("Unique source records:", len(source_ids))
print("Unique graph records:", len(graph_ids))
print("Source/graph intersection:", len(source_ids & graph_ids))
print("Source-only records:", len(source_ids - graph_ids))
print("Graph-only records:", len(graph_ids - source_ids))
print("Blank graph record IDs:", blank_graph_ids)
print("Source/graph identity gate passed:", identity_gate_passed)

print("\n=== REQUIRED PATH COVERAGE ===")
for path in REQUIRED_PATHS:
    cardinality = "exactly-one" if path in EXACT_ONE_PATHS else "one-or-more"
    duplicate_excess = sum(
        max(0, count - 1) for count in record_node_counts[path].values()
    )
    print(
        "path=", path,
        "| cardinality=", cardinality,
        "| registry=", "present" if path in registered_paths else "MISSING",
        "| mapping_owner=", "present" if path in mapped_owner_paths else "absent",
        "| nodes=", node_counts_by_path[path],
        "| source_coverage=", len(records_by_path[path] & source_ids),
        "| missing_source_records=", len(source_ids - records_by_path[path]),
        "| cardinality_blocked_records=", len(path_block_records[path]),
        "| duplicate_excess_nodes=", duplicate_excess,
        "| malformed_payloads=", payload_errors_by_path[path],
    )

print("\n=== REQUIRED FIELD COVERAGE ===")
for path in REQUIRED_PATHS:
    rules = FIELD_RULES.get(path, ())
    if not rules:
        print("path=", path, "| required_node_fields=none")
        continue
    for field_name, _validator, location in rules:
        counts = field_counts[(path, field_name)]
        print(
            "path=", path,
            "| field=", field_name,
            "| location=", location,
            "| valid=", counts["valid"],
            "| missing=", counts["missing"],
            "| invalid=", counts["invalid"],
        )
    if path == STATUS_PATH:
        conditional_field = "remarks (required when state=other)"
        counts = field_counts[(path, conditional_field)]
        print(
            "path=", path,
            "| field=", conditional_field,
            "| location= payload",
            "| valid=", counts["valid"],
            "| missing=", counts["missing"],
            "| invalid=", counts["invalid"],
        )
    print(
        "path=", path,
        "| records_blocked_by_fields_or_payload=",
        len(field_block_records[path] | payload_error_records[path]),
    )

print("\n=== STATIC SCOPE SUMMARY ===")
print("Required paths in minimum contract:", len(REQUIRED_PATHS))
print("Required paths present in registry:", len(set(REQUIRED_PATHS) & registered_paths))
print("Required paths missing from registry:", len(registry_missing_paths))
print("Required paths with mapping owner:", len(set(REQUIRED_PATHS) & mapped_owner_paths))
print("Required paths without mapping owner:", len(mapping_owner_missing_paths))
print("Mapping-owner absence is evidence only; path/field results decide blocking.")

print("\n=== CURRENT MINIMUM CONTRACT RESULT ===")
print("Unique source records evaluated:", len(source_ids))
print("Records blocked by minimum required structure/fields:", len(contract_block_records))
print("Records meeting the current minimum contract:", len(ready_records))
print(
    "Result:",
    "PASS" if contract_passed else "NOT READY",
)
print("This audit never authorizes writes.")
print(
    "Even a PASS requires assembled OSCAL JSON schema and constraint "
    "validation before any write decision."
)

