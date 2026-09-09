# Read-only SSP metadata.oscal-version validation
#
# Run this once after Mapper Cell 7 in the same Snowflake notebook session.
# It validates the in-memory canonical graph only. It performs no SQL, creates
# no objects, and writes no data. Output is limited to aggregate counts and
# result flags; source identifiers and payload values are never printed.

from collections import Counter
import json


METADATA_PATH = "system-security-plan.metadata"
METADATA_INSTANCE_KEY = "singleton"
OSCAL_VERSION_FIELD = "oscal-version"


required_objects = {
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "run_result": globals().get("run_result"),
}
missing_objects = [
    name for name, value in required_objects.items() if value is None
]
if missing_objects:
    raise RuntimeError(
        "Run Mapper Cells 1 through 7 first. Missing notebook state count: "
        + str(len(missing_objects))
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

configured_version = CONFIG.get("OSCAL_VERSION")
if (
    not isinstance(configured_version, str)
    or not configured_version.strip()
    or configured_version != configured_version.strip()
):
    raise RuntimeError(
        "CONFIG OSCAL_VERSION must be a nonblank, whitespace-normalized string."
    )


def _clean_identifier(value):
    if value is None:
        return ""
    return str(value).strip()


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


source_ids = set()
source_rows = 0
blank_source_ids = 0
duplicate_source_ids = 0
for row in source_df.select("SOURCE_RECORD_ID").to_local_iterator():
    source_rows += 1
    source_record_id = _clean_identifier(row["SOURCE_RECORD_ID"])
    if not source_record_id:
        blank_source_ids += 1
    elif source_record_id in source_ids:
        duplicate_source_ids += 1
    else:
        source_ids.add(source_record_id)

if not source_rows:
    raise RuntimeError("Source input is empty.")
if blank_source_ids or duplicate_source_ids:
    raise RuntimeError(
        "Source identity validation failed: blank="
        + str(blank_source_ids)
        + ", duplicate="
        + str(duplicate_source_ids)
    )


graph_source_ids = set()
blank_graph_source_ids = 0
metadata_node_counts = Counter()
metadata_nodes = []

for row in final_nodes_df.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "INSTANCE_KEY",
    "METADATA_JSON",
).to_local_iterator():
    source_record_id = _clean_identifier(row["SOURCE_RECORD_ID"])
    if not source_record_id:
        blank_graph_source_ids += 1
    else:
        graph_source_ids.add(source_record_id)

    element_path = _clean_identifier(row["ELEMENT_PATH"])
    if element_path == METADATA_PATH:
        metadata_node_counts[source_record_id] += 1
        metadata_nodes.append(
            (
                source_record_id,
                _clean_identifier(row["INSTANCE_KEY"]),
                row["METADATA_JSON"],
            )
        )

missing_graph_records = source_ids - graph_source_ids
orphan_graph_records = graph_source_ids - source_ids
if blank_graph_source_ids or missing_graph_records or orphan_graph_records:
    raise RuntimeError(
        "Source/graph identity mismatch: blank_graph_ids="
        + str(blank_graph_source_ids)
        + ", missing_graph_records="
        + str(len(missing_graph_records))
        + ", orphan_graph_records="
        + str(len(orphan_graph_records))
    )


missing_metadata_nodes = source_ids - set(metadata_node_counts)
orphan_metadata_nodes = set(metadata_node_counts) - source_ids
duplicate_metadata_nodes = sum(
    count - 1 for count in metadata_node_counts.values() if count > 1
)

stats = Counter()
for source_record_id, instance_key, payload_value in metadata_nodes:
    if source_record_id not in source_ids:
        continue
    if instance_key != METADATA_INSTANCE_KEY:
        stats["NON_SINGLETON_INSTANCE"] += 1

    payload, malformed = _payload_object(payload_value)
    if malformed:
        stats["MALFORMED_PAYLOAD"] += 1
        continue

    if OSCAL_VERSION_FIELD not in payload:
        stats["MISSING_VERSION"] += 1
        continue

    payload_version = payload[OSCAL_VERSION_FIELD]
    if not isinstance(payload_version, str):
        stats["NON_STRING_VERSION"] += 1
    elif not payload_version.strip():
        stats["BLANK_VERSION"] += 1
    elif payload_version != configured_version:
        stats["WRONG_VERSION"] += 1
    else:
        stats["VALID_VERSION"] += 1


result = {
    "SOURCE_ROWS": source_rows,
    "UNIQUE_SOURCE_RECORDS": len(source_ids),
    "GRAPH_SOURCE_RECORDS": len(graph_source_ids),
    "METADATA_NODES": len(metadata_nodes),
    "MISSING_METADATA_NODES": len(missing_metadata_nodes),
    "ORPHAN_METADATA_NODES": len(orphan_metadata_nodes),
    "DUPLICATE_METADATA_NODES": duplicate_metadata_nodes,
    "NON_SINGLETON_INSTANCES": stats["NON_SINGLETON_INSTANCE"],
    "MALFORMED_PAYLOADS": stats["MALFORMED_PAYLOAD"],
    "MISSING_VERSIONS": stats["MISSING_VERSION"],
    "NON_STRING_VERSIONS": stats["NON_STRING_VERSION"],
    "BLANK_VERSIONS": stats["BLANK_VERSION"],
    "WRONG_VERSIONS": stats["WRONG_VERSION"],
    "VALID_VERSIONS": stats["VALID_VERSION"],
    "WRITES_EXECUTED": False,
}

failure_count = sum(
    result[key]
    for key in (
        "MISSING_METADATA_NODES",
        "ORPHAN_METADATA_NODES",
        "DUPLICATE_METADATA_NODES",
        "NON_SINGLETON_INSTANCES",
        "MALFORMED_PAYLOADS",
        "MISSING_VERSIONS",
        "NON_STRING_VERSIONS",
        "BLANK_VERSIONS",
        "WRONG_VERSIONS",
    )
)
if result["METADATA_NODES"] != source_rows:
    failure_count += 1
if result["VALID_VERSIONS"] != source_rows:
    failure_count += 1

result["FAILURE_COUNT"] = failure_count
result["RESULT"] = "PASSED" if failure_count == 0 else "FAILED"

print("=" * 72)
print("SSP METADATA OSCAL-VERSION READ-ONLY VALIDATION")
print("=" * 72)
print("Source rows:", result["SOURCE_ROWS"])
print("Unique source records:", result["UNIQUE_SOURCE_RECORDS"])
print("Graph source records:", result["GRAPH_SOURCE_RECORDS"])
print("Metadata nodes:", result["METADATA_NODES"])
print("Missing metadata nodes:", result["MISSING_METADATA_NODES"])
print("Orphan metadata nodes:", result["ORPHAN_METADATA_NODES"])
print("Duplicate metadata nodes:", result["DUPLICATE_METADATA_NODES"])
print("Non-singleton metadata nodes:", result["NON_SINGLETON_INSTANCES"])
print("Malformed metadata payloads:", result["MALFORMED_PAYLOADS"])
print("Missing oscal-version fields:", result["MISSING_VERSIONS"])
print("Non-string oscal-version fields:", result["NON_STRING_VERSIONS"])
print("Blank oscal-version fields:", result["BLANK_VERSIONS"])
print("Wrong oscal-version fields:", result["WRONG_VERSIONS"])
print("Valid oscal-version fields:", result["VALID_VERSIONS"])
print("Validation performed writes: False")
print("RESULT:", result["RESULT"])

if failure_count:
    raise RuntimeError(
        "Metadata oscal-version validation failed; aggregate failure count: "
        + str(failure_count)
    )


metadata_oscal_version_validation_result = result
