# Read-only SSP referenced-component lookup discovery
#
# Run once after an accepted read-only Cell 7 run in the same session. This
# cell performs metadata reads and aggregate queries only. It prints object and
# field names plus counts, but never prints component IDs, source-record IDs,
# payloads, or source values. It does not approve or configure a lookup source.

from collections import defaultdict
import re


LOOKUP_DISCOVERY_COMPONENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
LOOKUP_DISCOVERY_MAX_CONTENT_ID_OBJECTS = 60
LOOKUP_DISCOVERY_MAX_MATCHED_OBJECTS = 20
LOOKUP_DISCOVERY_MAX_DIRECT_FIELDS_PER_OBJECT = 40
LOOKUP_DISCOVERY_MAX_JSON_KEYS_PER_OBJECT = 2000
LOOKUP_SEMISTRUCTURED_TYPES = {"VARIANT", "OBJECT", "ARRAY"}


def _lookup_quote_identifier(value):
    if not isinstance(value, str) or not value or "\x00" in value:
        raise RuntimeError("Lookup metadata contains an invalid identifier")
    return '"' + value.replace('"', '""') + '"'


def _lookup_compact_name(value):
    return re.sub(r"[^A-Z0-9]+", "", str(value or "").strip().upper())


def _lookup_token_name(value):
    return re.sub(
        r"[^A-Z0-9]+",
        "_",
        str(value or "").strip().upper(),
    ).strip("_")


def _lookup_safe_name(value):
    return re.sub(
        r"[^A-Za-z0-9_$.-]+",
        "_",
        str(value or "").strip(),
    )[:256]


def _lookup_split_qualified_name(value):
    parts = [part.strip().strip('"') for part in str(value or "").split(".")]
    if len(parts) != 3 or any(not part for part in parts):
        raise RuntimeError(
            "Configured RAW_TABLE must be a three-part Snowflake name"
        )
    return tuple(parts)


def _lookup_row_value(row, name):
    try:
        return row[name]
    except (KeyError, TypeError, IndexError):
        pass
    values = row.as_dict(recursive=True) if hasattr(row, "as_dict") else {}
    expected = _lookup_compact_name(name)
    for key, value in values.items():
        if _lookup_compact_name(key) == expected:
            return value
    return None


def _lookup_int(row, name):
    value = _lookup_row_value(row, name)
    return int(value) if value is not None else 0


def _lookup_field_category(name):
    token_name = _lookup_token_name(name)
    technical_markers = (
        "DW_",
        "PIPELINE_",
        "SOURCE_TABLE",
        "TARGET_TABLE",
        "TABLE_NAME",
        "SCHEMA_NAME",
        "FILE_NAME",
        "LOAD_",
        "CREATED_BY",
        "UPDATED_BY",
        "MODIFIED_BY",
    )
    if any(marker in token_name for marker in technical_markers):
        return None

    if (
        token_name
        in {
            "STATUS",
            "STATE",
            "RECORD_STATUS",
            "COMPONENT_STATUS",
            "LIFECYCLE_STATUS",
        }
        or token_name.endswith("_STATUS")
        or token_name.endswith("_STATE")
    ):
        return "status"
    if (
        token_name
        in {
            "DESCRIPTION",
            "DESC",
            "SUMMARY",
            "PURPOSE",
            "COMPONENT_DESCRIPTION",
            "SYSTEM_DESCRIPTION",
        }
        or token_name.endswith("_DESCRIPTION")
        or token_name.endswith("_SUMMARY")
    ):
        return "description"
    if (
        token_name
        in {
            "TITLE",
            "NAME",
            "RECORD_NAME",
            "DISPLAY_NAME",
            "COMPONENT_NAME",
            "SYSTEM_NAME",
            "SOFTWARE_NAME",
            "HARDWARE_NAME",
            "INTERCONNECTION_NAME",
            "APPLICATION_NAME",
            "ASSET_NAME",
        }
        or token_name.endswith("_TITLE")
        or token_name.endswith("_NAME")
    ):
        return "title"
    return None


