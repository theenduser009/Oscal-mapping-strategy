# %% Read-only diagnostic: why SSP PREVIEW hit OBSOLETE_TARGET_ROWS_BLOCKED
# Date: 2026-09-29
# Run in the SAME Snowflake notebook session immediately after the failed Cell 7 PREVIEW.
# No DML / DDL / DROP. This intentionally inspects the temporary stage tables left by
# the preparation failure so we can identify exactly which target rows are obsolete.

TARGET_DIM = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT"
TARGET_FACT = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY"
SCHEMA_NAME = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED"
DIM_PK = "PK_OSCAL_SSP_ELEMENT_HASH"
FACT_PK = "PK_FACT_OSCAL_DEPENDENCY_HASH"
SOURCE_SYSTEM = "ARCHER"
SOURCE_TABLE = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"

def _norm_row(row):
    return {str(k).upper(): v for k, v in row.as_dict().items()}

show_rows = [_norm_row(r) for r in session.sql(
    f"SHOW TABLES LIKE 'TMP_OSCAL_%' IN SCHEMA {SCHEMA_NAME}"
).collect()]

groups = {}
suffixes = ("_BD", "_BF", "_N", "_E", "_D", "_F")
for row in show_rows:
    name = str(row.get("NAME") or "")
    suffix = next((s for s in suffixes if name.endswith(s)), None)
    if suffix is None:
        continue
    prefix = name[:-len(suffix)]
    item = groups.setdefault(prefix, {"tables": {}, "created_on": row.get("CREATED_ON")})
    item["tables"][suffix[1:]] = f"{SCHEMA_NAME}.{name}"
    created = row.get("CREATED_ON")
    if created is not None and (item["created_on"] is None or created > item["created_on"]):
        item["created_on"] = created

complete = [
    (prefix, info) for prefix, info in groups.items()
    if {"N", "E", "D", "F", "BD", "BF"}.issubset(info["tables"])
]
if not complete:
    raise ValueError(
        "No complete TMP_OSCAL_* stage set is visible in this notebook session. "
        "Do not rerun the mapper yet; report this message."
    )

prefix, latest = max(
    complete,
    key=lambda x: (x[1]["created_on"] is not None, x[1]["created_on"])
)
D = latest["tables"]["D"]
F = latest["tables"]["F"]

print("Using failed PREVIEW temp stage:", prefix)
print("DIM stage:", D)
print("FACT stage:", F)

source_filter = (
    f"t.SOURCE_SYSTEM_NAME='{SOURCE_SYSTEM}' "
    f"AND t.SOURCE_TABLE_NAME='{SOURCE_TABLE}'"
)

dim_scope = f"""
SELECT t.*
FROM {TARGET_DIM} t
LEFT JOIN {D} s
  ON s.{DIM_PK}=t.{DIM_PK}
LEFT JOIN (SELECT DISTINCT SOURCE_RECORD_ID FROM {D}) i
  ON i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
 AND {source_filter}
WHERE s.{DIM_PK} IS NOT NULL
   OR i.SOURCE_RECORD_ID IS NOT NULL
"""

keys = f"""
SELECT {DIM_PK} FROM ({dim_scope})
UNION
SELECT {DIM_PK} FROM {D}
"""

fact_scope = f"""
SELECT t.*
FROM {TARGET_FACT} t
LEFT JOIN {F} s
  ON s.{FACT_PK}=t.{FACT_PK}
LEFT JOIN ({keys}) p
  ON p.{DIM_PK}=t.FK_SOURCE_ELEMENT_HASH
LEFT JOIN ({keys}) c
  ON c.{DIM_PK}=t.FK_TARGET_ELEMENT_HASH
WHERE s.{FACT_PK} IS NOT NULL
   OR p.{DIM_PK} IS NOT NULL
   OR c.{DIM_PK} IS NOT NULL
"""

obsolete_dim = f"""
SELECT t.*
FROM ({dim_scope}) t
WHERE NOT EXISTS (
    SELECT 1 FROM {D} s
    WHERE s.{DIM_PK}=t.{DIM_PK}
)
"""

