# RUN NOW — Source One Assessment Results FINDINGS final readiness check
# Date: 2026-09-22
# READ ONLY. No mapping CSV, registry, DIM, FACT, or source DML.
#
# Why this is next:
# - SSP Control Implementation core is source-blocked on the missing
#   ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW dataset.
# - FINDINGS already has the accepted OSCAL destination:
#     assessment-results.results[].findings[]
# - The current reviewed Source One snapshot was null, so this check confirms
#   Archer field metadata + live branch readiness before we change the CSV.
#
# If FINDINGS is a Cross-Reference field, we can reuse the existing generic
# reference-id pattern and finding branch; no new Python mapper logic is needed.

import json
from collections import Counter

SOURCE_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
FIELD = "FINDINGS"

def py(v):
    if hasattr(v, "as_dict"):
        return v.as_dict(recursive=True)
    if hasattr(v, "as_list"):
        return v.as_list()
    return v

def shape(v):
    v = py(v)
    if v is None:
        return "NULL"
    if isinstance(v, dict):
        return "OBJECT"
    if isinstance(v, list):
        return "ARRAY"
    if isinstance(v, bool):
        return "BOOL"
    if isinstance(v, (int, float)):
        return "NUMBER"
    if isinstance(v, str):
        return "STRING"
    return type(v).__name__.upper()

# 1) Current Source One value/shape coverage.
rows = session.sql(f"""
SELECT CONTENT_ID, CURATED_JSON:{FIELD} AS FIELD_VALUE
FROM {SOURCE_TABLE}
""").collect()

counts = Counter()
populated = 0
object_keys = Counter()
reference_levels = Counter()
array_element_shapes = Counter()

for row in rows:
    value = py(row["FIELD_VALUE"])
    counts[shape(value)] += 1
    if value not in (None, "", [], {}):
        populated += 1

    members = value if isinstance(value, list) else [value]
    for member in members:
        member = py(member)
        if isinstance(value, list):
            array_element_shapes[shape(member)] += 1
        if isinstance(member, dict):
            object_keys[",".join(sorted(str(k) for k in member.keys()))] += 1
            level_id = None
            for key, val in member.items():
                if str(key).replace("_","").lower() == "levelid":
                    level_id = py(val)
                    break
            if level_id is not None:
                reference_levels[str(level_id)] += 1

print("SOURCE_ONE_FINDINGS_VALUE_PROFILE")
print("SOURCE_RECORDS =", len(rows))
print("POPULATED =", populated)
print("SHAPES =", dict(sorted(counts.items())))
if array_element_shapes:
    print("ARRAY_ELEMENT_SHAPES =", dict(sorted(array_element_shapes.items())))
if object_keys:
    print("OBJECT_KEY_SIGNATURES =", dict(object_keys.most_common(5)))
if reference_levels:
    print("REFERENCE_LEVEL_IDS =", dict(sorted(reference_levels.items())))

# 2) Archer field metadata for FINDINGS.
meta = session.sql("""
SELECT
    FIELD_ID,
    SQL_FIELD_NAME,
    FIELD_TYPE_ID,
    LEVEL_ID,
    MODULE_ID,
    SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) = 'FINDINGS'
ORDER BY LEVEL_ID, MODULE_ID, FIELD_ID
""").collect()

print()
print("ARCHER_FINDINGS_METADATA")
for row in meta:
    print({
        "FIELD_ID": row["FIELD_ID"],
        "SQL_FIELD_NAME": row["SQL_FIELD_NAME"],
        "FIELD_TYPE_ID": row["FIELD_TYPE_ID"],
        "LEVEL_ID": row["LEVEL_ID"],
        "MODULE_ID": row["MODULE_ID"],
        "SELECT_ID": row["SELECT_ID"],
    })

# 3) Existing Assessment Results finding registry branch.
registry = session.sql("""
SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH,
    OPERATOR,
    UUID_POLICY
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(TRIM(OSCAL_MODEL_KEY)) = 'ASSESSMENT_RESULTS'
  AND TRIM(NODE_PATH) IN (
      'assessment-results.results[]',
      'assessment-results.results[].findings[]',
      'assessment-results.results[].findings[].props[]'
  )
ORDER BY PROCESS_ORDER, NODE_PATH
""").collect()

print()
print("ASSESSMENT_RESULTS_FINDING_REGISTRY")
for row in registry:
    print(row.as_dict())

active_paths = {
    str(row["NODE_PATH"]).strip()
    for row in registry
    if bool(row["IS_ACTIVE"])
}
required_paths = {
    "assessment-results.results[]",
    "assessment-results.results[].findings[]",
    "assessment-results.results[].findings[].props[]",
}
branch_ready = required_paths.issubset(active_paths)

# 4) Compact decision evidence.
cross_reference_meta = any(
    row["FIELD_TYPE_ID"] == 9
    for row in meta
)

print()
print("FINDING_BRANCH_READY =", branch_ready)
print("CROSS_REFERENCE_METADATA_FOUND =", cross_reference_meta)

if branch_ready and cross_reference_meta:
    print("RESULT: SOURCE_ONE_FINDINGS_REFERENCE_MAPPING_READY")
elif branch_ready and populated == 0:
    print("RESULT: SOURCE_ONE_FINDINGS_PATH_READY_BUT_REFERENCE_TYPE_UNCONFIRMED")
else:
    print("RESULT: SOURCE_ONE_FINDINGS_NEEDS_REVIEW")
