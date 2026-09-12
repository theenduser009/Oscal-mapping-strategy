# HISTORICAL — legacy field-dispatch workflow only; not for metadata-v1.
# Current workflow: Cell 3 routing reports and Cell 7 mapping coverage.
# Read-only populated-mapping dispatcher coverage diagnostic.
#
# Run this standalone Snowflake Python cell after Mapper V1 Cells 1 through 4.
# It uses Cell 4's exact dispatcher classifier and reports only mapping metadata
# plus aggregate populated-record counts. It never collects source values or
# record identifiers and performs no DML.

import re



def _require_legacy_dispatch_context():
    """Do not classify executable metadata with the retired field dispatcher."""
    state = globals()
    contexts = state.get("MAPPING_CONTEXTS", [])
    if not isinstance(contexts, (list, tuple)):
        contexts = []
    contexts = list(contexts) + [state.get("_default_context")]
    contracts = state.get("MODEL_CONTRACTS", {})
    if not isinstance(contracts, dict):
        contracts = {}
    metadata_context = any(
        isinstance(context, dict) and (
            context.get("model_contract", {}).get("POLICY") == "metadata-v1"
            or isinstance(context.get("compiled_plan"), dict)
        )
        for context in contexts
    )
    metadata_contract = any(
        isinstance(contract, dict) and contract.get("POLICY") == "metadata-v1"
        for contract in contracts.values()
    )
    rows = state.get("CANONICAL_MAPPING_ROWS", [])
    metadata_rows = isinstance(rows, (list, tuple)) and any(
        isinstance(row, dict) and bool(row.get("TRANSFORM_ID")) for row in rows
    )
    if metadata_context or metadata_contract or metadata_rows:
        raise RuntimeError(
            "Historical legacy-only diagnostic cannot run on metadata-v1. "
            "Use Cell 3 routing_report and Cell 7 mapping coverage instead."
        )

def _dispatch_safe_metadata(value):
    return re.sub(r"[\r\n\t]+", " ", str(value or "")).strip()


def _dispatch_row_metadata(mapping_row):
    return {
        "SOURCE_FIELD_NAME": _dispatch_safe_metadata(
            mapping_row.get("SOURCE_FIELD_NAME")
        ),
        "OWNER_ELEMENT_PATH": _dispatch_safe_metadata(
            mapping_row.get("OWNER_ELEMENT_PATH")
        ),
        "TARGET_FIELD": _dispatch_safe_metadata(
            _target_field_name(mapping_row)
        ),
        "MAPPING_TYPE": _dispatch_safe_metadata(
            mapping_row.get("MAPPING_TYPE") or "Direct"
        ),
    }


def _dispatch_rejected_rows(mapping_rows, classifier):
    rejected = []
    for mapping_row in mapping_rows:
        try:
            classifier(mapping_row)
        except (KeyError, TypeError, ValueError):
            rejected.append(_dispatch_row_metadata(mapping_row))
    return rejected


def _dispatch_quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


def _dispatch_row_value(row, key):
    if hasattr(row, "as_dict"):
        values = row.as_dict(recursive=True)
    elif isinstance(row, dict):
        values = row
    else:
        values = {}
    normalized = {str(name).upper(): value for name, value in values.items()}
    return normalized.get(str(key).upper())


def run_mapping_dispatch_coverage_diagnostic():
    _require_legacy_dispatch_context()
    required_state = {
        "session": globals().get("session"),
        "CONFIG": globals().get("CONFIG"),
        "source_df": globals().get("source_df"),
        "CANONICAL_MAPPING_ROWS": globals().get("CANONICAL_MAPPING_ROWS"),
        "_mapping_handler_for_row": globals().get(
            "_mapping_handler_for_row"
        ),
        "_target_field_name": globals().get("_target_field_name"),
    }
    missing_state = [
        name for name, value in required_state.items() if value is None
    ]
    if missing_state:
        raise RuntimeError(
            "Run Mapper V1 Cells 1 through 4 first. Missing notebook state: "
            + ", ".join(missing_state)
        )

    config = required_state["CONFIG"]
    if config.get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Set EXECUTE_WRITES = False before running this diagnostic."
        )

    source_dataframe = required_state["source_df"]
    source_columns = {
        str(name).strip().upper(): name for name in source_dataframe.columns
    }
    if "CURATED_JSON" not in source_columns:
        raise RuntimeError("Cell 2 source output is missing CURATED_JSON")

    rejected_rows = _dispatch_rejected_rows(
        required_state["CANONICAL_MAPPING_ROWS"],
        required_state["_mapping_handler_for_row"],
    )
    if not rejected_rows:
        print("Populated rejected canonical mapping rows: 0")
        return []

    from snowflake.snowpark.functions import (
        col,
        lit,
        parse_json,
        sum as sf_sum,
        to_json,
        when,
    )

    source_fields = sorted(
        {
            row["SOURCE_FIELD_NAME"]
            for row in rejected_rows
            if row["SOURCE_FIELD_NAME"]
        }
    )
    aliases = {
        source_field: f"_DISPATCH_COUNT_{index:04d}"
        for index, source_field in enumerate(source_fields)
    }
    source_json = parse_json(
        col(
            _dispatch_quote_identifier(source_columns["CURATED_JSON"])
        ).cast("string")
    )
    aggregate_expressions = []
    for source_field in source_fields:
        serialized_value = to_json(source_json.getItem(source_field))
        populated = serialized_value.is_not_null() & ~serialized_value.isin(
            "null",
            '""',
            "[]",
            "{}",
        )
        aggregate_expressions.append(
            sf_sum(when(populated, lit(1)).otherwise(lit(0))).alias(
                aliases[source_field]
            )
        )

    count_rows = source_dataframe.agg(*aggregate_expressions).collect()
    if len(count_rows) != 1:
        raise RuntimeError(
            "Dispatcher coverage aggregation did not return one count row"
        )
    count_row = count_rows[0]

    populated_rejections = []
    for rejected_row in rejected_rows:
        source_field = rejected_row["SOURCE_FIELD_NAME"]
        populated_count = (
            int(_dispatch_row_value(count_row, aliases[source_field]) or 0)
            if source_field in aliases
            else 0
        )
        if populated_count <= 0:
            continue
        output_row = dict(rejected_row)
        output_row["POPULATED_RECORD_COUNT"] = populated_count
        populated_rejections.append(output_row)

    print(
        "Populated rejected canonical mapping rows:",
        len(populated_rejections),
    )
    for output_row in populated_rejections:
        print(
            "SOURCE_FIELD_NAME=",
            output_row["SOURCE_FIELD_NAME"],
            "| OWNER_ELEMENT_PATH=",
            output_row["OWNER_ELEMENT_PATH"],
            "| TARGET_FIELD=",
            output_row["TARGET_FIELD"],
            "| MAPPING_TYPE=",
            output_row["MAPPING_TYPE"],
            "| POPULATED_RECORD_COUNT=",
            output_row["POPULATED_RECORD_COUNT"],
        )
    return populated_rejections


mapping_dispatch_coverage_result = (
    run_mapping_dispatch_coverage_diagnostic()
)
