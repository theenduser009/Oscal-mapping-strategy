# RUN NOW — Level-355 second-batch field profile
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# First Level-355 batch is COMMIT/read-back verified.
# This profiles only the next implementation fields using JSON-null-aware counts.
# No implementation text, IDs, user names, or sensitive values are printed.

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"

FIELDS = (
    "IMPLEMENTATION_DETAILS",
    "OVERALL_IMPLEMENTATION_DETAILS",
    "IMPLEMENTATION_STATUS",
    "CONTROL_ORIGINATION",
    "RESPONSIBLE_ROLE",
    "CONTROL_PARAMETERS",
    "CONTROL_ENTITY",
    "CONTROL_SET",
    "INHERITED_IMPLEMENTATION_DETAILS",
    "PARTIAL_INHERITED_IMPLEMENTATION_DETAILS",
    "ASSESSMENT_STATUS",
    "OVERALL_ASSESSMENT_STATUS",
)

def populated_case(expr):
    return f"""
    CASE
      WHEN {expr} IS NULL THEN 0
      WHEN TYPEOF({expr}) = 'NULL_VALUE' THEN 0
      WHEN TYPEOF({expr}) = 'VARCHAR' AND NULLIF(TRIM({expr}::STRING), '') IS NULL THEN 0
      WHEN TYPEOF({expr}) = 'ARRAY' AND ARRAY_SIZE({expr}) = 0 THEN 0
      WHEN TYPEOF({expr}) = 'OBJECT' AND ARRAY_SIZE(OBJECT_KEYS({expr})) = 0 THEN 0
      ELSE 1
    END
    """

print("LEVEL355_SECOND_BATCH_FIELD_PROFILE")

# One joined working set: only current Level-355 rows whose package CONTENT_ID
# exists in Source One Authorization Package.
matched_cte = f"""
WITH matched AS (
    SELECT s.CURATED_JSON
    FROM {CONTROL_TABLE} s
    JOIN {AUTH_TABLE} p
      ON TRIM(p.CONTENT_ID::STRING) = TRIM(s.CONTENT_ID::STRING)
)
"""

total = session.sql(matched_cte + "SELECT COUNT(*) AS N FROM matched").collect()[0]["N"]
print("MATCHED_LEVEL355_ROWS =", int(total or 0))

# Archer metadata for the exact candidate fields at Level 355.
names_sql = ", ".join("'" + f.replace("'", "''") + "'" for f in FIELDS)
meta = session.sql(f"""
SELECT SQL_FIELD_NAME, FIELD_ID, FIELD_TYPE_ID, LEVEL_ID, MODULE_ID, SELECT_ID
FROM RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD
WHERE LEVEL_ID = 355
  AND UPPER(TRIM(SQL_FIELD_NAME)) IN ({names_sql})
ORDER BY SQL_FIELD_NAME, FIELD_ID
""").collect()

meta_by_field = {}
for row in meta:
    meta_by_field.setdefault(str(row["SQL_FIELD_NAME"]).upper(), []).append(row.as_dict())

for field in FIELDS:
    expr = f"GET(CURATED_JSON, '{field}')"
    stats = session.sql(matched_cte + f"""
    SELECT
        SUM({populated_case(expr)}) AS EFFECTIVE_POPULATED,
        COUNT_IF(TYPEOF({expr}) = 'NULL_VALUE') AS JSON_NULL_ROWS,
        COUNT_IF({expr} IS NULL) AS SQL_NULL_OR_ABSENT_ROWS,
        COUNT(DISTINCT IFF({populated_case(expr)} = 1, {expr}::STRING, NULL)) AS DISTINCT_POPULATED_VALUES,
        MIN(IFF({populated_case(expr)} = 1, LENGTH({expr}::STRING), NULL)) AS MIN_POPULATED_LENGTH,
        MAX(IFF({populated_case(expr)} = 1, LENGTH({expr}::STRING), NULL)) AS MAX_POPULATED_LENGTH
    FROM matched
    """).collect()[0]

    shapes = session.sql(matched_cte + f"""
    SELECT
        COALESCE(TYPEOF({expr}), 'SQL_NULL_OR_ABSENT') AS VALUE_TYPE,
        COUNT(*) AS N
    FROM matched
    GROUP BY COALESCE(TYPEOF({expr}), 'SQL_NULL_OR_ABSENT')
    ORDER BY N DESC, VALUE_TYPE
    """).collect()

    print()
    print("FIELD =", field)
    print("ARCHER_META =", meta_by_field.get(field, []))
    print("EFFECTIVE_POPULATED =", int(stats["EFFECTIVE_POPULATED"] or 0))
    print("JSON_NULL_ROWS =", int(stats["JSON_NULL_ROWS"] or 0))
    print("SQL_NULL_OR_ABSENT_ROWS =", int(stats["SQL_NULL_OR_ABSENT_ROWS"] or 0))
    print("DISTINCT_POPULATED_VALUES =", int(stats["DISTINCT_POPULATED_VALUES"] or 0))
    print("MIN_MAX_POPULATED_LENGTH =", stats["MIN_POPULATED_LENGTH"], stats["MAX_POPULATED_LENGTH"])
    print("SHAPES =", {str(r["VALUE_TYPE"]): int(r["N"]) for r in shapes})

# Resolve ValuesList labels only for candidate fields that Archer metadata says
# are picklists. Aggregate labels only; no select IDs are printed.
select_fields = [
    field for field, rows in meta_by_field.items()
    if any(int(r["FIELD_TYPE_ID"]) == 4 for r in rows if r["FIELD_TYPE_ID"] is not None)
]

for field in select_fields:
    labels = session.sql(matched_cte + f"""
    , ids AS (
        SELECT f.VALUE::STRING AS SELECT_VALUE_ID
        FROM matched m,
             LATERAL FLATTEN(
                 INPUT => GET(GET(m.CURATED_JSON, '{field}'), 'ValuesListIds')
             ) f
    )
    SELECT
        v.SELECT_VALUE_NAME AS LABEL,
        COUNT(*) AS N
    FROM ids i
    LEFT JOIN RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE v
      ON TRIM(v.SELECT_VALUE_ID::STRING) = TRIM(i.SELECT_VALUE_ID)
    GROUP BY v.SELECT_VALUE_NAME
    ORDER BY N DESC, LABEL
    """).collect()

    print()
    print("SELECT_LABEL_COUNTS", field, "=",
          {("<UNRESOLVED>" if r["LABEL"] is None else str(r["LABEL"])): int(r["N"]) for r in labels})

print()
print("RESULT: LEVEL355_SECOND_BATCH_PROFILE_READY")
