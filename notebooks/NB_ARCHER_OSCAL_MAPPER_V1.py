"""NB_ARCHER_OSCAL_MAPPER_V1

Authoritative seven-cell Snowflake/Snowpark notebook source for the
metadata-driven Archer-to-OSCAL mapper.

Copy each ``# %% Cell N`` section into one Snowflake notebook Python cell and
run the cells in order.  The notebook is fail-closed: writes remain disabled
unless Cell 1 is deliberately changed after validation succeeds.
"""


# %% Cell 1 - Initialization and configuration

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import (
    col,
    lit,
    row_number,
    sha2,
    to_json,
)
from snowflake.snowpark.window import Window

import datetime
import hashlib
import json
import re
import uuid


session = get_active_session()

CONFIG = {
    "RUN_ID": datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    ),
    "OSCAL_MODEL": "SSP",
    "OSCAL_VERSION": "1.2.3",
    "SSP_DOCUMENT_VERSION": "1.0",
    "EXECUTE_WRITES": False,
    "BUILD_COVERAGE_REPORT": True,
    "SOURCE_SYSTEM_NAME": "ARCHER",
    "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
    "RAW_TABLE": (
        "RTX_RAW_DEV.ES_ESC_GRC."
        "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
    ),
    "ARCHER_META_VALUE_TABLE": (
        "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE"
    ),
    "TARGET_DIM": (
        "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED."
        "DIM_OSCAL_SSP_ELEMENT"
    ),
    "TARGET_FACT": (
        "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED."
        "FACT_OSCAL_SSP_DEPENDENCY"
    ),
    "DIM_PK_COLUMN": "PK_OSCAL_SSP_ELEMENT_HASH",
    "FACT_PK_COLUMN": "PK_FACT_OSCAL_DEPENDENCY_HASH",
    "MAPPING_FILE": "archer_to_oscal_mapping (4).csv",
    "ELEMENT_REGISTRY_TABLE": (
        "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
    ),
    "IDENTITY_VERSION": "v1_registry_path_instance",
    "NODE_UUID_POLICY": "deterministic_uuid5",
    # Ordered from strongest technical recency signal to weakest.
    "SOURCE_ORDER_CANDIDATES": [
        "DW_LOAD_TIMESTAMP_TZ",
        "DW_LOAD_TIMESTAMP",
        "UPDATED_DATE",
        "LAST_UPDATED_DATE",
        "MODIFIED_DATE",
        "CREATE_DATE",
    ],
}


if CONFIG["EXECUTE_WRITES"]:
    raise RuntimeError(
        "Repository baseline must start with EXECUTE_WRITES = False."
    )

print("Cell 1 initialized")
print("OSCAL model:", CONFIG["OSCAL_MODEL"])
print("OSCAL version:", CONFIG["OSCAL_VERSION"])
print("Writes enabled:", CONFIG["EXECUTE_WRITES"])


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


# %% Cell 3 - Canonical mapping contract

EXPECTED_MAPPING_COLUMNS = [
    "SOURCE_FIELD_NAME",
    "OSCAL_MODEL",
    "OSCAL_ELEMENT_PATH",
    "OSCAL_FIELD_NAME",
    "MAPPING_TYPE",
    "TRANSFORMATION_LOGIC",
    "STATUS",
]

MAPPING_COLUMN_ALIASES = {
    "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME",
    "SOURCE_FIELD": "SOURCE_FIELD_NAME",
    "MODEL": "OSCAL_MODEL",
    "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
    "ELEMENT_PATH": "OSCAL_ELEMENT_PATH",
    "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
    "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME",
    "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
    "MAPPING_STATUS": "STATUS",
}

canonical_mapping_pdf = mapping_artifact_pdf.copy()
canonical_mapping_pdf.rename(columns=MAPPING_COLUMN_ALIASES, inplace=True)

for column_name in EXPECTED_MAPPING_COLUMNS:
    if column_name not in canonical_mapping_pdf.columns:
        canonical_mapping_pdf[column_name] = None

for column_name in EXPECTED_MAPPING_COLUMNS:
    canonical_mapping_pdf[column_name] = canonical_mapping_pdf[
        column_name
    ].map(lambda value: value.strip() if isinstance(value, str) else value)

canonical_mapping_pdf = canonical_mapping_pdf[
    canonical_mapping_pdf["SOURCE_FIELD_NAME"].notna()
    & canonical_mapping_pdf["OSCAL_ELEMENT_PATH"].notna()
].copy()

# Mapping CSV model labels have not been consistent (for example, "SSP"
# versus "System Security Plan").  The registry is the authoritative model
# boundary, so assign each mapping to its deepest active registry owner rather
# than filtering on the display label in the CSV.
active_registry_paths = []
for registry_row in element_registry_df.collect():
    registry_values = {
        str(key).upper(): value
        for key, value in registry_row.as_dict(recursive=True).items()
    }
    registry_model = registry_values.get(
        "OSCAL_MODEL_KEY",
        registry_values.get("OSCAL_MODEL"),
    )
    if (
        registry_model is not None
        and str(registry_model).strip().upper()
        != CONFIG["OSCAL_MODEL"].upper()
    ):
        continue

    registry_active = registry_values.get("IS_ACTIVE")
    if registry_active is not None and str(registry_active).strip().upper() in {
        "FALSE",
        "F",
        "NO",
        "N",
        "0",
    }:
        continue

    registry_path = (
        registry_values.get("NODE_PATH")
        or registry_values.get("OSCAL_ELEMENT_PATH")
        or registry_values.get("ELEMENT_PATH")
        or registry_values.get("JSON_PATH")
    )
    if registry_path:
        active_registry_paths.append(str(registry_path).strip())

active_registry_paths = sorted(
    set(active_registry_paths),
    key=lambda path: (path.count("."), len(path)),
    reverse=True,
)

if not active_registry_paths:
    raise ValueError(
        "Cell 3 found no active registry paths for model "
        f"{CONFIG['OSCAL_MODEL']}"
    )


def _mapping_owner_path(mapping_path):
    mapping_path = str(mapping_path).strip()
    for registry_path in active_registry_paths:
        if mapping_path == registry_path or mapping_path.startswith(
            registry_path + "."
        ):
            return registry_path
    return None


# These eight sources are explicitly identified as extension properties in
# docs/MAPPING_ARTIFACT_SCREENSHOT_EVIDENCE_2026-09-09.md. Some artifact rows
# name a parent-level pseudo-field instead of the props[] collection. Resolve
# that approved intent before grouping; never put pseudo-fields on the parent.
APPROVED_SSP_EXTENSION_PROPERTY_FIELDS = {
    "INFORMATION_SYSTEM_TYPE",
    "FISMA_REPORTABLE",
    "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL",
    "CRITICAL_INFRASTRUCTURE",
    "PACKAGE_TYPE",
    "PIA_REQUIRED",
    "INFORMATION_CLASSIFICATION",
}
_SSP_CHARACTERISTICS_PATH = "system-security-plan.system-characteristics"
_SSP_PROPERTIES_PATH = _SSP_CHARACTERISTICS_PATH + ".props[]"


def _canonical_mapping_path(mapping_row):
    artifact_path = str(mapping_row["OSCAL_ELEMENT_PATH"]).strip()
    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    mapping_type = re.sub(
        r"[^a-z0-9]+", "-", str(mapping_row.get("MAPPING_TYPE") or "").lower()
    ).strip("-")
    if (
        CONFIG["OSCAL_MODEL"].upper() != "SSP"
        or source_field not in APPROVED_SSP_EXTENSION_PROPERTY_FIELDS
        or mapping_type != "extension-property"
    ):
        return artifact_path

    # Restrict normalization to the characteristics parent, a direct
    # unregistered leaf, or its actual props collection. Do not move mappings
    # out of another registered branch or arbitrary nested path.
    owner = _mapping_owner_path(artifact_path)
    if owner not in {_SSP_CHARACTERISTICS_PATH, _SSP_PROPERTIES_PATH}:
        return artifact_path
    relative_path = artifact_path[len(_SSP_CHARACTERISTICS_PATH):].lstrip(".")
    direct_leaf = not any(token in relative_path for token in (".", "[", "]"))
    properties_path = (
        artifact_path == _SSP_PROPERTIES_PATH
        or artifact_path in {
            _SSP_PROPERTIES_PATH + ".name",
            _SSP_PROPERTIES_PATH + ".value",
        }
    )
    if not (direct_leaf or properties_path):
        return artifact_path
    if _SSP_PROPERTIES_PATH not in active_registry_paths:
        raise ValueError(
            "Approved SSP extension property requires active registry path "
            + _SSP_PROPERTIES_PATH
        )
    return _SSP_PROPERTIES_PATH + ".value"


# Retain the original artifact path and explicit target column for provenance.
# Only the canonical route determines registry ownership and derived fields.
canonical_mapping_pdf["CANONICAL_ELEMENT_PATH"] = canonical_mapping_pdf.apply(
    _canonical_mapping_path, axis=1
)
canonical_mapping_pdf["OWNER_ELEMENT_PATH"] = canonical_mapping_pdf[
    "CANONICAL_ELEMENT_PATH"
].map(_mapping_owner_path)
canonical_mapping_pdf = canonical_mapping_pdf[
    canonical_mapping_pdf["OWNER_ELEMENT_PATH"].notna()
].copy()

if canonical_mapping_pdf.empty:
    raise ValueError(
        "Cell 3 found mapping rows, but none belong to an active registry "
        f"path for model {CONFIG['OSCAL_MODEL']}"
    )

canonical_mapping_pdf["FIELD_RELATIVE_PATH"] = canonical_mapping_pdf.apply(
    lambda row: str(row["CANONICAL_ELEMENT_PATH"])[
        len(str(row["OWNER_ELEMENT_PATH"])):
    ].lstrip("."),
    axis=1,
)

# When the CSV does not provide a separate target-field column, derive it
# from the portion of OSCAL_ELEMENT_PATH below the owning registry node.
missing_target_field = canonical_mapping_pdf["OSCAL_FIELD_NAME"].isna() | (
    canonical_mapping_pdf["OSCAL_FIELD_NAME"].fillna("").str.strip() == ""
)
canonical_mapping_pdf.loc[
    missing_target_field,
    "OSCAL_FIELD_NAME",
] = canonical_mapping_pdf.loc[
    missing_target_field,
    "FIELD_RELATIVE_PATH",
].map(
    lambda path: (
        str(path).split(".")[-1].replace("[]", "")
        if str(path).strip()
        else None
    )
)

canonical_mapping_pdf["OSCAL_MODEL"] = CONFIG["OSCAL_MODEL"].upper()
canonical_mapping_pdf["MAPPING_TYPE"] = (
    canonical_mapping_pdf["MAPPING_TYPE"].fillna("Direct").str.strip()
)
canonical_mapping_pdf["STATUS"] = canonical_mapping_pdf["STATUS"].fillna(
    "In Progress"
)

canonical_mapping_pdf.sort_values(
    ["OWNER_ELEMENT_PATH", "OSCAL_ELEMENT_PATH", "SOURCE_FIELD_NAME"],
    inplace=True,
    kind="stable",
)
canonical_mapping_pdf.reset_index(drop=True, inplace=True)

canonical_mapping_df = session.create_dataframe(canonical_mapping_pdf)

CANONICAL_MAPPING_ROWS = canonical_mapping_pdf.to_dict(orient="records")
MAPPINGS_BY_ELEMENT_PATH = {}
for mapping_row in CANONICAL_MAPPING_ROWS:
    owner_path = str(mapping_row["OWNER_ELEMENT_PATH"]).strip()
    MAPPINGS_BY_ELEMENT_PATH.setdefault(owner_path, []).append(mapping_row)

