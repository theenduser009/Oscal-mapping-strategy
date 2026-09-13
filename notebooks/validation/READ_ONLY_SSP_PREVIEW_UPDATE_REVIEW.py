# Paste into one new Python cell in the existing accepted SSP PREVIEW session.
# Reuses MODEL_GRAPHS and PIPELINE_REPORT; no graph rerun or explicit table/view creation.
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


def run_ssp_preview_update_review(session, graphs, pipeline_report):
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
    return _preview_summarize(rows, expected, config["RUN_ID"])


if __name__ == "__main__":
    ssp_preview_update_review = None
    try:
        ssp_preview_update_review = run_ssp_preview_update_review(session, MODEL_GRAPHS, PIPELINE_REPORT)
        print(json.dumps(ssp_preview_update_review, indent=2, sort_keys=True))
    except Exception as error:
        code = str(error) if isinstance(error, PreviewReviewError) else type(error).__name__
        print(json.dumps({"STATUS": "READ_ONLY_REVIEW_STOPPED", "TARGET_DML_ATTEMPTED": False, "ERROR": code}))
        raise RuntimeError("READ_ONLY_REVIEW_STOPPED; keep the accepted session open") from None
