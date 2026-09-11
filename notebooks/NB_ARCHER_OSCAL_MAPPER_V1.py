"""NB_ARCHER_OSCAL_MAPPER_V1

One seven-cell Source One to SSP/Assessment Results mapping workflow.
Copy each Cell N section into its existing Python cell and run in order.
Default PREVIEW: no target DML. AR destination contract remains pending.
See docs/SHARED_SEVEN_CELL_MAPPER.md for scope and run instructions.
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


# %% Cell 2 - Source, mapping, registry, and Archer value inputs

import csv
import pandas as pd


def _normalized_columns(columns):
    result = {}
    for name in columns:
        key = str(name).strip().upper()
        if key in result:
            raise ValueError("Duplicate normalized source column")
        result[key] = name
    return result


def _required_lookup_column(columns, expected_name, component_type):
    names = _normalized_columns(columns)
    if expected_name not in names:
        raise ValueError("Required lookup column missing: " + expected_name)
    return names[expected_name]


def _input_no_transaction(active_session):
    # Temporary-table DDL must never commit somebody else's open transaction.
    try:
        current = active_session.sql("SELECT CURRENT_TRANSACTION() AS TX").collect()[0]["TX"]
    except Exception:
        raise ValueError("Cannot verify transaction state before input snapshot") from None
    if current is not None:
        raise ValueError("Finish the existing transaction before input snapshot")


def load_source_input(active_session, profile):
    _input_no_transaction(active_session)
    raw = active_session.table(profile["RAW_TABLE"])
    columns = _normalized_columns(raw.columns)
    id_name = profile.get("CONTENT_ID_COLUMN", "CONTENT_ID").upper()
    json_name = profile.get("CURATED_JSON_COLUMN", "CURATED_JSON").upper()
    if id_name not in columns or json_name not in columns:
        raise ValueError("Source requires its configured identity and curated JSON columns")
    selected = [col(columns[id_name]).cast("string").alias("SOURCE_RECORD_ID"),
                col(columns[json_name]).alias("CURATED_JSON")]
    order_columns = []
    for candidate in profile.get("SOURCE_ORDER_CANDIDATES", ()):
        if candidate in columns:
            selected.append(col(columns[candidate]).alias(candidate))
            order_columns.append(candidate)
    # Freeze once in a session-local temporary table, before validation and
    # model fan-out. Keep the returned cache handle alive in SOURCE_INPUTS.
    candidates = raw.select(*selected).cache_result()
    if candidates.filter("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0").count():
        raise ValueError("Source contains missing record identities")
    count = candidates.count()
    distinct = candidates.select("SOURCE_RECORD_ID").distinct().count()
    if count != distinct:
        if not order_columns:
            raise ValueError("Duplicate source identities require approved technical ordering")
        order = [col(name).desc_nulls_last() for name in order_columns]
        order.append(sha2(to_json(col("CURATED_JSON")), 256).desc_nulls_last())
        result = candidates.with_column(
            "_SOURCE_ROW_NUMBER", row_number().over(
                Window.partition_by("SOURCE_RECORD_ID").order_by(*order)
            )
        ).filter(col("_SOURCE_ROW_NUMBER") == lit(1)).drop(
            "_SOURCE_ROW_NUMBER", *order_columns
        )
    else:
        result = candidates.select("SOURCE_RECORD_ID", "CURATED_JSON")
    selected_count = result.count()
    if selected_count != result.select("SOURCE_RECORD_ID").distinct().count():
        raise ValueError("Source selection did not produce unique identities")
    return result, {"RAW_ROWS": count, "SELECTED_ROWS": selected_count,
                    "DUPLICATE_SOURCE_ROWS_RESOLVED": count - selected_count}, candidates


def _read_mapping_header(mapping_file):
    # Inspect the real header before pandas can mangle repeated column names.
    # Use the same encoding and CSV quoting rules as the mapping-file read.
    with open(mapping_file, encoding="cp1252", newline="") as handle:
        header = next((row for row in csv.reader(handle)
                       if row and any(value.strip() for value in row)), None)
    if header is None:
        raise ValueError("Mapping CSV header is missing")
    return header


def load_mapping_rows(profile):
    header = [str(name).strip().upper()
              for name in _read_mapping_header(profile["MAPPING_FILE"])]
    if len(header) != len(set(header)):
        raise ValueError("Duplicate normalized mapping columns")
    frame = pd.read_csv(profile["MAPPING_FILE"], encoding="cp1252", dtype=str)
    frame = frame.where(lambda data: data.notna(), None)
    frame.columns = [str(name).strip().upper() for name in frame.columns]
    if len(frame.columns) != len(set(frame.columns)):
        raise ValueError("Duplicate normalized mapping columns")
    source_column = profile.get("MAPPING_SOURCE_COLUMN")
    if source_column:
        source_column = source_column.upper()
        if source_column not in frame.columns:
            raise ValueError("Mapping source binding column is missing")
        binding = profile.get("MAPPING_SOURCE_VALUE", profile["SOURCE_TABLE_NAME"])
        frame = frame[frame[source_column].map(
            lambda value: str(value or "").strip() == binding
        )].copy()
    return frame


def load_source_lookups(active_session, profile, model_contracts, shared_config):
    _input_no_transaction(active_session)
    values = active_session.table(shared_config["ARCHER_META_VALUE_TABLE"]).select(
        col("SELECT_VALUE_ID"), col("SELECT_VALUE_NAME")
    ).filter(col("SELECT_VALUE_NAME").is_not_null())
    archer = {}
    for row in values.collect():
        if row["SELECT_VALUE_ID"] is not None:
            key = str(row["SELECT_VALUE_ID"]).strip()
            value = str(row["SELECT_VALUE_NAME"]).strip()
            if key in archer and archer[key] != value:
                raise ValueError("Archer lookup identity has conflicting labels")
            archer[key] = value
    components = {}
    required = {group for key in profile["MODEL_KEYS"]
                for group in model_contracts[key].get("LOOKUP_GROUPS", ())}
    # Lookup requirements are data in the source profile, not table names in
    # the shared input loader. Only profiles that need them read them.
    for kind, contract in profile.get("LOOKUP_CONTRACTS", {}).items():
        if "components" not in required:
            continue
        table = active_session.table(contract["source_table"])
        names = _normalized_columns(table.columns)
        if not {"CONTENT_ID", "CURATED_JSON"}.issubset(names):
            raise ValueError("Configured component lookup columns are missing")
        components[kind] = table.select(
            col(names["CONTENT_ID"]).alias("CONTENT_ID"),
            col(names["CURATED_JSON"]).alias("CURATED_JSON")
        ).cache_result()
    return {"archer_values": archer,
            "fips_values": {key: value for key, value in archer.items()
                            if value.lower() in {"low", "moderate", "high"}},
            "component_sources": components,
            "component_contract": profile.get("LOOKUP_CONTRACTS", {})}


# Each source is selected once for this workflow; model routes reuse that
# source-local snapshot. Sources are never unioned or deduplicated together.
SOURCE_INPUTS = {}
MAPPING_INPUTS = {}
MAPPING_FRAMES = {}
source_selection_reports = {}
for source_profile in SOURCE_PROFILES:
    source_key = source_profile["SOURCE_KEY"]
    if source_key in SOURCE_INPUTS:
        raise ValueError("Duplicate configured source key")
    frame, selection, snapshot = load_source_input(session, source_profile)
    artifact = load_mapping_rows(source_profile)
    SOURCE_INPUTS[source_key] = {
        "source_df": frame,
        "snapshot": snapshot,
        "lookups": load_source_lookups(session, source_profile, MODEL_CONTRACTS, CONFIG),
    }
    MAPPING_FRAMES[source_key] = artifact
    MAPPING_INPUTS[source_key] = artifact.to_dict(orient="records")
    source_selection_reports[source_key] = selection
element_registry_df = session.table(CONFIG["ELEMENT_REGISTRY_TABLE"])
REGISTRY_INPUT_ROWS = [row.as_dict(recursive=True) for row in element_registry_df.collect()]

# Compatibility aliases for historical read-only diagnostics. Cell 7 does not
# use these aliases to choose a model or cross source boundaries.
_default_source_key = SOURCE_PROFILES[0]["SOURCE_KEY"]
source_df = SOURCE_INPUTS[_default_source_key]["source_df"]
mapping_artifact_pdf = MAPPING_FRAMES[_default_source_key]
mapping_df = session.create_dataframe(mapping_artifact_pdf)
ARCHER_VALUE_LOOKUP = SOURCE_INPUTS[_default_source_key]["lookups"]["archer_values"]
FIPS_199_VALUE_LOOKUP = SOURCE_INPUTS[_default_source_key]["lookups"]["fips_values"]
COMPONENT_HYDRATION_SOURCE_DFS = SOURCE_INPUTS[_default_source_key]["lookups"]["component_sources"]
COMPONENT_HYDRATION_SOURCE_CONTRACT = SOURCE_PROFILES[0].get("LOOKUP_CONTRACTS", {})
selected_source_count = source_selection_reports[_default_source_key]["SELECTED_ROWS"]
source_row_count = source_selection_reports[_default_source_key]["RAW_ROWS"]
print("Source selection reports:", source_selection_reports)


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


import copy
import math
import re


def _meta_row(original):
    if hasattr(original, "as_dict"):
        original = original.as_dict(recursive=True)
    if not isinstance(original, dict):
        raise ValueError("Expected a metadata row object")
    result = {}
    for key, value in original.items():
        key = str(key).strip().upper()
        key = MAPPING_COLUMN_ALIASES.get(key, key)
        if key in result:
            raise ValueError("Ambiguous metadata column aliases")
        if value is None or isinstance(value, float) and math.isnan(value):
            value = None
        elif isinstance(value, str):
            value = value.strip()
        result[key] = value
    return result


def _model_token(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _metadata_active(row):
    return str(row.get("IS_ACTIVE", row.get("ACTIVE", True))).upper() not in {
        "FALSE", "F", "NO", "N", "0"
    }


def _registry_model(row):
    return str(row.get("OSCAL_MODEL_KEY") or row.get("OSCAL_MODEL") or
               row.get("MODEL_NAME") or "").strip().upper()


def _registry_path(row):
    return str(row.get("NODE_PATH") or row.get("OSCAL_ELEMENT_PATH") or
               row.get("ELEMENT_PATH") or row.get("JSON_PATH") or "").strip()


def _model_aliases(model_contracts):
    aliases = {}
    for model, contract in model_contracts.items():
        for label in (model,) + tuple(contract.get("MODEL_ALIASES", ())):
            token = _model_token(label)
            if not token or token in aliases and aliases[token] != model:
                raise ValueError("Ambiguous model aliases")
            aliases[token] = model
    return aliases


def _validate_source_profiles(source_profiles, model_contracts, mapping_rows):
    if not isinstance(mapping_rows, dict) or not source_profiles:
        raise ValueError("Explicit source-to-mapping bindings are required")
    _model_aliases(model_contracts)
    keys, tables, physical = set(), set(), set()
    for profile in source_profiles:
        for field in ("SOURCE_KEY", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
                      "RAW_TABLE", "MAPPING_FILE"):
            if not isinstance(profile.get(field), str) or not profile[field].strip():
                raise ValueError("Source profile field is missing: " + field)
        key = profile["SOURCE_KEY"]
        namespace = (profile["SOURCE_SYSTEM_NAME"].upper(), profile["SOURCE_TABLE_NAME"].upper())
        physical_name = profile["RAW_TABLE"].upper()
        if key in keys or namespace in tables or physical_name in physical:
            raise ValueError("Duplicate source profile identity")
        keys.add(key)
        tables.add(namespace)
        physical.add(physical_name)
        models = tuple(profile.get("MODEL_KEYS", ()))
        if not models or len(models) != len(set(models)):
            raise ValueError("Model routes must be nonempty and unique")
        if any(model not in model_contracts for model in models):
            raise ValueError("Unknown enabled model")
        if set(profile.get("MODEL_STORAGE_CONTRACTS", {})) - set(models):
            raise ValueError("Storage contract override has no enabled model route")
        for model in models:
            contract = model_contracts[model]
            if contract.get("MODEL_KEY") != model or not contract.get("ROOT_PATH"):
                raise ValueError("Model contract identity is invalid")
        if key not in mapping_rows or not isinstance(mapping_rows[key], list):
            raise ValueError("Missing source mapping input")
    if set(mapping_rows) != keys:
        raise ValueError("Unknown source mapping input key")


def _owner_for_path(path, paths):
    candidates = [p for p in paths if path == p or path.startswith(p + ".")]
    return max(candidates, key=lambda p: (p.count("."), len(p))) if candidates else None


def _apply_mapping_path_rules(row, contract, paths):
    path = str(row.get("OSCAL_ELEMENT_PATH") or "")
    field = row.get("SOURCE_FIELD_NAME")
    kind = _model_token(row.get("MAPPING_TYPE") or "Direct")
    for rule in contract.get("PATH_RULES", ()):
        if field not in rule["SOURCE_FIELDS"] or kind != _model_token(rule["MAPPING_TYPE"]):
            continue
        parent, props = rule["PARENT_PATH"], rule["COLLECTION_PATH"]
        if _owner_for_path(path, paths) not in {parent, props}:
            continue
        relative = path[len(parent):].lstrip(".")
        direct_leaf = not any(token in relative for token in (".", "[", "]"))
        if direct_leaf or path in {props, props + ".name", props + ".value"}:
            if props not in paths:
                raise ValueError("Approved collection route requires active registry path")
            return props + ".value"
    return path


def compile_mapping_contexts(mapping_rows, registry_rows, source_profiles, model_contracts):
    """Pure source/model routing. No data reads, globals mutation or writes."""
    _validate_source_profiles(source_profiles, model_contracts, mapping_rows)
    aliases = _model_aliases(model_contracts)
    registry = [_meta_row(row) for row in registry_rows]
    active = [row for row in registry if _metadata_active(row)]
    root_models = {}
    for row in active:
        path, model = _registry_path(row), _registry_model(row)
        parent = row.get("PARENT_NODE_PATH") or row.get("PARENT_ELEMENT_PATH") or row.get("PARENT_PATH")
        if path and not parent and "." not in path and model:
            if path in root_models and root_models[path] != model:
                raise ValueError("Registry root belongs to multiple models")
            root_models[path] = model
            aliases.setdefault(_model_token(model), model)
    for model, contract in model_contracts.items():
        root = contract["ROOT_PATH"]
        if root in root_models and root_models[root] != model:
            raise ValueError("Configured root conflicts with registry model")
        root_models[root] = model
    contexts = []
    for profile in source_profiles:
        rows = [_meta_row(row) for row in mapping_rows[profile["SOURCE_KEY"]]]
        for model in profile["MODEL_KEYS"]:
            contract = copy.deepcopy(model_contracts[model])
            if model in profile.get("MODEL_STORAGE_CONTRACTS", {}):
                contract["STORAGE_CONTRACT"] = copy.deepcopy(profile["MODEL_STORAGE_CONTRACTS"][model])
            model_registry = [row for row in active if _registry_model(row) == model]
            paths = [_registry_path(row) for row in model_registry]
            if len(paths) != len(set(paths)):
                raise ValueError("Duplicate active registry path")
            if contract["ROOT_PATH"] not in paths:
                raise ValueError("Configured model registry root is absent")
            selected_paths = contract.get("ELEMENT_PATHS")
            if selected_paths:
                if not set(selected_paths).issubset(paths):
                    raise ValueError("Required model collection is absent from registry")
                model_registry = [row for row in model_registry if _registry_path(row) in selected_paths]
                paths = list(selected_paths)
            report = {"STATUS": "READY", "INPUT_ROWS": len(rows), "SELECTED_ROWS": 0,
                      "EXCLUDED_ROWS": 0, "DEFERRED_ROWS": 0, "BLOCKED_ROWS": 0,
                      "ISSUES": []}
            selected = []
            for index, row in enumerate(rows):
                field = row.get("SOURCE_FIELD_NAME")
                path = str(row.get("OSCAL_ELEMENT_PATH") or "")
                label = _model_token(row.get("OSCAL_MODEL"))
                labelled = aliases.get(label)
                root = path.split(".", 1)[0]
                path_model = root_models.get(root)
                classification, reason = None, None
                if not field:
                    classification, reason = "BLOCKED_ROWS", "MISSING_SOURCE_FIELD"
                elif labelled and path_model and labelled != path_model:
                    classification, reason = "BLOCKED_ROWS", "MODEL_PATH_CONFLICT"
                elif label and not labelled and label not in {"extensionproperty", "extensionproperties"}:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_LABEL"
                elif path and path_model is None:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif path_model and path_model != model or not path and labelled and labelled != model:
                    classification = "EXCLUDED_ROWS"
                elif contract.get("SELECTED_FIELDS") and field not in contract["SELECTED_FIELDS"]:
                    classification = "EXCLUDED_ROWS"
                elif not path:
                    classification, reason = "DEFERRED_ROWS", "MISSING_TARGET_PATH"
                elif path_model != model:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif _model_token(row.get("STATUS")) in {"deferred", "blocked", "tbd", "moreinformationneeded", "notmapped"} or _model_token(row.get("MAPPING_TYPE")) == "tbd":
                    classification, reason = "DEFERRED_ROWS", "UNAPPROVED_MAPPING"
                if classification:
                    report[classification] += 1
                    if reason:
                        report["ISSUES"].append({"row": index, "field": field, "reason": reason})
                    continue
                canonical = dict(row)
                canonical_path = _apply_mapping_path_rules(canonical, contract, paths)
                owner = _owner_for_path(canonical_path, paths)
                if owner is None:
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field, "reason": "UNREGISTERED_PATH"})
                    continue
                relative = canonical_path[len(owner):].lstrip(".")
                if "[]" in relative:
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field, "reason": "UNREGISTERED_COLLECTION"})
                    continue
                canonical.update(ARTIFACT_MODEL=row.get("ARTIFACT_MODEL", row.get("OSCAL_MODEL")),
                                 CANONICAL_ELEMENT_PATH=canonical_path,
                                 OWNER_ELEMENT_PATH=owner, FIELD_RELATIVE_PATH=relative,
                                 OSCAL_MODEL=model, SOURCE_KEY=profile["SOURCE_KEY"])
                if not canonical.get("OSCAL_FIELD_NAME"):
                    canonical["OSCAL_FIELD_NAME"] = relative.split(".")[-1].replace("[]", "") if relative else None
                canonical["MAPPING_TYPE"] = canonical.get("MAPPING_TYPE") or "Direct"
                canonical["STATUS"] = canonical.get("STATUS") or "In Progress"
                selected.append(canonical)
                report["SELECTED_ROWS"] += 1
            selected.sort(key=lambda row: (row["OWNER_ELEMENT_PATH"], row["OSCAL_ELEMENT_PATH"], row["SOURCE_FIELD_NAME"]))
            grouped = {}
            for row in selected:
                grouped.setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
            if report["BLOCKED_ROWS"]:
                report["STATUS"] = "BLOCKED"
            cfg = copy.deepcopy(profile.get("BASE_CONFIG", {}))
            for key in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "RAW_TABLE"):
                cfg[key] = profile[key]
            cfg.update(OSCAL_MODEL=model, ROOT_PATH=contract["ROOT_PATH"],
                       STORAGE_CONTRACT=copy.deepcopy(contract.get("STORAGE_CONTRACT")),
                       EXECUTE_WRITES=False)
            root_row = next(row for row in model_registry if _registry_path(row) == contract["ROOT_PATH"])
            cfg["ROOT_ELEMENT_TYPE"] = root_row.get("ELEMENT_TYPE") or contract["ROOT_PATH"]
            if cfg["STORAGE_CONTRACT"]:
                for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
                    cfg[key] = cfg["STORAGE_CONTRACT"][key]
            else:
                for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
                    cfg.pop(key, None)
            contexts.append({"source_key": profile["SOURCE_KEY"], "config": cfg,
                             "mapping_rows": selected, "mappings_by_path": grouped,
                             "model_contract": contract, "registry_rows": model_registry,
                             "routing_report": report})
    return contexts


MAPPING_CONTEXTS = compile_mapping_contexts(
    MAPPING_INPUTS, REGISTRY_INPUT_ROWS, SOURCE_PROFILES, MODEL_CONTRACTS
)
# Legacy SSP aliases are observational only; the active runner uses contexts.
_default_context = next((context for context in MAPPING_CONTEXTS
                         if context["config"]["OSCAL_MODEL"] == CONFIG["OSCAL_MODEL"]),
                        MAPPING_CONTEXTS[0])
CANONICAL_MAPPING_ROWS = _default_context["mapping_rows"]
MAPPINGS_BY_ELEMENT_PATH = _default_context["mappings_by_path"]
canonical_mapping_pdf = pd.DataFrame(CANONICAL_MAPPING_ROWS)
canonical_mapping_df = session.create_dataframe(canonical_mapping_pdf)
active_registry_paths = [_registry_path(row) for row in _default_context["registry_rows"]]
print("Mapping routes:", [
    {"source": context["source_key"], "model": context["config"]["OSCAL_MODEL"],
     **context["routing_report"]} for context in MAPPING_CONTEXTS
])


# %% Cell 4 - Generic parsing, transformation, and payload helpers

import datetime
import math
from decimal import Decimal

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


def _context_config(context=None):
    return context["config"] if context is not None else globals().get("CONFIG", {})


def _context_mappings(context=None):
    return context["mappings_by_path"] if context is not None else globals().get("MAPPINGS_BY_ELEMENT_PATH", {})


def _context_lookup(name, legacy_name, context=None):
    return context.get("lookups", {}).get(name, {}) if context is not None else globals().get(legacy_name, {})


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


def resolve_archer_select_value(value, context=None):
    value_lookup = _context_lookup("archer_values", "ARCHER_VALUE_LOOKUP", context)
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
            if key not in value_lookup or not _has_value(
                value_lookup[key]
            ):
                raise ValueError("Archer select-value ID is unresolved")
            return value_lookup[key]
        return value_lookup.get(key, item)

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
    context=None,
):
    if _context_config(context).get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Component hydration must be built before guarded writes"
        )
    if not isinstance(hydration_source_dfs, dict):
        raise RuntimeError("Component hydration sources are unavailable")
    if set(hydration_source_dfs) != set(COMPONENT_HYDRATION_CONTRACT):
        raise RuntimeError("Component hydration source contract is incomplete")
    source_contract = (
        context.get("lookups", {}).get("component_contract")
        if context is not None else globals().get("COMPONENT_HYDRATION_SOURCE_CONTRACT")
    )
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


def transform_fips_199(value, context=None):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    normalized = []
    for item in values:
        if item is None:
            continue
        key = str(item).strip()
        label = _context_lookup("fips_values", "FIPS_199_VALUE_LOOKUP", context).get(key)
        if label is None:
            candidate = str(_context_lookup("archer_values", "ARCHER_VALUE_LOOKUP", context).get(key, item)).strip().lower()
            if candidate in {"low", "moderate", "high"}:
                label = candidate
        if label is not None:
            normalized.append(label)
    if not normalized:
        return None
    return normalized[0] if len(normalized) == 1 else normalized


def _single_archer_label(value, context=None):
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

    resolved = _context_lookup("archer_values", "ARCHER_VALUE_LOOKUP", context).get(key)
    if resolved is not None:
        label = str(resolved).strip()
        return label or None

    # An already resolved textual label is safe to preserve. An unknown
    # numeric ID is not: it must be added to ARCHER_META_VALUE first.
    if isinstance(item, str) and not key.isdigit():
        return key
    return None


def transform_security_objective(value, context=None):
    normalized = transform_fips_199(value, context)
    if isinstance(normalized, list):
        if len(normalized) != 1:
            raise ValueError(
                "Security objective resolved to multiple FIPS values"
            )
        normalized = normalized[0]
    if _has_value(normalized):
        return str(normalized)

    label = _single_archer_label(value, context)
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


def transform_status_state(value, context=None):
    label = _single_archer_label(value, context)
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


def transform_authorization_date(value):
    # Excel contract: ATOIATO_DATE -> date-authorized, Transform,
    # Notes: Convert timestamp to DateDatatype.
    # Retain the source calendar date; do not invent a timezone or shift days.
    value = _to_python(value)
    if not _has_value(value):
        return SKIP_VALUE
    error_message = (
        "ATOIATO_DATE requires a valid ISO date or ISO timestamp "
        "(YYYY-MM-DD, or YYYY-MM-DDTHH:MM:SS with optional fraction/offset); "
        "numeric epochs, locale dates and object wrappers require source review"
    )
    try:
        if isinstance(value, (datetime.datetime, datetime.date)):
            return datetime.date(value.year, value.month, value.day).isoformat()
        if not isinstance(value, str):
            raise ValueError(error_message)
        text = value.strip()
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
            return datetime.date.fromisoformat(text).isoformat()
        if not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ][0-9]{2}:[0-9]{2}:[0-9]{2}"
            r"(?:\.[0-9]{1,9})?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])?",
            text,
        ):
            raise ValueError(error_message)
        normalized = text[:10] + "T" + text[11:]
        if normalized[-1:] in {"Z", "z"}:
            normalized = normalized[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(normalized).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        # Do not include source values or record IDs in notebook errors.
        raise ValueError(error_message) from None


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


def _active_responsible_party_role_instances(source_obj, source_record_id, context=None):
    instances = []
    emitted_role_ids = set()
    mapping_rows = _context_mappings(context).get(
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
        if not _party_uuid_values(source_record_id, source_value, context):
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


def _party_uuid(source_record_id, identifier, context=None):
    config = _context_config(context)
    if context is not None and not (
        config.get("SOURCE_SYSTEM_NAME") == "ARCHER"
        and config.get("SOURCE_TABLE_NAME") == "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
        and config.get("OSCAL_MODEL") == "SSP"
    ):
        return _deterministic_uuid(
            config["IDENTITY_VERSION"], config["SOURCE_SYSTEM_NAME"],
            config["SOURCE_TABLE_NAME"], source_record_id, config["OSCAL_MODEL"],
            "party", identifier,
        )
    return _deterministic_uuid(
        config["SOURCE_SYSTEM_NAME"],
        source_record_id,
        "party",
        identifier,
    )


def _party_uuid_values(source_record_id, value, context=None):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    party_uuids = []
    for item in values:
        if item is None:
            continue
        party_uuid = _party_uuid(
            source_record_id,
            _party_reference_identifier(item),
            context,
        )
        if party_uuid not in party_uuids:
            party_uuids.append(party_uuid)
    return party_uuids


def _active_responsible_party_instances(source_obj, source_record_id, context=None):
    instances = []
    emitted_party_uuids = set()
    mapping_rows = _context_mappings(context).get(
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

        for party_uuid in _party_uuid_values(source_record_id, source_value, context):
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
    context=None,
):
    assignments_by_role = {}
    mapping_rows = _context_mappings(context).get(
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

        party_uuids = _party_uuid_values(source_record_id, source_value, context)
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


def transform_responsible_party(source_record_id, source_field, value, context=None):
    role_id = RESPONSIBLE_PARTY_ROLE_IDS.get(source_field)
    if role_id is None:
        return SKIP_VALUE
    party_uuids = _party_uuid_values(source_record_id, value, context)
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
    elif source_field == "ATOIATO_DATE" or (
        owner_path == SYSTEM_CHARACTERISTICS_ELEMENT_PATH
        and target_field == "date-authorized"
    ):
        _validate_exact_mapping(
            mapping_row,
            "ATOIATO_DATE",
            SYSTEM_CHARACTERISTICS_ELEMENT_PATH,
            "date-authorized",
            "transform",
            "Authorization date",
        )
        handler = "authorization-date"
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


def apply_mapping_transform(mapping_row, value, source_record_id, context=None):
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
            source_record_id, source_field, value, context
        )
    if handler == "security-objective":
        return transform_security_objective(value, context)
    if handler == "status-state":
        return transform_status_state(value, context)
    if handler == "authorization-date":
        return transform_authorization_date(value)
    if handler == "published":
        return transform_published(value)
    if handler == "last-modified":
        return transform_last_modified(value)
    if handler == "document-identifier":
        return transform_document_identifier(value)
    if handler == "governed-property":
        transformed = resolve_archer_select_value(value, context)
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
    context=None,
):
    is_collection = "[]" in element_path
    instances = []
    aggregate_payload = {}
    resolved_cluster_fields = set()

    if element_path == METADATA_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_instances(
            source_obj,
            source_record_id,
            context,
        )

    if element_path == METADATA_ROLES_ELEMENT_PATH:
        return _active_responsible_party_role_instances(
            source_obj,
            source_record_id,
            context,
        )

    if element_path == RESPONSIBLE_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_assignment_instances(
            source_obj,
            source_record_id,
            context,
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
            mapping_row, source_value, source_record_id, context
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

# Model-specific registry and payload policies, initialized with Cell 4.

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
    row_dict = row.as_dict(recursive=True) if hasattr(row, "as_dict") else dict(row)
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


def _inject_controlled_metadata_fields(element_path, instances, context=None):
    if element_path != METADATA_ELEMENT_PATH:
        return instances

    if len(instances) != 1 or instances[0].get("instance_key") != "singleton":
        raise ValueError("Expected exactly one singleton metadata instance")

    configured_version = str(_context_config(context).get("OSCAL_VERSION") or "").strip()
    if not configured_version:
        raise ValueError("OSCAL_VERSION must be configured for metadata")

    document_version = _context_config(context).get("SSP_DOCUMENT_VERSION")
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
    context=None,
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
        _context_config(context)["IDENTITY_VERSION"],
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


def _canonical_registry_rows(element_registry_dataframe, model_key, context=None):
    rows = []
    supplied_rows = context.get("registry_rows") if context is not None else None
    for row in (supplied_rows if supplied_rows is not None else element_registry_dataframe.collect()):
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
        selected_paths = context["model_contract"].get("ELEMENT_PATHS") if context is not None else None
        if selected_paths is not None and path not in selected_paths:
            continue
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
                "element_type": _registry_value(row, "ELEMENT_TYPE"),
                "raw": row,
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

    if context is None:
        _ssp_registry_policy(rows, None)
    else:
        context["policy"]["registry"](rows, context)
    if len({row["element_path"] for row in rows}) != len(rows):
        raise ValueError("Duplicate registry paths for configured OSCAL model")
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



def _ssp_registry_policy(rows, context=None):
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
    for mapping_row in _context_mappings(context).get(
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

    return rows


# AR v2 is the accepted seventeen-field scope. The later v3 candidate is not
# silently promoted by the shared engine.
_SCORE_ACCEPTED_FIELDS = (
    "VULNERABILITY_SCORE", "ANTIVIRUS_SCORE", "PATCH_SCORE",
    "SECURITY_COMPLIANCE_SCORE",
    "STANDARD_OPERATING_ENVIRONMENT_SCORE", "COMPUTER_PASSWORD_AGE_SCORE",
    "VULNERABILITY_REPORTING_SCORE", "SECURITY_COMPLIANCE_REPORTING_SCORE",
    "TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE", "AVG_AUTHORIZATION_PACKAGE_RISK_SCORE",
    "RISK_SCORE_GRADE", "AVG_VULNERABILITY_SCORE", "AVG_PATCH_SCORE",
    "AVG_ANTIVIRUS_SCORE", "AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE",
    "AVG_COMPUTER_PASSWORD_AGE_SCORE", "AVG_VULNERABILITY_REPORTING_SCORE",
)

_SCORE_ROOT_PATH = "assessment-results"
_SCORE_RESULT_PATH = "assessment-results.results[]"
_SCORE_OBSERVATION_PATH = "assessment-results.results[].observations[]"
_SCORE_NOTES = "archer specific risk scoring map as observation"

def _score_words(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _score_row_dict(row):
    if hasattr(row, "as_dict"):
        row = row.as_dict(recursive=True)
    if not isinstance(row, dict):
        raise ValueError("Expected a mapping or registry row object")
    result = {}
    for key, value in row.items():
        name = str(key).strip().upper()
        if name in result:
            raise ValueError("Duplicate normalized metadata column")
        result[name] = value
    return result



def _score_mapping_contract(mapping_rows):
    aliases = {
        "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME", "SOURCE_FIELD": "SOURCE_FIELD_NAME",
        "MODEL": "OSCAL_MODEL", "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
        "ELEMENT_PATH": "OSCAL_ELEMENT_PATH", "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
        "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME", "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
        "MAPPING_STATUS": "STATUS",
    }
    found = {field: [] for field in _SCORE_ACCEPTED_FIELDS}
    other_rows = 0
    for original in mapping_rows:
        normalized = _score_row_dict(original)
        row = {}
        for key, value in normalized.items():
            canonical = aliases.get(key, key)
            if canonical in row:
                raise ValueError("Ambiguous mapping column aliases")
            if value is None or (isinstance(value, float) and math.isnan(value)):
                value = ""
            row[canonical] = value
        field = row.get("SOURCE_FIELD_NAME", "")
        path = str(row.get("OSCAL_ELEMENT_PATH", "")).strip()
        model = _score_words(row.get("OSCAL_MODEL")).replace(" ", "")
        in_ar = model == "assessmentresults" or path.startswith(_SCORE_ROOT_PATH + ".")
        if not in_ar:
            continue
        if field in found:
            found[field].append(row)
        else:
            other_rows += 1
    errors = []
    for field, rows in found.items():
        if len(rows) != 1:
            errors.append({"field": field, "issue": "expected_one_mapping_row", "rows": len(rows)})
            continue
        row = rows[0]
        expected_path = _SCORE_OBSERVATION_PATH
        expected_notes = _SCORE_NOTES
        checks = {
            "model": _score_words(row.get("OSCAL_MODEL")).replace(" ", "") == "assessmentresults",
            "target": str(row.get("OSCAL_ELEMENT_PATH", "")).strip() == expected_path,
            "mapping_type": _score_words(row.get("MAPPING_TYPE")) == "extension property",
            "notes": _score_words(row.get("NOTES")) == expected_notes,
            "target_member": not str(row.get("OSCAL_FIELD_NAME", "")).strip(),
            "extra_transform": not str(row.get("TRANSFORMATION_LOGIC", "")).strip(),
            "extra_notes": not str(row.get("MAPPING_NOTES", "")).strip(),
            "status": _score_words(row.get("STATUS")) not in {
                "tbd", "deferred", "blocked", "more information needed", "not mapped",
            },
        }
        errors.extend({"field": field, "issue": "contract_" + key}
                      for key, valid in checks.items() if not valid)
    return errors, other_rows



def _score_registry_contract(registry_rows):
    expected = {
        _SCORE_ROOT_PATH: (None, False, None),
        _SCORE_RESULT_PATH: (_SCORE_ROOT_PATH, True, "SOURCE_RECORD_ID"),
        _SCORE_OBSERVATION_PATH: (_SCORE_RESULT_PATH, True, "SOURCE_FIELD_NAME"),
    }
    found = {path: [] for path in expected}
    for original in registry_rows:
        row = _score_row_dict(original)
        if str(row.get("OSCAL_MODEL_KEY", "")).strip().upper() != "ASSESSMENT_RESULTS":
            continue
        path = str(row.get("NODE_PATH", "")).strip()
        if path in found:
            found[path].append(row)
    errors, selected = [], {}
    for path, matches in found.items():
        if len(matches) != 1:
            errors.append({"path": path, "issue": "expected_one_registry_row", "rows": len(matches)})
            continue
        row = matches[0]
        parent, collection, rule = expected[path]
        active = str(row.get("IS_ACTIVE", "")).strip().upper()
        flag = str(row.get("IS_COLLECTION", "")).strip().upper()
        actual_parent = row.get("PARENT_NODE_PATH")
        actual_parent = str(actual_parent).strip() if actual_parent else None
        checks = {
            "active": active in {"TRUE", "T", "YES", "Y", "1"},
            "parent": actual_parent == parent,
            "collection": flag in ({"TRUE", "T", "YES", "Y", "1"} if collection
                                   else {"FALSE", "F", "NO", "N", "0"}),
            "element_type": isinstance(row.get("ELEMENT_TYPE"), str) and bool(row["ELEMENT_TYPE"].strip()),
        }
        if rule:
            checks["instance_rule"] = str(row.get("INSTANCE_KEY_RULE", "")).strip() == rule
            checks["element_type"] = row.get("ELEMENT_TYPE") == path.rsplit(".", 1)[-1].replace("[]", "")
            # The saved AR collection contract uses no nested extraction path.
            checks["item_path"] = row.get("ITEM_PATH") in (None, "")
        errors.extend({"path": path, "issue": "registry_" + key}
                      for key, valid in checks.items() if not valid)
        selected[path] = row
    return errors, selected



def _score_value(value, context=None):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Score must be finite")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError("Score must be finite")
    if not _has_value(value):
        return None
    # Bare scores must never go through the lookup's scalar-ID fallback.
    if _contains_archer_select_id_container(value):
        value = resolve_archer_select_value(value, context)
    values = value if isinstance(value, list) else [value]
    if len(values) != 1:
        raise ValueError("One scalar score is required per observation")
    item = values[0]
    if not isinstance(item, (str, int, float, bool, Decimal)):
        raise ValueError("Score must resolve to a scalar")
    if isinstance(item, float) and not math.isfinite(item):
        raise ValueError("Score must be finite")
    if isinstance(item, Decimal) and not item.is_finite():
        raise ValueError("Score must be finite")
    normalized = _oscal_property_values(value)
    if len(normalized) != 1 or normalized[0].lower() in {"infinity", "+infinity", "-infinity"}:
        raise ValueError("One finite scalar score is required")
    return normalized[0]



def _score_registry_policy(rows, context):
    errors, selected = _score_registry_contract([row["raw"] for row in rows])
    if errors:
        raise ValueError("Assessment Results registry contract failed: " + json.dumps(errors, sort_keys=True))
    return rows


def _score_prepare(source_df, context):
    del source_df
    fields = tuple(context["model_contract"].get("SELECTED_FIELDS", ()))
    if fields != _SCORE_ACCEPTED_FIELDS:
        raise ValueError("Assessment Results policy requires the accepted seventeen-field contract")
    errors, other_rows = _score_mapping_contract(context["mapping_rows"])
    report = context["graph_report"]
    report.update(
        MODEL="ASSESSMENT_RESULTS", TARGET_PATH=_SCORE_OBSERVATION_PATH,
        MAPPING_RELEASE="ar-observation-scores-v2-17-fields",
        REPRESENTATION="one-named-property-per-observation",
        SELECTED_FIELDS=list(fields),
        OTHER_AR_MAPPING_ROWS_NOT_PROCESSED=other_rows,
        MAPPING_CONTRACT_ERRORS=errors, REGISTRY_CONTRACT_ERRORS=[],
        FIELDS={field: {"emitted": 0, "missing": 0, "invalid": 0} for field in fields},
        WRITES_EXECUTED=False, FULL_MODEL_COMPLETE=False, SCHEMA_VALIDATED=False,
    )
    if errors:
        raise ValueError("Assessment Results mapping contract failed: " + json.dumps(errors, sort_keys=True))


def _score_parse(record, context):
    del context
    raw = _to_python(record["CURATED_JSON"])
    value = json.loads(raw, parse_float=Decimal) if isinstance(raw, str) else raw
    if not isinstance(value, dict):
        raise ValueError("Source JSON must be an object")
    return value


def _score_instances(source_obj, source_record_id, registry_row, context):
    path = registry_row["element_path"]
    if path == _SCORE_ROOT_PATH:
        return [{"instance_key": "singleton", "payload": {}, "parent_instance_key": None}]
    if path == _SCORE_RESULT_PATH:
        return [{"instance_key": source_record_id, "payload": {}, "parent_instance_key": "singleton"}]
    if path != _SCORE_OBSERVATION_PATH:
        raise ValueError("Unapproved Assessment Results registry path")
    instances = []
    for field in context["model_contract"]["SELECTED_FIELDS"]:
        counts = context["graph_report"]["FIELDS"][field]
        try:
            value = _score_value(resolve_json_path(source_obj, field), context)
        except (TypeError, ValueError, ArithmeticError):
            counts["invalid"] += 1
            continue
        if value is None:
            counts["missing"] += 1
            continue
        instances.append({
            "instance_key": field, "parent_instance_key": source_record_id,
            "payload": {"props": [{"name": _stable_property_name(field), "value": value}]},
        })
        counts["emitted"] += 1
    return instances


def _score_uuid(path, instance, source_system, source_table, source_id, model_key, context):
    return _deterministic_uuid(
        context["config"]["IDENTITY_VERSION"], source_system, source_table,
        source_id, model_key, path, instance["instance_key"],
    )


def _score_payload(path, payload, node_uuid, context):
    del path, context
    if not isinstance(payload, dict):
        raise ValueError("Assessment Results payload must be an object")
    return {"uuid": node_uuid, **payload}


def _score_record_complete(nodes_by_path, context):
    del nodes_by_path, context


def _score_finish(nodes, edges, context):
    report = context["graph_report"]
    invalid = report["INVALID_SOURCE_RECORDS"] + report["DUPLICATE_SOURCE_RECORDS"]
    invalid += sum(row["invalid"] for row in report["FIELDS"].values())
    report.update(CANDIDATE_NODES=len(nodes), CANDIDATE_EDGES=len(edges),
                  COUNTS_ARE_CANDIDATES=True)
    if invalid or not report["SOURCE_RECORDS"]:
        report.update(STATUS="BLOCKED", OUTPUTS_PUBLISHED=False)
        # No values or source identifiers appear in the aggregate report.
        raise ValueError("Assessment Results values rejected: " + json.dumps(report, sort_keys=True))
    report.update(
        STATUS="MAPPED_SCOPE_BUILT", OUTPUTS_PUBLISHED=True,
        NODES=len(nodes), EDGES=len(edges), DOCUMENTS=report["SOURCE_RECORDS"],
        COUNTS_ARE_CANDIDATES=False,
        FIELDS_WITH_POPULATED_EVIDENCE=sum(row["emitted"] > 0 for row in report["FIELDS"].values()),
    )


def _ssp_prepare(source_df, context):
    hydration_sources = context["lookups"].get("component_sources")
    if hydration_sources is None:
        raise RuntimeError("Run the updated Cell 2 before building the SSP graph")
    context["component_hydration_lookups"] = _build_component_hydration_lookups(
        source_df, context["mappings_by_path"].get(COMPONENTS_ELEMENT_PATH, []),
        hydration_sources,
        *(() if context.get("_legacy_context") else (context,)),
    )


def _ssp_parse(record, context):
    del context
    return _parse_source_json(record)


def _ssp_instances(source_obj, source_record_id, registry_row, context):
    path = registry_row["element_path"]
    instances = build_element_instances(
        source_obj, source_record_id, path, context["mappings_by_path"].get(path, []),
        context.get("component_hydration_lookups"),
        *(() if context.get("_legacy_context") else (context,)),
    )
    if not instances and _should_materialize_structural_singleton(path, context["model_contract"]["ROOT_PATH"]):
        instances = [{"instance_key": "singleton", "payload": {}, "parent_instance_key": None}]
    return _inject_controlled_metadata_fields(path, instances, context)


def _ssp_uuid(path, instance, source_system, source_table, source_id, model_key, context):
    return _instance_oscal_uuid(path, instance, source_system, source_table, source_id, model_key, context)


def _ssp_payload(path, payload, node_uuid, context):
    del context
    return _payload_with_instance_uuid(path, payload, node_uuid)


def _ssp_record_complete(nodes_by_path, context):
    del context
    _validate_metadata_reference_closure(nodes_by_path)


def _ssp_finish(nodes, edges, context):
    context["graph_report"].update(
        STATUS="MAPPED_SCOPE_BUILT", OUTPUTS_PUBLISHED=True,
        NODES=len(nodes), EDGES=len(edges), WRITES_EXECUTED=False,
    )


MODEL_GRAPH_POLICIES = {
    "ssp-approved-v1": {
        "model": "SSP", "root": "system-security-plan",
        "registry": _ssp_registry_policy, "prepare": _ssp_prepare,
        "parse": _ssp_parse, "instances": _ssp_instances,
        "uuid": _ssp_uuid, "payload": _ssp_payload,
        "record_complete": _ssp_record_complete, "finish": _ssp_finish,
        "aggregate_invalid": False, "allow_nan": True,
    },
    "observation-scores-v2": {
        "model": "ASSESSMENT_RESULTS", "root": _SCORE_ROOT_PATH,
        "registry": _score_registry_policy, "prepare": _score_prepare,
        "parse": _score_parse, "instances": _score_instances,
        "uuid": _score_uuid, "payload": _score_payload,
        "record_complete": _score_record_complete, "finish": _score_finish,
        "aggregate_invalid": True, "allow_nan": False,
    },
}


def _prepare_model_context(context, model_key, source_system, source_table):
    legacy_context = context is None
    if context is None:
        config = dict(globals().get("CONFIG", {}))
        config.update(OSCAL_MODEL=model_key, SOURCE_SYSTEM_NAME=source_system,
                      SOURCE_TABLE_NAME=source_table)
        model_contract = globals().get("MODEL_CONTRACTS", {}).get(model_key)
        if model_contract is None:
            matches = [(key, value) for key, value in MODEL_GRAPH_POLICIES.items() if value["model"] == model_key]
            if len(matches) != 1:
                raise ValueError("An explicit model contract is required")
            policy_name, policy = matches[0]
            model_contract = {"MODEL_KEY": model_key, "ROOT_PATH": policy["root"], "POLICY": policy_name}
        mappings = globals().get("MAPPINGS_BY_ELEMENT_PATH", {})
        context = {
            "config": config, "model_contract": model_contract,
            "mapping_rows": globals().get("CANONICAL_MAPPING_ROWS", [row for rows in mappings.values() for row in rows]),
            "mappings_by_path": mappings,
            "lookups": {
                "archer_values": globals().get("ARCHER_VALUE_LOOKUP", {}),
                "fips_values": globals().get("FIPS_199_VALUE_LOOKUP", {}),
                "component_sources": globals().get("COMPONENT_HYDRATION_SOURCE_DFS"),
                "component_contract": globals().get("COMPONENT_HYDRATION_SOURCE_CONTRACT"),
            },
        }
    config, contract = context["config"], context["model_contract"]
    if any(config.get(name) != value for name, value in (
        ("OSCAL_MODEL", model_key), ("SOURCE_SYSTEM_NAME", source_system), ("SOURCE_TABLE_NAME", source_table),
    )):
        raise ValueError("Graph arguments conflict with explicit source/model context")
    policy = MODEL_GRAPH_POLICIES.get(contract.get("POLICY"))
    if policy is None or contract.get("MODEL_KEY") != model_key or policy["model"] != model_key or contract.get("ROOT_PATH") != policy["root"]:
        raise ValueError("Unsupported model policy or root contract")
    if not isinstance(config.get("IDENTITY_VERSION"), str) or not config["IDENTITY_VERSION"].strip():
        raise ValueError("A nonblank identity version is required")
    context["_legacy_context"] = legacy_context
    context["policy"] = policy
    context["graph_report"] = {
        "SOURCE_RECORDS": 0, "INVALID_SOURCE_RECORDS": 0, "DUPLICATE_SOURCE_RECORDS": 0,
        "STATUS": "NOT_RUN", "OUTPUTS_PUBLISHED": False,
    }
    return context


# %% Cell 5 - Registry-driven canonical node and edge graph

def build_oscal_graph(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    model_key,
    source_system,
    source_table,
    context=None,
):
    # Payload, mapping, and instance rules belong to Cell 4's explicit policy.
    # This loop owns only graph mechanics and never swaps notebook globals.
    del canonical_mapping_df
    context = _prepare_model_context(context, model_key, source_system, source_table)
    config, policy = context["config"], context["policy"]
    report = context["graph_report"]
    registry_rows = _canonical_registry_rows(element_registry_df, model_key, context)
    root_paths = [row["element_path"] for row in registry_rows if not row["parent_path"]]
    if root_paths != [context["model_contract"]["ROOT_PATH"]]:
        raise ValueError("Expected exactly the configured registry root")
    root_row = next(row for row in registry_rows if row["element_path"] == root_paths[0])
    context["root_element_type"] = root_row.get("element_type") or _element_type(root_paths[0])
    policy["prepare"](source_df, context)

    node_rows, edge_rows, seen_records = [], [], set()
    load_timestamp = datetime.datetime.now(datetime.timezone.utc)
    for record in source_df.to_local_iterator():
        report["SOURCE_RECORDS"] += 1
        source_record_id = record["SOURCE_RECORD_ID"]
        if not isinstance(source_record_id, str) or not source_record_id.strip() or source_record_id != source_record_id.strip():
            report["INVALID_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise ValueError("Source record identity must be a nonblank canonical string")
        if source_record_id in seen_records:
            report["DUPLICATE_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise ValueError("Duplicate source record identity")
        seen_records.add(source_record_id)
        try:
            source_obj = policy["parse"](record, context)
        except (TypeError, ValueError, ArithmeticError):
            report["INVALID_SOURCE_RECORDS"] += 1
            if policy["aggregate_invalid"]:
                continue
            raise
        nodes_by_path = {}
        for registry_row in registry_rows:
            path, parent_path = registry_row["element_path"], registry_row["parent_path"]
            instances = policy["instances"](source_obj, source_record_id, registry_row, context)
            created_nodes = []
            seen_instances = set()
            for instance in instances:
                instance_key = instance["instance_key"]
                if not isinstance(instance_key, str) or not instance_key.strip():
                    raise ValueError("Element instance requires a stable nonblank identity")
                if instance_key in seen_instances:
                    raise ValueError("Duplicate element instance identity")
                seen_instances.add(instance_key)
                node_key = _deterministic_hash(
                    config["IDENTITY_VERSION"], source_system, source_table,
                    source_record_id, model_key, path, instance_key,
                )
                oscal_uuid = policy["uuid"](
                    path, instance, source_system, source_table, source_record_id, model_key, context,
                )
                payload = policy["payload"](path, instance["payload"], oscal_uuid, context)
                if not isinstance(payload, dict):
                    raise ValueError("An element payload must be an object")
                node = {
                    "NODE_KEY": node_key, "ELEMENT_PATH": path, "INSTANCE_KEY": instance_key,
                    "PARENT_INSTANCE_KEY": instance.get("parent_instance_key"),
                    "OSCAL_UUID": oscal_uuid,
                    "ELEMENT_TYPE": registry_row.get("element_type") or _element_type(path),
                    "METADATA_JSON": json.dumps(payload, sort_keys=True, default=str, allow_nan=policy["allow_nan"]),
                    "SOURCE_SYSTEM_NAME": source_system, "SOURCE_TABLE_NAME": source_table,
                    "SOURCE_RECORD_ID": source_record_id, "DW_PIPELINE_RUN_ID": config["RUN_ID"],
                    "DW_LOAD_TIMESTAMP": load_timestamp, "DW_LOAD_TIMESTAMP_TZ": load_timestamp,
                }
                node_rows.append(node)
                created_nodes.append(node)
            nodes_by_path[path] = created_nodes
            if not parent_path:
                continue
            parent_nodes = nodes_by_path.get(parent_path, [])
            for child_node in created_nodes:
                if not parent_nodes:
                    raise ValueError(f"Missing parent {parent_path} for child {path}")
                parent_key = child_node["PARENT_INSTANCE_KEY"]
                if parent_key is not None:
                    matches = [node for node in parent_nodes if node["INSTANCE_KEY"] == parent_key]
                    if len(matches) != 1:
                        raise ValueError("Unresolved explicit collection parent instance")
                    parent_node = matches[0]
                elif len(parent_nodes) == 1:
                    parent_node = parent_nodes[0]
                else:
                    raise ValueError(f"Ambiguous collection parent for {path}")
                edge_key = _deterministic_hash(
                    "edge-v1", parent_node["NODE_KEY"], child_node["NODE_KEY"], "CONTAINS",
                )
                edge_rows.append({
                    "EDGE_KEY": edge_key,
                    "FK_SOURCE_ELEMENT_HASH": parent_node["NODE_KEY"],
                    "FK_TARGET_ELEMENT_HASH": child_node["NODE_KEY"],
                    "DEPENDENCY_TYPE": "CONTAINS",
                    "SOURCE_OSCAL_UUID": parent_node["OSCAL_UUID"],
                    "TARGET_OSCAL_UUID": child_node["OSCAL_UUID"],
                })
        policy["record_complete"](nodes_by_path, context)

    node_keys = {row["NODE_KEY"] for row in node_rows}
    report["DUPLICATE_NODE_KEYS"] = len(node_rows) - len(node_keys)
    report["DUPLICATE_EDGE_KEYS"] = len(edge_rows) - len({row["EDGE_KEY"] for row in edge_rows})
    report["DANGLING_EDGES"] = sum(
        row["FK_SOURCE_ELEMENT_HASH"] not in node_keys or row["FK_TARGET_ELEMENT_HASH"] not in node_keys
        for row in edge_rows
    )
    if any(report[key] for key in ("DUPLICATE_NODE_KEYS", "DUPLICATE_EDGE_KEYS", "DANGLING_EDGES")):
        raise ValueError("Canonical graph key integrity failed")
    policy["finish"](node_rows, edge_rows, context)
    if not node_rows:
        raise ValueError("Graph builder produced no nodes")
    canonical_nodes_df = session.create_dataframe(node_rows)
    canonical_edges_df = session.create_dataframe(edge_rows)
    return canonical_nodes_df, canonical_edges_df


print("Cell 5 graph builder initialized")


# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification
# Shared reviewed-contract upsert. Missing/obsolete in-scope rows block; no destructive policy.
# Keep other target writers paused for the complete preflight/transaction/readback.
import json
import re
import uuid
from types import MappingProxyType

OSCAL_LOAD_RELEASE = "oscal-shared-daily-upsert-v2"
SSP_LOAD_RELEASE = OSCAL_LOAD_RELEASE
SSP_LOAD_DIM = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT"
SSP_LOAD_FACT = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY"
SSP_LOAD_DIM_PK = "PK_OSCAL_SSP_ELEMENT_HASH"
SSP_LOAD_FACT_PK = "PK_FACT_OSCAL_DEPENDENCY_HASH"
SSP_LOAD_SOURCE = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
_LOAD_AUDIT_COLUMNS = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}


class LoadError(RuntimeError):
    def __init__(self, code, details=None):
        self.code = code
        self.details = details or {}
        super().__init__(code)

_LOAD_DIM_SOURCES = {
    SSP_LOAD_DIM_PK: "NODE_KEY", "ELEMENT_TYPE": "ELEMENT_TYPE",
    "OSCAL_UUID": "OSCAL_UUID", "METADATA_JSON": "METADATA_JSON",
    "SOURCE_SYSTEM_NAME": "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME": "SOURCE_TABLE_NAME",
    "SOURCE_RECORD_ID": "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID": "DW_PIPELINE_RUN_ID",
    "DW_LOAD_TIMESTAMP": "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ": "DW_LOAD_TIMESTAMP_TZ",
}
_LOAD_FACT_SOURCES = {
    SSP_LOAD_FACT_PK: "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH": "FK_SOURCE_ELEMENT_HASH",
    "FK_TARGET_ELEMENT_HASH": "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE": "DEPENDENCY_TYPE",
    "SOURCE_OSCAL_UUID": "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID": "TARGET_OSCAL_UUID",
}
_LOAD_HASH_SOURCES = {"NODE_KEY", "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"}
_LOAD_UUID_SOURCES = {"OSCAL_UUID", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID"}
_LOAD_HEX_PATTERN = r"[0-9a-fA-F]{32}"
_LOAD_UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _load_query(session, statement):
    return session.sql(statement).collect()


def _load_error_details(error):
    # Preserve actionable categories without echoing Snowflake/source messages.
    details = {"CAUSE": error.code if isinstance(error, LoadError) else
               ("CANCELLED" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "SQL_OR_CLIENT_ERROR")}
    if isinstance(error, LoadError):
        details.update(error.details)
    for attr, label, pattern in (("sql_error_code", "SQL_ERROR_CODE", r"[0-9]{1,10}"),
                                 ("sqlstate", "SQLSTATE", r"[A-Z0-9]{5}"),
                                 ("sfqid", "QUERY_ID", r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")):
        value = str(getattr(error, attr, ""))
        if re.fullmatch(pattern, value):
            details[label] = value
    return details


def _load_no_transaction(session):
    try:
        transaction = _load_query(session, "SELECT CURRENT_TRANSACTION() AS TX")[0]["TX"]
    except BaseException:
        raise LoadError("TRANSACTION_STATE_UNAVAILABLE") from None
    if transaction is not None:
        raise LoadError("EXISTING_TRANSACTION")


def _load_ident(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
        raise LoadError("UNSUPPORTED_COLUMN_IDENTIFIER")
    return '"' + value + '"'


def _load_table(name):
    parts = name.split(".") if isinstance(name, str) else []
    if len(parts) not in (1, 3):
        raise LoadError("UNSUPPORTED_TABLE_IDENTIFIER")
    return ".".join(_load_ident(part.upper()) for part in parts)


def _load_safe_type(value):
    if not isinstance(value, str):
        raise LoadError("MISSING_LIVE_COLUMN_DATATYPE")
    value = value.strip().upper()
    match = re.fullmatch(r"(?:VARCHAR|STRING|TEXT)(?:\(\s*([1-9][0-9]*)\s*\))?", value)
    if match:
        return "VARCHAR" + ("(" + str(int(match[1])) + ")" if match[1] else "")
    if re.fullmatch(r"BINARY\(\s*16\s*\)", value):
        return "BINARY(16)"
    if value == "VARIANT" or re.fullmatch(r"TIMESTAMP_(?:NTZ|LTZ|TZ)(?:\([0-9]\))?", value):
        return value
    raise LoadError("UNSUPPORTED_LIVE_COLUMN_DATATYPE")


def _load_column_plan(description, kind, contract=None):
    c = _load_runtime_contract(contract)
    mappings = _load_sources(c)
    if kind not in mappings:
        raise LoadError("INVALID_PROJECTION_KIND")
    sources = mappings[kind]
    seen, plan = set(), []
    for row in description:
        raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
        entry = {str(k).lower(): v for k, v in raw.items()}
        if not {"name", "type", "kind", "null?", "default"}.issubset(entry):
            raise LoadError("INCOMPLETE_DESC_TABLE_METADATA")
        name = entry["name"]
        _load_ident(name)  # Quoted lower-case/case-colliding targets are not guessed.
        if name in seen:
            raise LoadError("DUPLICATE_LIVE_COLUMN_NAMES")
        seen.add(name)
        nullable = str(entry["null?"]).strip().upper()
        column_kind = str(entry["kind"]).strip().upper()
        if nullable not in {"Y", "N"} or column_kind not in {"COLUMN", "VIRTUAL", "VIRTUAL_COLUMN"}:
            raise LoadError("UNSUPPORTED_LIVE_COLUMN_METADATA")
        if name not in sources:
            if column_kind == "COLUMN" and nullable == "N" and entry["default"] is None:
                raise LoadError("UNMAPPED_REQUIRED_INSERT_COLUMN_" + name)
            continue
        if column_kind != "COLUMN" or entry.get("expression") not in (None, ""):
            raise LoadError("MAPPED_COLUMN_NOT_WRITABLE_" + name)
        try:
            dtype = _load_safe_type(entry["type"])
        except LoadError as error:
            # Only column metadata, never source values or full SQL, is reported.
            raise LoadError(error.code, {"TABLE_KIND": kind, "COLUMN": name,
                             "LIVE_TYPE": str(entry["type"])[:128]}) from None
        source, encoding = sources[name], None
        expression = "s." + _load_ident(source)
        if source in _LOAD_HASH_SOURCES and dtype == "BINARY(16)":
            # Decode the existing MD5 hex identity; never hash again or truncate.
            expression = "TO_BINARY(" + expression + ", 'HEX')"
            encoding = "HEX_TO_BINARY16"
        elif source in _LOAD_UUID_SOURCES and dtype == "VARCHAR(32)":
            # Storage only. Canonical UUIDs inside the graph and JSON stay unchanged.
            expression = "REPLACE(" + expression + ", '-', '')"
            encoding = "UUID_TO_COMPACT32"
        elif name == "METADATA_JSON":
            if dtype == "VARIANT":
                expression = "PARSE_JSON(" + expression + ")"
            elif dtype.startswith("VARCHAR"):
                expression = "CAST(" + expression + " AS VARCHAR)"
            else:
                raise LoadError("UNSUPPORTED_PAYLOAD_DATATYPE")
        elif name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}:
            if not dtype.startswith("TIMESTAMP_"):
                raise LoadError("EXPLICIT_AUDIT_TIMESTAMP_TYPE_REQUIRED")
            expression = "CAST(" + expression + " AS " + dtype + ")"
        else:
            if not dtype.startswith("VARCHAR"):
                raise LoadError("IDENTIFIERS_AND_LABELS_REQUIRE_STRING_TYPE")
            expression = "CAST(" + expression + " AS VARCHAR)"
        plan.append({"name": name, "source": source, "expression": expression,
                     "type": dtype, "nullable": nullable == "Y", "encoding": encoding})
    required = set(sources)
    if kind == "DIM":
        # The existing loader projects these audit columns only when exposed.
        # Do not invent a requirement that an optional target column must exist.
        required -= {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}
    if required - seen:
        raise LoadError("MISSING_TARGET_COLUMNS_" + "_".join(sorted(required - seen)))
    return plan


def _load_count(session, sql):
    return int(_load_query(session, sql)[0]["N"])


def _load_zero(session, sql, code):
    if _load_count(session, sql):
        raise LoadError(code)


def _load_unique(session, table, key):
    _load_zero(session, f"SELECT COUNT(*) AS N FROM (SELECT {key} FROM {table} "
                f"GROUP BY {key} HAVING {key} IS NULL OR COUNT(*) > 1)",
                "NULL_OR_DUPLICATE_KEYS")


def _load_selection_schema(plans, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    """Selection compares identities using the posted physical BINARY(16) schema."""
    required = ((dk,),
                (fk, "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"))
    for plan, keys in zip(plans, required):
        types = {c["name"]: c["type"] for c in plan}
        if any(types.get(key) != "BINARY(16)" for key in keys):
            raise LoadError("CONFIRMED_BINARY16_SCHEMA_REQUIRED")


    for plan, columns in zip(plans, (("OSCAL_UUID",), ("SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID"))):
        types = {column["name"]: column["type"] for column in plan}
        if any(types.get(name) != "VARCHAR(32)" for name in columns):
            raise LoadError("VERIFIED_UUID32_PROFILE_REQUIRED")


def _load_stage(session, raw_stage, stage, plan):
    # Validate identity syntax before evaluating conversions; NULL is not an identity.
    for column in plan:
        encoding = column.get("encoding")
        if encoding:
            source = _load_ident(column["source"])
            pattern = _LOAD_HEX_PATTERN if encoding == "HEX_TO_BINARY16" else _LOAD_UUID_PATTERN
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {raw_stage} WHERE "
                        f"{source} IS NULL OR NOT REGEXP_LIKE({source}, '{pattern}')",
                        "INVALID_STORAGE_IDENTITY_" + column["name"])
    expressions = ", ".join(c["expression"] + " AS " + _load_ident(c["name"]) for c in plan)
    _load_query(session, f"CREATE TEMPORARY TABLE {stage} AS SELECT {expressions} FROM {raw_stage} s")
    for column in plan:
        name = _load_ident(column["name"])
        if column["type"] == "BINARY(16)":
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE "
                        f"{name} IS NULL OR OCTET_LENGTH({name}) <> 16", "BINARY_KEY_WIDTH_INVALID")
        if column["source"] in {"NODE_KEY", "EDGE_KEY"}:
            # Different text casing can collapse to the same physical binary key.
            _load_unique(session, stage, name)
        if not column["nullable"]:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE {name} IS NULL",
                        "REQUIRED_TARGET_VALUE_IS_NULL")
        width = re.fullmatch(r"VARCHAR\((\d+)\)", column["type"])
        if width:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE LENGTH({name}) > {int(width[1])}",
                        "TARGET_STRING_CAPACITY_EXCEEDED")


def _load_baseline_equal(session, names, queries):
    # Multiset comparison: keep duplicate multiplicities in the OLD full tables.
    # GROUP BY ALL includes every existing target column, including VARIANT payloads.
    for baseline, query in zip((names["DB"], names["FB"]), queries):
        current = f"SELECT *, COUNT(*) AS OSCAL_LOAD_ROW_MULTIPLICITY FROM ({query}) GROUP BY ALL"
        frozen = f"SELECT *, COUNT(*) AS OSCAL_LOAD_ROW_MULTIPLICITY FROM {baseline} GROUP BY ALL"
        _load_zero(session, f"SELECT COUNT(*) AS N FROM (({current}) MINUS ({frozen}))",
                    "TARGET_BASELINE_CHANGED")
        _load_zero(session, f"SELECT COUNT(*) AS N FROM (({frozen}) MINUS ({current}))",
                    "TARGET_BASELINE_CHANGED")
        if _load_count(session, f"SELECT COUNT(*) AS N FROM ({query})") != _load_count(
                session, f"SELECT COUNT(*) AS N FROM {baseline}"):
            raise LoadError("TARGET_BASELINE_CHANGED")


def _load_integrity_sql(queries, ids, allow_absent=False, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    if type(allow_absent) is not bool:
        raise LoadError("INVALID_OLD_GRAPH_POLICY")
    dim, fact = queries
    relationship = "('parent_of','CONTAINS')" if allow_absent else "('CONTAINS')"
    empty = "c.NODES=0 AND COALESCE(e.EDGES,0)=0" if allow_absent else "FALSE"
    return f"""WITH checked_nodes AS ({dim}), checked_edges AS ({fact}),