print("Canonical SSP mapping rows:", len(CANONICAL_MAPPING_ROWS))
print("Active SSP registry paths:", len(active_registry_paths))
print("Mapped registry owner paths:", len(MAPPINGS_BY_ELEMENT_PATH))


# %% Cell 4 - Generic parsing, transformation, and payload helpers

SKIP_VALUE = object()

RESPONSIBLE_PARTY_ROLE_DEFINITIONS = {
    "INFORMATION_OWNER_IO": {
        "id": "information-owner",
        "title": "Information Owner",
    },
    "INFORMATION_SYSTEM_OWNER_ISO": {
        "id": "system-owner",
        "title": "Information System Owner",
    },
    "AUTHORIZING_OFFICIAL_AO": {
        "id": "authorizing-official",
        "title": "Authorizing Official",
    },
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO": {
        "id": "system-security-officer",
        "title": "Information System Security Officer",
    },
    "PRIVACY_OFFICER_PO": {
        "id": "privacy-officer",
        "title": "Privacy Officer",
    },
}
RESPONSIBLE_PARTY_ROLE_IDS = {
    source_field: definition["id"]
    for source_field, definition in RESPONSIBLE_PARTY_ROLE_DEFINITIONS.items()
}

TRANSIENT_SOURCE_FIELDS = {
    "HELPER_PTA_CALC",
    "PACKAGE_TYPE_HELPER_CALC",
}

SECURITY_IMPACT_ELEMENT_PATH = (
    "system-security-plan.system-characteristics.security-impact-level"
)
SYSTEM_CHARACTERISTICS_ELEMENT_PATH = (
    "system-security-plan.system-characteristics"
)
STATUS_ELEMENT_PATH = "system-security-plan.system-characteristics.status"
AUTHORIZATION_BOUNDARY_ELEMENT_PATH = (
    "system-security-plan.system-characteristics.authorization-boundary"
)
SYSTEM_CHARACTERISTICS_PROPS_ELEMENT_PATH = (
    "system-security-plan.system-characteristics.props[]"
)
SYSTEM_IDS_ELEMENT_PATH = (
    "system-security-plan.system-characteristics.system-ids[]"
)
COMPONENTS_ELEMENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
COMPONENT_SOURCE_TYPES = {
    "SUBSYSTEMS": "system",
    "SOFTWARE": "software",
    "HARDWARE": "hardware",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
    "SAP_INTAKE_FORM_INTERCONNECTIONS": "interconnection",
}
COMPONENT_HYDRATION_CONTRACT = {
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
COMPONENT_HYDRATION_SOURCE_FIELDS = {
    "SOFTWARE": "software",
    "INTERCONNECTIONS": "interconnection",
    "INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM": "interconnection",
}
DOCUMENT_IDS_ELEMENT_PATH = "system-security-plan.metadata.document-ids[]"
METADATA_ELEMENT_PATH = "system-security-plan.metadata"
METADATA_ROLES_ELEMENT_PATH = "system-security-plan.metadata.roles[]"
METADATA_PARTIES_ELEMENT_PATH = "system-security-plan.metadata.parties[]"
RESPONSIBLE_PARTIES_ELEMENT_PATH = (
    "system-security-plan.metadata.responsible-parties[]"
)
METADATA_TITLE_SOURCE_FIELD = "AUTHORIZATION_PACKAGE_NAME"
APPROVED_RESPONSIBLE_PARTY_TYPE = "person"
METADATA_TIMESTAMP_FIELDS = ("published", "last-modified")

APPROVED_TEXT_MAPPING_CONTRACTS = {
    "AUTHORIZATION_PACKAGE_NAME": {
        "owner_path": SYSTEM_CHARACTERISTICS_ELEMENT_PATH,
        "target_field": "system-name",
    },
    "ACRONYM": {
        "owner_path": SYSTEM_CHARACTERISTICS_ELEMENT_PATH,
        "target_field": "system-name-short",
    },
    "MISSION_PURPOSE": {
        "owner_path": SYSTEM_CHARACTERISTICS_ELEMENT_PATH,
        "target_field": "description",
    },
    "AUTHORIZATION_BOUNDARY_DESCRIPTION": {
        "owner_path": AUTHORIZATION_BOUNDARY_ELEMENT_PATH,
        "target_field": "description",
    },
}

SECURITY_IMPACT_SOURCE_OBJECTIVES = {
    "RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY": (
        "security-objective-confidentiality"
    ),
    "CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE": (
        "security-objective-confidentiality"
    ),
    "RECOMMENDED_INTEGRITY_CONTROL_CATEGORY": "security-objective-integrity",
    "INTEGRITY_CONTROL_CATEGORY_OVERRIDE": "security-objective-integrity",
    "RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY": (
        "security-objective-availability"
    ),
    "AVAILABILITY_CONTROL_CATEGORY_OVERRIDE": (
        "security-objective-availability"
    ),
    "PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY": "security-objective-integrity",
    "PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY": (
        "security-objective-availability"
    ),
    "CNSS_AVAILABILITY_RATING": "security-objective-availability",
    "CNSS_CONFIDENTIALITY_RATING": "security-objective-confidentiality",
    "CNSS_INTEGRITY_RATING": "security-objective-integrity",
}

ARCHER_SELECT_ID_CONTAINER_KEYS = {
    "valuelistid",
    "valuelistids",
    "valueslistid",
    "valueslistids",
}

SECURITY_OBJECTIVE_FIELDS = {
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
}
REVIEWED_LEGACY_SECURITY_VALUES = {
    "Legacy LOE A",
    "Legacy LOE B",
    "Legacy LOE C",
    "Legacy LOE D",
    "Legacy LOE A + DFARS",
    "Legacy LOE B + DFARS",
    "Legacy LOE C + DFARS",
    "Legacy LOE D + DFARS",
}

STATUS_STATE_CROSSWALK = {
    "operational": "operational",
    "under-development": "under-development",
    "decommissioned": "disposition",
    # OSCAL has no reauthorization state. `other` is the lossless catch-all,
    # and build_element_instances adds the required explanatory remark.
    "reauthorize": "other",
}


def _to_python(value):
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if hasattr(value, "as_list"):
        return value.as_list()
    return value


def _parse_source_json(record):
    value = _to_python(record["CURATED_JSON"])
    if value is None:
        return {}
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, dict):
        return value
    raise TypeError("CURATED_JSON must resolve to an object")


def resolve_json_path(source_obj, field_path):
    if not field_path:
        return None
    if isinstance(source_obj, dict) and field_path in source_obj:
        return _to_python(source_obj[field_path])

    current = source_obj
    tokens = [token for token in re.split(r"[./]", str(field_path)) if token]
    for token in tokens:
        current = _to_python(current)
        if isinstance(current, dict):
            if token in current:
                current = current[token]
            elif token.upper() in current:
                current = current[token.upper()]
            else:
                return None
        elif isinstance(current, list) and token.isdigit():
            index = int(token)
            if index >= len(current):
                return None
            current = current[index]
        else:
            return None
    return _to_python(current)


def _has_value(value):
    return value not in (None, "", [], {})


def _stable_property_name(source_field):
    return re.sub(r"[^a-z0-9]+", "-", source_field.lower()).strip("-")


def _deterministic_uuid(*parts):
    identity = "|".join(str(part) for part in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, identity))


def _deterministic_hash(*parts):
    identity = "|".join(str(part) for part in parts)
    return hashlib.md5(identity.encode("utf-8")).hexdigest()


def _extract_reference_ids(value):
    value = _to_python(value)
    if isinstance(value, dict):
        for key in (
            "UserList",
            "ValuesListIds",
            "ValueListIds",
            "ContentIds",
            "Ids",
            "Value",
        ):
            if key in value and _has_value(value[key]):
                return _extract_reference_ids(value[key])
        for key, item in value.items():
            key_token = re.sub(r"[^a-z0-9]+", "", str(key).lower())
            if (
                key_token in ARCHER_SELECT_ID_CONTAINER_KEYS
                and _has_value(item)
            ):
                return _extract_reference_ids(item)
        return value
    if isinstance(value, list):
        flattened = []
        for item in value:
            extracted = _extract_reference_ids(item)
            if isinstance(extracted, list):
                flattened.extend(extracted)
            else:
                flattened.append(extracted)
        return flattened
    return value


def _contains_archer_select_id_container(value):
    value = _to_python(value)
    if isinstance(value, dict):
        for key, item in value.items():
            key_token = re.sub(r"[^a-z0-9]+", "", str(key).lower())
            if key_token in ARCHER_SELECT_ID_CONTAINER_KEYS:
                return True
            if _contains_archer_select_id_container(item):
                return True
    elif isinstance(value, list):
        return any(_contains_archer_select_id_container(item) for item in value)
    return False


def resolve_archer_select_value(value):
    strict_select_ids = _contains_archer_select_id_container(value)
    extracted = _extract_reference_ids(value)

    def resolve_one(item):
        if item is None:
            return None
        item = _to_python(item)
        if isinstance(item, (dict, list, bool)):
            if strict_select_ids:
                raise ValueError("Archer select-value container is invalid")
            return item
        key = str(item).strip()
        if strict_select_ids:
            if key not in ARCHER_VALUE_LOOKUP or not _has_value(
                ARCHER_VALUE_LOOKUP[key]
            ):
                raise ValueError("Archer select-value ID is unresolved")
            return ARCHER_VALUE_LOOKUP[key]
        return ARCHER_VALUE_LOOKUP.get(key, item)

    if isinstance(extracted, list):
        resolved = [resolve_one(item) for item in extracted]
        return [item for item in resolved if item is not None]
    return resolve_one(extracted)


def _oscal_property_values(value):
    values = value if isinstance(value, list) else [value]
    normalized = []

    for item in values:
        item = _to_python(item)
        if isinstance(item, (dict, list)) or item is None:
            raise ValueError(
                "OSCAL property value must resolve to a scalar"
            )

        if isinstance(item, bool):
            text = "true" if item else "false"
        else:
            text = str(item).strip()

        if not text or text.lower() in {
            "nan",
            "inf",
            "+inf",
            "-inf",
        }:
            raise ValueError(
                "OSCAL property value must be a nonblank finite scalar"
            )
        normalized.append(text)

    return normalized


def _append_unique_collection_instance(instances, instance):
    instance_key = instance["instance_key"]
    for existing in instances:
        if existing["instance_key"] != instance_key:
            continue
        if existing["payload"] != instance["payload"]:
            raise ValueError(
                "Collection identity resolves to conflicting payloads"
            )
        return
    instances.append(instance)


def _source_value_instance_key(source_field, value):
    return (
        source_field
        + ":"
        + _deterministic_hash(
            "source-field-value-v1",
            source_field,
            value,
        )
    )


def _value_instance_key(value):
    return _deterministic_hash("value-v1", value)


def _component_mapping_type(mapping_row):
    source_field = str(mapping_row.get("SOURCE_FIELD_NAME") or "").strip()
    component_type = COMPONENT_SOURCE_TYPES.get(source_field)
    if component_type is None:
        raise ValueError("Component mapping source is not approved")

    mapping_type = str(
        mapping_row.get("MAPPING_TYPE") or ""
    ).strip().lower()
    if mapping_type != "reference":
        raise ValueError("Component mapping must use Reference type")

    evidence_text = " ".join(
        str(mapping_row.get(column) or "")
        for column in (
            "TRANSFORMATION_LOGIC",
            "NOTES",
            "NOTE",
            "COMMENTS",
            "COMMENT",
        )
    ).lower()
    declared_types = {
        candidate
        for candidate in set(COMPONENT_SOURCE_TYPES.values())
        if re.search(r"\b" + re.escape(candidate) + r"\b", evidence_text)
    }
    if declared_types != {component_type}:
        raise ValueError(
            "Component mapping type signal does not match approved contract"
        )
    return component_type


