# Source One Assessment Results — targeted reference/select structure check
# Date: 2026-09-21
# READ ONLY. Run after Cells 1-3 in the same Snowflake notebook session.
#
# Purpose:
# Resolve the three populated-shape exceptions found by
# 2026-09-21_source_one_ar_populated_shape_check.py:
#   - RISK_ACCEPTANCE_RBDS
#   - RISK_ASSESSMENT_REPORT
#   - WORKFLOW_JOB_STATUS
#
# Privacy:
# Prints counts and structural/key signatures only. It does NOT print source
# values, ContentIds, LevelIds, select IDs, or source record IDs.

import json
from collections import Counter

FIELDS = (
    "RISK_ACCEPTANCE_RBDS",
    "RISK_ASSESSMENT_REPORT",
    "WORKFLOW_JOB_STATUS",
)


def to_python(value):
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if hasattr(value, "as_list"):
        return value.as_list()
    return value


def shape(value):
    value = to_python(value)
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, str):
        return "STRING"
    if isinstance(value, (int, float)):
        return "NUMBER"
    if isinstance(value, dict):
        return "OBJECT"
    if isinstance(value, list):
        return "ARRAY"
    return type(value).__name__.upper()


def normalized_key(key):
    return "".join(ch for ch in str(key).lower() if ch.isalnum())


def object_signature(obj):
    return ",".join(sorted(str(k) for k in obj.keys())) or "<EMPTY_OBJECT>"


def find_key(obj, wanted):
    wanted = normalized_key(wanted)
    for key, value in obj.items():
        if normalized_key(key) == wanted:
            return to_python(value)
    return None


source_df = SOURCE_INPUTS["source-one"]["source_df"]
archer_lookup = SOURCE_INPUTS["source-one"]["lookups"].get("archer_values", {})

stats = {
    field: {
        "top_shapes": Counter(),
        "array_lengths": Counter(),
        "element_shapes": Counter(),
        "object_keys": Counter(),
        "content_id_members": 0,
        "level_id_members": 0,
        "select_container_members": 0,
        "other_text_members": 0,
        "numeric_members": 0,
        "unique_numeric_tokens": set(),
        "lookup_matches": set(),
        "lookup_misses": set(),
        "select_cardinality": Counter(),
    }
    for field in FIELDS
}


def inspect_scalar_token(field, value):
    s = stats[field]
    value = to_python(value)
    if isinstance(value, bool) or value is None or isinstance(value, (dict, list)):
        return
    if isinstance(value, (int, float)) or (isinstance(value, str) and value.strip().isdigit()):
        token = str(value).strip()
        s["numeric_members"] += 1
        s["unique_numeric_tokens"].add(token)
        if token in archer_lookup:
            s["lookup_matches"].add(token)
        else:
            s["lookup_misses"].add(token)


def inspect_object(field, obj):
    s = stats[field]
    s["object_keys"][object_signature(obj)] += 1

    content_id = find_key(obj, "ContentId")
    if content_id is not None:
        s["content_id_members"] += 1
        inspect_scalar_token(field, content_id)

    level_id = find_key(obj, "LevelId")
    if level_id is not None:
        s["level_id_members"] += 1

    other_text = find_key(obj, "OtherText")
    if any(normalized_key(k) == "othertext" for k in obj):
        s["other_text_members"] += 1

    select_ids = None
    for candidate in ("ValuesListIds", "ValueListIds"):
        value = find_key(obj, candidate)
        if value is not None:
            select_ids = to_python(value)
            break

    if select_ids is not None:
        s["select_container_members"] += 1
        members = select_ids if isinstance(select_ids, list) else [select_ids]
        s["select_cardinality"][len(members)] += 1
        for member in members:
            inspect_scalar_token(field, member)


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
        s = stats[field]
        s["top_shapes"][shape(value)] += 1

        if isinstance(value, list):
            s["array_lengths"][len(value)] += 1
            for member in value:
                member = to_python(member)
                s["element_shapes"][shape(member)] += 1
                if isinstance(member, dict):
                    inspect_object(field, member)
                else:
                    inspect_scalar_token(field, member)
        elif isinstance(value, dict):
            inspect_object(field, value)
        else:
            inspect_scalar_token(field, value)


print("SOURCE_ONE_AR_TARGETED_REFERENCE_SELECT_CHECK")
for field in FIELDS:
    s = stats[field]
    print()
    print(field)
    print("  TOP_SHAPES:", dict(sorted(s["top_shapes"].items())))
    if s["array_lengths"]:
        print("  ARRAY_LENGTHS:", dict(sorted(s["array_lengths"].items())))
    if s["element_shapes"]:
        print("  ARRAY_ELEMENT_SHAPES:", dict(sorted(s["element_shapes"].items())))
    if s["object_keys"]:
        print("  OBJECT_KEY_SIGNATURES:")
        for signature, count in s["object_keys"].most_common():
            print("   ", count, "|", signature)
    print("  CONTENT_ID_OBJECTS:", s["content_id_members"])
    print("  LEVEL_ID_OBJECTS:", s["level_id_members"])
    print("  SELECT_CONTAINER_OBJECTS:", s["select_container_members"])
    print("  OTHER_TEXT_OBJECTS:", s["other_text_members"])
    if s["select_cardinality"]:
        print("  SELECT_CARDINALITY:", dict(sorted(s["select_cardinality"].items())))
    print("  UNIQUE_NUMERIC_TOKENS:", len(s["unique_numeric_tokens"]))
    print("  TOKENS_MATCHING_ARCHER_META_VALUE:", len(s["lookup_matches"]))
    print("  TOKENS_NOT_IN_ARCHER_META_VALUE:", len(s["lookup_misses"]))

print()
print("INTERPRETATION_HINTS")
print("- ContentId/LevelId objects indicate Archer cross-reference structure, not a direct scalar property.")
print("- OtherText/ValuesListIds objects indicate Archer select-value structure; use archer-select when cardinality is one.")
print("- Bare numeric arrays with few/no ARCHER_META_VALUE matches should be treated as reference IDs until their target object is identified.")
print("- Do not rerun Cells 4-7 until these three mappings are resolved.")
