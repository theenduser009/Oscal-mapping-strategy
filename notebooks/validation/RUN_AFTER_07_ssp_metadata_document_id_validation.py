# Read-only SSP metadata document-id validation
#
# Run this once after Mapper Cell 7 in the same Snowflake notebook session.
# It proves the exact TRACKING_ID-to-document-identifier mapping in the
# in-memory canonical graph. It performs no SQL, creates no objects, and
# writes no data. Output is aggregate-only; identifiers, payloads, and source
# record IDs are never printed.

from collections import Counter
import json


TARGET_PATH = "system-security-plan.metadata.document-ids[]"
TARGET_OSCAL_PATH = TARGET_PATH + ".identifier"
TARGET_FIELD = "identifier"
SOURCE_FIELD = "TRACKING_ID"
EXPECTED_MAPPING_TYPE = "direct"
EXPECTED_INSTANCE_KEY = "singleton"


required_objects = {
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "run_result": globals().get("run_result"),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
    "_has_value": globals().get("_has_value"),
    "transform_document_identifier": globals().get(
        "transform_document_identifier"
    ),
}
missing_object_count = sum(
    value is None for value in required_objects.values()
)
if missing_object_count:
    raise RuntimeError(
        "Run Mapper Cells 1 through 7 first. Missing notebook state count: "
        + str(missing_object_count)
    )

if str(CONFIG.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
    raise RuntimeError("This validation requires the SSP model.")
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running this validation."
    )
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", True):
    raise RuntimeError("This validation requires a read-only Cell 7 run.")


def _clean(value):
    return "" if value is None else str(value).strip()


def _payload_object(value):
    try:
        if hasattr(value, "as_dict"):
            value = value.as_dict(recursive=True)
        if isinstance(value, dict):
            return value, False
        if isinstance(value, str):
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed, False
        return {}, True
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}, True


contract_rows = [
    row
    for row in CANONICAL_MAPPING_ROWS
    if _clean(row.get("SOURCE_FIELD_NAME")) == SOURCE_FIELD
    or _clean(row.get("OWNER_ELEMENT_PATH")) == TARGET_PATH
]
mapping_contract_valid = False
if len(contract_rows) == 1:
    contract_row = contract_rows[0]
    mapping_contract_valid = all(
        (
            _clean(contract_row.get("SOURCE_FIELD_NAME")) == SOURCE_FIELD,
            _clean(contract_row.get("OWNER_ELEMENT_PATH")) == TARGET_PATH,
            _clean(contract_row.get("OSCAL_ELEMENT_PATH"))
            == TARGET_OSCAL_PATH,
            _clean(contract_row.get("OSCAL_FIELD_NAME")) == TARGET_FIELD,
            _clean(contract_row.get("MAPPING_TYPE")).lower()
            == EXPECTED_MAPPING_TYPE,
        )
    )

print("=" * 72)
print("SSP METADATA DOCUMENT-ID READ-ONLY VALIDATION")
print("=" * 72)
print("Document-id mapping rows:", len(contract_rows))
print("Mapping contract valid:", mapping_contract_valid)
if not mapping_contract_valid:
    raise RuntimeError("Document-id mapping contract validation failed.")


source_stats = Counter()
source_ids = set()
expected_identifiers = {}

for row in source_df.select(
    "SOURCE_RECORD_ID",
    "CURATED_JSON",
).to_local_iterator():
    source_stats["ROWS"] += 1
    source_record_id = _clean(row["SOURCE_RECORD_ID"])
    if not source_record_id:
        source_stats["BLANK_IDS"] += 1
        continue
    if source_record_id in source_ids:
        source_stats["DUPLICATE_IDS"] += 1
        continue
    source_ids.add(source_record_id)

    try:
        source_obj = _parse_source_json(row)
        source_value = resolve_json_path(source_obj, SOURCE_FIELD)
    except Exception:
        source_stats["PARSE_ERRORS"] += 1
        continue

    if not _has_value(source_value):
        source_stats["ABSENT_VALUES"] += 1
        continue

    source_stats["POPULATED_VALUES"] += 1
    try:
        expected_identifiers[source_record_id] = (
            transform_document_identifier(source_value)
        )
    except (TypeError, ValueError):
        source_stats["INVALID_VALUES"] += 1

if not source_stats["ROWS"]:
    raise RuntimeError("Source input is empty.")


