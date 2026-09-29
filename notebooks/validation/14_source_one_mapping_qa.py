# %% Source One mapping QA gate
# Date: 2026-09-29
# READ ONLY. No DML / DDL / MERGE / INSERT / UPDATE / DELETE.
#
# Run after a successful Cell 7 PREVIEW or COMMIT/verification in the same notebook session.
# The script validates the currently selected Source One model route(s).
#
# Outputs:
#   QA_SUMMARY
#   QA_COVERAGE_DF   - one row per active runtime mapping
#   QA_ATTENTION_DF  - only rows needing review
#   QA_DISPOSITION_DF - deferred/excluded/blocked/blank-path inventory
#   QA_SAMPLE_DF     - deterministic 15-Content-ID source -> target value samples
#
# Important QA rules:
#   * A shared props/observations container is NOT enough. Evidence must match the
#     mapping's exact property name, target member, role, or reference identity.
#   * Populated source + empty target is a failure.
#   * No populated source data is reported separately and is not a mapping failure.
#   * Archer field types 9 and 23 are reported as relationship/reference exceptions
#     and are not forced through scalar value equality.
#   * Archer Dev FIELD_ID is resolved with source-table LevelId context. Ambiguous
#     matches are reported; this script never silently chooses one.
#   * Config/support mappings are separated from Archer-field validation.

import copy
import json
from collections import defaultdict
from snowflake.snowpark import functions as F

QA_SOURCE_KEY = "source-one"
QA_SAMPLE_CONTENT_IDS = 15
QA_META_FIELD_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_FIELD"
QA_RELATIONSHIP_FIELD_TYPES = {9, 23}

if "MAPPING_INPUTS" not in globals() or QA_SOURCE_KEY not in MAPPING_INPUTS:
    raise ValueError("Run current Cell 2 before Source One QA")
if "MAPPING_CONTEXTS" not in globals() or "SOURCE_INPUTS" not in globals():
    raise ValueError("Run current Cells 2-3 before Source One QA")
if "MODEL_GRAPHS" not in globals() or MODEL_GRAPHS is None:
    raise ValueError("Run current Cell 7 PREVIEW/COMMIT before Source One QA")
if "PIPELINE_REPORT" not in globals() or PIPELINE_REPORT is None:
    raise ValueError("Current Cell 7 report is unavailable")

source_profile = next(
    (p for p in SOURCE_PROFILES if p["SOURCE_KEY"] == QA_SOURCE_KEY),
    None,
)
if source_profile is None:
    raise ValueError("Current notebook selection does not include Source One")

route_contexts = [
    c for c in MAPPING_CONTEXTS
    if c["source_key"] == QA_SOURCE_KEY and c["routing_report"]["STATUS"] == "READY"
]
if not route_contexts:
    raise ValueError("No READY Source One route is loaded")

report_by_route = {
    (g["source"], g["model"]): g["load"]
    for g in PIPELINE_REPORT.get("groups", [])
}
for context in route_contexts:
    route = (QA_SOURCE_KEY, context["config"]["OSCAL_MODEL"])
    load = report_by_route.get(route)
    if load is None or load.get("status") not in {
        "PREVIEW_PASSED_NO_TARGET_DML", "COMMITTED_AND_VERIFIED"
    }:
        raise ValueError("Every selected Source One route needs an accepted Cell 7 result before QA")

