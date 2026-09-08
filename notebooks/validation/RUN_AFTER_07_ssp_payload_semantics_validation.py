# Read-only SSP payload-semantics validation
#
# Run this temporary Snowflake Python cell after Mapper V1 Cell 7.  It checks
# aggregate payload shapes and semantic value classes without printing source
# records or payload contents.  It creates no permanent objects and performs
# no DIM or FACT writes.

from collections import Counter
import json
import uuid


if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running semantic validation."
    )

if final_nodes_df is None or not run_result.get("validation_passed", False):
    raise RuntimeError("Run Mapper V1 Cells 1 through 7 successfully first.")


PATHS = {
    "document_ids": "system-security-plan.metadata.document-ids[]",
    "responsible_parties": (
        "system-security-plan.metadata.responsible-parties[]"
    ),
    "props": "system-security-plan.system-characteristics.props[]",
    "security_impact": (
        "system-security-plan.system-characteristics.security-impact-level"
    ),
    "status": "system-security-plan.system-characteristics.status",
    "components": "system-security-plan.system-implementation.components[]",
}

SECURITY_OBJECTIVES = {
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
}

ALLOWED_SECURITY_VALUES = {
    "low",
    "moderate",
    "high",
    "fips-199-low",
    "fips-199-moderate",
    "fips-199-high",
}

REVIEWED_LEGACY_SECURITY_VALUES = {
    "legacy-loe-a",
    "legacy-loe-b",
    "legacy-loe-c",
    "legacy-loe-c-+-dfars",
    "legacy-loe-d",
    "legacy-loe-d-+-dfars",
}

ALLOWED_STATUS_VALUES = {
    "operational",
    "under-development",
    "under-major-modification",
    "disposition",
    "other",
}


def _payload_dict(value):
    if value is None:
        return {}
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _leaf_values(value):
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_leaf_values(item))
        return result
    if isinstance(value, dict):
        if "value" in value:
            return _leaf_values(value["value"])
        result = []
        for item in value.values():
            result.extend(_leaf_values(item))
        return result
    return [value]


def _normalized_token(value):
    return "-".join(str(value).strip().lower().replace("_", "-").split())


def _is_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except (TypeError, ValueError, AttributeError):
        return False


def _recursive_keys(value):
    keys = set()
    if isinstance(value, dict):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(_recursive_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_recursive_keys(item))
    return keys


stats = Counter()

for row in final_nodes_df.select(
    "ELEMENT_PATH",
    "METADATA_JSON",
).to_local_iterator():
    path = str(row["ELEMENT_PATH"])
    payload = _payload_dict(row["METADATA_JSON"])

    if path == PATHS["security_impact"]:
        stats["security_total"] += 1
        if not payload:
            stats["security_empty"] += 1
            continue

        present_objectives = SECURITY_OBJECTIVES.intersection(payload)
        if len(present_objectives) < len(SECURITY_OBJECTIVES):
            stats["security_incomplete_objective_nodes"] += 1

        invalid_value_found = False
        value_found = False
        for objective in present_objectives:
            value = payload.get(objective)
            value_found = True
            if not isinstance(value, str) or not value.strip():
                invalid_value_found = True
                stats["security_invalid_type_or_empty_occurrences"] += 1
                continue

            token = _normalized_token(value)
            if token in ALLOWED_SECURITY_VALUES:
                stats["security_standard_value_occurrences"] += 1
            elif token in REVIEWED_LEGACY_SECURITY_VALUES:
                # OSCAL defines these objective fields as strings. Preserve
                # reviewed legacy LOE labels without claiming a FIPS level.
                stats["security_reviewed_legacy_occurrences"] += 1
            else:
                invalid_value_found = True
                stats["security_unreviewed_label_occurrences"] += 1

        if value_found and not invalid_value_found:
            stats["security_semantically_valid"] += 1
        else:
            stats["security_semantically_invalid"] += 1

    elif path == PATHS["status"]:
        stats["status_total"] += 1
        state = payload.get("state")
        if state is None or state == "":
            stats["status_empty_or_missing"] += 1
            continue

        state_token = _normalized_token(state)
        valid_state = (
            isinstance(state, str)
            and state_token in ALLOWED_STATUS_VALUES
        )
        valid_other_remarks = (
            state_token != "other"
            or (
                isinstance(payload.get("remarks"), str)
                and bool(payload.get("remarks").strip())
            )
        )
        if valid_state and valid_other_remarks:
            stats["status_semantically_valid"] += 1
        else:
            stats["status_semantically_invalid"] += 1

    elif path == PATHS["props"]:
        stats["props_total"] += 1
        prop_name = payload.get("name")
        prop_value = payload.get("value")
        valid_shape = (
            isinstance(prop_name, str)
            and bool(prop_name.strip())
            and isinstance(prop_value, str)
            and bool(prop_value.strip())
            and prop_name != "helper-pta-calc"
            and prop_name != "package-type-helper-calc"
        )
        stats[
            "props_valid" if valid_shape else "props_invalid"
        ] += 1

    elif path == PATHS["responsible_parties"]:
        stats["responsible_parties_total"] += 1
        role_id = payload.get("role-id")
        party_uuids = payload.get("party-uuids")
        valid_shape = (
            isinstance(role_id, str)
            and bool(role_id.strip())
            and isinstance(party_uuids, list)
            and bool(party_uuids)
            and all(_is_uuid(value) for value in party_uuids)
        )
        stats[
            "responsible_parties_valid"
            if valid_shape
            else "responsible_parties_invalid"
        ] += 1

    elif path == PATHS["document_ids"]:
        stats["document_ids_total"] += 1
        identifier = payload.get("identifier")
        valid_shape = isinstance(identifier, str) and bool(identifier.strip())
        stats[
            "document_ids_valid" if valid_shape else "document_ids_invalid"
        ] += 1

    elif path == PATHS["components"]:
        stats["components_total"] += 1
        normalized_keys = {
            str(key).replace("_", "").replace("-", "").lower()
            for key in _recursive_keys(payload)
        }
        if "contentid" in normalized_keys or "levelid" in normalized_keys:
            stats["components_raw_reference_payloads"] += 1
        else:
            stats["components_nonraw_payloads"] += 1