def _canonical_component_content_id(value):
    value = _to_python(value)
    if isinstance(value, (bool, dict, list)) or value is None:
        raise ValueError("Component reference has invalid ContentId")
    content_id = str(value).strip()
    if not content_id or content_id.lower() in {
        "nan",
        "inf",
        "+inf",
        "-inf",
    }:
        raise ValueError("Component reference has invalid ContentId")
    return content_id


def _component_reference_content_ids(value):
    value = _to_python(value)
    members = value if isinstance(value, list) else [value]
    content_ids = []
    for member in members:
        member = _to_python(member)
        if isinstance(member, dict):
            if "ContentId" not in member:
                raise ValueError("Component reference is missing ContentId")
            content_id = _canonical_component_content_id(
                member["ContentId"]
            )
        else:
            content_id = _canonical_component_content_id(member)
        content_ids.append(content_id)
    return content_ids


def _component_row_value(row, name):
    try:
        return row[name]
    except (KeyError, TypeError, IndexError):
        pass
    values = row.as_dict(recursive=True) if hasattr(row, "as_dict") else {}
    expected = re.sub(r"[^A-Z0-9]", "", str(name).upper())
    for key, value in values.items():
        normalized = re.sub(r"[^A-Z0-9]", "", str(key).upper())
        if normalized == expected:
            return value
    return None


def _component_text(value, label, required):
    if value is None:
        if required:
            raise ValueError(f"Component hydration {label} is missing")
        return None
    if not isinstance(value, str):
        raise ValueError(f"Component hydration {label} must be text")
    normalized = value.strip()
    if not normalized:
        if required:
            raise ValueError(f"Component hydration {label} is blank")
        return None
    return normalized


def _hydrate_component_payload(
    component_type,
    content_id,
    hydration_lookups,
):
    payload = {"type": component_type}
    contract = COMPONENT_HYDRATION_CONTRACT.get(component_type)
    if contract is None:
        return payload
    if not isinstance(hydration_lookups, dict):
        raise ValueError("Component hydration lookup is unavailable")
    type_lookup = hydration_lookups.get(component_type)
    if not isinstance(type_lookup, dict) or content_id not in type_lookup:
        raise ValueError("Component hydration lookup record is missing")
    lookup_payload = type_lookup[content_id]
    if not isinstance(lookup_payload, dict):
        raise ValueError("Component hydration lookup payload is invalid")

    payload["title"] = _component_text(
        lookup_payload.get("title"),
        "title",
        required=True,
    )
    description = _component_text(
        lookup_payload.get("description"),
        "description",
        required=(component_type == "software"),
    )
    if description is not None:
        payload["description"] = description
    return payload


def _build_component_hydration_lookups(
    source_dataframe,
    mapping_rows,
    hydration_source_dfs,
):
    if CONFIG.get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Component hydration must be built before guarded writes"
        )
    if not isinstance(hydration_source_dfs, dict):
        raise RuntimeError("Component hydration sources are unavailable")
    if set(hydration_source_dfs) != set(COMPONENT_HYDRATION_CONTRACT):
        raise RuntimeError("Component hydration source contract is incomplete")
    source_contract = globals().get("COMPONENT_HYDRATION_SOURCE_CONTRACT")
    if source_contract != COMPONENT_HYDRATION_CONTRACT:
        raise RuntimeError("Component hydration source contract has drifted")

    component_rows_by_field = {}
    unexpected_component_rows = 0
    for row in mapping_rows:
        source_field = str(row.get("SOURCE_FIELD_NAME") or "").strip()
        if source_field in COMPONENT_SOURCE_TYPES:
            component_rows_by_field.setdefault(source_field, []).append(row)
        else:
            unexpected_component_rows += 1

    if unexpected_component_rows:
        raise RuntimeError("Canonical component mapping contract has drifted")
    if set(component_rows_by_field) != set(COMPONENT_SOURCE_TYPES):
        raise RuntimeError("Canonical component mapping contract has drifted")
    for source_field, rows in component_rows_by_field.items():
        if len(rows) != 1:
            raise RuntimeError(
                "Canonical component mapping is duplicated"
            )
        if _component_mapping_type(rows[0]) != COMPONENT_SOURCE_TYPES[source_field]:
            raise RuntimeError("Canonical component mapping type drifted")

    from snowflake.snowpark.functions import (
        col as hydration_col,
        count as hydration_count,
        count_distinct as hydration_count_distinct,
        length as hydration_length,
        lit as hydration_lit,
        parse_json as hydration_parse_json,
        trim as hydration_trim,
        typeof as hydration_typeof,
        upper as hydration_upper,
        when as hydration_when,
    )

    def hydration_nonblank(column):
        return (
            column.is_not_null()
            & (
                hydration_length(hydration_trim(column.cast("string")))
                > hydration_lit(0)
            )
        )

    source_columns = {
        str(name).strip().upper(): name for name in source_dataframe.columns
    }
    if not {"SOURCE_RECORD_ID", "CURATED_JSON"}.issubset(source_columns):
        raise RuntimeError("Component hydration source columns are missing")

    source_json = hydration_parse_json(
        hydration_col(source_columns["CURATED_JSON"]).cast("string")
    )
    route_frames = []
    scalar_types = (
        "VARCHAR",
        "INTEGER",
        "DECIMAL",
        "NUMBER",
        "FIXED",
        "REAL",
        "DOUBLE",
    )
    for source_field, component_type in (
        COMPONENT_HYDRATION_SOURCE_FIELDS.items()
    ):
        roots_df = source_dataframe.select(
            hydration_lit(source_field).alias("_SOURCE_FIELD"),
            hydration_lit(component_type).alias("_COMPONENT_TYPE"),
            source_json.getItem(source_field).alias("_REFERENCE_ROOT"),
        )
        invalid_roots = roots_df.filter(
            hydration_col("_REFERENCE_ROOT").is_not_null()
            & ~hydration_upper(
                hydration_typeof(hydration_col("_REFERENCE_ROOT"))
            ).isin("ARRAY", "NULL_VALUE")
        ).count()
        if invalid_roots:
            raise RuntimeError(
                "Approved component reference root has invalid shape"
            )

        members_df = roots_df.filter(
            hydration_upper(
                hydration_typeof(hydration_col("_REFERENCE_ROOT"))
            )
            == hydration_lit("ARRAY")
        ).join_table_function(
            "flatten",
            hydration_col("_REFERENCE_ROOT"),
        )
        member_value = hydration_col("VALUE")
        member_type = hydration_upper(hydration_typeof(member_value))
        object_content_id = member_value.getItem("ContentId")
        object_id_type = hydration_upper(hydration_typeof(object_content_id))
        component_id_value = (
            hydration_when(
                (member_type == hydration_lit("OBJECT"))
                & object_id_type.isin(*scalar_types),
                object_content_id,
            )
            .when(member_type.isin(*scalar_types), member_value)
            .otherwise(hydration_lit(None))
        )
        member_ids_df = members_df.select(
            hydration_col("_SOURCE_FIELD"),
            hydration_col("_COMPONENT_TYPE"),
            hydration_trim(component_id_value.cast("string")).alias(
                "_COMPONENT_ID"
            ),
        )
        invalid_members = member_ids_df.filter(
            ~hydration_nonblank(hydration_col("_COMPONENT_ID"))
        ).count()
        if invalid_members:
            raise RuntimeError(
                "Approved component reference contains an invalid ContentId"
            )
        route_frames.append(member_ids_df)

    component_routes_df = route_frames[0]
    for route_frame in route_frames[1:]:
        component_routes_df = component_routes_df.union_all(route_frame)

    type_collisions = (
        component_routes_df.select(
            hydration_col("_COMPONENT_TYPE"),
            hydration_col("_COMPONENT_ID"),
        )
        .distinct()
        .group_by(hydration_col("_COMPONENT_ID"))
        .agg(
            hydration_count_distinct(
                hydration_col("_COMPONENT_TYPE")
            ).alias("_TYPE_COUNT")
        )
        .filter(hydration_col("_TYPE_COUNT") > hydration_lit(1))
        .count()
    )
    if type_collisions:
        raise RuntimeError("Component hydration identity has a type collision")

    hydration_lookups = {}
    for component_type, contract in COMPONENT_HYDRATION_CONTRACT.items():
        routed_ids_df = (
            component_routes_df.filter(
                hydration_col("_COMPONENT_TYPE")
                == hydration_lit(component_type)
            )
            .select(
                hydration_col("_COMPONENT_ID").alias("_ROUTE_ID")
            )
            .distinct()
        )
        lookup_source_df = hydration_source_dfs[component_type]
        lookup_columns = {
            str(name).strip().upper(): name
            for name in lookup_source_df.columns
        }
        if not {"CONTENT_ID", "CURATED_JSON"}.issubset(lookup_columns):
            raise RuntimeError(
                "Approved component lookup source columns are missing"
            )
        lookup_rows_df = lookup_source_df.select(
            hydration_trim(
                hydration_col(lookup_columns["CONTENT_ID"]).cast("string")
            ).alias("_LOOKUP_ID"),
            hydration_parse_json(
                hydration_col(lookup_columns["CURATED_JSON"]).cast("string")
            ).alias("_LOOKUP_JSON"),
        )
        key_summary = lookup_rows_df.agg(
            hydration_count(hydration_lit(1)).alias("_TOTAL_ROWS"),
            hydration_count(
                hydration_when(
                    hydration_nonblank(hydration_col("_LOOKUP_ID")),
                    hydration_lit(1),
                )
            ).alias("_NONBLANK_ROWS"),
            hydration_count_distinct(
                hydration_col("_LOOKUP_ID")
            ).alias("_DISTINCT_IDS"),
            hydration_count(
                hydration_when(
                    hydration_upper(
                        hydration_typeof(hydration_col("_LOOKUP_JSON"))
                    )
                    != hydration_lit("OBJECT"),
                    hydration_lit(1),
                )
            ).alias("_INVALID_JSON_ROWS"),
        ).collect()[0]
        total_rows = int(_component_row_value(key_summary, "_TOTAL_ROWS") or 0)
        nonblank_rows = int(
            _component_row_value(key_summary, "_NONBLANK_ROWS") or 0
        )
        distinct_ids = int(
            _component_row_value(key_summary, "_DISTINCT_IDS") or 0
        )
        invalid_lookup_json_rows = int(
            _component_row_value(key_summary, "_INVALID_JSON_ROWS") or 0
        )
        if total_rows != nonblank_rows:
            raise RuntimeError(
                "Approved component lookup contains a missing ContentId"
            )
        if nonblank_rows != distinct_ids:
            raise RuntimeError(
                "Approved component lookup contains duplicate ContentId values"
            )
        if invalid_lookup_json_rows:
            raise RuntimeError(
                "Approved component lookup contains invalid curated JSON"
            )

        matched_df = routed_ids_df.join(
            lookup_rows_df,
            routed_ids_df["_ROUTE_ID"] == lookup_rows_df["_LOOKUP_ID"],
            "left",
        )
        title_value = hydration_col("_LOOKUP_JSON").getItem(
            contract["title_field"]
        )
        description_value = hydration_col("_LOOKUP_JSON").getItem(
            contract["description_field"]
        )
        title_is_valid = (
            hydration_upper(hydration_typeof(title_value))
            == hydration_lit("VARCHAR")
        ) & hydration_nonblank(title_value)
        description_type = hydration_upper(
            hydration_typeof(description_value)
        )
        description_is_text = description_type == hydration_lit("VARCHAR")
        description_is_nonblank = (
            description_is_text & hydration_nonblank(description_value)
        )
        if component_type == "software":
            invalid_description_condition = ~description_is_nonblank
        else:
            description_is_absent = (
                description_value.is_null()
                | (description_type == hydration_lit("NULL_VALUE"))
                | (description_is_text & ~hydration_nonblank(description_value))
            )
            invalid_description_condition = ~(
                description_is_absent | description_is_nonblank
            )

        match_summary = matched_df.agg(
            hydration_count(hydration_lit(1)).alias("_MATCHED_ROWS"),
            hydration_count(
                hydration_when(
                    hydration_col("_LOOKUP_ID").is_null(),
                    hydration_lit(1),
                )
            ).alias("_MISSING_LOOKUP_ROWS"),
            hydration_count(
                hydration_when(~title_is_valid, hydration_lit(1))
            ).alias("_INVALID_TITLE_ROWS"),
            hydration_count(
                hydration_when(
                    invalid_description_condition,
                    hydration_lit(1),
                )
            ).alias("_INVALID_DESCRIPTION_ROWS"),
        ).collect()[0]
        routed_id_count = int(
            _component_row_value(match_summary, "_MATCHED_ROWS") or 0
        )
        missing_lookup_rows = int(
            _component_row_value(match_summary, "_MISSING_LOOKUP_ROWS") or 0
        )
        invalid_title_rows = int(
            _component_row_value(match_summary, "_INVALID_TITLE_ROWS") or 0
        )
        invalid_description_rows = int(
            _component_row_value(
                match_summary,
                "_INVALID_DESCRIPTION_ROWS",
            )
            or 0
        )
        if missing_lookup_rows:
            raise RuntimeError(
                "Approved component hydration lookup record is missing"
            )
        if invalid_title_rows:
            raise RuntimeError(
                "Approved component hydration title is missing or invalid"
            )
        if invalid_description_rows:
            raise RuntimeError(
                "Approved component hydration description is invalid"
            )

        projected_df = matched_df.select(
            hydration_col("_ROUTE_ID").alias("COMPONENT_ID"),
            hydration_trim(title_value.cast("string")).alias("TITLE"),
            hydration_when(
                description_is_nonblank,
                hydration_trim(description_value.cast("string")),
            )
            .otherwise(hydration_lit(None))
            .alias("DESCRIPTION"),
        )
        type_lookup = {}
        for row in projected_df.to_local_iterator():
            content_id = _canonical_component_content_id(
                _component_row_value(row, "COMPONENT_ID")
            )
            if content_id in type_lookup:
                raise RuntimeError(
                    "Component hydration lookup contains duplicate routed IDs"
                )
            type_lookup[content_id] = {
                "title": _component_row_value(row, "TITLE"),
                "description": _component_row_value(row, "DESCRIPTION"),
            }
        if len(type_lookup) != routed_id_count:
            raise RuntimeError(
                "Component hydration lookup collection is incomplete"
            )
        hydration_lookups[component_type] = type_lookup

    print(
        "Component hydration lookup rows:",
        sum(len(type_lookup) for type_lookup in hydration_lookups.values()),
    )
    for component_type in sorted(hydration_lookups):
        type_lookup = hydration_lookups[component_type]
        print(
            f"Component hydration {component_type} rows:",
            len(type_lookup),
        )
        print(
            f"Component hydration {component_type} descriptions:",
            sum(
                1
                for payload in type_lookup.values()
                if payload.get("description") is not None
            ),
        )
    return hydration_lookups


