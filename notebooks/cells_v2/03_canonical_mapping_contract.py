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
import json
import math
import re


# Engine capabilities, not source/model-specific mapping decisions.
METADATA_TRANSFORM_IDS = {
    "direct", "text", "timestamp", "date", "identifier", "archer-select",
    "scalar-score", "security-objective", "status-crosswalk", "reject-populated", "skip", "canonical-text",
}
METADATA_OPERATORS = {
    "object", "record", "properties", "values", "observations", "references",
    "roles", "parties", "assignments",
}


def _metadata_object(value, label):
    if value in (None, ""):
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            raise ValueError(label + " must contain a JSON object") from None
    if not isinstance(value, dict):
        raise ValueError(label + " must be an object")
    return copy.deepcopy(value)


def _metadata_words(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _compile_value_constraints(value):
    """Validate declarative output constraints once, before reading source values."""
    rules = _metadata_object(value, "VALUE_CONSTRAINTS")
    if set(rules) - {"required", "null_policy", "cardinality", "validation"}:
        raise ValueError("Unknown value constraint")
    if "required" in rules and not isinstance(rules["required"], bool):
        raise ValueError("Required must be a boolean")
    if rules.get("null_policy", "omit") not in {"omit", "reject"}:
        raise ValueError("Null policy must be omit or reject")
    cardinality = _metadata_object(rules.get("cardinality"), "Cardinality")
    if set(cardinality) - {"min", "max"}:
        raise ValueError("Cardinality supports only min and max")
    for key, limit in cardinality.items():
        if key == "max" and limit is None:
            continue
        if type(limit) is not int or limit < 0:
            raise ValueError("Cardinality limits must be nonnegative integers")
    lower, upper = cardinality.get("min", 0), cardinality.get("max")
    if upper is not None and (upper < lower or rules.get("required") and upper == 0):
        raise ValueError("Conflicting required/cardinality constraints")
    validation = _metadata_object(rules.get("validation"), "Validation")
    if set(validation) - {"type", "enum", "minimum", "maximum"}:
        raise ValueError("Unknown value validation")
    if "type" in validation and validation["type"] not in {"string", "integer", "number", "boolean", "object", "array"}:
        raise ValueError("Unknown validation type")
    if "enum" in validation:
        if not isinstance(validation["enum"], list) or not validation["enum"]:
            raise ValueError("Enum must be a nonempty JSON array")
        try:
            json.dumps(validation["enum"], allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError("Enum must contain JSON values") from None
    for key in ("minimum", "maximum"):
        if key in validation and (type(validation[key]) not in (int, float) or
                                  type(validation[key]) is float and not math.isfinite(validation[key])):
            raise ValueError("Numeric bounds must be finite numbers")
    if "minimum" in validation and "maximum" in validation and validation["minimum"] > validation["maximum"]:
        raise ValueError("Conflicting numeric bounds")
    if "cardinality" in rules:
        rules["cardinality"] = cardinality
    if "validation" in rules:
        rules["validation"] = validation
    return rules


def _metadata_rule_candidates(row, contract):
    return [rule for rule in contract.get("MAPPING_RULES", ())
            if row.get("SOURCE_FIELD_NAME") in rule.get("SOURCE_FIELDS", ())]


def _metadata_rule_matches(row, rule):
    checks = [row.get("OWNER_ELEMENT_PATH") == rule.get("OWNER_PATH")]
    for key, value in (
        ("MAPPING_TYPES", row.get("MAPPING_TYPE")),
        ("TARGET_FIELDS", row.get("OSCAL_FIELD_NAME") or row.get("FIELD_RELATIVE_PATH")),
        ("ARTIFACT_PATHS", row.get("OSCAL_ELEMENT_PATH")),
    ):
        if key in rule:
            if key == "MAPPING_TYPES":
                checks.append(_metadata_words(value) in {_metadata_words(v) for v in rule[key]})
            else:
                checks.append(value in rule[key])
    if "NOTES_EQUALS" in rule:
        checks.append(_metadata_words(row.get("NOTES")) == _metadata_words(rule["NOTES_EQUALS"]))
    for token in rule.get("NOTES_CONTAINS", ()):
        checks.append(_metadata_words(token) in _metadata_words(
            " ".join(str(row.get(k) or "") for k in ("NOTES", "TRANSFORMATION_LOGIC", "MAPPING_NOTES"))))
    checks.extend(not row.get(key) for key in rule.get("EMPTY_COLUMNS", ()))
    return all(checks)


def _compile_metadata_mapping(row, contract, elements):
    result = copy.deepcopy(row)
    approval = _model_token(row.get("APPROVAL_STATUS"))
    candidates = _metadata_rule_candidates(row, contract)
    matches = [rule for rule in candidates if _metadata_rule_matches(row, rule)]
    if len(matches) > 1:
        raise ValueError("Multiple approved metadata rules match one mapping")
    if approval:
        if approval != "approved":
            raise ValueError("Mapping metadata is not approved")
        if candidates and not matches:
            raise ValueError("Mapping contradicts its current reviewed release contract")
        chosen = matches[0] if matches else {}
        if chosen and row.get("TRANSFORM_ID") != chosen.get("TRANSFORM_ID"):
            raise ValueError("Transform conflicts with the current reviewed release contract")
        transform = row.get("TRANSFORM_ID")
        transform_params = _metadata_object(row.get("TRANSFORM_PARAMS"), "TRANSFORM_PARAMS")
        representation_params = _metadata_object(row.get("REPRESENTATION_PARAMS"), "REPRESENTATION_PARAMS")
        value_constraints = _compile_value_constraints(row.get("VALUE_CONSTRAINTS"))
        if chosen:
            for actual, key in ((transform_params, "TRANSFORM_PARAMS"),
                                (representation_params, "REPRESENTATION_PARAMS")):
                if actual != chosen.get(key, {}):
                    raise ValueError("Parameters conflict with the current reviewed release contract")
            if value_constraints != _compile_value_constraints(chosen.get("VALUE_CONSTRAINTS")):
                raise ValueError("Constraints conflict with the current reviewed release contract")
    else:
        if any(row.get(key) not in (None, "") for key in
               ("TRANSFORM_ID", "TRANSFORM_PARAMS", "REPRESENTATION", "REPRESENTATION_PARAMS", "VALUE_CONSTRAINTS")):
            raise ValueError("Executable mapping metadata requires explicit approval")
        if len(matches) != 1:
            raise ValueError("Mapping requires an explicit approved executable contract")
        chosen = matches[0]
        if chosen.get("APPROVAL_STATUS") not in {"APPROVED", "BLOCKED_IF_POPULATED"}:
            raise ValueError("Release metadata rule is not approved")
        transform = chosen.get("TRANSFORM_ID")
        transform_params = _metadata_object(chosen.get("TRANSFORM_PARAMS"), "TRANSFORM_PARAMS")
        representation_params = _metadata_object(chosen.get("REPRESENTATION_PARAMS"), "REPRESENTATION_PARAMS")
        value_constraints = _compile_value_constraints(chosen.get("VALUE_CONSTRAINTS"))
        approval = chosen["APPROVAL_STATUS"]
    if transform not in METADATA_TRANSFORM_IDS:
        raise ValueError("Unknown reusable transform identifier")
    if transform == "skip" and (value_constraints.get("required") or
                                value_constraints.get("null_policy") == "reject" or
                                value_constraints.get("cardinality", {}).get("min", 0) > 0):
        raise ValueError("Skip transform conflicts with required-value constraints")
    if chosen.get("APPROVAL_STATUS") == "BLOCKED_IF_POPULATED" and transform != "reject-populated":
        raise ValueError("Unresolved populated values must remain rejected")
    owner = row["OWNER_ELEMENT_PATH"]
    if owner not in elements:
        raise ValueError("Mapping has no metadata-defined element operator")
    operator = elements[owner]["operator"]
    if row.get("REPRESENTATION") not in (None, "", operator):
        raise ValueError("Mapping representation conflicts with its element operator")
    result.update(
        TRANSFORM_ID=transform, TRANSFORM_PARAMS=transform_params,
        REPRESENTATION=operator, REPRESENTATION_PARAMS=representation_params,
        VALUE_CONSTRAINTS=value_constraints,
        APPROVAL_STATUS=(chosen.get("APPROVAL_STATUS") or "APPROVED"),
        RULE_ID=chosen.get("RULE_ID") or row.get("RULE_ID") or row.get("MAPPING_ID"),
        CONTRACT_SOURCE="reviewed-catalog" if chosen else "mapping-artifact",
    )
    return result


def compile_metadata_plan(context):
    """Compile approved metadata to inert operations; never evaluate Notes as code."""
    contract = context["model_contract"]
    definitions = _metadata_object(contract.get("ELEMENTS"), "ELEMENTS")
    default = _metadata_object(contract.get("DEFAULT_ELEMENT"), "DEFAULT_ELEMENT")
    default_scope = default.get("scope", "noncollection")
    if default_scope not in {"noncollection", "singletons-without-collection-ancestors"}:
        raise ValueError("Unknown default element scope")
    elements = {}
    mapped_paths = {row["OWNER_ELEMENT_PATH"] for row in context["mapping_rows"]}
    for registry in context["registry_rows"]:
        path = _registry_path(registry)
        definition = definitions.get(path)
        collection = str(registry.get("IS_COLLECTION", False)).upper() in {"TRUE", "T", "1", "YES", "Y"}
        if definition is None:
            if (not collection and default and
                    (default_scope != "singletons-without-collection-ancestors" or "[]" not in path)):
                definition = default
            elif path in mapped_paths:
                raise ValueError("Mapped registry path has no metadata-defined operator")
            else:
                continue
        definition = _metadata_object(definition, "Element definition")
        if definition.get("operator") not in METADATA_OPERATORS:
            raise ValueError("Unknown reusable element operator")
        definition["parameters"] = _metadata_object(definition.get("parameters"), "Element parameters")
        elements[path] = definition
    if contract["ROOT_PATH"] not in elements:
        raise ValueError("Registry root has no metadata-defined operator")
    mappings = [_compile_metadata_mapping(row, contract, elements) for row in context["mapping_rows"]]
    counts = {}
    for row in mappings:
        if row.get("RULE_ID"):
            counts[row["RULE_ID"]] = counts.get(row["RULE_ID"], 0) + 1
    if any(counts.get(rule_id) != 1 for rule_id in contract.get("REQUIRED_RULE_IDS", ())):
        raise ValueError("Required reviewed mapping row is missing or duplicated")
    reference_groups = []
    for group in contract.get("REFERENCE_GROUPS", []):
        required = {group[k] for k in ("roles_path", "parties_path", "assignments_path")}
        if required.issubset(elements):
            reference_groups.append(copy.deepcopy(group))
        elif required & mapped_paths:
            raise ValueError("Mapped reference family requires every governed registry path")
    return {"version": 1, "elements": elements, "mappings": mappings,
            "reference_groups": reference_groups,
            "options": copy.deepcopy(contract.get("RUNTIME_OPTIONS", {})),
            "report": copy.deepcopy(contract.get("REPORT", {})),
            "default_element": copy.deepcopy(default) if default else None}


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


def _summarize_routing_issues(report, sample_limit=25):
    """Keep exact issue counts but bound printed samples, showing blockers first."""
    issues = report["ISSUES"]
    reason_counts, severity_counts = {}, {}
    for issue in issues:
        count = issue.get("affected_rows", 1)
        reason = issue["reason"]
        severity = issue["severity"]
        reason_counts[reason] = reason_counts.get(reason, 0) + count
        severity_counts[severity] = severity_counts.get(severity, 0) + count
    ordered = sorted(issues, key=lambda issue: (
        0 if issue["severity"] == "BLOCKED" else 1,
        issue.get("row") if issue.get("row") is not None else -1,
    ))
    report.update(
        REASON_COUNTS=reason_counts, SEVERITY_COUNTS=severity_counts,
        ISSUE_EVENTS_TOTAL=len(issues), ISSUE_SAMPLE_LIMIT=sample_limit,
        ISSUE_SAMPLES_TRUNCATED=len(issues) > sample_limit,
        ISSUES=ordered[:sample_limit],
    )


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
                # Establish unambiguous model ownership before validating an
                # executable field. An incomplete row owned by another model is
                # out of scope here; unknown/conflicting ownership is not.
                if labelled and path_model and labelled != path_model:
                    classification, reason = "BLOCKED_ROWS", "MODEL_PATH_CONFLICT"
                elif label and not labelled and label not in {"extensionproperty", "extensionproperties"}:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_LABEL"
                elif path and path_model is None:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif path_model and path_model != model or not path and labelled and labelled != model:
                    classification = "EXCLUDED_ROWS"
                elif not field:
                    classification, reason = "BLOCKED_ROWS", "MISSING_SOURCE_FIELD"
                elif contract.get("SELECTED_FIELDS") and field not in contract["SELECTED_FIELDS"]:
                    classification = "EXCLUDED_ROWS"
                elif field in contract.get("EXCLUDED_FIELDS", ()):
                    classification, reason = "DEFERRED_ROWS", "DEFERRED_RELEASE_FIELD"
                elif contract.get("POLICY") == "metadata-v1" and not _metadata_rule_candidates(row, contract) and not row.get("APPROVAL_STATUS"):
                    classification = "DEFERRED_ROWS" if contract.get("UNREVIEWED_ROWS") == "DEFER" else "BLOCKED_ROWS"
                    reason = "MISSING_APPROVED_METADATA"
                elif not path:
                    classification, reason = "DEFERRED_ROWS", "MISSING_TARGET_PATH"
                elif path_model != model:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif _model_token(row.get("STATUS")) in {"deferred", "blocked", "tbd", "moreinformationneeded", "notmapped"} or _model_token(row.get("MAPPING_TYPE")) == "tbd":
                    classification, reason = "DEFERRED_ROWS", "UNAPPROVED_MAPPING"
                if classification:
                    report[classification] += 1
                    if reason:
                        report["ISSUES"].append({"row": index, "field": field, "reason": reason,
                                                 "severity": classification.removesuffix("_ROWS")})
                    continue
                canonical = dict(row)
                canonical_path = _apply_mapping_path_rules(canonical, contract, paths)
                owner = _owner_for_path(canonical_path, paths)
                if owner is None:
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field, "reason": "UNREGISTERED_PATH",
                                             "severity": "BLOCKED"})
                    continue
                relative = canonical_path[len(owner):].lstrip(".")
                if "[]" in relative:
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field, "reason": "UNREGISTERED_COLLECTION",
                                             "severity": "BLOCKED"})
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
            context = {"source_key": profile["SOURCE_KEY"], "config": cfg,
                             "mapping_rows": selected, "mappings_by_path": grouped,
                             "model_contract": contract, "registry_rows": model_registry,
                             "routing_report": report}
            if contract.get("POLICY") == "metadata-v1" and report["STATUS"] == "READY":
                try:
                    context["compiled_plan"] = compile_metadata_plan(context)
                    context["mapping_rows"] = context["compiled_plan"]["mappings"]
                    context["mappings_by_path"] = {}
                    for row in context["mapping_rows"]:
                        context["mappings_by_path"].setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
                except ValueError as error:
                    report["STATUS"] = "BLOCKED"
                    report["CONTRACT_ERROR"] = str(error)
                    report["ISSUES"].append({"row": None, "field": None,
                                             "reason": "METADATA_CONTRACT_ERROR",
                                             "severity": "BLOCKED",
                                             "affected_rows": report["SELECTED_ROWS"]})
                    report["BLOCKED_ROWS"] += report["SELECTED_ROWS"]
                    report["SELECTED_ROWS"] = 0
                    context["mapping_rows"] = []
                    context["mappings_by_path"] = {}
            _summarize_routing_issues(report)
            contexts.append(context)
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