def _lookup_validate_runtime_state(config, run_result):
    if str(config.get("OSCAL_MODEL", "")).strip().upper() != "SSP":
        raise RuntimeError("Component lookup discovery requires the SSP model")
    if config.get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Set EXECUTE_WRITES = False before component lookup discovery"
        )
    if not isinstance(run_result, dict):
        raise RuntimeError("Cell 7 did not return the expected run result")
    if not run_result.get("validation_passed", False):
        raise RuntimeError("Cell 7 graph validation must pass first")
    if not run_result.get("pre_write_validation_passed", False):
        raise RuntimeError("Cell 7 pre-write validation must pass first")
    if run_result.get("writes_executed", True):
        raise RuntimeError("Component lookup discovery requires a read-only run")


def _lookup_catalog_objects(table_rows, column_rows):
    objects = {}
    for row in table_rows:
        table_name = _lookup_row_value(row, "TABLE_NAME")
        if table_name is None:
            continue
        table_name = str(table_name)
        objects[table_name] = {
            "table_name": table_name,
            "table_type": str(_lookup_row_value(row, "TABLE_TYPE") or ""),
            "metadata_row_count": _lookup_row_value(row, "ROW_COUNT"),
            "columns": [],
        }

    for row in column_rows:
        table_name = _lookup_row_value(row, "TABLE_NAME")
        column_name = _lookup_row_value(row, "COLUMN_NAME")
        if table_name is None or column_name is None:
            continue
        table_name = str(table_name)
        if table_name not in objects:
            continue
        ordinal = _lookup_row_value(row, "ORDINAL_POSITION")
        objects[table_name]["columns"].append(
            {
                "name": str(column_name),
                "data_type": str(
                    _lookup_row_value(row, "DATA_TYPE") or ""
                ).upper(),
                "ordinal_position": int(ordinal) if ordinal is not None else 0,
            }
        )

    for metadata in objects.values():
        metadata["columns"].sort(
            key=lambda item: item["ordinal_position"]
        )
    return objects


def _lookup_is_internal_object(metadata):
    table_name = str(metadata.get("table_name") or "").strip().upper()
    table_type = str(metadata.get("table_type") or "").strip().upper()
    return (
        table_name.startswith("$JS_USR_")
        or table_name.startswith("SNOWPARK_TEMP_")
        or "TEMPORARY" in table_type
    )


def _lookup_content_id_objects(objects):
    candidates = []
    ambiguous = []
    for metadata in objects.values():
        if _lookup_is_internal_object(metadata):
            continue
        key_columns = [
            item
            for item in metadata["columns"]
            if _lookup_compact_name(item["name"]) == "CONTENTID"
        ]
        if len(key_columns) > 1:
            ambiguous.append(metadata["table_name"])
            continue
        if len(key_columns) == 1:
            candidate = dict(metadata)
            candidate["key_column"] = key_columns[0]
            candidates.append(candidate)
    candidates.sort(key=lambda item: item["table_name"])
    return candidates, ambiguous


def _lookup_best_field_coverage(profile, category):
    counts = [
        item["populated_ids"]
        for item in profile["direct_field_evidence"]
        if item["category"] == category
    ]
    counts.extend(
        item["nonblank_ids"]
        for item in profile["json_key_evidence"]
        if item["category"] == category
    )
    return max(counts) if counts else 0


