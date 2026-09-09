# Read-only SSP component-reference source-contract extraction
#
# Run this once after Mapper Cell 7 in the same Snowflake notebook session.
# It profiles the six approved Archer component-reference fields so the
# components[] hydrator can implement the recorded CONTENT_ID identity from
# evidence. It prints aggregate counts, object key names, and mapping-contract
# classifications only. It never prints source record IDs, reference values,
# component identifiers, or payloads, and it performs no DML.

from collections import Counter, defaultdict
import hashlib
import math
import re


COMPONENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
COMPONENT_SOURCE_FIELDS = (
    "SUBSYSTEMS",
    "SOFTWARE",
    "HARDWARE",
    "INTERCONNECTIONS",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM",
    "SAP_INTAKE_FORM_INTERCONNECTIONS",
)
COMPONENT_TYPE_TOKENS = (
    "system",
    "software",
    "hardware",
    "interconnection",
)


required_objects = {
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "run_result": globals().get("run_result"),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
}
missing_objects = [
    name for name, value in required_objects.items() if value is None
]
if missing_objects:
    raise RuntimeError(
        "Run Mapper Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_objects)
    )
if str(CONFIG.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
    raise RuntimeError("This extraction requires the SSP mapper model.")
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before extracting the component contract."
    )
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", True):
    raise RuntimeError("This extraction requires a read-only Cell 7 run.")


def _contract_has_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return True


