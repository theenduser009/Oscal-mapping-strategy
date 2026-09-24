# RUN NOW — Corrected SSP component hydration coverage diagnostic
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Correction:
# The prior aggregate helper did not JSON-decode CURATED_JSON when Snowpark
# returned the VARIANT as a Python string. That made component-reference counts
# appear as zero. This version uses the mapper's own _metadata_parse() routine,
# so it applies the exact same source interpretation as the graph builder.
#
# Prior graph-build error:
#   Component hydration lookup record is missing
#
# Current hydrated component contracts:
#   SOFTWARE -> software -> ARCHER_CONTENT_SOFTWARE_RAW
#   INTERCONNECTIONS -> interconnection -> ARCHER_CONTENT_INTERCONNECTIONS_RAW
#   INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM -> interconnection -> same lookup
#
# Aggregate counts only. Referenced ContentIds are never printed.

from collections import defaultdict
from snowflake.snowpark import functions as F

SOURCE_KEY = "source-one"
ROUTE = ("source-one", "SSP")

HYDRATED_FIELDS = {
    "SOFTWARE": "software",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
}

LOOKUP_TABLES = {
    "software": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW",
    "interconnection": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW",
}

def component_ids(value):
    value = _to_python(value)
    if not _has_value(value):
        return []
    if not isinstance(value, list):
        raise ValueError("Hydrated component reference root must be an array")
    return _component_reference_content_ids(value)

contexts = [
    c for c in MAPPING_CONTEXTS
    if (c["source_key"], c["config"]["OSCAL_MODEL"]) == ROUTE
]
if len(contexts) != 1:
    raise ValueError("Expected exactly one source-one / SSP mapping context")

context = copy.deepcopy(contexts[0])
source = SOURCE_INPUTS[SOURCE_KEY]
context["lookups"] = source.get("lookups", {})

refs_by_kind = defaultdict(set)
refs_by_field = defaultdict(set)

for record in source["source_df"].to_local_iterator():
    payload = _metadata_parse(record, context)
    for field, kind in HYDRATED_FIELDS.items():
        ids = component_ids(resolve_json_path(payload, field))
        refs_by_field[field].update(ids)
        refs_by_kind[kind].update(ids)

print("SOURCE_ONE_COMPONENT_HYDRATION_DIAGNOSTIC_CORRECTED")
print("SOURCE_SELECTED_ROWS =", source.get("selection", {}).get("SELECTED_ROWS"))

for field, kind in HYDRATED_FIELDS.items():
    print(
        "FIELD_REFERENCE_COUNT",
        field,
        "| TYPE =", kind,
        "| DISTINCT_REFERENCES =", len(refs_by_field[field]),
    )

frozen_sources = source.get("lookups", {}).get("component_sources", {})
summary = {}

for kind in ("software", "interconnection"):
    required = refs_by_kind[kind]
    frozen = frozen_sources.get(kind)

    print()
    print("COMPONENT_TYPE =", kind)
    print("REQUIRED_DISTINCT_REFERENCES =", len(required))

    if frozen is None:
        print("FROZEN_LOOKUP_PRESENT = False")
        frozen_ids = set()
        frozen_rows = None
    else:
        print("FROZEN_LOOKUP_PRESENT = True")
        frozen_rows = frozen.count()
        frozen_ids = {
            str(r["CONTENT_ID"]).strip()
            for r in frozen.select("CONTENT_ID").distinct().collect()
            if r["CONTENT_ID"] is not None
        }
        print("FROZEN_LOOKUP_ROWS =", frozen_rows)
        print("FROZEN_LOOKUP_DISTINCT_IDS =", len(frozen_ids))

    live_table = LOOKUP_TABLES[kind]
    live_stats = session.sql(f"""
        SELECT
            COUNT(*) AS RAW_ROWS,
            COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_CONTENT_IDS
        FROM {live_table}
    """).collect()[0]

    print("LIVE_LOOKUP_TABLE =", live_table)
    print("LIVE_LOOKUP_ROWS =", live_stats["RAW_ROWS"])
    print("LIVE_LOOKUP_DISTINCT_IDS =", live_stats["DISTINCT_CONTENT_IDS"])

    if required:
        required_df = session.create_dataframe([(x,) for x in sorted(required)], schema=["CONTENT_ID"])
        live_df = session.table(live_table).select(
            F.trim(F.col("CONTENT_ID").cast("string")).alias("CONTENT_ID")
        ).distinct()
        live_match = required_df.join(live_df, "CONTENT_ID", "inner").count()
    else:
        live_match = 0

    frozen_match = len(required & frozen_ids)
    frozen_missing = len(required) - frozen_match
    live_missing = len(required) - int(live_match or 0)

    print("FROZEN_MATCHED_REFERENCES =", frozen_match)
    print("FROZEN_MISSING_REFERENCES =", frozen_missing)
    print("LIVE_MATCHED_REFERENCES =", live_match)
    print("LIVE_MISSING_REFERENCES =", live_missing)

    summary[kind] = {
        "required": len(required),
        "frozen_missing": frozen_missing,
        "live_missing": live_missing,
        "frozen_rows": frozen_rows,
        "live_rows": int(live_stats["RAW_ROWS"] or 0),
    }

print()
print("SUMMARY =", summary)

if all(v["frozen_missing"] == 0 for v in summary.values()):
    print("RESULT: FROZEN_COMPONENT_LOOKUPS_COMPLETE_RETRY_GRAPH")
elif all(v["live_missing"] == 0 for v in summary.values()):
    print("RESULT: LIVE_LOOKUPS_COMPLETE_RERUN_CELL_2_THEN_3_AND_7")
else:
    print("RESULT: LIVE_COMPONENT_LOOKUP_COVERAGE_GAP_IDENTIFIED")
