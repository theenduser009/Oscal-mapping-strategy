# %% Cell 1 - Configuration
# Source 2 / Authoritative Sources Source -> Catalog Metadata reviewed Source-tab batch.
# PREVIEW only. Reuses shared Cells 2-7. No Source 1 settings are changed.

import copy
import csv
import datetime
import hashlib
import json
import re
import uuid
from decimal import Decimal
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, lit, dense_rank
from snowflake.snowpark.window import Window
from snowflake.snowpark.types import StringType, StructField, StructType, TimestampType, TimestampTimeZone

session = get_active_session()
SELECTED_MODELS = ("CATALOG",)
CONFIG = {
    "RUN_ID": str(uuid.uuid4()),
    "OSCAL_VERSION": "1.2.3",
    "SSP_DOCUMENT_VERSION": "1.0",
    "EXECUTE_WRITES": False,
    "IDENTITY_VERSION": "v1_registry_path_instance",
    "ASSESSMENT_TASK_TITLE": "Preassessment review",
    "ASSESSMENT_TASK_TYPE": "action",
    "ELEMENT_REGISTRY_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY",
    "ARCHER_META_VALUE_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE",
}

SOURCE_FILES = [{
    "SOURCE_KEY": "source-two-source",
    "SOURCE_SYSTEM_NAME": "ARCHER",
    "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW",
    "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW",
    "CONTENT_ID_COLUMN": "CONTENT_ID",
    "CURATED_JSON_COLUMN": "CURATED_JSON",
    "MAPPING_FILE": "sources_source_runtime.csv",
    "MAPPING_ENCODING": "utf-8-sig",
    "MAPPING_SOURCE_COLUMN": "SOURCE_KEY",
    "MAPPING_SOURCE_VALUE": "source-two-source",
    "MODEL_BINDINGS": ("CATALOG",),
    "SOURCE_ORDER_CANDIDATES": (
        "ETL_LOAD_TS",
        "LOAD_TIMESTAMP",
        "FILE_DATE",
    ),
    "LOOKUP_CONTRACTS": {},
}]

MODEL_CONTRACTS = {
    "CATALOG": {
        "MODEL_KEY": "CATALOG",
        "POLICY": "metadata-v1",
        "UNREVIEWED_ROWS": "DEFER",
        "MODEL_ALIASES": (
            "Catalog",
            "Catalog - Metadata",
            "Catalog - Group",
            "Catalog - Back Matter",
        ),
        "LOOKUP_GROUPS": (),
        "RUNTIME_OPTIONS": {
            "parse_decimal": False,
            "null_source_as_empty": False,
        },
        "STORAGE_CONTRACT": {
            "VERIFIED": True,
            "PHYSICAL_PROFILE": "BINARY16_UUID32",
            "MODEL_KEY": "CATALOG",
            "ROOT_PATH": "catalog",
            "ROOT_ELEMENT_TYPE": "catalog",
            "SOURCE_SYSTEM_NAME": "ARCHER",
            "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW",
            "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW",
            "TARGET_DIM": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_CATALOG_ELEMENT",
            "TARGET_FACT": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_CATALOG_DEPENDENCY",
            "DIM_PK_COLUMN": "PK_DIM_OSCAL_CATALOG_ELEMENT_HASH",
            "FACT_PK_COLUMN": "PK_FACT_OSCAL_CATALOG_DEPENDENCY_HASH",
            "IDENTITY_VERSION": "v1_registry_path_instance",
        },
    },
}

ROUTING_METADATA = {
    "DEFERRED_MODEL_LABELS": ("TBD", "N/A - Calculated", "Multiple - See Notes"),
    "DEFERRED_TARGET_PATHS": ("TBD", "All Nulls", "Multiple - See Notes"),
}

if (not SELECTED_MODELS or len(set(SELECTED_MODELS)) != len(SELECTED_MODELS)
        or set(SELECTED_MODELS) - MODEL_CONTRACTS.keys()):
    raise ValueError("Choose distinct configured models in SELECTED_MODELS")

SOURCE_PROFILES = []
if (len({source["SOURCE_KEY"] for source in SOURCE_FILES}) != len(SOURCE_FILES)
        or len({source["RAW_TABLE"].upper() for source in SOURCE_FILES}) != len(SOURCE_FILES)
        or len({(source["SOURCE_SYSTEM_NAME"].upper(), source["SOURCE_TABLE_NAME"].upper())
                for source in SOURCE_FILES}) != len(SOURCE_FILES)):
    raise ValueError("Each source key, physical source and source namespace must have one binding")

for source in SOURCE_FILES:
    routes = tuple(model for model in SELECTED_MODELS if model in source["MODEL_BINDINGS"])
    if routes:
        SOURCE_PROFILES.append({**source, "MODEL_KEYS": routes, "BASE_CONFIG": dict(CONFIG)})

if any(not any(model in source["MODEL_KEYS"] for source in SOURCE_PROFILES) for model in SELECTED_MODELS):
    raise ValueError("Selected model has no configured source")

print("OSCAL mapping:", SELECTED_MODELS, "Run:", CONFIG["RUN_ID"])
