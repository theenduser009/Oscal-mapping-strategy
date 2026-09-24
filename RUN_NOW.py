# RUN NOW — Validate CONTROL_NAME prefix as one-row control-id fallback
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Proven blocker:
# - 127,496 matched Level-355 rows
# - 127,495 have CONTROL_NUMBER
# - exactly 1 has no CONTROL_NUMBER, FEED_CONTROL_NUMBER, or CONTROL_NUMBER_ONLY
#
# This check asks one precise question:
# Does the leading token of CONTROL_NAME reproduce CONTROL_NUMBER on all rows where
# CONTROL_NUMBER exists, and can it cover the one missing row?
#
# No source values or IDs are printed.

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"

cn = "GET(s.CURATED_JSON, 'CONTROL_NUMBER')"
name = "GET(s.CURATED_JSON, 'CONTROL_NAME')"

def present(expr):
    return f"""
    CASE
      WHEN {expr} IS NULL THEN 0
      WHEN TYPEOF({expr}) = 'NULL_VALUE' THEN 0
      WHEN TYPEOF({expr}) = 'VARCHAR' AND NULLIF(TRIM({expr}::STRING), '') IS NULL THEN 0
      ELSE 1
    END
    """

# Extract the first whitespace-delimited token from CONTROL_NAME.
name_prefix = f"SPLIT_PART(TRIM({name}::STRING), ' ', 1)"

row = session.sql(f"""
SELECT
    COUNT(*) AS MATCHED_ROWS,
    COUNT_IF({present(cn)} = 1) AS CONTROL_NUMBER_PRESENT,
    COUNT_IF({present(name)} = 1) AS CONTROL_NAME_PRESENT,

    COUNT_IF(
        {present(cn)} = 1
        AND {present(name)} = 1
        AND TRIM({cn}::STRING) = {name_prefix}
    ) AS EXISTING_ROWS_PREFIX_EQUALS_CONTROL_NUMBER,

    COUNT_IF(
        {present(cn)} = 1
        AND {present(name)} = 1
        AND TRIM({cn}::STRING) <> {name_prefix}
    ) AS EXISTING_ROWS_PREFIX_MISMATCH,

    COUNT_IF(
        {present(cn)} = 0
        AND {present(name)} = 1
        AND NULLIF({name_prefix}, '') IS NOT NULL
    ) AS MISSING_CONTROL_NUMBER_WITH_NAME_PREFIX,

    COUNT_IF(
        {present(cn)} = 0
        AND (
            {present(name)} = 0
            OR NULLIF({name_prefix}, '') IS NULL
        )
    ) AS MISSING_CONTROL_NUMBER_WITHOUT_NAME_PREFIX
FROM {CONTROL_TABLE} s
JOIN {AUTH_TABLE} p
  ON TRIM(p.CONTENT_ID::STRING) = TRIM(s.CONTENT_ID::STRING)
""").collect()[0]

print("LEVEL355_CONTROL_NAME_PREFIX_FALLBACK_CHECK")
for key in (
    "MATCHED_ROWS",
    "CONTROL_NUMBER_PRESENT",
    "CONTROL_NAME_PRESENT",
    "EXISTING_ROWS_PREFIX_EQUALS_CONTROL_NUMBER",
    "EXISTING_ROWS_PREFIX_MISMATCH",
    "MISSING_CONTROL_NUMBER_WITH_NAME_PREFIX",
    "MISSING_CONTROL_NUMBER_WITHOUT_NAME_PREFIX",
):
    print(key, "=", int(row[key] or 0))

if (
    int(row["EXISTING_ROWS_PREFIX_MISMATCH"] or 0) == 0
    and int(row["MISSING_CONTROL_NUMBER_WITH_NAME_PREFIX"] or 0) == 1
    and int(row["MISSING_CONTROL_NUMBER_WITHOUT_NAME_PREFIX"] or 0) == 0
):
    print("RESULT: CONTROL_NAME_PREFIX_IS_VALIDATED_ONE_ROW_FALLBACK")
else:
    print("RESULT: CONTROL_NAME_PREFIX_FALLBACK_NOT_PROVEN")
