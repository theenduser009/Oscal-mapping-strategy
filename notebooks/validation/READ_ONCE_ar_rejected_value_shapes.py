# Run once AFTER the blocked v3 AR cell, in the same notebook session.
# Read-only: two fields, aggregate shapes only; no values, IDs or arbitrary keys.
import collections
import json
from decimal import Decimal


AR_SHAPE_FIELDS = ("RISK_ACCEPTANCE_RBDS", "RISK_ASSESSMENT_REPORT")
AR_SHAPE_RELEASE = "ar-observation-scores-v3-34-fields"
AR_SHAPE_KEYS = frozenset({
    "Id", "ContentId", "LevelId", "Value", "Name", "ValuesListIds",
    "ValuesListId", "ValuesList", "Values", "UserList", "Users", "Groups",
    "FileId", "FileName", "AttachmentId", "Attachments", "Url", "URL",
})
AR_SHAPE_REASONS = {
    "Score must be finite": "non_finite_value",
    "One scalar score is required per observation": "multiple_resolved_values",
    "Score must resolve to a scalar": "resolved_value_is_not_scalar",
    "One finite scalar score is required": "scalar_normalization_rejected",
}


def _ar_shape_type(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float, Decimal)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "other"


def _ar_value_shape(value, depth=0):
    shape = {"type": _ar_shape_type(value)}
    if isinstance(value, dict):
        shape["key_count"] = len(value)
        # Emit only fixed structural labels, never unknown source-supplied keys.
        shape["recognized_keys"] = {key: _ar_shape_type(value[key])
                                    for key in sorted(AR_SHAPE_KEYS) if key in value}
        shape["other_key_count"] = sum(key not in AR_SHAPE_KEYS for key in value)
    elif isinstance(value, list):
        shape["length"] = len(value)
        if depth < 1:
            members = collections.Counter(json.dumps(_ar_value_shape(item, depth + 1),
                                                     sort_keys=True) for item in value)
            shape["member_shapes"] = [{"shape": json.loads(key), "count": count}
                                      for key, count in sorted(members.items())]
    return shape


def inspect_ar_rejected_shapes(source_records, blocked_report, config, helpers, score_value):
    if config.get("EXECUTE_WRITES") is not False:
        raise ValueError("Keep writes disabled")
    if (blocked_report.get("MAPPING_RELEASE") != AR_SHAPE_RELEASE
            or blocked_report.get("STATUS") != "BLOCKED"
            or blocked_report.get("MAPPING_CONTRACT_ERRORS") != []
            or blocked_report.get("REGISTRY_CONTRACT_ERRORS") != []):
        raise ValueError("Use the existing blocked v3 AR report; do not rerun the mapper")
    if not callable(score_value) or not all(callable(helpers.get(name)) for name in
                                           ("resolve_json_path", "_parse_source_json")):
        raise ValueError("Keep the current AR notebook session open")
    expected = {field: blocked_report["FIELDS"][field]["invalid"] for field in AR_SHAPE_FIELDS}
    report = {"STATUS": "SHAPE_EVIDENCE_ONLY", "WRITES_EXECUTED": False,
              "SOURCE_RECORDS": 0, "SOURCE_PARSE_ERRORS": 0, "FIELDS": {}}
    counts = {field: collections.Counter() for field in AR_SHAPE_FIELDS}
    for record in source_records:
        report["SOURCE_RECORDS"] += 1
        try:
            raw = record["CURATED_JSON"]
            obj = (json.loads(raw, parse_float=Decimal) if isinstance(raw, str)
                   else helpers["_parse_source_json"](record))
            if not isinstance(obj, dict):
                raise ValueError("Source JSON must be an object")
        except (TypeError, ValueError, KeyError):
            report["SOURCE_PARSE_ERRORS"] += 1
            continue
        for field in AR_SHAPE_FIELDS:
            value = None
            stage = "source_path_resolution"
            try:
                value = helpers["resolve_json_path"](obj, field)
                stage = "scalar_conversion"
                score_value(value, helpers)
            except (TypeError, ValueError, ArithmeticError) as error:
                # Unknown error text may contain source data: never include it.
                reason = AR_SHAPE_REASONS.get(str(error), "conversion_or_lookup_rejected")
                shape = {"stage": stage, "reason": reason, "source_shape": _ar_value_shape(value)}
                counts[field][json.dumps(shape, sort_keys=True)] += 1
    for field in AR_SHAPE_FIELDS:
        report["FIELDS"][field] = {
            "EXPECTED_REJECTED": expected[field],
            "OBSERVED_REJECTED": sum(counts[field].values()),
            "SHAPES": [{**json.loads(shape), "count": count}
                       for shape, count in sorted(counts[field].items())],
        }
    report["MATCHES_BLOCKED_RUN"] = (
        report["SOURCE_RECORDS"] == blocked_report.get("SOURCE_RECORDS")
        and report["SOURCE_PARSE_ERRORS"] == 0
        and all(report["FIELDS"][f]["OBSERVED_REJECTED"] == expected[f] for f in AR_SHAPE_FIELDS)
    )
    return report


if __name__ == "__main__":
    AR_REJECTED_VALUE_SHAPES_REPORT = None
    required = ("source_df", "AR_SCORE_RUN_REPORT", "CONFIG", "AR_HELPERS", "_ar_score_value")
    if any(name not in globals() for name in required):
        raise RuntimeError("This cell needs the session containing the blocked v3 AR run")
    try:
        AR_REJECTED_VALUE_SHAPES_REPORT = inspect_ar_rejected_shapes(
            source_df.to_local_iterator(), AR_SCORE_RUN_REPORT, CONFIG,
            {name: globals().get(name) for name in AR_HELPERS}, _ar_score_value,
        )
    except Exception:
        raise RuntimeError("Shape inspection could not complete; no source values were printed") from None
    print(json.dumps(AR_REJECTED_VALUE_SHAPES_REPORT, indent=2))