record_counts AS (
 SELECT i.SOURCE_RECORD_ID, COUNT(d.{dk}) AS NODES,
        SUM(CASE WHEN d.ELEMENT_TYPE={root_type} THEN 1 ELSE 0 END) AS ROOTS
 FROM {ids} i LEFT JOIN checked_nodes d ON d.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
 GROUP BY i.SOURCE_RECORD_ID),
edge_counts AS (
 SELECT d.SOURCE_RECORD_ID, COUNT(f.{fk}) AS EDGES
 FROM checked_edges f JOIN checked_nodes d ON d.{dk}=f.FK_SOURCE_ELEMENT_HASH
 GROUP BY d.SOURCE_RECORD_ID)
SELECT
 (SELECT COUNT(*) FROM {ids}) AS SELECTED_RECORDS,
 (SELECT COUNT(*) FROM checked_nodes) AS NODES,
 (SELECT COUNT(*) FROM checked_edges) AS EDGES,
 (SELECT COUNT(*) FROM checked_nodes WHERE {dk} IS NULL) AS DIM_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {dk} FROM checked_nodes GROUP BY {dk} HAVING COUNT(*)>1)) AS DIM_DUPLICATE_KEYS,
 (SELECT COUNT(*) FROM checked_edges WHERE {fk} IS NULL) AS FACT_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {fk} FROM checked_edges GROUP BY {fk} HAVING COUNT(*)>1)) AS FACT_DUPLICATE_KEYS,
 (SELECT COUNT(*) FROM checked_nodes d LEFT JOIN {ids} i ON i.SOURCE_RECORD_ID=d.SOURCE_RECORD_ID
     WHERE d.OSCAL_UUID IS NULL OR
     NOT EQUAL_NULL(d.SOURCE_SYSTEM_NAME,{source_system}) OR
     NOT EQUAL_NULL(d.SOURCE_TABLE_NAME,{source_table}) OR
     i.SOURCE_RECORD_ID IS NULL) AS INVALID_NODE_OWNERSHIP_OR_UUID,
 (SELECT COUNT(*) FROM checked_edges WHERE FK_SOURCE_ELEMENT_HASH IS NULL OR FK_TARGET_ELEMENT_HASH IS NULL) AS NULL_FOREIGN_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS
     (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_SOURCE_ELEMENT_HASH)) AS DANGLING_SOURCE_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS
     (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_TARGET_ELEMENT_HASH)) AS DANGLING_TARGET_KEYS,
 (SELECT COUNT(*) FROM checked_edges f JOIN checked_nodes s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
     JOIN checked_nodes t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
     WHERE NOT EQUAL_NULL(s.SOURCE_RECORD_ID,t.SOURCE_RECORD_ID)) AS CROSS_RECORD_EDGES,
 (SELECT COUNT(*) FROM checked_edges f JOIN checked_nodes s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
     JOIN checked_nodes t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
     WHERE NOT EQUAL_NULL(f.SOURCE_OSCAL_UUID,s.OSCAL_UUID)
        OR NOT EQUAL_NULL(f.TARGET_OSCAL_UUID,t.OSCAL_UUID)) AS UUID_LINK_MISMATCHES,
 (SELECT COUNT(*) FROM checked_edges WHERE DEPENDENCY_TYPE IS NULL
     OR DEPENDENCY_TYPE NOT IN {relationship}) AS WRONG_RELATIONSHIP_TYPE,
 (SELECT COUNT(*) FROM (SELECT d.{dk},d.ELEMENT_TYPE,COUNT(f.{fk}) AS PARENTS
     FROM checked_nodes d LEFT JOIN checked_edges f ON f.FK_TARGET_ELEMENT_HASH=d.{dk}
     GROUP BY d.{dk},d.ELEMENT_TYPE
     HAVING COUNT(f.{fk}) <> CASE WHEN d.ELEMENT_TYPE={root_type} THEN 0 ELSE 1 END)) AS WRONG_PARENT_COUNTS,
 (SELECT COUNT(*) FROM record_counts c LEFT JOIN edge_counts e ON e.SOURCE_RECORD_ID=c.SOURCE_RECORD_ID
     WHERE NOT ({empty}) AND
     (c.NODES<1 OR c.ROOTS<>1 OR COALESCE(e.EDGES,0)<>c.NODES-1)) AS INVALID_RECORD_SHAPES"""


def _load_integrity(session, queries, ids, expected_records, allow_absent=False, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    row = _load_query(session, _load_integrity_sql(queries, ids, allow_absent, c))[0]
    report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
    metrics = ("SELECTED_RECORDS", "NODES", "EDGES")
    if report.get("SELECTED_RECORDS") != expected_records or any(v != 0 for k, v in report.items() if k not in metrics):
        raise LoadError("BATCH_PRIMARY_FOREIGN_KEY_OR_HIERARCHY_FAILED", {"KEY_CHECKS": report})
    # Cardinality is checked first; disconnected cycles must still fail reachability.
    dim, fact = queries
    bound = max(int(report["NODES"]), 1)
    sql = f"""WITH RECURSIVE checked_nodes AS ({dim}), checked_edges AS ({fact}),
