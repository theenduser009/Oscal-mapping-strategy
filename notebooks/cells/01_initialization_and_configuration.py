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

import copy
from pathlib import Path
import datetime
import hashlib
import json
import re
import uuid


session = get_active_session()

# One selector. Capabilities, source bindings, mappings, and destinations
# come from the reviewed metadata artifact, not per-model Python branches.
SELECTED_MODELS = ("SSP", "ASSESSMENT_RESULTS")
MAPPER_METADATA_FILE = "mapper_contract.v1.json"


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


def _load_mapper_catalog(filename):
    # In Snowflake, upload the reviewed JSON alongside the mapping CSV.
    # Local repository execution may resolve the checked-in deployment artifact.
    path = Path(filename)
    if not path.is_file() and "__file__" in globals():
        origin = Path(__file__).resolve()
        for directory in (origin.parent, *origin.parents):
            candidate = directory / "metadata" / filename
            if candidate.is_file():
                path = candidate
                break
    if not path.is_file():
        raise ValueError("Reviewed mapper metadata file is missing; upload it to notebook Files")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate key in mapper metadata")
            result[key] = value
        return result
    with path.open(encoding="utf-8") as handle:
        catalog = json.load(handle, object_pairs_hook=unique_object)
    if not isinstance(catalog, dict) or catalog.get("CATALOG_VERSION") != 1:
        raise ValueError("Unsupported mapper metadata catalog version")
    if not isinstance(catalog.get("MODELS"), dict) or not catalog["MODELS"]:
        raise ValueError("Mapper metadata must define models")
    if not isinstance(catalog.get("SOURCES"), list) or not catalog["SOURCES"]:
        raise ValueError("Mapper metadata must define source bindings")
    if not isinstance(catalog.get("CONFIG_DEFAULTS"), dict):
        raise ValueError("Mapper metadata defaults must be an object")
    for key, contract in catalog["MODELS"].items():
        if not isinstance(contract, dict) or contract.get("MODEL_KEY") != key:
            raise ValueError("Invalid model metadata identity")
        if contract.get("POLICY") != "metadata-v1" or not contract.get("ROOT_PATH"):
            raise ValueError("Active models require the metadata-driven engine and a root")
    return catalog


MAPPER_CATALOG = _load_mapper_catalog(MAPPER_METADATA_FILE)
MODEL_CONTRACTS = copy.deepcopy(MAPPER_CATALOG["MODELS"])
_enabled_models = _selected_model_keys(SELECTED_MODELS, MODEL_CONTRACTS)
CONFIG = copy.deepcopy(MAPPER_CATALOG["CONFIG_DEFAULTS"])
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Reviewed metadata must keep normal mapper writes disabled")
CONFIG["RUN_ID"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CONFIG["METADATA_RELEASE"] = MAPPER_CATALOG.get("RELEASE_ID")
CONFIG["OSCAL_MODEL"] = _enabled_models[0]
CONFIG["ROOT_PATH"] = MODEL_CONTRACTS[_enabled_models[0]]["ROOT_PATH"]
# Compatibility aliases only; Cell Seven uses source/model contexts.
_default_storage = MODEL_CONTRACTS[_enabled_models[0]].get("STORAGE_CONTRACT")
for _key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
    CONFIG.pop(_key, None)
if _default_storage and _default_storage.get("VERIFIED") is True:
    for _key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        CONFIG[_key] = _default_storage[_key]

_source_profiles = []
_source_keys = set()
for _source in MAPPER_CATALOG["SOURCES"]:
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
print("Cell 1 initialized")
print("Metadata release:", CONFIG["METADATA_RELEASE"])
print("Selected OSCAL models:", list(_enabled_models))
print("Writes enabled:", CONFIG["EXECUTE_WRITES"])
print("Enabled source/model routes:", [
    (profile["SOURCE_KEY"], list(profile["MODEL_KEYS"])) for profile in SOURCE_PROFILES
])
