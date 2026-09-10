# Assessment Results batch 1: actual in-memory mapping, not a grouping report.
# Run in the existing notebook session after Cells 2 and 4 have initialized.
# Does not change CONFIG, SSP outputs, registry, DIM or FACT. No database writes.
import datetime
import json
import math
import re
from decimal import Decimal


AR_SCORE_FIELDS = (
    "VULNERABILITY_SCORE", "ANTIVIRUS_SCORE", "PATCH_SCORE",
    "SECURITY_COMPLIANCE_SCORE",
)
AR_ROOT_PATH = "assessment-results"
AR_RESULT_PATH = "assessment-results.results[]"
AR_OBSERVATION_PATH = "assessment-results.results[].observations[]"
AR_SCORE_NOTES = "archer specific risk scoring map as observation"
AR_SOURCE_TABLE = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
AR_RAW_TABLE = "RTX_RAW_DEV.ES_ESC_GRC." + AR_SOURCE_TABLE
AR_HELPERS = (
    "_parse_source_json", "resolve_json_path", "_has_value",
    "_stable_property_name", "_contains_archer_select_id_container",
    "resolve_archer_select_value", "_oscal_property_values",
    "_deterministic_hash", "_deterministic_uuid",
)


def _ar_words(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _ar_row_dict(row):
    if hasattr(row, "as_dict"):
        row = row.as_dict(recursive=True)
    if not isinstance(row, dict):
        raise ValueError("Expected a mapping or registry row object")
    result = {}
    for key, value in row.items():
        name = str(key).strip().upper()
        if name in result:
            raise ValueError("Duplicate normalized metadata column")
        result[name] = value
    return result


def _ar_mapping_contract(mapping_rows):
    aliases = {
        "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME", "SOURCE_FIELD": "SOURCE_FIELD_NAME",
        "MODEL": "OSCAL_MODEL", "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
        "ELEMENT_PATH": "OSCAL_ELEMENT_PATH", "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
        "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME", "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
        "MAPPING_STATUS": "STATUS",
    }
    found = {field: [] for field in AR_SCORE_FIELDS}
    other_rows = 0
    for original in mapping_rows:
        normalized = _ar_row_dict(original)
        row = {}
        for key, value in normalized.items():
            canonical = aliases.get(key, key)
            if canonical in row:
                raise ValueError("Ambiguous mapping column aliases")
            if value is None or (isinstance(value, float) and math.isnan(value)):
                value = ""
            row[canonical] = value
        field = row.get("SOURCE_FIELD_NAME", "")
        path = str(row.get("OSCAL_ELEMENT_PATH", "")).strip()
        model = _ar_words(row.get("OSCAL_MODEL")).replace(" ", "")
        in_ar = model == "assessmentresults" or path.startswith(AR_ROOT_PATH + ".")
        if not in_ar:
            continue
        if field in found:
            found[field].append(row)
        else:
            other_rows += 1
    errors = []
    for field, rows in found.items():
        if len(rows) != 1:
            errors.append({"field": field, "issue": "expected_one_mapping_row", "rows": len(rows)})
            continue
        row = rows[0]
        checks = {
            "model": _ar_words(row.get("OSCAL_MODEL")).replace(" ", "") == "assessmentresults",
            "target": str(row.get("OSCAL_ELEMENT_PATH", "")).strip() == AR_OBSERVATION_PATH,
            "mapping_type": _ar_words(row.get("MAPPING_TYPE")) == "extension property",
            "notes": _ar_words(row.get("NOTES")) == AR_SCORE_NOTES,
            "target_member": not str(row.get("OSCAL_FIELD_NAME", "")).strip(),
            "extra_transform": not str(row.get("TRANSFORMATION_LOGIC", "")).strip(),
            "extra_notes": not str(row.get("MAPPING_NOTES", "")).strip(),
            "status": _ar_words(row.get("STATUS")) not in {
                "tbd", "deferred", "blocked", "more information needed", "not mapped",
            },
        }
        errors.extend({"field": field, "issue": "contract_" + key}
                      for key, valid in checks.items() if not valid)
    return errors, other_rows


def _ar_registry_contract(registry_rows):
    expected = {
        AR_ROOT_PATH: (None, False, None),
        AR_RESULT_PATH: (AR_ROOT_PATH, True, "SOURCE_RECORD_ID"),
        AR_OBSERVATION_PATH: (AR_RESULT_PATH, True, "SOURCE_FIELD_NAME"),
    }
    found = {path: [] for path in expected}
    for original in registry_rows:
        row = _ar_row_dict(original)
        if str(row.get("OSCAL_MODEL_KEY", "")).strip().upper() != "ASSESSMENT_RESULTS":
            continue
        path = str(row.get("NODE_PATH", "")).strip()
        if path in found:
            found[path].append(row)
    errors, selected = [], {}
    for path, matches in found.items():
        if len(matches) != 1:
            errors.append({"path": path, "issue": "expected_one_registry_row", "rows": len(matches)})
            continue
        row = matches[0]
        parent, collection, rule = expected[path]
        active = str(row.get("IS_ACTIVE", "")).strip().upper()
        flag = str(row.get("IS_COLLECTION", "")).strip().upper()
        actual_parent = row.get("PARENT_NODE_PATH")
        actual_parent = str(actual_parent).strip() if actual_parent else None
        checks = {
            "active": active in {"TRUE", "T", "YES", "Y", "1"},
            "parent": actual_parent == parent,
            "collection": flag in ({"TRUE", "T", "YES", "Y", "1"} if collection
                                   else {"FALSE", "F", "NO", "N", "0"}),
            "element_type": isinstance(row.get("ELEMENT_TYPE"), str) and bool(row["ELEMENT_TYPE"].strip()),
        }
        if rule:
            checks["instance_rule"] = str(row.get("INSTANCE_KEY_RULE", "")).strip() == rule
            checks["element_type"] = row.get("ELEMENT_TYPE") == path.rsplit(".", 1)[-1].replace("[]", "")
            # The saved AR collection contract uses no nested extraction path.
            checks["item_path"] = row.get("ITEM_PATH") in (None, "")
        errors.extend({"path": path, "issue": "registry_" + key}
                      for key, valid in checks.items() if not valid)
        selected[path] = row
    return errors, selected


def _ar_score_value(value, helpers):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Score must be finite")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError("Score must be finite")
    if not helpers["_has_value"](value):
        return None
    # Bare scores must never go through the lookup's scalar-ID fallback.
    if helpers["_contains_archer_select_id_container"](value):
        value = helpers["resolve_archer_select_value"](value)
    values = value if isinstance(value, list) else [value]
    if len(values) != 1:
        raise ValueError("One scalar score is required per observation")
    item = values[0]
    if not isinstance(item, (str, int, float, bool, Decimal)):
        raise ValueError("Score must resolve to a scalar")
    if isinstance(item, float) and not math.isfinite(item):
        raise ValueError("Score must be finite")
    if isinstance(item, Decimal) and not item.is_finite():
        raise ValueError("Score must be finite")
    normalized = helpers["_oscal_property_values"](value)
    if len(normalized) != 1 or normalized[0].lower() in {"infinity", "+infinity", "-infinity"}:
        raise ValueError("One finite scalar score is required")
    return normalized[0]


def build_ar_score_batch(source_records, mapping_rows, registry_rows, config, helpers):
    """Return separate in-memory nodes, edges, partial documents and aggregate report."""
    if config.get("EXECUTE_WRITES") is not False:
        raise ValueError("Keep mapper writes disabled before running this read-only batch")
    if (config.get("SOURCE_SYSTEM_NAME") != "ARCHER"
            or config.get("SOURCE_TABLE_NAME") != AR_SOURCE_TABLE
            or config.get("RAW_TABLE") != AR_RAW_TABLE):
        raise ValueError("This batch is restricted to the existing Source One input")
    if any(not callable(helpers.get(name)) for name in AR_HELPERS):
        raise ValueError("Run existing Cell 4 to initialize the shared helpers")
    mapping_errors, outside_batch = _ar_mapping_contract(mapping_rows)
    registry_errors, registry = _ar_registry_contract(registry_rows)
    report = {
        "MODEL": "ASSESSMENT_RESULTS", "TARGET_PATH": AR_OBSERVATION_PATH,
        "STATUS": "BLOCKED", "SELECTED_FIELDS": list(AR_SCORE_FIELDS),
        "OTHER_AR_MAPPING_ROWS_NOT_PROCESSED": outside_batch,
        "MAPPING_CONTRACT_ERRORS": mapping_errors, "REGISTRY_CONTRACT_ERRORS": registry_errors,
        "SOURCE_RECORDS": 0, "INVALID_SOURCE_RECORDS": 0, "DUPLICATE_SOURCE_RECORDS": 0,
        "FIELDS": {f: {"emitted": 0, "missing": 0, "invalid": 0} for f in AR_SCORE_FIELDS},
        "WRITES_EXECUTED": False, "FULL_MODEL_COMPLETE": False, "SCHEMA_VALIDATED": False,
    }
    empty = {"nodes": [], "edges": [], "documents": {}, "report": report}
    if mapping_errors or registry_errors:
        return empty  # No source values are read when the metadata contract is blocked.
    nodes, edges, documents, seen = [], [], {}, set()
    load_time = datetime.datetime.now(datetime.timezone.utc)
    run_id = load_time.strftime("%Y%m%dT%H%M%SZ")
    identity_version = config.get("IDENTITY_VERSION")
    if not isinstance(identity_version, str) or not identity_version.strip():
        raise ValueError("Missing shared identity version")

    def node(source_id, path, instance, parent_instance, payload):
        identity = (identity_version, "ARCHER", AR_SOURCE_TABLE, source_id,
                    "ASSESSMENT_RESULTS", path, instance)
        node_key = helpers["_deterministic_hash"](*identity)
        node_uuid = helpers["_deterministic_uuid"](*identity)
        payload = {"uuid": node_uuid, **payload}
        item = {
            "NODE_KEY": node_key, "ELEMENT_PATH": path, "INSTANCE_KEY": instance,
            "PARENT_INSTANCE_KEY": parent_instance, "OSCAL_UUID": node_uuid,
            "ELEMENT_TYPE": registry[path]["ELEMENT_TYPE"],
            "METADATA_JSON": json.dumps(payload, sort_keys=True, allow_nan=False),
            "SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": AR_SOURCE_TABLE,
            "SOURCE_RECORD_ID": source_id, "DW_PIPELINE_RUN_ID": run_id,
            "DW_LOAD_TIMESTAMP": load_time, "DW_LOAD_TIMESTAMP_TZ": load_time,
        }
        nodes.append(item)
        return item, payload

    def contain(parent, child):
        if child["PARENT_INSTANCE_KEY"] != parent["INSTANCE_KEY"]:
            raise ValueError("Assessment result parent identity mismatch")
        edges.append({
            "EDGE_KEY": helpers["_deterministic_hash"]("edge-v1", parent["NODE_KEY"], child["NODE_KEY"], "CONTAINS"),
            "FK_SOURCE_ELEMENT_HASH": parent["NODE_KEY"], "FK_TARGET_ELEMENT_HASH": child["NODE_KEY"],
            "DEPENDENCY_TYPE": "CONTAINS", "SOURCE_OSCAL_UUID": parent["OSCAL_UUID"],
            "TARGET_OSCAL_UUID": child["OSCAL_UUID"],
        })

    for original in source_records:
        report["SOURCE_RECORDS"] += 1
        source_id = original["SOURCE_RECORD_ID"]
        if not isinstance(source_id, str) or not source_id.strip() or source_id != source_id.strip():
            report["INVALID_SOURCE_RECORDS"] += 1
            continue
        if source_id in seen:
            report["DUPLICATE_SOURCE_RECORDS"] += 1
            continue
        seen.add(source_id)
        try:
            raw_json = original["CURATED_JSON"]
            # Preserve JSON decimal precision for score-to-string conversion.
            source_obj = (json.loads(raw_json, parse_float=Decimal)
                          if isinstance(raw_json, str)
                          else helpers["_parse_source_json"](original))
            if not isinstance(source_obj, dict):
                raise ValueError("Source JSON must be an object")
        except (TypeError, ValueError):
            report["INVALID_SOURCE_RECORDS"] += 1
            continue
        root, root_payload = node(source_id, AR_ROOT_PATH, "singleton", None, {})
        result, result_payload = node(source_id, AR_RESULT_PATH, source_id, "singleton", {})
        contain(root, result)
        observations = []
        for field in AR_SCORE_FIELDS:
            try:
                value = _ar_score_value(helpers["resolve_json_path"](source_obj, field), helpers)
            except (TypeError, ValueError, ArithmeticError):
                report["FIELDS"][field]["invalid"] += 1
                continue
            if value is None:
                report["FIELDS"][field]["missing"] += 1
                continue
            observation, observation_payload = node(source_id, AR_OBSERVATION_PATH, field, source_id, {
                "props": [{"name": helpers["_stable_property_name"](field), "value": value}],
            })
            contain(result, observation)
            observations.append(observation_payload)
            report["FIELDS"][field]["emitted"] += 1
        if observations:
            result_payload["observations"] = observations
        root_payload["results"] = [result_payload]
        documents[source_id] = {AR_ROOT_PATH: root_payload}
    report["CANDIDATE_NODES"] = len(nodes)
    report["CANDIDATE_EDGES"] = len(edges)
    report["COUNTS_ARE_CANDIDATES"] = True
    invalid = report["INVALID_SOURCE_RECORDS"] + report["DUPLICATE_SOURCE_RECORDS"]
    invalid += sum(r["invalid"] for r in report["FIELDS"].values())
    keys = {n["NODE_KEY"] for n in nodes}
    report["DUPLICATE_NODE_KEYS"] = len(nodes) - len(keys)
    report["DUPLICATE_EDGE_KEYS"] = len(edges) - len({e["EDGE_KEY"] for e in edges})
    report["DANGLING_EDGES"] = sum(e["FK_SOURCE_ELEMENT_HASH"] not in keys or
                                   e["FK_TARGET_ELEMENT_HASH"] not in keys for e in edges)
    invalid += report["DUPLICATE_NODE_KEYS"] + report["DUPLICATE_EDGE_KEYS"] + report["DANGLING_EDGES"]
    if invalid or not report["SOURCE_RECORDS"]:
        report["OUTPUTS_PUBLISHED"] = False
        return empty  # Never expose a successful-looking partial batch after an error.
    report.update(STATUS="MAPPED_SCOPE_BUILT", OUTPUTS_PUBLISHED=True,
                  NODES=len(nodes), EDGES=len(edges), DOCUMENTS=len(documents),
                  COUNTS_ARE_CANDIDATES=False)
    report["FIELDS_WITH_POPULATED_EVIDENCE"] = sum(r["emitted"] > 0 for r in report["FIELDS"].values())
    return {"nodes": nodes, "edges": edges, "documents": documents, "report": report}


if __name__ == "__main__":
    # Clear only this batch's previous outputs, so a failed rerun cannot look current.
    AR_SCORE_BATCH = None
    AR_SCORE_NODES = []
    AR_SCORE_EDGES = []
    AR_SCORE_DOCUMENTS = {}
    AR_SCORE_RUN_REPORT = {"STATUS": "NOT_RUN", "WRITES_EXECUTED": False}
    required = ("source_df", "mapping_artifact_pdf", "element_registry_df", "CONFIG")
    if any(name not in globals() for name in required):
        raise RuntimeError("Initialize existing notebook Cells 1, 2 and 4 first; no SSP rerun is needed")
    def _ar_source_records():
        yield from source_df.to_local_iterator()

    AR_SCORE_BATCH = build_ar_score_batch(
        _ar_source_records(), mapping_artifact_pdf.to_dict(orient="records"),
        element_registry_df.collect(), CONFIG,
        {name: globals().get(name) for name in AR_HELPERS},
    )
    AR_SCORE_NODES = AR_SCORE_BATCH["nodes"]
    AR_SCORE_EDGES = AR_SCORE_BATCH["edges"]
    AR_SCORE_DOCUMENTS = AR_SCORE_BATCH["documents"]
    AR_SCORE_RUN_REPORT = AR_SCORE_BATCH["report"]
    print(json.dumps(AR_SCORE_RUN_REPORT, indent=2))