def _contract_kind(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _contract_normalize_key(key):
    return re.sub(r"[^a-z0-9]", "", str(key).strip().lower())


def _contract_scalar(value):
    if value is None or isinstance(value, (bool, dict, list, tuple, set)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    text = str(value).strip()
    return text or None


def _contract_flatten_scalars(value):
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            result.extend(_contract_flatten_scalars(item))
        return result
    scalar = _contract_scalar(value)
    return [scalar] if scalar is not None else []


def _contract_identifier_hash(value):
    return hashlib.sha256(
        ("component-contract-v1|" + value).encode("utf-8")
    ).hexdigest()


CONTENT_ID_KEYS = {"contentid", "contentids"}
GENERIC_ID_KEYS = {"id", "ids", "recordid", "recordids"}
TITLE_KEYS = {"name", "title", "recordname", "displayname"}
DESCRIPTION_KEYS = {"description", "desc", "summary"}
STATUS_KEYS = {"status", "state", "recordstatus"}


def _contract_scan_value(value, stats, key_signatures):
    explicit_content_ids = []
    generic_ids = []
    scalar_reference_ids = []

    def visit(item, top_level=False):
        if isinstance(item, (list, tuple)):
            stats["arrays"] += 1
            for member in item:
                if isinstance(member, dict):
                    visit(member)
                elif isinstance(member, (list, tuple)):
                    visit(member, top_level=top_level)
                elif top_level:
                    scalar = _contract_scalar(member)
                    if scalar is not None:
                        scalar_reference_ids.append(
                            _contract_identifier_hash(scalar)
                        )
                        stats["scalar_reference_members"] += 1
            return

        if not isinstance(item, dict):
            if top_level:
                scalar = _contract_scalar(item)
                if scalar is not None:
                    scalar_reference_ids.append(
                        _contract_identifier_hash(scalar)
                    )
                    stats["scalar_reference_members"] += 1
            return

        stats["objects"] += 1
        normalized_keys = {
            _contract_normalize_key(key): key for key in item
        }
        signature = ",".join(sorted(str(key) for key in item))
        key_signatures[signature or "<empty-object>"] += 1

        local_explicit = []
        local_generic = []
        for key, nested_value in item.items():
            normalized_key = _contract_normalize_key(key)
            if normalized_key in CONTENT_ID_KEYS:
                for scalar in _contract_flatten_scalars(nested_value):
                    local_explicit.append(_contract_identifier_hash(scalar))
            elif normalized_key in GENERIC_ID_KEYS:
                for scalar in _contract_flatten_scalars(nested_value):
                    local_generic.append(_contract_identifier_hash(scalar))

        if local_explicit or local_generic:
            stats["identifier_bearing_objects"] += 1
            if local_explicit:
                stats["objects_with_content_id"] += 1
            elif local_generic:
                stats["objects_with_generic_id_only"] += 1
            if normalized_keys.keys() & TITLE_KEYS:
                stats["identifier_objects_with_title_key"] += 1
            if normalized_keys.keys() & DESCRIPTION_KEYS:
                stats["identifier_objects_with_description_key"] += 1
            if normalized_keys.keys() & STATUS_KEYS:
                stats["identifier_objects_with_status_key"] += 1

        explicit_content_ids.extend(local_explicit)
        generic_ids.extend(local_generic)

        for nested_value in item.values():
            if isinstance(nested_value, (dict, list, tuple)):
                visit(nested_value)

    stats["root_" + _contract_kind(value)] += 1
    visit(value, top_level=True)
    return explicit_content_ids, generic_ids, scalar_reference_ids


mapping_rows_by_field = defaultdict(list)
for mapping_row in CANONICAL_MAPPING_ROWS:
    source_field = str(
        mapping_row.get("SOURCE_FIELD_NAME") or ""
    ).strip()
    owner_path = str(
        mapping_row.get("OWNER_ELEMENT_PATH") or ""
    ).strip()
    if source_field in COMPONENT_SOURCE_FIELDS and owner_path == COMPONENT_PATH:
        mapping_rows_by_field[source_field].append(mapping_row)


field_stats = {field: Counter() for field in COMPONENT_SOURCE_FIELDS}
field_signatures = {field: Counter() for field in COMPONENT_SOURCE_FIELDS}
cross_field_records = 0
cross_field_shared_ids = 0
source_records = 0

for source_row in source_df.to_local_iterator():
    source_records += 1
    source_obj = _parse_source_json(source_row)
    ids_by_field = {}

    for source_field in COMPONENT_SOURCE_FIELDS:
        source_value = resolve_json_path(source_obj, source_field)
        if not _contract_has_value(source_value):
            continue

        stats = field_stats[source_field]
        stats["populated_records"] += 1
        explicit_ids, generic_ids, scalar_ids = _contract_scan_value(
            source_value,
            stats,
            field_signatures[source_field],
        )
        governed_candidates = explicit_ids + scalar_ids
        stats["content_id_occurrences"] += len(explicit_ids)
        stats["scalar_id_occurrences"] += len(scalar_ids)
        stats["generic_id_occurrences"] += len(generic_ids)

        unique_candidates = set(governed_candidates)
        if unique_candidates:
            stats["records_with_governed_id_candidate"] += 1
            stats["governed_unique_ids"] += len(unique_candidates)
            stats["within_field_duplicate_id_occurrences"] += (
                len(governed_candidates) - len(unique_candidates)
            )
            ids_by_field[source_field] = unique_candidates
        else:
            stats["populated_records_without_governed_id_candidate"] += 1

    record_id_fields = defaultdict(set)
    for source_field, identifier_hashes in ids_by_field.items():
        for identifier_hash in identifier_hashes:
            record_id_fields[identifier_hash].add(source_field)
    shared = [
        fields for fields in record_id_fields.values() if len(fields) > 1
    ]
    if shared:
        cross_field_records += 1
        cross_field_shared_ids += len(shared)


print("=== SSP COMPONENT SOURCE CONTRACT ===")
print("Safety: aggregate-only; no identifiers or source values printed")
print("Writes executed: False")
print("Source records scanned:", source_records)
print("Expected reference fields:", len(COMPONENT_SOURCE_FIELDS))
print("Fields with component mapping rows:", len(mapping_rows_by_field))
print("Records with cross-field shared governed IDs:", cross_field_records)
print("Unique governed IDs shared across fields:", cross_field_shared_ids)

for source_field in COMPONENT_SOURCE_FIELDS:
    rows = mapping_rows_by_field[source_field]
    mapping_types = sorted(
        {
            str(row.get("MAPPING_TYPE") or "").strip().upper()
            for row in rows
            if str(row.get("MAPPING_TYPE") or "").strip()
        }
    )
    type_signals = set()
    for row in rows:
        evidence_text = " ".join(
            str(row.get(column) or "")
            for column in (
                "TRANSFORMATION_LOGIC",
                "NOTES",
                "NOTE",
                "COMMENTS",
                "COMMENT",
            )
        ).lower()
        for component_type in COMPONENT_TYPE_TOKENS:
            if re.search(
                r"\b" + re.escape(component_type) + r"\b",
                evidence_text,
            ):
                type_signals.add(component_type)

    stats = field_stats[source_field]
    print("\nFIELD:", source_field)
    print("  Mapping rows:", len(rows))
    print("  Mapping types:", ",".join(mapping_types) or "MISSING")
    print(
        "  Declared component-type signals:",
        ",".join(sorted(type_signals)) or "MISSING",
    )
    print("  Populated records:", stats["populated_records"])
    print(
        "  Records with governed ID candidate:",
        stats["records_with_governed_id_candidate"],
    )
    print(
        "  Populated records without governed ID candidate:",
        stats["populated_records_without_governed_id_candidate"],
    )
    print("  Explicit ContentId occurrences:", stats["content_id_occurrences"])
    print("  Scalar reference occurrences:", stats["scalar_id_occurrences"])
    print("  Generic ID occurrences:", stats["generic_id_occurrences"])
    print(
        "  Within-field duplicate governed ID occurrences:",
        stats["within_field_duplicate_id_occurrences"],
    )
    print("  Identifier-bearing objects:", stats["identifier_bearing_objects"])
    print(
        "  Identifier objects with title-like key:",
        stats["identifier_objects_with_title_key"],
    )
    print(
        "  Identifier objects with description-like key:",
        stats["identifier_objects_with_description_key"],
    )
    print(
        "  Identifier objects with status-like key:",
        stats["identifier_objects_with_status_key"],
    )
    root_types = sorted(
        (key.removeprefix("root_"), count)
        for key, count in stats.items()
        if key.startswith("root_") and count
    )
    print(
        "  Root value types:",
        ",".join(f"{kind}={count}" for kind, count in root_types)
        or "NONE",
    )
    print("  Top object key signatures (keys only):")
    signatures = field_signatures[source_field].most_common(10)
    if not signatures:
        print("    NONE")
    for signature, count in signatures:
        print(f"    {count}: {signature}")

print("\nRESULT: COMPONENT SOURCE CONTRACT EVIDENCE CAPTURED")
print("No database objects or rows were changed.")
