# Read-only OSCAL SSP v1.2.3 required-source readiness audit
#
# Run after Mapper V1 Cell 7 and the minimum-required-scope audit. This cell
# keeps registry, mapping-artifact, source-population, and generated-output
# evidence separate for every minimum-contract path and field. It prints only
# hard-coded OSCAL target names and aggregate counts. It never prints source
# record IDs, Archer field names, values, payloads, hashes, or lookup labels.
# It creates no objects and performs no writes.

from collections import Counter, defaultdict
import json
import re


EXPECTED_OSCAL_VERSION = "1.2.3"

required_objects = {
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "final_edges_df": globals().get("final_edges_df"),
    "run_result": globals().get("run_result"),
    "mapping_artifact_pdf": globals().get("mapping_artifact_pdf"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "active_registry_paths": globals().get("active_registry_paths"),
    "MAPPINGS_BY_ELEMENT_PATH": globals().get("MAPPINGS_BY_ELEMENT_PATH"),
    "TRANSIENT_SOURCE_FIELDS": globals().get("TRANSIENT_SOURCE_FIELDS"),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
    "_has_value": globals().get("_has_value"),
    "_mapping_owner_path": globals().get("_mapping_owner_path"),
    "col": globals().get("col"),
}
missing_objects = [name for name, value in required_objects.items() if value is None]
if missing_objects:
    raise RuntimeError(
        "Run Mapper V1 Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_objects)
    )
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError("Set EXECUTE_WRITES = False before running this audit.")
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", False):
    raise RuntimeError("This audit requires a Cell 7 read-only run.")

configured_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
if configured_version and configured_version != EXPECTED_OSCAL_VERSION:
    raise RuntimeError(
        "This audit implements OSCAL SSP 1.2.3, but CONFIG pins a different version."
    )


ROOT = "system-security-plan"
METADATA = ROOT + ".metadata"
IMPORT_PROFILE = ROOT + ".import-profile"
CHARACTERISTICS = ROOT + ".system-characteristics"
SYSTEM_IDS = CHARACTERISTICS + ".system-ids[]"
SYSTEM_INFORMATION = CHARACTERISTICS + ".system-information"
INFORMATION_TYPES = SYSTEM_INFORMATION + ".information-types[]"
STATUS = CHARACTERISTICS + ".status"
AUTHORIZATION_BOUNDARY = CHARACTERISTICS + ".authorization-boundary"
SYSTEM_IMPLEMENTATION = ROOT + ".system-implementation"
COMPONENTS = SYSTEM_IMPLEMENTATION + ".components[]"
CONTROL_IMPLEMENTATION = ROOT + ".control-implementation"
IMPLEMENTED_REQUIREMENTS = CONTROL_IMPLEMENTATION + ".implemented-requirements[]"

EXACT_ONE_PATHS = (
    ROOT,
    METADATA,
    IMPORT_PROFILE,
    CHARACTERISTICS,
    SYSTEM_INFORMATION,
    STATUS,
    AUTHORIZATION_BOUNDARY,
    SYSTEM_IMPLEMENTATION,
    CONTROL_IMPLEMENTATION,
)

ONE_OR_MORE_PATHS = (
    SYSTEM_IDS,
    INFORMATION_TYPES,
    COMPONENTS,
    IMPLEMENTED_REQUIREMENTS,
)
REQUIRED_PATHS = EXACT_ONE_PATHS + ONE_OR_MORE_PATHS

# UUID-bearing nodes use deterministic graph OSCAL_UUID values and are not
# source-mapping gaps. These are the required payload fields to investigate.
REQUIRED_FIELDS = {
    METADATA: ("title", "last-modified", "version", "oscal-version"),
    IMPORT_PROFILE: ("href",),
    CHARACTERISTICS: ("system-name", "description"),
    SYSTEM_IDS: ("id",),
    INFORMATION_TYPES: ("title", "description"),
    STATUS: ("state",),
    AUTHORIZATION_BOUNDARY: ("description",),
    COMPONENTS: ("type", "title", "description", "status.state"),
    CONTROL_IMPLEMENTATION: ("description",),
    IMPLEMENTED_REQUIREMENTS: ("control-id",),
}

# Only authoritative non-record-specific values belong in controlled config.
# Availability is checked here; this audit never invents either value.
CONTROLLED_CONFIG = {
    (IMPORT_PROFILE, "href"): "SSP_IMPORT_PROFILE_HREF",
    (METADATA, "oscal-version"): "OSCAL_VERSION",
}

SYSTEM_STATUS_VALUES = {
    "operational",
    "under-development",
    "under-major-modification",
    "disposition",
    "other",
}
COMPONENT_STATUS_VALUES = {
    "under-development",
    "operational",
    "disposition",
    "other",
}

MAPPING_COLUMN_ALIASES = {
    "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME",
    "SOURCE_FIELD": "SOURCE_FIELD_NAME",
    "MODEL": "OSCAL_MODEL",
    "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
    "ELEMENT_PATH": "OSCAL_ELEMENT_PATH",
    "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
    "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME",
    "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
    "MAPPING_STATUS": "STATUS",
}


def _clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _normalize_target(value):
    text = _clean(value).lower().replace("[*]", "[]")
    if text.startswith("$."):
        text = text[2:]
    text = re.sub(r"\s*\.\s*", ".", text)
    text = re.sub(r"\s+", "", text)
    return text.strip(".")


registry_paths = {_normalize_target(path) for path in active_registry_paths}
prospective_owner_paths = registry_paths | set(REQUIRED_PATHS)


def _payload(value):
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


def _nested(payload, dotted_name):
    current = payload
    for token in dotted_name.split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def _nonblank_text(value):
    return isinstance(value, str) and bool(value.strip())


def _stable_property_name(value):
    return re.sub(r"[^a-z0-9]+", "-", _clean(value).lower()).strip("-")


def _valid_field(path, field_name, payload):
    value = _nested(payload, field_name)
    if not _nonblank_text(value):
        return False
    value = value.strip()
    if (path, field_name) == (METADATA, "oscal-version"):
        return value == EXPECTED_OSCAL_VERSION
    if (path, field_name) == (STATUS, "state"):
        if value not in SYSTEM_STATUS_VALUES:
            return False
        return value != "other" or _nonblank_text(payload.get("remarks"))
    if (path, field_name) == (COMPONENTS, "status.state"):
        return value in COMPONENT_STATUS_VALUES
    return True


def _expected_owner(mapping_path):
    candidates = [
        path
        for path in prospective_owner_paths
        if mapping_path == path or mapping_path.startswith(path + ".")
    ]
    return max(candidates, key=len) if candidates else None


def _normalized_explicit_field(value, owner):
    field_name = _normalize_target(value).replace("[]", "")
    owner_without_arrays = owner.replace("[]", "")
    if field_name.startswith(owner_without_arrays + "."):
        field_name = field_name[len(owner_without_arrays) + 1:]
    return field_name


def _target_analysis(mapping_row, owner):
    mapping_path = _normalize_target(mapping_row.get("OSCAL_ELEMENT_PATH"))
    explicit = _normalized_explicit_field(
        mapping_row.get("OSCAL_FIELD_NAME"), owner
    )
    relative = mapping_path[len(owner):].lstrip(".").replace("[]", "")

    if not relative:
        intended = explicit or _stable_property_name(
            mapping_row.get("SOURCE_FIELD_NAME")
        )
    elif not explicit or explicit == relative or relative.endswith("." + explicit):
        intended = relative
    elif relative + "." + explicit in REQUIRED_FIELDS.get(owner, ()):
        intended = relative + "." + explicit
    else:
        return "", True, False

    # Cell 3 derives only the last relative segment when OSCAL_FIELD_NAME is
    # blank. Cell 4 then writes that target as one flat payload key. A dotted
    # OSCAL target therefore needs explicit nested-payload shaping even when a
    # usable source candidate already exists.
    current_target = explicit or (
        relative.split(".")[-1]
        if relative
        else _stable_property_name(mapping_row.get("SOURCE_FIELD_NAME"))
    )
    current_shape_supported = "." not in intended and current_target == intended
    return intended, False, current_shape_supported


def _eligible(mapping_row):
    source_field = _clean(mapping_row.get("SOURCE_FIELD_NAME"))
    mapping_path = _normalize_target(mapping_row.get("OSCAL_ELEMENT_PATH"))
    mapping_type = _clean(mapping_row.get("MAPPING_TYPE") or "Direct").lower()
    mapping_status = _clean(mapping_row.get("STATUS")).lower()
    return (
        bool(source_field)
        and bool(mapping_path)
        and source_field not in TRANSIENT_SOURCE_FIELDS
        and "tbd" not in mapping_type
        and "more information" not in mapping_status
    )


def _normalized_mapping_rows(dataframe):
    output = []
    for original in dataframe.to_dict(orient="records"):
        normalized = {}
        for key, value in original.items():
            source_key = str(key).strip().upper()
            normalized[MAPPING_COLUMN_ALIASES.get(source_key, source_key)] = value
        output.append(normalized)
    return output


def _config_ready(path, field_name):
    config_name = CONTROLLED_CONFIG.get((path, field_name))
    if not config_name:
        return False, "not-designated"
    value = CONFIG.get(config_name)
    ready = (
        _clean(value) == EXPECTED_OSCAL_VERSION
        if config_name == "OSCAL_VERSION"
        else _nonblank_text(value)
    )
    return ready, config_name


# Read the original 608-row artifact so candidates below missing registry paths
# are visible even when Cell 3 currently routes them to an active ancestor.
raw_mapping_rows = _normalized_mapping_rows(mapping_artifact_pdf)
raw_path_rows = Counter()
eligible_path_rows = Counter()
skipped_path_rows = Counter()
ambiguous_path_rows = Counter()
owner_aligned_path_rows = Counter()
raw_field_rows = Counter()
eligible_field_rows = Counter()
owner_aligned_field_rows = Counter()
shaping_required_field_rows = Counter()
active_field_rows = Counter()
source_paths_by_path = defaultdict(set)
source_paths_by_field = defaultdict(set)
path_fingerprints = defaultdict(Counter)
field_fingerprints = defaultdict(Counter)

for mapping_row in raw_mapping_rows:
    original_mapping_path = _clean(mapping_row.get("OSCAL_ELEMENT_PATH"))
    mapping_path = _normalize_target(original_mapping_path)
    owner = _expected_owner(mapping_path)
    if owner not in REQUIRED_PATHS:
        continue

    source_field = _clean(mapping_row.get("SOURCE_FIELD_NAME"))
    fingerprint = (
        mapping_path,
        source_field,
        _normalize_target(mapping_row.get("OSCAL_FIELD_NAME")),
        _clean(mapping_row.get("MAPPING_TYPE")).lower(),
        _clean(mapping_row.get("STATUS")).lower(),
    )
    raw_path_rows[owner] += 1
    path_fingerprints[owner][fingerprint] += 1

    resolved_field, ambiguous, shape_supported = _target_analysis(
        mapping_row, owner
    )
    if ambiguous:
        ambiguous_path_rows[owner] += 1

    if not _eligible(mapping_row):
        skipped_path_rows[owner] += 1
    else:
        eligible_path_rows[owner] += 1
        source_paths_by_path[owner].add(source_field)
        current_owner = _mapping_owner_path(original_mapping_path)
        if _normalize_target(current_owner) == owner:
            owner_aligned_path_rows[owner] += 1

    if resolved_field not in REQUIRED_FIELDS.get(owner, ()):
        continue
    field_key = (owner, resolved_field)
    raw_field_rows[field_key] += 1
    field_fingerprints[field_key][fingerprint] += 1
    if _eligible(mapping_row):
        eligible_field_rows[field_key] += 1
        source_paths_by_field[field_key].add(source_field)
        if not shape_supported:
            shaping_required_field_rows[field_key] += 1
        current_owner = _mapping_owner_path(original_mapping_path)
        if _normalize_target(current_owner) == owner:
            owner_aligned_field_rows[field_key] += 1

for mapping_row in CANONICAL_MAPPING_ROWS:
    mapping_path = _normalize_target(mapping_row.get("OSCAL_ELEMENT_PATH"))
    expected_owner = _expected_owner(mapping_path)
    if expected_owner not in REQUIRED_FIELDS:
        continue
    resolved_field, ambiguous, shape_supported = _target_analysis(
        mapping_row, expected_owner
    )
    actual_owner = _normalize_target(mapping_row.get("OWNER_ELEMENT_PATH"))
    if (
        not ambiguous
        and shape_supported
        and resolved_field in REQUIRED_FIELDS[expected_owner]
        and actual_owner == expected_owner
        and _eligible(mapping_row)
    ):
        active_field_rows[(expected_owner, resolved_field)] += 1

duplicate_path_rows = Counter(
    {
        path: sum(max(0, count - 1) for count in fingerprints.values())
        for path, fingerprints in path_fingerprints.items()
    }
)
duplicate_field_rows = Counter(
    {
        key: sum(max(0, count - 1) for count in fingerprints.values())
        for key, fingerprints in field_fingerprints.items()
    }
)
# Parse CURATED_JSON once per source record and evaluate only the deduplicated
# candidate paths. Candidate path names remain in memory and are never printed.
source_ids = set()
source_rows = 0
blank_source_ids = 0
duplicate_source_rows = 0
source_parse_errors = 0
source_resolution_errors = 0
source_present_by_path = defaultdict(set)
source_present_by_field = defaultdict(set)
source_candidate_patterns_by_path = defaultdict(Counter)
source_candidate_patterns_by_field = defaultdict(Counter)
all_candidate_paths = {
    value
    for values in source_paths_by_path.values()
    for value in values
    if value
} | {
    value
    for values in source_paths_by_field.values()
    for value in values
    if value
}

for source_row in source_df.to_local_iterator():
    source_rows += 1
    raw_id = source_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_id is None else str(raw_id).strip()
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
        source_object = {}

    present_source_paths = set()
    for source_path in all_candidate_paths:
        try:
            if _has_value(resolve_json_path(source_object, source_path)):
                present_source_paths.add(source_path)
        except (TypeError, ValueError, KeyError, IndexError):
            source_resolution_errors += 1

    for path in REQUIRED_PATHS:
        populated = len(present_source_paths & source_paths_by_path[path])
        bucket = "zero" if populated == 0 else ("one" if populated == 1 else "multiple")
        source_candidate_patterns_by_path[path][bucket] += 1
        if populated:
            source_present_by_path[path].add(record_id)

    for path, fields in REQUIRED_FIELDS.items():
        for field_name in fields:
            key = (path, field_name)
            populated = len(present_source_paths & source_paths_by_field[key])
            bucket = "zero" if populated == 0 else ("one" if populated == 1 else "multiple")
            source_candidate_patterns_by_field[key][bucket] += 1
            if populated:
                source_present_by_field[key].add(record_id)

if blank_source_ids or duplicate_source_rows or not source_ids:
    raise RuntimeError(
        "Source identity check failed without displaying IDs: "
        f"rows={source_rows}, unique={len(source_ids)}, "
        f"blank={blank_source_ids}, duplicate={duplicate_source_rows}."
    )
if source_parse_errors or source_resolution_errors:
    raise RuntimeError(
        "Source candidate evaluation failed closed without displaying data: "
        f"parse_errors={source_parse_errors}, "
        f"resolution_errors={source_resolution_errors}. "
        "Do not interpret readiness classifications until these are zero."
    )


# Reconcile source and graph identity before interpreting coverage.
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

if blank_graph_ids or source_ids != graph_ids:
    raise RuntimeError(
        "Source/graph identity check failed without displaying IDs: "
        f"source={len(source_ids)}, graph={len(graph_ids)}, "
        f"intersection={len(source_ids & graph_ids)}, "
        f"source_only={len(source_ids - graph_ids)}, "
        f"graph_only={len(graph_ids - source_ids)}, blank_graph={blank_graph_ids}."
    )


# Inspect generated nodes once. For collections, a record is field-valid only
# when every emitted member validates; a single valid member is insufficient.
node_counts_by_path = Counter()
record_node_counts = defaultdict(Counter)
payload_errors_by_path = Counter()
payload_error_records_by_path = defaultdict(set)
field_present_node_counts = defaultdict(Counter)
field_valid_node_counts = defaultdict(Counter)
flat_nested_shape_mismatches = Counter()
all_fields_valid_node_counts = defaultdict(Counter)

required_nodes_df = final_nodes_df.select(
    "SOURCE_RECORD_ID", "ELEMENT_PATH", "METADATA_JSON"
).filter(col("ELEMENT_PATH").in_(list(REQUIRED_PATHS)))

for node_row in required_nodes_df.to_local_iterator():
    raw_id = node_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_id is None else str(raw_id).strip()
    path = _normalize_target(node_row["ELEMENT_PATH"])
    if not record_id or path not in REQUIRED_PATHS:
        continue

    node_counts_by_path[path] += 1
    record_node_counts[path][record_id] += 1
    payload, parse_error = _payload(node_row["METADATA_JSON"])
    if parse_error:
        payload_errors_by_path[path] += 1
        payload_error_records_by_path[path].add(record_id)

    node_all_fields_valid = not parse_error
    for field_name in REQUIRED_FIELDS.get(path, ()):
        key = (path, field_name)
        value = _nested(payload, field_name)
        if _has_value(value):
            field_present_node_counts[key][record_id] += 1
        else:
            node_all_fields_valid = False

        if not parse_error and _valid_field(path, field_name, payload):
            field_valid_node_counts[key][record_id] += 1
        else:
            node_all_fields_valid = False

        if "." in field_name and value is None:
            leaf_name = field_name.split(".")[-1]
            if field_name in payload or leaf_name in payload:
                flat_nested_shape_mismatches[key] += 1

    if node_all_fields_valid:
        all_fields_valid_node_counts[path][record_id] += 1


path_cardinality_valid_records = defaultdict(set)
field_any_present_records = defaultdict(set)
field_any_valid_records = defaultdict(set)
field_all_members_valid_records = defaultdict(set)
generated_all_fields_valid_records = defaultdict(set)

for path in REQUIRED_PATHS:
    for record_id in source_ids:
        node_count = record_node_counts[path][record_id]
        cardinality_valid = (
            node_count == 1 if path in EXACT_ONE_PATHS else node_count >= 1
        )
        if cardinality_valid:
            path_cardinality_valid_records[path].add(record_id)

        fields = REQUIRED_FIELDS.get(path, ())
        for field_name in fields:
            key = (path, field_name)
            present_count = field_present_node_counts[key][record_id]
            valid_count = field_valid_node_counts[key][record_id]
            if present_count:
                field_any_present_records[key].add(record_id)
            if valid_count:
                field_any_valid_records[key].add(record_id)
            if cardinality_valid and valid_count == node_count:
                field_all_members_valid_records[key].add(record_id)

        if cardinality_valid and (
            not fields
            or all_fields_valid_node_counts[path][record_id] == node_count
        ):
            generated_all_fields_valid_records[path].add(record_id)


source_all_fields_ready_records = defaultdict(set)
for path, fields in REQUIRED_FIELDS.items():
    for record_id in source_ids:
        all_ready = True
        for field_name in fields:
            key = (path, field_name)
            config_ready, _config_name = _config_ready(path, field_name)
            if not config_ready and record_id not in source_present_by_field[key]:
                all_ready = False
                break
        if all_ready:
            source_all_fields_ready_records[path].add(record_id)


def _path_action(path):
    registry_present = path in registry_paths
    cardinality_coverage = len(path_cardinality_valid_records[path])
    patterns = source_candidate_patterns_by_path[path]
    if not registry_present:
        if path in EXACT_ONE_PATHS:
            return "ADD_STRUCTURAL_REGISTRY_PATH"
        return (
            "ADD_COLLECTION_REGISTRY_AND_REVIEW_CANDIDATES"
            if eligible_path_rows[path]
            else "DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING"
        )
    if cardinality_coverage == len(source_ids):
        return "STRUCTURE_CARDINALITY_COVERED"
    if not raw_path_rows[path]:
        return "MAPPING_SOURCE_REQUIRED"
    if not eligible_path_rows[path]:
        return "ARTIFACT_ROWS_NOT_EXECUTABLE"
    if not owner_aligned_path_rows[path]:
        return "OWNER_ALIGNMENT_REQUIRED"
    if patterns["multiple"]:
        return "SOURCE_CANDIDATE_COLLISION_REVIEW"
    if not source_present_by_path[path]:
        return "SOURCE_VALUE_OR_CONTROLLED_CONFIG_REQUIRED"
    return "SOURCE_INSTANCE_COVERAGE_REQUIRED"


def _field_action(path, field_name):
    key = (path, field_name)
    registry_present = path in registry_paths
    config_ready, config_name = _config_ready(path, field_name)
    valid_coverage = len(field_all_members_valid_records[key])
    source_coverage = len(source_present_by_field[key])
    patterns = source_candidate_patterns_by_field[key]

    if valid_coverage == len(source_ids):
        return "GENERATED_VALID_FULL_COVERAGE", config_name
    if not registry_present:
        if config_ready:
            return "ADD_REGISTRY_AND_CONFIG_INJECTION", config_name
        if eligible_field_rows[key] and source_coverage:
            return (
                "ADD_REGISTRY_AND_SHAPING_IMPLEMENTATION"
                if shaping_required_field_rows[key]
                else "ADD_REGISTRY_AND_ACTIVATE_CANDIDATE"
            ), config_name
        if eligible_field_rows[key]:
            return "ADD_REGISTRY_SOURCE_VALUE_REQUIRED", config_name
        if key in CONTROLLED_CONFIG:
            return "ADD_REGISTRY_CONFIG_VALUE_REQUIRED", config_name
        return "ADD_REGISTRY_AND_MAPPING_SOURCE", config_name
    if config_ready:
        return "CONFIG_INJECTION_OR_SHAPING_REQUIRED", config_name
    if "." in field_name and shaping_required_field_rows[key]:
        return "SHAPING_IMPLEMENTATION_REQUIRED", config_name
    if "." in field_name and not raw_field_rows[key]:
        return "MAPPING_SOURCE_AND_SHAPING_REQUIRED", config_name
    if not raw_field_rows[key]:
        return (
            "CONTROLLED_CONFIG_VALUE_REQUIRED"
            if key in CONTROLLED_CONFIG
            else "MAPPING_SOURCE_REQUIRED"
        ), config_name
    if not eligible_field_rows[key]:
        return "ARTIFACT_ROWS_NOT_EXECUTABLE", config_name
    if not active_field_rows[key]:
        return "CANONICAL_ACTIVATION_REQUIRED", config_name
    if not owner_aligned_field_rows[key]:
        return "OWNER_ALIGNMENT_REQUIRED", config_name
    if patterns["multiple"]:
        return "SOURCE_CANDIDATE_COLLISION_REVIEW", config_name
    if not source_coverage:
        return "SOURCE_VALUE_OR_CONTROLLED_CONFIG_REQUIRED", config_name
    if source_present_by_field[key] - field_all_members_valid_records[key]:
        return "ROUTING_TRANSFORM_OR_SHAPE_REVIEW", config_name
    return "SOURCE_COMPLETENESS_REQUIRED", config_name


print("=" * 78)
print("READ-ONLY OSCAL SSP 1.2.3 REQUIRED-SOURCE READINESS AUDIT")
print("No record IDs, Archer field names, values, payloads, or hashes are shown.")
print("=" * 78)
print(
    "Session CONFIG OSCAL version:",
    configured_version or "<session predates repository pin>",
)
print("Cell 7 graph validation passed:", bool(run_result.get("validation_passed")))
print(
    "Cell 7 pre-write validation passed:",
    bool(run_result.get("pre_write_validation_passed")),
)
print("Writes executed:", bool(run_result.get("writes_executed", False)))
print("Source rows:", source_rows)
print("Unique source records:", len(source_ids))
print("Unique graph records:", len(graph_ids))
print("Source/graph identity reconciled:", source_ids == graph_ids)
print("Source parse errors:", source_parse_errors)
print("Source path resolution errors:", source_resolution_errors)

print("\n=== REQUIRED PATH READINESS ===")
path_actions = Counter()
for path in REQUIRED_PATHS:
    action = _path_action(path)
    path_actions[action] += 1
    patterns = source_candidate_patterns_by_path[path]
    print(
        "path=", path,
        "| cardinality=", "exactly-one" if path in EXACT_ONE_PATHS else "one-or-more",
        "| registry=", "present" if path in registry_paths else "missing",
        "| artifact_rows=", raw_path_rows[path],
        "| executable_rows=", eligible_path_rows[path],
        "| skipped_rows=", skipped_path_rows[path],
        "| duplicate_artifact_rows=", duplicate_path_rows[path],
        "| ambiguous_target_rows=", ambiguous_path_rows[path],
        "| currently_owner_aligned_rows=", owner_aligned_path_rows[path],
        "| currently_owner_misaligned_rows=",
        eligible_path_rows[path] - owner_aligned_path_rows[path],
        "| unique_source_candidates=", len(source_paths_by_path[path]),
        "| candidate_records_zero=", patterns["zero"],
        "| candidate_records_one=", patterns["one"],
        "| candidate_records_multiple=", patterns["multiple"],
        "| generated_nodes=", node_counts_by_path[path],
        "| generated_record_coverage=", len(record_node_counts[path]),
        "| cardinality_valid_records=", len(path_cardinality_valid_records[path]),
        "| malformed_payloads=", payload_errors_by_path[path],
        "| action=", action,
    )

print("\n=== REQUIRED FIELD SOURCE / OUTPUT READINESS ===")
field_actions = Counter()
for path in REQUIRED_PATHS:
    for field_name in REQUIRED_FIELDS.get(path, ()):
        key = (path, field_name)
        action, config_name = _field_action(path, field_name)
        field_actions[action] += 1
        patterns = source_candidate_patterns_by_field[key]
        source_records = source_present_by_field[key]
        any_present = field_any_present_records[key]
        any_valid = field_any_valid_records[key]
        all_members_valid = field_all_members_valid_records[key]
        config_ready, _ = _config_ready(path, field_name)
        print(
            "path=", path,
            "| field=", field_name,
            "| provenance=", "controlled-config" if key in CONTROLLED_CONFIG else "mapping-artifact",
            "| registry=", "present" if path in registry_paths else "missing",
            "| artifact_rows=", raw_field_rows[key],
            "| executable_rows=", eligible_field_rows[key],
            "| skipped_rows=", raw_field_rows[key] - eligible_field_rows[key],
            "| duplicate_artifact_rows=", duplicate_field_rows[key],
            "| shaping_required_rows=", shaping_required_field_rows[key],
            "| currently_owner_aligned_rows=", owner_aligned_field_rows[key],
            "| currently_owner_misaligned_rows=",
            eligible_field_rows[key] - owner_aligned_field_rows[key],
            "| active_mapping_rows=", active_field_rows[key],
            "| unique_source_candidates=", len(source_paths_by_field[key]),
            "| candidate_records_zero=", patterns["zero"],
            "| candidate_records_one=", patterns["one"],
            "| candidate_records_multiple=", patterns["multiple"],
            "| generated_any_nonblank_records=", len(any_present),
            "| generated_any_valid_records=", len(any_valid),
            "| generated_all_members_valid_records=", len(all_members_valid),
            "| source_present_not_all_members_valid=", len(source_records - all_members_valid),
            "| flat_nested_shape_mismatches=", flat_nested_shape_mismatches[key],
            "| controlled_config=", config_name,
            "| controlled_config_ready=", config_ready,
            "| action=", action,
        )

print("\n=== COMPOSITE RECORD-LEVEL READINESS ===")
for path in REQUIRED_PATHS:
    print(
        "path=", path,
        "| candidate_sources_cover_all_required_fields=",
        len(source_all_fields_ready_records[path]) if path in REQUIRED_FIELDS else "not-applicable",
        "| generated_nodes_satisfy_cardinality_and_all_required_fields=",
        len(generated_all_fields_valid_records[path]),
    )
print(
    "Candidate-source coverage is record-level evidence only; for collections "
    "it does not prove that values correlate to the same member instance."
)

print("\n=== ACTION SUMMARY ===")
print("Required paths reviewed:", len(REQUIRED_PATHS))
for action in sorted(path_actions):
    print("Path action", action, "=", path_actions[action])
field_total = sum(len(fields) for fields in REQUIRED_FIELDS.values())
print("Required payload fields reviewed:", field_total)
for action in sorted(field_actions):
    print("Field action", action, "=", field_actions[action])

profile_key = (IMPORT_PROFILE, "href")
profile_config_ready, _ = _config_ready(*profile_key)
profile_patterns = source_candidate_patterns_by_field[profile_key]
print("\n=== IMPORT-PROFILE DECISION GATE ===")
print("Registry path present:", IMPORT_PROFILE in registry_paths)
print("Artifact rows for href:", raw_field_rows[profile_key])
print("Executable rows for href:", eligible_field_rows[profile_key])
print("Currently owner-aligned rows for href:", owner_aligned_field_rows[profile_key])
print("Candidate records with one populated value:", profile_patterns["one"])
print("Candidate records with multiple populated values:", profile_patterns["multiple"])
print("SSP_IMPORT_PROFILE_HREF configured:", profile_config_ready)
if source_present_by_field[profile_key]:
    print(
        "NEXT DECISION: review whether the aggregate source candidate represents "
        "the approved OSCAL profile URI; no value is exposed or assumed."
    )
elif not profile_config_ready:
    print(
        "NEXT DECISION: provide the approved profile URI for "
        "CONFIG['SSP_IMPORT_PROFILE_HREF']; no default was invented."
    )
elif IMPORT_PROFILE not in registry_paths:
    print(
        "NEXT ENGINEERING ACTION: add the import-profile registry path and "
        "controlled-config mapping."
    )
else:
    print(
        "NEXT ENGINEERING ACTION: inject and validate the configured "
        "import-profile href."
    )

print("\nRESULT: MAPPING-BACKLOG EVIDENCE ONLY")
print("This audit never authorizes writes.")
print(
    "Assembled OSCAL JSON schema and constraint validation remain mandatory "
    "after all minimum-contract gaps are resolved."
)

