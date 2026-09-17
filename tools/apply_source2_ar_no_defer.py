from __future__ import annotations

import csv
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        return
    if new in text:
        return
    raise SystemExit(f"Patch anchor not found in {path}: {old!r}")


def patch_cells() -> None:
    cell3 = Path("notebooks/cells/03_canonical_mapping_contract.py")
    replace_once(
        cell3,
        '    "record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",\n',
        '    "record": "SOURCE_RECORD_ID", "optional-record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",\n',
    )
    replace_once(cell3, '"skip", "canonical-text",\n', '"skip", "canonical-text", "reference-ids",\n')
    replace_once(
        cell3,
        'None if operator in {"record", "observations"} else\n',
        'None if operator in {"record", "optional-record", "observations"} else\n',
    )
    replace_once(
        cell3,
        '            if _registry_operator(by_path[parent]) != "record":\n',
        '            if _registry_operator(by_path[parent]) not in {"record", "optional-record"}:\n',
    )
    replace_once(
        cell3,
        '        elif operator == "record":\n            parameters["parent_instance_rule"] = "singleton"\n',
        '        elif operator in {"record", "optional-record"}:\n            parameters["parent_instance_rule"] = "singleton"\n',
    )
    replace_once(
        cell3,
        '        if operator not in {"object", "record", "values"} or not re.fullmatch',
        '        if operator not in {"object", "record", "optional-record", "values"} or not re.fullmatch',
    )
    replace_once(
        cell3,
        'source == "CONFIG" and (operator not in {"object", "record"} or not target)',
        'source == "CONFIG" and (operator not in {"object", "record", "optional-record"} or not target)',
    )
    replace_once(
        cell3,
        'operator not in {"object", "record", "properties", "observations"}',
        'operator not in {"object", "record", "optional-record", "properties", "observations"}',
    )

    cell4 = Path("notebooks/cells/04_parsing_transform_payload_helpers.py")
    replace_once(
        cell4,
        'for key in ("UserList", "ValuesListIds", "ValueListIds", "ContentIds", "Ids", "Value"):',
        'for key in ("UserList", "ValuesListIds", "ValueListIds", "ContentId", "ContentIds", "Ids", "Value"):',
    )
    replace_once(
        cell4,
        '    if transform == "archer-select":\n        result = resolve_archer_select_value(value, context)\n        return result if _has_value(result) else SKIP_VALUE\n',
        '    if transform == "archer-select":\n        result = resolve_archer_select_value(value, context)\n        return result if _has_value(result) else SKIP_VALUE\n    if transform == "reference-ids":\n        result = _extract_reference_ids(value)\n        return result if _has_value(result) else SKIP_VALUE\n',
    )

    marker = "\ndef _metadata_instances(source_obj, source_id, registry_row, context):\n"
    helper = '''\ndef _metadata_descendant_has_value(path, source_obj, context):
    prefix = path + "."
    for mapped_path, rows in context["mappings_by_path"].items():
        if mapped_path != path and not mapped_path.startswith(prefix):
            continue
        for row in rows:
            params = _metadata_params(row)
            raw = (context["config"].get(row["SOURCE_FIELD_NAME"], SKIP_VALUE)
                   if params.get("value_source") == "CONFIG"
                   else resolve_json_path(source_obj, row["SOURCE_FIELD_NAME"], default=SKIP_VALUE))
            if raw is not SKIP_VALUE and _has_value(raw):
                return True
    return False


def _metadata_instances(source_obj, source_id, registry_row, context):
'''
    replace_once(cell4, marker, helper)
    replace_once(
        cell4,
        '    if operator in {"object", "record"} and (payload or parameters.get("materialize_empty") or operator == "record"):\n        instances.append({"instance_key": source_id if operator == "record" else "singleton",\n                          "payload": payload, "parent_instance_key": parent})\n',
        '    if operator == "optional-record":\n        if payload or _metadata_descendant_has_value(path, source_obj, context):\n            instances.append({"instance_key": source_id, "payload": payload, "parent_instance_key": parent})\n    elif operator in {"object", "record"} and (payload or parameters.get("materialize_empty") or operator == "record"):\n        instances.append({"instance_key": source_id if operator == "record" else "singleton",\n                          "payload": payload, "parent_instance_key": parent})\n',
    )


