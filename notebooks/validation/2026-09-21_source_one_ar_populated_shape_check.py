# Source One Assessment Results — populated value shape compatibility check
# Date: 2026-09-21
# READ ONLY. Run after Cells 1-3 in the same Snowflake notebook session.
#
# Purpose:
# Verify that the transforms approved on 2026-09-21 match the ACTUAL populated
# Source One payload shapes before rerunning Cells 4-7.
#
# Privacy:
# Prints counts and structural signatures only. It does not print source values,
# source record IDs, ContentIds, or lookup IDs.

import datetime
import json
import math
from collections import Counter
from decimal import Decimal

FIELDS = (
    "AVG_SECURITY_COMPLIANCE_REPORTING_SCORE",
    "AVG_SECURITY_COMPLIANCE_SCORE",
    "TOTAL_PACKAGE_INHERENT_RISK",
    "RISK_ACCEPTANCE_RBDS",
    "RISK_ASSESSMENT_REPORT",
    "WORKFLOW_CURRENT_NODE",
    "WORKFLOW_PROCESS_VERSION",
    "WORKFLOW_JOB_STATUS",
    "WORKFLOW_STATUS",
    "DUE_DATE",
    "WORKFLOW_CURRENT_NODE_HRTN",
    "WORKFLOW_STATUS_CHANGED",
)

context = next(
    (
        c for c in MAPPING_CONTEXTS
        if c["source_key"] == "source-one"
        and c["config"]["OSCAL_MODEL"] == "ASSESSMENT_RESULTS"
    ),
    None,
)
if context is None:
    raise ValueError("Source One Assessment Results context is not loaded; rerun Cells 1-3.")

compiled = {
    row["SOURCE_FIELD_NAME"]: row
    for row in context["mapping_rows"]
    if row["SOURCE_FIELD_NAME"] in FIELDS
}
missing = [field for field in FIELDS if field not in compiled]
if missing:
    raise ValueError("Missing compiled fields: " + ", ".join(missing))


def to_python(value):
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if hasattr(value, "as_list"):
        return value.as_list()
    return value


def is_scalar(value):
    return value is None or isinstance(value, (str, int, float, bool, Decimal))


def shape(value):
    value = to_python(value)
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, (int, float, Decimal)):
        return "NUMBER"
    if isinstance(value, dict):
        return "OBJECT"
    if isinstance(value, list):
        return "ARRAY"
    return type(value).__name__.upper()


def key_signature(value):
    value = to_python(value)
    if not isinstance(value, dict):
        return None
    return ",".join(sorted(str(k) for k in value.keys())) or "<EMPTY_OBJECT>"


def list_signature(value):
    value = to_python(value)
    if not isinstance(value, list):
        return None
    element_shapes = Counter(shape(v) for v in value)
    body = ",".join(f"{k}:{element_shapes[k]}" for k in sorted(element_shapes))
    return f"LEN={len(value)}|{body or '<EMPTY_ARRAY>'}"


def valid_date(value):
    value = to_python(value)
    if isinstance(value, (datetime.datetime, datetime.date)):
        return True
    if not isinstance(value, str):
        return False
    text = value.strip()
    if not text:
        return False
    try:
        if len(text) == 10:
            datetime.date.fromisoformat(text)
            return True
        candidate = text[:-1] + "+00:00" if text[-1:] in {"Z", "z"} else text
        datetime.datetime.fromisoformat(candidate.replace(" ", "T", 1))
        return True
    except ValueError:
        return False


def select_cardinality(value):
    value = to_python(value)
    if not isinstance(value, dict):
        return None
    for key in ("ValuesListIds", "ValueListIds", "valuesListIds", "valueListIds"):
        if key in value:
            ids = to_python(value[key])
            if isinstance(ids, list):
                return len(ids)
            return 0 if ids is None else 1
    return None


summary = {
    field: {
        "shapes": Counter(),
        "object_keys": Counter(),
        "array_shapes": Counter(),
        "compatible": 0,
        "incompatible": 0,
        "select_cardinality": Counter(),
    }
    for field in FIELDS
}

source_df = SOURCE_INPUTS["source-one"]["source_df"]

for record in source_df.to_local_iterator():
    payload = to_python(record["CURATED_JSON"])
    if isinstance(payload, str):
        payload = json.loads(payload)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Source One CURATED_JSON must resolve to an object")

    for field in FIELDS:
        if field not in payload:
            continue

        value = to_python(payload[field])
        s = shape(value)
        summary[field]["shapes"][s] += 1

        if s == "OBJECT":
            summary[field]["object_keys"][key_signature(value)] += 1
        elif s == "ARRAY":
            summary[field]["array_shapes"][list_signature(value)] += 1

        transform = compiled[field]["TRANSFORM_ID"]
        ok = True

        if value is None:
            ok = True
        elif transform == "scalar-score":
            members = value if isinstance(value, list) else [value]
            ok = (
                len(members) == 1
                and is_scalar(to_python(members[0]))
                and not isinstance(to_python(members[0]), (dict, list))
            )
        elif transform == "direct":
            # results[].props[] uses SOURCE_FIELD_NAME identity, so exactly one
            # scalar property value is allowed per source field.
            members = value if isinstance(value, list) else [value]
            ok = (
                len(members) == 1
                and is_scalar(to_python(members[0]))
                and not isinstance(to_python(members[0]), (dict, list))
            )
        elif transform == "date":
            ok = valid_date(value)
        elif transform == "archer-select":
            cardinality = select_cardinality(value)
            if cardinality is not None:
                summary[field]["select_cardinality"][str(cardinality)] += 1
                ok = cardinality == 1
            else:
                # Scalar labels/IDs can also be handled by the existing resolver.
                ok = is_scalar(value) and not isinstance(value, (dict, list))

        summary[field]["compatible" if ok else "incompatible"] += 1

print("SOURCE_ONE_AR_SHAPE_COMPATIBILITY")
for field in FIELDS:
    row = compiled[field]
    s = summary[field]
    print()
    print(field)
    print("  TRANSFORM:", row["TRANSFORM_ID"])
    print("  TARGET:", row["CANONICAL_ELEMENT_PATH"])
    print("  SHAPES:", dict(sorted(s["shapes"].items())))
    print("  COMPATIBLE:", s["compatible"])
    print("  INCOMPATIBLE:", s["incompatible"])

    if s["object_keys"]:
        print("  OBJECT_KEY_SIGNATURES:")
        for signature, count in s["object_keys"].most_common():
            print("   ", count, "|", signature)

    if s["array_shapes"]:
        print("  ARRAY_SIGNATURES:")
        for signature, count in s["array_shapes"].most_common():
            print("   ", count, "|", signature)

    if s["select_cardinality"]:
        print("  SELECT_VALUE_COUNTS:", dict(sorted(s["select_cardinality"].items())))

problems = [
    field for field in FIELDS
    if summary[field]["incompatible"] > 0
]

print()
print("FIELDS_WITH_INCOMPATIBLE_POPULATED_SHAPES:", len(problems))
for field in problems:
    print(" -", field, ":", summary[field]["incompatible"])

if problems:
    print("RESULT: REVIEW_TRANSFORMS_BEFORE_CELLS_4_TO_7")
else:
    print("RESULT: SHAPES_COMPATIBLE_WITH_APPROVED_TRANSFORMS")