obsolete_fact = f"""
SELECT t.*
FROM ({fact_scope}) t
WHERE NOT EXISTS (
    SELECT 1 FROM {F} s
    WHERE s.{FACT_PK}=t.{FACT_PK}
)
"""

summary = session.sql(f"""
SELECT
    (SELECT COUNT(*) FROM ({obsolete_dim})) AS OBSOLETE_DIM_ROWS,
    (SELECT COUNT(*) FROM ({obsolete_fact})) AS OBSOLETE_FACT_ROWS,
    (SELECT COUNT(DISTINCT SOURCE_RECORD_ID) FROM ({obsolete_dim})) AS AFFECTED_SOURCE_RECORDS,
    (SELECT COUNT(*) FROM {D}) AS CANDIDATE_DIM_ROWS,
    (SELECT COUNT(*) FROM {F}) AS CANDIDATE_FACT_ROWS
""").collect()
print("OBSOLETE SUMMARY")
for row in summary:
    print(row.as_dict())

print("\nOBSOLETE DIM BY ELEMENT TYPE")
for row in session.sql(f"""
SELECT
    ELEMENT_TYPE,
    COUNT(*) AS OBSOLETE_ROWS,
    COUNT(DISTINCT SOURCE_RECORD_ID) AS SOURCE_RECORDS
FROM ({obsolete_dim})
GROUP BY ELEMENT_TYPE
ORDER BY OBSOLETE_ROWS DESC, ELEMENT_TYPE
""").collect():
    print(row.as_dict())

print("\nOBSOLETE DIM CLASSIFICATION")
for row in session.sql(f"""
WITH old_rows AS (
    SELECT * FROM ({obsolete_dim})
),
classified AS (
    SELECT
        o.SOURCE_RECORD_ID,
        o.ELEMENT_TYPE,
        COUNT(*) AS OBSOLETE_ROWS,
        COUNT_IF(n.{DIM_PK} IS NOT NULL) AS CANDIDATE_SAME_RECORD_AND_TYPE
    FROM old_rows o
    LEFT JOIN {D} n
      ON n.SOURCE_RECORD_ID=o.SOURCE_RECORD_ID
     AND n.ELEMENT_TYPE=o.ELEMENT_TYPE
    GROUP BY o.SOURCE_RECORD_ID, o.ELEMENT_TYPE
)
SELECT
    ELEMENT_TYPE,
    IFF(MAX(CANDIDATE_SAME_RECORD_AND_TYPE) > 0,
        'CANDIDATE_HAS_SAME_RECORD_AND_TYPE_DIFFERENT_KEY',
        'NO_CANDIDATE_SAME_RECORD_AND_TYPE') AS CLASSIFICATION,
    SUM(OBSOLETE_ROWS) AS OBSOLETE_ROWS,
    COUNT(*) AS SOURCE_RECORD_TYPE_GROUPS
FROM classified
GROUP BY ELEMENT_TYPE, CLASSIFICATION
ORDER BY OBSOLETE_ROWS DESC, ELEMENT_TYPE
""").collect():
    print(row.as_dict())

print("\nTOP AFFECTED SOURCE RECORDS (IDs only; no payload values)")
for row in session.sql(f"""
SELECT
    SOURCE_RECORD_ID,
    COUNT(*) AS OBSOLETE_DIM_ROWS,
    LISTAGG(DISTINCT ELEMENT_TYPE, ', ')
      WITHIN GROUP (ORDER BY ELEMENT_TYPE) AS ELEMENT_TYPES
FROM ({obsolete_dim})
GROUP BY SOURCE_RECORD_ID
ORDER BY OBSOLETE_DIM_ROWS DESC, SOURCE_RECORD_ID
LIMIT 25
""").collect():
    print(row.as_dict())

print("\nOBSOLETE FACT BY DEPENDENCY TYPE")
for row in session.sql(f"""
SELECT
    DEPENDENCY_TYPE,
    COUNT(*) AS OBSOLETE_ROWS
FROM ({obsolete_fact})
GROUP BY DEPENDENCY_TYPE
ORDER BY OBSOLETE_ROWS DESC, DEPENDENCY_TYPE
""").collect():
    print(row.as_dict())

print("\nREAD_ONLY_DIAGNOSTIC_COMPLETE")