graph_source_ids = set()
graph_stats = Counter()
document_node_counts = Counter()

for row in final_nodes_df.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "INSTANCE_KEY",
    "METADATA_JSON",
).to_local_iterator():
    source_record_id = _clean(row["SOURCE_RECORD_ID"])
    if not source_record_id:
        graph_stats["BLANK_SOURCE_IDS"] += 1
    else:
        graph_source_ids.add(source_record_id)

    if _clean(row["ELEMENT_PATH"]) != TARGET_PATH:
        continue

    graph_stats["DOCUMENT_NODES"] += 1
    document_node_counts[source_record_id] += 1
    if source_record_id not in expected_identifiers:
        graph_stats["UNEXPECTED_NODES"] += 1

    if _clean(row["INSTANCE_KEY"]) != EXPECTED_INSTANCE_KEY:
        graph_stats["NON_SINGLETON_NODES"] += 1

    payload, malformed = _payload_object(row["METADATA_JSON"])
    if malformed:
        graph_stats["MALFORMED_PAYLOADS"] += 1
        continue

    if set(payload) != {TARGET_FIELD}:
        graph_stats["UNEXPECTED_PAYLOAD_SHAPES"] += 1
    if TARGET_FIELD not in payload:
        graph_stats["MISSING_IDENTIFIERS"] += 1
        continue

    actual_identifier = payload[TARGET_FIELD]
    if not isinstance(actual_identifier, str):
        graph_stats["NON_STRING_IDENTIFIERS"] += 1
    elif not actual_identifier.strip():
        graph_stats["BLANK_IDENTIFIERS"] += 1
    elif (
        source_record_id in expected_identifiers
        and actual_identifier == expected_identifiers[source_record_id]
    ):
        graph_stats["EXACT_MATCHES"] += 1
    else:
        graph_stats["VALUE_MISMATCHES"] += 1


missing_graph_records = source_ids - graph_source_ids
orphan_graph_records = graph_source_ids - source_ids
missing_document_nodes = sum(
    1
    for source_record_id in expected_identifiers
    if document_node_counts[source_record_id] == 0
)
duplicate_document_nodes = sum(
    count - 1
    for source_record_id, count in document_node_counts.items()
    if source_record_id in expected_identifiers and count > 1
)

result = {
    "SOURCE_ROWS": source_stats["ROWS"],
    "UNIQUE_SOURCE_RECORDS": len(source_ids),
    "BLANK_SOURCE_IDS": source_stats["BLANK_IDS"],
    "DUPLICATE_SOURCE_IDS": source_stats["DUPLICATE_IDS"],
    "SOURCE_PARSE_ERRORS": source_stats["PARSE_ERRORS"],
    "POPULATED_TRACKING_IDS": source_stats["POPULATED_VALUES"],
    "ABSENT_TRACKING_IDS": source_stats["ABSENT_VALUES"],
    "INVALID_TRACKING_IDS": source_stats["INVALID_VALUES"],
    "GRAPH_SOURCE_RECORDS": len(graph_source_ids),
    "BLANK_GRAPH_SOURCE_IDS": graph_stats["BLANK_SOURCE_IDS"],
    "MISSING_GRAPH_RECORDS": len(missing_graph_records),
    "ORPHAN_GRAPH_RECORDS": len(orphan_graph_records),
    "EXPECTED_DOCUMENT_ID_NODES": len(expected_identifiers),
    "DOCUMENT_ID_NODES": graph_stats["DOCUMENT_NODES"],
    "MISSING_DOCUMENT_ID_NODES": missing_document_nodes,
    "UNEXPECTED_DOCUMENT_ID_NODES": graph_stats["UNEXPECTED_NODES"],
    "DUPLICATE_DOCUMENT_ID_NODES": duplicate_document_nodes,
    "NON_SINGLETON_DOCUMENT_ID_NODES": graph_stats["NON_SINGLETON_NODES"],
    "MALFORMED_PAYLOADS": graph_stats["MALFORMED_PAYLOADS"],
    "UNEXPECTED_PAYLOAD_SHAPES": graph_stats[
        "UNEXPECTED_PAYLOAD_SHAPES"
    ],
    "MISSING_IDENTIFIERS": graph_stats["MISSING_IDENTIFIERS"],
    "NON_STRING_IDENTIFIERS": graph_stats["NON_STRING_IDENTIFIERS"],
    "BLANK_IDENTIFIERS": graph_stats["BLANK_IDENTIFIERS"],
    "VALUE_MISMATCHES": graph_stats["VALUE_MISMATCHES"],
    "EXACT_IDENTIFIER_MATCHES": graph_stats["EXACT_MATCHES"],
    "WRITES_EXECUTED": False,
}

