# RUN NOW — Empirically identify the Level-355 reverse link to Authorization Package
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Relationship metadata is not exposed in the current Snowflake schema.
# Therefore test only the Level-355 fields whose metadata names explicitly
# indicate Authorization Package linkage, plus CONTROL_TO_INHERIT as a comparison.
#
# Goal:
# Find which Level-355 field contains {ContentId, LevelId} references whose
# ContentId values actually match current Authorization Package CONTENT_IDs.
#
# Aggregate counts only; no IDs or business values are printed.

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"

CANDIDATE_FIELDS = (
    "AUTHORIZATION_PACKAGE",
    "AUTHORIZATION_PACKAGE_SELECT_CONTROL",
    "AUTHORIZATION_PACKAGE_ARCHIVED_CONTROLS",
    "AUTHORIZATION_PACKAGES_ALLOWED_TO_INHERIT",
    "CONTROL_TO_INHERIT",
)

print("LEVEL355_AUTHORIZATION_PACKAGE_REVERSE_LINK_PROFILE")

# Current Authorization Package identities.
auth_count = session.sql(f"""
SELECT COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS N
FROM {AUTH_TABLE}
WHERE CONTENT_ID IS NOT NULL
""").collect()[0]["N"]

print("AUTHORIZATION_PACKAGE_DISTINCT_IDS =", int(auth_count or 0))

# Latest row per Level-355 top-level control record.
for field in CANDIDATE_FIELDS:
    print()
    print("FIELD =", field)

    shapes = session.sql(f"""
    WITH latest AS (
        SELECT *
        FROM {CONTROL_TABLE}
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRIM(CONTENT_ID::STRING)
            ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
        ) = 1
    )
    SELECT
        TYPEOF(GET(CURATED_JSON, '{field}')) AS VALUE_TYPE,
        COUNT(*) AS ROW_COUNT
    FROM latest
    GROUP BY TYPEOF(GET(CURATED_JSON, '{field}'))
    ORDER BY ROW_COUNT DESC, VALUE_TYPE
    """).collect()

    print("SHAPES =", {
        ("SQL_NULL" if r["VALUE_TYPE"] is None else str(r["VALUE_TYPE"])): int(r["ROW_COUNT"])
        for r in shapes
    })

    result = session.sql(f"""
    WITH auth_ids AS (
        SELECT DISTINCT TRIM(CONTENT_ID::STRING) AS AUTH_CONTENT_ID
        FROM {AUTH_TABLE}
        WHERE CONTENT_ID IS NOT NULL
    ),
    latest AS (
        SELECT *
        FROM {CONTROL_TABLE}
        QUALIFY ROW_NUMBER() OVER (
            PARTITION BY TRIM(CONTENT_ID::STRING)
            ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
        ) = 1
    ),
    array_refs AS (
        SELECT DISTINCT
            TRIM(c.CONTENT_ID::STRING) AS CONTROL_ROW_ID,
            TRIM(f.VALUE:ContentId::STRING) AS REF_ID,
            TRIM(f.VALUE:LevelId::STRING) AS REF_LEVEL_ID
        FROM latest c,
             LATERAL FLATTEN(INPUT => GET(c.CURATED_JSON, '{field}')) f
        WHERE f.VALUE:ContentId IS NOT NULL
    ),
    object_refs AS (
        SELECT DISTINCT
            TRIM(c.CONTENT_ID::STRING) AS CONTROL_ROW_ID,
            TRIM(GET(GET(c.CURATED_JSON, '{field}'), 'ContentId')::STRING) AS REF_ID,
            TRIM(GET(GET(c.CURATED_JSON, '{field}'), 'LevelId')::STRING) AS REF_LEVEL_ID
        FROM latest c
        WHERE TYPEOF(GET(c.CURATED_JSON, '{field}')) = 'OBJECT'
          AND GET(GET(c.CURATED_JSON, '{field}'), 'ContentId') IS NOT NULL
    ),
    refs AS (
        SELECT * FROM array_refs
        UNION
        SELECT * FROM object_refs
    )
    SELECT
        COUNT(DISTINCT CONTROL_ROW_ID) AS CONTROLS_WITH_REFERENCE,
        COUNT(DISTINCT REF_ID) AS DISTINCT_REFERENCED_IDS,
        COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, CONTROL_ROW_ID, NULL)) AS CONTROLS_LINKED_TO_AUTH_PACKAGE,
        COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, REF_ID, NULL)) AS MATCHED_AUTH_PACKAGE_IDS,
        COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, REF_LEVEL_ID, NULL)) AS MATCHED_LEVEL_ID_VARIANTS
    FROM refs r
    LEFT JOIN auth_ids a
      ON r.REF_ID = a.AUTH_CONTENT_ID
    """).collect()[0]

    print("CONTROLS_WITH_REFERENCE =", int(result["CONTROLS_WITH_REFERENCE"] or 0))
    print("DISTINCT_REFERENCED_IDS =", int(result["DISTINCT_REFERENCED_IDS"] or 0))
    print("CONTROLS_LINKED_TO_AUTH_PACKAGE =", int(result["CONTROLS_LINKED_TO_AUTH_PACKAGE"] or 0))
    print("MATCHED_AUTH_PACKAGE_IDS =", int(result["MATCHED_AUTH_PACKAGE_IDS"] or 0))
    print("MATCHED_LEVEL_ID_VARIANTS =", int(result["MATCHED_LEVEL_ID_VARIANTS"] or 0))

