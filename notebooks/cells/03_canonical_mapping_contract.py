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
