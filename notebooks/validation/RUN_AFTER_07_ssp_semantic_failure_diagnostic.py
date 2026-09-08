# Read-only SSP semantic-failure diagnostic
#
# Run this temporary Snowflake Python cell after Mapper V1 Cell 7 and the
# payload-semantics validator. It reports mapping-dispatch and aggregate shape
# evidence only. It does not print source record IDs or payload values, create
# permanent objects, or write to DIM/FACT tables.

from collections import Counter
import json
import re


if "CONFIG" not in globals():
    raise RuntimeError("Run Mapper V1 Cells 1 through 7 first.")
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running this diagnostic."
    )
if "final_nodes_df" not in globals() or final_nodes_df is None:
    raise RuntimeError("Cell 7 final_nodes_df is not available.")
if "run_result" not in globals() or not run_result.get(
    "validation_passed", False
):
    raise RuntimeError("Cell 7 validation must pass before this diagnostic.")
if "CANONICAL_MAPPING_ROWS" not in globals():
    raise RuntimeError("Cell 3 canonical mappings are not available.")


DIAG_PATHS = {
    "document_ids": "system-security-plan.metadata.document-ids[]",
    "props": "system-security-plan.system-characteristics.props[]",
    "security_impact": (
        "system-security-plan.system-characteristics.security-impact-level"
    ),
    "status": "system-security-plan.system-characteristics.status",
    "components": "system-security-plan.system-implementation.components[]",
}

DIAG_SECURITY_OBJECTIVES = {
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
}

DIAG_ALLOWED_STATUS = {
    "operational",
    "under-development",
    "under-major-modification",
    "disposition",
    "other",
}


def _diag_to_dict(value):
    if value is None:
        return {}
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _diag_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def _diag_normalize(value):
    return "-".join(
        str(value).strip().lower().replace("_", "-").split()
    )


def _diag_key_signature(value):
    if not isinstance(value, dict):
        return "<not-object>"
    return ",".join(sorted(str(key) for key in value)) or "<empty-object>"


def _diag_recursive_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(_diag_recursive_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_diag_recursive_keys(item))
    return keys