print("=" * 72)
print("SSP READ-ONLY PAYLOAD SEMANTICS VALIDATION")
print("=" * 72)

print("Security-impact nodes:", stats["security_total"])
print("  Empty/no source values:", stats["security_empty"])
print("  Semantically valid populated nodes:", stats["security_semantically_valid"])
print("  Semantically invalid populated nodes:", stats["security_semantically_invalid"])
print("  Incomplete objective nodes:", stats["security_incomplete_objective_nodes"])
print("  Standard value occurrences:", stats["security_standard_value_occurrences"])
print("  Reviewed legacy LOE occurrences:", stats["security_reviewed_legacy_occurrences"])
print("  Invalid type/empty occurrences:", stats["security_invalid_type_or_empty_occurrences"])
print("  Unreviewed label occurrences:", stats["security_unreviewed_label_occurrences"])

print("Status nodes:", stats["status_total"])
print("  Semantically valid:", stats["status_semantically_valid"])
print("  Semantically invalid:", stats["status_semantically_invalid"])
print("  Empty/no source state:", stats["status_empty_or_missing"])

print("Property nodes:", stats["props_total"])
print("  Valid OSCAL name/value shape:", stats["props_valid"])
print("  Invalid OSCAL name/value shape:", stats["props_invalid"])

print("Responsible-party nodes:", stats["responsible_parties_total"])
print("  Valid role/UUID shape:", stats["responsible_parties_valid"])
print("  Invalid role/UUID shape:", stats["responsible_parties_invalid"])

print("Document-ID nodes:", stats["document_ids_total"])
print("  Valid identifier shape:", stats["document_ids_valid"])
print("  Invalid identifier shape:", stats["document_ids_invalid"])

print("Component-reference nodes:", stats["components_total"])
print("  Raw Archer reference payloads:", stats["components_raw_reference_payloads"])
print("  Non-raw payloads:", stats["components_nonraw_payloads"])


phase_one_issues = {
    "security-impact normalization": stats["security_semantically_invalid"],
    "status normalization": stats["status_semantically_invalid"],
    "property shaping": stats["props_invalid"],
    "responsible-party shaping": stats["responsible_parties_invalid"],
    "document-ID shaping": stats["document_ids_invalid"],
}

remaining_phase_one = {
    name: count for name, count in phase_one_issues.items() if count
}

print("\n=== READINESS RESULT ===")
if remaining_phase_one:
    print("PHASE 1 REVIEW REQUIRED")
    for name, count in remaining_phase_one.items():
        print(" -", name + ":", count, "invalid populated nodes")
else:
    print("PHASE 1 PAYLOAD SHAPES PASSED")

required_field_source_gaps = (
    stats["security_empty"]
    + stats["security_incomplete_objective_nodes"]
    + stats["status_empty_or_missing"]
)
if required_field_source_gaps:
    print(
        "REQUIRED-FIELD SOURCE GAPS REMAIN:",
        required_field_source_gaps,
        "aggregate empty/incomplete node observations",
    )

if stats["components_raw_reference_payloads"]:
    print(
        "PHASE 2 COMPONENT HYDRATION REMAINS:",
        stats["components_raw_reference_payloads"],
        "raw reference payloads",
    )

priority_order = [
    "security-impact normalization",
    "status normalization",
    "property shaping",
    "responsible-party shaping",
    "document-ID shaping",
]

next_focus = next(
    (name for name in priority_order if phase_one_issues[name]),
    (
        "required-field source-gap review"
        if required_field_source_gaps
        else (
            "component reference hydration"
            if stats["components_raw_reference_payloads"]
            else "write-readiness review"
        )
    ),
)

print("NEXT ENGINEERING FOCUS:", next_focus)

