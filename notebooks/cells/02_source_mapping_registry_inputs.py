# %% Cell 2 - Source, mapping, registry, and Archer value inputs

import pandas as pd


def _normalized_columns(columns):
    normalized = {}
    for name in columns:
        key = str(name).strip().upper()
        if key in normalized:
            raise RuntimeError(
                "Source schema contains duplicate normalized column names"
            )
        normalized[key] = name
    return normalized


def _required_lookup_column(columns, expected_name, component_type):
    matches = [
        name
        for name in columns
        if str(name).strip().upper() == expected_name
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Approved component hydration source must expose exactly one "
            + expected_name
            + " column: "
            + component_type
        )
    return matches[0]


COMPONENT_HYDRATION_SOURCE_CONTRACT = {
    "software": {
        "source_table": (
            "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW"
        ),
        "title_field": "SOFTWARE_NAME",
        "description_field": "DESCRIPTION",
    },
    "interconnection": {
        "source_table": (
            "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW"
        ),
        "title_field": "INTERCONNECTION_NAME",
        "description_field": "DESCRIPTION",
    },
}


raw_input_df = session.table(CONFIG["RAW_TABLE"])
raw_columns = _normalized_columns(raw_input_df.columns)

if "CONTENT_ID" not in raw_columns or "CURATED_JSON" not in raw_columns:
    raise ValueError("RAW table must contain CONTENT_ID and CURATED_JSON")

source_select = [
    col(raw_columns["CONTENT_ID"]).cast("string").alias("SOURCE_RECORD_ID"),
    col(raw_columns["CURATED_JSON"]).alias("CURATED_JSON"),
]

source_order_columns = []
for candidate in CONFIG["SOURCE_ORDER_CANDIDATES"]:
    if candidate in raw_columns:
        source_select.append(col(raw_columns[candidate]).alias(candidate))
        source_order_columns.append(candidate)

source_candidates_df = raw_input_df.select(*source_select)

source_row_count = source_candidates_df.count()
source_distinct_count = (
    source_candidates_df.select("SOURCE_RECORD_ID").distinct().count()
)

if source_row_count != source_distinct_count:
    if not source_order_columns:
        raise RuntimeError(
            "Duplicate CONTENT_ID values exist, but no approved technical "
            "load/version column is available. Do not use DISTINCT or an "
            "arbitrary drop_duplicates rule. Add an approved source-order "
            "column to CONFIG before continuing."
        )

    order_expressions = [
        col(column_name).desc_nulls_last()
        for column_name in source_order_columns
    ]
    order_expressions.append(
        sha2(to_json(col("CURATED_JSON")), 256).desc_nulls_last()
    )

    source_df = (
        source_candidates_df.with_column(
            "_SOURCE_ROW_NUMBER",
            row_number().over(
                Window.partition_by("SOURCE_RECORD_ID").order_by(
                    *order_expressions
                )
            ),
        )
        .filter(col("_SOURCE_ROW_NUMBER") == lit(1))
        .drop("_SOURCE_ROW_NUMBER", *source_order_columns)
    )
else:
    source_df = source_candidates_df

selected_source_count = source_df.count()
selected_distinct_count = source_df.select("SOURCE_RECORD_ID").distinct().count()

if selected_source_count != selected_distinct_count:
    raise ValueError("Source selection did not produce one row per CONTENT_ID")

# Keep the approved lookup sources lazy in Cell 2. Cell 5 asks Cell 4 to join
# only the component IDs referenced by this SSP run, then validates duplicate
# keys and missing hydration rows before any graph node is built.
COMPONENT_HYDRATION_SOURCE_DFS = {}
for component_type, contract in COMPONENT_HYDRATION_SOURCE_CONTRACT.items():
    lookup_source_df = session.table(contract["source_table"])
    lookup_content_id_column = _required_lookup_column(
        lookup_source_df.columns,
        "CONTENT_ID",
        component_type,
    )
    lookup_curated_json_column = _required_lookup_column(
        lookup_source_df.columns,
        "CURATED_JSON",
        component_type,
    )

    COMPONENT_HYDRATION_SOURCE_DFS[component_type] = (
        lookup_source_df.select(
            col(lookup_content_id_column).alias("CONTENT_ID"),
            col(lookup_curated_json_column).alias("CURATED_JSON"),
        )
    )

mapping_artifact_pdf = pd.read_csv(
    CONFIG["MAPPING_FILE"],
    encoding="cp1252",
    dtype=str,
).where(lambda frame: frame.notna(), None)
mapping_artifact_pdf.columns = [
    str(name).strip().upper() for name in mapping_artifact_pdf.columns
]
mapping_df = session.create_dataframe(mapping_artifact_pdf)

element_registry_df = session.table(CONFIG["ELEMENT_REGISTRY_TABLE"])

archer_meta_value_df = (
    session.table(CONFIG["ARCHER_META_VALUE_TABLE"])
    .select(col("SELECT_VALUE_ID"), col("SELECT_VALUE_NAME"))
    .filter(col("SELECT_VALUE_NAME").is_not_null())
)

ARCHER_VALUE_LOOKUP = {}
for row in archer_meta_value_df.collect():
    value_id = row["SELECT_VALUE_ID"]
    value_name = row["SELECT_VALUE_NAME"]
    if value_id is not None:
        ARCHER_VALUE_LOOKUP[str(value_id).strip()] = (
            str(value_name).strip() if value_name is not None else None
        )

FIPS_199_VALUE_LOOKUP = {}
for value_id, value_name in ARCHER_VALUE_LOOKUP.items():
    normalized_name = (value_name or "").strip().lower()
    if normalized_name in {"low", "moderate", "high"}:
        FIPS_199_VALUE_LOOKUP[value_id] = normalized_name

print("RAW source rows:", source_row_count)
print("RAW distinct CONTENT_ID values:", source_distinct_count)
print("Selected source rows:", selected_source_count)
print("Source order columns:", source_order_columns)
print("Mapping rows:", mapping_df.count())
print("Archer select values:", len(ARCHER_VALUE_LOOKUP))
print(
    "Approved component hydration sources:",
    len(COMPONENT_HYDRATION_SOURCE_DFS),
)
