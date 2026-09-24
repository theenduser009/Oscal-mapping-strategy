# RUN NOW — Diagnose missing SSP component hydration lookups
# Date: 2026-09-24
# READ ONLY. No source, registry, mapping, DIM, or FACT DML.
#
# Prior graph-build error:
#   Component hydration lookup record is missing
#
# Current approved hydrated component contracts:
#   SOFTWARE -> software -> ARCHER_CONTENT_SOFTWARE_RAW
#   INTERCONNECTIONS -> interconnection -> ARCHER_CONTENT_INTERCONNECTIONS_RAW
#   INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM -> interconnection -> same lookup
#
# This helper compares referenced ContentIds to both the frozen Cell-2 lookup
# snapshots and the current live RAW lookup tables. It prints only aggregate
# counts, never the ContentIds themselves.

from collections import defaultdict

SOURCE_KEY = "source-one"

HYDRATED_FIELDS = {
    "SOFTWARE": "software",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
}

LOOKUP_TABLES = {
    "software": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW",
    "interconnection": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW",
}

def py(v):
    if hasattr(v, "as_dict"):
        return v.as_dict(recursive=True)
    if hasattr(v, "as_list"):
        return v.as_list()
    return v

def content_ids(value):
    value = py(value)
    if value in (None, "", [], {}):
        return []
    members = value if isinstance(value, list) else [value]
    out = []
    for item in members:
        item = py(item)
        if isinstance(item, dict):
            item = item.get("ContentId")
        if item is not None and str(item).strip():
            out.append(str(item).strip())
    return out

source = SOURCE_INPUTS[SOURCE_KEY]
refs_by_kind = defaultdict(set)
refs_by_field = defaultdict(set)

for row in source["source_df"].to_local_iterator():
    payload = py(row["CURATED_JSON"])
    if not isinstance(payload, dict):
        continue
    for field, kind in HYDRATED_FIELDS.items():
        ids = content_ids(payload.get(field))
        refs_by_kind[kind].update(ids)
        refs_by_field[field].update(ids)

print("SOURCE_ONE_COMPONENT_HYDRATION_DIAGNOSTIC")
print("SOURCE_SELECTED_ROWS =", source.get("selection", {}).get("SELECTED_ROWS"))

for field, kind in HYDRATED_FIELDS.items():
    print(
        "FIELD_REFERENCE_COUNT",
        field,
        "| TYPE =", kind,
        "| DISTINCT_REFERENCES =", len(refs_by_field[field]),
    )

frozen_sources = source.get("lookups", {}).get("component_sources", {})

for kind in ("software", "interconnection"):
    required = refs_by_kind[kind]
    frozen = frozen_sources.get(kind)

    print()
    print("COMPONENT_TYPE =", kind)
    print("REQUIRED_DISTINCT_REFERENCES =", len(required))

    if frozen is None:
        print("FROZEN_LOOKUP_PRESENT = False")
        frozen_ids = set()
        frozen_total = None
    else:
        print("FROZEN_LOOKUP_PRESENT = True")
        frozen_total = frozen.count()
        frozen_ids = {
            str(r["CONTENT_ID"]).strip()
            for r in frozen.select("CONTENT_ID").distinct().collect()
            if r["CONTENT_ID"] is not None
        }
        print("FROZEN_LOOKUP_ROWS =", frozen_total)
        print("FROZEN_LOOKUP_DISTINCT_IDS =", len(frozen_ids))

    live_table = LOOKUP_TABLES[kind]
    live = session.sql(f"""
        SELECT
            COUNT(*) AS RAW_ROWS,
            COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS DISTINCT_CONTENT_IDS
        FROM {live_table}
    """).collect()[0]

    print("LIVE_LOOKUP_TABLE =", live_table)
    print("LIVE_LOOKUP_ROWS =", live["RAW_ROWS"])
    print("LIVE_LOOKUP_DISTINCT_IDS =", live["DISTINCT_CONTENT_IDS"])

    if required:
        quoted = ", ".join("'" + x.replace("'", "''") + "'" for x in sorted(required))
        live_match = session.sql(f"""
            SELECT COUNT(DISTINCT TRIM(CONTENT_ID::STRING)) AS MATCHED
            FROM {live_table}
            WHERE TRIM(CONTENT_ID::STRING) IN ({quoted})
        """).collect()[0]["MATCHED"]
    else:
        live_match = 0

    frozen_match = len(required & frozen_ids)
    print("FROZEN_MATCHED_REFERENCES =", frozen_match)
    print("FROZEN_MISSING_REFERENCES =", len(required) - frozen_match)
    print("LIVE_MATCHED_REFERENCES =", live_match)
    print("LIVE_MISSING_REFERENCES =", len(required) - int(live_match or 0))

print()
software_missing_frozen = len(refs_by_kind["software"]) - len(
    refs_by_kind["software"] & (
        {
            str(r["CONTENT_ID"]).strip()
            for r in frozen_sources["software"].select("CONTENT_ID").distinct().collect()
            if r["CONTENT_ID"] is not None
        } if "software" in frozen_sources else set()
    )
)
inter_missing_frozen = len(refs_by_kind["interconnection"]) - len(
    refs_by_kind["interconnection"] & (
        {
            str(r["CONTENT_ID"]).strip()
            for r in frozen_sources["interconnection"].select("CONTENT_ID").distinct().collect()
            if r["CONTENT_ID"] is not None
        } if "interconnection" in frozen_sources else set()
    )
)

if software_missing_frozen == 0 and inter_missing_frozen == 0:
    print("RESULT: FROZEN_COMPONENT_LOOKUPS_COMPLETE_RETRY_GRAPH")
else:
    print("RESULT: COMPONENT_LOOKUP_COVERAGE_GAP_IDENTIFIED")
