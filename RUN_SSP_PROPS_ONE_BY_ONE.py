# %% SSP props QA — one field at a time
# Date: 2026-10-02
# READ ONLY. No DML / DDL / MERGE / INSERT / UPDATE / DELETE.
#
# Run after a successful SSP Cell 7 PREVIEW in the SAME Snowflake notebook session.
#
# Start with metadata props only. Later change QA_PROP_PATH to:
#   system-security-plan.system-characteristics.props[]
#
# What this proves for each mapped prop:
#   Archer SQL field name
#   Archer display field name / FIELD_ID / FIELD_TYPE_ID
#   exact OSCAL props[] path
#   exact expected OSCAL prop name
#   source present/populated/null counts
#   exact source-transformed value vs actual prop value
#   deterministic sample Content IDs
#
# This helper intentionally does NOT use the broad QA "relationship exception" shortcut.
# A prop mapping must match its exact property name and exact transformed value.

import json
from collections import defaultdict
from snowflake.snowpark import functions as F

QA_PROP_PATH = "system-security-plan.metadata.props[]"
QA_SAMPLE_PER_FIELD = 5
QA_META_FIELD_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD"
QA_SOURCE_KEY = "source-one"
QA_MODEL = "SSP"
QA_RUNTIME_RELEASE = "lean-csv-registry-v10-curated-resolved-only"

route = (QA_SOURCE_KEY, QA_MODEL)
if "MODEL_GRAPHS" not in globals() or route not in MODEL_GRAPHS:
    raise ValueError("Run current SSP Cell 7 PREVIEW before props QA")
if "SOURCE_INPUTS" not in globals() or QA_SOURCE_KEY not in SOURCE_INPUTS:
    raise ValueError("Run current Cell 2 before props QA")

graph = MODEL_GRAPHS[route]
ctx = graph["context"]
if ctx["compiled_plan"].get("release") != QA_RUNTIME_RELEASE:
    raise ValueError("Props QA requires the matched v10 curated-resolved-only runtime")

prop_rows = [
    row for row in ctx["mapping_rows"]
    if row["OWNER_ELEMENT_PATH"] == QA_PROP_PATH
       and row["REPRESENTATION"] == "properties"
       and row["TRANSFORM_ID"] != "skip"
]
if not prop_rows:
    raise ValueError("No active property mappings found for " + QA_PROP_PATH)

# ---------------------------------------------------------------------------
# Resolve Archer field metadata without silently choosing ambiguous candidates.
# ---------------------------------------------------------------------------

raw_table = ctx["config"]["RAW_TABLE"]
level_rows = session.sql(f"""
    SELECT DISTINCT
        IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA)
            :"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID
    FROM {raw_table}
    WHERE RAW_DATA IS NOT NULL
""").collect()
source_levels = sorted({
    int(row["LEVEL_ID"]) for row in level_rows if row["LEVEL_ID"] is not None
})

field_names = sorted({row["SOURCE_FIELD_NAME"].upper() for row in prop_rows})
meta_candidates = defaultdict(list)
if field_names:
    meta_df = session.table(QA_META_FIELD_TABLE).filter(
        F.upper(F.col("SQL_FIELD_NAME")).isin(*field_names)
    ).select(
        "FIELD_ID", "FIELD_TYPE_ID", "LEVEL_ID", "MODULE_ID",
        "SQL_FIELD_NAME", "FIELD_NAME"
    )
    for record in meta_df.to_local_iterator():
        item = {str(k).upper(): v for k, v in record.as_dict().items()}
        if source_levels and item["LEVEL_ID"] not in source_levels:
            continue
        meta_candidates[str(item["SQL_FIELD_NAME"]).upper()].append(item)


def _meta_summary(sql_field):
    items = meta_candidates.get(sql_field.upper(), [])
    field_ids = sorted({str(x["FIELD_ID"]) for x in items if x["FIELD_ID"] is not None})
    type_ids = sorted({str(x["FIELD_TYPE_ID"]) for x in items if x["FIELD_TYPE_ID"] is not None})
    display_names = sorted({str(x["FIELD_NAME"]) for x in items if x["FIELD_NAME"] is not None})
    level_ids = sorted({str(x["LEVEL_ID"]) for x in items if x["LEVEL_ID"] is not None})
    status = "RESOLVED" if len(field_ids) == 1 else "NOT_FOUND" if not field_ids else "AMBIGUOUS"
    return {
        "META_STATUS": status,
        "FIELD_ID": "|".join(field_ids) or None,
        "FIELD_TYPE_ID": "|".join(type_ids) or None,
        "ARCHER_FIELD_NAME": "|".join(display_names) or None,
        "LEVEL_ID": "|".join(level_ids) or None,
    }


# ---------------------------------------------------------------------------
# Freeze source + exact prop target evidence from the successful candidate graph.
# ---------------------------------------------------------------------------

source_records = {}
for record in SOURCE_INPUTS[QA_SOURCE_KEY]["source_df"].to_local_iterator():
    rid = str(record["SOURCE_RECORD_ID"]).strip()
    source_records[rid] = _metadata_parse(record, ctx)

actual_props = defaultdict(lambda: defaultdict(list))
node_rows = graph["nodes"].filter(
    F.col("ELEMENT_PATH") == F.lit(QA_PROP_PATH)
).select(
    "SOURCE_RECORD_ID", "METADATA_JSON"
).collect()

