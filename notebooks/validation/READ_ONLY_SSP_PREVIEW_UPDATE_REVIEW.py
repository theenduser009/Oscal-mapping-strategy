# Paste into one new Python cell in the existing accepted SSP PREVIEW session.
# Reuses MODEL_GRAPHS, PIPELINE_REPORT and frozen SOURCE_INPUTS; no graph rerun or explicit table/view creation.
# Snowpark may internally materialize its existing list-backed candidate frame.
# Output contains aggregates only. This review does not authorize COMMIT.
import json
from collections import Counter, defaultdict
from decimal import Decimal


class PreviewReviewError(ValueError):
    pass


def _preview_json_changes(old, new, path=""):
    """JSON pointers preserve literal keys, absent/null, booleans and array order."""
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(old.keys() | new.keys()):
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in old or key not in new:
                yield pointer, "ADDED" if key not in old else "REMOVED"
            else:
                yield from _preview_json_changes(old[key], new[key], pointer)
    elif isinstance(old, list) and isinstance(new, list):
        for index in range(max(len(old), len(new))):
            pointer = path + "/" + str(index)
            if index >= len(old) or index >= len(new):
                yield pointer, "ADDED" if index >= len(old) else "REMOVED"
            else:
                yield from _preview_json_changes(old[index], new[index], pointer)
    elif isinstance(old, bool) != isinstance(new, bool) or old != new:
        yield path, "CHANGED"


def _preview_comparison_frame(session, nodes, storage):
    fields = [name for name in _DIM_FIELDS if name not in _AUDIT]
    candidate = nodes.select_expr(
        "TO_BINARY(NODE_KEY, 'HEX') AS REVIEW_KEY", "ELEMENT_PATH",
        "SOURCE_RECORD_ID AS REVIEW_RECORD", "DW_PIPELINE_RUN_ID AS REVIEW_RUN",
        *[("PARSE_JSON(METADATA_JSON)" if name == "METADATA_JSON" else
           "REPLACE(OSCAL_UUID, '-', '')" if name == "OSCAL_UUID" else name) + " AS NEW_" + name
          for name in fields])
    target = session.table(storage["TARGET_DIM"]).select_expr(
        storage["DIM_PK_COLUMN"] + " AS TARGET_KEY", *[name + " AS OLD_" + name for name in fields])
    different = "TARGET_KEY IS NOT NULL AND NEW_METADATA_JSON IS DISTINCT FROM OLD_METADATA_JSON"
    identity = " OR ".join("NEW_" + name + " IS DISTINCT FROM OLD_" + name
                           for name in fields if name != "METADATA_JSON")
    return candidate.join(target, candidate["REVIEW_KEY"] == target["TARGET_KEY"], "left").select_expr(
        "REVIEW_KEY", "ELEMENT_PATH", "REVIEW_RECORD", "REVIEW_RUN",
        "TARGET_KEY IS NULL AS MISSING_TARGET", different + " AS PAYLOAD_CHANGED",
        "TARGET_KEY IS NOT NULL AND (" + identity + ") AS IDENTITY_CHANGED",
        "CASE WHEN " + different + " THEN TO_JSON(OLD_METADATA_JSON) END AS OLD_JSON",
        "CASE WHEN " + different + " THEN TO_JSON(NEW_METADATA_JSON) END AS NEW_JSON")


