# RUN NOW — Source One SSP Metadata deferred-field shape and Archer metadata check
# Date: 2026-09-21
# READ ONLY. No DIM/FACT/registry/mapping DML.
#
# Context:
# Source One Assessment Results has just been COMMITTED_AND_VERIFIED.
# Next Source One backlog area = SSP Metadata (5 deferred rows).
#
# Purpose:
# Compare the four deferred responsible-party fields with the already-approved
# responsible-party fields, and inspect the shape/metadata of
# ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER.
#
# Privacy:
# Prints only counts, field/type metadata, and structural key signatures.
# It does not print user names, IDs, emails, record IDs, or source values.

import json
from collections import Counter

DEFERRED_FIELDS = (
    "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER",
    "SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO",
    "INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE",
    "INFORMATION_SYSTEM_ADMINISTRATOR_ISA",
    "AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR",
)

APPROVED_ROLE_COMPARATORS = (
    "INFORMATION_OWNER_IO",
    "INFORMATION_SYSTEM_OWNER_ISO",
    "AUTHORIZING_OFFICIAL_AO",
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO",
    "PRIVACY_OFFICER_PO",
)

ALL_FIELDS = DEFERRED_FIELDS + APPROVED_ROLE_COMPARATORS


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


def signature(obj):
    return ",".join(sorted(str(k) for k in obj.keys())) or "<EMPTY_OBJECT>"


source_df = SOURCE_INPUTS["source-one"]["source_df"]

stats = {
    field: {
        "top_shapes": Counter(),
        "object_keys": Counter(),
        "array_lengths": Counter(),
        "array_element_shapes": Counter(),
        "userlist_lengths": Counter(),
        "user_object_keys": Counter(),
    }
    for field in ALL_FIELDS
}

for record in source_df.to_local_iterator():
    payload = to_python(record["CURATED_JSON"])
    if isinstance(payload, str):
        payload = json.loads(payload)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Source One CURATED_JSON must resolve to an object")

    for field in ALL_FIELDS:
        if field not in payload:
            continue
        value = to_python(payload[field])
        s = stats[field]
        s["top_shapes"][shape(value)] += 1

        if isinstance(value, dict):
            s["object_keys"][signature(value)] += 1
            user_list = None
            for key, item in value.items():
                if str(key).lower() == "userlist":
                    user_list = to_python(item)
                    break
            if isinstance(user_list, list):
                s["userlist_lengths"][len(user_list)] += 1
                for user in user_list:
                    user = to_python(user)
                    if isinstance(user, dict):
                        s["user_object_keys"][signature(user)] += 1

        elif isinstance(value, list):
            s["array_lengths"][len(value)] += 1
            for member in value:
                member = to_python(member)
                s["array_element_shapes"][shape(member)] += 1
                if isinstance(member, dict):
                    s["object_keys"][signature(member)] += 1


print("SOURCE_ONE_SSP_METADATA_SHAPE_CHECK")
for field in ALL_FIELDS:
    s = stats[field]
    print()
    print(field)
    print("  TOP_SHAPES:", dict(sorted(s["top_shapes"].items())))
    if s["array_lengths"]:
        print("  ARRAY_LENGTHS:", dict(sorted(s["array_lengths"].items())))
    if s["array_element_shapes"]:
        print("  ARRAY_ELEMENT_SHAPES:", dict(sorted(s["array_element_shapes"].items())))
    if s["object_keys"]:
        print("  OBJECT_KEY_SIGNATURES:")
        for key_sig, count in s["object_keys"].most_common():
            print("   ", count, "|", key_sig)
    if s["userlist_lengths"]:
        print("  USERLIST_LENGTHS:", dict(sorted(s["userlist_lengths"].items())))
    if s["user_object_keys"]:
        print("  USER_OBJECT_KEY_SIGNATURES:")
        for key_sig, count in s["user_object_keys"].most_common():
            print("   ", count, "|", key_sig)

names = ", ".join("'" + field.replace("'", "''") + "'" for field in ALL_FIELDS)

rows = session.sql(f"""
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
for row in rows:
    print(
        row["SQL_FIELD_NAME"],
        "| FIELD_TYPE_ID=", row["FIELD_TYPE_ID"],
        "| LEVEL_ID=", row["LEVEL_ID"],
        "| MODULE_ID=", row["MODULE_ID"],
        "| SELECT_ID=", row["SELECT_ID"],
    )

print()
print("RESULT: SSP_METADATA_EVIDENCE_READY_FOR_MAPPING_REVIEW")
