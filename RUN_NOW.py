# RUN NOW — Level-355 control-id failure check
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Current PREVIEW failed before commit after joined VARIANT decoding was fixed.
# This check is intentionally narrow:
# 1) prove whether CONTROL_NUMBER has any true null/blank rows;
# 2) see whether FEED_CONTROL_NUMBER can cover those rows;
# 3) print the underlying graph ValueError.
#
# No IDs or business text are printed.

import copy

AUTH_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
CONTROL_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW"
ROUTE = ("source-one", "SSP")

def effective_value_sql(expr):
    return f"""
    CASE
      WHEN {expr} IS NULL THEN 0
      WHEN TYPEOF({expr}) = 'NULL_VALUE' THEN 0
      WHEN TYPEOF({expr}) = 'VARCHAR' AND NULLIF(TRIM({expr}::STRING), '') IS NULL THEN 0
      ELSE 1
    END
    """

matched = f"""
WITH matched AS (
    SELECT s.CURATED_JSON
    FROM {CONTROL_TABLE} s
    JOIN {AUTH_TABLE} p
      ON TRIM(p.CONTENT_ID::STRING) = TRIM(s.CONTENT_ID::STRING)
)
"""

cn = "GET(CURATED_JSON, 'CONTROL_NUMBER')"
feed = "GET(CURATED_JSON, 'FEED_CONTROL_NUMBER')"
aid = "GET(CURATED_JSON, 'ALLOCATED_CONTROL_ID')"

stats = session.sql(matched + f"""
SELECT
    COUNT(*) AS MATCHED_ROWS,
    SUM({effective_value_sql(cn)}) AS CONTROL_NUMBER_EFFECTIVE,
    COUNT(*) - SUM({effective_value_sql(cn)}) AS CONTROL_NUMBER_MISSING,
    SUM({effective_value_sql(feed)}) AS FEED_CONTROL_NUMBER_EFFECTIVE,
    COUNT_IF({effective_value_sql(cn)} = 0 AND {effective_value_sql(feed)} = 1)
        AS MISSING_CONTROL_NUMBER_WITH_FEED_FALLBACK,
    COUNT_IF({effective_value_sql(cn)} = 0 AND {effective_value_sql(feed)} = 0)
        AS MISSING_BOTH_CONTROL_NUMBERS,
    SUM({effective_value_sql(aid)}) AS ALLOCATED_CONTROL_ID_EFFECTIVE
FROM matched
""").collect()[0]

print("LEVEL355_CONTROL_ID_REQUIRED_FIELD_CHECK")
print(stats.as_dict())

shape_rows = session.sql(matched + f"""
SELECT
    COALESCE(TYPEOF({cn}), 'SQL_NULL_OR_ABSENT') AS CONTROL_NUMBER_TYPE,
    COUNT(*) AS N
FROM matched
GROUP BY COALESCE(TYPEOF({cn}), 'SQL_NULL_OR_ABSENT')
ORDER BY N DESC, CONTROL_NUMBER_TYPE
""").collect()
print("CONTROL_NUMBER_SHAPES =", {str(r["CONTROL_NUMBER_TYPE"]): int(r["N"]) for r in shape_rows})

# Surface the exact mapper failure too.
contexts = [
    c for c in MAPPING_CONTEXTS
    if (c["source_key"], c["config"]["OSCAL_MODEL"]) == ROUTE
]
print("MATCHING_CONTEXTS =", len(contexts))

if len(contexts) == 1:
    context = copy.deepcopy(contexts[0])
    source = SOURCE_INPUTS[ROUTE[0]]
    context["lookups"] = source.get("lookups", {})

    try:
        nodes, edges = build_oscal_graph(
            source["source_df"], None, None,
            context["config"]["OSCAL_MODEL"],
            context["config"]["SOURCE_SYSTEM_NAME"],
            context["config"]["SOURCE_TABLE_NAME"],
            context=context,
        )
        print("GRAPH_BUILD = PASS")
        print("NODES =", nodes.count())
        print("EDGES =", edges.count())
        print("RESULT: LEVEL355_CONTROL_ID_CHECK_AND_GRAPH_PASS")
    except Exception as error:
        print("GRAPH_BUILD = FAILED")
        print("UNDERLYING_ERROR_TYPE =", type(error).__name__)
        print("UNDERLYING_ERROR_MESSAGE =", str(error))
        print("RESULT: LEVEL355_CONTROL_ID_CHECK_IDENTIFIED_BLOCKER")
else:
    print("RESULT: LEVEL355_CONTEXT_NOT_READY")
