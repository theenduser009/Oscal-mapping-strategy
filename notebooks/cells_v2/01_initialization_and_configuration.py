# %% Cell 1 - Initialization and configuration

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, lit, row_number, sha2, to_json
from snowflake.snowpark.window import Window

import copy
import datetime
import hashlib
import json
import re
import uuid


session = get_active_session()

# One selector. Field mappings live in the CSV; the existing registry supplies
# structure and identity. Only three sparse execution rules extend it.
SELECTED_MODELS = ("SSP", "ASSESSMENT_RESULTS")

CONFIG = {
    "OSCAL_VERSION": "1.2.3",
    "SSP_DOCUMENT_VERSION": "1.0",
    "EXECUTE_WRITES": False,
    "BUILD_COVERAGE_REPORT": True,
    "ARCHER_META_VALUE_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE",
    "ELEMENT_REGISTRY_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY",
    "IDENTITY_VERSION": "v1_registry_path_instance",
    "METADATA_RELEASE": "lean-registry-v1",
}

SOURCE_FILES = [
    {
        "SOURCE_KEY": "source-one",
        "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
        "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
        "CONTENT_ID_COLUMN": "CONTENT_ID",
        "CURATED_JSON_COLUMN": "CURATED_JSON",
        "MAPPING_FILE": "ARCHER_OSCAL_MAPPINGS.csv",
        "MAPPING_SOURCE_COLUMN": "SOURCE_KEY",
        "SOURCE_ORDER_CANDIDATES": [
            "DW_LOAD_TIMESTAMP_TZ",
            "DW_LOAD_TIMESTAMP",
            "UPDATED_DATE",
            "LAST_UPDATED_DATE",
            "MODIFIED_DATE",
            "CREATE_DATE",
        ],
        "LOOKUP_CONTRACTS": {
            "software": {
                "source_table": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW",
                "title_field": "SOFTWARE_NAME",
                "description_field": "DESCRIPTION",
            },
            "interconnection": {
                "source_table": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW",
                "title_field": "INTERCONNECTION_NAME",
                "description_field": "DESCRIPTION",
            },
        },
        "MODEL_BINDINGS": ["SSP", "ASSESSMENT_RESULTS"],
        "MAPPING_SOURCE_VALUE": "source-one",
        "MAPPING_ENCODING": "utf-8-sig",
    },
]

ROUTING_METADATA = {
    "DEFERRED_MODEL_LABELS": [
        "TBD",
        "N/A - Calculated",
        "Multiple - See Notes",
    ],
    "DEFERRED_TARGET_PATHS": [
        "TBD",
        "All Nulls",
        "Multiple - See Notes",
    ],
}

# Storage guards describe the verified destination, not registry defaults.
MODEL_CONTRACTS = {
    "SSP": {
        "MODEL_KEY": "SSP",
        "POLICY": "metadata-v1",
        "UNREVIEWED_ROWS": "DEFER",
        "LOOKUP_GROUPS": ["components"],
        "MODEL_ALIASES": [
            "SSP",
            "System Security Plan",
            "SSP - Metadata",
            "SSP - System Characteristics",
            "SSP - System Implementation",
            "SSP - Control Implementation",
        ],
        "STORAGE_CONTRACT": {
            "VERIFIED": True,
            "PHYSICAL_PROFILE": "BINARY16_UUID32",
            "MODEL_KEY": "SSP",
            "ROOT_PATH": "system-security-plan",
            "ROOT_ELEMENT_TYPE": "system-security-plan",
            "SOURCE_SYSTEM_NAME": "ARCHER",
            "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
            "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
            "TARGET_DIM": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT",
            "TARGET_FACT": "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY",
            "DIM_PK_COLUMN": "PK_OSCAL_SSP_ELEMENT_HASH",
            "FACT_PK_COLUMN": "PK_FACT_OSCAL_DEPENDENCY_HASH",
            "IDENTITY_VERSION": "v1_registry_path_instance",
        },
        "RUNTIME_OPTIONS": {
            "parse_decimal": False,
            "null_source_as_empty": True,
            "aggregate_invalid": False,
            "allow_nan": True,
        },
    },
    "ASSESSMENT_RESULTS": {
        "MODEL_KEY": "ASSESSMENT_RESULTS",
        "POLICY": "metadata-v1",
        "UNREVIEWED_ROWS": "DEFER",
        "LOOKUP_GROUPS": [],
        "MODEL_ALIASES": [
            "ASSESSMENT_RESULTS",
            "Assessment Results",
            "AR",
        ],
        "STORAGE_CONTRACT": None,
        "RUNTIME_OPTIONS": {
            "parse_decimal": True,
            "null_source_as_empty": False,
            "aggregate_invalid": True,
            "allow_nan": False,
        },
        "REPORT": {
            "MAPPING_RELEASE": "ar-observation-scores-v2-17-fields",
            "REPRESENTATION": "one-named-property-per-observation",
        },
    },
}


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


