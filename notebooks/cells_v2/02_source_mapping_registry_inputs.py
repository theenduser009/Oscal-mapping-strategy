# %% Cell 2 - Source, mapping, registry, and Archer value inputs

import csv
import pandas as pd


def _normalized_columns(columns):
    result = {}
    for name in columns:
        key = str(name).strip().upper()
        if key in result:
            raise ValueError("Duplicate normalized source column")
        result[key] = name
    return result


def _input_no_transaction(active_session):
    # Temporary-table DDL must never commit somebody else's open transaction.
    try:
        current = active_session.sql("SELECT CURRENT_TRANSACTION() AS TX").collect()[0]["TX"]
    except Exception:
        raise ValueError("Cannot verify transaction state before input snapshot") from None
    if current is not None:
        raise ValueError("Finish the existing transaction before input snapshot")


def load_source_input(active_session, profile):
    _input_no_transaction(active_session)
    raw = active_session.table(profile["RAW_TABLE"])
    columns = _normalized_columns(raw.columns)
    id_name = profile.get("CONTENT_ID_COLUMN", "CONTENT_ID").upper()
    json_name = profile.get("CURATED_JSON_COLUMN", "CURATED_JSON").upper()
    if id_name not in columns or json_name not in columns:
        raise ValueError("Source requires its configured identity and curated JSON columns")
    selected = [col(columns[id_name]).cast("string").alias("SOURCE_RECORD_ID"),
                col(columns[json_name]).alias("CURATED_JSON")]
    order_columns = []
    for candidate in profile.get("SOURCE_ORDER_CANDIDATES", ()):
        if candidate in columns:
            selected.append(col(columns[candidate]).alias(candidate))
            order_columns.append(candidate)
    # Freeze once in a session-local temporary table, before validation and
    # model fan-out. Keep the returned cache handle alive in SOURCE_INPUTS.
    candidates = raw.select(*selected).cache_result()
    if candidates.filter("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0").count():
        raise ValueError("Source contains missing record identities")
    count = candidates.count()
    distinct = candidates.select("SOURCE_RECORD_ID").distinct().count()
    if count != distinct:
        if not order_columns:
            raise ValueError("Duplicate source identities require approved technical ordering")
        order = [col(name).desc_nulls_last() for name in order_columns]
        order.append(sha2(to_json(col("CURATED_JSON")), 256).desc_nulls_last())
        result = candidates.with_column(
            "_SOURCE_ROW_NUMBER", row_number().over(
                Window.partition_by("SOURCE_RECORD_ID").order_by(*order)
            )
        ).filter(col("_SOURCE_ROW_NUMBER") == lit(1)).drop(
            "_SOURCE_ROW_NUMBER", *order_columns
        )
    else:
        result = candidates.select("SOURCE_RECORD_ID", "CURATED_JSON")
    # The frozen snapshot yields one selected row per distinct source identity.
    return result, {"RAW_ROWS": count, "SELECTED_ROWS": distinct,
                    "DUPLICATE_SOURCE_ROWS_RESOLVED": count - distinct}, candidates


def _read_mapping_header(mapping_file, encoding="cp1252"):
    # Inspect the real header before pandas can mangle repeated column names.
    # Use the same encoding and CSV quoting rules as the mapping-file read.
    with open(mapping_file, encoding=encoding, newline="") as handle:
        header = next((row for row in csv.reader(handle)
                       if row and any(value.strip() for value in row)), None)
    if header is None:
        raise ValueError("Mapping CSV header is missing")
    return header


def load_mapping_rows(profile):
    encoding = profile.get("MAPPING_ENCODING", "cp1252")
    header = [str(name).strip().upper()
              for name in _read_mapping_header(profile["MAPPING_FILE"], encoding)]
    if len(header) != len(set(header)):
        raise ValueError("Duplicate normalized mapping columns")
    frame = pd.read_csv(profile["MAPPING_FILE"], encoding=encoding, dtype=str,
                        keep_default_na=False)
    # Preserve literal labels such as N/A; only empty cells are absent metadata.
    frame = frame.replace("", None)
    frame = frame.where(lambda data: data.notna(), None)
    frame.columns = [str(name).strip().upper() for name in frame.columns]
    if len(frame.columns) != len(set(frame.columns)):
        raise ValueError("Duplicate normalized mapping columns")
    source_column = profile.get("MAPPING_SOURCE_COLUMN")
    if source_column:
        source_column = source_column.upper()
        if source_column not in frame.columns:
            raise ValueError("Mapping source binding column is missing")
        binding = profile.get("MAPPING_SOURCE_VALUE", profile["SOURCE_TABLE_NAME"])
        frame = frame[frame[source_column].map(
            lambda value: str(value or "").strip() == binding
        )].copy()
    return frame