def _diag_flatten(value):
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_diag_flatten(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(_diag_flatten(item))
        return result
    return [value]


def _diag_status_bucket(value):
    token = _diag_normalize(value)
    if token in DIAG_ALLOWED_STATUS:
        return "already-allowed"
    if "major" in token and any(
        word in token for word in ("modification", "change")
    ):
        return "candidate-under-major-modification"
    if any(
        word in token
        for word in ("develop", "design", "planning", "planned")
    ):
        return "candidate-under-development"
    if any(
        word in token
        for word in (
            "operational",
            "production",
            "active",
            "implemented",
            "in-use",
        )
    ):
        return "candidate-operational"
    if any(
        word in token
        for word in (
            "disposition",
            "retired",
            "decommission",
            "terminated",
        )
    ):
        return "candidate-disposition"
    return "needs-approved-crosswalk"


def _diag_security_buckets(value):
    """Classify impact values without printing IDs or labels."""
    extracted = _extract_reference_ids(value)
    items = extracted if isinstance(extracted, list) else [extracted]
    buckets = []
    for item in items:
        if isinstance(item, (dict, list)) or item is None:
            buckets.append("unresolved-structured-or-null")
            continue

        key = str(item).strip()
        token = _diag_normalize(key)
        if token in {
            "low",
            "moderate",
            "high",
            "fips-199-low",
            "fips-199-moderate",
            "fips-199-high",
        }:
            buckets.append("already-standard")
            continue

        if key in globals().get("FIPS_199_VALUE_LOOKUP", {}):
            buckets.append("lookup-resolves-to-standard")
            continue

        if key in globals().get("ARCHER_VALUE_LOOKUP", {}):
            label = ARCHER_VALUE_LOOKUP.get(key)
            if _diag_normalize(label) in {"low", "moderate", "high"}:
                buckets.append("lookup-resolves-to-standard")
            else:
                buckets.append("recognized-archer-nonstandard-label")
            continue

        if isinstance(item, str) and item.strip() and not item.strip().isdigit():
            # The generic lookup may already have converted an Archer ID into
            # a preserved legacy label before the payload was serialized.
            buckets.append("preserved-nonstandard-string-label")
        else:
            buckets.append("unresolved-id-or-scalar")
    return buckets


def _diag_mapping_dispatch(mapping_row):
    source_field = str(mapping_row.get("SOURCE_FIELD_NAME") or "").strip()
    mapping_type = str(mapping_row.get("MAPPING_TYPE") or "Direct").lower()
    transform_logic = str(
        mapping_row.get("TRANSFORMATION_LOGIC") or ""
    ).lower()
    status = str(mapping_row.get("STATUS") or "").lower()

    if source_field in globals().get("TRANSIENT_SOURCE_FIELDS", set()):
        return "skip-transient"
    if "tbd" in mapping_type or "more information" in status:
        return "skip-unapproved"
    if source_field in globals().get("RESPONSIBLE_PARTY_ROLE_IDS", {}):
        return "responsible-party-transform"
    if "fips" in transform_logic or "security objective" in transform_logic:
        return "fips-transform"
    if (
        "archer" in transform_logic
        or "select value" in transform_logic
        or "lookup" in transform_logic
        or "extension" in mapping_type
    ):
        return "archer-select-lookup"
    return "direct-pass-through"


print("=" * 78)
print("SSP READ-ONLY SEMANTIC FAILURE DIAGNOSTIC")
print("No source record IDs or payload values are displayed.")
print("=" * 78)

print("\n=== RELEVANT MAPPING DISPATCH ===")
for mapping in CANONICAL_MAPPING_ROWS:
    owner_path = str(mapping.get("OWNER_ELEMENT_PATH") or "").strip()
    if owner_path not in DIAG_PATHS.values():
        continue
    source_field = str(mapping.get("SOURCE_FIELD_NAME") or "").strip()
    target_field = str(mapping.get("OSCAL_FIELD_NAME") or "").strip()
    relative_path = str(mapping.get("FIELD_RELATIVE_PATH") or "").strip()
    print(
        owner_path,
        "| source=", source_field,
        "| target=", target_field or relative_path or "<owner>",
        "| dispatch=", _diag_mapping_dispatch(mapping),
    )


security_stats = Counter()
security_candidate_stats = Counter()
status_stats = Counter()
document_stats = Counter()
props_stats = Counter()
component_stats = Counter()
props_invalid_profiles = Counter()
component_key_profiles = Counter()

selected_paths = set(DIAG_PATHS.values())
for row in final_nodes_df.select(
    "ELEMENT_PATH",
    "INSTANCE_KEY",
    "METADATA_JSON",
).filter(col("ELEMENT_PATH").in_(list(selected_paths))).to_local_iterator():
    path = str(row["ELEMENT_PATH"])
    instance_key = str(row["INSTANCE_KEY"] or "")
    payload = _diag_to_dict(row["METADATA_JSON"])

    if path == DIAG_PATHS["security_impact"]:
        security_stats["nodes"] += 1
        for objective in DIAG_SECURITY_OBJECTIVES:
            if objective not in payload:
                security_stats["missing-objective-fields"] += 1
                continue
            raw_value = payload.get(objective)
            security_stats["objective-value-type:" + _diag_type(raw_value)] += 1
            for bucket in _diag_security_buckets(raw_value):
                security_stats["classification:" + bucket] += 1
            transformed = transform_fips_199(raw_value)
            if transformed is None:
                security_stats["not-resolvable-by-current-fips-helper"] += 1
                continue
            transformed_values = _diag_flatten(transformed)
            if transformed_values and all(
                _diag_normalize(item) in {"low", "moderate", "high"}
                for item in transformed_values
            ):
                security_stats["resolvable-by-current-fips-helper"] += 1
                for item in transformed_values:
                    security_stats[
                        "resolved-standard-value:" + _diag_normalize(item)
                    ] += 1
            else:
                security_stats["fips-helper-returned-nonstandard"] += 1

    elif path == DIAG_PATHS["status"]:
        status_stats["nodes"] += 1
        raw_state = payload.get("state")
        status_stats["state-type:" + _diag_type(raw_state)] += 1
        resolved_state = resolve_archer_select_value(raw_state)
        resolved_values = _diag_flatten(resolved_state)
        if not resolved_values:
            status_stats["empty-after-select-lookup"] += 1
        for item in resolved_values:
            status_stats["lookup-result-type:" + _diag_type(item)] += 1
            if isinstance(item, (str, int, float, bool)):
                status_stats[
                    "crosswalk-bucket:" + _diag_status_bucket(item)
                ] += 1
            else:
                status_stats["crosswalk-bucket:non-scalar"] += 1

    elif path == DIAG_PATHS["document_ids"]:
        document_stats["nodes"] += 1
        document_stats[
            "payload-keys:" + _diag_key_signature(payload)
        ] += 1
        identifier = payload.get("identifier")
        document_stats["identifier-type:" + _diag_type(identifier)] += 1
        extracted = _extract_reference_ids(identifier)
        document_stats["extracted-type:" + _diag_type(extracted)] += 1
        extracted_items = extracted if isinstance(extracted, list) else [extracted]
        usable = [
            item
            for item in extracted_items
            if isinstance(item, (str, int, float))
            and not isinstance(item, bool)
            and str(item).strip()
        ]
        if len(usable) == 1 and len(extracted_items) == 1:
            document_stats["single-scalar-identifier-candidate"] += 1
        elif usable and len(usable) == len(extracted_items):
            document_stats["multiple-scalar-identifier-candidates"] += 1
        else:
            document_stats["unresolved-identifier-shape"] += 1
        if isinstance(identifier, dict):
            document_stats[
                "identifier-object-keys:" + _diag_key_signature(identifier)
            ] += 1

    elif path == DIAG_PATHS["props"]:
        props_stats["nodes"] += 1
        name = payload.get("name")
        value = payload.get("value")
        valid_name = isinstance(name, str) and bool(name.strip())
        valid_value = isinstance(value, str) and bool(value.strip())
        if valid_name and valid_value:
            props_stats["valid"] += 1
        else:
            props_stats["invalid"] += 1
            source_field = re.sub(r":\d+$", "", instance_key)
            reasons = []
            if not valid_name:
                reasons.append("invalid-name")
            if value is None or value == "":
                reasons.append("empty-value")
            elif not isinstance(value, str):
                reasons.append("non-string-value")
            props_invalid_profiles[
                (
                    source_field or "<unknown-source-field>",
                    "+".join(reasons),
                    _diag_type(value),
                    _diag_key_signature(value),
                )
            ] += 1

    elif path == DIAG_PATHS["components"]:
        component_stats["nodes"] += 1
        recursive_keys = _diag_recursive_keys(payload)
        normalized_keys = {
            key.replace("_", "").replace("-", "").lower()
            for key in recursive_keys
        }
        if "contentid" in normalized_keys or "levelid" in normalized_keys:
            component_stats["raw-reference-at-any-depth"] += 1
        else:
            component_stats["no-known-raw-reference-key"] += 1
        component_key_profiles[",".join(sorted(recursive_keys))] += 1


# Count populated source candidates converging on each security objective.
# More than one candidate for a record exposes the current silent overwrite
# risk, but no source record identifier or value is retained or printed.
security_mapping_rows = [
    mapping
    for mapping in CANONICAL_MAPPING_ROWS
    if str(mapping.get("OWNER_ELEMENT_PATH") or "").strip()
    == DIAG_PATHS["security_impact"]
    and str(mapping.get("OSCAL_FIELD_NAME") or "").strip()
    in DIAG_SECURITY_OBJECTIVES
]
security_mappings_by_target = {}
for mapping in security_mapping_rows:
    target = str(mapping.get("OSCAL_FIELD_NAME") or "").strip()
    security_mappings_by_target.setdefault(target, []).append(mapping)

for source_record in source_df.to_local_iterator():
    source_object = _parse_source_json(source_record)
    for target, mappings in security_mappings_by_target.items():
        populated_candidates = sum(
            1
            for mapping in mappings
            if _has_value(
                resolve_json_path(
                    source_object,
                    str(mapping.get("SOURCE_FIELD_NAME") or "").strip(),
                )
            )
        )
        if populated_candidates == 0:
            bucket = "zero-populated-candidates"
        elif populated_candidates == 1:
            bucket = "one-populated-candidate"
        else:
            bucket = "multiple-populated-candidates"
        security_candidate_stats[target + ":" + bucket] += 1


def _diag_print_counter(title, values):
    print("\n===", title, "===")
    for key, count in sorted(values.items(), key=lambda item: str(item[0])):
        print(key, "=", count)


_diag_print_counter("SECURITY IMPACT", security_stats)
_diag_print_counter(
    "SECURITY IMPACT SOURCE-CANDIDATE COLLISIONS",
    security_candidate_stats,
)
_diag_print_counter("STATUS", status_stats)
_diag_print_counter("DOCUMENT IDS", document_stats)
_diag_print_counter("PROPERTIES", props_stats)

print("\n=== INVALID PROPERTY PROFILES (NO VALUES) ===")
for profile, count in props_invalid_profiles.most_common(50):
    source_field, reason, value_type, object_keys = profile
    print(
        "source=", source_field,
        "| reason=", reason,
        "| type=", value_type,
        "| object_keys=", object_keys,
        "| count=", count,
    )

_diag_print_counter("COMPONENT REFERENCES", component_stats)
print("\n=== COMPONENT KEY PROFILES (NO VALUES; TOP 20) ===")
for signature, count in component_key_profiles.most_common(20):
    print("keys=", signature or "<none>", "| count=", count)

print("\n=== SAFETY RESULT ===")
print("READ-ONLY DIAGNOSTIC COMPLETE")
print("EXECUTE_WRITES =", CONFIG.get("EXECUTE_WRITES", False))
print("No DIM/FACT writes or permanent objects were created.")

