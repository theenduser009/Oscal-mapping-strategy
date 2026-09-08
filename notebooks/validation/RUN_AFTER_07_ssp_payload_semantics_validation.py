# Read-only SSP payload-semantics validation
#
# Run this temporary Snowflake Python cell after Mapper V1 Cell 7.  It checks
# aggregate payload shapes and semantic value classes without printing source
# records or payload contents.  It creates no permanent objects and performs
# no DIM or FACT writes. OSCAL SSP 1.2.3 is used provisionally until the
# project pins a version in CONFIG. This validates only the currently mapped
# payload scope; it is not whole-document OSCAL conformance validation.

from collections import Counter
import json
import uuid


PROVISIONAL_OSCAL_VERSION = "1.2.3"

required_semantic_objects = {
    "CONFIG": globals().get("CONFIG"),
    "final_nodes_df": globals().get("final_nodes_df"),
    "source_df": globals().get("source_df"),
    "run_result": globals().get("run_result"),
}
missing_semantic_objects = [
    name for name, value in required_semantic_objects.items() if value is None
]
if missing_semantic_objects:
    raise RuntimeError(
        "Run Mapper V1 Cells 1 through 7 first. Missing notebook state: "
        + ", ".join(missing_semantic_objects)
    )
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running semantic validation."
    )

if not run_result.get("validation_passed", False):
    raise RuntimeError("Run Mapper V1 Cells 1 through 7 successfully first.")
configured_oscal_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
if (
    configured_oscal_version
    and configured_oscal_version != PROVISIONAL_OSCAL_VERSION
):
    raise RuntimeError(
        "This validator implements OSCAL SSP 1.2.3 cardinality. "
        "CONFIG pins a different OSCAL_VERSION; use a version-specific validator."
    )


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

SECURITY_OBJECTIVES = (
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
)

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
    try:
        if value is None:
            return {}, True
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


def _security_label_token(value):
    # Security objectives are strings, not a status-style controlled enum.
    # Normalize only to recognize the explicitly reviewed source label family.
    return "-".join(str(value).strip().lower().replace("_", "-").split())


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
source_ids = set()
source_rows_seen = 0
blank_source_ids = 0
duplicate_source_rows = 0
for source_row in source_df.select("SOURCE_RECORD_ID").to_local_iterator():
    source_rows_seen += 1
    raw_record_id = source_row["SOURCE_RECORD_ID"]
    record_id = "" if raw_record_id is None else str(raw_record_id).strip()
    if not record_id:
        blank_source_ids += 1
    elif record_id in source_ids:
        duplicate_source_rows += 1
    else:
        source_ids.add(record_id)

security_node_counts = Counter()
status_node_counts = Counter()
security_node_records = set()
status_node_records = set()

