# Read-only SSP component source-routing audit
#
# Run once after the accepted component lookup discovery, in the same
# Snowflake notebook session as Cells 1 through 7. The canonical Excel mapping
# rows define the only component-reference scope. Component and SSP identifiers
# remain inside Snowflake; this cell collects and prints aggregate counts plus
# Excel mapping and candidate table/field names only. It performs no DDL or
# DML and does not approve or configure a lookup source or transformation.

import re


ROUTING_COMPONENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
ROUTING_COMPONENT_SOURCE_TYPES = {
    "SUBSYSTEMS": "system",
    "SOFTWARE": "software",
    "HARDWARE": "hardware",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
    "SAP_INTAKE_FORM_INTERCONNECTIONS": "interconnection",
}

# These are the only hydration-bearing candidates proved by the accepted
# aggregate lookup discovery. The three generic identity-only objects are not
# rescanned here because they exposed no recognized title, description, or
# status field. Names do not imply approval: this audit still reports evidence
# and blockers only.
ROUTING_EVIDENCE_SOURCES = {
    "ARCHER_CONTENT_INTERCONNECTIONS_RAW": {
        "field_candidates": {
            "title": ("INTERCONNECTION_NAME", "THIRD_PARTY_NAME"),
            "description": ("DESCRIPTION", "THIRD_PARTY_DESCRIPTION"),
            "status": (),
        },
    },
    "ARCHER_CONTENT_SOFTWARE_RAW": {
        "field_candidates": {
            "title": ("SOFTWARE_NAME", "BUSINESS_NAME"),
            "description": ("DESCRIPTION",),
            "status": (
                "INSTALL_STATUS",
                "OPERATIONAL_STATUS",
                "RECORD_STATUS",
                "SERVICENOW_LIFE_CYCLE_STAGE_STATUS",
            ),
        },
    },
}

ROUTING_ACCEPTED_BASELINE = {
    "reference_occurrences": 4804,
    "source_record_component_pairs": 4792,
    "graph_component_nodes": 4792,
    "distinct_component_ids": 1436,
    "field_occurrences": {
        "SUBSYSTEMS": 0,
        "SOFTWARE": 7,
        "HARDWARE": 1,
        "INTERCONNECTIONS": 4444,
        "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": 352,
        "SAP_INTAKE_FORM_INTERCONNECTIONS": 0,
    },
}

ROUTING_SCALAR_VARIANT_TYPES = (
    "VARCHAR",
    "INTEGER",
    "DECIMAL",
    "NUMBER",
    "FIXED",
    "REAL",
    "DOUBLE",
)


def _routing_compact_name(value):
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").strip().upper())


def _routing_safe_name(value):
    return re.sub(
        r"[^A-Za-z0-9_$.-]+",
        "_",
        str(value or "").strip(),
    )[:256]


def _routing_quote_identifier(value):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RuntimeError("Routing metadata contains an invalid identifier")
    return '"' + value.replace('"', '""') + '"'


def _routing_split_qualified_name(value):
    parts = [part.strip().strip('"') for part in str(value or "").split(".")]
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            "Configured RAW_TABLE must be a three-part Snowflake name"
        )
    return tuple(parts)


def _routing_row_value(row, name):
    try:
        return row[name]
    except (KeyError, TypeError, IndexError):
        pass
    values = row.as_dict(recursive=True) if hasattr(row, "as_dict") else {}
    expected = _routing_compact_name(name)
    for key, value in values.items():
        if _routing_compact_name(key) == expected:
            return value
    return None


def _routing_int(row, name):
    value = _routing_row_value(row, name)
    return int(value) if value is not None else 0


def _routing_validate_runtime_state(config, run_result):
    if str(config.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
        raise RuntimeError("Component routing audit requires the SSP model")
    if config.get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Set EXECUTE_WRITES = False before component routing audit"
        )
    if not isinstance(run_result, dict):
        raise RuntimeError("Cell 7 did not return the expected run result")
    if not run_result.get("validation_passed", False):
        raise RuntimeError("Cell 7 graph validation must pass first")
    if not run_result.get("pre_write_validation_passed", False):
        raise RuntimeError("Cell 7 pre-write validation must pass first")
    if run_result.get("writes_executed", True):
        raise RuntimeError("Component routing audit requires a read-only run")


