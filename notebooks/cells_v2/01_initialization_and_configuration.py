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

# The only model selector. Use "SSP", "ASSESSMENT_RESULTS", or a tuple/list
# of configured model keys. Model contracts below describe capabilities;
# they are not a second run selector. Unknown models fail before source reads.
SELECTED_MODELS = ("SSP", "ASSESSMENT_RESULTS")


def _selected_model_keys(selection, model_contracts):
    if isinstance(selection, str):
        selection = (selection,)
    if not isinstance(selection, (tuple, list)) or not selection:
        raise ValueError("SELECTED_MODELS must name at least one configured model")
    if any(not isinstance(model, str) or not model.strip() for model in selection):
        raise ValueError("SELECTED_MODELS contains an invalid model key")
    if len(selection) != len(set(selection)):
        raise ValueError("SELECTED_MODELS contains duplicate models")
    if any(model not in model_contracts for model in selection):
        raise ValueError("SELECTED_MODELS contains an unconfigured model")
    return tuple(selection)


CONFIG = {
    "RUN_ID": datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    ),
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

# Governed capabilities and accepted release scope, not run selectors.
# Field-level approvals still need migration into reviewed mapping metadata;
# do not remove the AR acceptance boundary to enable deferred/candidate rows.
# Additional sources require explicit profiles and reviewed mapping bindings;
# do not invent names for the other six source tables.
AR_ACCEPTED_FIELDS = (
    "VULNERABILITY_SCORE", "ANTIVIRUS_SCORE", "PATCH_SCORE",
    "SECURITY_COMPLIANCE_SCORE", "STANDARD_OPERATING_ENVIRONMENT_SCORE",
    "COMPUTER_PASSWORD_AGE_SCORE", "VULNERABILITY_REPORTING_SCORE",
    "SECURITY_COMPLIANCE_REPORTING_SCORE", "TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE",
    "AVG_AUTHORIZATION_PACKAGE_RISK_SCORE", "RISK_SCORE_GRADE",
    "AVG_VULNERABILITY_SCORE", "AVG_PATCH_SCORE", "AVG_ANTIVIRUS_SCORE",
    "AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE", "AVG_COMPUTER_PASSWORD_AGE_SCORE",
    "AVG_VULNERABILITY_REPORTING_SCORE",
)

_SSP_STORAGE_CONTRACT = {
    "VERIFIED": True,
    "PHYSICAL_PROFILE": "BINARY16_UUID32",
    "MODEL_KEY": "SSP",
    "ROOT_PATH": "system-security-plan",
    "ROOT_ELEMENT_TYPE": "system-security-plan",
    "SOURCE_SYSTEM_NAME": CONFIG["SOURCE_SYSTEM_NAME"],
    "SOURCE_TABLE_NAME": CONFIG["SOURCE_TABLE_NAME"],
    "RAW_TABLE": CONFIG["RAW_TABLE"],
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
    "IDENTITY_VERSION": CONFIG["IDENTITY_VERSION"],
}
MODEL_CONTRACTS = {
    "SSP": {
        "MODEL_KEY": "SSP", "ROOT_PATH": "system-security-plan",
        "POLICY": "ssp-approved-v1",
        "LOOKUP_GROUPS": ("components",),
        "PATH_RULES": ({
            "SOURCE_FIELDS": ("INFORMATION_SYSTEM_TYPE", "FISMA_REPORTABLE",
                              "FINANCIAL_SYSTEM", "MISSION_CRITICAL",
                              "CRITICAL_INFRASTRUCTURE", "PACKAGE_TYPE",
                              "PIA_REQUIRED", "INFORMATION_CLASSIFICATION"),
            "MAPPING_TYPE": "Extension Property",
            "PARENT_PATH": "system-security-plan.system-characteristics",
            "COLLECTION_PATH": "system-security-plan.system-characteristics.props[]",
        },),
        "MODEL_ALIASES": ("SSP", "System Security Plan", "SSP - Metadata",
                          "SSP - System Characteristics", "SSP - System Implementation",
                          "SSP - Control Implementation"),
        "STORAGE_CONTRACT": _SSP_STORAGE_CONTRACT,
    },
    "ASSESSMENT_RESULTS": {
        "MODEL_KEY": "ASSESSMENT_RESULTS", "ROOT_PATH": "assessment-results",
        "POLICY": "observation-scores-v2",
        "LOOKUP_GROUPS": (),
        "MODEL_ALIASES": ("ASSESSMENT_RESULTS", "Assessment Results", "AR"),
        "SELECTED_FIELDS": AR_ACCEPTED_FIELDS,
        "ELEMENT_PATHS": ("assessment-results",
                          "assessment-results.results[]",
                          "assessment-results.results[].observations[]"),
        # Actual AR destination names/physical columns have not been verified.
        # This permits graph preview only; COMMIT must refuse this contract.
        "STORAGE_CONTRACT": None,
    },
}
_enabled_models = _selected_model_keys(SELECTED_MODELS, MODEL_CONTRACTS)
# Compatibility aliases are derived, never separately selected. An AR-only
# selection must not retain SSP destinations in CONFIG or source BASE_CONFIG.
CONFIG["OSCAL_MODEL"] = _enabled_models[0]
CONFIG["ROOT_PATH"] = MODEL_CONTRACTS[_enabled_models[0]]["ROOT_PATH"]
_default_storage = MODEL_CONTRACTS[_enabled_models[0]].get("STORAGE_CONTRACT")
if _default_storage and _default_storage.get("VERIFIED") is True:
    for _key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        CONFIG[_key] = _default_storage[_key]

SOURCE_PROFILES = (
    {
        "SOURCE_KEY": "source-one",
        "SOURCE_SYSTEM_NAME": CONFIG["SOURCE_SYSTEM_NAME"],
        "SOURCE_TABLE_NAME": CONFIG["SOURCE_TABLE_NAME"],
        "RAW_TABLE": CONFIG["RAW_TABLE"],
        "CONTENT_ID_COLUMN": "CONTENT_ID", "CURATED_JSON_COLUMN": "CURATED_JSON",
        "MAPPING_FILE": CONFIG["MAPPING_FILE"],
        "MAPPING_SOURCE_COLUMN": None,
        "MODEL_KEYS": _enabled_models,
        "SOURCE_ORDER_CANDIDATES": tuple(CONFIG["SOURCE_ORDER_CANDIDATES"]),
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
        "BASE_CONFIG": dict(CONFIG),
    },
)
print("Cell 1 initialized")
print("Selected OSCAL models:", list(_enabled_models))
print("OSCAL version:", CONFIG["OSCAL_VERSION"])
print("Writes enabled:", CONFIG["EXECUTE_WRITES"])
print("Enabled source/model routes:", [
    (profile["SOURCE_KEY"], list(profile["MODEL_KEYS"])) for profile in SOURCE_PROFILES
])