tree(K,SOURCE_RECORD_ID,DEPTH) AS (
 SELECT {dk},SOURCE_RECORD_ID,0 FROM checked_nodes WHERE ELEMENT_TYPE={root_type}
 UNION ALL
 SELECT f.FK_TARGET_ELEMENT_HASH,t.SOURCE_RECORD_ID,t.DEPTH+1
 FROM tree t JOIN checked_edges f ON f.FK_SOURCE_ELEMENT_HASH=t.K
 JOIN checked_nodes d ON d.{dk}=f.FK_TARGET_ELEMENT_HASH AND d.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
 WHERE t.DEPTH<{bound}),
node_counts AS (SELECT SOURCE_RECORD_ID,COUNT(*) AS N FROM checked_nodes GROUP BY SOURCE_RECORD_ID),
reachable AS (SELECT SOURCE_RECORD_ID,COUNT(DISTINCT K) AS N FROM tree GROUP BY SOURCE_RECORD_ID)
SELECT COUNT(*) AS N FROM {ids} i
LEFT JOIN node_counts d ON d.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
LEFT JOIN reachable r ON r.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
WHERE COALESCE(d.N,0)<>COALESCE(r.N,0)"""
    _load_zero(session, sql, "BATCH_DISCONNECTED_RECORD_TREE")
    report["DISCONNECTED_RECORDS"] = 0
    return report


def _assert_safe_identifier(identifier):
    _load_table(identifier)


def _duplicate_count(dataframe, key_column):
    return dataframe.group_by(col(key_column)).count().filter(col("COUNT") > lit(1)).count()


def _load_columns(columns):
    names = [c["name"] if isinstance(c, dict) else c for c in columns]
    for name in names:
        _load_ident(name)
    if not names or len(names) != len(set(names)):
        raise LoadError("INVALID_PROJECTION_COLUMNS")
    return names


def _load_business_columns(columns):
    return [name for name in _load_columns(columns) if name not in _LOAD_AUDIT_COLUMNS]


def _load_difference_predicate(columns, left="t", right="s"):
    if left not in ("t", "s", "b") or right not in ("t", "s", "b"):
        raise LoadError("INVALID_COMPARISON_ALIAS")
    terms = []
    for name in _load_business_columns(columns):
        lhs, rhs = left + "." + _load_ident(name), right + "." + _load_ident(name)
        if name == "METADATA_JSON":
            # Structural object comparison, not JSON key ordering.
            lhs = "TRY_PARSE_JSON(TO_VARCHAR(" + lhs + "))"
            rhs = "TRY_PARSE_JSON(TO_VARCHAR(" + rhs + "))"
        terms.append("(" + lhs + " IS DISTINCT FROM " + rhs + ")")
    if not terms:
        raise LoadError("BUSINESS_COLUMNS_REQUIRED")
    return " OR ".join(terms)


def _build_merge_sql(target_table, source_view, pk_column, columns, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    expected_pk = {dim_table: dk, fact_table: fk}
    if expected_pk.get(target_table) != pk_column:
        raise LoadError("TARGET_OUTSIDE_APPROVED_STORAGE_CONTRACT")
    names = _load_columns(columns)
    if pk_column not in names:
        raise LoadError("MISSING_PROJECTED_PRIMARY_KEY")
    _load_table(source_view)
    changed = _load_difference_predicate(columns)
    updates = ", ".join("t." + _load_ident(n) + " = s." + _load_ident(n)
                        for n in names if n != pk_column)
    return (
        f"MERGE INTO {target_table} t USING {source_view} s "
        f"ON t.{_load_ident(pk_column)} = s.{_load_ident(pk_column)} "
        f"WHEN MATCHED AND ({changed}) THEN UPDATE SET {updates} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(_load_ident(n) for n in names)}) "
        f"VALUES ({', '.join('s.' + _load_ident(n) for n in names)})"
    )


def _load_expected_changes_sql(target, stage, pk, columns):
    target_sql, stage_sql, key = _load_table(target), _load_table(stage), _load_ident(pk)
    changed = _load_difference_predicate(columns)
    return f"""SELECT
 (SELECT COUNT(*) FROM {stage_sql} s WHERE NOT EXISTS
     (SELECT 1 FROM {target_sql} t WHERE t.{key}=s.{key})) AS INSERTS,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE {changed}) AS UPDATES,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE NOT ({changed})) AS UNCHANGED"""



def _load_row(row):
    raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
    return {str(k).upper(): v for k, v in raw.items()}


def _load_scope_queries(names, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    # Include ownership AND key matches: foreign-owned identities cannot hide.
    dim = f"""SELECT t.* FROM {dim_table} t
 LEFT JOIN {names['D']} s ON s.{dk}=t.{dk}
 LEFT JOIN {names['IDS']} i ON i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
     AND t.SOURCE_SYSTEM_NAME={source_system} AND t.SOURCE_TABLE_NAME={source_table}
 WHERE s.{dk} IS NOT NULL OR i.SOURCE_RECORD_ID IS NOT NULL"""
    keys = f"SELECT {dk} FROM ({dim}) UNION SELECT {dk} FROM {names['D']}"
    fact = f"""SELECT t.* FROM {fact_table} t
 LEFT JOIN {names['F']} f ON f.{fk}=t.{fk}
 LEFT JOIN ({keys}) s ON s.{dk}=t.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({keys}) d ON d.{dk}=t.FK_TARGET_ELEMENT_HASH
 WHERE f.{fk} IS NOT NULL OR s.{dk} IS NOT NULL
     OR d.{dk} IS NOT NULL"""
    return dim, fact


def _load_storage_values(session, query, plan):
    for column in plan:
        name, dtype = _load_ident(column["name"]), column["type"]
        where = []
        if not column["nullable"]:
            where.append(name + " IS NULL")
        if dtype == "BINARY(16)":
            where.append(name + " IS NULL OR OCTET_LENGTH(" + name + ")<>16")
        if column["source"] in _LOAD_UUID_SOURCES:
            pattern = r"[0-9a-f]{32}" if dtype == "VARCHAR(32)" else _LOAD_UUID_PATTERN
            where.append(name + " IS NULL OR NOT REGEXP_LIKE(" + name + ", '" + pattern + "')")
        width = re.fullmatch(r"VARCHAR\((\d+)\)", dtype)
        if width:
            where.append("LENGTH(" + name + ")>" + width[1])
        if column["name"] == "METADATA_JSON":
            where.append("NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(TO_VARCHAR(" + name + "))),FALSE)")
        if where:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) WHERE " + " OR ".join(where),
                       "INVALID_STORED_OR_STAGED_COLUMN_" + column["name"])


def _load_scope_check(session, names, plans, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    queries = _load_scope_queries(names, c)
    for target, pk in ((dim_table, dk), (fact_table, fk)):
        _load_unique(session, target, pk)
    extra = {}
    for kind, pk, query, plan in zip(("D", "F"), (dk, fk), queries, plans):
        extra[kind] = _load_count(session, f"SELECT COUNT(*) AS N FROM ({query}) t "
                                  f"WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})")
        ownership = ("SOURCE_RECORD_ID", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "ELEMENT_TYPE", "OSCAL_UUID") if kind == "D" else (
            "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID")
        conflict = " OR ".join(f"t.{_load_ident(c)} IS DISTINCT FROM s.{_load_ident(c)}" for c in ownership)
        _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) t JOIN {names[kind]} s "
                           f"ON t.{pk}=s.{pk} WHERE {conflict}", "TARGET_IDENTITY_PROVENANCE_CONFLICT")
        _load_storage_values(session, query, plan)
    report = {"OBSOLETE_DIM_ROWS": extra["D"], "OBSOLETE_FACT_ROWS": extra["F"]}
    if any(extra.values()):
        raise LoadError("OBSOLETE_TARGET_ROWS_BLOCKED", report)
    dim, fact = queries
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM ({fact}) f
 LEFT JOIN ({dim}) s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({dim}) t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
 WHERE s.{dk} IS NULL OR t.{dk} IS NULL""",
               "CROSS_SCOPE_LINKS_BLOCKED")
    report["ABSENT_INPUT_SOURCE_RECORDS_PRESERVED"] = _load_count(session, f"""
 SELECT COUNT(*) AS N FROM (SELECT DISTINCT t.SOURCE_RECORD_ID FROM {dim_table} t
 WHERE t.SOURCE_SYSTEM_NAME={source_system} AND t.SOURCE_TABLE_NAME={source_table}
 AND NOT EXISTS (SELECT 1 FROM {names['IDS']} i WHERE i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID))""")
    return report


