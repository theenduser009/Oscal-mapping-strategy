# %% Cell 2 - Read source and metadata once

def _normalized_columns(columns):
    result = {}
    for name in columns:
        # Snowpark includes quotes around case-sensitive/otherwise quoted names.
        key = name[1:-1].replace('""', '"') if name.startswith('"') and name.endswith('"') else name.strip().upper()
        if key in result:
            raise ValueError("Duplicate normalized source column")
        result[key] = name
    return result


def _input_column(columns, configured):
    if configured.startswith('"') and configured.endswith('"'):
        return columns.get(configured[1:-1].replace('""', '"'))
    return columns.get(configured, columns.get(configured.upper()))


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
    id_name = _input_column(columns, profile.get("CONTENT_ID_COLUMN", "CONTENT_ID"))
    json_name = _input_column(columns, profile.get("CURATED_JSON_COLUMN", "CURATED_JSON"))
    if id_name is None or json_name is None:
        raise ValueError("Source requires its configured identity and curated JSON columns")
    selected = [col(id_name).cast("string").alias("SOURCE_RECORD_ID"),
                col(json_name).alias("CURATED_JSON")]
    order_columns = []
    for candidate in profile.get("SOURCE_ORDER_CANDIDATES", ()):
        name = _input_column(columns, candidate)
        if name is not None:
            alias = "_SOURCE_ORDER_" + str(len(order_columns))
            selected.append(col(name).alias(alias))
            order_columns.append(alias)
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
        latest = candidates.with_column(
            "_SOURCE_RANK", dense_rank().over(
                Window.partition_by("SOURCE_RECORD_ID").order_by(*order)
            )
        ).filter(col("_SOURCE_RANK") == lit(1))
        # Equal latest payloads are interchangeable; conflicting ones need a
        # source tie-break column. JSON text/object key order is not an identity.
        result = latest.select("SOURCE_RECORD_ID", "CURATED_JSON").distinct()
        if result.count() != distinct:
            raise ValueError("Conflicting source payloads share the latest approved technical ordering")
    else:
        result = candidates.select("SOURCE_RECORD_ID", "CURATED_JSON")
    # The frozen snapshot yields one selected row per distinct source identity.
    return result, {"RAW_ROWS": count, "SELECTED_ROWS": distinct,
                    "DUPLICATE_SOURCE_ROWS_RESOLVED": count - distinct}, candidates


def load_mapping_rows(profile):
    with open(profile["MAPPING_FILE"], encoding=profile.get("MAPPING_ENCODING", "utf-8-sig"), newline="") as handle:
        reader = csv.reader(handle, strict=True)
        header = next((row for row in reader if row and any(v.strip() for v in row)), None)
        if header is None:
            raise ValueError("Mapping CSV header is missing")
        header = [name.strip().upper() for name in header]
        if not all(header) or len(header) != len(set(header)):
            raise ValueError("Mapping CSV columns must be nonblank and unique")
        binding = profile.get("MAPPING_SOURCE_COLUMN", "").upper()
        if binding and binding not in header:
            raise ValueError("Mapping source binding column is missing")
        rows = []
        for values in reader:
            if not values or not any(value.strip() for value in values):
                continue
            if len(values) > len(header):
                raise ValueError("Mapping CSV row has more values than header columns")
            row = dict.fromkeys(header)
            row.update((key, value or None) for key, value in zip(header, values))
            if not binding or str(row[binding] or "").strip() == profile.get("MAPPING_SOURCE_VALUE", profile["SOURCE_TABLE_NAME"]):
                rows.append(row)
    return rows


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


SOURCE_INPUTS, MAPPING_INPUTS = {}, {}
for profile in SOURCE_PROFILES:
    key = profile["SOURCE_KEY"]
    if key in SOURCE_INPUTS:
        raise ValueError("Duplicate source binding")
    frame, counts, snapshot = load_source_input(session, profile)
    MAPPING_INPUTS[key] = load_mapping_rows(profile)
    SOURCE_INPUTS[key] = {
        "source_df": frame, "snapshot": snapshot, "selection": counts,
        "lookups": load_source_lookups(session, profile, MODEL_CONTRACTS, CONFIG),
    }
REGISTRY_INPUT_ROWS = [row.as_dict(recursive=True) for row in
                       session.table(CONFIG["ELEMENT_REGISTRY_TABLE"]).collect()]
print("Sources:", {key: value["selection"] for key, value in SOURCE_INPUTS.items()})