def _preview_summarize(rows, expected, run_id):
    keys, records, affected = set(), set(), set()
    counts, anomalies = Counter(), Counter()
    elements, members = defaultdict(set), defaultdict(set)
    element_nodes, member_nodes = Counter(), Counter()
    for row in rows:
        key, record, path = bytes(row["REVIEW_KEY"]), row["REVIEW_RECORD"], row["ELEMENT_PATH"]
        anomalies["DUPLICATE_JOINED_KEYS"] += key in keys
        anomalies["CANDIDATE_RUN_MISMATCH"] += row["REVIEW_RUN"] != run_id
        anomalies["IDENTITY_PROVENANCE_CHANGED"] += bool(row["IDENTITY_CHANGED"])
        keys.add(key)
        records.add(record)
        changed = row["PAYLOAD_CHANGED"] or row["IDENTITY_CHANGED"]
        category = "INSERTS" if row["MISSING_TARGET"] else "UPDATES" if changed else "UNCHANGED"
        counts[category] += 1
        if category != "UPDATES":
            continue
        affected.add(record)
        elements[path].add(record)
        element_nodes[path] += 1
        if not row["PAYLOAD_CHANGED"]:
            continue
        old, new = (json.loads(row[name], parse_float=Decimal) if row[name] is not None else None
                    for name in ("OLD_JSON", "NEW_JSON"))
        differences = list(_preview_json_changes(old, new))
        anomalies["SQL_CHANGED_WITHOUT_JSON_DIFFERENCE"] += not differences
        for pointer, kind in differences:
            group = (path, pointer, kind)
            members[group].add(record)
            member_nodes[group] += 1
    actual = {name: counts[name] for name in ("INSERTS", "UPDATES", "UNCHANGED")}
    drift = (actual != expected["expected_changes"]["D"] or len(keys) != expected["nodes"]
             or len(records) != expected["source_records"] or any(anomalies.values()))
    return {
        "STATUS": "READ_ONLY_REVIEW_DRIFT_DETECTED" if drift else "READ_ONLY_REVIEW_COMPLETE",
        "MODEL": "SSP", "COMPARISON": "ACCEPTED_CANDIDATE_VERSUS_CURRENT_TARGET",
        "HISTORICAL_TARGET_SNAPSHOT_AVAILABLE": False, "TARGET_DML_ATTEMPTED": False,
        "NOTE": "Matching counts do not prove the target is unchanged since PREVIEW; COMMIT is not authorized.",
        "CANDIDATE_NODES": len(keys), "SOURCE_RECORDS": len(records), "DIM": actual,
        "ACCEPTED_PREVIEW_DIM": expected["expected_changes"]["D"], "AFFECTED_SOURCE_RECORDS": len(affected),
        "ANOMALIES": dict(sorted(anomalies.items())),
        "BY_ELEMENT_PATH": [{"ELEMENT_PATH": path, "CHANGED_NODES": element_nodes[path],
                             "AFFECTED_SOURCE_RECORDS": len(elements[path])} for path in sorted(elements)],
        "BY_JSON_MEMBER": [{"ELEMENT_PATH": path, "JSON_POINTER": pointer, "CHANGE": kind,
                            "CHANGED_NODES": member_nodes[(path, pointer, kind)],
                            "AFFECTED_SOURCE_RECORDS": len(members[(path, pointer, kind)])}
                           for path, pointer, kind in sorted(members)],
    }


def _preview_controlled_value(value, allowed):
    if isinstance(value, str) and (value.lower() in {
            "low", "moderate", "high", "fips-199-low", "fips-199-moderate", "fips-199-high"} or value in allowed):
        return value
    return "REDACTED_" + ("NULL" if value is None else type(value).__name__.upper())


def _preview_value_relation(old, new):
    if type(old) is type(new) and old == new:
        return "EXACT_MATCH"
    if isinstance(old, str) and isinstance(new, str) and old.lower() == new.lower():
        return "CASE_ONLY"
    return "OTHER_TRANSITION"


def _preview_source_label(raw, context):
    """Do not filter unknown IDs before checking whether a field is single valued."""
    extracted = _extract_reference_ids(raw)
    values = extracted if isinstance(extracted, list) else [extracted]
    labels, states = [], []
    for value in values:
        if value is None or isinstance(value, str) and not value.strip():
            labels.append(None)
            states.append("EMPTY")
            continue
        label = context["lookups"].get("archer_values", {}).get(str(value).strip())
        state = "SINGLE_LOOKUP"
        if isinstance(value, (dict, list, bool)):
            state, label = "INVALID_SHAPE", None
        elif not isinstance(label, str) or not label.strip():
            if isinstance(value, str) and not value.strip().isdigit() and not _contains_archer_select_id_container(raw):
                state, label = "DIRECT_TEXT", value.strip()
            else:
                state, label = "UNKNOWN_ID", None
        labels.append(label)
        states.append(state)
    if not values:
        return None, "EMPTY"
    if len(values) > 1:
        return None, "MULTIPLE_WITH_UNKNOWN_IDS" if "UNKNOWN_ID" in states else "MULTIPLE_VALUES"
    return labels[0], states[0]