def _build_component_instances(
    source_obj,
    source_record_id,
    mapping_rows,
    component_hydration_lookups,
):
    components = {}
    for mapping_row in mapping_rows:
        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        source_value = resolve_json_path(source_obj, source_field)
        transformed = apply_mapping_transform(
            mapping_row,
            source_value,
            source_record_id,
        )
        if transformed is SKIP_VALUE:
            continue
        component_type = _component_mapping_type(mapping_row)
        is_approved_hydration_route = (
            COMPONENT_HYDRATION_SOURCE_FIELDS.get(source_field)
            == component_type
        )
        for content_id in _component_reference_content_ids(transformed):
            existing = components.get(content_id)
            if existing is None:
                components[content_id] = {
                    "type": component_type,
                    "hydrate": is_approved_hydration_route,
                }
                continue
            if existing["type"] != component_type:
                raise ValueError(
                    "Component ContentId resolves to conflicting types"
                )
            existing["hydrate"] = (
                existing["hydrate"] or is_approved_hydration_route
            )

    instances = []
    for content_id in sorted(components):
        component = components[content_id]
        if component["hydrate"] and component_hydration_lookups is not None:
            payload = _hydrate_component_payload(
                component["type"],
                content_id,
                component_hydration_lookups,
            )
        else:
            payload = {"type": component["type"]}
        instances.append(
            {
                "instance_key": content_id,
                "payload": payload,
                "parent_instance_key": None,
            }
        )
    return instances