def _load_freeze(session, nodes, edges, names, contract=None):
    c = _load_runtime_contract(contract)
    root = _load_literal(c["ROOT_PATH"])
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    required_nodes = set(_load_sources(c)["DIM"].values()) - _LOAD_AUDIT_COLUMNS
    required_nodes |= {"ELEMENT_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY"}
    required_edges = set(_load_sources(c)["FACT"].values())
    if required_nodes - set(nodes.columns) or required_edges - set(edges.columns):
        raise LoadError("MISSING_CANONICAL_GRAPH_COLUMNS")
    for frame, key in ((nodes, "NV"), (edges, "EV")):
        frame.write.save_as_table(names[key], mode="errorifexists", table_type="temporary")
    nv, ev = names["NV"], names["EV"]
    _load_unique(session, nv, "NODE_KEY")
    _load_unique(session, ev, "EDGE_KEY")
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM {nv} WHERE
 SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID))=0
 OR INSTANCE_KEY IS NULL OR LENGTH(TRIM(INSTANCE_KEY))=0
 OR ELEMENT_PATH IS NULL OR (ELEMENT_PATH<>{root}
     AND NOT STARTSWITH(ELEMENT_PATH, {root}||'.'))
 OR ELEMENT_TYPE IS DISTINCT FROM CASE WHEN ELEMENT_PATH={root} THEN {root_type} ELSE REPLACE(SPLIT_PART(ELEMENT_PATH,'.',-1),'[]','') END
 OR NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(METADATA_JSON)),FALSE)""", "INVALID_MODEL_PATH_IDENTITY_OR_PAYLOAD")
    roots = f"SELECT SOURCE_RECORD_ID FROM {nv} WHERE ELEMENT_PATH={root}"
    _load_unique(session, f"({roots})", "SOURCE_RECORD_ID")
    _load_query(session, f"CREATE TEMPORARY TABLE {names['IDS']} AS {roots}")
    selected = _load_count(session, f"SELECT COUNT(*) AS N FROM {names['IDS']}")
    if selected == 0:
        raise LoadError("EMPTY_INPUT_NOT_AUTHORIZED")
    # Explicit collection context is preserved; singleton parent may leave it NULL.
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM {ev} e
 JOIN {nv} p ON LOWER(p.NODE_KEY)=LOWER(e.FK_SOURCE_ELEMENT_HASH)
 JOIN {nv} c ON LOWER(c.NODE_KEY)=LOWER(e.FK_TARGET_ELEMENT_HASH)
 WHERE NOT STARTSWITH(c.ELEMENT_PATH, p.ELEMENT_PATH||'.')
 OR (c.PARENT_INSTANCE_KEY IS NOT NULL AND
     c.PARENT_INSTANCE_KEY IS DISTINCT FROM p.INSTANCE_KEY)""", "CANONICAL_PARENT_CONTEXT_MISMATCH")
    return selected