failure_keys = (
    "BLANK_SOURCE_IDS",
    "DUPLICATE_SOURCE_IDS",
    "SOURCE_PARSE_ERRORS",
    "INVALID_TRACKING_IDS",
    "BLANK_GRAPH_SOURCE_IDS",
    "MISSING_GRAPH_RECORDS",
    "ORPHAN_GRAPH_RECORDS",
    "MISSING_DOCUMENT_ID_NODES",
    "UNEXPECTED_DOCUMENT_ID_NODES",
    "DUPLICATE_DOCUMENT_ID_NODES",
    "NON_SINGLETON_DOCUMENT_ID_NODES",
    "MALFORMED_PAYLOADS",
    "UNEXPECTED_PAYLOAD_SHAPES",
    "MISSING_IDENTIFIERS",
    "NON_STRING_IDENTIFIERS",
    "BLANK_IDENTIFIERS",
    "VALUE_MISMATCHES",
)
failure_count = sum(result[key] for key in failure_keys)
if result["DOCUMENT_ID_NODES"] != result["EXPECTED_DOCUMENT_ID_NODES"]:
    failure_count += 1
if result["EXACT_IDENTIFIER_MATCHES"] != result[
    "EXPECTED_DOCUMENT_ID_NODES"
]:
    failure_count += 1

result["FAILURE_COUNT"] = failure_count
result["RESULT"] = "PASSED" if failure_count == 0 else "FAILED"

print("Source rows:", result["SOURCE_ROWS"])
print("Unique source records:", result["UNIQUE_SOURCE_RECORDS"])
print("Blank source record IDs:", result["BLANK_SOURCE_IDS"])
print("Duplicate source record IDs:", result["DUPLICATE_SOURCE_IDS"])
print("Source parse errors:", result["SOURCE_PARSE_ERRORS"])
print("Populated TRACKING_ID values:", result["POPULATED_TRACKING_IDS"])
print("Absent TRACKING_ID values:", result["ABSENT_TRACKING_IDS"])
print("Invalid TRACKING_ID values:", result["INVALID_TRACKING_IDS"])
print("Graph source records:", result["GRAPH_SOURCE_RECORDS"])
print("Blank graph source record IDs:", result["BLANK_GRAPH_SOURCE_IDS"])
print("Missing graph records:", result["MISSING_GRAPH_RECORDS"])
print("Orphan graph records:", result["ORPHAN_GRAPH_RECORDS"])
print("Expected document-id nodes:", result["EXPECTED_DOCUMENT_ID_NODES"])
print("Generated document-id nodes:", result["DOCUMENT_ID_NODES"])
print("Missing document-id nodes:", result["MISSING_DOCUMENT_ID_NODES"])
print("Unexpected document-id nodes:", result["UNEXPECTED_DOCUMENT_ID_NODES"])
print("Duplicate document-id nodes:", result["DUPLICATE_DOCUMENT_ID_NODES"])
print(
    "Non-singleton document-id nodes:",
    result["NON_SINGLETON_DOCUMENT_ID_NODES"],
)
print("Malformed document-id payloads:", result["MALFORMED_PAYLOADS"])
print("Unexpected payload shapes:", result["UNEXPECTED_PAYLOAD_SHAPES"])
print("Missing identifiers:", result["MISSING_IDENTIFIERS"])
print("Non-string identifiers:", result["NON_STRING_IDENTIFIERS"])
print("Blank identifiers:", result["BLANK_IDENTIFIERS"])
print("Identifier value mismatches:", result["VALUE_MISMATCHES"])
print("Exact identifier matches:", result["EXACT_IDENTIFIER_MATCHES"])
print("Validation performed writes: False")
print("RESULT:", result["RESULT"])

if failure_count:
    raise RuntimeError(
        "Metadata document-id validation failed; aggregate failure count: "
        + str(failure_count)
    )


metadata_document_id_validation_result = result