for record in node_rows:
    rid = str(record["SOURCE_RECORD_ID"]).strip()
    payload = json.loads(record["METADATA_JSON"])
    if not isinstance(payload, dict) or "name" not in payload:
        continue
    actual_props[rid][payload.get("name")].append(payload.get("value"))


def _json_key(value):
    return json.dumps(value, sort_keys=True, default=str, allow_nan=False)


def _expected_prop_values(mapping, source_obj):
    qa_ctx = dict(ctx)
    qa_ctx["graph_report"] = {
        "STATUS": "NOT_RUN",
        "MAPPED_VALUES": 0,
        "MISSING_VALUES": 0,
    }
    value = _metadata_mapped_value(mapping, source_obj, qa_ctx)
    if value is SKIP_VALUE:
        return SKIP_VALUE
    return [None] if value is None else _oscal_property_values(value)


def _same_values(expected, actual):
    return sorted(_json_key(x) for x in expected) == sorted(_json_key(x) for x in actual)


print("SSP_PROPS_ONE_BY_ONE")
print("PROP_PATH =", QA_PROP_PATH)
print("ACTIVE_PROP_MAPPINGS =", len(prop_rows))
print("SOURCE_LEVEL_IDS =", source_levels)

overall_failures = 0

for index, mapping in enumerate(sorted(prop_rows, key=lambda r: r["SOURCE_FIELD_NAME"]), start=1):
    field = mapping["SOURCE_FIELD_NAME"]
    prop_name = _metadata_params(mapping).get("property_name") or _stable_property_name(field)
    meta = _meta_summary(field)

    source_present = 0
    source_populated = 0
    source_explicit_null = 0
    target_records = 0
    exact_matches = 0
    mismatches = []
    samples = []

    for rid in sorted(source_records):
        source_obj = source_records[rid]
        raw = resolve_json_path(source_obj, field, default=SKIP_VALUE)

        if raw is not SKIP_VALUE:
            source_present += 1
        if raw is None:
            source_explicit_null += 1
        if raw is not SKIP_VALUE and _has_value(raw):
            source_populated += 1

        try:
            expected = _expected_prop_values(mapping, source_obj)
        except Exception as error:
            mismatches.append({
                "CONTENT_ID": rid,
                "ERROR": "TRANSFORM_" + type(error).__name__,
            })
            continue

        if expected is SKIP_VALUE:
            continue

        actual = actual_props[rid].get(prop_name, [])
        if actual:
            target_records += 1

        if _same_values(expected, actual):
            exact_matches += 1
        else:
            mismatches.append({
                "CONTENT_ID": rid,
                "EXPECTED": expected,
                "ACTUAL": actual,
            })

        if len(samples) < QA_SAMPLE_PER_FIELD:
            samples.append({
                "CONTENT_ID": rid,
                "SOURCE_RAW": _to_python(raw),
                "EXPECTED_PROP_VALUE": expected,
                "ACTUAL_PROP_VALUE": actual,
            })

    if mismatches:
        status = "FAIL_VALUE_OR_TARGET_MISMATCH"
        overall_failures += 1
    elif source_populated == 0:
        status = "NO_POPULATED_SOURCE_DATA"
    else:
        status = "PASS_EXACT_PROP_VALUE"

    print("\n" + "=" * 88)
    print(f"PROP {index}/{len(prop_rows)}")
    print("SQL_FIELD_NAME =", field)
    print("ARCHER_FIELD_NAME =", meta["ARCHER_FIELD_NAME"])
    print("ARCHER_FIELD_ID =", meta["FIELD_ID"])
    print("ARCHER_FIELD_TYPE_ID =", meta["FIELD_TYPE_ID"])
    print("ARCHER_LEVEL_ID =", meta["LEVEL_ID"])
    print("META_STATUS =", meta["META_STATUS"])
    print("OSCAL_PROP_PATH =", QA_PROP_PATH)
    print("EXPECTED_PROP_NAME =", prop_name)
    print("TRANSFORM_ID =", mapping["TRANSFORM_ID"])
    print("SOURCE_PRESENT =", source_present)
    print("SOURCE_POPULATED =", source_populated)
    print("SOURCE_EXPLICIT_NULL =", source_explicit_null)
    print("TARGET_RECORDS_WITH_EXACT_PROP_NAME =", target_records)
    print("EXACT_VALUE_MATCHES =", exact_matches)
    print("MISMATCHES =", len(mismatches))
    print("STATUS =", status)

    if samples:
        print("SAMPLES")
        for sample in samples:
            print(
                "  CONTENT_ID =", sample["CONTENT_ID"],
                "| SOURCE_RAW =", json.dumps(sample["SOURCE_RAW"], default=str),
                "| EXPECTED =", json.dumps(sample["EXPECTED_PROP_VALUE"], default=str),
                "| ACTUAL =", json.dumps(sample["ACTUAL_PROP_VALUE"], default=str),
            )

    if mismatches:
        print("FIRST_MISMATCH =", mismatches[0])

print("\n" + "=" * 88)
print("PROP_QA_FAILURES =", overall_failures)
print("SSP_PROPS_QA_COMPLETE =", overall_failures == 0)