print()
summary = session.sql(f"""
WITH auth_ids AS (
    SELECT DISTINCT TRIM(CONTENT_ID::STRING) AS AUTH_CONTENT_ID
    FROM {AUTH_TABLE}
    WHERE CONTENT_ID IS NOT NULL
),
latest AS (
    SELECT *
    FROM {CONTROL_TABLE}
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY TRIM(CONTENT_ID::STRING)
        ORDER BY ETL_LOAD_TS DESC NULLS LAST, LOAD_TIMESTAMP DESC NULLS LAST
    ) = 1
),
candidates AS (
    SELECT COLUMN1 AS FIELD_NAME
    FROM VALUES
      ('AUTHORIZATION_PACKAGE'),
      ('AUTHORIZATION_PACKAGE_SELECT_CONTROL'),
      ('AUTHORIZATION_PACKAGE_ARCHIVED_CONTROLS'),
      ('AUTHORIZATION_PACKAGES_ALLOWED_TO_INHERIT'),
      ('CONTROL_TO_INHERIT')
),
exploded AS (
    SELECT
        c.FIELD_NAME,
        TRIM(l.CONTENT_ID::STRING) AS CONTROL_ROW_ID,
        TRIM(f.VALUE:ContentId::STRING) AS REF_ID
    FROM latest l
    CROSS JOIN candidates c,
         LATERAL FLATTEN(INPUT => GET(l.CURATED_JSON, c.FIELD_NAME)) f
    WHERE f.VALUE:ContentId IS NOT NULL
),
scored AS (
    SELECT
        e.FIELD_NAME,
        COUNT(DISTINCT e.CONTROL_ROW_ID) AS CONTROLS_LINKED,
        COUNT(DISTINCT e.REF_ID) AS DISTINCT_REFS,
        COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, e.CONTROL_ROW_ID, NULL)) AS AUTH_MATCHING_CONTROLS,
        COUNT(DISTINCT IFF(a.AUTH_CONTENT_ID IS NOT NULL, e.REF_ID, NULL)) AS AUTH_IDS_MATCHED
    FROM exploded e
    LEFT JOIN auth_ids a
      ON e.REF_ID = a.AUTH_CONTENT_ID
    GROUP BY e.FIELD_NAME
)
SELECT *
FROM scored
ORDER BY AUTH_MATCHING_CONTROLS DESC, AUTH_IDS_MATCHED DESC, FIELD_NAME
""").collect()

print("RANKED_REVERSE_LINK_FIELDS")
for row in summary:
    print(row.as_dict())

strong = [r for r in summary if int(r["AUTH_MATCHING_CONTROLS"] or 0) > 0]

if len(strong) == 1:
    print("RESULT: UNIQUE_LEVEL355_AUTHORIZATION_PACKAGE_REVERSE_LINK_FOUND")
elif len(strong) > 1:
    print("RESULT: MULTIPLE_LEVEL355_AUTHORIZATION_PACKAGE_LINKS_FOUND")
else:
    print("RESULT: NO_LEVEL355_AUTHORIZATION_PACKAGE_REVERSE_LINK_FOUND")
