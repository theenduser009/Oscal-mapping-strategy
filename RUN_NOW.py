# RUN NOW — Resolve Archer Level-355 control references to the current RAW table
# Date: 2026-09-21
# READ ONLY. No DIM/FACT/registry/mapping DML.
#
# Context:
# ALLOCATED_CONTROLS in Source One contains 252,165 observed {ContentId,LevelId}
# references and every observed LevelId is 355.
#
# Owner boundary:
# Historical structured/STG tables are discovery-only. This check searches only
# current Archer *_RAW tables for the Level-355 referenced ContentIds.
#
# Privacy:
# ContentIds are used internally for matching but are not printed.

from snowflake.snowpark import functions as F

SOURCE_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
TARGET_LEVEL_ID = "355"
SAMPLE_SIZE = 100

# 1) Resolve Level 355 business metadata.
print("ARCHER_LEVEL_355_METADATA")
level_rows = session.sql("""
SELECT LEVEL_ID, LEVEL_NAME, MODULE_ID, MODULE_NAME
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_LEVEL
WHERE LEVEL_ID = 355
ORDER BY LEVEL_ID
""").collect()

for row in level_rows:
    print(
        "LEVEL_ID =", row["LEVEL_ID"],
        "| LEVEL_NAME =", row["LEVEL_NAME"],
        "| MODULE_ID =", row["MODULE_ID"],
        "| MODULE_NAME =", row["MODULE_NAME"],
    )

# 2) Build a deterministic private sample of Level-355 referenced ContentIds.
sample_rows = session.sql(f"""
SELECT DISTINCT f.value:ContentId::STRING AS CONTENT_ID
FROM {SOURCE_TABLE} s,
     LATERAL FLATTEN(INPUT => s.CURATED_JSON:ALLOCATED_CONTROLS) f
WHERE f.value:LevelId::STRING = '{TARGET_LEVEL_ID}'
  AND f.value:ContentId IS NOT NULL
ORDER BY CONTENT_ID
LIMIT {SAMPLE_SIZE}
""").collect()

sample_ids = [str(row["CONTENT_ID"]).strip() for row in sample_rows if row["CONTENT_ID"] is not None]
if not sample_ids:
    raise ValueError("No Level-355 ALLOCATED_CONTROLS references were found")

print("PRIVATE_SAMPLE_SIZE =", len(sample_ids))

# 3) Find current Archer *_RAW tables that expose both CONTENT_ID and CURATED_JSON.
candidate_rows = session.sql("""
WITH cols AS (
    SELECT TABLE_NAME,
           COUNT_IF(UPPER(COLUMN_NAME)='CONTENT_ID') AS HAS_CONTENT_ID,
           COUNT_IF(UPPER(COLUMN_NAME)='CURATED_JSON') AS HAS_CURATED_JSON
    FROM RTX_RAW_DEV.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA='ES_ESC_GRC'
      AND STARTSWITH(UPPER(TABLE_NAME), 'ARCHER_CONTENT')
      AND ENDSWITH(UPPER(TABLE_NAME), '_RAW')
    GROUP BY TABLE_NAME
)
SELECT TABLE_NAME
FROM cols
WHERE HAS_CONTENT_ID > 0
  AND HAS_CURATED_JSON > 0
ORDER BY TABLE_NAME
""").collect()

candidate_tables = [row["TABLE_NAME"] for row in candidate_rows]
print("CURRENT_RAW_CANDIDATE_TABLES =", len(candidate_tables))

# 4) Match the private sample to each current RAW table. Print table/count only.
matches = []
for table_name in candidate_tables:
    full_name = "RTX_RAW_DEV.ES_ESC_GRC." + table_name
    frame = session.table(full_name)
    cols = {str(c).strip('"').upper(): c for c in frame.columns}
    if "CONTENT_ID" not in cols:
        continue
    count = (
        frame
        .filter(F.trim(F.col(cols["CONTENT_ID"]).cast("string")).isin(sample_ids))
        .select(F.trim(F.col(cols["CONTENT_ID"]).cast("string")).alias("CONTENT_ID"))
        .distinct()
        .count()
    )
    if count:
        matches.append((table_name, int(count)))

print("MATCHING_CURRENT_RAW_TABLES")
for table_name, count in sorted(matches, key=lambda x: (-x[1], x[0])):
    print(table_name, "| SAMPLE_MATCHES =", count)

full_matches = [name for name, count in matches if count == len(sample_ids)]
print("FULL_SAMPLE_MATCH_TABLES =", full_matches)

if len(full_matches) == 1:
    print("RESULT: LEVEL_355_CURRENT_RAW_BINDING_IDENTIFIED")
elif not matches:
    print("RESULT: LEVEL_355_CURRENT_RAW_BINDING_NOT_FOUND")
else:
    print("RESULT: LEVEL_355_CURRENT_RAW_BINDING_AMBIGUOUS")