def _preview_value_reconciliation(rows, context, source_input):
    impact_path = "system-security-plan.system-characteristics.security-impact-level"
    sensitivity_path, sensitivity = "system-security-plan.system-characteristics", "security-sensitivity-level"
    mappings = [row for row in context["compiled_plan"]["mappings"]
                if row["TRANSFORM_ID"] == "security-objective" and row["OWNER_ELEMENT_PATH"] == impact_path]
    by_objective = defaultdict(list)
    for mapping in mappings:
        by_objective[_metadata_target(mapping)].append(mapping)
    allowed = {value for mapping in mappings for value in mapping["TRANSFORM_PARAMS"].get("approved_legacy_values", ())}
    lookups = context["lookups"]
    lower_context = dict(context, lookups=dict(lookups, fips_values={
        key: value.lower() if isinstance(value, str) and value.lower() in {"low", "moderate", "high"} else value
        for key, value in lookups.get("fips_values", {}).items()}))
    selected = []
    for row in rows:
        if not row["PAYLOAD_CHANGED"] or row["ELEMENT_PATH"] not in {impact_path, sensitivity_path}:
            continue
        old, new = (json.loads(row[name], parse_float=Decimal) for name in ("OLD_JSON", "NEW_JSON"))
        if row["ELEMENT_PATH"] == impact_path or sensitivity in old and sensitivity not in new:
            selected.append((row["REVIEW_RECORD"], row["ELEMENT_PATH"], old, new))
    needed = {record for record, _, _, _ in selected}
    sources, source_errors = {}, {}
    for record in source_input["source_df"].select("SOURCE_RECORD_ID", "CURATED_JSON").to_local_iterator():
        record_id = record["SOURCE_RECORD_ID"]
        if record_id not in needed:
            continue
        if record_id in sources or record_id in source_errors:
            sources.pop(record_id, None)
            source_errors[record_id] = "DUPLICATE_SOURCE_RECORD"
            continue
        try:
            sources[record_id] = _metadata_parse(record, context)
        except (ValueError, TypeError, ArithmeticError):
            source_errors[record_id] = "SOURCE_PARSE_ERROR"
    transitions, checks, field_inputs, sensitivity_sources, payload_checks = (Counter() for _ in range(5))
    impact_nodes = sensitivity_nodes = 0
    for record_id, path, old, new in selected:
        source = sources.get(record_id)
        source_error = source_errors.get(record_id, "SOURCE_RECORD_ABSENT") if source is None else None
        if path == impact_path:
            impact_nodes += 1
            node_checks = []
            for objective, rules in sorted(by_objective.items()):
                before, candidate = old.get(objective), new.get(objective)
                transitions[(objective, _preview_controlled_value(before, allowed),
                             _preview_controlled_value(candidate, allowed), _preview_value_relation(before, candidate))] += 1
                values, errors, ambiguous = [[], []], [False, False], False
                for rule in rules:
                    raw = resolve_json_path(source, rule["SOURCE_FIELD_NAME"]) if source is not None else None
                    _, state = _preview_source_label(raw, context)
                    field_inputs[(rule["SOURCE_FIELD_NAME"], source_error or state)] += 1
                    ambiguous |= state not in {"SINGLE_LOOKUP", "DIRECT_TEXT", "EMPTY"} and _has_value(raw)
                    for index, execution in enumerate((context, lower_context)):
                        try:
                            value = _metadata_transform(rule, raw, execution)
                            if value is not SKIP_VALUE:
                                values[index].append(value)
                        except (ValueError, TypeError, ArithmeticError):
                            errors[index] = True
                outcomes = []
                for index in (0, 1):
                    distinct = {json.dumps(value, sort_keys=True, default=str) for value in values[index]}
                    if source_error or errors[index]:
                        outcome = source_error or "TRANSFORM_ERROR"
                    elif ambiguous:
                        outcome = "AMBIGUOUS_SOURCE"
                    elif not distinct:
                        outcome = "NO_POPULATED_RULE"
                    elif len(distinct) > 1:
                        outcome = "CONFLICTING_RULES"
                    else:
                        outcome = "MATCH" if _preview_value_relation(values[index][0], candidate) == "EXACT_MATCH" else "MISMATCH"
                    outcomes.append(outcome)
                if outcomes == ["MATCH", "MISMATCH"] and _preview_value_relation(values[0][0], values[1][0]) == "CASE_ONLY":
                    outcomes[1] = "CASE_NORMALIZATION_NEEDED"
                checks[(objective, *outcomes)] += 1
                node_checks.append(outcomes[0])
            payload_checks["MATCH" if node_checks and all(value == "MATCH" for value in node_checks) else
                           "MISMATCH" if "MISMATCH" in node_checks else "UNRESOLVED"] += 1
        else:
            sensitivity_nodes += 1
            raw = resolve_json_path(source, "SECURITY_CATEGORY") if source is not None else None
            if source is None or "SECURITY_CATEGORY" not in source:
                presence = source_error or "ABSENT"
            elif raw is None:
                presence = "NULL"
            else:
                presence = "EMPTY" if not _has_value(raw) or isinstance(raw, str) and not raw.strip() else "POPULATED"
            label, resolution = _preview_source_label(raw, context)
            relation = _preview_value_relation(label, old[sensitivity]) if resolution in {"SINGLE_LOOKUP", "DIRECT_TEXT"} else "UNRESOLVED"
            sensitivity_sources[(presence, type(raw).__name__.upper(), resolution, relation)] += 1
    def table(counter, names):
        return [dict(zip(names, key), NODES=count) for key, count in sorted(counter.items())]
    return {
        "STATUS": "READ_ONLY_VALUE_RECONCILIATION", "COMMIT_AUTHORIZED": False,
        "IMPACT_NODES": impact_nodes, "SENSITIVITY_REMOVALS": sensitivity_nodes,
        "COUNTS_MATCH_POSTED_REVIEW": (impact_nodes, sensitivity_nodes) == (36, 1958),
        "IMPACT_VALUE_TRANSITIONS": table(transitions, ("OBJECTIVE", "OLD", "NEW", "RELATION")),
        "IMPACT_SOURCE_CHECKS": table(checks, ("OBJECTIVE", "ACCEPTED_TRANSFORM", "LOWERCASE_LOOKUP_TRANSFORM")),
        "IMPACT_PAYLOAD_SOURCE_CHECKS": dict(sorted(payload_checks.items())),
        "IMPACT_SOURCE_FIELDS": table(field_inputs, ("FIELD", "RESOLUTION")),
        "SENSITIVITY_SOURCE": table(sensitivity_sources, ("PRESENCE", "SHAPE", "RESOLUTION", "SOURCE_VS_REMOVED_VALUE")),
        "NOTE": "Frozen source; accepted context and separate lowercase-lookup comparison. No sensitivity approval, fallback, graph rebuild or write readiness.",
    }