def update_runtime() -> None:
    runtime = Path("Mapping/sources_source_runtime.csv")
    with runtime.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        rows = list(reader)
    if not fields or "PROPERTY_NAME" not in fields:
        raise SystemExit("Runtime mapping header is invalid")
    for row in rows:
        extras = row.pop(None, None)
        if extras and any(str(value or "").strip() for value in extras):
            raise SystemExit("Runtime mapping has nonblank values beyond its header")

    updates = {
        "COMPLIANCE_RATING": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.reviewed-controls.control-selection.reviewed-control[@control-id].prop[@name='compliance-rating']",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "archer-select",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].props[]",
            "RULE_ID": "assessment-results:COMPLIANCE_RATING:property",
            "PROPERTY_NAME": "compliance-rating",
            "EXECUTION_NOTE": "Executable at the Source assessment-result grain as a named result property. This preserves the source-level aggregate without fabricating a reviewed-control control-id.",
        },
        "FINDINGS": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding[@uuid]",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "reference-ids",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:FINDINGS:finding-property",
            "PROPERTY_NAME": "source-finding-reference",
            "EXECUTION_NOTE": "Executable on the finding branch. Stable source references are preserved as finding extension properties; no duplicate finding identity is fabricated.",
        },
        "FINDINGS_AUTHORITATIVE_SOURCES": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding.related-observation",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "reference-ids",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:FINDINGS_AUTHORITATIVE_SOURCES:finding-property",
            "PROPERTY_NAME": "authoritative-source-finding-reference",
            "EXECUTION_NOTE": "Executable on the finding branch as a named extension property; no separate duplicate observation node is created.",
        },
        "CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding.collected.prop[@name='test-result']",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "direct",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT:finding-property",
            "PROPERTY_NAME": "test-result",
            "EXECUTION_NOTE": "Executable on the finding branch as named property test-result. Empty source values emit nothing.",
        },
        "DEVIATIONS_AUTHORITATIVE_SOURCES": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding[@uuid].prop[@name='deviation']",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "direct",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:DEVIATIONS_AUTHORITATIVE_SOURCES:finding-property",
            "PROPERTY_NAME": "deviation",
            "EXECUTION_NOTE": "Executable on the finding branch as named property deviation. Empty source values emit nothing.",
        },
        "DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding.related-observation.relevant-evidence.link",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "reference-ids",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS:finding-property",
            "PROPERTY_NAME": "linked-control-standard",
            "EXECUTION_NOTE": "Executable on the finding branch. Each source control-standard identifier becomes one named finding extension property; identifiers are not serialized as hrefs and no duplicate control nodes are created.",
        },
        "EVIDENCE_REPOSITORY": {
            "OSCAL_ELEMENT_PATH": "assessment-results.result.finding.relevant-evidence.link.href",
            "EXECUTION_STATUS": "APPROVED",
            "TRANSFORM_ID": "direct",
            "RUNTIME_TARGET_PATH": "assessment-results.results[].findings[].props[]",
            "RULE_ID": "assessment-results:EVIDENCE_REPOSITORY:finding-property",
            "PROPERTY_NAME": "evidence-repository",
            "EXECUTION_NOTE": "Executable on the finding branch as named evidence-repository extension property. Empty source values emit nothing.",
        },
    }

    seen: set[str] = set()
    for row in rows:
        field = row["SOURCE_FIELD_NAME"]
        if row["OSCAL_MODEL"] == "Assessment Results" and field in updates:
            row.update(updates[field])
            seen.add(field)
    missing = set(updates) - seen
    if missing:
        raise SystemExit(f"Missing Assessment Results runtime rows: {sorted(missing)}")

    with runtime.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_runtime() -> None:
    runtime = Path("Mapping/sources_source_runtime.csv")
    with runtime.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["OSCAL_MODEL"] == "Assessment Results"]
    if len(rows) != 10:
        raise SystemExit(f"Expected 10 Assessment Results rows, found {len(rows)}")
    by_field = {row["SOURCE_FIELD_NAME"]: row for row in rows}
    if len(by_field) != 10:
        raise SystemExit("Duplicate Assessment Results source fields detected")
    if by_field["_OF_NONCOMPLIANT_CONTROLS"]["EXECUTION_STATUS"] != "EXCLUDED":
        raise SystemExit("Duplicate noncompliant alias must remain excluded")
    for field, row in by_field.items():
        if field == "_OF_NONCOMPLIANT_CONTROLS":
            continue
        if row["EXECUTION_STATUS"] != "APPROVED":
            raise SystemExit(f"{field} is not APPROVED")
        if not row["TRANSFORM_ID"] or not row["RUNTIME_TARGET_PATH"] or not row["RULE_ID"]:
            raise SystemExit(f"{field} is missing executable metadata")
    owners = [
        row["SOURCE_FIELD_NAME"]
        for row in rows
        if row["EXECUTION_STATUS"] == "APPROVED" and row["PROPERTY_NAME"] == "noncompliant-count"
    ]
    if owners != ["COUNT_OF_NONCOMPLIANT_CONTROLS"]:
        raise SystemExit(f"Unexpected noncompliant-count owners: {owners}")


if __name__ == "__main__":
    patch_cells()
    update_runtime()
    validate_runtime()
    print("SOURCE2_AR_NO_DEFER_PATCH_VALIDATED")
