# %% Cell 1 - Configuration
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
SELECTED_MODELS = ("SSP",)
CONFIG = {
    "RUN_ID": str(uuid.uuid4()), "OSCAL_VERSION": "1.2.3", "SSP_DOCUMENT_VERSION": "1.0",
    "EXECUTE_WRITES": False, "IDENTITY_VERSION": "v1_registry_path_instance",
    "ELEMENT_REGISTRY_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY",
    "ARCHER_META_VALUE_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE",
}
SOURCE_FILES = [{
    "SOURCE_KEY": "source-one", "SOURCE_SYSTEM_NAME": "ARCHER",
    "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
    "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
    "CONTENT_ID_COLUMN": "CONTENT_ID", "CURATED_JSON_COLUMN": "CURATED_JSON",
    "MAPPING_FILE": "ARCHER_OSCAL_MAPPINGS.csv", "MAPPING_ENCODING": "utf-8-sig",
    "MAPPING_SOURCE_COLUMN": "SOURCE_KEY", "MAPPING_SOURCE_VALUE": "source-one",
    "MODEL_BINDINGS": ("SSP", "ASSESSMENT_RESULTS"),
    "SOURCE_ORDER_CANDIDATES": (
        "DW_LOAD_TIMESTAMP_TZ", "DW_LOAD_TIMESTAMP", "UPDATED_DATE",
        "LAST_UPDATED_DATE", "MODIFIED_DATE", "CREATE_DATE",
    ),
    "LOOKUP_CONTRACTS": {
        "software": {
            "source_table": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW",
            "title_field": "SOFTWARE_NAME", "description_field": "DESCRIPTION",
        },
        "interconnection": {
            "source_table": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW",
            "title_field": "INTERCONNECTION_NAME", "description_field": "DESCRIPTION",
        },
    },
}]
MODEL_CONTRACTS = {
    "SSP": {
        "MODEL_KEY": "SSP", "POLICY": "metadata-v1", "UNREVIEWED_ROWS": "DEFER",
        "MODEL_ALIASES": ("System Security Plan", "SSP - Metadata", "SSP - System Characteristics",
                          "SSP - System Implementation", "SSP - Control Implementation"),
        "LOOKUP_GROUPS": ("components",),
        "RUNTIME_OPTIONS": {"parse_decimal": False, "null_source_as_empty": True},
        "STORAGE_CONTRACT": {
            "VERIFIED": True, "PHYSICAL_PROFILE": "BINARY16_UUID32", "MODEL_KEY": "SSP",
            "ROOT_PATH": "system-security-plan", "ROOT_ELEMENT_TYPE": "system-security-plan",
            "SOURCE_SYSTEM_NAME": "ARCHER", "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
            "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
            "TARGET_DIM": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT",
            "TARGET_FACT": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY",
            "DIM_PK_COLUMN": "PK_OSCAL_SSP_ELEMENT_HASH", "FACT_PK_COLUMN": "PK_FACT_OSCAL_DEPENDENCY_HASH",
            "IDENTITY_VERSION": "v1_registry_path_instance",
        },
    },
    "ASSESSMENT_RESULTS": {
        "MODEL_KEY": "ASSESSMENT_RESULTS", "POLICY": "metadata-v1", "UNREVIEWED_ROWS": "DEFER",
        "MODEL_ALIASES": ("Assessment Results", "AR"), "LOOKUP_GROUPS": (),
        "RUNTIME_OPTIONS": {"parse_decimal": True, "null_source_as_empty": False},
        "STORAGE_CONTRACT": None,
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
