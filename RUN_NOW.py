# RUN NOW — Source One FINDINGS serialization check (corrected)
# Date: 2026-09-22
# READ ONLY. No mapping CSV, registry, DIM, FACT, or source DML.
#
# Correction to the prior helper:
# FINDINGS exists on many Archer levels/modules. The previous helper incorrectly
# treated ANY FINDINGS metadata row with FIELD_TYPE_ID=9 as Source One evidence.
# Source One Authorization Package is LEVEL_ID=353 / MODULE_ID=547, so only that
# metadata row is authoritative for this mapping decision.
#
# Current screenshot evidence already showed:
#   Source One FINDINGS = STRING on 2,813 / 2,813 rows
#   Source One metadata row = FIELD_TYPE_ID 23 at LEVEL 353 / MODULE 547
#
# This check determines whether those strings are just empty sentinels such as
# "[]"/"null", JSON-encoded related-record collections, numeric reference text,
# or some other serialization. Raw IDs/values are NOT printed.

import json
import re
from collections import Counter

SOURCE_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
FIELD = "FINDINGS"
SOURCE_LEVEL_ID = 353
SOURCE_MODULE_ID = 547

EMPTY_SENTINELS = {
    "", "[]", "{}", "null", "none", "nil", "n/a", "na"
}

def py(v):
    if hasattr(v, "as_dict"):
        return v.as_dict(recursive=True)
    if hasattr(v, "as_list"):
        return v.as_list()
    return v

def category(value):
    value = py(value)
    if value is None:
        return "SQL_NULL", True, 0

    text = str(value).strip()
    if text.lower() in EMPTY_SENTINELS:
        return "EMPTY_SENTINEL", True, len(text)

    # JSON text?
    try:
        parsed = json.loads(text)
        if parsed is None:
            return "JSON_NULL", True, len(text)
        if isinstance(parsed, list):
            return ("JSON_ARRAY_EMPTY" if len(parsed) == 0 else "JSON_ARRAY_NONEMPTY",
                    len(parsed) == 0, len(text))
        if isinstance(parsed, dict):
            return ("JSON_OBJECT_EMPTY" if len(parsed) == 0 else "JSON_OBJECT_NONEMPTY",
                    len(parsed) == 0, len(text))
        if isinstance(parsed, (int, float)):
            return "JSON_SCALAR_NUMBER", False, len(text)
        if isinstance(parsed, str):
            return "JSON_SCALAR_STRING", parsed.strip() == "", len(text)
    except Exception:
        pass

    # Common reference-like textual encodings. Values themselves are not printed.
    if re.fullmatch(r"[+-]?\d+", text):
        return "INTEGER_TEXT", False, len(text)
    if re.fullmatch(r"[+-]?\d+(\s*[,;|]\s*[+-]?\d+)+", text):
        return "DELIMITED_INTEGER_TEXT", False, len(text)
    if re.fullmatch(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}", text):
        return "UUID_TEXT", False, len(text)

    return "OTHER_TEXT", False, len(text)

rows = session.sql(f"""
SELECT CONTENT_ID, CURATED_JSON:{FIELD} AS FIELD_VALUE
FROM {SOURCE_TABLE}
""").collect()

cats = Counter()
lengths = Counter()
effective_nonempty = 0
for row in rows:
    cat, effectively_empty, length = category(row["FIELD_VALUE"])
    cats[cat] += 1
    lengths[length] += 1
    if not effectively_empty:
        effective_nonempty += 1

print("SOURCE_ONE_FINDINGS_SERIALIZATION_PROFILE")
print("SOURCE_RECORDS =", len(rows))
print("CATEGORY_COUNTS =", dict(sorted(cats.items())))
print("EFFECTIVE_NONEMPTY =", effective_nonempty)
print("DISTINCT_STRING_LENGTHS =", len(lengths))
if lengths:
    print("STRING_LENGTH_MIN_MAX =", min(lengths), max(lengths))
    if len(lengths) <= 12:
        print("STRING_LENGTH_COUNTS =", dict(sorted(lengths.items())))

# Authoritative Source One Archer metadata only.
meta = session.sql(f"""
SELECT
    FIELD_ID,
    SQL_FIELD_NAME,
    FIELD_TYPE_ID,
    LEVEL_ID,
    MODULE_ID,
    SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE UPPER(TRIM(SQL_FIELD_NAME)) = '{FIELD}'
  AND LEVEL_ID = {SOURCE_LEVEL_ID}
  AND MODULE_ID = {SOURCE_MODULE_ID}
ORDER BY FIELD_ID
""").collect()

print()
print("SOURCE_ONE_FINDINGS_METADATA")
for row in meta:
    print(row.as_dict())

# Existing finding branch.
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

source_meta_types = sorted({int(row["FIELD_TYPE_ID"]) for row in meta if row["FIELD_TYPE_ID"] is not None})

print()
print("FINDING_BRANCH_READY =", branch_ready)
print("SOURCE_ONE_FIELD_TYPE_IDS =", source_meta_types)
print("SOURCE_ONE_IS_RELATED_RECORD =", source_meta_types == [23])

if branch_ready and source_meta_types == [23] and effective_nonempty == 0:
    print("RESULT: SOURCE_ONE_FINDINGS_PATH_READY_CURRENTLY_EMPTY")
elif branch_ready and source_meta_types == [23] and effective_nonempty > 0:
    print("RESULT: SOURCE_ONE_FINDINGS_RELATED_RECORD_SERIALIZATION_NEEDS_MAPPING_CONTRACT")
else:
    print("RESULT: SOURCE_ONE_FINDINGS_NEEDS_REVIEW")