def run_ssp_preview_update_review(session, graphs, pipeline_report, source_inputs=None):
    if (not isinstance(pipeline_report, dict) or pipeline_report.get("mode") != "PREVIEW"
            or pipeline_report.get("status") != "PREVIEW_COMPLETE"
            or pipeline_report.get("writes_executed") is not False
            or pipeline_report.get("commit_attempted") is not False):
        raise PreviewReviewError("ACCEPTED_PREVIEW_REQUIRED")
    groups = [group for group in pipeline_report.get("groups", []) if group.get("model") == "SSP"]
    if len(groups) != 1:
        raise PreviewReviewError("ONE_ACCEPTED_SSP_ROUTE_REQUIRED")
    group, expected = groups[0], groups[0]["load"]
    if (expected.get("status") != "PREVIEW_PASSED_NO_TARGET_DML"
            or expected.get("release") != "oscal-lean-daily-v3.1"
            or expected.get("validation_passed") is not True
            or expected.get("persisted") is not False or expected.get("committed") is not False
            or expected.get("pre_write_validation_passed") is not True
            or expected.get("storage_verified") is not True
            or expected.get("writes_executed") is not False
            or expected.get("target_dml_attempted") is not False
            or (expected.get("nodes"), expected.get("edges"), expected.get("source_records")) != (70102, 67289, 2813)
            or expected.get("expected_changes") != {"D": {"INSERTS": 0, "UPDATES": 1994, "UNCHANGED": 68108},
                                                    "F": {"INSERTS": 0, "UPDATES": 0, "UNCHANGED": 67289}}):
        raise PreviewReviewError("PREVIEW_DIFFERS_FROM_ACCEPTED_1994_UPDATE_RUN")
    graph = graphs[(group["source"], "SSP")]
    config = graph["context"]["config"]
    if config.get("EXECUTE_WRITES") is not False or config.get("OSCAL_MODEL") != "SSP" or not config.get("RUN_ID"):
        raise PreviewReviewError("ACCEPTED_PREVIEW_CONFIGURATION_REQUIRED")
    storage = _load_storage(config)
    if storage is None:
        raise PreviewReviewError("VERIFIED_PREVIEW_STORAGE_REQUIRED")
    _load_no_transaction()
    # One action reads every candidate classification from one current target statement snapshot.
    rows = _preview_comparison_frame(session, graph["nodes"], storage).collect()
    report = _preview_summarize(rows, expected, config["RUN_ID"])
    if source_inputs is not None and report["STATUS"] == "READ_ONLY_REVIEW_COMPLETE":
        try:
            report["VALUE_RECONCILIATION"] = _preview_value_reconciliation(rows, graph["context"], source_inputs[group["source"]])
        except Exception as error:
            report["VALUE_RECONCILIATION"] = {"STATUS": "VALUE_RECONCILIATION_STOPPED", "ERROR": type(error).__name__}
    return report


if __name__ == "__main__":
    ssp_preview_update_review = None
    try:
        ssp_preview_update_review = run_ssp_preview_update_review(session, MODEL_GRAPHS, PIPELINE_REPORT, SOURCE_INPUTS)
        print(json.dumps(ssp_preview_update_review, indent=2, sort_keys=True))
    except Exception as error:
        code = str(error) if isinstance(error, PreviewReviewError) else type(error).__name__
        print(json.dumps({"STATUS": "READ_ONLY_REVIEW_STOPPED", "TARGET_DML_ATTEMPTED": False, "ERROR": code}))
        raise RuntimeError("READ_ONLY_REVIEW_STOPPED; keep the accepted session open") from None
