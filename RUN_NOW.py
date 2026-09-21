# RUN NOW — Source One SSP Control Implementation bulk evidence inventory
# Date: 2026-09-21
# READ ONLY. No DIM/FACT/registry/mapping DML.
#
# This is the first bulk pass over the CURRENT deferred SSP Control Implementation
# backlog. It intentionally profiles all unique deferred source fields together so
# we can map by reusable semantic/shape classes instead of one field at a time.
#
# Historical Level-355 evidence remains relevant for cross-reference targets, but
# this check uses the current Source One RAW/CURATED_JSON plus live Archer metadata.
#
# Privacy:
# - no ContentIds, user IDs, attachment IDs, record IDs, or payload values printed
# - select labels are printed only as aggregate label counts
# - cross-reference LevelIds are printed only as aggregate counts

import json
from collections import Counter

FIELDS = (
    "COUNT_OF_CONTROLS",
    "ALLOCATE_BASELINE_CONTROLS",
    "CONTROL_SET_VERSION_NUMBER",
    "COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS",
    "COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS",
    "NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS",
    "ARCHIVE_CONTROLS",
    "CONTROL_OWNER_CO",
    "SECURITY_CONTROL_ASSESSOR_SCA",
    "ADD_ADDITIONAL_CONTROLS",
    "ALLOCATED_CONTROLS",
    "ARCHIVED_CONTROLS",
    "INHERITED_CONTROL_SELECTION",
    "INHERITABLE_CONTROLS",
    "LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING",
    "LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING",
    "LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING",
    "HELPER_ALLOCATED_CONTROLS",
    "PRECONTROL_ALLOCATION_PROGRESS_VIEW",
    "COUNT_OF_FULLY_IMPLEMENTED_CONTROLS",
    "CONTROL_SET_VERSION_NUMBER_HRC",
    "GS_LAB_CONTROL_ENTITY",
    "CONTROL_STANDARDS",
    "MASTER_CONTROLS",
    "ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS",
    "ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT",
    "EXPORT_CONTROL_ASSESSOR_ECA_TEXT",
    "SECURITY_CONTROL_ASSESSOR_SCA_TEXT",
    "EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE",
    "COUNT_OF_CONTROLS_WITH_OPEN_POAMS",
    "COUNT_OF_CONTROLS_MISSING_POAMRBD",
    "ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA",
    "ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE",
    "CONTROL_SET_TO_ASSESS",
    "CHANGE_CONTROL",
    "HELPER_OTS_CONTROLS",
    "COUNT_OF_INHERITED_CONTROLS",
    "COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED",
    "DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION",
    "CURRENT_CONTROL_RISK_THRESHOLD",
    "OF_SATISFIED_CONTROLS",
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

def key_sig(obj):
    return ",".join(sorted(str(k) for k in obj.keys())) or "<EMPTY_OBJECT>"

def norm(key):
    return "".join(ch for ch in str(key).lower() if ch.isalnum())

def get_key(obj, wanted):
    wanted = norm(wanted)
    for key, value in obj.items():
        if norm(key) == wanted:
            return to_python(value)
    return None

def select_ids(obj):
    if not isinstance(obj, dict):
        return []
    for key, value in obj.items():
        if norm(key) in {"valuelistid","valuelistids","valueslistid","valueslistids"}:
            value = to_python(value)
            if value is None:
                return []
            return value if isinstance(value, list) else [value]
    return []

source_df = SOURCE_INPUTS["source-one"]["source_df"]
lookup = SOURCE_INPUTS["source-one"]["lookups"].get("archer_values", {})

stats = {
    field: {
        "present": 0,
        "populated": 0,
        "shapes": Counter(),
        "object_keys": Counter(),
        "array_lengths": Counter(),
        "array_element_shapes": Counter(),
        "reference_level_ids": Counter(),
        "select_cardinality": Counter(),
        "select_labels": Counter(),
        "unresolved_select_ids": 0,
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
        s = stats[field]
        s["present"] += 1
        value = to_python(payload[field])
        s["shapes"][shape(value)] += 1
        if value not in (None, "", [], {}):
            s["populated"] += 1

        members = value if isinstance(value, list) else [value]
        if isinstance(value, list):
            s["array_lengths"][len(value)] += 1

        for member in members:
            member = to_python(member)
            if isinstance(value, list):
                s["array_element_shapes"][shape(member)] += 1

            if isinstance(member, dict):
                s["object_keys"][key_sig(member)] += 1

                level_id = get_key(member, "LevelId")
                if level_id is not None:
                    s["reference_level_ids"][str(level_id)] += 1

                ids = select_ids(member)
                if ids:
                    s["select_cardinality"][len(ids)] += 1
                    for item in ids:
                        key = str(item).strip()
                        label = lookup.get(key)
                        if label is None:
                            s["unresolved_select_ids"] += 1
                        else:
                            s["select_labels"][str(label).strip()] += 1

print("SOURCE_ONE_SSP_CONTROL_IMPLEMENTATION_BULK_EVIDENCE")
print("DEFERRED_ROW_COUNT =", 42)
print("UNIQUE_FIELD_COUNT =", 41)
print("DUPLICATE_FIELD_NAMES =", ["HELPER_ALLOCATED_CONTROLS"])

# Live Archer metadata for the exact deferred names.
names = ", ".join("'" + field.replace("'", "''") + "'" for field in FIELDS)
meta_rows = session.sql(f"""
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

meta_by_field = {}
for row in meta_rows:
    meta_by_field.setdefault(row["SQL_FIELD_NAME"], []).append({
        "FIELD_TYPE_ID": row["FIELD_TYPE_ID"],
        "LEVEL_ID": row["LEVEL_ID"],
        "MODULE_ID": row["MODULE_ID"],
        "SELECT_ID": row["SELECT_ID"],
    })

for field in FIELDS:
    s = stats[field]
    print()
    print(field)
    print("  PRESENT =", s["present"], "| POPULATED =", s["populated"])
    print("  SHAPES =", dict(sorted(s["shapes"].items())))
    if s["array_lengths"]:
        # Keep output compact: print min/max plus exact distribution only when small.
        lengths = s["array_lengths"]
        print("  ARRAY_LENGTH_MIN_MAX =", min(lengths), max(lengths))
        if len(lengths) <= 10:
            print("  ARRAY_LENGTHS =", dict(sorted(lengths.items())))
    if s["array_element_shapes"]:
        print("  ARRAY_ELEMENT_SHAPES =", dict(sorted(s["array_element_shapes"].items())))
    if s["object_keys"]:
        print("  OBJECT_KEY_SIGNATURES =")
        for signature, count in s["object_keys"].most_common(3):
            print("   ", count, "|", signature)
    if s["reference_level_ids"]:
        print("  REFERENCE_LEVEL_IDS =", dict(sorted(s["reference_level_ids"].items())))
    if s["select_cardinality"]:
        print("  SELECT_CARDINALITY =", dict(sorted(s["select_cardinality"].items())))
    if s["select_labels"]:
        if len(s["select_labels"]) <= 12:
            print("  SELECT_LABEL_COUNTS =", dict(sorted(s["select_labels"].items())))
        else:
            print("  DISTINCT_SELECT_LABELS =", len(s["select_labels"]))
    if s["unresolved_select_ids"]:
        print("  UNRESOLVED_SELECT_IDS =", s["unresolved_select_ids"])
    print("  ARCHER_META =", meta_by_field.get(field, []))

print()
print("RESULT: SSP_CONTROL_IMPLEMENTATION_BULK_EVIDENCE_READY_FOR_CLASSIFICATION")
