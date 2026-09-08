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

