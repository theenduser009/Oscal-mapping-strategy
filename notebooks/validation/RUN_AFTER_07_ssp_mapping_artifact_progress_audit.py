# Read-only SSP mapping-artifact progress audit
#
# Run this once after Mapper Cell 7 in the same Snowflake notebook session.
# The loaded Archer-to-OSCAL mapping artifact is the progress denominator.
# This audit does not add NIST-required rows, infer blank target paths, expose
# source values or record IDs, create database objects, or perform writes.
#
# By default it prints only safe aggregate counts and normalized SSP target
# paths. Set SHOW_FIELD_DETAIL = True only for private notebook inspection if
# individual Archer field names are needed; field detail is never required for
# the Git status checkpoint. A matching non-empty output is called presence
# reconciliation, not proof of transformed value equality or OSCAL conformance.

from collections import Counter, defaultdict
import json
import re


SHOW_FIELD_DETAIL = False
SCREENSHOT_REPORTED_ARTIFACT_ROWS = 609
SSP_ROOT = "system-security-plan"

required_objects = {
    "session": globals().get("session"),
    "CONFIG": globals().get("CONFIG"),
    "source_df": globals().get("source_df"),
    "mapping_df": globals().get("mapping_df"),
    "mapping_artifact_pdf": globals().get("mapping_artifact_pdf"),
    "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
    "active_registry_paths": globals().get("active_registry_paths"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "run_result": globals().get("run_result"),
    "TRANSIENT_SOURCE_FIELDS": globals().get("TRANSIENT_SOURCE_FIELDS"),
    "RESPONSIBLE_PARTY_ROLE_IDS": globals().get(
        "RESPONSIBLE_PARTY_ROLE_IDS"
    ),
    "SECURITY_IMPACT_ELEMENT_PATH": globals().get(
        "SECURITY_IMPACT_ELEMENT_PATH"
    ),
    "STATUS_ELEMENT_PATH": globals().get("STATUS_ELEMENT_PATH"),
    "DOCUMENT_IDS_ELEMENT_PATH": globals().get(
        "DOCUMENT_IDS_ELEMENT_PATH"
    ),
    "SECURITY_OBJECTIVE_FIELDS": globals().get(
        "SECURITY_OBJECTIVE_FIELDS"
    ),
    "_parse_source_json": globals().get("_parse_source_json"),
    "resolve_json_path": globals().get("resolve_json_path"),
    "_mapping_owner_path": globals().get("_mapping_owner_path"),
    "_stable_property_name": globals().get("_stable_property_name"),
    "_target_field_name": globals().get("_target_field_name"),
    "col": globals().get("col"),
}
missing_objects = [name for name, value in required_objects.items() if value is None]
if missing_objects:
    raise RuntimeError(
        "Run Mapper Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_objects)
    )
if str(CONFIG.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
    raise RuntimeError("This audit requires CONFIG['OSCAL_MODEL'] = 'SSP'.")
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError("Set EXECUTE_WRITES = False before running this audit.")
if not run_result.get("validation_passed", False):
    raise RuntimeError("Cell 7 graph validation must pass first.")
if not run_result.get("pre_write_validation_passed", False):
    raise RuntimeError("Cell 7 pre-write validation must pass first.")
if run_result.get("writes_executed", True):
    raise RuntimeError("This audit requires a read-only Cell 7 run.")


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
REQUIRED_ARTIFACT_COLUMNS = {
    "SOURCE_FIELD_NAME",
    "OSCAL_MODEL",
    "OSCAL_ELEMENT_PATH",
    "MAPPING_TYPE",
}
SUPPORTED_MAPPING_TYPES = {
    "DIRECT",
    "TRANSFORM",
    "EXTENSION_PROPERTY",
    "REFERENCE",
    "CALCULATED",
    "TBD",
}
COMPLETED_STATUS_VALUES = {
    "approved",
    "complete",
    "completed",
    "done",
    "implemented",
    "validated",
}


def _clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none", "null"} else text


def _normalize_path(value):
    text = _clean(value).lower().replace("[*]", "[]")
    if text.startswith("$."):
        text = text[2:]
    text = re.sub(r"\s*\.\s*", ".", text)
    text = re.sub(r"\s+", "", text)
    return text.strip(".")


def _valid_oscal_path(path):
    return bool(
        re.fullmatch(
            r"[a-z0-9][a-z0-9-]*(?:\[\])?"
            r"(?:\.[a-z0-9][a-z0-9-]*(?:\[\])?)*",
            path,
        )
    )


def _model_is_ssp(value):
    token = re.sub(r"[^a-z0-9]+", " ", _clean(value).lower()).strip()
    return token == "ssp" or token.startswith("ssp ") or (
        "system security plan" in token
    )


def _mapping_type_bucket(value):
    token = re.sub(r"[^a-z0-9]+", "_", _clean(value).lower()).strip("_")
    if not token:
        return "BLANK"
    if "tbd" in token or "more_information" in token:
        return "TBD"
    if "extension" in token and "property" in token:
        return "EXTENSION_PROPERTY"
    if "reference" in token:
        return "REFERENCE"
    if "calculated" in token or "calculation" in token:
        return "CALCULATED"
    if "transform" in token:
        return "TRANSFORM"
    if "direct" in token:
        return "DIRECT"
    return "OTHER"


def _status_bucket(value):
    token = _clean(value).lower()
    if not token:
        return "UNSPECIFIED"
    if token in COMPLETED_STATUS_VALUES:
        return "COMPLETE"
    if "more information" in token or "tbd" in token:
        return "MORE_INFORMATION_REQUIRED"
    if token in {"not applicable", "n/a", "na"}:
        return "NOT_APPLICABLE"
    return "IN_PROGRESS"


def _meaningful(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_meaningful(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_meaningful(item) for item in value)
    return True


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


def _normalize_artifact_rows(dataframe):
    source_columns = [str(name).strip().upper() for name in dataframe.columns]
    canonical_sources = defaultdict(list)
    for source_column in source_columns:
        canonical_sources[
            MAPPING_COLUMN_ALIASES.get(source_column, source_column)
        ].append(source_column)

    missing_columns = sorted(REQUIRED_ARTIFACT_COLUMNS - set(canonical_sources))
    if missing_columns:
        raise RuntimeError(
            "Mapping artifact is missing required columns: "
            + ", ".join(missing_columns)
        )

    output = []
    alias_conflicts = 0
    for original in dataframe.to_dict(orient="records"):
        normalized = {}
        for key, value in original.items():
            source_key = str(key).strip().upper()
            canonical_key = MAPPING_COLUMN_ALIASES.get(source_key, source_key)
            prior = _clean(normalized.get(canonical_key))
            candidate = _clean(value)
            if prior and candidate and prior != candidate:
                alias_conflicts += 1
            if not prior or candidate:
                normalized[canonical_key] = value
        output.append(normalized)

    if alias_conflicts:
        raise RuntimeError(
            "Mapping artifact contains conflicting alias-column values. "
            f"Conflicts: {alias_conflicts}"
        )
    return output, bool(canonical_sources.get("STATUS"))


raw_mapping_rows, artifact_has_status_column = _normalize_artifact_rows(
    mapping_artifact_pdf
)
artifact_row_count = len(raw_mapping_rows)
snowpark_mapping_row_count = mapping_df.count()
if artifact_row_count == 0:
    raise RuntimeError("The loaded mapping artifact is empty.")
if artifact_row_count != snowpark_mapping_row_count:
    raise RuntimeError(
        "Pandas/Snowpark mapping row counts disagree: "
        f"{artifact_row_count} versus {snowpark_mapping_row_count}"
    )


# Reconcile the source and graph identities without printing any identifiers.
source_ids = []
source_objects = {}
source_parse_errors = 0
for record in source_df.select("SOURCE_RECORD_ID", "CURATED_JSON").to_local_iterator():
    source_record_id = _clean(record["SOURCE_RECORD_ID"])
    source_ids.append(source_record_id)
    try:
        source_objects[source_record_id] = _parse_source_json(record)
    except (TypeError, ValueError, json.JSONDecodeError):
        source_parse_errors += 1

if not source_ids or any(not value for value in source_ids):
    raise RuntimeError("Source records contain a blank SOURCE_RECORD_ID.")
if len(source_ids) != len(set(source_ids)):
    raise RuntimeError("Source records are not unique by SOURCE_RECORD_ID.")
if source_parse_errors:
    raise RuntimeError(
        f"Source JSON parse errors prevent progress audit: {source_parse_errors}"
    )

graph_source_ids = {
    _clean(row["SOURCE_RECORD_ID"])
    for row in final_nodes_df.select("SOURCE_RECORD_ID").distinct().to_local_iterator()
}
if set(source_ids) != graph_source_ids:
    raise RuntimeError(
        "Source/graph identity mismatch prevents mapping-progress claims."
    )


# Keep every path-evidenced SSP row and every SSP-label-only conceptual row.
ssp_rows = []
scope_counts = Counter()
for artifact_index, mapping_row in enumerate(raw_mapping_rows, start=1):
    model_label = _clean(mapping_row.get("OSCAL_MODEL"))
    original_path = _clean(mapping_row.get("OSCAL_ELEMENT_PATH"))
    normalized_path = _normalize_path(original_path)
    path_valid = bool(normalized_path) and _valid_oscal_path(normalized_path)
    path_is_ssp = path_valid and (
        normalized_path == SSP_ROOT
        or normalized_path.startswith(SSP_ROOT + ".")
    )
    model_is_ssp = _model_is_ssp(model_label)

    if path_is_ssp and (not model_label or model_is_ssp):
        scope_bucket = "PATH_EVIDENCED_SSP"
    elif not normalized_path and model_is_ssp:
        scope_bucket = "SSP_LABEL_ONLY_BLANK_PATH"
    elif path_is_ssp or model_is_ssp:
        scope_bucket = "MODEL_PATH_CONFLICT"
    else:
        scope_bucket = "OUT_OF_SCOPE"

    scope_counts[scope_bucket] += 1
    if scope_bucket == "OUT_OF_SCOPE":
        continue

    enriched = dict(mapping_row)
    enriched.update(
        {
            "_ARTIFACT_INDEX": artifact_index,
            "_ORIGINAL_PATH": original_path,
            "_NORMALIZED_PATH": normalized_path,
            "_PATH_VALID": path_valid,
            "_SCOPE_BUCKET": scope_bucket,
            "_MAPPING_TYPE_BUCKET": _mapping_type_bucket(
                mapping_row.get("MAPPING_TYPE")
            ),
            "_STATUS_BUCKET": _status_bucket(mapping_row.get("STATUS")),
        }
    )
    ssp_rows.append(enriched)

if not ssp_rows:
    raise RuntimeError("No SSP rows were found in the loaded mapping artifact.")


fingerprints = Counter()
for row in ssp_rows:
    fingerprint = (
        _clean(row.get("SOURCE_FIELD_NAME")).upper(),
        _clean(row.get("OSCAL_MODEL")).lower(),
        row["_NORMALIZED_PATH"],
        _normalize_path(row.get("OSCAL_FIELD_NAME")),
        row["_MAPPING_TYPE_BUCKET"],
        _clean(row.get("TRANSFORMATION_LOGIC")).lower(),
        _clean(row.get("STATUS")).lower(),
        _clean(row.get("NOTES")),
    )
    fingerprints[fingerprint] += 1
exact_duplicate_rows = sum(count - 1 for count in fingerprints.values() if count > 1)


# Source population is evaluated once per distinct SSP source field. Values and
# identifiers remain in memory and are never printed.
source_fields = sorted(
    {
        _clean(row.get("SOURCE_FIELD_NAME"))
        for row in ssp_rows
        if _clean(row.get("SOURCE_FIELD_NAME"))
    }
)
source_record_sets = {field_name: set() for field_name in source_fields}
source_resolution_errors = 0
for source_record_id, source_obj in source_objects.items():
    for field_name in source_fields:
        try:
            value = resolve_json_path(source_obj, field_name)
        except (AttributeError, KeyError, TypeError, ValueError):
            source_resolution_errors += 1
            continue
        if _meaningful(value):
            source_record_sets[field_name].add(source_record_id)

if source_resolution_errors:
    raise RuntimeError(
        "Source path-resolution errors prevent progress audit: "
        f"{source_resolution_errors}"
    )


# Parse generated nodes once. Payloads and record IDs are retained only in
# memory for aggregate source-to-output presence reconciliation.
nodes_by_path = defaultdict(list)
node_payload_errors = 0
for node_row in final_nodes_df.select(
    "ELEMENT_PATH", "SOURCE_RECORD_ID", "INSTANCE_KEY", "METADATA_JSON"
).to_local_iterator():
    node_path = _normalize_path(node_row["ELEMENT_PATH"])
    node_record_id = _clean(node_row["SOURCE_RECORD_ID"])
    node_instance_key = _clean(node_row["INSTANCE_KEY"])
    node_payload, malformed = _payload(node_row["METADATA_JSON"])
    if malformed:
        node_payload_errors += 1
    nodes_by_path[node_path].append(
        (node_record_id, node_instance_key, node_payload)
    )

if node_payload_errors:
    raise RuntimeError(
        f"Malformed generated node payloads prevent progress audit: {node_payload_errors}"
    )


canonical_index = defaultdict(list)
for canonical_row in CANONICAL_MAPPING_ROWS:
    canonical_key = (
        _clean(canonical_row.get("SOURCE_FIELD_NAME")).upper(),
        _normalize_path(canonical_row.get("OSCAL_ELEMENT_PATH")),
    )
    canonical_index[canonical_key].append(canonical_row)

transient_fields = {
    _clean(value).upper() for value in TRANSIENT_SOURCE_FIELDS
}
approved_party_roles = {
    _clean(key).upper(): _clean(value)
    for key, value in RESPONSIBLE_PARTY_ROLE_IDS.items()
}
security_objective_fields = {
    _clean(value) for value in SECURITY_OBJECTIVE_FIELDS
}


def _transform_handler_supported(canonical_row):
    source_field = _clean(canonical_row.get("SOURCE_FIELD_NAME")).upper()
    owner = _normalize_path(canonical_row.get("OWNER_ELEMENT_PATH"))
    target_field = _clean(_target_field_name(canonical_row))
    transform_logic = _clean(
        canonical_row.get("TRANSFORMATION_LOGIC")
    ).lower()

    if source_field in approved_party_roles:
        return True
    if (
        owner == _normalize_path(SECURITY_IMPACT_ELEMENT_PATH)
        and target_field in security_objective_fields
    ):
        return True
    if owner == _normalize_path(STATUS_ELEMENT_PATH) and target_field == "state":
        return True
    if (
        owner == _normalize_path(DOCUMENT_IDS_ELEMENT_PATH)
        and target_field == "identifier"
    ):
        return True
    return any(
        marker in transform_logic
        for marker in ("archer", "fips", "lookup", "security objective", "select value")
    )


def _output_records_for_mapping(canonical_row):
    source_field = _clean(canonical_row.get("SOURCE_FIELD_NAME")).upper()
    owner = _normalize_path(canonical_row.get("OWNER_ELEMENT_PATH"))
    target_field = _clean(_target_field_name(canonical_row))
    output_records = set()

    for source_record_id, instance_key, payload in nodes_by_path.get(owner, []):
        if owner.endswith(".props[]"):
            expected_name = _stable_property_name(source_field)
            if (
                instance_key.startswith(source_field + ":")
                and
                _clean(payload.get("name")) == expected_name
                and _meaningful(payload.get("value"))
            ):
                output_records.add(source_record_id)
            continue

        if owner.endswith(".responsible-parties[]"):
            expected_role = approved_party_roles.get(source_field)
            if (
                instance_key == source_field
                and expected_role
                and _clean(payload.get("role-id")) == expected_role
            ):
                party_values = payload.get("party-uuids")
                if _meaningful(party_values):
                    output_records.add(source_record_id)
            continue

        instance_is_attributable = (
            instance_key == "singleton"
            or instance_key.startswith(source_field + ":")
        )
        if (
            instance_is_attributable
            and target_field
            and _meaningful(payload.get(target_field))
        ):
            output_records.add(source_record_id)

    return output_records


# Find target convergence before classifying individual mappings. Multiple
# populated source candidates for one emitted singleton target require an
# approved precedence rule; graph presence cannot prove row attribution.
semantic_target_sources = defaultdict(set)
for row in ssp_rows:
    source_field = _clean(row.get("SOURCE_FIELD_NAME"))
    canonical_key = (source_field.upper(), row["_NORMALIZED_PATH"])
    matches = canonical_index.get(canonical_key, [])
    if len(matches) != 1 or not source_record_sets.get(source_field):
        continue
    canonical_row = matches[0]
    owner = _normalize_path(canonical_row.get("OWNER_ELEMENT_PATH"))
    target_field = _clean(_target_field_name(canonical_row))
    if owner.endswith(".responsible-parties[]"):
        target_field = approved_party_roles.get(source_field.upper(), "")
    semantic_target_sources[(owner, target_field)].add(source_field.upper())


def _classify_mapping(row):
    source_field = _clean(row.get("SOURCE_FIELD_NAME"))
    source_field_key = source_field.upper()
    normalized_path = row["_NORMALIZED_PATH"]
    mapping_type = row["_MAPPING_TYPE_BUCKET"]
    status_bucket = row["_STATUS_BUCKET"]

    if not source_field:
        return "MORE_INFORMATION_REQUIRED", "BLANK_SOURCE_FIELD", None, set()
    if row["_SCOPE_BUCKET"] == "MODEL_PATH_CONFLICT":
        return "MORE_INFORMATION_REQUIRED", "MODEL_TARGET_CONFLICT", None, set()
    if not normalized_path:
        return "MORE_INFORMATION_REQUIRED", "BLANK_TARGET_PATH", None, set()
    if not row["_PATH_VALID"]:
        return "MORE_INFORMATION_REQUIRED", "INVALID_TARGET_SYNTAX", None, set()
    if source_field_key in transient_fields:
        return "NOT_APPLICABLE", "APPROVED_TRANSIENT_HELPER", None, set()
    if status_bucket == "MORE_INFORMATION_REQUIRED" or mapping_type == "TBD":
        return "MORE_INFORMATION_REQUIRED", "TBD_OR_UNAPPROVED_TYPE", None, set()
    if status_bucket == "NOT_APPLICABLE":
        return "MORE_INFORMATION_REQUIRED", "UNAPPROVED_NOT_APPLICABLE", None, set()
    if mapping_type not in SUPPORTED_MAPPING_TYPES:
        return "MORE_INFORMATION_REQUIRED", "UNKNOWN_MAPPING_TYPE", None, set()

    owner = _mapping_owner_path(row["_ORIGINAL_PATH"])
    if not owner:
        return "MORE_INFORMATION_REQUIRED", "NO_ACTIVE_REGISTRY_OWNER", None, set()

    canonical_key = (source_field_key, normalized_path)
    matches = canonical_index.get(canonical_key, [])
    if len(matches) != 1:
        return "MORE_INFORMATION_REQUIRED", "CANONICAL_ROUTING_REVIEW", owner, set()
    canonical_row = matches[0]
    normalized_owner = _normalize_path(owner)
    target_field = _clean(_target_field_name(canonical_row))

    relative_path = normalized_path[len(normalized_owner):].lstrip(".")
    relative_path = relative_path.replace("[]", "")
    normalized_target_field = _normalize_path(target_field)
    if "." in relative_path or "." in normalized_target_field:
        return "MORE_INFORMATION_REQUIRED", "NESTED_SHAPING_REQUIRED", owner, set()
    if mapping_type == "EXTENSION_PROPERTY" and not normalized_owner.endswith(
        ".props[]"
    ):
        return "MORE_INFORMATION_REQUIRED", "EXTENSION_OWNER_NOT_PROPS", owner, set()
    if mapping_type == "REFERENCE":
        return (
            "MORE_INFORMATION_REQUIRED",
            "REFERENCE_INSTANCE_IDENTITY_OR_HYDRATION_REQUIRED",
            owner,
            set(),
        )
    if mapping_type == "CALCULATED":
        return "MORE_INFORMATION_REQUIRED", "CALCULATED_RULE_REVIEW", owner, set()
    if mapping_type == "TRANSFORM" and not _transform_handler_supported(
        canonical_row
    ):
        return "MORE_INFORMATION_REQUIRED", "TRANSFORM_HANDLER_MISSING", owner, set()
    if (
        normalized_owner.endswith(".responsible-parties[]")
        and source_field_key not in approved_party_roles
    ):
        return (
            "MORE_INFORMATION_REQUIRED",
            "RESPONSIBLE_PARTY_ROLE_UNAPPROVED",
            owner,
            set(),
        )

    semantic_target = target_field
    if normalized_owner.endswith(".responsible-parties[]"):
        semantic_target = approved_party_roles.get(source_field_key, "")
    converging_sources = semantic_target_sources.get(
        (normalized_owner, semantic_target), set()
    )
    identity_safe_collection = normalized_owner.endswith(
        (".props[]", ".responsible-parties[]")
    )
    if len(converging_sources) > 1 and not identity_safe_collection:
        return (
            "MORE_INFORMATION_REQUIRED",
            "TARGET_COLLISION_PRECEDENCE_REQUIRED",
            owner,
            set(),
        )

    populated_records = source_record_sets.get(source_field, set())
    if not populated_records:
        return "NO_SOURCE_DATA", "SOURCE_ZERO", owner, set()

    output_records = _output_records_for_mapping(canonical_row)
    if populated_records - output_records:
        return (
            "IN_PROGRESS",
            "OUTPUT_MISSING_FOR_POPULATED_SOURCE",
            owner,
            output_records,
        )
    if output_records - populated_records:
        return (
            "IN_PROGRESS",
            "OUTPUT_ATTRIBUTION_AMBIGUOUS",
            owner,
            output_records,
        )
    if status_bucket == "COMPLETE":
        return (
            "PRESENCE_RECONCILED",
            "DECLARED_COMPLETE_PRESENCE_RECONCILED",
            owner,
            output_records,
        )
    return (
        "PRESENCE_RECONCILED",
        "PRESENCE_RECONCILED_STATUS_UNCONFIRMED",
        owner,
        output_records,
    )


progress_rows = []
for row in ssp_rows:
    progress_class, reason_code, owner, output_records = _classify_mapping(row)
    source_field = _clean(row.get("SOURCE_FIELD_NAME"))
    source_populated_records = len(
        source_record_sets.get(source_field, set())
    )
    implementation_ready = bool(
        owner
        and source_populated_records
        and reason_code
        in {
            "NESTED_SHAPING_REQUIRED",
            "TRANSFORM_HANDLER_MISSING",
            "OUTPUT_MISSING_FOR_POPULATED_SOURCE",
        }
    )
    safe_path = (
        row["_NORMALIZED_PATH"]
        if row["_PATH_VALID"]
        and (
            row["_NORMALIZED_PATH"] == SSP_ROOT
            or row["_NORMALIZED_PATH"].startswith(SSP_ROOT + ".")
        )
        else "(no valid SSP target path)"
    )
    progress_rows.append(
        {
            "ARTIFACT_INDEX": row["_ARTIFACT_INDEX"],
            "SOURCE_FIELD_NAME": source_field,
            "OSCAL_ELEMENT_PATH": safe_path,
            "MAPPING_TYPE": row["_MAPPING_TYPE_BUCKET"],
            "ARTIFACT_STATUS": row["_STATUS_BUCKET"],
            "TECHNICAL_PROGRESS_CLASS": progress_class,
            "REASON_CODE": reason_code,
            "SOURCE_POPULATED_RECORDS": source_populated_records,
            "OUTPUT_RECORDS": len(output_records),
            "REGISTRY_OWNER_PRESENT": bool(owner),
            "IMPLEMENTATION_READY": implementation_ready,
        }
    )


class_counts = Counter(
    row["TECHNICAL_PROGRESS_CLASS"] for row in progress_rows
)
reason_counts = Counter(row["REASON_CODE"] for row in progress_rows)
mapping_type_counts = Counter(row["MAPPING_TYPE"] for row in progress_rows)
declared_complete_rows = sum(
    row["ARTIFACT_STATUS"] == "COMPLETE" for row in progress_rows
)

reason_priority = {
    "MODEL_TARGET_CONFLICT": 1,
    "BLANK_TARGET_PATH": 2,
    "INVALID_TARGET_SYNTAX": 3,
    "NO_ACTIVE_REGISTRY_OWNER": 4,
    "TBD_OR_UNAPPROVED_TYPE": 5,
    "TARGET_COLLISION_PRECEDENCE_REQUIRED": 6,
    "REFERENCE_INSTANCE_IDENTITY_OR_HYDRATION_REQUIRED": 7,
    "RESPONSIBLE_PARTY_ROLE_UNAPPROVED": 8,
    "NESTED_SHAPING_REQUIRED": 9,
    "TRANSFORM_HANDLER_MISSING": 10,
    "OUTPUT_MISSING_FOR_POPULATED_SOURCE": 11,
    "PRESENCE_RECONCILED_STATUS_UNCONFIRMED": 12,
    "DECLARED_COMPLETE_PRESENCE_RECONCILED": 13,
    "SOURCE_ZERO": 13,
    "APPROVED_TRANSIENT_HELPER": 15,
}
class_priority = {
    "MORE_INFORMATION_REQUIRED": 1,
    "IN_PROGRESS": 2,
    "NO_SOURCE_DATA": 3,
    "PRESENCE_RECONCILED": 4,
    "NOT_APPLICABLE": 5,
}

path_groups = defaultdict(list)
for row in progress_rows:
    path_groups[row["OSCAL_ELEMENT_PATH"]].append(row)

path_summary_rows = []
for path, rows in path_groups.items():
    path_classes = Counter(row["TECHNICAL_PROGRESS_CLASS"] for row in rows)
    path_progress_class = min(path_classes, key=lambda item: class_priority[item])
    class_reasons = Counter(
        row["REASON_CODE"]
        for row in rows
        if row["TECHNICAL_PROGRESS_CLASS"] == path_progress_class
    )
    top_reason = min(
        class_reasons,
        key=lambda item: (reason_priority.get(item, 999), item),
    )
    ready_rows = [row for row in rows if row["IMPLEMENTATION_READY"]]
    if ready_rows:
        ready_classes = Counter(
            row["TECHNICAL_PROGRESS_CLASS"] for row in ready_rows
        )
        ready_progress_class = min(
            ready_classes,
            key=lambda item: class_priority[item],
        )
        ready_reasons = Counter(
            row["REASON_CODE"]
            for row in ready_rows
            if row["TECHNICAL_PROGRESS_CLASS"] == ready_progress_class
        )
        ready_top_reason = min(
            ready_reasons,
            key=lambda item: (reason_priority.get(item, 999), item),
        )
    else:
        ready_progress_class = ""
        ready_top_reason = ""
    path_summary_rows.append(
        {
            "OSCAL_ELEMENT_PATH": path,
            "ARTIFACT_ROWS": len(rows),
            "DECLARED_COMPLETE_ROWS": sum(
                row["ARTIFACT_STATUS"] == "COMPLETE" for row in rows
            ),
            "PRESENCE_RECONCILED_ROWS": path_classes[
                "PRESENCE_RECONCILED"
            ],
            "IN_PROGRESS_ROWS": path_classes["IN_PROGRESS"],
            "MORE_INFORMATION_REQUIRED_ROWS": path_classes[
                "MORE_INFORMATION_REQUIRED"
            ],
            "NO_SOURCE_DATA_ROWS": path_classes["NO_SOURCE_DATA"],
            "NOT_APPLICABLE_ROWS": path_classes["NOT_APPLICABLE"],
            "IMPLEMENTATION_READY_ROWS": len(ready_rows),
            "PATH_PROGRESS_CLASS": path_progress_class,
            "TOP_REASON_CODE": top_reason,
            "IMPLEMENTATION_READY_CLASS": ready_progress_class,
            "IMPLEMENTATION_READY_REASON_CODE": ready_top_reason,
        }
    )

path_summary_rows.sort(
    key=lambda row: (
        row["OSCAL_ELEMENT_PATH"] == "(no valid SSP target path)",
        row["OSCAL_ELEMENT_PATH"].count("."),
        row["OSCAL_ELEMENT_PATH"],
    )
)
for order_index, row in enumerate(path_summary_rows, start=1):
    row["ROOT_TO_LEAF_ORDER"] = order_index

implementation_ready_paths = [
    row
    for row in path_summary_rows
    if row["IMPLEMENTATION_READY_ROWS"] > 0
]
unresolved_paths = [
    row
    for row in path_summary_rows
    if row["PATH_PROGRESS_CLASS"]
    in {"MORE_INFORMATION_REQUIRED", "IN_PROGRESS"}
]
next_path = (
    implementation_ready_paths[0]
    if implementation_ready_paths
    else (unresolved_paths[0] if unresolved_paths else None)
)
next_path_basis = (
    "IMPLEMENTATION_READY"
    if implementation_ready_paths
    else "FIRST_UNRESOLVED_REVIEW"
)

mapper_contract_version_present = bool(
    _clean(CONFIG.get("MAPPER_CONTRACT_VERSION"))
)
artifact_version_present = bool(
    _clean(CONFIG.get("MAPPING_ARTIFACT_VERSION"))
)
artifact_row_count_matches_screenshot = (
    artifact_row_count == SCREENSHOT_REPORTED_ARTIFACT_ROWS
)
# A count and two unverified labels cannot establish artifact identity or prove
# that the live V2 notebook is byte-equivalent to repository Mapper V1.
artifact_baseline_reconciled = False
runtime_implementation_provenance_verified = False

print("=" * 78)
print("SSP MAPPING ARTIFACT PROGRESS AUDIT")
print("=" * 78)
print("Loaded artifact rows:", artifact_row_count)
print("Screenshot-reported artifact rows:", SCREENSHOT_REPORTED_ARTIFACT_ROWS)
print("Artifact row count matches screenshot:", artifact_row_count_matches_screenshot)
print("Artifact identity/version baseline reconciled:", artifact_baseline_reconciled)
print("Artifact has explicit STATUS column:", artifact_has_status_column)
print("Mapper contract version configured:", mapper_contract_version_present)
print("Mapping artifact version configured:", artifact_version_present)
print(
    "Runtime implementation provenance verified:",
    runtime_implementation_provenance_verified,
)
print("Source/graph records reconciled:", len(source_ids))
print("SSP rows retained:", len(progress_rows))
print("Unique SSP row fingerprints:", len(fingerprints))
print("Exact duplicate SSP rows:", exact_duplicate_rows)
print("SSP scope buckets:", dict(sorted(scope_counts.items())))
print("Mapping type buckets:", dict(sorted(mapping_type_counts.items())))
print("Artifact rows explicitly marked complete:", declared_complete_rows)
print("Technical progress classes:", dict(sorted(class_counts.items())))
print("Reason codes:", dict(sorted(reason_counts.items())))
print("Presence reconciliation proves transformed value equality: False")
print("Global completion claim allowed: False")
print("RESULT: ARTIFACT PROGRESS EVIDENCE ONLY")

if next_path:
    print("NEXT ROOT-TO-LEAF TARGET:", next_path["OSCAL_ELEMENT_PATH"])
    print("NEXT TARGET SELECTION BASIS:", next_path_basis)
    if next_path_basis == "IMPLEMENTATION_READY":
        print("NEXT TARGET CLASS:", next_path["IMPLEMENTATION_READY_CLASS"])
        print(
            "NEXT TARGET REASON:",
            next_path["IMPLEMENTATION_READY_REASON_CODE"],
        )
    else:
        print("NEXT TARGET CLASS:", next_path["PATH_PROGRESS_CLASS"])
        print("NEXT TARGET REASON:", next_path["TOP_REASON_CODE"])
else:
    print("NEXT ROOT-TO-LEAF TARGET: none from current artifact evidence")

ssp_mapping_path_progress_df = session.create_dataframe(path_summary_rows)
ssp_mapping_path_progress_df.order_by("ROOT_TO_LEAF_ORDER").show(
    len(path_summary_rows),
    250,
)

if SHOW_FIELD_DETAIL:
    field_detail_rows = sorted(
        progress_rows,
        key=lambda row: (
            row["OSCAL_ELEMENT_PATH"] == "(no valid SSP target path)",
            row["OSCAL_ELEMENT_PATH"].count("."),
            row["OSCAL_ELEMENT_PATH"],
            row["SOURCE_FIELD_NAME"],
        ),
    )
    ssp_mapping_field_progress_df = session.create_dataframe(field_detail_rows)
    ssp_mapping_field_progress_df.show(len(field_detail_rows), 250)

# Remove in-memory source/payload evidence from the notebook namespace after
# aggregate results are built. None of these values are printed or persisted.
for _sensitive_temporary_name in (
    "source_objects",
    "source_record_sets",
    "nodes_by_path",
    "source_ids",
    "graph_source_ids",
    "source_record_id",
    "source_obj",
    "value",
    "record",
    "node_row",
    "node_record_id",
    "node_instance_key",
    "node_payload",
    "output_records",
    "populated_records",
):
    globals().pop(_sensitive_temporary_name, None)
del _sensitive_temporary_name