def _load_prepare(session, nodes, edges, config):
    c = _load_contract(config)
    if c is None:
        if config["EXECUTE_WRITES"]:
            raise LoadError("STORAGE_CONTRACT_NOT_VERIFIED")
        graph = _load_logical_graph(nodes, edges, _load_graph_contract(config), config.get("EXPECTED_SOURCE_RECORDS"))
        return {"storage_verified": False, "candidate": graph, "records": graph["SELECTED_RECORDS"]}
    dim_table, fact_table, dk, fk = _load_targets(c)
    _load_no_transaction(session)
    prefix = c["TARGET_DIM"].rsplit(".", 1)[0] + ".TMP_OSCAL_DAILY_" + uuid.uuid4().hex.upper()
    names = {k: prefix + "_" + k for k in ("NV", "EV", "IDS", "D", "F", "DB", "FB")}
    plans = [_load_column_plan(_load_query(session, "DESC TABLE " + target), kind, c)
             for target, kind in ((dim_table, "DIM"), (fact_table, "FACT"))]
    _load_selection_schema(plans, c)
    records = _load_freeze(session, nodes, edges, names, c)
    expected_records = config.get("EXPECTED_SOURCE_RECORDS")
    if expected_records is not None and (
            type(expected_records) is not int or expected_records <= 0 or records != expected_records):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH",
                        {"EXPECTED_SOURCE_RECORDS": expected_records, "GRAPH_SOURCE_RECORDS": records})
    for raw, physical, plan in zip(("NV", "EV"), ("D", "F"), plans):
        _load_stage(session, names[raw], names[physical], plan)
    candidates = (f"SELECT * FROM {names['D']}", f"SELECT * FROM {names['F']}")
    candidate = _load_integrity(session, candidates, names["IDS"], records, contract=c)
    for query, plan in zip(candidates, plans):
        _load_storage_values(session, query, plan)
    for target, key in ((dim_table, "DB"), (fact_table, "FB")):
        _load_query(session, f"CREATE TEMPORARY TABLE {names[key]} AS SELECT * FROM {target}")
    context = {"names": names, "plans": plans, "records": records, "candidate": candidate, "contract": c, "storage_verified": True}
    context["scope"] = _load_scope_check(session, names, plans, c)
    _load_integrity(session, _load_scope_queries(names, c), names["IDS"], records, allow_absent=True, contract=c)
    context["changes"] = [
        _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        for target, kind, pk, plan in zip((dim_table, fact_table), ("D", "F"),
                                         (dk, fk), plans)]
    return context