def load_source_lookups(active_session, profile, model_contracts, shared_config):
    _input_no_transaction(active_session)
    values = active_session.table(shared_config["ARCHER_META_VALUE_TABLE"]).select(
        col("SELECT_VALUE_ID"), col("SELECT_VALUE_NAME")
    ).filter(col("SELECT_VALUE_NAME").is_not_null())
    archer = {}
    for row in values.collect():
        if row["SELECT_VALUE_ID"] is not None:
            key = str(row["SELECT_VALUE_ID"]).strip()
            value = str(row["SELECT_VALUE_NAME"]).strip()
            if key in archer and archer[key] != value:
                raise ValueError("Archer lookup identity has conflicting labels")
            archer[key] = value
    components = {}
    required = {group for key in profile["MODEL_KEYS"]
                for group in model_contracts[key].get("LOOKUP_GROUPS", ())}
    # Lookup requirements are data in the source profile, not table names in
    # the shared input loader. Only profiles that need them read them.
    for kind, contract in profile.get("LOOKUP_CONTRACTS", {}).items():
        if "components" not in required:
            continue
        table = active_session.table(contract["source_table"])
        names = _normalized_columns(table.columns)
        if not {"CONTENT_ID", "CURATED_JSON"}.issubset(names):
            raise ValueError("Configured component lookup columns are missing")
        components[kind] = table.select(
            col(names["CONTENT_ID"]).alias("CONTENT_ID"),
            col(names["CURATED_JSON"]).alias("CURATED_JSON")
        ).cache_result()
    return {"archer_values": archer,
            "fips_values": {key: value for key, value in archer.items()
                            if value.lower() in {"low", "moderate", "high"}},
            "component_sources": components,
            "component_contract": profile.get("LOOKUP_CONTRACTS", {})}


# Each source is selected once for this workflow; model routes reuse that
# source-local snapshot. Sources are never unioned or deduplicated together.
SOURCE_INPUTS = {}
MAPPING_INPUTS = {}
MAPPING_FRAMES = {}
source_selection_reports = {}
for source_profile in SOURCE_PROFILES:
    source_key = source_profile["SOURCE_KEY"]
    if source_key in SOURCE_INPUTS:
        raise ValueError("Duplicate configured source key")
    frame, selection, snapshot = load_source_input(session, source_profile)
    artifact = load_mapping_rows(source_profile)
    SOURCE_INPUTS[source_key] = {
        "source_df": frame,
        "snapshot": snapshot,
        "lookups": load_source_lookups(session, source_profile, MODEL_CONTRACTS, CONFIG),
    }
    MAPPING_FRAMES[source_key] = artifact
    MAPPING_INPUTS[source_key] = artifact.to_dict(orient="records")
    source_selection_reports[source_key] = selection
element_registry_df = session.table(CONFIG["ELEMENT_REGISTRY_TABLE"])
REGISTRY_INPUT_ROWS = [row.as_dict(recursive=True) for row in element_registry_df.collect()]

# Compatibility aliases for historical read-only diagnostics. Cell 7 does not
# use these aliases to choose a model or cross source boundaries.
_default_source_key = SOURCE_PROFILES[0]["SOURCE_KEY"]
source_df = SOURCE_INPUTS[_default_source_key]["source_df"]
mapping_artifact_pdf = MAPPING_FRAMES[_default_source_key]
mapping_df = session.create_dataframe(mapping_artifact_pdf)
ARCHER_VALUE_LOOKUP = SOURCE_INPUTS[_default_source_key]["lookups"]["archer_values"]
FIPS_199_VALUE_LOOKUP = SOURCE_INPUTS[_default_source_key]["lookups"]["fips_values"]
COMPONENT_HYDRATION_SOURCE_DFS = SOURCE_INPUTS[_default_source_key]["lookups"]["component_sources"]
COMPONENT_HYDRATION_SOURCE_CONTRACT = SOURCE_PROFILES[0].get("LOOKUP_CONTRACTS", {})
selected_source_count = source_selection_reports[_default_source_key]["SELECTED_ROWS"]
source_row_count = source_selection_reports[_default_source_key]["RAW_ROWS"]
print("Source selection reports:", source_selection_reports)