# Use the runtime contexts retained by Cell 7 because those contain the frozen
# lookup snapshots actually used to build/verify the graph.
runtime_contexts = []
for context in route_contexts:
    route = (QA_SOURCE_KEY, context["config"]["OSCAL_MODEL"])
    graph = MODEL_GRAPHS.get(route)
    if graph is None or graph.get("context") is None:
        raise ValueError("Cell 7 runtime context is unavailable for " + str(route))
    runtime_contexts.append(graph["context"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _qa_json(value):
    value = _to_python(value)
    return json.dumps(value, sort_keys=True, default=str, allow_nan=False)


def _qa_present(value):
    return value is not SKIP_VALUE


def _qa_populated(value):
    return value is not SKIP_VALUE and _has_value(value)


def _qa_payload_get(payload, target):
    if not target:
        return payload
    return _metadata_get(payload, target)


def _qa_property_name(row):
    return _metadata_params(row).get("property_name") or _stable_property_name(
        row["SOURCE_FIELD_NAME"]
    )


def _qa_target_values(row, node):
    """Return exact mapping-specific values from one canonical graph node."""
    payload = node["payload"]
    operator = row["REPRESENTATION"]
    target = _metadata_target(row)

    if operator == "properties":
        expected_name = _qa_property_name(row)
        if payload.get("name") != expected_name or "value" not in payload:
            return []
        return [payload.get("value")]

    if operator == "observations":
        expected_name = _qa_property_name(row)
        if node["instance_key"] != row["SOURCE_FIELD_NAME"]:
            return []
        values = []
        for prop in payload.get("props") or []:
            if isinstance(prop, dict) and prop.get("name") == expected_name and "value" in prop:
                values.append(prop.get("value"))
        return values

    if operator == "assignments":
        params = _metadata_params(row)
        if node["instance_key"] != row["SOURCE_FIELD_NAME"]:
            return []
        if payload.get("role-id") != params.get("role_id"):
            return []
        refs = payload.get("party-uuids")
        return [payload] if isinstance(refs, list) and len(refs) > 0 else []

    if operator == "references":
        # Exact evidence is matched later by source reference identity -> node instance key.
        return [payload]

    value = _qa_payload_get(payload, target)
    if value is None:
        # Explicit JSON null can be a valid preserved target.
        return [None] if target and target.split(".")[-1] in _qa_json(payload) else []
    return [value] if _has_value(value) else []


def _qa_expected_value(row, source_obj, context):
    qa_context = dict(context)
    qa_context["graph_report"] = {
        "STATUS": "NOT_RUN", "MAPPED_VALUES": 0, "MISSING_VALUES": 0
    }
    value = _metadata_mapped_value(row, source_obj, qa_context)
    if value is SKIP_VALUE:
        return SKIP_VALUE
    operator = row["REPRESENTATION"]
    if operator in {"properties", "observations"}:
        return [None] if value is None else _oscal_property_values(value)
    if row["TRANSFORM_ID"] == "status-crosswalk":
        target = _metadata_target(row)
        return _metadata_get(value, target)
    return value


def _qa_values_equal(expected, actual_values):
    if expected is SKIP_VALUE:
        return None
    if isinstance(expected, list):
        return sorted(_qa_json(v) for v in expected) == sorted(
            _qa_json(v) for v in actual_values
        )
    return any(_qa_json(expected) == _qa_json(v) for v in actual_values)


def _qa_level_ids(table_name):
    rows = session.sql(f"""
        SELECT DISTINCT
            IFF(TYPEOF(RAW_DATA) = 'ARRAY', RAW_DATA[0], RAW_DATA)
                :"RequestedObject":"LevelId"::NUMBER AS LEVEL_ID
        FROM {table_name}
        WHERE RAW_DATA IS NOT NULL
    """).collect()
    return sorted({int(r["LEVEL_ID"]) for r in rows if r["LEVEL_ID"] is not None})


# ---------------------------------------------------------------------------
# Full mapping disposition inventory
# ---------------------------------------------------------------------------

all_mapping_rows = MAPPING_INPUTS[QA_SOURCE_KEY]
disposition_rows = []
for row in all_mapping_rows:
    status = (row.get("EXECUTION_STATUS") or "").strip() or "<BLANK>"
    path = (row.get("RUNTIME_TARGET_PATH") or row.get("OSCAL_ELEMENT_PATH") or "").strip()
    if status != "APPROVED" or not path or "TBD" in path.upper() or "MULTIPLE" in path.upper():
        disposition_rows.append({
            "SOURCE_FIELD_NAME": row.get("SOURCE_FIELD_NAME"),
            "OSCAL_MODEL": row.get("OSCAL_MODEL"),
            "EXECUTION_STATUS": status,
            "TARGET_PATH": path or "<BLANK>",
            "RULE_ID": row.get("RULE_ID"),
        })

# ---------------------------------------------------------------------------
# Archer Dev FIELD_ID resolution with source-level context
# ---------------------------------------------------------------------------

active_rows = []
for context in runtime_contexts:
    model = context["config"]["OSCAL_MODEL"]
    for row in context["mapping_rows"]:
        active_rows.append((context, model, row))

source_tables = {source_profile["RAW_TABLE"]}
for context, model, row in active_rows:
    params = _metadata_params(row)
    if row["REPRESENTATION"] == "joined-records":
        binding = params.get("joined_lookup")
        contract = context["lookups"]["joined_contract"].get(binding, {})
        if contract.get("source_table"):
            source_tables.add(contract["source_table"])

levels_by_table = {table: _qa_level_ids(table) for table in sorted(source_tables)}

field_origin = {}
field_names = set()
for context, model, row in active_rows:
    field = row["SOURCE_FIELD_NAME"]
    params = _metadata_params(row)
    if params.get("value_source") == "CONFIG":
        field_origin[(model, row["RULE_ID"])] = (None, ())
        continue
    table = source_profile["RAW_TABLE"]
    if row["REPRESENTATION"] == "joined-records":
        binding = params.get("joined_lookup")
        contract = context["lookups"]["joined_contract"].get(binding, {})
        table = contract.get("source_table") or table
    field_origin[(model, row["RULE_ID"])] = (table, tuple(levels_by_table.get(table, ())))
    field_names.add(field.upper())

meta_candidates = defaultdict(list)
if field_names:
    meta_df = session.table(QA_META_FIELD_TABLE).filter(
        F.upper(F.col("SQL_FIELD_NAME")).isin(list(sorted(field_names)))
    ).select(
        "FIELD_ID", "FIELD_TYPE_ID", "LEVEL_ID", "MODULE_ID",
        "SQL_FIELD_NAME", "FIELD_NAME"
    )
    for record in meta_df.to_local_iterator():
        item = {str(k).upper(): v for k, v in record.as_dict().items()}
        meta_candidates[str(item["SQL_FIELD_NAME"]).upper()].append(item)


def _qa_meta_resolution(model, row):
    params = _metadata_params(row)
    if params.get("value_source") == "CONFIG":
        return {
            "ARCHER_DEV_FIELD_ID": None,
            "ARCHER_FIELD_TYPE_ID": None,
            "META_FIELD_STATUS": "CONFIG_SUPPORT",
        }
    field = row["SOURCE_FIELD_NAME"].upper()
    _, levels = field_origin[(model, row["RULE_ID"])]
    candidates = [
        item for item in meta_candidates.get(field, [])
        if not levels or item["LEVEL_ID"] in levels
    ]
    ids = sorted({int(item["FIELD_ID"]) for item in candidates if item["FIELD_ID"] is not None})
    types = sorted({int(item["FIELD_TYPE_ID"]) for item in candidates if item["FIELD_TYPE_ID"] is not None})
    return {
        "ARCHER_DEV_FIELD_ID": str(ids[0]) if len(ids) == 1 else "|".join(map(str, ids)) or None,
        "ARCHER_FIELD_TYPE_ID": str(types[0]) if len(types) == 1 else "|".join(map(str, types)) or None,
        "META_FIELD_STATUS": (
            "RESOLVED" if len(ids) == 1
            else "NOT_FOUND" if len(ids) == 0
            else "AMBIGUOUS"
        ),
    }

# ---------------------------------------------------------------------------
# Source coverage and deterministic 15-Content-ID sample cohort
# ---------------------------------------------------------------------------

source_records = {}
for record in SOURCE_INPUTS[QA_SOURCE_KEY]["source_df"].to_local_iterator():
    rid = str(record["SOURCE_RECORD_ID"]).strip()
    source_records[rid] = _metadata_parse(record, runtime_contexts[0])

sample_content_ids = sorted(source_records)[:QA_SAMPLE_CONTENT_IDS]

coverage = {}
source_expected = defaultdict(lambda: defaultdict(list))
sample_expected = {}

for context, model, row in active_rows:
    key = (model, row["RULE_ID"])
    coverage[key] = {
        "SOURCE_FIELD_NAME": row["SOURCE_FIELD_NAME"],
        "OSCAL_MODEL": model,
        "RULE_ID": row["RULE_ID"],
        "TARGET_PATH": row["CANONICAL_ELEMENT_PATH"],
        "OWNER_ELEMENT_PATH": row["OWNER_ELEMENT_PATH"],
        "REPRESENTATION": row["REPRESENTATION"],
        "TRANSFORM_ID": row["TRANSFORM_ID"],
        "SOURCE_PRESENT": 0,
        "SOURCE_POPULATED": 0,
        "SOURCE_EXPLICIT_NULL": 0,
        "TARGET_EVIDENCE_RECORDS": set(),
        "TARGET_EVIDENCE_OCCURRENCES": 0,
        "TARGET_VALUES_BY_RECORD": defaultdict(list),
    }

    params = _metadata_params(row)
    if params.get("value_source") == "CONFIG":
        continue

    if row["REPRESENTATION"] == "joined-records":
        binding = params.get("joined_lookup")
        joined = context["lookups"]["joined_sources"].get(binding)
        if joined is None:
            continue
        for child in joined.to_local_iterator():
            rid = str(child["CONTENT_ID"]).strip()
            child_obj = _to_python(child["CURATED_JSON"])
            raw = resolve_json_path(child_obj, row["SOURCE_FIELD_NAME"], default=SKIP_VALUE)
            if _qa_present(raw):
                coverage[key]["SOURCE_PRESENT"] += 1
            if raw is None:
                coverage[key]["SOURCE_EXPLICIT_NULL"] += 1
            if _qa_populated(raw):
                coverage[key]["SOURCE_POPULATED"] += 1
                source_expected[key][rid].append(raw)
        continue

    for rid, source_obj in source_records.items():
        raw = resolve_json_path(source_obj, row["SOURCE_FIELD_NAME"], default=SKIP_VALUE)
        if _qa_present(raw):
            coverage[key]["SOURCE_PRESENT"] += 1
        if raw is None:
            coverage[key]["SOURCE_EXPLICIT_NULL"] += 1
        if _qa_populated(raw):
            coverage[key]["SOURCE_POPULATED"] += 1
            source_expected[key][rid].append(raw)
            if rid in sample_content_ids:
                try:
                    sample_expected[(key, rid)] = _qa_expected_value(row, source_obj, context)
                except Exception as error:
                    sample_expected[(key, rid)] = {
                        "__qa_error__": type(error).__name__
                    }

# ---------------------------------------------------------------------------
# Exact target evidence from the current canonical graph.
# Cell 7 has already verified this graph against the persisted target.
# ---------------------------------------------------------------------------

rows_by_owner = defaultdict(list)
context_by_model = {}
for context, model, row in active_rows:
    rows_by_owner[(model, row["OWNER_ELEMENT_PATH"])].append(row)
    context_by_model[model] = context

for context in runtime_contexts:
    model = context["config"]["OSCAL_MODEL"]
    graph = MODEL_GRAPHS[(QA_SOURCE_KEY, model)]["nodes"]
    owner_paths = sorted({
        row["OWNER_ELEMENT_PATH"] for c, m, row in active_rows if m == model
    })
    node_frame = graph.filter(F.col("ELEMENT_PATH").isin(owner_paths)).select(
        "ELEMENT_PATH", "INSTANCE_KEY", "SOURCE_RECORD_ID", "METADATA_JSON"
    )

    for record in node_frame.to_local_iterator():
        owner = record["ELEMENT_PATH"]
        rid = str(record["SOURCE_RECORD_ID"]).strip()
        payload = json.loads(record["METADATA_JSON"])
        node = {
            "instance_key": record["INSTANCE_KEY"],
            "payload": payload,
        }
        for row in rows_by_owner.get((model, owner), ()):
            key = (model, row["RULE_ID"])
            operator = row["REPRESENTATION"]
            values = _qa_target_values(row, node)

            if operator == "references":
                # Match this mapping to the exact source-referenced identity, not merely
                # another node in the same shared collection.
                expected_ids = set()
                for raw in source_expected[key].get(rid, ()):
                    try:
                        expected_ids.update(_component_reference_content_ids(raw))
                    except Exception:
                        pass
                if record["INSTANCE_KEY"] not in expected_ids:
                    continue

            if not values:
                continue
            coverage[key]["TARGET_EVIDENCE_OCCURRENCES"] += 1
            coverage[key]["TARGET_EVIDENCE_RECORDS"].add(rid)
            if rid in sample_content_ids:
                coverage[key]["TARGET_VALUES_BY_RECORD"][rid].extend(values)

# ---------------------------------------------------------------------------
# Final classification
# ---------------------------------------------------------------------------

coverage_rows = []
attention_rows = []
sample_rows = []

for context, model, row in active_rows:
    key = (model, row["RULE_ID"])
    item = coverage[key]
    meta = _qa_meta_resolution(model, row)
    item.update(meta)

    type_tokens = {
        int(v) for v in str(meta["ARCHER_FIELD_TYPE_ID"] or "").split("|")
        if v.isdigit()
    }
    relationship_exception = bool(type_tokens & QA_RELATIONSHIP_FIELD_TYPES)
    config_support = meta["META_FIELD_STATUS"] == "CONFIG_SUPPORT"

    source_populated = item["SOURCE_POPULATED"]
    target_records = len(item["TARGET_EVIDENCE_RECORDS"])

    if config_support:
        qa_status = "SUPPORT_CONFIG_NOT_ARCHER_FIELD"
    elif source_populated == 0:
        qa_status = "NO_POPULATED_SOURCE_DATA"
    elif target_records == 0:
        qa_status = "POPULATED_SOURCE_TARGET_EMPTY"
    elif relationship_exception:
        qa_status = "RELATIONSHIP_EXCEPTION_EVIDENCE_PRESENT"
    else:
        qa_status = "TARGET_EVIDENCE_PRESENT"

    if meta["META_FIELD_STATUS"] in {"NOT_FOUND", "AMBIGUOUS"} and not config_support:
        qa_status = qa_status + "__META_FIELD_" + meta["META_FIELD_STATUS"]

    output = {
        "SOURCE_FIELD_NAME": item["SOURCE_FIELD_NAME"],
        "OSCAL_MODEL": model,
        "ARCHER_DEV_FIELD_ID": meta["ARCHER_DEV_FIELD_ID"],
        "ARCHER_FIELD_TYPE_ID": meta["ARCHER_FIELD_TYPE_ID"],
        "META_FIELD_STATUS": meta["META_FIELD_STATUS"],
        "TARGET_PATH": item["TARGET_PATH"],
        "SOURCE_PRESENT": item["SOURCE_PRESENT"],
        "SOURCE_POPULATED": source_populated,
        "SOURCE_EXPLICIT_NULL": item["SOURCE_EXPLICIT_NULL"],
        "TARGET_EVIDENCE_RECORDS": target_records,
        "TARGET_EVIDENCE_OCCURRENCES": item["TARGET_EVIDENCE_OCCURRENCES"],
        "QA_STATUS": qa_status,
        "RULE_ID": item["RULE_ID"],
    }
    coverage_rows.append(output)

    if (
        "TARGET_EMPTY" in qa_status
        or "META_FIELD_NOT_FOUND" in qa_status
        or "META_FIELD_AMBIGUOUS" in qa_status
        or "RELATIONSHIP_EXCEPTION" in qa_status
    ):
        attention_rows.append(output)

    if (
        not config_support
        and source_populated > 0
        and not relationship_exception
        and row["REPRESENTATION"] not in {"assignments", "references", "joined-records"}
    ):
        for rid in sample_content_ids:
            expected = sample_expected.get((key, rid), SKIP_VALUE)
            if expected is SKIP_VALUE:
                continue
            actual = item["TARGET_VALUES_BY_RECORD"].get(rid, [])
            if isinstance(expected, dict) and "__qa_error__" in expected:
                match = "EXPECTED_TRANSFORM_ERROR"
            else:
                match = "MATCH" if _qa_values_equal(expected, actual) else "MISMATCH"
            sample_rows.append({
                "CONTENT_ID": rid,
                "SOURCE_FIELD_NAME": item["SOURCE_FIELD_NAME"],
                "OSCAL_MODEL": model,
                "TARGET_PATH": item["TARGET_PATH"],
                "EXPECTED_VALUE": _qa_json(expected),
                "TARGET_VALUES": _qa_json(actual),
                "VALUE_STATUS": match,
            })

# ---------------------------------------------------------------------------
# Publish read-only result frames
# ---------------------------------------------------------------------------

def _qa_frame(rows, columns, fallback):
    data = rows if rows else [fallback]
    return session.create_dataframe(
        [tuple(row.get(name) for name in columns) for row in data],
        schema=columns,
    )


coverage_columns = [
    "SOURCE_FIELD_NAME", "OSCAL_MODEL", "ARCHER_DEV_FIELD_ID",
    "ARCHER_FIELD_TYPE_ID", "META_FIELD_STATUS", "TARGET_PATH",
    "SOURCE_PRESENT", "SOURCE_POPULATED", "SOURCE_EXPLICIT_NULL",
    "TARGET_EVIDENCE_RECORDS", "TARGET_EVIDENCE_OCCURRENCES",
    "QA_STATUS", "RULE_ID",
]
disposition_columns = [
    "SOURCE_FIELD_NAME", "OSCAL_MODEL", "EXECUTION_STATUS", "TARGET_PATH", "RULE_ID",
]
sample_columns = [
    "CONTENT_ID", "SOURCE_FIELD_NAME", "OSCAL_MODEL", "TARGET_PATH",
    "EXPECTED_VALUE", "TARGET_VALUES", "VALUE_STATUS",
]

QA_COVERAGE_DF = _qa_frame(
    coverage_rows,
    coverage_columns,
    {name: None for name in coverage_columns},
)
QA_ATTENTION_DF = _qa_frame(
    attention_rows,
    coverage_columns,
    {
        **{name: None for name in coverage_columns},
        "SOURCE_FIELD_NAME": "<NONE>",
        "OSCAL_MODEL": "<NONE>",
        "META_FIELD_STATUS": "NONE",
        "TARGET_PATH": "<NONE>",
        "SOURCE_PRESENT": 0,
        "SOURCE_POPULATED": 0,
        "SOURCE_EXPLICIT_NULL": 0,
        "TARGET_EVIDENCE_RECORDS": 0,
        "TARGET_EVIDENCE_OCCURRENCES": 0,
        "QA_STATUS": "NO_ATTENTION_ROWS",
        "RULE_ID": "<NONE>",
    },
)
QA_DISPOSITION_DF = _qa_frame(
    disposition_rows,
    disposition_columns,
    {
        "SOURCE_FIELD_NAME": "<NONE>",
        "OSCAL_MODEL": "<NONE>",
        "EXECUTION_STATUS": "NONE",
        "TARGET_PATH": "<NONE>",
        "RULE_ID": "<NONE>",
    },
)
QA_SAMPLE_DF = _qa_frame(
    sample_rows,
    sample_columns,
    {
        "CONTENT_ID": "<NONE>",
        "SOURCE_FIELD_NAME": "<NONE>",
        "OSCAL_MODEL": "<NONE>",
        "TARGET_PATH": "<NONE>",
        "EXPECTED_VALUE": "<NONE>",
        "TARGET_VALUES": "<NONE>",
        "VALUE_STATUS": "NO_SAMPLE_ROWS",
    },
)

status_counts = defaultdict(int)
for row in coverage_rows:
    status_counts[row["QA_STATUS"]] += 1

sample_status_counts = defaultdict(int)
for row in sample_rows:
    sample_status_counts[row["VALUE_STATUS"]] += 1

QA_SUMMARY = {
    "SOURCE_KEY": QA_SOURCE_KEY,
    "MODELS_VALIDATED": sorted({row["OSCAL_MODEL"] for row in coverage_rows}),
    "ACTIVE_MAPPING_ROWS": len(coverage_rows),
    "MAPPING_STATUS_COUNTS": dict(sorted(status_counts.items())),
    "DISPOSITION_ROWS": len(disposition_rows),
    "SAMPLE_CONTENT_IDS": sample_content_ids,
    "SAMPLE_VALUE_STATUS_COUNTS": dict(sorted(sample_status_counts.items())),
    "ATTENTION_ROWS": len(attention_rows),
}

print("SOURCE_ONE_QA_SUMMARY")
print(json.dumps(QA_SUMMARY, indent=2, default=str))

print("\nSOURCE_ONE_QA_ATTENTION")
QA_ATTENTION_DF.sort("OSCAL_MODEL", "SOURCE_FIELD_NAME").show(n=500, max_width=120)

print("\nSOURCE_ONE_QA_DISPOSITIONS")
QA_DISPOSITION_DF.sort("EXECUTION_STATUS", "OSCAL_MODEL", "SOURCE_FIELD_NAME").show(n=500, max_width=120)

print("\nSOURCE_ONE_QA_SAMPLE_VALUE_CHECKS")
QA_SAMPLE_DF.sort("CONTENT_ID", "OSCAL_MODEL", "SOURCE_FIELD_NAME").show(n=2000, max_width=120)

print("\nSOURCE_ONE_QA_COVERAGE_ALL")
QA_COVERAGE_DF.sort("OSCAL_MODEL", "SOURCE_FIELD_NAME").show(n=500, max_width=120)