def _routing_mapping_contract(mapping_rows, type_resolver):
    scoped_rows = [
        row
        for row in mapping_rows
        if str(row.get("OWNER_ELEMENT_PATH") or "").strip()
        == ROUTING_COMPONENT_PATH
    ]
    if len(scoped_rows) != len(ROUTING_COMPONENT_SOURCE_TYPES):
        raise RuntimeError(
            "Canonical Excel component scope does not contain exactly the "
            "six approved mapping rows"
        )

    rows_by_field = {}
    for row in scoped_rows:
        source_field = str(row.get("SOURCE_FIELD_NAME") or "").strip()
        if source_field not in ROUTING_COMPONENT_SOURCE_TYPES:
            raise RuntimeError(
                "Canonical Excel component scope contains an unexpected "
                "source field"
            )
        rows_by_field.setdefault(source_field, []).append(row)

    if set(rows_by_field) != set(ROUTING_COMPONENT_SOURCE_TYPES):
        raise RuntimeError(
            "Canonical Excel component source-field set is incomplete"
        )

    contract = []
    for source_field, expected_type in ROUTING_COMPONENT_SOURCE_TYPES.items():
        rows = rows_by_field[source_field]
        if len(rows) != 1:
            raise RuntimeError(
                "Canonical Excel component source field is duplicated"
            )
        row = rows[0]
        if str(row.get("MAPPING_TYPE") or "").strip().upper() != "REFERENCE":
            raise RuntimeError(
                "Canonical Excel component mapping is not Reference"
            )
        declared_type = str(type_resolver(row) or "").strip().lower()
        if declared_type != expected_type:
            raise RuntimeError(
                "Canonical Excel component mapping type signal conflicts "
                "with the governed source field"
            )
        contract.append(
            {
                "source_field": source_field,
                "component_type": declared_type,
            }
        )
    return contract


def _routing_source_metadata(column_rows):
    metadata = {}
    for row in column_rows:
        table_name = _routing_row_value(row, "TABLE_NAME")
        column_name = _routing_row_value(row, "COLUMN_NAME")
        if table_name is None or column_name is None:
            continue
        table_name = str(table_name)
        if table_name not in ROUTING_EVIDENCE_SOURCES:
            continue
        metadata.setdefault(table_name, []).append(
            {
                "name": str(column_name),
                "data_type": str(
                    _routing_row_value(row, "DATA_TYPE") or ""
                ).upper(),
            }
        )

    contracts = {}
    failures = []
    for table_name in ROUTING_EVIDENCE_SOURCES:
        columns = metadata.get(table_name, [])
        content_id_columns = [
            item
            for item in columns
            if _routing_compact_name(item["name"]) == "CONTENTID"
        ]
        json_columns = [
            item
            for item in columns
            if _routing_compact_name(item["name"]) == "CURATEDJSON"
        ]
        if len(content_id_columns) != 1 or len(json_columns) != 1:
            failures.append(
                _routing_safe_name(table_name) + " | SOURCE_METADATA"
            )
            continue
        contracts[table_name] = {
            "content_id_column": content_id_columns[0],
            "json_column": json_columns[0],
        }
    return contracts, failures