for row in final_nodes_df.select(
    "SOURCE_RECORD_ID",
    "ELEMENT_PATH",
    "METADATA_JSON",
).to_local_iterator():
    raw_record_id = row["SOURCE_RECORD_ID"]
    record_id = "" if raw_record_id is None else str(raw_record_id).strip()
    path = str(row["ELEMENT_PATH"])
    payload, payload_shape_error = _payload_dict(row["METADATA_JSON"])

    if path == PATHS["security_impact"]:
        stats["security_total"] += 1
        security_node_counts[record_id] += 1
        security_node_records.add(record_id)
        if payload_shape_error:
            stats["security_payload_parse_or_shape_errors"] += 1
            stats["security_populated_value_invalid"] += 1
            continue
        if not payload:
            # security-impact-level is optional in OSCAL SSP 1.2.3. The
            # registry graph still materializes an empty structural node; a
            # final serializer should omit that absent optional assembly.
            stats["security_absent_optional"] += 1
            continue

        present_objectives = {
            objective
            for objective in SECURITY_OBJECTIVES
            if (
                isinstance(payload.get(objective), str)
                and bool(payload.get(objective).strip())
            )
        }
        missing_objectives = [
            objective
            for objective in SECURITY_OBJECTIVES
            if objective not in present_objectives
        ]
        if missing_objectives:
            stats["security_partial_assemblies"] += 1
            stats[
                "security_missing_required_objective_occurrences"
            ] += len(missing_objectives)
            for objective in missing_objectives:
                stats["security_missing_" + objective] += 1
        else:
            stats["security_complete_assemblies"] += 1

        invalid_value_found = False
        for objective in SECURITY_OBJECTIVES:
            if objective not in payload:
                continue
            value = payload.get(objective)
            if not isinstance(value, str) or not value.strip():
                invalid_value_found = True
                stats["security_invalid_type_or_empty_occurrences"] += 1
                continue

            security_token = _security_label_token(value)
            if security_token in ALLOWED_SECURITY_VALUES:
                stats["security_standard_value_occurrences"] += 1
            elif security_token in REVIEWED_LEGACY_SECURITY_VALUES:
                # OSCAL defines these objective fields as strings. Preserve
                # reviewed legacy LOE labels without claiming a FIPS level.
                stats["security_reviewed_legacy_occurrences"] += 1
            else:
                invalid_value_found = True
                stats["security_unreviewed_label_occurrences"] += 1

        if present_objectives and not invalid_value_found:
            stats["security_populated_value_valid"] += 1
        else:
            stats["security_populated_value_invalid"] += 1

    elif path == PATHS["status"]:
        stats["status_total"] += 1
        status_node_counts[record_id] += 1
        status_node_records.add(record_id)
        if payload_shape_error:
            stats["status_payload_parse_or_shape_errors"] += 1
            stats["status_semantically_invalid"] += 1
            continue
        state = payload.get("state")
        if not isinstance(state, str) or not state.strip():
            stats["status_empty_or_missing"] += 1
            continue

        valid_state = state in ALLOWED_STATUS_VALUES
        valid_other_remarks = (
            state != "other"
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
        if payload_shape_error:
            stats["props_invalid"] += 1
            stats["other_payload_parse_or_shape_errors"] += 1
            continue
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
        if payload_shape_error:
            stats["responsible_parties_invalid"] += 1
            stats["other_payload_parse_or_shape_errors"] += 1
            continue
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
        if payload_shape_error:
            stats["document_ids_invalid"] += 1
            stats["other_payload_parse_or_shape_errors"] += 1
            continue
        identifier = payload.get("identifier")
        valid_shape = isinstance(identifier, str) and bool(identifier.strip())
        stats[
            "document_ids_valid" if valid_shape else "document_ids_invalid"
        ] += 1

    elif path == PATHS["components"]:
        stats["components_total"] += 1
        if payload_shape_error:
            stats["components_invalid_payload_shape"] += 1
            stats["other_payload_parse_or_shape_errors"] += 1
            continue
        normalized_keys = {
            str(key).replace("_", "").replace("-", "").lower()
            for key in _recursive_keys(payload)
        }
        if "contentid" in normalized_keys or "levelid" in normalized_keys:
            stats["components_raw_reference_payloads"] += 1
        else:
            stats["components_nonraw_payloads"] += 1


duplicate_security_nodes = sum(
    count - 1 for count in security_node_counts.values() if count > 1
)
duplicate_status_nodes = sum(
    count - 1 for count in status_node_counts.values() if count > 1
)
missing_security_nodes = source_ids - security_node_records
missing_status_nodes = source_ids - status_node_records
orphan_security_nodes = security_node_records - source_ids
orphan_status_nodes = status_node_records - source_ids


print("=" * 72)
print("SSP READ-ONLY PAYLOAD SEMANTICS VALIDATION")
print("Provisional evaluation target: OSCAL SSP", PROVISIONAL_OSCAL_VERSION)
print("CONFIG-pinned OSCAL version:", CONFIG.get("OSCAL_VERSION", "<not pinned>"))
print("=" * 72)

print("Security-impact nodes:", stats["security_total"])
print("  Optional absent assemblies:", stats["security_absent_optional"])
print("  Assemblies whose present objective values are valid (cardinality separate):", stats["security_populated_value_valid"])
print("  Assemblies with invalid values/payload shape:", stats["security_populated_value_invalid"])
print("  Complete C/I/A assemblies:", stats["security_complete_assemblies"])
print("  Partial C/I/A assemblies:", stats["security_partial_assemblies"])
print("  Missing required objective occurrences in partial assemblies:", stats["security_missing_required_objective_occurrences"])
print("    Missing confidentiality:", stats["security_missing_security-objective-confidentiality"])
print("    Missing integrity:", stats["security_missing_security-objective-integrity"])
print("    Missing availability:", stats["security_missing_security-objective-availability"])
print("  Standard value occurrences:", stats["security_standard_value_occurrences"])
print("  Reviewed legacy LOE occurrences:", stats["security_reviewed_legacy_occurrences"])
print("  Invalid type/empty occurrences:", stats["security_invalid_type_or_empty_occurrences"])
print("  Unreviewed label occurrences:", stats["security_unreviewed_label_occurrences"])
print("  Payload parse/non-object errors:", stats["security_payload_parse_or_shape_errors"])
print("  Missing structural nodes for source records:", len(missing_security_nodes))
print("  Duplicate singleton nodes:", duplicate_security_nodes)
print("  Orphan node records:", len(orphan_security_nodes))

print("Status nodes:", stats["status_total"])
print("  Semantically valid:", stats["status_semantically_valid"])
print("  Semantically invalid:", stats["status_semantically_invalid"])
print("  Empty/no source state:", stats["status_empty_or_missing"])
print("  Payload parse/non-object errors:", stats["status_payload_parse_or_shape_errors"])
print("  Missing nodes for source records:", len(missing_status_nodes))
print("  Duplicate singleton nodes:", duplicate_status_nodes)
print("  Orphan node records:", len(orphan_status_nodes))

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
print("  Non-raw payloads (not schema-validated here):", stats["components_nonraw_payloads"])
print("  Invalid payload shape:", stats["components_invalid_payload_shape"])

print("Source rows:", source_rows_seen)
print("Unique source records:", len(source_ids))
print("Blank source IDs:", blank_source_ids)
print("Duplicate source rows:", duplicate_source_rows)


populated_value_issues = {
    "security-impact value normalization": stats["security_populated_value_invalid"],
    "status normalization": stats["status_semantically_invalid"],
    "property shaping": stats["props_invalid"],
    "responsible-party shaping": stats["responsible_parties_invalid"],
    "document-ID shaping": stats["document_ids_invalid"],
    "component payload shaping": stats["components_invalid_payload_shape"],
}

remaining_value_issues = {
    name: count for name, count in populated_value_issues.items() if count
}

print("\n=== INDIVIDUAL VALUE-SHAPE RESULT ===")
if remaining_value_issues:
    print("POPULATED VALUE-SHAPE REVIEW REQUIRED")
    for name, count in remaining_value_issues.items():
        print(" -", name + ":", count, "invalid populated nodes")
else:
    print("INDIVIDUAL POPULATED VALUE TOKENS/SHAPES PASSED")

missing_status_occurrences = (
    stats["status_empty_or_missing"] + len(missing_status_nodes)
)
missing_required_occurrences = (
    stats["security_missing_required_objective_occurrences"]
    + missing_status_occurrences
)
if missing_required_occurrences:
    print(
        "OSCAL 1.2.3 CARDINALITY/REQUIRED-FIELD GAPS:",
        missing_required_occurrences,
        "missing required field occurrences",
    )
    print(
        "  Missing objectives inside partial security-impact assemblies:",
        stats["security_missing_required_objective_occurrences"],
    )
    print(
        "  Missing required status.state occurrences:",
        missing_status_occurrences,
    )
print(
    "OPTIONAL ABSENT SECURITY-IMPACT ASSEMBLIES (NOT REQUIRED GAPS):",
    stats["security_absent_optional"],
)

mapped_scope_issues = {
    "partial security-impact assemblies": stats["security_partial_assemblies"],
    "missing required status.state occurrences": missing_status_occurrences,
    "invalid mapped value/payload observations": sum(remaining_value_issues.values()),
    "blank/duplicate source identity observations": blank_source_ids + duplicate_source_rows,
    "missing security structural nodes": len(missing_security_nodes),
    "duplicate security singleton nodes": duplicate_security_nodes,
    "orphan security node records": len(orphan_security_nodes),
    "duplicate status singleton nodes": duplicate_status_nodes,
    "orphan status node records": len(orphan_status_nodes),
    "raw Archer component-reference payloads": stats["components_raw_reference_payloads"],
}
remaining_mapped_scope_issues = {
    name: count for name, count in mapped_scope_issues.items() if count
}

print("\n=== CURRENT MAPPED-SCOPE RESULT ===")
if remaining_mapped_scope_issues:
    print("CURRENT MAPPED-SCOPE REVIEW REQUIRED")
    for name, count in remaining_mapped_scope_issues.items():
        print(" -", name + ":", count)
else:
    print("CURRENT MAPPED-SCOPE CHECK PASSED")

if stats["components_raw_reference_payloads"]:
    print(
        "PHASE 2 COMPONENT HYDRATION REMAINS:",
        stats["components_raw_reference_payloads"],
        "raw reference payloads",
    )

priority_order = [
    "security-impact value normalization",
    "status normalization",
    "property shaping",
    "responsible-party shaping",
    "document-ID shaping",
    "component payload shaping",
]

next_focus = next(
    (name for name in priority_order if populated_value_issues[name]),
    (
        "OSCAL 1.2.3 security/status cardinality source-gap review"
        if missing_required_occurrences
        else (
            "component reference hydration"
            if stats["components_raw_reference_payloads"]
            else (
                "mapped-scope structural review"
                if remaining_mapped_scope_issues
                else "full SSP scope and assembled-document validation"
            )
        )
    ),
)

print("NEXT ENGINEERING FOCUS:", next_focus)
print(
    "FULL-SCOPE WARNING: this mapped-subset check does not validate a complete "
    "assembled SSP or authorize writes."
)

