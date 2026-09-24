# RUN NOW — Level-355 one-row control-id fallback check
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Current blocker:
# - 127,496 matched Level-355 control rows
# - CONTROL_NUMBER effective on 127,495 rows
# - exactly 1 row has JSON null CONTROL_NUMBER
#
# Check only whether another control-number field covers that one row.
# No IDs or source values are printed.

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"

def present(expr):
    return f"""
    CASE
      WHEN {expr} IS NULL THEN 0
      WHEN TYPEOF({expr}) = 'NULL_VALUE' THEN 0
      WHEN TYPEOF({expr}) = 'VARCHAR' AND NULLIF(TRIM({expr}::STRING), '') IS NULL THEN 0
      ELSE 1
    END
    """

cn = "GET(s.CURATED_JSON, 'CONTROL_NUMBER')"
feed = "GET(s.CURATED_JSON, 'FEED_CONTROL_NUMBER')"
only = "GET(s.CURATED_JSON, 'CONTROL_NUMBER_ONLY')"

row = session.sql(f"""
SELECT
    COUNT(*) AS MATCHED_ROWS,
    COUNT_IF({present(cn)} = 0) AS CONTROL_NUMBER_MISSING,
    COUNT_IF({present(cn)} = 0 AND {present(feed)} = 1) AS FEED_FALLBACK_COVERS,
    COUNT_IF({present(cn)} = 0 AND {present(only)} = 1) AS CONTROL_NUMBER_ONLY_COVERS,
    COUNT_IF({present(cn)} = 0 AND ({present(feed)} = 1 OR {present(only)} = 1))
        AS ANY_FALLBACK_COVERS,
    COUNT_IF({present(cn)} = 0 AND {present(feed)} = 0 AND {present(only)} = 0)
        AS MISSING_ALL_CONTROL_NUMBER_CANDIDATES
FROM {CONTROL_TABLE} s
JOIN {AUTH_TABLE} p
  ON TRIM(p.CONTENT_ID::STRING) = TRIM(s.CONTENT_ID::STRING)
""").collect()[0]

print("LEVEL355_CONTROL_ID_FALLBACK_CHECK")
for key in (
    "MATCHED_ROWS",
    "CONTROL_NUMBER_MISSING",
    "FEED_FALLBACK_COVERS",
    "CONTROL_NUMBER_ONLY_COVERS",
    "ANY_FALLBACK_COVERS",
    "MISSING_ALL_CONTROL_NUMBER_CANDIDATES",
):
    print(key, "=", int(row[key] or 0))

if int(row["CONTROL_NUMBER_MISSING"] or 0) == 0:
    print("RESULT: CONTROL_NUMBER_COMPLETE")
elif int(row["ANY_FALLBACK_COVERS"] or 0) == int(row["CONTROL_NUMBER_MISSING"] or 0):
    print("RESULT: CONTROL_NUMBER_FALLBACK_AVAILABLE")
else:
    print("RESULT: ONE_OR_MORE_CONTROLS_HAVE_NO_CONTROL_NUMBER")