def run_component_lookup_source_discovery():
    required_state = {
        "session": globals().get("session"),
        "CONFIG": globals().get("CONFIG"),
        "final_nodes_df": globals().get("final_nodes_df"),
        "run_result": globals().get("run_result"),
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
    final_nodes_df = required_state["final_nodes_df"]
    run_result = required_state["run_result"]
    _lookup_validate_runtime_state(config, run_result)

    from snowflake.snowpark.functions import (
        col,
        count as sf_count,
        count_distinct,
        length,
        lit,
        parse_json,
        trim,
        upper,
        when,
    )

    def lookup_col(name):
        return col(_lookup_quote_identifier(name))

    def lookup_nonblank(column):
        return (
            column.is_not_null()
            & (length(trim(column.cast("string"))) > lit(0))
        )

    node_columns = {
        str(name).strip().upper(): name for name in final_nodes_df.columns
    }
    required_node_columns = {"ELEMENT_PATH", "INSTANCE_KEY"}
    missing_node_columns = sorted(
        required_node_columns - set(node_columns)
    )
    if missing_node_columns:
        raise RuntimeError(
            "Cell 7 node output is missing required columns: "
            + ", ".join(missing_node_columns)
        )

    component_node_ids_df = (
        final_nodes_df.filter(
            lookup_col(node_columns["ELEMENT_PATH"])
            == lit(LOOKUP_DISCOVERY_COMPONENT_PATH)
        )
        .select(
            trim(
                lookup_col(node_columns["INSTANCE_KEY"]).cast("string")
            ).alias("_COMPONENT_ID")
        )
    )
    component_node_occurrences = component_node_ids_df.count()
    if component_node_occurrences == 0:
        raise RuntimeError(
            "The accepted Cell 7 graph contains no component nodes"
        )
    invalid_component_ids = component_node_ids_df.filter(
        ~lookup_nonblank(col("_COMPONENT_ID"))
    ).count()
    if invalid_component_ids:
        raise RuntimeError(
            "The accepted component graph contains a blank instance identity"
        )
    component_ids_df = component_node_ids_df.distinct()
    distinct_component_ids = component_ids_df.count()

    database, schema, _ = _lookup_split_qualified_name(
        config.get("RAW_TABLE")
    )
    try:
        table_metadata_rows = (
            session.table([database, "INFORMATION_SCHEMA", "TABLES"])
            .filter(upper(col("TABLE_SCHEMA")) == lit(schema.upper()))
            .select("TABLE_NAME", "TABLE_TYPE", "ROW_COUNT")
            .collect()
        )
        column_metadata_rows = (
            session.table([database, "INFORMATION_SCHEMA", "COLUMNS"])
            .filter(upper(col("TABLE_SCHEMA")) == lit(schema.upper()))
            .select(
                "TABLE_NAME",
                "COLUMN_NAME",
                "DATA_TYPE",
                "ORDINAL_POSITION",
            )
            .collect()
        )
    except Exception:
        raise RuntimeError(
            "Read-only component lookup metadata discovery failed; "
            "no lookup source was selected"
        ) from None

    objects = _lookup_catalog_objects(
        table_metadata_rows,
        column_metadata_rows,
    )
    content_id_objects, ambiguous_key_objects = (
        _lookup_content_id_objects(objects)
    )
    if ambiguous_key_objects:
        raise RuntimeError(
            "Multiple ContentId-like columns exist in one or more metadata "
            "objects; no lookup source was selected"
        )
    if not content_id_objects:
        raise RuntimeError(
            "No metadata-visible object in the Archer schema exposes ContentId"
        )
    if (
        len(content_id_objects)
        > LOOKUP_DISCOVERY_MAX_CONTENT_ID_OBJECTS
    ):
        raise RuntimeError(
            "ContentId metadata search exceeds the safe object-scan limit; "
            "narrow the approved table scope before continuing"
        )

    profiles = []
    membership_dfs = []
    for metadata in content_id_objects:
        table_name = metadata["table_name"]
        display_name = ".".join(
            _lookup_safe_name(part)
            for part in (database, schema, table_name)
        )
        key_column = metadata["key_column"]["name"]

        try:
            candidate_table_df = session.table(
                [database, schema, table_name]
            )
            candidate_key_df = candidate_table_df.select(
                trim(lookup_col(key_column).cast("string")).alias(
                    "_LOOKUP_ID"
                )
            )
            key_summary = candidate_key_df.agg(
                sf_count(lit(1)).alias("TOTAL_ROWS"),
                sf_count(
                    when(lookup_nonblank(col("_LOOKUP_ID")), lit(1))
                ).alias("NONBLANK_KEY_ROWS"),
                count_distinct(
                    when(
                        lookup_nonblank(col("_LOOKUP_ID")),
                        col("_LOOKUP_ID"),
                    )
                ).alias("DISTINCT_KEYS"),
            ).collect()[0]
            nonblank_candidate_keys_df = candidate_key_df.filter(
                lookup_nonblank(col("_LOOKUP_ID"))
            )
            matched_key_rows_df = component_ids_df.join(
                nonblank_candidate_keys_df,
                component_ids_df["_COMPONENT_ID"]
                == nonblank_candidate_keys_df["_LOOKUP_ID"],
                "inner",
            )
            match_summary = matched_key_rows_df.agg(
                sf_count(lit(1)).alias("MATCHED_KEY_ROWS"),
                count_distinct(col("_COMPONENT_ID")).alias("MATCHED_IDS"),
            ).collect()[0]
        except Exception:
            raise RuntimeError(
                "Read-only aggregate profiling failed for metadata object "
                + display_name
                + "; no lookup source was selected"
            ) from None

        total_rows = _lookup_int(key_summary, "TOTAL_ROWS")
        nonblank_key_rows = _lookup_int(
            key_summary,
            "NONBLANK_KEY_ROWS",
        )
        distinct_keys = _lookup_int(key_summary, "DISTINCT_KEYS")
        matched_key_rows = _lookup_int(
            match_summary,
            "MATCHED_KEY_ROWS",
        )
        matched_ids = _lookup_int(match_summary, "MATCHED_IDS")
        profile = {
            "metadata": metadata,
            "display_name": display_name,
            "key_column": key_column,
            "total_rows": total_rows,
            "nonblank_key_rows": nonblank_key_rows,
            "distinct_keys": distinct_keys,
            "duplicate_key_rows": nonblank_key_rows - distinct_keys,
            "matched_key_rows": matched_key_rows,
            "matched_ids": matched_ids,
            "matched_duplicate_rows": matched_key_rows - matched_ids,
            "coverage_percent": round(
                100.0 * matched_ids / distinct_component_ids,
                2,
            ),
            "direct_field_evidence": [],
            "json_key_evidence": [],
        }
        profiles.append(profile)
        if matched_ids:
            membership_dfs.append(
                matched_key_rows_df.select(
                    col("_COMPONENT_ID"),
                    lit(display_name).alias("_LOOKUP_OBJECT"),
                ).distinct()
            )

    matched_profiles = [
        profile for profile in profiles if profile["matched_ids"] > 0
    ]
    if len(matched_profiles) > LOOKUP_DISCOVERY_MAX_MATCHED_OBJECTS:
        raise RuntimeError(
            "Too many ContentId objects match governed component identities; "
            "an owner-provided schema scope is required before payload profiling"
        )

    for profile in matched_profiles:
        metadata = profile["metadata"]
        direct_fields = []
        json_columns = []
        for column_metadata in metadata["columns"]:
            column_name = column_metadata["name"]
            if _lookup_compact_name(column_name) == "CURATEDJSON":
                json_columns.append(column_metadata)
                continue
            category = _lookup_field_category(column_name)
            if category is not None:
                direct_fields.append(
                    {"name": column_name, "category": category}
                )

        if (
            len(direct_fields)
            > LOOKUP_DISCOVERY_MAX_DIRECT_FIELDS_PER_OBJECT
        ):
            raise RuntimeError(
                "Likely field metadata exceeds the safe per-object limit; "
                "no lookup source was selected"
            )
        if len(json_columns) > 1:
            raise RuntimeError(
                "More than one CuratedJson-like column exists in a matching "
                "object; no lookup source was selected"
            )

        table_name = metadata["table_name"]
        candidate_table_df = session.table([database, schema, table_name])
        key_expression = trim(
            lookup_col(profile["key_column"]).cast("string")
        )

        if direct_fields:
            select_expressions = [key_expression.alias("_LOOKUP_ID")]
            aliases = []
            for index, field_metadata in enumerate(direct_fields):
                alias = "FIELD_{:03d}".format(index)
                aliases.append(alias)
                select_expressions.append(
                    lookup_col(field_metadata["name"]).alias(alias)
                )
            candidate_fields_df = candidate_table_df.select(
                *select_expressions
            ).filter(lookup_nonblank(col("_LOOKUP_ID")))
            matched_fields_df = component_ids_df.join(
                candidate_fields_df,
                component_ids_df["_COMPONENT_ID"]
                == candidate_fields_df["_LOOKUP_ID"],
                "inner",
            )
            aggregate_expressions = [
                count_distinct(
                    when(
                        lookup_nonblank(col(alias)),
                        col("_COMPONENT_ID"),
                    )
                ).alias("POPULATED_{:03d}".format(index))
                for index, alias in enumerate(aliases)
            ]
            try:
                direct_summary = matched_fields_df.agg(
                    *aggregate_expressions
                ).collect()[0]
            except Exception:
                raise RuntimeError(
                    "Read-only field profiling failed for metadata object "
                    + profile["display_name"]
                    + "; no lookup source was selected"
                ) from None

            for index, field_metadata in enumerate(direct_fields):
                populated_ids = _lookup_int(
                    direct_summary,
                    "POPULATED_{:03d}".format(index),
                )
                profile["direct_field_evidence"].append(
                    {
                        "category": field_metadata["category"],
                        "name": field_metadata["name"],
                        "populated_ids": populated_ids,
                        "coverage_percent": round(
                            100.0 * populated_ids / profile["matched_ids"],
                            2,
                        ),
                    }
                )

        if json_columns:
            json_metadata = json_columns[0]
            json_expression = lookup_col(json_metadata["name"])
            if json_metadata["data_type"] not in LOOKUP_SEMISTRUCTURED_TYPES:
                json_expression = parse_json(
                    json_expression.cast("string")
                )
            candidate_json_df = candidate_table_df.select(
                key_expression.alias("_LOOKUP_ID"),
                json_expression.alias("_JSON_OBJECT"),
            ).filter(lookup_nonblank(col("_LOOKUP_ID")))
            matched_json_df = component_ids_df.join(
                candidate_json_df,
                component_ids_df["_COMPONENT_ID"]
                == candidate_json_df["_LOOKUP_ID"],
                "inner",
            )
            try:
                json_key_rows = (
                    matched_json_df.join_table_function(
                        "flatten",
                        col("_JSON_OBJECT"),
                    )
                    .filter(col("KEY").is_not_null())
                    .select(
                        col("_COMPONENT_ID"),
                        col("KEY").cast("string").alias("_JSON_KEY"),
                        col("VALUE").alias("_JSON_VALUE"),
                    )
                    .group_by(col("_JSON_KEY"))
                    .agg(
                        count_distinct(col("_COMPONENT_ID")).alias(
                            "PRESENT_IDS"
                        ),
                        count_distinct(
                            when(
                                lookup_nonblank(col("_JSON_VALUE")),
                                col("_COMPONENT_ID"),
                            )
                        ).alias("NONBLANK_IDS"),
                    )
                    .limit(LOOKUP_DISCOVERY_MAX_JSON_KEYS_PER_OBJECT + 1)
                    .collect()
                )
            except Exception:
                raise RuntimeError(
                    "Read-only CuratedJson key profiling failed for metadata "
                    "object "
                    + profile["display_name"]
                    + "; no lookup source was selected"
                ) from None
            if len(json_key_rows) > LOOKUP_DISCOVERY_MAX_JSON_KEYS_PER_OBJECT:
                raise RuntimeError(
                    "CuratedJson key profiling exceeds the safe key limit; "
                    "no lookup source was selected"
                )

            for row in json_key_rows:
                key_name = str(_lookup_row_value(row, "_JSON_KEY"))
                category = _lookup_field_category(key_name)
                if category is None:
                    continue
                nonblank_ids = _lookup_int(row, "NONBLANK_IDS")
                profile["json_key_evidence"].append(
                    {
                        "category": category,
                        "name": key_name,
                        "present_ids": _lookup_int(row, "PRESENT_IDS"),
                        "nonblank_ids": nonblank_ids,
                        "coverage_percent": round(
                            100.0 * nonblank_ids / profile["matched_ids"],
                            2,
                        ),
                    }
                )

    if membership_dfs:
        combined_membership_df = membership_dfs[0]
        for membership_df in membership_dfs[1:]:
            combined_membership_df = combined_membership_df.union_all(
                membership_df
            )
        combined_membership_df = combined_membership_df.distinct()
        combined_matched_ids = combined_membership_df.select(
            col("_COMPONENT_ID")
        ).distinct().count()
        cross_object_ambiguous_ids = (
            combined_membership_df.group_by(col("_COMPONENT_ID"))
            .agg(
                count_distinct(col("_LOOKUP_OBJECT")).alias("OBJECT_COUNT")
            )
            .filter(col("OBJECT_COUNT") > lit(1))
            .count()
        )
    else:
        combined_matched_ids = 0
        cross_object_ambiguous_ids = 0

    profiles.sort(
        key=lambda item: (
            -item["matched_ids"],
            item["matched_duplicate_rows"],
            item["display_name"],
        )
    )

    print("=== SSP COMPONENT LOOKUP DISCOVERY ===")
    print(
        "Safety: aggregate-only; no component IDs, source-record IDs, "
        "payloads, or values printed"
    )
    print("Writes executed: False")
    print("Component-node occurrences:", component_node_occurrences)
    print("Distinct governed component IDs:", distinct_component_ids)
    print("ContentId metadata objects profiled:", len(profiles))
    print("Objects with governed-ID matches:", len(matched_profiles))
    print("Objects with zero governed-ID matches:", len(profiles) - len(matched_profiles))
    print("Distinct IDs matched by any object:", combined_matched_ids)
    print(
        "Distinct IDs unmatched by all objects:",
        distinct_component_ids - combined_matched_ids,
    )
    print("IDs matching more than one object:", cross_object_ambiguous_ids)

    for profile in profiles:
        if not profile["matched_ids"]:
            continue
        print("\nOBJECT:", profile["display_name"])
        print("  Object type:", profile["metadata"]["table_type"])
        print("  Key column:", _lookup_safe_name(profile["key_column"]))
        print("  Total rows:", profile["total_rows"])
        print("  Nonblank key rows:", profile["nonblank_key_rows"])
        print("  Distinct keys:", profile["distinct_keys"])
        print("  Duplicate key rows:", profile["duplicate_key_rows"])
        print("  Matched key rows:", profile["matched_key_rows"])
        print("  Matched distinct component IDs:", profile["matched_ids"])
        print("  Duplicate matched key rows:", profile["matched_duplicate_rows"])
        print("  Governed-ID coverage percent:", profile["coverage_percent"])

        available_columns = {
            _lookup_compact_name(item["name"]): item["name"]
            for item in profile["metadata"]["columns"]
        }
        order_columns = []
        for configured_name in config.get("SOURCE_ORDER_CANDIDATES", []):
            actual_name = available_columns.get(
                _lookup_compact_name(configured_name)
            )
            if actual_name and actual_name not in order_columns:
                order_columns.append(actual_name)
        print(
            "  Available source-order columns:",
            ",".join(_lookup_safe_name(name) for name in order_columns)
            or "NONE",
        )

        print("  Likely relational fields:")
        direct_evidence = sorted(
            profile["direct_field_evidence"],
            key=lambda item: (
                item["category"],
                -item["populated_ids"],
                item["name"],
            ),
        )
        if not direct_evidence:
            print("    NONE")
        for item in direct_evidence:
            print(
                "    {} | {} | populated matched IDs={} | coverage={}%".format(
                    item["category"],
                    _lookup_safe_name(item["name"]),
                    item["populated_ids"],
                    item["coverage_percent"],
                )
            )

        print("  Likely top-level CURATED_JSON keys:")
        json_evidence = sorted(
            profile["json_key_evidence"],
            key=lambda item: (
                item["category"],
                -item["nonblank_ids"],
                item["name"],
            ),
        )
        if not json_evidence:
            print("    NONE")
        for item in json_evidence:
            print(
                "    {} | {} | key-present IDs={} | "
                "nonblank matched IDs={} | coverage={}%".format(
                    item["category"],
                    _lookup_safe_name(item["name"]),
                    item["present_ids"],
                    item["nonblank_ids"],
                    item["coverage_percent"],
                )
            )

    strong_candidates = [
        profile
        for profile in matched_profiles
        if (
            profile["matched_ids"] == distinct_component_ids
            and profile["duplicate_key_rows"] == 0
            and all(
                _lookup_best_field_coverage(profile, category)
                == distinct_component_ids
                for category in ("title", "description", "status")
            )
        )
    ]

    print("\n=== DISCOVERY CONCLUSION ===")
    if len(strong_candidates) == 1 and cross_object_ambiguous_ids == 0:
        print(
            "RESULT: SINGLE FULL-COVERAGE METADATA CANDIDATE; "
            "OWNER APPROVAL AND STATUS-TRANSFORMATION REVIEW REQUIRED"
        )
    elif combined_matched_ids == 0:
        print(
            "RESULT: NO CONTENT_ID LOOKUP MATCH FOUND IN THE SEARCHED SCHEMA"
        )
    elif combined_matched_ids < distinct_component_ids:
        print(
            "RESULT: PARTIAL LOOKUP COVERAGE; ADDITIONAL SOURCE OBJECTS "
            "OR KEY GOVERNANCE REQUIRED"
        )
    elif cross_object_ambiguous_ids:
        print(
            "RESULT: CROSS-OBJECT LOOKUP AMBIGUITY; EXPLICIT SOURCE "
            "PRECEDENCE OR UNION CONTRACT REQUIRED"
        )
    else:
        print(
            "RESULT: COMPLETE COMBINED COVERAGE; EXPLICIT SOURCE-OBJECT "
            "AND FIELD APPROVAL REQUIRED"
        )
    print(
        "No lookup table or field was approved, configured, or written by "
        "this discovery cell."
    )
    print("No database objects or rows were changed.")


if not globals().get("_LOOKUP_DISCOVERY_SKIP_EXECUTION", False):
    run_component_lookup_source_discovery()