def _load_unchanged_scope(session, names, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    for target, baseline, kind, pk in (
        (dim_table, names["DB"], "D", dk),
        (fact_table, names["FB"], "F", fk)):
        current = f"SELECT t.* FROM {target} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        frozen = f"SELECT t.* FROM {baseline} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        for lhs, rhs in ((current, frozen), (frozen, current)):
            _load_zero(session, f"SELECT COUNT(*) AS N FROM (({lhs}) MINUS ({rhs}))",
                       "UNTOUCHED_TARGET_ROWS_CHANGED")


def _load_verify_context(session, context):
    c = _load_runtime_contract(context.get("contract"))
    dim_table, fact_table, dk, fk = _load_targets(c)
    names, plans = context["names"], context["plans"]
    scope = _load_scope_check(session, names, plans, c)
    saved = _load_integrity(session, _load_scope_queries(names, c), names["IDS"], context["records"], contract=c)
    reports = {}
    for target, kind, pk, plan, baseline in zip(
            (dim_table, fact_table), ("D", "F"), (dk, fk),
            plans, (names["DB"], names["FB"])):
        changes = _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        if changes["INSERTS"] or changes["UPDATES"]:
            raise LoadError("SAVED_BUSINESS_PAYLOAD_OR_KEYS_DIFFER", {"TABLE_KIND": kind, "COUNTS": changes})
        # Business-unchanged rows retain prior fields, including audit. Updated/new
        # rows must match every projected stage field, including current audit.
        cols = _load_columns(plan)
        business_same = "NOT (" + _load_difference_predicate(plan, "b", "s") + ")"
        all_old = " OR ".join("t." + _load_ident(c) + " IS DISTINCT FROM b." + _load_ident(c) for c in cols)
        all_new = " OR ".join(
            ("TRY_PARSE_JSON(TO_VARCHAR(t." + _load_ident(c) + ")) IS DISTINCT FROM "
             "TRY_PARSE_JSON(TO_VARCHAR(s." + _load_ident(c) + "))") if c == "METADATA_JSON"
            else "t." + _load_ident(c) + " IS DISTINCT FROM s." + _load_ident(c) for c in cols)
        _load_zero(session, f"""SELECT COUNT(*) AS N FROM {names[kind]} s
 JOIN {target} t ON t.{pk}=s.{pk} LEFT JOIN {baseline} b ON b.{pk}=s.{pk}
 WHERE (b.{pk} IS NOT NULL AND ({business_same}) AND ({all_old}))
 OR ((b.{pk} IS NULL OR NOT ({business_same})) AND ({all_new}))""",
                   "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER")
        reports["DIM" if kind == "D" else "FACT"] = changes
    _load_unchanged_scope(session, names, c)
    reports.update({"KEY_INTEGRITY": saved, "SCOPE": scope})
    return reports


def _load_dml_counts(rows):
    if len(rows) != 1:
        raise LoadError("DML_ROW_COUNT_UNAVAILABLE")
    row = {str(k).lower(): v for k, v in _load_row(rows[0]).items()}
    counts = []
    for label in ("number of rows inserted", "number of rows updated"):
        value = row.get(label)
        if type(value) not in (int, str) or not re.fullmatch(r"[0-9]+", str(value)):
            raise LoadError("DML_ROW_COUNT_UNAVAILABLE")
        counts.append(int(value))
    return tuple(counts)


def _load_transaction(session, merges, before_write, verify, expected_changes, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    if (not isinstance(merges, (list, tuple)) or len(merges) != 2
            or not isinstance(expected_changes, (list, tuple)) or len(expected_changes) != 2
            or any(not isinstance(pair, (list, tuple)) or len(pair) != 2
                   or any(type(v) is not int or v < 0 for v in pair) for pair in expected_changes)
            or not callable(before_write) or not callable(verify)):
        raise LoadError("INVALID_TRANSACTION_ARGUMENTS")
    for statement, target in zip(merges, (dim_table, fact_table)):
        if (not isinstance(statement, str) or ";" in statement
                or not statement.startswith("MERGE INTO " + target + " t USING ")
                or "WHEN MATCHED AND (" not in statement or "WHEN NOT MATCHED THEN INSERT" not in statement
                or re.search(r"\b(?:DELETE|TRUNCATE|DROP|CREATE|ALTER)\b", statement, re.IGNORECASE)):
            raise LoadError("MERGE_OUTSIDE_APPROVED_UPSERT_POLICY")
    _load_no_transaction(session)
    try:
        _load_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise LoadError("BEGIN_OUTCOME_UNKNOWN") from None
    step, pass_number, changes, checks = "PREWRITE_BASELINE", 0, [], []
    try:
        before_write()
        for pass_number in (1, 2):
            result = []
            for index, (step, statement) in enumerate(zip(("DIM_MERGE", "FACT_MERGE"), merges)):
                actual = _load_dml_counts(_load_query(session, statement))
                expected = tuple(expected_changes[index]) if pass_number == 1 else (0, 0)
                if actual != expected:
                    raise LoadError("UNEXPECTED_MERGE_CHANGE_COUNT",
                                    {"EXPECTED_INSERTS": expected[0], "EXPECTED_UPDATES": expected[1],
                                     "ACTUAL_INSERTS": actual[0], "ACTUAL_UPDATES": actual[1]})
                result.append({"INSERTS": actual[0], "UPDATES": actual[1]})
            changes.append({"PASS": pass_number, "DIM": result[0], "FACT": result[1]})
            step = "READBACK_AND_INTEGRITY"
            checks.append(verify(pass_number))
    except BaseException as error:
        details = dict(_load_error_details(error), STEP=step, PASS=pass_number)
        try:
            _load_query(session, "ROLLBACK")
        except BaseException:
            raise LoadError("ROLLBACK_OUTCOME_UNKNOWN", details) from None
        raise LoadError("TRANSACTION_ROLLED_BACK", details) from None
    try:
        _load_query(session, "COMMIT")
    except BaseException:
        raise LoadError("COMMIT_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED", "CHANGE_COUNTS": changes, "VERIFIED_PASSES": len(checks)}


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    config = dict(config)
    result = {"release": OSCAL_LOAD_RELEASE, "model": config.get("OSCAL_MODEL"),
              "mode": "COMMIT" if config.get("EXECUTE_WRITES") is True else "PREVIEW",
              "writes_executed": False, "persisted": False, "target_dml_attempted": False,
              "obsolete_policy": "BLOCK"}
    phase, context = "SCHEMA_STAGING_AND_PREFLIGHT", None
    try:
        context = _load_prepare(session, canonical_nodes_df, canonical_edges_df, config)
        candidate = context["candidate"]
        if context.get("storage_verified") is False:
            result.update(status="MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING",
                          validation_passed=True, pre_write_validation_passed=False, storage_verified=False,
                          nodes=int(candidate["NODES"]), edges=int(candidate["EDGES"]),
                          source_records=context["records"], graph_integrity=candidate,
                          dim_load_rows=0, fact_load_rows=0)
            return result
        c = _load_runtime_contract(context.get("contract"))
        dim_table, fact_table, dk, fk = _load_targets(c)
        result.update(nodes=int(candidate["NODES"]), edges=int(candidate["EDGES"]),
                      source_records=context["records"], validation_passed=True,
                      pre_write_validation_passed=True, storage_verified=True, dim_load_rows=int(candidate["NODES"]),
                      fact_load_rows=int(candidate["EDGES"]), scope=context["scope"],
                      expected_changes={"DIM": context["changes"][0], "FACT": context["changes"][1]})
        print("Graph nodes:", result["nodes"])
        print("Graph edges:", result["edges"])
        print("Duplicate node keys:", candidate["DIM_DUPLICATE_KEYS"])
        print("Duplicate edge keys:", candidate["FACT_DUPLICATE_KEYS"])
        print("Dangling source edges:", candidate["DANGLING_SOURCE_KEYS"])
        print("Dangling target edges:", candidate["DANGLING_TARGET_KEYS"])
        print("PRE-WRITE VALIDATION PASSED")
        if not config["EXECUTE_WRITES"]:
            result["status"] = "DAILY_" + c["MODEL_KEY"] + "_PREVIEW_PASSED_NO_TARGET_DML"
            print("EXECUTE_WRITES = False; no DIM/FACT changes were made")
            return result
        names, plans = context["names"], context["plans"]
        queries = (f"SELECT * FROM {dim_table}", f"SELECT * FROM {fact_table}")
        merges = [_build_merge_sql(target, names[kind], pk, plan, c) for target, kind, pk, plan in
                  zip((dim_table, fact_table), ("D", "F"), (dk, fk), plans)]
        expected = tuple((int(c["INSERTS"]), int(c["UPDATES"])) for c in context["changes"])

        def before_write():
            _load_baseline_equal(session, names, queries)
            _load_scope_check(session, names, plans, c)
            result["target_dml_attempted"] = True

        phase = "TRANSACTION"
        transaction = _load_transaction(session, merges, before_write,
                                        lambda number: _load_verify_context(session, context), expected,
                                        **({"contract": c} if "contract" in context else {}))
        result.update(writes_executed=True, persisted=True, transaction=transaction,
                      dim_merge_result=transaction["CHANGE_COUNTS"][0]["DIM"],
                      fact_merge_result=transaction["CHANGE_COUNTS"][0]["FACT"])
        phase = "POST_COMMIT_READBACK"
        verification = _load_verify_context(session, context)
        verification.update(dim_expected=result["nodes"], dim_matched=result["nodes"],
                            fact_expected=result["edges"], fact_matched=result["edges"])
        result.update(status="DAILY_" + c["MODEL_KEY"] + "_COMMITTED_AND_VERIFIED", verification=verification)
        print("LOAD VERIFIED")
        return result
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "DAILY_LOAD_OPERATION_FAILED"
        result.update(status=code, phase=phase, error_details=_load_error_details(error))
        if code in ("BEGIN_OUTCOME_UNKNOWN", "COMMIT_OUTCOME_UNKNOWN", "ROLLBACK_OUTCOME_UNKNOWN"):
            result["persisted"] = "UNKNOWN_DO_NOT_RETRY"
        elif code == "TRANSACTION_ROLLED_BACK" and context:
            try:
                _load_baseline_equal(session, context["names"],
                                     (f"SELECT * FROM {dim_table}", f"SELECT * FROM {fact_table}"))
                result["rollback_readback_verified"] = True
            except BaseException:
                result.update(status="ROLLBACK_READBACK_FAILED_DO_NOT_RETRY", persisted="UNKNOWN_DO_NOT_RETRY")
        if phase == "POST_COMMIT_READBACK":
            result["status"] = "POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY"
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        raise LoadError(result["status"], result) from None


def verify_oscal_load(canonical_nodes_df, canonical_edges_df, config):
    # Public API freezes fresh logical inputs; no target DML is performed.
    read_config = dict(config)
    read_config["EXECUTE_WRITES"] = False
    try:
        context = _load_prepare(session, canonical_nodes_df, canonical_edges_df, read_config)
        if context.get("storage_verified") is False:
            return {"status": "MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING",
                    "validation_passed": True, "storage_verified": False, "writes_executed": False,
                    "dim_expected": context["candidate"]["NODES"], "fact_expected": context["candidate"]["EDGES"],
                    "dim_matched": None, "fact_matched": None}
        report = _load_verify_context(session, context)
        n, e = int(context["candidate"]["NODES"]), int(context["candidate"]["EDGES"])
        report.update(dim_expected=n, dim_matched=n, fact_expected=e, fact_matched=e)
        return report
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "READ_ONLY_VERIFICATION_FAILED"
        raise LoadError(code, _load_error_details(error)) from None



def _load_legacy_contract():
    # Compatibility adapter only: actual configured runs provide STORAGE_CONTRACT.
    return MappingProxyType({
        "MODEL_KEY": "SSP", "ROOT_PATH": "system-security-plan",
        "ROOT_ELEMENT_TYPE": "system-security-plan", "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": SSP_LOAD_SOURCE,
        "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC." + SSP_LOAD_SOURCE,
        "TARGET_DIM": SSP_LOAD_DIM, "TARGET_FACT": SSP_LOAD_FACT,
        "DIM_PK_COLUMN": SSP_LOAD_DIM_PK, "FACT_PK_COLUMN": SSP_LOAD_FACT_PK,
        "IDENTITY_VERSION": "v1_registry_path_instance",
        "PHYSICAL_PROFILE": "BINARY16_UUID32", "VERIFIED": True,
    })


def _load_literal(value):
    if not isinstance(value, str) or not value.strip():
        raise LoadError("EMPTY_CONTRACT_VALUE")
    return "'" + value.replace("'", "''") + "'"


def _load_runtime_contract(contract=None):
    if contract is None:
        return _load_legacy_contract()
    if not isinstance(contract, (dict, MappingProxyType)):
        raise LoadError("INVALID_STORAGE_CONTRACT")
    copied = dict(contract)
    required = ("MODEL_KEY", "ROOT_PATH", "ROOT_ELEMENT_TYPE", "SOURCE_SYSTEM_NAME",
                "SOURCE_TABLE_NAME", "RAW_TABLE", "TARGET_DIM", "TARGET_FACT",
                "DIM_PK_COLUMN", "FACT_PK_COLUMN", "IDENTITY_VERSION", "PHYSICAL_PROFILE")
    if copied.get("VERIFIED") is not True or any(
            not isinstance(copied.get(k), str) or not copied[k].strip() for k in required):
        raise LoadError("STORAGE_CONTRACT_NOT_VERIFIED")
    if copied["PHYSICAL_PROFILE"] != "BINARY16_UUID32":
        raise LoadError("UNSUPPORTED_REVIEWED_PHYSICAL_PROFILE")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", copied["MODEL_KEY"]):
        raise LoadError("INVALID_MODEL_KEY")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", copied["ROOT_PATH"]):
        raise LoadError("INVALID_MODEL_ROOT_PATH")
    for key in ("RAW_TABLE", "TARGET_DIM", "TARGET_FACT"):
        parts = copied[key].split(".")
        if len(parts) != 3:
            raise LoadError("FULLY_QUALIFIED_CONTRACT_TABLE_REQUIRED")
        for part in parts:
            _load_ident(part)
    for key in ("DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        _load_ident(copied[key])
    if copied["TARGET_DIM"] == copied["TARGET_FACT"]:
        raise LoadError("DIM_AND_FACT_TARGETS_MUST_DIFFER")
    return MappingProxyType({k: copied[k] for k in (*required, 'VERIFIED')})


def _load_targets(contract):
    return (contract["TARGET_DIM"], contract["TARGET_FACT"],
            contract["DIM_PK_COLUMN"], contract["FACT_PK_COLUMN"])


def _load_sources(contract):
    dim = {k: v for k, v in _LOAD_DIM_SOURCES.items() if v != "NODE_KEY"}
    fact = {k: v for k, v in _LOAD_FACT_SOURCES.items() if v != "EDGE_KEY"}
    dim[contract["DIM_PK_COLUMN"]] = "NODE_KEY"
    fact[contract["FACT_PK_COLUMN"]] = "EDGE_KEY"
    return {"DIM": dim, "FACT": fact}


def _load_graph_contract(config):
    root = config.get("ROOT_PATH", config.get("MODEL_ROOT_PATH"))
    if root is None and "STORAGE_CONTRACT" not in config:
        legacy = _load_legacy_contract()
        if config.get("OSCAL_MODEL") == legacy["MODEL_KEY"]:
            root = legacy["ROOT_PATH"]
    fields = {"MODEL_KEY": config.get("OSCAL_MODEL"), "ROOT_PATH": root,
              "ROOT_ELEMENT_TYPE": config.get("ROOT_ELEMENT_TYPE"),
              "SOURCE_SYSTEM_NAME": config.get("SOURCE_SYSTEM_NAME"),
              "SOURCE_TABLE_NAME": config.get("SOURCE_TABLE_NAME"),
              "RAW_TABLE": config.get("RAW_TABLE"),
              "IDENTITY_VERSION": config.get("IDENTITY_VERSION")}
    for key in ("MODEL_KEY", "ROOT_PATH", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
                "RAW_TABLE", "IDENTITY_VERSION"):
        if not isinstance(fields[key], str) or not fields[key].strip():
            raise LoadError("MISSING_GRAPH_CONTRACT_" + key)
    if not re.fullmatch(r"[a-z][a-z0-9-]*", root):
        raise LoadError("INVALID_MODEL_ROOT_PATH")
    return MappingProxyType(fields)


def _load_contract(config):
    if type(config.get("EXECUTE_WRITES")) is not bool:
        raise LoadError("EXPLICIT_BOOLEAN_WRITE_MODE_REQUIRED")
    if config.get("OBSOLETE_ROW_POLICY", "BLOCK") != "BLOCK":
        raise LoadError("ONLY_BLOCK_OBSOLETE_POLICY_IS_APPROVED")
    if "STORAGE_CONTRACT" in config:
        supplied = config["STORAGE_CONTRACT"]
        if supplied is None or (isinstance(supplied, (dict, MappingProxyType))
                                and supplied.get("VERIFIED") is not True):
            return None
        contract = _load_runtime_contract(supplied)
    else:
        contract = _load_legacy_contract()
        required = {"OSCAL_MODEL": contract["MODEL_KEY"], "TARGET_DIM": contract["TARGET_DIM"],
                    "TARGET_FACT": contract["TARGET_FACT"], "DIM_PK_COLUMN": contract["DIM_PK_COLUMN"],
                    "FACT_PK_COLUMN": contract["FACT_PK_COLUMN"], "SOURCE_SYSTEM_NAME": contract["SOURCE_SYSTEM_NAME"],
                    "SOURCE_TABLE_NAME": contract["SOURCE_TABLE_NAME"], "RAW_TABLE": contract["RAW_TABLE"],
                    "IDENTITY_VERSION": contract["IDENTITY_VERSION"]}
        if any(config.get(k) != v for k, v in required.items()):
            return None
    matches = {"OSCAL_MODEL": "MODEL_KEY", "SOURCE_SYSTEM_NAME": "SOURCE_SYSTEM_NAME",
               "SOURCE_TABLE_NAME": "SOURCE_TABLE_NAME", "RAW_TABLE": "RAW_TABLE",
               "IDENTITY_VERSION": "IDENTITY_VERSION"}
    for cfg, key in matches.items():
        if config.get(cfg) != contract[key]:
            raise LoadError("CONFIG_STORAGE_CONTRACT_MISMATCH")
    for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        if config.get(key) is not None and config[key] != contract[key]:
            raise LoadError("CONFIG_STORAGE_CONTRACT_MISMATCH")
    root = config.get("ROOT_PATH", config.get("MODEL_ROOT_PATH"))
    if root is not None and root != contract["ROOT_PATH"]:
        raise LoadError("CONFIG_STORAGE_ROOT_MISMATCH")
    if config.get("ROOT_ELEMENT_TYPE") not in (None, contract["ROOT_ELEMENT_TYPE"]):
        raise LoadError("CONFIG_STORAGE_ROOT_TYPE_MISMATCH")
    return contract


def _load_logical_graph(nodes, edges, contract, expected_records=None):
    # A targetless preview reads only the canonical graph, never target metadata.
    # Payloads are checked then discarded; reports contain aggregate counts only.
    def rows(frame):
        return frame.to_local_iterator() if hasattr(frame, "to_local_iterator") else iter(frame)
    def row(value):
        return value.as_dict() if hasattr(value, "as_dict") else dict(value)
    def key(value):
        if not isinstance(value, str) or not re.fullmatch(_LOAD_HEX_PATTERN, value):
            raise LoadError("INVALID_LOGICAL_HASH_IDENTITY")
        return value.lower()
    def canonical_uuid(value):
        if not isinstance(value, str) or not re.fullmatch(_LOAD_UUID_PATTERN, value):
            raise LoadError("INVALID_LOGICAL_UUID")
        return value

    root = contract["ROOT_PATH"]
    by_key, roots, parents, children, root_types = {}, {}, {}, {}, set()
    for raw in rows(nodes):
        n = row(raw)
        k = key(n.get("NODE_KEY"))
        if k in by_key:
            raise LoadError("DUPLICATE_LOGICAL_NODE_KEY")
        sid, path, typ = n.get("SOURCE_RECORD_ID"), n.get("ELEMENT_PATH"), n.get("ELEMENT_TYPE")
        if not isinstance(sid, str) or not sid.strip():
            raise LoadError("MISSING_LOGICAL_SOURCE_RECORD_ID")
        if (not isinstance(path, str) or not (path == root or path.startswith(root + "."))
                or not isinstance(typ, str) or not typ.strip()):
            raise LoadError("LOGICAL_MODEL_PATH_OR_TYPE_MISMATCH")
        if (n.get("SOURCE_SYSTEM_NAME") != contract["SOURCE_SYSTEM_NAME"]
                or n.get("SOURCE_TABLE_NAME") != contract["SOURCE_TABLE_NAME"]
                or ("MODEL_KEY" in n and n["MODEL_KEY"] != contract["MODEL_KEY"])):
            raise LoadError("LOGICAL_MODEL_OR_SOURCE_OWNERSHIP_MISMATCH")
        instance = n.get("INSTANCE_KEY")
        if not isinstance(instance, str) or not instance.strip():
            raise LoadError("MISSING_LOGICAL_INSTANCE_KEY")
        payload = n.get("METADATA_JSON")
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except (ValueError, TypeError):
            raise LoadError("INVALID_LOGICAL_PAYLOAD") from None
        if not isinstance(payload, dict):
            raise LoadError("INVALID_LOGICAL_PAYLOAD")
        by_key[k] = (sid, path, canonical_uuid(n.get("OSCAL_UUID")), instance, n.get("PARENT_INSTANCE_KEY"))
        parents[k], children[k] = 0, []
        if path == root:
            if sid in roots:
                raise LoadError("MULTIPLE_MODEL_ROOTS_FOR_RECORD")
            roots[sid] = k
            root_types.add(typ)
            if contract.get("ROOT_ELEMENT_TYPE") not in (None, typ):
                raise LoadError("LOGICAL_ROOT_REGISTRY_TYPE_MISMATCH")
    if not roots or len(root_types) != 1:
        raise LoadError("EMPTY_OR_INCONSISTENT_MODEL_ROOTS")
    if expected_records is not None and (type(expected_records) is not int
                                         or expected_records != len(roots)):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH")
    edge_keys = set()
    for raw in rows(edges):
        e = row(raw)
        ek = key(e.get("EDGE_KEY"))
        if ek in edge_keys:
            raise LoadError("DUPLICATE_LOGICAL_EDGE_KEY")
        edge_keys.add(ek)
        source, target = key(e.get("FK_SOURCE_ELEMENT_HASH")), key(e.get("FK_TARGET_ELEMENT_HASH"))
        if source not in by_key or target not in by_key:
            raise LoadError("DANGLING_LOGICAL_FOREIGN_KEY")
        s, t = by_key[source], by_key[target]
        if s[0] != t[0] or s[0] not in roots:
            raise LoadError("CROSS_RECORD_LOGICAL_EDGE")
        if (e.get("DEPENDENCY_TYPE") != "CONTAINS"
                or canonical_uuid(e.get("SOURCE_OSCAL_UUID")) != s[2]
                or canonical_uuid(e.get("TARGET_OSCAL_UUID")) != t[2]):
            raise LoadError("LOGICAL_RELATIONSHIP_OR_UUID_MISMATCH")
        if not t[1].startswith(s[1] + ".") or (t[4] is not None and t[4] != s[3]):
            raise LoadError("LOGICAL_PARENT_CONTEXT_MISMATCH")
        parents[target] += 1
        children[source].append(target)
    root_keys = set(roots.values())
    if any(parents[k] != (0 if k in root_keys else 1) for k in by_key):
        raise LoadError("INVALID_LOGICAL_PARENT_CARDINALITY")
    visited, pending = set(), list(root_keys)
    while pending:
        k = pending.pop()
        if k in visited:
            raise LoadError("LOGICAL_GRAPH_CYCLE")
        visited.add(k)
        pending.extend(children[k])
    if visited != set(by_key) or any(n[0] not in roots for n in by_key.values()):
        raise LoadError("DISCONNECTED_LOGICAL_GRAPH")
    return {"SELECTED_RECORDS": len(roots), "NODES": len(by_key), "EDGES": len(edge_keys),
            "DIM_DUPLICATE_KEYS": 0, "FACT_DUPLICATE_KEYS": 0,
            "DANGLING_SOURCE_KEYS": 0, "DANGLING_TARGET_KEYS": 0,
            "ROOTS": len(roots), "DISCONNECTED_RECORDS": 0}


validate_and_load_oscal._oscal_loader_release = "oscal-shared-daily-upsert-v2"
print("Cell 6 validation and loader initialized; execution remains in Cell 7")


# %% Cell 7 - OSCAL mapper orchestrator

import copy
import json

# One runner for all configured source/model routes. No daily truncate.
# Keep Cell 1 EXECUTE_WRITES=False. COMMIT needs every selected storage contract
# verified; the shipped AR route has no verified destination, so use PREVIEW.
OSCAL_LOAD_MODE = "PREVIEW"


class PipelineError(ValueError):
    def __init__(self, message, report):
        super().__init__(message)
        self.report = report
        self.details = report


def _oscal_run_config(config, load_mode):
    if load_mode not in ("PREVIEW", "COMMIT"):
        raise ValueError("OSCAL_LOAD_MODE must be PREVIEW or COMMIT")
    if config.get("EXECUTE_WRITES") is not False:
        raise ValueError("Keep the shared CONFIG EXECUTE_WRITES false; select the Cell 7 load mode")
    if getattr(globals().get("validate_and_load_oscal"), "_oscal_loader_release", None) != "oscal-shared-daily-upsert-v2":
        raise ValueError("Run the matching updated Cell 6 before this Cell 7")
    if load_mode == "COMMIT" and (config.get("STORAGE_CONTRACT") or {}).get("VERIFIED") is not True:
        raise ValueError("Every selected source/model route needs a verified storage contract before COMMIT")
    run_config = dict(config)
    run_config["EXECUTE_WRITES"] = load_mode == "COMMIT"
    return run_config


def _oscal_source_count(source_df):
    if "SOURCE_RECORD_ID" not in source_df.columns:
        raise ValueError("Source input must expose SOURCE_RECORD_ID")
    if source_df.filter("SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID)) = 0").count():
        raise ValueError("Source input has missing record identities; no write attempted")
    count = source_df.count()
    if count == 0:
        raise ValueError("Empty source input is not authorization to change targets")
    return count


def run_oscal_mapping(
    source_df, canonical_mapping_df, element_registry_df, config,
    load_mode="PREVIEW", context=None,
):
    run_config = _oscal_run_config(config, load_mode)
    run_config["EXPECTED_SOURCE_RECORDS"] = _oscal_source_count(source_df)
    graph_arguments = dict(
        source_df=source_df, canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df, model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"], source_table=config["SOURCE_TABLE_NAME"],
    )
    if context is not None:
        graph_arguments["context"] = context
    nodes_df, edges_df = build_oscal_graph(**graph_arguments)
    coverage_df = None
    if config.get("BUILD_COVERAGE_REPORT", False):
        mapping_rows = context["mapping_rows"] if context is not None else CANONICAL_MAPPING_ROWS
        coverage_df = build_mapping_coverage(source_df, mapping_rows)
    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df, canonical_edges_df=edges_df, config=run_config,
    )
    return nodes_df, edges_df, coverage_df, result


def run_oscal_pipeline(source_inputs, mapping_contexts, load_mode="PREVIEW"):
    """Validate every selected route before commits; never swap model globals.

    Commits are per source/model transaction, not one distributed transaction.
    A later commit failure reports prior committed groups and stops; no retry.
    """
    report = {"status": "NOT_RUN", "mode": load_mode, "writes_executed": False,
              "commit_attempted": False, "groups": []}
    graphs, seen = {}, set()
    context = None
    phase = "routing"
    try:
        if not mapping_contexts:
            raise ValueError("No configured mapping routes")
        for original in mapping_contexts:
            key = (original["source_key"], original["config"]["OSCAL_MODEL"])
            report["active_group"] = {"source": key[0], "model": key[1]}
            report["active_routing"] = copy.deepcopy(original["routing_report"])
            if key in seen:
                raise ValueError("Duplicate source/model route")
            seen.add(key)
            if key[0] not in source_inputs:
                raise ValueError("Missing selected source input")
            if original["routing_report"].get("STATUS") != "READY":
                raise ValueError("Mapping routing has blocked rows")
            if not original["mapping_rows"]:
                raise ValueError("Selected route has no approved mappings")
            _oscal_run_config(original["config"], load_mode)
        # Build and validate every candidate before the first target commit.
        phase = "preview"
        for original in mapping_contexts:
            key = (original["source_key"], original["config"]["OSCAL_MODEL"])
            context = copy.deepcopy(original)
            report["active_group"] = {"source": key[0], "model": key[1]}
            context["lookups"] = dict(source_inputs[key[0]].get("lookups", {}))
            nodes, edges, coverage, result = run_oscal_mapping(
                source_inputs[key[0]]["source_df"], None, None, context["config"],
                load_mode="PREVIEW", context=context,
            )
            if result.get("validation_passed") is not True:
                raise ValueError("Candidate graph validation did not pass")
            if result.get("writes_executed") is not False:
                raise ValueError("Preview reported an unexpected target write")
            context["config"]["EXPECTED_SOURCE_RECORDS"] = result.get(
                "source_records", context.get("graph_report", {}).get("SOURCE_RECORDS")
            )
            graphs[key] = {"nodes": nodes, "edges": edges, "coverage": coverage, "context": context}
            report["groups"].append({
                "source": key[0], "model": key[1], "status": result.get("status", "VALIDATED"),
                "routing": copy.deepcopy(context["routing_report"]),
                "graph": copy.deepcopy(context.get("graph_report", {})), "load": result,
            })
        if load_mode == "COMMIT":
            phase = "commit"
            for group in report["groups"]:
                report["active_group"] = {"source": group["source"], "model": group["model"]}
                graph = graphs[(group["source"], group["model"])]
                cfg = _oscal_run_config(graph["context"]["config"], "COMMIT")
                report["commit_attempted"] = True
                result = validate_and_load_oscal(
                    canonical_nodes_df=graph["nodes"], canonical_edges_df=graph["edges"], config=cfg,
                )
                group.update(status=result.get("status", "UNKNOWN"), load=result)
                report["writes_executed"] = report["writes_executed"] or result.get("writes_executed", False)
                if (result.get("writes_executed") is not True or result.get("persisted") is not True
                        or not str(result.get("status", "")).endswith("_COMMITTED_AND_VERIFIED")
                        or not isinstance(result.get("verification"), dict)):
                    raise ValueError("Commit requires confirmed persistence and read-back verification")
            report["status"] = "ALL_SELECTED_GROUPS_COMMITTED_AND_VERIFIED"
        else:
            pending = any(group["load"].get("storage_verified") is False for group in report["groups"])
            report["status"] = ("PREVIEW_WITH_TARGET_CONTRACTS_PENDING" if pending
                                else "ALL_SELECTED_GROUPS_PREVIEW_VERIFIED")
        report.pop("active_group", None)
        report.pop("active_routing", None)
        return graphs, report
    except Exception as exc:
        report["status"] = ("PIPELINE_COMMIT_FAILED_REVIEW_REQUIRED" if report["commit_attempted"]
                            else "PIPELINE_FAILED_NO_TARGET_DML")
        report["failed_phase"] = phase
        report["error_type"] = type(exc).__name__
        if phase == "routing":
            report["error_reason"] = str(exc)
        if context is not None and "graph_report" in context:
            report["active_graph_report"] = copy.deepcopy(context["graph_report"])
        # Loader reports carry only approved diagnostics; never print source payloads.
        load_report = getattr(exc, "report", getattr(exc, "details", None))
        if isinstance(load_report, dict):
            report["failed_load_report"] = load_report
        if report["commit_attempted"]:
            report["failed_commit_outcome"] = "REVIEW_REQUIRED_NO_AUTOMATIC_RETRY"
        raise PipelineError("OSCAL pipeline stopped; inspect OSCAL_PIPELINE_REPORT", report) from None


# Clear old outputs first. A failed run must not expose the previous graph as new.
MODEL_GRAPHS = PIPELINE_REPORT = None
final_nodes_df = final_edges_df = mapping_coverage_df = run_result = None
try:
    MODEL_GRAPHS, PIPELINE_REPORT = run_oscal_pipeline(
        SOURCE_INPUTS, MAPPING_CONTEXTS, load_mode=OSCAL_LOAD_MODE,
    )
except PipelineError as error:
    PIPELINE_REPORT = error.report
    print("OSCAL_PIPELINE_REPORT")
    print(json.dumps(PIPELINE_REPORT, indent=2, sort_keys=True, default=str))
    raise
print("OSCAL_PIPELINE_REPORT")
print(json.dumps(PIPELINE_REPORT, indent=2, sort_keys=True, default=str))
# Compatibility outputs refer only to the explicitly configured default group.
_default_key = (SOURCE_PROFILES[0]["SOURCE_KEY"], CONFIG["OSCAL_MODEL"])
if _default_key in MODEL_GRAPHS:
    _graph = MODEL_GRAPHS[_default_key]
    final_nodes_df, final_edges_df = _graph["nodes"], _graph["edges"]
    mapping_coverage_df = _graph["coverage"]
    run_result = next(group["load"] for group in PIPELINE_REPORT["groups"]
                      if (group["source"], group["model"]) == _default_key)