def transform_fips_199(value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    normalized = []
    for item in values:
        if item is None:
            continue
        key = str(item).strip()
        label = FIPS_199_VALUE_LOOKUP.get(key)
        if label is None:
            candidate = str(ARCHER_VALUE_LOOKUP.get(key, item)).strip().lower()
            if candidate in {"low", "moderate", "high"}:
                label = candidate
        if label is not None:
            normalized.append(label)
    if not normalized:
        return None
    return normalized[0] if len(normalized) == 1 else normalized


def _single_archer_label(value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    values = [item for item in values if item is not None]
    if len(values) != 1:
        return None

    item = values[0]
    if isinstance(item, (dict, list)):
        return None

    key = str(item).strip()
    if not key:
        return None

    resolved = ARCHER_VALUE_LOOKUP.get(key)
    if resolved is not None:
        label = str(resolved).strip()
        return label or None

    # An already resolved textual label is safe to preserve. An unknown
    # numeric ID is not: it must be added to ARCHER_META_VALUE first.
    if isinstance(item, str) and not key.isdigit():
        return key
    return None


def transform_security_objective(value):
    normalized = transform_fips_199(value)
    if isinstance(normalized, list):
        if len(normalized) != 1:
            raise ValueError(
                "Security objective resolved to multiple FIPS values"
            )
        normalized = normalized[0]
    if _has_value(normalized):
        return str(normalized)

    label = _single_archer_label(value)
    if label is None:
        raise ValueError(
            "Security objective contains an unresolved or multi-value label"
        )

    # OSCAL models these objectives as strings. Preserve only the reviewed
    # legacy LOE labels instead of accepting arbitrary text or inventing an
    # unapproved Low/Moderate/High equivalence.
    if label not in REVIEWED_LEGACY_SECURITY_VALUES:
        raise ValueError("Security objective contains an unreviewed label")
    return label


def _is_complete_security_impact_payload(payload):
    return all(
        isinstance(payload.get(field_name), str)
        and bool(payload[field_name].strip())
        for field_name in SECURITY_OBJECTIVE_FIELDS
    )


def transform_status_state(value):
    label = _single_archer_label(value)
    if label is None:
        raise ValueError("Status contains an unresolved or multi-value label")

    source_token = _stable_property_name(label)
    target_state = STATUS_STATE_CROSSWALK.get(source_token)
    if target_state is None:
        raise ValueError(
            "Status label is not present in the approved OSCAL crosswalk"
        )

    payload = {"state": target_state}
    if target_state == "other":
        payload["remarks"] = (
            "Mapped from Archer operational status: " + label + "."
        )
    return payload


def transform_document_identifier(value):
    value = _to_python(value)
    if isinstance(value, (bool, dict, list)) or value is None:
        raise ValueError("Document identifier must be a single scalar value")

    identifier = str(value).strip()
    if not identifier or identifier.lower() in {
        "nan",
        "inf",
        "+inf",
        "-inf",
    }:
        raise ValueError("Document identifier is empty or non-finite")
    return identifier


def _preserve_metadata_timestamp(value, target_field):
    value = _to_python(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"Metadata {target_field} must be a nonblank source string"
        )
    return value


def transform_published(value):
    return _preserve_metadata_timestamp(value, "published")


def transform_last_modified(value):
    return _preserve_metadata_timestamp(value, "last-modified")


def transform_metadata_title(value):
    value = _to_python(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Metadata title source must be a nonblank string")
    return value


def transform_approved_text(value):
    value = _to_python(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Approved OSCAL text source must be nonblank text")
    return value


def _is_executable_responsible_party_mapping(mapping_row):
    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    if source_field not in RESPONSIBLE_PARTY_ROLE_DEFINITIONS:
        return False

    mapping_type = _mapping_type_token(mapping_row)
    status = str(mapping_row.get("STATUS") or "").strip().lower()
    if "tbd" in mapping_type or "more information" in status:
        return False
    if mapping_type != "transform":
        raise ValueError("Responsible-party mapping type must be Transform")
    return True


def _active_responsible_party_role_instances(source_obj, source_record_id):
    instances = []
    emitted_role_ids = set()
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
        RESPONSIBLE_PARTIES_ELEMENT_PATH,
        [],
    )
    for mapping_row in mapping_rows:
        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        if not _is_executable_responsible_party_mapping(mapping_row):
            continue
        definition = RESPONSIBLE_PARTY_ROLE_DEFINITIONS.get(source_field)

        source_value = resolve_json_path(source_obj, source_field)
        if not _has_value(source_value):
            continue
        if not _party_uuid_values(source_record_id, source_value):
            continue

        role_id = definition["id"]
        if role_id in emitted_role_ids:
            continue
        emitted_role_ids.add(role_id)
        instances.append(
            {
                "instance_key": role_id,
                "payload": {
                    "id": role_id,
                    "title": definition["title"],
                },
                "parent_instance_key": None,
            }
        )
    return instances


def _party_reference_identifier(item):
    item = _to_python(item)
    if isinstance(item, dict):
        identifier = (
            item.get("Id")
            or item.get("UserId")
            or item.get("ContentId")
        )
        if not _has_value(identifier):
            raise ValueError(
                "Responsible-party reference has no stable identifier"
            )
        return str(identifier).strip()
    if isinstance(item, (list, bool)) or item is None:
        raise ValueError("Responsible-party reference identifier is invalid")
    identifier = str(item).strip()
    if not identifier:
        raise ValueError("Responsible-party reference identifier is empty")
    return identifier


def _party_uuid(source_record_id, identifier):
    return _deterministic_uuid(
        CONFIG["SOURCE_SYSTEM_NAME"],
        source_record_id,
        "party",
        identifier,
    )


def _party_uuid_values(source_record_id, value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    party_uuids = []
    for item in values:
        if item is None:
            continue
        party_uuid = _party_uuid(
            source_record_id,
            _party_reference_identifier(item),
        )
        if party_uuid not in party_uuids:
            party_uuids.append(party_uuid)
    return party_uuids


def _active_responsible_party_instances(source_obj, source_record_id):
    instances = []
    emitted_party_uuids = set()
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
        RESPONSIBLE_PARTIES_ELEMENT_PATH,
        [],
    )
    for mapping_row in mapping_rows:
        if not _is_executable_responsible_party_mapping(mapping_row):
            continue

        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        source_value = resolve_json_path(source_obj, source_field)
        if not _has_value(source_value):
            continue

        for party_uuid in _party_uuid_values(source_record_id, source_value):
            if party_uuid in emitted_party_uuids:
                continue
            emitted_party_uuids.add(party_uuid)
            instances.append(
                {
                    "instance_key": party_uuid,
                    "payload": {
                        "uuid": party_uuid,
                        "type": APPROVED_RESPONSIBLE_PARTY_TYPE,
                    },
                    "parent_instance_key": None,
                }
            )
    return instances


def _active_responsible_party_assignment_instances(
    source_obj,
    source_record_id,
):
    assignments_by_role = {}
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
        RESPONSIBLE_PARTIES_ELEMENT_PATH,
        [],
    )
    for mapping_row in mapping_rows:
        if not _is_executable_responsible_party_mapping(mapping_row):
            continue

        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        source_value = resolve_json_path(source_obj, source_field)
        if not _has_value(source_value):
            continue

        party_uuids = _party_uuid_values(source_record_id, source_value)
        if not party_uuids:
            continue

        role_id = RESPONSIBLE_PARTY_ROLE_IDS[source_field]
        assignment = assignments_by_role.get(role_id)
        if assignment is None:
            assignment = {
                "instance_key": source_field,
                "payload": {
                    "role-id": role_id,
                    "party-uuids": [],
                },
                "parent_instance_key": None,
            }
            assignments_by_role[role_id] = assignment

        emitted_uuids = assignment["payload"]["party-uuids"]
        for party_uuid in party_uuids:
            if party_uuid not in emitted_uuids:
                emitted_uuids.append(party_uuid)

    return list(assignments_by_role.values())


def transform_responsible_party(source_record_id, source_field, value):
    role_id = RESPONSIBLE_PARTY_ROLE_IDS.get(source_field)
    if role_id is None:
        return SKIP_VALUE
    party_uuids = _party_uuid_values(source_record_id, value)
    if not party_uuids:
        return SKIP_VALUE
    return {"role-id": role_id, "party-uuids": party_uuids}


def _target_field_name(mapping_row):
    explicit = mapping_row.get("OSCAL_FIELD_NAME")
    if explicit:
        return str(explicit).strip().replace("[]", "")
    return _stable_property_name(str(mapping_row["SOURCE_FIELD_NAME"]))


def _mapping_type_token(mapping_row):
    return re.sub(
        r"[^a-z0-9]+",
        "-",
        str(mapping_row.get("MAPPING_TYPE") or "Direct").strip().lower(),
    ).strip("-")


def _validate_approved_text_mapping(mapping_row):
    source_field = str(mapping_row.get("SOURCE_FIELD_NAME") or "").strip()
    contract = APPROVED_TEXT_MAPPING_CONTRACTS.get(source_field)
    if contract is None:
        return False
    if (
        str(mapping_row.get("OWNER_ELEMENT_PATH") or "").strip()
        != contract["owner_path"]
        or _target_field_name(mapping_row) != contract["target_field"]
        or _mapping_type_token(mapping_row) != "direct"
    ):
        raise ValueError("Approved OSCAL text mapping contract does not match")
    return True


def _validate_security_objective_mapping(mapping_row):
    source_field = str(mapping_row.get("SOURCE_FIELD_NAME") or "").strip()
    owner_path = str(mapping_row.get("OWNER_ELEMENT_PATH") or "").strip()
    target_field = _target_field_name(mapping_row)
    expected_target = SECURITY_IMPACT_SOURCE_OBJECTIVES.get(source_field)

    if expected_target is None:
        if owner_path == SECURITY_IMPACT_ELEMENT_PATH:
            raise ValueError("Security-impact mapping source is not approved")
        return False
    if (
        owner_path != SECURITY_IMPACT_ELEMENT_PATH
        or target_field != expected_target
        or _mapping_type_token(mapping_row)
        not in {"direct", "transform", "direct-transform"}
    ):
        raise ValueError("Security-impact source/target contract does not match")
    return True


def _validate_exact_mapping(
    mapping_row,
    source_field,
    owner_path,
    target_field,
    mapping_type,
    label,
):
    if (
        str(mapping_row.get("SOURCE_FIELD_NAME") or "").strip()
        != source_field
        or str(mapping_row.get("OWNER_ELEMENT_PATH") or "").strip()
        != owner_path
        or _target_field_name(mapping_row) != target_field
        or _mapping_type_token(mapping_row) != mapping_type
    ):
        raise ValueError(f"{label} mapping contract does not match")


def _resolve_metadata_timestamp_cluster(
    source_obj,
    mapping_rows,
    target_field,
):
    cluster_rows = [
        row
        for row in mapping_rows
        if _target_field_name(row) == target_field
    ]
    resolved_values = []

    for mapping_row in cluster_rows:
        mapping_type = str(
            mapping_row.get("MAPPING_TYPE") or ""
        ).strip().lower()
        if mapping_type != "transform":
            raise ValueError(
                f"Metadata {target_field} mapping type must be Transform"
            )

        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        source_value = resolve_json_path(source_obj, source_field)
        if not _has_value(source_value):
            continue

        if target_field == "published":
            transformed = transform_published(source_value)
        else:
            transformed = transform_last_modified(source_value)

        if transformed not in resolved_values:
            resolved_values.append(transformed)

    if len(resolved_values) > 1:
        raise ValueError(
            f"Conflicting populated metadata {target_field} sources"
        )
    if not resolved_values:
        return SKIP_VALUE
    return resolved_values[0]


def _mapping_handler_for_row(mapping_row):
    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    mapping_type = _mapping_type_token(mapping_row)
    status = str(mapping_row.get("STATUS") or "").lower()

    if source_field in TRANSIENT_SOURCE_FIELDS:
        return "skip"
    if "tbd" in mapping_type or "more information" in status:
        return "skip"

    owner_path = str(mapping_row.get("OWNER_ELEMENT_PATH") or "").strip()
    target_field = _target_field_name(mapping_row)

    if _validate_approved_text_mapping(mapping_row):
        handler = "approved-text"
    elif (
        source_field in SECURITY_IMPACT_SOURCE_OBJECTIVES
        or owner_path == SECURITY_IMPACT_ELEMENT_PATH
    ):
        _validate_security_objective_mapping(mapping_row)
        handler = "security-objective"
    elif source_field == "OPERATIONAL_STATUS" or (
        owner_path == STATUS_ELEMENT_PATH and target_field == "state"
    ):
        _validate_exact_mapping(
            mapping_row,
            "OPERATIONAL_STATUS",
            STATUS_ELEMENT_PATH,
            "state",
            "transform",
            "System status",
        )
        handler = "status-state"
    elif source_field == "AUTHORIZATION_COMMENTS" or (
        owner_path == STATUS_ELEMENT_PATH and target_field == "remarks"
    ):
        _validate_exact_mapping(
            mapping_row,
            "AUTHORIZATION_COMMENTS",
            STATUS_ELEMENT_PATH,
            "remarks",
            "extension-property",
            "Authorization comments",
        )
        handler = "approved-text"
    elif owner_path == METADATA_ELEMENT_PATH and target_field == "published":
        if mapping_type != "transform":
            raise ValueError("Metadata published mapping type must be Transform")
        handler = "published"
    elif (
        owner_path == METADATA_ELEMENT_PATH and target_field == "last-modified"
    ):
        if mapping_type != "transform":
            raise ValueError(
                "Metadata last-modified mapping type must be Transform"
            )
        handler = "last-modified"
    elif owner_path == DOCUMENT_IDS_ELEMENT_PATH and target_field == "identifier":
        _validate_exact_mapping(
            mapping_row,
            "TRACKING_ID",
            DOCUMENT_IDS_ELEMENT_PATH,
            "identifier",
            "direct",
            "Document identifier",
        )
        handler = "document-identifier"
    elif owner_path == SYSTEM_IDS_ELEMENT_PATH and target_field == "id":
        _validate_exact_mapping(
            mapping_row,
            "SAP_ID",
            SYSTEM_IDS_ELEMENT_PATH,
            "id",
            "direct",
            "System identifier",
        )
        handler = "direct"
    elif source_field in RESPONSIBLE_PARTY_ROLE_IDS:
        if not _is_executable_responsible_party_mapping(mapping_row):
            return "skip"
        handler = "responsible-party"
    elif owner_path == COMPONENTS_ELEMENT_PATH:
        _component_mapping_type(mapping_row)
        handler = "component-reference"
    elif owner_path == SYSTEM_CHARACTERISTICS_PROPS_ELEMENT_PATH:
        if mapping_type != "extension-property":
            raise ValueError(
                "System-characteristics property mapping type must be "
                "Extension Property"
            )
        handler = "governed-property"
    elif mapping_type == "direct":
        handler = "direct"
    else:
        safe_metadata = {
            "source_field": source_field,
            "owner_path": owner_path,
            "target_field": target_field,
            "mapping_type": mapping_type,
        }
        safe_metadata = {
            key: re.sub(r"[\r\n\t]+", " ", str(value)).strip()
            for key, value in safe_metadata.items()
        }
        raise ValueError(
            "Mapping has no approved transformation handler: "
            + "; ".join(
                key + "=" + safe_metadata[key]
                for key in (
                    "source_field",
                    "owner_path",
                    "target_field",
                    "mapping_type",
                )
            )
        )
    return handler


def apply_mapping_transform(mapping_row, value, source_record_id):
    # A configured row with no source value emits nothing. Keep this omission
    # ahead of strict row classification so known no-source mappings do not
    # make an otherwise valid run fail.
    if not _has_value(value):
        return SKIP_VALUE

    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    handler = _mapping_handler_for_row(mapping_row)
    if handler == "skip":
        return SKIP_VALUE

    if handler == "approved-text":
        return transform_approved_text(value)
    if handler == "responsible-party":
        return transform_responsible_party(
            source_record_id, source_field, value
        )
    if handler == "security-objective":
        return transform_security_objective(value)
    if handler == "status-state":
        return transform_status_state(value)
    if handler == "published":
        return transform_published(value)
    if handler == "last-modified":
        return transform_last_modified(value)
    if handler == "document-identifier":
        return transform_document_identifier(value)
    if handler == "governed-property":
        transformed = resolve_archer_select_value(value)
        return transformed if _has_value(transformed) else SKIP_VALUE
    if handler in {"component-reference", "direct"}:
        return _to_python(value)
    raise RuntimeError("Approved mapping handler did not return a value")


def build_element_instances(
    source_obj,
    source_record_id,
    element_path,
    mapping_rows,
    component_hydration_lookups=None,
):
    is_collection = "[]" in element_path
    instances = []
    aggregate_payload = {}
    resolved_cluster_fields = set()

    if element_path == METADATA_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_instances(
            source_obj,
            source_record_id,
        )

    if element_path == METADATA_ROLES_ELEMENT_PATH:
        return _active_responsible_party_role_instances(
            source_obj,
            source_record_id,
        )

    if element_path == RESPONSIBLE_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_assignment_instances(
            source_obj,
            source_record_id,
        )

    if element_path == COMPONENTS_ELEMENT_PATH:
        return _build_component_instances(
            source_obj,
            source_record_id,
            mapping_rows,
            component_hydration_lookups,
        )

    if element_path == METADATA_ELEMENT_PATH:
        aggregate_payload["title"] = transform_metadata_title(
            resolve_json_path(source_obj, METADATA_TITLE_SOURCE_FIELD)
        )
        resolved_cluster_fields.add("title")
        for target_field in METADATA_TIMESTAMP_FIELDS:
            cluster_rows = [
                row
                for row in mapping_rows
                if _target_field_name(row) == target_field
            ]
            if not cluster_rows:
                continue
            resolved_cluster_fields.add(target_field)
            resolved_value = _resolve_metadata_timestamp_cluster(
                source_obj,
                cluster_rows,
                target_field,
            )
            if resolved_value is not SKIP_VALUE:
                aggregate_payload[target_field] = resolved_value

    for mapping_row in mapping_rows:
        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        target_field = _target_field_name(mapping_row)
        if target_field in resolved_cluster_fields:
            continue
        source_value = resolve_json_path(source_obj, source_field)
        transformed = apply_mapping_transform(
            mapping_row, source_value, source_record_id
        )
        if transformed is SKIP_VALUE:
            continue

        # The registry path owns node cardinality.  An Extension mapping may
        # resolve a value, but it must create a separate OSCAL property node
        # only when its owning registry node is actually props[].  Treating
        # every Extension mapping as a collection created multiple instances
        # of singleton parents such as system-characteristics.
        if element_path == SYSTEM_CHARACTERISTICS_PROPS_ELEMENT_PATH:
            values = _oscal_property_values(transformed)
            for item in values:
                payload = {
                    "name": _stable_property_name(source_field),
                    "value": item,
                }
                _append_unique_collection_instance(
                    instances,
                    {
                        "instance_key": _source_value_instance_key(
                            source_field,
                            item,
                        ),
                        "payload": payload,
                        "parent_instance_key": None,
                    },
                )
            continue

        if element_path == SYSTEM_IDS_ELEMENT_PATH:
            values = transformed if isinstance(transformed, list) else [transformed]
            for item in values:
                payload = item if isinstance(item, dict) else {target_field: item}
                identity_values = _oscal_property_values(
                    payload.get(target_field)
                )
                if len(identity_values) != 1:
                    raise ValueError(
                        "System ID must resolve to exactly one scalar value"
                    )
                canonical_value = identity_values[0]
                payload = dict(payload)
                payload[target_field] = canonical_value
                _append_unique_collection_instance(
                    instances,
                    {
                        "instance_key": _value_instance_key(canonical_value),
                        "payload": payload,
                        "parent_instance_key": None,
                    },
                )
            continue

        if element_path.endswith("responsible-parties[]"):
            instances.append(
                {
                    "instance_key": source_field,
                    "payload": transformed,
                    "parent_instance_key": None,
                }
            )
            continue

        if is_collection and isinstance(transformed, list):
            for index, item in enumerate(transformed):
                payload = item if isinstance(item, dict) else {target_field: item}
                instances.append(
                    {
                        "instance_key": f"{source_field}:{index}",
                        "payload": payload,
                        "parent_instance_key": None,
                    }
                )
            continue

        if (
            element_path == STATUS_ELEMENT_PATH
            and target_field == "state"
            and isinstance(transformed, dict)
            and "state" in transformed
        ):
            aggregate_payload["state"] = transformed["state"]
            if "remarks" in transformed:
                existing_remarks = aggregate_payload.get("remarks")
                if not (
                    isinstance(existing_remarks, str)
                    and existing_remarks.strip()
                ):
                    aggregate_payload["remarks"] = transformed["remarks"]
            continue

        if (
            target_field in aggregate_payload
            and aggregate_payload[target_field] != transformed
        ):
            raise ValueError(
                "Singleton target has conflicting populated mappings"
            )
        aggregate_payload[target_field] = transformed

    # security-impact-level is optional as an assembly, but once emitted all
    # three security objectives are required. Omit empty and partial
    # assemblies instead of inventing missing confidentiality, integrity, or
    # availability values.
    if (
        element_path == SECURITY_IMPACT_ELEMENT_PATH
        and not _is_complete_security_impact_payload(aggregate_payload)
    ):
        return []

    if aggregate_payload:
        instances.insert(
            0,
            {
                "instance_key": "singleton",
                "payload": aggregate_payload,
                "parent_instance_key": None,
            },
        )

    return instances


def build_mapping_coverage(source_dataframe, mapping_rows):
    counts = {row["SOURCE_FIELD_NAME"]: 0 for row in mapping_rows}
    total = 0
    for record in source_dataframe.to_local_iterator():
        total += 1
        source_obj = _parse_source_json(record)
        for field_name in counts:
            if _has_value(resolve_json_path(source_obj, field_name)):
                counts[field_name] += 1

    output = []
    for mapping_row in mapping_rows:
        field_name = mapping_row["SOURCE_FIELD_NAME"]
        populated = counts[field_name]
        output.append(
            {
                "ARCHER_FIELD": field_name,
                "OSCAL_MODEL": mapping_row["OSCAL_MODEL"],
                "OSCAL_ELEMENT": mapping_row["OSCAL_ELEMENT_PATH"],
                "MAPPING_TYPE": mapping_row["MAPPING_TYPE"],
                "STATUS": mapping_row["STATUS"],
                "HAS_SOURCE_DATA": populated > 0,
                "POPULATED_RECORDS": populated,
                "SOURCE_RECORDS": total,
                "POPULATION_PERCENT": (
                    round(100.0 * populated / total, 2) if total else 0.0
                ),
            }
        )
    return session.create_dataframe(output)


print("Cell 4 helpers initialized")


# %% Cell 5 - Registry-driven canonical node and edge graph

import uuid

METADATA_ELEMENT_PATH = "system-security-plan.metadata"
METADATA_ROLES_ELEMENT_PATH = "system-security-plan.metadata.roles[]"
METADATA_PARTIES_ELEMENT_PATH = "system-security-plan.metadata.parties[]"
RESPONSIBLE_PARTIES_ELEMENT_PATH = (
    "system-security-plan.metadata.responsible-parties[]"
)
COMPONENTS_ELEMENT_PATH = (
    "system-security-plan.system-implementation.components[]"
)
APPROVED_RESPONSIBLE_PARTY_TYPE = "person"
OPTIONAL_SINGLETON_ELEMENT_PATHS = {
    "system-security-plan.system-characteristics.security-impact-level",
}
GOVERNED_COLLECTION_CONTRACTS = {
    "system-security-plan.system-characteristics.props[]": {
        "parent_path": "system-security-plan.system-characteristics",
        "instance_key_rule": "SOURCE_FIELD_NAME+VALUE",
        "item_path": "$",
    },
    "system-security-plan.system-characteristics.system-ids[]": {
        "parent_path": "system-security-plan.system-characteristics",
        "instance_key_rule": "VALUE",
        "item_path": "$",
    },
    "system-security-plan.system-implementation.components[]": {
        "parent_path": "system-security-plan.system-implementation",
        "instance_key_rule": "CONTENT_ID",
        "item_path": "$",
    },
}

def _registry_value(row, *names):
    row_dict = row.as_dict(recursive=True)
    normalized = {str(key).upper(): value for key, value in row_dict.items()}
    for name in names:
        if name.upper() in normalized and normalized[name.upper()] is not None:
            return normalized[name.upper()]
    return None


def _derive_parent_path(element_path):
    parts = element_path.split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else None


def _element_type(element_path):
    return element_path.split(".")[-1].replace("[]", "")


def _registry_true(value):
    return str(value).strip().upper() in {"TRUE", "T", "YES", "Y", "1"}


def _should_materialize_structural_singleton(element_path, root_path):
    return (
        (element_path == root_path or "[]" not in element_path)
        and element_path not in OPTIONAL_SINGLETON_ELEMENT_PATHS
    )


def _inject_controlled_metadata_fields(element_path, instances):
    if element_path != METADATA_ELEMENT_PATH:
        return instances

    if len(instances) != 1 or instances[0].get("instance_key") != "singleton":
        raise ValueError("Expected exactly one singleton metadata instance")

    configured_version = str(CONFIG.get("OSCAL_VERSION") or "").strip()
    if not configured_version:
        raise ValueError("OSCAL_VERSION must be configured for metadata")

    document_version = CONFIG.get("SSP_DOCUMENT_VERSION")
    if (
        not isinstance(document_version, str)
        or not document_version.strip()
        or document_version != document_version.strip()
    ):
        raise ValueError(
            "SSP_DOCUMENT_VERSION must be a nonblank canonical string"
        )

    payload = instances[0].get("payload")
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValueError("Metadata payload must be an object")

    existing_version = payload.get("oscal-version")
    if (
        existing_version is not None
        and str(existing_version).strip()
        and str(existing_version).strip() != configured_version
    ):
        raise ValueError("Metadata oscal-version conflicts with configuration")

    existing_document_version = payload.get("version")
    if (
        existing_document_version not in (None, "")
        and existing_document_version != document_version
    ):
        raise ValueError(
            "Metadata document version conflicts with configuration"
        )

    updated_payload = dict(payload)
    updated_payload["oscal-version"] = configured_version
    updated_payload["version"] = document_version
    updated_instance = dict(instances[0])
    updated_instance["payload"] = updated_payload
    return [updated_instance]


def _canonical_uuid(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a canonical UUID")
    try:
        canonical = str(uuid.UUID(value))
    except (ValueError, AttributeError, TypeError):
        raise ValueError(f"{label} must be a canonical UUID") from None
    if value != canonical:
        raise ValueError(f"{label} must be a canonical UUID")
    return canonical


def _instance_oscal_uuid(
    element_path,
    instance,
    source_system,
    source_table,
    source_record_id,
    model_key,
):
    instance_key = instance["instance_key"]
    if element_path == METADATA_PARTIES_ELEMENT_PATH:
        payload = instance.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("Metadata party payload must be an object")
        instance_uuid = _canonical_uuid(
            instance_key,
            "Metadata party instance key",
        )
        payload_uuid = _canonical_uuid(
            payload.get("uuid"),
            "Metadata party payload uuid",
        )
        if instance_uuid != payload_uuid:
            raise ValueError("Metadata party UUID fields do not match")
        return payload_uuid

    return _deterministic_uuid(
        CONFIG["IDENTITY_VERSION"],
        source_system,
        source_table,
        source_record_id,
        model_key,
        element_path,
        instance_key,
    )


def _payload_with_instance_uuid(element_path, payload, oscal_uuid):
    if element_path != COMPONENTS_ELEMENT_PATH:
        return payload
    if not isinstance(payload, dict):
        raise ValueError("Component payload must be an object")
    existing_uuid = payload.get("uuid")
    if existing_uuid not in (None, "") and existing_uuid != oscal_uuid:
        raise ValueError("Component payload uuid conflicts with node uuid")
    if "status" in payload:
        raise ValueError("Component status hydration is not approved")
    for field_name in ("title", "description"):
        if field_name not in payload:
            continue
        field_value = payload[field_name]
        if not isinstance(field_value, str) or not field_value.strip():
            raise ValueError(
                f"Component payload {field_name} must be nonblank text"
            )
    updated_payload = dict(payload)
    updated_payload["uuid"] = oscal_uuid
    return updated_payload


def _canonical_registry_rows(element_registry_dataframe, model_key):
    rows = []
    for row in element_registry_dataframe.collect():
        model = _registry_value(
            row,
            "OSCAL_MODEL_KEY",
            "OSCAL_MODEL",
            "MODEL_NAME",
            "MODEL",
        )
        if model and str(model).strip().upper() != model_key.upper():
            continue

        is_active = _registry_value(row, "IS_ACTIVE", "ACTIVE")
        if is_active is not None and str(is_active).strip().upper() in {
            "FALSE",
            "F",
            "NO",
            "N",
            "0",
        }:
            continue

        path = _registry_value(
            row,
            "NODE_PATH",
            "OSCAL_ELEMENT_PATH",
            "ELEMENT_PATH",
            "JSON_PATH",
        )
        if not path:
            continue
        path = str(path).strip()
        parent = _registry_value(
            row,
            "PARENT_NODE_PATH",
            "PARENT_ELEMENT_PATH",
            "PARENT_PATH",
        )
        level = _registry_value(
            row,
            "HIERARCHY_LEVEL",
            "ELEMENT_LEVEL",
            "LEVEL_NUMBER",
        )
        process_order = _registry_value(row, "PROCESS_ORDER")
        is_collection = _registry_value(row, "IS_COLLECTION")
        instance_key_rule = _registry_value(row, "INSTANCE_KEY_RULE")
        item_path = _registry_value(row, "ITEM_PATH")
        derived_level = path.count(".") + 1
        rows.append(
            {
                "element_path": path,
                "parent_path": str(parent).strip() if parent else _derive_parent_path(path),
                "level": int(level) if level is not None else derived_level,
                "process_order": (
                    int(process_order)
                    if process_order is not None
                    else derived_level * 1000000
                ),
                "is_collection": _registry_true(is_collection),
                "instance_key_rule": (
                    str(instance_key_rule).strip().upper()
                    if instance_key_rule is not None
                    else None
                ),
                "item_path": (
                    str(item_path).strip()
                    if item_path is not None
                    else None
                ),
            }
        )

    existing_paths = {row["element_path"] for row in rows}
    responsible_party_row = next(
        (
            row
            for row in rows
            if row["element_path"] == RESPONSIBLE_PARTIES_ELEMENT_PATH
        ),
        None,
    )
    approved_party_mapping_exists = False
    for mapping_row in MAPPINGS_BY_ELEMENT_PATH.get(
        RESPONSIBLE_PARTIES_ELEMENT_PATH,
        [],
    ):
        source_field = str(
            mapping_row.get("SOURCE_FIELD_NAME") or ""
        ).strip()
        mapping_type = str(
            mapping_row.get("MAPPING_TYPE") or "Direct"
        ).strip().lower()
        status = str(mapping_row.get("STATUS") or "").strip().lower()
        if (
            source_field in RESPONSIBLE_PARTY_ROLE_IDS
            and "tbd" not in mapping_type
            and "more information" not in status
        ):
            approved_party_mapping_exists = True
            break

    role_row = next(
        (
            row
            for row in rows
            if row["element_path"] == METADATA_ROLES_ELEMENT_PATH
        ),
        None,
    )
    party_row = next(
        (
            row
            for row in rows
            if row["element_path"] == METADATA_PARTIES_ELEMENT_PATH
        ),
        None,
    )

    if approved_party_mapping_exists:
        if responsible_party_row is None:
            raise ValueError(
                "Registry is missing metadata.responsible-parties[] required "
                "by approved responsible-party mappings"
            )
        if METADATA_ROLES_ELEMENT_PATH not in existing_paths:
            raise ValueError(
                "Registry is missing metadata.roles[] required by approved "
                "responsible-party mappings"
            )
        if METADATA_PARTIES_ELEMENT_PATH not in existing_paths:
            raise ValueError(
                "Registry is missing metadata.parties[] required by approved "
                "responsible-party mappings"
            )

    if role_row is not None and role_row["parent_path"] != METADATA_ELEMENT_PATH:
        raise ValueError("Registry metadata.roles[] parent path is invalid")
    if party_row is not None and party_row["parent_path"] != METADATA_ELEMENT_PATH:
        raise ValueError("Registry metadata.parties[] parent path is invalid")
    if (
        responsible_party_row is not None
        and responsible_party_row["parent_path"] != METADATA_ELEMENT_PATH
    ):
        raise ValueError(
            "Registry metadata.responsible-parties[] parent path is invalid"
        )

    for path, contract in GOVERNED_COLLECTION_CONTRACTS.items():
        registry_row = next(
            (row for row in rows if row["element_path"] == path),
            None,
        )
        if registry_row is None:
            continue
        if not registry_row["is_collection"]:
            raise ValueError(
                "Governed registry collection flag is invalid"
            )
        if registry_row["parent_path"] != contract["parent_path"]:
            raise ValueError("Governed registry parent path is invalid")
        if (
            registry_row["instance_key_rule"]
            != contract["instance_key_rule"]
        ):
            raise ValueError("Governed registry instance rule is invalid")
        if registry_row["item_path"] != contract["item_path"]:
            raise ValueError("Governed registry item path is invalid")
    rows.sort(
        key=lambda item: (
            item["process_order"],
            item["level"],
            item["element_path"],
        )
    )
    if not rows:
        raise ValueError("No registry paths found for configured OSCAL model")
    return rows


def _metadata_reference_payload(node, label):
    raw_payload = node.get("METADATA_JSON")
    if isinstance(raw_payload, str):
        try:
            payload = json.loads(raw_payload)
        except (TypeError, ValueError):
            raise ValueError(f"{label} payload is not valid JSON") from None
    else:
        payload = raw_payload
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload must be an object")
    return payload


def _validate_metadata_reference_closure(nodes_by_path):
    role_nodes = nodes_by_path.get(METADATA_ROLES_ELEMENT_PATH, [])
    party_nodes = nodes_by_path.get(METADATA_PARTIES_ELEMENT_PATH, [])
    assignment_nodes = nodes_by_path.get(
        RESPONSIBLE_PARTIES_ELEMENT_PATH,
        [],
    )

    role_counts = {}
    for node in role_nodes:
        payload = _metadata_reference_payload(node, "Metadata role")
        role_id = payload.get("id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError("Metadata role id must be a nonblank string")
        if node.get("INSTANCE_KEY") != role_id:
            raise ValueError("Metadata role id and instance key do not match")
        role_counts[role_id] = role_counts.get(role_id, 0) + 1
        if role_counts[role_id] != 1:
            raise ValueError("Metadata role id is not unique")

    party_counts = {}
    for node in party_nodes:
        payload = _metadata_reference_payload(node, "Metadata party")
        node_uuid = _canonical_uuid(
            node.get("OSCAL_UUID"),
            "Metadata party node uuid",
        )
        payload_uuid = _canonical_uuid(
            payload.get("uuid"),
            "Metadata party payload uuid",
        )
        if node_uuid != payload_uuid or node.get("INSTANCE_KEY") != node_uuid:
            raise ValueError("Metadata party UUID fields do not match")
        if payload.get("type") != APPROVED_RESPONSIBLE_PARTY_TYPE:
            raise ValueError("Metadata party type violates approved contract")
        party_counts[node_uuid] = party_counts.get(node_uuid, 0) + 1
        if party_counts[node_uuid] != 1:
            raise ValueError("Metadata party uuid is not unique")

    referenced_roles = set()
    referenced_parties = set()
    assignment_role_counts = {}
    for node in assignment_nodes:
        payload = _metadata_reference_payload(
            node,
            "Metadata responsible-party",
        )
        role_id = payload.get("role-id")
        if not isinstance(role_id, str) or not role_id.strip():
            raise ValueError(
                "Metadata responsible-party role-id must be nonblank"
            )
        assignment_role_counts[role_id] = (
            assignment_role_counts.get(role_id, 0) + 1
        )
        if assignment_role_counts[role_id] != 1:
            raise ValueError(
                "Metadata responsible-party role-id is not unique"
            )
        if role_counts.get(role_id) != 1:
            raise ValueError(
                "Metadata responsible-party role reference is unresolved"
            )
        referenced_roles.add(role_id)

        party_uuids = payload.get("party-uuids")
        if not isinstance(party_uuids, list) or not party_uuids:
            raise ValueError(
                "Metadata responsible-party must reference a party"
            )
        local_party_uuids = set()
        for party_uuid in party_uuids:
            canonical_uuid = _canonical_uuid(
                party_uuid,
                "Metadata responsible-party reference uuid",
            )
            if canonical_uuid in local_party_uuids:
                raise ValueError(
                    "Metadata responsible-party contains duplicate party "
                    "references"
                )
            local_party_uuids.add(canonical_uuid)
            if party_counts.get(canonical_uuid) != 1:
                raise ValueError(
                    "Metadata responsible-party reference is unresolved"
                )
            referenced_parties.add(canonical_uuid)

    if set(role_counts) != referenced_roles:
        raise ValueError("Metadata contains an unreferenced role")
    if set(party_counts) != referenced_parties:
        raise ValueError("Metadata contains an unreferenced party")


def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table,
):
    del canonical_mapping_df  # canonical rows are already materialized in Cell 3

    registry_rows = _canonical_registry_rows(element_registry_df, model_key)
    root_paths = [row["element_path"] for row in registry_rows if not row["parent_path"]]
    if len(root_paths) != 1:
        raise ValueError(f"Expected one registry root; found {root_paths}")
    root_path = root_paths[0]

    component_hydration_lookups = None
    if model_key.upper() == "SSP":
        hydration_source_dfs = globals().get(
            "COMPONENT_HYDRATION_SOURCE_DFS"
        )
        if hydration_source_dfs is None:
            raise RuntimeError(
                "Run the updated Cell 2 before building the SSP graph"
            )
        component_hydration_lookups = _build_component_hydration_lookups(
            source_df,
            MAPPINGS_BY_ELEMENT_PATH.get(COMPONENTS_ELEMENT_PATH, []),
            hydration_source_dfs,
        )

    node_rows = []
    edge_rows = []
    load_timestamp = datetime.datetime.now(datetime.timezone.utc)

    for record in source_df.to_local_iterator():
        source_record_id = str(record["SOURCE_RECORD_ID"])
        source_obj = _parse_source_json(record)
        nodes_by_path = {}

        for registry_row in registry_rows:
            path = registry_row["element_path"]
            parent_path = registry_row["parent_path"]
            mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(path, [])
            instances = build_element_instances(
                source_obj,
                source_record_id,
                path,
                mapping_rows,
                component_hydration_lookups,
            )

            # Structural singleton containers are materialized even without a
            # direct mapping. Empty collections are not invented.
            if not instances and _should_materialize_structural_singleton(
                path,
                root_path,
            ):
                instances = [
                    {
                        "instance_key": "singleton",
                        "payload": {},
                        "parent_instance_key": None,
                    }
                ]

            instances = _inject_controlled_metadata_fields(path, instances)

            created_nodes = []
            for instance in instances:
                instance_key = instance["instance_key"]
                node_key = _deterministic_hash(
                    CONFIG["IDENTITY_VERSION"],
                    source_system,
                    source_table,
                    source_record_id,
                    model_key,
                    path,
                    instance_key,
                )
                oscal_uuid = _instance_oscal_uuid(
                    path,
                    instance,
                    source_system,
                    source_table,
                    source_record_id,
                    model_key,
                )
                payload = _payload_with_instance_uuid(
                    path,
                    instance["payload"],
                    oscal_uuid,
                )
                created = {
                    "NODE_KEY": node_key,
                    "ELEMENT_PATH": path,
                    "INSTANCE_KEY": instance_key,
                    "PARENT_INSTANCE_KEY": instance.get("parent_instance_key"),
                    "OSCAL_UUID": oscal_uuid,
                    "ELEMENT_TYPE": _element_type(path),
                    "METADATA_JSON": json.dumps(
                        payload, sort_keys=True, default=str
                    ),
                    "SOURCE_SYSTEM_NAME": source_system,
                    "SOURCE_TABLE_NAME": source_table,
                    "SOURCE_RECORD_ID": source_record_id,
                    "DW_PIPELINE_RUN_ID": CONFIG["RUN_ID"],
                    "DW_LOAD_TIMESTAMP": load_timestamp,
                    "DW_LOAD_TIMESTAMP_TZ": load_timestamp,
                }
                node_rows.append(created)
                created_nodes.append(created)

            nodes_by_path[path] = created_nodes

            if not parent_path:
                continue
            parent_nodes = nodes_by_path.get(parent_path, [])
            for child_node in created_nodes:
                if not parent_nodes:
                    raise ValueError(
                        f"Missing parent {parent_path} for child {path}"
                    )
                if len(parent_nodes) == 1:
                    parent_node = parent_nodes[0]
                else:
                    parent_key = child_node["PARENT_INSTANCE_KEY"]
                    matches = [
                        node
                        for node in parent_nodes
                        if node["INSTANCE_KEY"] == parent_key
                    ]
                    if len(matches) != 1:
                        raise ValueError(
                            "Ambiguous collection parent for "
                            f"{path} instance {child_node['INSTANCE_KEY']}"
                        )
                    parent_node = matches[0]

                edge_key = _deterministic_hash(
                    "edge-v1",
                    parent_node["NODE_KEY"],
                    child_node["NODE_KEY"],
                    "CONTAINS",
                )
                edge_rows.append(
                    {
                        "EDGE_KEY": edge_key,
                        "FK_SOURCE_ELEMENT_HASH": parent_node["NODE_KEY"],
                        "FK_TARGET_ELEMENT_HASH": child_node["NODE_KEY"],
                        "DEPENDENCY_TYPE": "CONTAINS",
                        "SOURCE_OSCAL_UUID": parent_node["OSCAL_UUID"],
                        "TARGET_OSCAL_UUID": child_node["OSCAL_UUID"],
                    }
                )

        _validate_metadata_reference_closure(nodes_by_path)

    if not node_rows:
        raise ValueError("Graph builder produced no nodes")

    canonical_nodes_df = session.create_dataframe(node_rows)
    canonical_edges_df = session.create_dataframe(edge_rows)
    return canonical_nodes_df, canonical_edges_df


print("Cell 5 graph builder initialized")


# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification

def _assert_safe_identifier(identifier):
    if not re.fullmatch(r"[A-Za-z0-9_.$]+", identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier}")


def _duplicate_count(dataframe, key_column):
    return (
        dataframe.group_by(col(key_column))
        .count()
        .filter(col("COUNT") > lit(1))
        .count()
    )


def _build_merge_sql(target_table, source_view, pk_column, columns):
    update_columns = [name for name in columns if name.upper() != pk_column.upper()]
    update_set = ",\n".join(f"t.{name} = s.{name}" for name in update_columns)
    insert_columns = ",\n".join(columns)
    insert_values = ",\n".join(f"s.{name}" for name in columns)
    return f"""
MERGE INTO {target_table} t
USING {source_view} s
ON t.{pk_column} = s.{pk_column}
WHEN MATCHED THEN UPDATE SET
{update_set}
WHEN NOT MATCHED THEN INSERT (
{insert_columns}
) VALUES (
{insert_values}
)
"""


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    node_count = canonical_nodes_df.count()
    edge_count = canonical_edges_df.count()
    node_duplicate_count = _duplicate_count(canonical_nodes_df, "NODE_KEY")
    edge_duplicate_count = _duplicate_count(canonical_edges_df, "EDGE_KEY")
    node_null_count = canonical_nodes_df.filter(col("NODE_KEY").is_null()).count()
    edge_null_count = canonical_edges_df.filter(col("EDGE_KEY").is_null()).count()

    node_keys_df = canonical_nodes_df.select(col("NODE_KEY").alias("GRAPH_NODE_KEY"))
    missing_sources = (
        canonical_edges_df.join(
            node_keys_df,
            canonical_edges_df["FK_SOURCE_ELEMENT_HASH"] == node_keys_df["GRAPH_NODE_KEY"],
            "left_anti",
        ).count()
    )
    missing_targets = (
        canonical_edges_df.join(
            node_keys_df,
            canonical_edges_df["FK_TARGET_ELEMENT_HASH"] == node_keys_df["GRAPH_NODE_KEY"],
            "left_anti",
        ).count()
    )

    print("Graph nodes:", node_count)
    print("Graph edges:", edge_count)
    print("Duplicate node keys:", node_duplicate_count)
    print("Duplicate edge keys:", edge_duplicate_count)
    print("Dangling source edges:", missing_sources)
    print("Dangling target edges:", missing_targets)

    validation_errors = sum(
        [
            node_duplicate_count,
            edge_duplicate_count,
            node_null_count,
            edge_null_count,
            missing_sources,
            missing_targets,
        ]
    )
    if validation_errors:
        raise ValueError("OSCAL graph validation FAILED")

    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]
    dim_pk = config["DIM_PK_COLUMN"]
    fact_pk = config["FACT_PK_COLUMN"]
    for identifier in (dim_table, fact_table, dim_pk, fact_pk):
        _assert_safe_identifier(identifier)

    dim_target_columns = session.table(dim_table).columns
    fact_target_columns = session.table(fact_table).columns

    dim_expression_map = {
        dim_pk.upper(): col("NODE_KEY").alias(dim_pk),
        "ELEMENT_TYPE": col("ELEMENT_TYPE"),
        "OSCAL_UUID": col("OSCAL_UUID"),
        "METADATA_JSON": col("METADATA_JSON"),
        "SOURCE_SYSTEM_NAME": col("SOURCE_SYSTEM_NAME"),
        "SOURCE_TABLE_NAME": col("SOURCE_TABLE_NAME"),
        "SOURCE_RECORD_ID": col("SOURCE_RECORD_ID"),
        "DW_PIPELINE_RUN_ID": col("DW_PIPELINE_RUN_ID"),
        "DW_LOAD_TIMESTAMP": col("DW_LOAD_TIMESTAMP"),
        "DW_LOAD_TIMESTAMP_TZ": col("DW_LOAD_TIMESTAMP_TZ"),
    }
    fact_expression_map = {
        fact_pk.upper(): col("EDGE_KEY").alias(fact_pk),
        "FK_SOURCE_ELEMENT_HASH": col("FK_SOURCE_ELEMENT_HASH"),
        "FK_TARGET_ELEMENT_HASH": col("FK_TARGET_ELEMENT_HASH"),
        "DEPENDENCY_TYPE": col("DEPENDENCY_TYPE"),
        "SOURCE_OSCAL_UUID": col("SOURCE_OSCAL_UUID"),
        "TARGET_OSCAL_UUID": col("TARGET_OSCAL_UUID"),
    }

    dim_load_columns = [
        name for name in dim_target_columns if name.upper() in dim_expression_map
    ]
    fact_load_columns = [
        name for name in fact_target_columns if name.upper() in fact_expression_map
    ]

    if dim_pk.upper() not in {name.upper() for name in dim_load_columns}:
        raise ValueError(f"Target DIM does not expose configured PK {dim_pk}")
    if fact_pk.upper() not in {name.upper() for name in fact_load_columns}:
        raise ValueError(f"Target FACT does not expose configured PK {fact_pk}")

    dim_load_df = canonical_nodes_df.select(
        *[dim_expression_map[name.upper()] for name in dim_load_columns]
    )
    fact_load_df = canonical_edges_df.select(
        *[fact_expression_map[name.upper()] for name in fact_load_columns]
    )

    dim_load_count = dim_load_df.count()
    fact_load_count = fact_load_df.count()
    if _duplicate_count(dim_load_df, dim_pk) or _duplicate_count(fact_load_df, fact_pk):
        raise ValueError("OSCAL pre-write validation FAILED: duplicate target PK")
    if dim_load_df.filter(col(dim_pk).is_null()).count():
        raise ValueError("OSCAL pre-write validation FAILED: NULL DIM PK")
    if fact_load_df.filter(col(fact_pk).is_null()).count():
        raise ValueError("OSCAL pre-write validation FAILED: NULL FACT PK")

    print("PRE-WRITE VALIDATION PASSED")

    if not config["EXECUTE_WRITES"]:
        print("EXECUTE_WRITES = False; no DIM/FACT changes were made")
        return {
            "nodes": node_count,
            "edges": edge_count,
            "validation_passed": True,
            "pre_write_validation_passed": True,
            "dim_load_rows": dim_load_count,
            "fact_load_rows": fact_load_count,
            "writes_executed": False,
        }

    dim_source_view = "TMP_OSCAL_DIM_LOAD"
    fact_source_view = "TMP_OSCAL_FACT_LOAD"
    dim_load_df.create_or_replace_temp_view(dim_source_view)
    fact_load_df.create_or_replace_temp_view(fact_source_view)

    dim_merge_result = session.sql(
        _build_merge_sql(
            dim_table, dim_source_view, dim_pk, dim_load_columns
        )
    ).collect()
    fact_merge_result = session.sql(
        _build_merge_sql(
            fact_table, fact_source_view, fact_pk, fact_load_columns
        )
    ).collect()

    verification = verify_oscal_load(canonical_nodes_df, canonical_edges_df, config)
    return {
        "nodes": node_count,
        "edges": edge_count,
        "validation_passed": True,
        "pre_write_validation_passed": True,
        "dim_load_rows": dim_load_count,
        "fact_load_rows": fact_load_count,
        "writes_executed": True,
        "dim_merge_result": dim_merge_result,
        "fact_merge_result": fact_merge_result,
        "verification": verification,
    }


def verify_oscal_load(canonical_nodes_df, canonical_edges_df, config):
    dim_table = config["TARGET_DIM"]
    fact_table = config["TARGET_FACT"]
    dim_pk = config["DIM_PK_COLUMN"]
    fact_pk = config["FACT_PK_COLUMN"]

    expected_dim = canonical_nodes_df.count()
    expected_fact = canonical_edges_df.count()
    canonical_nodes_df.select(col("NODE_KEY").alias(dim_pk)).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_DIM"
    )
    canonical_edges_df.select(col("EDGE_KEY").alias(fact_pk)).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_FACT"
    )

    dim_matches = session.sql(
        f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_DIM s
        JOIN {dim_table} t ON s.{dim_pk} = t.{dim_pk}
        """
    ).collect()[0]["CNT"]
    fact_matches = session.sql(
        f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_FACT s
        JOIN {fact_table} t ON s.{fact_pk} = t.{fact_pk}
        """
    ).collect()[0]["CNT"]

    if dim_matches != expected_dim or fact_matches != expected_fact:
        raise ValueError("OSCAL post-load verification FAILED")
    print("LOAD VERIFIED")
    return {
        "dim_expected": expected_dim,
        "dim_matched": dim_matches,
        "fact_expected": expected_fact,
        "fact_matched": fact_matches,
    }


print("Cell 6 validation and loader initialized; execution remains in Cell 7")


# %% Cell 7 - OSCAL mapper orchestrator

def run_oscal_mapping(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    config,
):
    print("=" * 70)
    print("OSCAL MAPPING RUN")
    print("Model:", config["OSCAL_MODEL"])
    print("Run ID:", config["RUN_ID"])
    print("=" * 70)

    nodes_df, edges_df = build_oscal_graph(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"],
        source_table=config["SOURCE_TABLE_NAME"],
    )

    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df,
        canonical_edges_df=edges_df,
        config=config,
    )

    coverage_df = None
    if config.get("BUILD_COVERAGE_REPORT", False):
        coverage_df = build_mapping_coverage(
            source_df,
            CANONICAL_MAPPING_ROWS,
        )

    print("OSCAL MAPPING RUN COMPLETE")
    print("Nodes:", result["nodes"])
    print("Edges:", result["edges"])
    print("Writes:", result["writes_executed"])
    return nodes_df, edges_df, coverage_df, result


final_nodes_df, final_edges_df, mapping_coverage_df, run_result = (
    run_oscal_mapping(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        config=CONFIG,
    )
)

