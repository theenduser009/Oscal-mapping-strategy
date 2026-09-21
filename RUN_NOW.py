# RUN NOW — Source One SSP System Characteristics deferred-field evidence check
# Date: 2026-09-21
# READ ONLY. Run after Cells 1-3 with SSP selected.
#
# Current remaining SSP System Characteristics deferred rows:
#   AUTHORIZATION_DECISION
#   FULL_CONTROL_ASSESSMENT_HELPER
#
# Purpose:
# 1) inspect live payload shapes and Archer metadata;
# 2) resolve distinct Archer select labels without printing record IDs;
# 3) compare AUTHORIZATION_DECISION with approved OPERATIONAL_STATUS semantics;
# 4) compare FULL_CONTROL_ASSESSMENT_HELPER with approved security-objective fields.
#
# No target DML.

import json
from collections import Counter

FIELDS = (
    "AUTHORIZATION_DECISION",
    "FULL_CONTROL_ASSESSMENT_HELPER",
    "OPERATIONAL_STATUS",
    "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY",
    "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE",
    "CNSS_CONFIDENTIALITY_RATING",
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

def select_ids(value):
    value = to_python(value)
    if not isinstance(value, dict):
        return []
    for key, item in value.items():
        if normalized_key(key) in {"valuelistid","valuelistids","valueslistid","valueslistids"}:
            item = to_python(item)
            if item is None:
                return []
            return item if isinstance(item, list) else [item]
    return []

source_df = SOURCE_INPUTS["source-one"]["source_df"]
lookup = SOURCE_INPUTS["source-one"]["lookups"].get("archer_values", {})

stats = {
    field: {
        "shapes": Counter(),
        "object_keys": Counter(),
        "select_cardinality": Counter(),
        "labels": Counter(),
        "unresolved_select_ids": 0,
        "scalar_values": Counter(),
    }
    for field in FIELDS
}

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
        s["shapes"][shape(value)] += 1

        if isinstance(value, dict):
            s["object_keys"][",".join(sorted(str(k) for k in value.keys()))] += 1
            ids = select_ids(value)
            if ids:
                s["select_cardinality"][len(ids)] += 1
                for item in ids:
                    key = str(item).strip()
                    label = lookup.get(key)
                    if label is None:
                        s["unresolved_select_ids"] += 1
                    else:
                        s["labels"][str(label).strip()] += 1
        elif isinstance(value, (str, int, float, bool)):
            text = str(value).strip()
            if text:
                s["scalar_values"][text] += 1

print("SOURCE_ONE_SSP_SYSTEM_CHARACTERISTICS_EVIDENCE")

for field in FIELDS:
    s = stats[field]
    print()
    print(field)
    print("  SHAPES:", dict(sorted(s["shapes"].items())))
    if s["object_keys"]:
        print("  OBJECT_KEY_SIGNATURES:", dict(s["object_keys"]))
    if s["select_cardinality"]:
        print("  SELECT_CARDINALITY:", dict(sorted(s["select_cardinality"].items())))
    if s["labels"]:
        print("  RESOLVED_LABEL_COUNTS:")
        for label, count in sorted(s["labels"].items()):
            print("   ", label, "=", count)
    if s["scalar_values"]:
        print("  SCALAR_VALUE_COUNTS:")
        for value, count in sorted(s["scalar_values"].items()):
            print("   ", value, "=", count)
    print("  UNRESOLVED_SELECT_IDS:", s["unresolved_select_ids"])

names = ", ".join("'" + f.replace("'", "''") + "'" for f in FIELDS)
meta = session.sql(f"""
SELECT
    UPPER(TRIM(SQL_FIELD_NAME)) AS SQL_FIELD_NAME,
    FIELD_TYPE_ID,
    LEVEL_ID,
    MODULE_ID,
    SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) IN ({names})
ORDER BY SQL_FIELD_NAME, LEVEL_ID, FIELD_ID
""").collect()

print()
print("ARCHER_META_FIELD_SUMMARY")
for row in meta:
    print(
        row["SQL_FIELD_NAME"],
        "| FIELD_TYPE_ID=", row["FIELD_TYPE_ID"],
        "| LEVEL_ID=", row["LEVEL_ID"],
        "| MODULE_ID=", row["MODULE_ID"],
        "| SELECT_ID=", row["SELECT_ID"],
    )

print()
print("RESULT: SSP_SYSTEM_CHARACTERISTICS_EVIDENCE_READY_FOR_MAPPING_REVIEW")