if not isinstance(MODEL_CONTRACTS, dict) or not MODEL_CONTRACTS:
    raise ValueError("Deployment configuration must define models")
for _model_key, _contract in MODEL_CONTRACTS.items():
    if not isinstance(_contract, dict) or _contract.get("MODEL_KEY") != _model_key:
        raise ValueError("Invalid model deployment identity")
    if _contract.get("POLICY") != "metadata-v1":
        raise ValueError("Active models require the shared metadata policy")
    if {"REGISTRY_METADATA_VERSION", "ROOT_PATH", "ELEMENTS", "DEFAULT_ELEMENT", "REFERENCE_GROUPS",
            "REQUIRED_RULE_IDS", "ELEMENT_PATHS", "MAPPING_RULES", "PATH_RULES",
            "EXCLUDED_FIELDS", "SELECTED_FIELDS"} & _contract.keys():
        raise ValueError("Graph structure belongs in the registry; field rules belong in the mapping CSV")
_enabled_models = _selected_model_keys(SELECTED_MODELS, MODEL_CONTRACTS)
if not isinstance(CONFIG, dict) or CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Deployment configuration must keep normal mapper writes disabled")
CONFIG["RUN_ID"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CONFIG["OSCAL_MODEL"] = _enabled_models[0]
# Root paths are resolved from the live registry in Cell Three, not guessed here.
# Compatibility targets are projected only from a verified default contract.
_default_storage = MODEL_CONTRACTS[_enabled_models[0]].get("STORAGE_CONTRACT")
for _key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
    if _default_storage and _default_storage.get("VERIFIED") is True:
        CONFIG[_key] = _default_storage[_key]
    else:
        CONFIG.pop(_key, None)

if not isinstance(SOURCE_FILES, (tuple, list)) or not SOURCE_FILES:
    raise ValueError("Deployment configuration must define source bindings")
_source_profiles = []
_source_keys = set()
for _source in SOURCE_FILES:
    if not isinstance(_source, dict):
        raise ValueError("Source binding must be an object")
    _profile = copy.deepcopy(_source)
    _source_key = _profile.get("SOURCE_KEY")
    if not isinstance(_source_key, str) or not _source_key.strip() or _source_key in _source_keys:
        raise ValueError("Source metadata requires distinct nonblank source keys")
    _source_keys.add(_source_key)
    _bindings = _selected_model_keys(_profile.get("MODEL_BINDINGS"), MODEL_CONTRACTS)
    _routes = tuple(model for model in _enabled_models if model in _bindings)
    if not _routes:
        continue
    for _key in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "RAW_TABLE", "MAPPING_FILE"):
        if not isinstance(_profile.get(_key), str) or not _profile[_key].strip():
            raise ValueError("Source metadata is missing a required binding")
    _profile["MODEL_KEYS"] = _routes
    _profile["BASE_CONFIG"] = copy.deepcopy(CONFIG)
    _source_profiles.append(_profile)
SOURCE_PROFILES = tuple(_source_profiles)
if any(not any(model in profile["MODEL_KEYS"] for profile in SOURCE_PROFILES)
       for model in _enabled_models):
    raise ValueError("Selected model has no approved source binding")
# Historical diagnostics resolve the first source, never choose routes.
for _key in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "RAW_TABLE", "MAPPING_FILE"):
    CONFIG[_key] = SOURCE_PROFILES[0][_key]
CONFIG["SOURCE_ORDER_CANDIDATES"] = copy.deepcopy(
    SOURCE_PROFILES[0].get("SOURCE_ORDER_CANDIDATES", []))
print("Cell 1 initialized")
print("Metadata release:", CONFIG["METADATA_RELEASE"])
print("Selected OSCAL models:", list(_enabled_models))
print("Writes enabled:", CONFIG["EXECUTE_WRITES"])
print("Enabled source/model routes:", [
    (profile["SOURCE_KEY"], list(profile["MODEL_KEYS"])) for profile in SOURCE_PROFILES
])