def run_component_source_routing_audit():
    required_state = {
        "session": globals().get("session"),
        "CONFIG": globals().get("CONFIG"),
        "source_df": globals().get("source_df"),
        "final_nodes_df": globals().get("final_nodes_df"),
        "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
        "run_result": globals().get("run_result"),
        "_component_mapping_type": globals().get(
            "_component_mapping_type"
        ),
    }
    missing_state = [
        name for name, value in required_state.items() if value is None
    ]
    if missing_state:
        raise RuntimeError(
            "Run Mapper Cells 1 through 7 first. Missing notebook state: "
            + ", ".join(missing_state)
        )

    session = required_state["session"]
    config = required_state["CONFIG"]
    source_df = required_state["source_df"]
    final_nodes_df = required_state["final_nodes_df"]
    mapping_rows = required_state["CANONICAL_MAPPING_ROWS"]
    run_result = required_state["run_result"]
    type_resolver = required_state["_component_mapping_type"]

    _routing_validate_runtime_state(config, run_result)
    mapping_contract = _routing_mapping_contract(
        mapping_rows,
        type_resolver,
    )

    from snowflake.snowpark.functions import (
        col,
        count as sf_count,
        count_distinct,
        length,
        lit,
        lower,
        parse_json,
        trim,
        typeof,
        upper,
        when,
    )

    def routing_col(name):
        return col(_routing_quote_identifier(name))

    def routing_nonblank(column):
        return (
            column.is_not_null()
            & (length(trim(column.cast("string"))) > lit(0))
        )

    source_columns = {
        str(name).strip().upper(): name for name in source_df.columns
    }
    required_source_columns = {"SOURCE_RECORD_ID", "CURATED_JSON"}
    missing_source_columns = sorted(
        required_source_columns - set(source_columns)
    )
    if missing_source_columns:
        raise RuntimeError(
            "Cell 2 source output is missing required routing columns"
        )

    node_columns = {
        str(name).strip().upper(): name for name in final_nodes_df.columns
    }
    required_node_columns = {
        "ELEMENT_PATH",
        "INSTANCE_KEY",
        "METADATA_JSON",
        "SOURCE_RECORD_ID",
    }
    missing_node_columns = sorted(
        required_node_columns - set(node_columns)
    )
    if missing_node_columns:
        raise RuntimeError(
            "Cell 7 node output is missing required routing columns"
        )

    source_json = parse_json(
        routing_col(source_columns["CURATED_JSON"]).cast("string")
    )
    root_dfs = []
    for route in mapping_contract:
        root_dfs.append(
            source_df.select(
                trim(
                    routing_col(
                        source_columns["SOURCE_RECORD_ID"]
                    ).cast("string")
                ).alias("_SOURCE_RECORD_ID"),
                lit(route["source_field"]).alias("_SOURCE_FIELD"),
                lit(route["component_type"]).alias("_COMPONENT_TYPE"),
                source_json.getItem(route["source_field"]).alias(
                    "_REFERENCE_ROOT"
                ),
            )
        )

    reference_roots_df = root_dfs[0]
    for root_df in root_dfs[1:]:
        reference_roots_df = reference_roots_df.union_all(root_df)

    root_type_rows = (
        reference_roots_df.filter(col("_REFERENCE_ROOT").is_not_null())
        .select(
            col("_SOURCE_FIELD"),
            col("_COMPONENT_TYPE"),
            upper(typeof(col("_REFERENCE_ROOT"))).alias("ROOT_TYPE"),
        )
        .group_by(
            col("_SOURCE_FIELD"),
            col("_COMPONENT_TYPE"),
            col("ROOT_TYPE"),
        )
        .agg(sf_count(lit(1)).alias("ROOT_ROWS"))
        .collect()
    )
    unexpected_root_rows = sum(
        _routing_int(row, "ROOT_ROWS")
        for row in root_type_rows
        if str(_routing_row_value(row, "ROOT_TYPE") or "").upper()
        not in {"ARRAY", "NULL_VALUE"}
    )
    json_null_root_rows = sum(
        _routing_int(row, "ROOT_ROWS")
        for row in root_type_rows
        if str(_routing_row_value(row, "ROOT_TYPE") or "").upper()
        == "NULL_VALUE"
    )

    array_roots_df = reference_roots_df.filter(
        upper(typeof(col("_REFERENCE_ROOT"))) == lit("ARRAY")
    )
    reference_members_df = array_roots_df.join_table_function(
        "flatten",
        col("_REFERENCE_ROOT"),
    )
    member_value = col("VALUE")
    member_type = upper(typeof(member_value))
    object_content_id = member_value.getItem("ContentId")
    object_id_type = upper(typeof(object_content_id))
    scalar_types = list(ROUTING_SCALAR_VARIANT_TYPES)
    component_id_value = (
        when(
            (member_type == lit("OBJECT"))
            & object_id_type.isin(*scalar_types),
            object_content_id,
        )
        .when(member_type.isin(*scalar_types), member_value)
        .otherwise(lit(None))
    )
    route_members_df = reference_members_df.select(
        col("_SOURCE_RECORD_ID"),
        col("_SOURCE_FIELD"),
        col("_COMPONENT_TYPE"),
        trim(component_id_value.cast("string")).alias("_COMPONENT_ID"),
    )

    route_stat_rows = (
        route_members_df.group_by(
            col("_SOURCE_FIELD"),
            col("_COMPONENT_TYPE"),
        )
        .agg(
            sf_count(lit(1)).alias("MEMBER_ROWS"),
            sf_count(
                when(
                    routing_nonblank(col("_COMPONENT_ID")),
                    lit(1),
                )
            ).alias("REFERENCE_OCCURRENCES"),
            count_distinct(
                when(
                    routing_nonblank(col("_COMPONENT_ID")),
                    col("_COMPONENT_ID"),
                )
            ).alias("DISTINCT_COMPONENT_IDS"),
        )
        .collect()
    )
    route_stats = {
        str(_routing_row_value(row, "_SOURCE_FIELD")): {
            "component_type": str(
                _routing_row_value(row, "_COMPONENT_TYPE") or ""
            ),
            "member_rows": _routing_int(row, "MEMBER_ROWS"),
            "reference_occurrences": _routing_int(
                row,
                "REFERENCE_OCCURRENCES",
            ),
            "distinct_component_ids": _routing_int(
                row,
                "DISTINCT_COMPONENT_IDS",
            ),
        }
        for row in route_stat_rows
    }

    component_routes_df = route_members_df.filter(
        routing_nonblank(col("_COMPONENT_ID"))
    )
    reference_occurrences = component_routes_df.count()
    invalid_reference_members = sum(
        stats["member_rows"] - stats["reference_occurrences"]
        for stats in route_stats.values()
    )
    source_record_component_pairs_df = component_routes_df.select(
        col("_SOURCE_RECORD_ID"),
        col("_COMPONENT_ID"),
        col("_COMPONENT_TYPE"),
    ).distinct()
    source_record_component_pairs = source_record_component_pairs_df.count()
    distinct_component_ids = component_routes_df.select(
        col("_COMPONENT_ID")
    ).distinct().count()
    cross_type_component_ids = (
        component_routes_df.select(
            col("_COMPONENT_ID"),
            col("_COMPONENT_TYPE"),
        )
        .distinct()
        .group_by(col("_COMPONENT_ID"))
        .agg(
            count_distinct(col("_COMPONENT_TYPE")).alias("TYPE_COUNT")
        )
        .filter(col("TYPE_COUNT") > lit(1))
        .count()
    )

    graph_payload = parse_json(
        routing_col(node_columns["METADATA_JSON"]).cast("string")
    )
    graph_component_df = (
        final_nodes_df.filter(
            routing_col(node_columns["ELEMENT_PATH"])
            == lit(ROUTING_COMPONENT_PATH)
        )
        .select(
            trim(
                routing_col(node_columns["SOURCE_RECORD_ID"]).cast("string")
            ).alias("_SOURCE_RECORD_ID"),
            trim(
                routing_col(node_columns["INSTANCE_KEY"]).cast("string")
            ).alias("_COMPONENT_ID"),
            lower(
                trim(graph_payload.getItem("type").cast("string"))
            ).alias("_COMPONENT_TYPE"),
        )
    )
    graph_component_nodes = graph_component_df.count()
    valid_component_types = sorted(set(ROUTING_COMPONENT_SOURCE_TYPES.values()))
    invalid_graph_nodes = graph_component_df.filter(
        ~routing_nonblank(col("_SOURCE_RECORD_ID"))
        | ~routing_nonblank(col("_COMPONENT_ID"))
        | ~col("_COMPONENT_TYPE").isin(*valid_component_types)
    ).count()
    graph_pairs_df = graph_component_df.distinct()

    source_pairs = source_record_component_pairs_df.select(
        col("_SOURCE_RECORD_ID").alias("_SOURCE_PAIR_RECORD"),
        col("_COMPONENT_ID").alias("_SOURCE_PAIR_ID"),
        col("_COMPONENT_TYPE").alias("_SOURCE_PAIR_TYPE"),
    )
    graph_pairs = graph_pairs_df.select(
        col("_SOURCE_RECORD_ID").alias("_GRAPH_PAIR_RECORD"),
        col("_COMPONENT_ID").alias("_GRAPH_PAIR_ID"),
        col("_COMPONENT_TYPE").alias("_GRAPH_PAIR_TYPE"),
    )
    source_pairs_without_graph = (
        source_pairs.join(
            graph_pairs,
            (source_pairs["_SOURCE_PAIR_RECORD"] == graph_pairs["_GRAPH_PAIR_RECORD"])
            & (source_pairs["_SOURCE_PAIR_ID"] == graph_pairs["_GRAPH_PAIR_ID"])
            & (source_pairs["_SOURCE_PAIR_TYPE"] == graph_pairs["_GRAPH_PAIR_TYPE"]),
            "left",
        )
        .filter(col("_GRAPH_PAIR_ID").is_null())
        .count()
    )
    graph_pairs_without_source = (
        graph_pairs.join(
            source_pairs,
            (graph_pairs["_GRAPH_PAIR_RECORD"] == source_pairs["_SOURCE_PAIR_RECORD"])
            & (graph_pairs["_GRAPH_PAIR_ID"] == source_pairs["_SOURCE_PAIR_ID"])
            & (graph_pairs["_GRAPH_PAIR_TYPE"] == source_pairs["_SOURCE_PAIR_TYPE"]),
            "left",
        )
        .filter(col("_SOURCE_PAIR_ID").is_null())
        .count()
    )

    database, schema, _ = _routing_split_qualified_name(
        config.get("RAW_TABLE")
    )
    evidence_table_names = list(ROUTING_EVIDENCE_SOURCES)
    metadata_query_failed = False
    try:
        column_metadata_rows = (
            session.table([database, "INFORMATION_SCHEMA", "COLUMNS"])
            .filter(upper(col("TABLE_SCHEMA")) == lit(schema.upper()))
            .filter(upper(col("TABLE_NAME")).isin(*evidence_table_names))
            .select("TABLE_NAME", "COLUMN_NAME", "DATA_TYPE")
            .collect()
        )
    except Exception:
        column_metadata_rows = []
        metadata_query_failed = True

    source_contracts, scan_failures = _routing_source_metadata(
        column_metadata_rows
    )
    if metadata_query_failed:
        scan_failures = ["CATALOG | SOURCE_METADATA_QUERY"] + scan_failures
    source_profiles = {}
    for table_name, source_contract in source_contracts.items():
        display_name = ".".join(
            _routing_safe_name(part)
            for part in (database, schema, table_name)
        )
        try:
            candidate_table_df = session.table(
                [database, schema, table_name]
            )
            lookup_id = trim(
                routing_col(
                    source_contract["content_id_column"]["name"]
                ).cast("string")
            )
            lookup_json = parse_json(
                routing_col(
                    source_contract["json_column"]["name"]
                ).cast("string")
            )
            candidate_rows_df = candidate_table_df.select(
                lookup_id.alias("_LOOKUP_ID"),
                lookup_json.alias("_LOOKUP_JSON"),
            )
            key_summary = candidate_rows_df.agg(
                sf_count(lit(1)).alias("TOTAL_ROWS"),
                sf_count(
                    when(routing_nonblank(col("_LOOKUP_ID")), lit(1))
                ).alias("NONBLANK_KEY_ROWS"),
                count_distinct(
                    when(
                        routing_nonblank(col("_LOOKUP_ID")),
                        col("_LOOKUP_ID"),
                    )
                ).alias("DISTINCT_KEYS"),
            ).collect()[0]
            source_profiles[table_name] = {
                "display_name": display_name,
                "rows_df": candidate_rows_df.filter(
                    routing_nonblank(col("_LOOKUP_ID"))
                ),
                "total_rows": _routing_int(key_summary, "TOTAL_ROWS"),
                "nonblank_key_rows": _routing_int(
                    key_summary,
                    "NONBLANK_KEY_ROWS",
                ),
                "distinct_keys": _routing_int(
                    key_summary,
                    "DISTINCT_KEYS",
                ),
            }
        except Exception:
            scan_failures.append(display_name + " | KEY_PROFILE")

    routes_by_field_df = component_routes_df.select(
        col("_SOURCE_FIELD"),
        col("_COMPONENT_TYPE"),
        col("_COMPONENT_ID"),
    ).distinct()
    type_id_rows = (
        routes_by_field_df.group_by(col("_COMPONENT_TYPE"))
        .agg(
            count_distinct(col("_COMPONENT_ID")).alias(
                "DISTINCT_COMPONENT_IDS"
            )
        )
        .collect()
    )
    type_id_counts = {
        str(_routing_row_value(row, "_COMPONENT_TYPE") or ""):
        _routing_int(row, "DISTINCT_COMPONENT_IDS")
        for row in type_id_rows
    }
    match_matrix = {}
    field_evidence = {}
    for table_name, profile in source_profiles.items():
        try:
            matched_routes_df = routes_by_field_df.join(
                profile["rows_df"],
                routes_by_field_df["_COMPONENT_ID"]
                == profile["rows_df"]["_LOOKUP_ID"],
                "inner",
            )
            matrix_rows = (
                matched_routes_df.group_by(
                    col("_SOURCE_FIELD"),
                    col("_COMPONENT_TYPE"),
                )
                .agg(
                    count_distinct(col("_COMPONENT_ID")).alias(
                        "MATCHED_IDS"
                    ),
                    sf_count(lit(1)).alias("MATCHED_ROWS"),
                )
                .collect()
            )
            for row in matrix_rows:
                source_field = str(
                    _routing_row_value(row, "_SOURCE_FIELD") or ""
                )
                match_matrix[(source_field, table_name)] = {
                    "matched_ids": _routing_int(row, "MATCHED_IDS"),
                    "matched_rows": _routing_int(row, "MATCHED_ROWS"),
                }

            for component_type in sorted(type_id_counts):
                type_ids_df = routes_by_field_df.filter(
                    col("_COMPONENT_TYPE") == lit(component_type)
                ).select(col("_COMPONENT_ID")).distinct()
                matched_type_df = type_ids_df.join(
                    profile["rows_df"],
                    type_ids_df["_COMPONENT_ID"]
                    == profile["rows_df"]["_LOOKUP_ID"],
                    "inner",
                )
                expressions = [
                    count_distinct(col("_COMPONENT_ID")).alias(
                        "MATCHED_IDS"
                    )
                ]
                field_aliases = []
                category_aliases = []
                for category, field_names in ROUTING_EVIDENCE_SOURCES[
                    table_name
                ]["field_candidates"].items():
                    populated_conditions = []
                    for index, field_name in enumerate(field_names):
                        alias = "{}_{}".format(category.upper(), index)
                        field_aliases.append((category, field_name, alias))
                        populated_condition = routing_nonblank(
                            col("_LOOKUP_JSON").getItem(field_name)
                        )
                        populated_conditions.append(populated_condition)
                        expressions.append(
                            count_distinct(
                                when(
                                    populated_condition,
                                    col("_COMPONENT_ID"),
                                )
                            ).alias(alias)
                        )
                    if populated_conditions:
                        combined_condition = populated_conditions[0]
                        for populated_condition in populated_conditions[1:]:
                            combined_condition = (
                                combined_condition | populated_condition
                            )
                        category_alias = "{}_ANY".format(category.upper())
                        category_aliases.append((category, category_alias))
                        expressions.append(
                            count_distinct(
                                when(
                                    combined_condition,
                                    col("_COMPONENT_ID"),
                                )
                            ).alias(category_alias)
                        )
                evidence_row = matched_type_df.agg(*expressions).collect()[0]
                evidence_items = []
                for category, field_name, alias in field_aliases:
                    evidence_items.append(
                        {
                            "category": category,
                            "field_name": field_name,
                            "populated_ids": _routing_int(
                                evidence_row,
                                alias,
                            ),
                        }
                    )
                field_evidence[(component_type, table_name)] = {
                    "matched_ids": _routing_int(
                        evidence_row,
                        "MATCHED_IDS",
                    ),
                    "items": evidence_items,
                    "category_populated_ids": {
                        category: _routing_int(evidence_row, alias)
                        for category, alias in category_aliases
                    },
                }
        except Exception:
            scan_failures.append(
                profile["display_name"] + " | ROUTE_PROFILE"
            )

    baseline_drift = []
    if reference_occurrences != ROUTING_ACCEPTED_BASELINE[
        "reference_occurrences"
    ]:
        baseline_drift.append("REFERENCE_OCCURRENCES")
    if source_record_component_pairs != ROUTING_ACCEPTED_BASELINE[
        "source_record_component_pairs"
    ]:
        baseline_drift.append("SOURCE_RECORD_COMPONENT_PAIRS")
    if graph_component_nodes != ROUTING_ACCEPTED_BASELINE[
        "graph_component_nodes"
    ]:
        baseline_drift.append("GRAPH_COMPONENT_NODES")
    if distinct_component_ids != ROUTING_ACCEPTED_BASELINE[
        "distinct_component_ids"
    ]:
        baseline_drift.append("DISTINCT_COMPONENT_IDS")
    for source_field, expected_count in ROUTING_ACCEPTED_BASELINE[
        "field_occurrences"
    ].items():
        actual_count = route_stats.get(source_field, {}).get(
            "reference_occurrences",
            0,
        )
        if actual_count != expected_count:
            baseline_drift.append("FIELD_" + source_field)

    print("=== SSP COMPONENT SOURCE ROUTING AUDIT ===")
    print(
        "Safety: aggregate-only; no component IDs, source-record IDs, "
        "payloads, or source values printed"
    )
    print("Writes executed: False")
    print("Canonical Excel component mapping rows:", len(mapping_contract))
    print("Reference occurrences:", reference_occurrences)
    print(
        "Distinct source-record/component/type pairs:",
        source_record_component_pairs,
    )
    print("Graph component nodes:", graph_component_nodes)
    print("Distinct component IDs:", distinct_component_ids)
    print("Invalid reference members:", invalid_reference_members)
    print("JSON-null reference roots:", json_null_root_rows)
    print("Unexpected non-array reference roots:", unexpected_root_rows)
    print("Cross-type component IDs:", cross_type_component_ids)
    print("Source pairs missing from graph:", source_pairs_without_graph)
    print("Graph pairs missing from source:", graph_pairs_without_source)
    print("Invalid graph component nodes:", invalid_graph_nodes)
    print("Lookup source profiling failures:", len(scan_failures))
    print("Accepted-baseline drift checks:", len(baseline_drift))

    print("\n=== EXCEL SOURCE-FIELD ROUTES ===")
    for route in mapping_contract:
        source_field = route["source_field"]
        stats = route_stats.get(
            source_field,
            {
                "member_rows": 0,
                "reference_occurrences": 0,
                "distinct_component_ids": 0,
            },
        )
        print("SOURCE FIELD:", source_field)
        print("  Declared component type:", route["component_type"])
        print("  Flattened members:", stats["member_rows"])
        print("  Valid reference occurrences:", stats["reference_occurrences"])
        print("  Distinct component IDs:", stats["distinct_component_ids"])
        if stats["reference_occurrences"] == 0:
            print("  Route result: NO_RUNTIME_REFERENCE_EVIDENCE")
            continue

        for table_name in ROUTING_EVIDENCE_SOURCES:
            matrix = match_matrix.get(
                (source_field, table_name),
                {"matched_ids": 0, "matched_rows": 0},
            )
            print("  CANDIDATE:", table_name)
            print("    Matched distinct IDs:", matrix["matched_ids"])
            print("    Matched lookup rows:", matrix["matched_rows"])

        hydration_sources = [
            table_name
            for table_name in ROUTING_EVIDENCE_SOURCES
            if match_matrix.get(
                (source_field, table_name),
                {"matched_ids": 0},
            )["matched_ids"]
        ]
        full_coverage_sources = [
            table_name
            for table_name in hydration_sources
            if match_matrix[(source_field, table_name)]["matched_ids"]
            == stats["distinct_component_ids"]
        ]
        if not hydration_sources:
            route_result = "NO_HYDRATION_BEARING_SOURCE"
        elif len(hydration_sources) > 1:
            route_result = "MULTIPLE_HYDRATION_CANDIDATES"
        elif not full_coverage_sources:
            route_result = "PARTIAL_SOURCE_COVERAGE"
        else:
            route_result = "OWNER_FIELD_APPROVAL_REQUIRED"
        print("  Route result:", route_result)

    print("\n=== HYDRATION FIELD EVIDENCE ===")
    for (component_type, table_name), evidence in sorted(
        field_evidence.items()
    ):
        profile = source_profiles.get(table_name, {})
        duplicate_key_rows = profile.get("nonblank_key_rows", 0) - profile.get(
            "distinct_keys",
            0,
        )
        print("COMPONENT TYPE:", component_type)
        print("  Candidate object:", table_name)
        print("  Candidate duplicate key rows:", duplicate_key_rows)
        print("  Matched distinct IDs:", evidence["matched_ids"])
        for item in evidence["items"]:
            print(
                "  FIELD: {} | {} | populated matched IDs={}".format(
                    item["category"],
                    item["field_name"],
                    item["populated_ids"],
                )
            )
        for category in ("title", "description", "status"):
            print(
                "  CATEGORY COVERAGE: {} | any candidate populated IDs={}".format(
                    category,
                    evidence["category_populated_ids"].get(category, 0),
                )
            )
        print("  Field or transformation approved: False")

    if scan_failures:
        print("\nFailed source objects/stages (safe names only):")
        for failure in scan_failures:
            print("  ", failure)
    if baseline_drift:
        print("\nBaseline drift checks:")
        for drift in baseline_drift:
            print("  ", drift)

    blockers = []
    if scan_failures:
        blockers.append("INCOMPLETE_SOURCE_SCAN")
    if baseline_drift:
        blockers.append("LOOKUP_BASELINE_DRIFT")
    if unexpected_root_rows or invalid_reference_members:
        blockers.append("REFERENCE_SHAPE_GAP")
    if cross_type_component_ids:
        blockers.append("CROSS_TYPE_IDENTITY_CONFLICT")
    if source_pairs_without_graph or graph_pairs_without_source:
        blockers.append("SOURCE_GRAPH_RECONCILIATION_GAP")
    if invalid_graph_nodes:
        blockers.append("INVALID_GRAPH_COMPONENT_NODE")
    for table_name, profile in source_profiles.items():
        if profile["nonblank_key_rows"] != profile["distinct_keys"]:
            blockers.append(
                "DUPLICATE_{}_LOOKUP_KEYS".format(
                    _routing_compact_name(table_name)
                )
            )

    active_types = set(type_id_counts)
    for component_type in active_types:
        matching_sources = [
            table_name
            for table_name in ROUTING_EVIDENCE_SOURCES
            if field_evidence.get((component_type, table_name), {}).get(
                "matched_ids",
                0,
            )
        ]
        if not matching_sources:
            blockers.append("MISSING_{}_SOURCE".format(component_type.upper()))
            continue
        if len(matching_sources) > 1:
            blockers.append(
                "AMBIGUOUS_{}_SOURCE_ROUTE".format(
                    component_type.upper()
                )
            )
        best_source_coverage = max(
            field_evidence[(component_type, table_name)]["matched_ids"]
            for table_name in matching_sources
        )
        if best_source_coverage < type_id_counts[component_type]:
            blockers.append(
                "PARTIAL_{}_SOURCE_COVERAGE".format(
                    component_type.upper()
                )
            )
        for table_name in matching_sources:
            evidence = field_evidence[(component_type, table_name)]
            categories = {
                category: [
                    item
                    for item in evidence["items"]
                    if item["category"] == category
                ]
                for category in ("title", "description", "status")
            }
            for category, items in categories.items():
                if not items:
                    blockers.append(
                        "MISSING_{}_{}_FIELD_CATEGORY".format(
                            component_type.upper(),
                            category.upper(),
                        )
                    )
                    continue
                if len(items) > 1:
                    blockers.append(
                        "AMBIGUOUS_{}_{}_FIELD_CHOICE".format(
                            component_type.upper(),
                            category.upper(),
                        )
                    )
                if evidence["category_populated_ids"].get(category, 0) < (
                    evidence["matched_ids"]
                ):
                    blockers.append(
                        "INCOMPLETE_{}_{}_COVERAGE".format(
                            component_type.upper(),
                            category.upper(),
                        )
                    )

    blockers = sorted(set(blockers))
    print("\n=== ROUTING AUDIT CONCLUSION ===")
    if blockers:
        print(
            "RESULT: COMPONENT ROUTING OR FIELD-APPROVAL GAPS REMAIN; "
            "NO SOURCE OR TRANSFORMATION WAS APPROVED"
        )
        print("Blocking reason count:", len(blockers))
        for blocker in blockers:
            print("  ", blocker)
    else:
        print(
            "RESULT: ROUTING EVIDENCE COMPLETE; OWNER SOURCE, FIELD, AND "
            "STATUS-TRANSFORMATION APPROVAL STILL REQUIRED"
        )
    print(
        "No lookup source, field, precedence rule, or status transformation "
        "was configured by this audit."
    )
    print("An incomplete audit cannot approve a component lookup source.")
    print("No database objects or rows were changed.")


if not globals().get("_ROUTING_AUDIT_SKIP_EXECUTION", False):
    run_component_source_routing_audit()

