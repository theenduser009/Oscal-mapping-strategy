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



FLAT_MAPPING_COLUMNS = {
    "EXECUTION_STATUS", "RUNTIME_TARGET_PATH", "ALLOWED_VALUES", "VALUE_MAP",
    "OTHER_REMARKS_TEMPLATE", "ROLE_ID", "ROLE_TITLE", "REFERENCE_TYPE",
    "LOOKUP_KEY", "DESCRIPTION_REQUIRED", "VALUE_SOURCE", "VALUE_REQUIRED",
}


def _flat_mapping_status(row):
    if not any(row.get(key) not in (None, "") for key in FLAT_MAPPING_COLUMNS):
        return None
    status = row.get("EXECUTION_STATUS")
    if not isinstance(status, str) or status.upper() not in {
        "APPROVED", "BLOCKED_IF_POPULATED", "DEFERRED", "EXCLUDED",
    }:
        raise ValueError("Flat mapping requires an explicit valid EXECUTION_STATUS")
    return status.upper()


def _flat_text(row, key, required=False):
    value = row.get(key)
    if value in (None, "") and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + " must contain nonblank text")
    return value.strip()


def _flat_items(row, key):
    value = _flat_text(row, key)
    if value is None:
        return []
    items = [item.strip() for item in value.split("|")]
    if any(not item for item in items) or len(set(items)) != len(items):
        raise ValueError(key + " contains empty or duplicate entries")
    return items


def _compile_flat_mapping(row, elements):
    """Translate readable sheet columns to inert runtime parameters, never code."""
    status = _flat_mapping_status(row)
    if status not in {"APPROVED", "BLOCKED_IF_POPULATED"}:
        raise ValueError("Non-executable row cannot enter the compiled plan")
    transform = _flat_text(row, "TRANSFORM_ID", required=True)
    if transform not in METADATA_TRANSFORM_IDS:
        raise ValueError("Unknown reusable transform identifier")
    if status == "BLOCKED_IF_POPULATED" and transform != "reject-populated":
        raise ValueError("Populated-only guard requires reject-populated transform")
    rule_id = _flat_text(row, "RULE_ID", required=True)
    _flat_text(row, "RUNTIME_TARGET_PATH", required=True)
    owner = row["OWNER_ELEMENT_PATH"]
    if owner not in elements:
        raise ValueError("Mapping has no metadata-defined element operator")
    operator = elements[owner]["operator"]
    transform_params, representation_params = {}, {}
    allowed = {"VALUE_SOURCE", "VALUE_REQUIRED"}
    value_source = _flat_text(row, "VALUE_SOURCE") or "FIELD"
    if value_source not in {"FIELD", "CONFIG"}:
        raise ValueError("VALUE_SOURCE must be FIELD or CONFIG")
    if value_source == "CONFIG":
        if operator not in {"object", "record"} or not row.get("FIELD_RELATIVE_PATH"):
            raise ValueError("Config values require an explicit object member target")
        representation_params["value_source"] = "CONFIG"
    required = row.get("VALUE_REQUIRED")
    if required not in (None, ""):
        if type(required) is bool:
            representation_params["required"] = required
        elif isinstance(required, str) and required.lower() in {"true", "false"}:
            representation_params["required"] = required.lower() == "true"
        else:
            raise ValueError("VALUE_REQUIRED must be true or false")
    if transform == "security-objective":
        allowed.add("ALLOWED_VALUES")
        labels = _flat_items(row, "ALLOWED_VALUES")
        if labels:
            transform_params["approved_legacy_values"] = labels
    if transform == "status-crosswalk":
        allowed.update({"VALUE_MAP", "OTHER_REMARKS_TEMPLATE"})
        crosswalk = {}
        for entry in _flat_items(row, "VALUE_MAP"):
            if entry.count("=") != 1:
                raise ValueError("VALUE_MAP entries must be source=target")
            source, target = (token.strip() for token in entry.split("=", 1))
            # Match the runtime's stable-property-name normalization exactly.
            source = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
            if not source or not target or source in crosswalk:
                raise ValueError("VALUE_MAP contains empty or conflicting labels")
            crosswalk[source] = target
        if not crosswalk:
            raise ValueError("Crosswalk transform requires VALUE_MAP")
        transform_params["crosswalk"] = crosswalk
        template = _flat_text(row, "OTHER_REMARKS_TEMPLATE")
        if template is not None:
            if template.count("{label}") != 1 or any(
                    brace in template.replace("{label}", "") for brace in "{}"):
                raise ValueError("OTHER_REMARKS_TEMPLATE requires one {label} placeholder")
            prefix, suffix = template.split("{label}")
            transform_params.update(other_remarks_prefix=prefix, other_remarks_suffix=suffix)
        elif "other" in crosswalk.values():
            raise ValueError("Crosswalk other value requires an explanation template")
    if operator == "assignments":
        allowed.update({"ROLE_ID", "ROLE_TITLE"})
        representation_params.update(
            role_id=_flat_text(row, "ROLE_ID", required=True),
            role_title=_flat_text(row, "ROLE_TITLE", required=True),
        )
    if operator == "references":
        allowed.update({"REFERENCE_TYPE", "LOOKUP_KEY", "DESCRIPTION_REQUIRED"})
        representation_params["reference_type"] = _flat_text(row, "REFERENCE_TYPE", required=True)
        binding = _flat_text(row, "LOOKUP_KEY")
        if binding is not None:
            representation_params["hydrate_lookup"] = binding
        required = row.get("DESCRIPTION_REQUIRED")
        if required not in (None, ""):
            if binding is None:
                raise ValueError("DESCRIPTION_REQUIRED needs a LOOKUP_KEY")
            if type(required) is bool:
                flag = required
            elif isinstance(required, str) and required.lower() in {"true", "false"}:
                flag = required.lower() == "true"
            else:
                raise ValueError("DESCRIPTION_REQUIRED must be true or false")
            representation_params["description_required"] = flag
    parameters = FLAT_MAPPING_COLUMNS - {"EXECUTION_STATUS", "RUNTIME_TARGET_PATH"}
    if any(row.get(key) not in (None, "") for key in parameters - allowed):
        raise ValueError("Flat parameter does not apply to the chosen operation")
    target = row.get("FIELD_RELATIVE_PATH")
    if target:
        if operator not in {"object", "record", "values"}:
            raise ValueError("Member target is unsupported by the chosen element operator")
        representation_params["target"] = target
    for key, expected in (("TRANSFORM_PARAMS", transform_params),
                          ("REPRESENTATION_PARAMS", representation_params)):
        if row.get(key) not in (None, "") and _metadata_object(row[key], key) != expected:
            raise ValueError("Flat columns contradict " + key)
    if row.get("REPRESENTATION") not in (None, "", operator):
        raise ValueError("Mapping representation conflicts with its element operator")
    if row.get("APPROVAL_STATUS") not in (None, "", status):
        raise ValueError("EXECUTION_STATUS contradicts APPROVAL_STATUS")
    constraints = _compile_value_constraints(row.get("VALUE_CONSTRAINTS"))
    if transform == "skip" and (representation_params.get("required") or constraints.get("required") or
                                constraints.get("null_policy") == "reject" or
                                constraints.get("cardinality", {}).get("min", 0) > 0):
        raise ValueError("Skip transform conflicts with required-value constraints")
    result = copy.deepcopy(row)
    result.update(TRANSFORM_ID=transform, TRANSFORM_PARAMS=transform_params,
                  REPRESENTATION=operator, REPRESENTATION_PARAMS=representation_params,
                  VALUE_CONSTRAINTS=constraints, APPROVAL_STATUS=status,
                  RULE_ID=rule_id, CONTRACT_SOURCE="flat-mapping-artifact")
    return result


def _compile_metadata_mapping(row, elements):
    if _flat_mapping_status(row) is not None:
        return _compile_flat_mapping(row, elements)
    # Programmatic callers may supply already explicit executable metadata.
    # No source-name lookup, Notes matching or catalog approval fallback exists.
    if _model_token(row.get("APPROVAL_STATUS")) != "approved":
        raise ValueError("Executable mapping metadata requires explicit approval")
    transform = row.get("TRANSFORM_ID")
    if transform not in METADATA_TRANSFORM_IDS:
        raise ValueError("Unknown reusable transform identifier")
    constraints = _compile_value_constraints(row.get("VALUE_CONSTRAINTS"))
    if transform == "skip" and (constraints.get("required") or
                                constraints.get("null_policy") == "reject" or
                                constraints.get("cardinality", {}).get("min", 0) > 0):
        raise ValueError("Skip transform conflicts with required-value constraints")
    owner = row["OWNER_ELEMENT_PATH"]
    if owner not in elements:
        raise ValueError("Mapping has no metadata-defined element operator")
    operator = elements[owner]["operator"]
    if row.get("REPRESENTATION") not in (None, "", operator):
        raise ValueError("Mapping representation conflicts with its element operator")
    result = copy.deepcopy(row)
    result.update(
        TRANSFORM_ID=transform,
        TRANSFORM_PARAMS=_metadata_object(row.get("TRANSFORM_PARAMS"), "TRANSFORM_PARAMS"),
        REPRESENTATION=operator,
        REPRESENTATION_PARAMS=_metadata_object(row.get("REPRESENTATION_PARAMS"), "REPRESENTATION_PARAMS"),
        VALUE_CONSTRAINTS=constraints, APPROVAL_STATUS="APPROVED",
        RULE_ID=row.get("RULE_ID") or row.get("MAPPING_ID"),
        CONTRACT_SOURCE="mapping-artifact",
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
    mappings = [_compile_metadata_mapping(row, elements) for row in context["mapping_rows"]]
    counts = {}
    for row in mappings:
        if row.get("RULE_ID"):
            counts[row["RULE_ID"]] = counts.get(row["RULE_ID"], 0) + 1
    flat_ids = {row["RULE_ID"] for row in mappings if row.get("CONTRACT_SOURCE") == "flat-mapping-artifact"}
    if any(counts[rule_id] != 1 for rule_id in flat_ids):
        raise ValueError("Duplicate flat mapping RULE_ID within source/model")
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


def _registry_meta_text(row, key, required=False):
    value = row.get(key)
    if value is None or value == "":
        if required:
            raise ValueError("Registry metadata requires " + key)
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Registry metadata must be nonblank text: " + key)
    return value.strip()


def _registry_meta_enum(row, key, choices, required=False):
    value = _registry_meta_text(row, key, required)
    if value is not None and value not in choices:
        raise ValueError("Unknown registry policy: " + key)
    return value


def _registry_meta_bool(row, key):
    value = row.get(key)
    if type(value) is bool:
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    raise ValueError("Registry requires explicit boolean: " + key)


def _registry_meta_list(row, key):
    value = _registry_meta_text(row, key)
    if value is None:
        return []
    values = [part.strip() for part in value.split("|")]
    if any(not part for part in values) or len(values) != len(set(values)):
        raise ValueError("Registry list contains empty or duplicate values: " + key)
    return values


def _registry_operator(row):
    """Resolve a reusable collection shape from the original registry contract."""
    explicit = _registry_meta_enum(row, "OPERATOR", METADATA_OPERATORS)
    if explicit:
        return explicit
    if not _registry_meta_bool(row, "IS_COLLECTION"):
        return "object"
    rule = (_registry_meta_text(row, "INSTANCE_KEY_RULE", True) or "").upper()
    item_path = _registry_meta_text(row, "ITEM_PATH")
    if rule == "SOURCE_RECORD_ID" and item_path is None:
        return "record"
    if rule == "SOURCE_FIELD_NAME" and item_path is None:
        return "observations"
    if rule == "SOURCE_FIELD_NAME" and item_path == "$":
        return "roles"
    inferred = {
        ("SOURCE_FIELD_NAME+VALUE", "$"): "properties",
        ("VALUE", "$"): "values",
        ("CONTENT_ID", "$"): "references",
        ("ID", "UserList[]"): "parties",
        ("SOURCE_FIELD_NAME+ID", "UserList[]"): "assignments",
    }.get((rule, item_path))
    if inferred:
        return inferred
    raise ValueError("Collection requires an explicit reusable OPERATOR")


def _registry_model_rows(registry, model):
    rows = [row for row in registry if _metadata_active(row) and _registry_model(row) == model]
    paths = [_registry_path(row) for row in rows]
    if not paths or any(not path for path in paths) or len(paths) != len(set(paths)):
        raise ValueError("Enabled model requires unique active registry paths")
    by_path = dict(zip(paths, rows))
    roots = [path for path, row in by_path.items()
             if _registry_meta_text(row, "PARENT_NODE_PATH") is None]
    if len(roots) != 1 or "." in roots[0]:
        raise ValueError("Enabled model requires exactly one registry root")
    root = roots[0]
    for path, row in by_path.items():
        collection = _registry_meta_bool(row, "IS_COLLECTION")
        if collection != path.endswith("[]"):
            raise ValueError("Registry collection flag conflicts with path")
        parent = _registry_meta_text(row, "PARENT_NODE_PATH")
        if path == root:
            if parent is not None:
                raise ValueError("Registry root cannot have a parent")
        elif parent not in by_path or not path.startswith(parent + "."):
            raise ValueError("Registry child requires its active path ancestor")
    return by_path, root


def _executable_registry_paths(mapping_rows, source_profiles, model, registry_paths, root):
    owners = set()
    for profile in source_profiles:
        if model not in profile.get("MODEL_KEYS", ()):
            continue
        for original in mapping_rows.get(profile["SOURCE_KEY"], ()):
            row = _meta_row(original)
            try:
                status = _flat_mapping_status(row)
            except ValueError:
                continue  # The routing report retains the invalid row as blocked.
            executable = status in {"APPROVED", "BLOCKED_IF_POPULATED"}
            executable = executable or (status is None and
                                         _model_token(row.get("APPROVAL_STATUS")) == "approved")
            if not executable:
                continue
            declared_source = row.get("SOURCE_KEY")
            if declared_source and declared_source != profile["SOURCE_KEY"]:
                continue
            path = str((row.get("RUNTIME_TARGET_PATH") if status else
                        row.get("OSCAL_ELEMENT_PATH")) or "").strip()
            if not (path == root or path.startswith(root + ".")):
                continue
            owner = _owner_for_path(path, registry_paths)
            if owner:
                owners.add(owner)
    return owners


def _with_registry_ancestors(paths, by_path):
    result = set(paths)
    for path in tuple(paths):
        current = path
        while current is not None:
            result.add(current)
            current = _registry_meta_text(by_path[current], "PARENT_NODE_PATH")
    return result


def _decode_registry_element(row, root, by_path):
    path = _registry_path(row)
    operator = _registry_operator(row)
    collection = _registry_meta_bool(row, "IS_COLLECTION")
    parent = _registry_meta_text(row, "PARENT_NODE_PATH")
    # INSTANCE_KEY_RULE and ITEM_PATH describe collection instances. Some
    # established scalar registry rows retain legacy values in those columns;
    # they do not change scalar identity and must not make a valid path fail.
    key_rule = _registry_meta_text(row, "INSTANCE_KEY_RULE") if collection else None
    item_path = _registry_meta_text(row, "ITEM_PATH") if collection else None
    if operator != "object" and not collection:
        raise ValueError("Registry operator requires a collection")
    identities = {"record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",
                  "properties": "SOURCE_FIELD_NAME+VALUE", "values": "VALUE",
                  "references": "CONTENT_ID", "roles": "SOURCE_FIELD_NAME",
                  "parties": "ID", "assignments": "SOURCE_FIELD_NAME+ID"}
    if operator in identities and key_rule != identities[operator]:
        raise ValueError("Registry instance rule conflicts with operator")
    if operator in {"record", "observations"} and item_path is not None:
        raise ValueError("Record/observation operator requires null item path")
    if operator in {"properties", "values", "references", "roles"} and item_path != "$":
        raise ValueError("Registry operator requires root item path")
    if operator in {"parties", "assignments"} and item_path != "UserList[]":
        raise ValueError("Linked identity operator requires reviewed user-list item path")
    if operator == "object" and collection and (key_rule, item_path) != ("VALUE", "$"):
        raise ValueError("Object-list operator requires VALUE identity at the root item path")
    registry_contract = {"parent_path": parent, "is_collection": collection}
    if collection:
        registry_contract.update(instance_key_rule=key_rule, item_path=item_path)
    parameters = {"registry_contract": registry_contract}
    if parent:
        parent_operator = _registry_operator(by_path[parent])
        if _registry_meta_bool(by_path[parent], "IS_COLLECTION"):
            if parent_operator != "record":
                raise ValueError("Nested collection needs a supported parent identity")
            parameters["parent_instance_rule"] = "source-record"
        elif operator == "record":
            parameters["parent_instance_rule"] = "singleton"
    # UUID injection is opt-in. The original registry remains sufficient for
    # ordinary scalar mapping; use the sparse policy only when payload
    # compatibility requires a UUID.
    uuid_policy = _registry_meta_enum(
        row, "UUID_POLICY", {"omit", "node", "instance"},
        required=_registry_meta_text(row, "OPERATOR") is not None) or "omit"
    if operator == "parties" and uuid_policy != "instance":
        raise ValueError("Party identity requires the instance UUID policy")
    if uuid_policy == "instance" and operator != "parties":
        raise ValueError("Instance UUID policy is supported only for parties")
    if uuid_policy != "omit":
        parameters["include_uuid"] = True
    if uuid_policy == "instance":
        if not collection:
            raise ValueError("Instance UUID policy requires a collection")
        parameters["uuid_from_instance"] = True
    members = _registry_meta_list(row, "REQUIRED_MEMBERS")
    if members:
        if operator != "object" or collection or any(
                any(not token or "[" in token or "]" in token for token in member.split("."))
                for member in members):
            raise ValueError("Required members need a scalar object assembly")
        parameters.update(required_members=members, optional_assembly=True)
    elif operator == "object" and not collection:
        parameters["materialize_empty"] = True
    if collection and operator == "object":
        parameters.update(allow_list_instances=True, list_identity="source-field-index")
    if operator in {"properties", "observations"}:
        parameters["property_name_rule"] = "source-field-slug"
    return {"operator": operator, "parameters": parameters}


def decode_registry_model_contracts(registry_rows, source_profiles, model_contracts,
                                    mapping_rows=None):
    """Compile CSV mappings with the original registry plus three sparse rules."""
    result = copy.deepcopy(model_contracts)
    enabled = {model for profile in source_profiles for model in profile.get("MODEL_KEYS", ())}
    registry = [_meta_row(row) for row in registry_rows]
    mapping_rows = mapping_rows or {}
    forbidden = {"ROOT_PATH", "ELEMENT_PATHS", "REFERENCE_GROUPS", "DEFAULT_ELEMENT",
                 "REQUIRED_RULE_IDS", "MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS"}
    for model in sorted(enabled):
        if model not in result:
            raise ValueError("Source route names an unconfigured model")
        contract = result[model]
        # Explicit in-memory contracts remain a test/programmatic API; deployed
        # contracts have no structural definitions and use the live registry.
        if isinstance(contract.get("ELEMENTS"), dict) and contract.get("ROOT_PATH"):
            continue
        if forbidden & contract.keys() or contract.get("MODEL_KEY") != model or \
                contract.get("POLICY") != "metadata-v1":
            raise ValueError("Lean registry model identity is invalid")
        by_path, root = _registry_model_rows(registry, model)
        mapped = _executable_registry_paths(mapping_rows, source_profiles, model,
                                             tuple(by_path), root)
        explicit = {path for path, row in by_path.items()
                    if _registry_meta_text(row, "OPERATOR") is not None}
        included = mapped | explicit | {root}

        # Assignment mappings materialize the registered role and party
        # siblings even though those nodes are not direct CSV payload owners.
        for path in tuple(included):
            if _registry_operator(by_path[path]) != "assignments":
                continue
            parent = _registry_meta_text(by_path[path], "PARENT_NODE_PATH")
            siblings = []
            for candidate, row in by_path.items():
                if _registry_meta_text(row, "PARENT_NODE_PATH") != parent:
                    continue
                try:
                    sibling_operator = _registry_operator(row)
                except ValueError:
                    if _registry_meta_text(row, "OPERATOR") is not None:
                        raise
                    continue
                if sibling_operator in {"roles", "parties"}:
                    siblings.append((candidate, sibling_operator))
            roles = [candidate for candidate, operator in siblings if operator == "roles"]
            parties = [candidate for candidate, operator in siblings if operator == "parties"]
            if len(roles) != 1 or len(parties) != 1:
                raise ValueError("Assignment mapping requires one role and one party registry sibling")
            included.update((roles[0], parties[0]))
        included = _with_registry_ancestors(included, by_path)

        elements = {path: _decode_registry_element(by_path[path], root, by_path)
                    for path in sorted(included)}
        if elements[root]["operator"] != "object":
            raise ValueError("Registry root requires an object operator")

        groups, linked = [], set()
        namespaces = {
            (profile["SOURCE_SYSTEM_NAME"], profile["SOURCE_TABLE_NAME"])
            for profile in source_profiles if model in profile.get("MODEL_KEYS", ())
        }
        for path in sorted(included):
            if elements[path]["operator"] != "assignments":
                continue
            parent = _registry_meta_text(by_path[path], "PARENT_NODE_PATH")
            roles = [candidate for candidate in included
                     if _registry_meta_text(by_path[candidate], "PARENT_NODE_PATH") == parent
                     and elements[candidate]["operator"] == "roles"]
            parties = [candidate for candidate in included
                       if _registry_meta_text(by_path[candidate], "PARENT_NODE_PATH") == parent
                       and elements[candidate]["operator"] == "parties"]
            if len(roles) != 1 or len(parties) != 1:
                raise ValueError("Assignment mapping requires one role and one party registry sibling")
            group_paths = {path, roles[0], parties[0]}
            if len(group_paths) != 3 or group_paths & linked:
                raise ValueError("Reference family registry paths must be distinct")
            group = {"roles_path": roles[0], "parties_path": parties[0],
                     "assignments_path": path, "party_type": "person"}
            if len(namespaces) != 1:
                raise ValueError("Reference family requires one source namespace")
            source_system, source_table = next(iter(namespaces))
            group.update(
                party_uuid_parts=["$source_system", "$source_record", "party",
                                  "$reference_id"],
                source_namespace={"SOURCE_SYSTEM_NAME": source_system,
                                  "SOURCE_TABLE_NAME": source_table,
                                  "MODEL_KEY": model},
            )
            groups.append(group)
            linked.update(group_paths)
        if any(spec["operator"] in {"roles", "parties"} and path not in linked
               for path, spec in elements.items()):
            raise ValueError("Linked identity operator lacks an assignment family")

        report = _metadata_object(contract.get("REPORT"), "REPORT")
        if "TARGET_PATH" in report:
            raise ValueError("Report target is derived from executable mappings")
        observation_paths = [path for path, spec in elements.items()
                             if spec["operator"] == "observations"]
        if report:
            if len(observation_paths) != 1:
                raise ValueError("Report metadata requires one observation registry path")
            report["TARGET_PATH"] = observation_paths[0]
        contract.update(ROOT_PATH=root, ELEMENTS=elements,
                        ELEMENT_PATHS=tuple(sorted(included)), DEFAULT_ELEMENT=None,
                        REFERENCE_GROUPS=groups, REPORT=report)
    return result


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
            if {"MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS"} & contract.keys():
                raise ValueError("Field rules belong in the mapping artifact, not model settings")
            if contract.get("MODEL_KEY") != model or not contract.get("ROOT_PATH"):
                raise ValueError("Model contract identity is invalid")
        if key not in mapping_rows or not isinstance(mapping_rows[key], list):
            raise ValueError("Missing source mapping input")
    if set(mapping_rows) != keys:
        raise ValueError("Unknown source mapping input key")


def _owner_for_path(path, paths):
    candidates = [p for p in paths if path == p or path.startswith(p + ".")]
    return max(candidates, key=lambda p: (p.count("."), len(p))) if candidates else None



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


def compile_mapping_contexts(mapping_rows, registry_rows, source_profiles, model_contracts,
                             routing_metadata=None):
    """Pure source/model routing. No data reads, globals mutation or writes."""
    model_contracts = decode_registry_model_contracts(
        registry_rows, source_profiles, model_contracts, mapping_rows)
    _validate_source_profiles(source_profiles, model_contracts, mapping_rows)
    routing = _metadata_object(routing_metadata, "ROUTING")
    if set(routing) - {"DEFERRED_MODEL_LABELS", "DEFERRED_TARGET_PATHS"}:
        raise ValueError("Unknown routing metadata option")
    for values in routing.values():
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
            raise ValueError("Routing placeholders must be lists of nonblank text")
    deferred_labels = {_model_token(v) for v in routing.get("DEFERRED_MODEL_LABELS", ())}
    if "" in deferred_labels:
        raise ValueError("Deferred model labels must contain an alphanumeric token")
    deferred_paths = {v.strip() for v in routing.get("DEFERRED_TARGET_PATHS", ())}
    aliases = _model_aliases(model_contracts)
    registry = [_meta_row(row) for row in registry_rows]
    active = [row for row in registry if _metadata_active(row)]
    root_models = {}
    for row in active:
        path, model = _registry_path(row), _registry_model(row)
        # Every active registry path identifies its model, not just root rows.
        # Recognizing ownership does not configure or enable an executor.
        if path and model:
            root = path.split(".", 1)[0]
            if root in root_models and root_models[root] != model:
                raise ValueError("Registry root belongs to multiple models")
            root_models[root] = model
            for label in (model, root, row.get("OSCAL_MODEL"), row.get("MODEL_NAME")):
                token = _model_token(label)
                if not token:
                    continue
                if token in aliases and aliases[token] != model:
                    raise ValueError("Registry label conflicts with configured model ownership")
                aliases[token] = model
    for model, contract in model_contracts.items():
        root = contract.get("ROOT_PATH")
        if not root:
            continue  # Unselected strict models have not loaded registry metadata.
        if root in root_models and root_models[root] != model:
            raise ValueError("Configured root conflicts with registry model")
        root_models[root] = model
    if deferred_labels & set(aliases) or deferred_paths & {_registry_path(row) for row in active}:
        raise ValueError("Deferred placeholder conflicts with a registered model or path")
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
            # Retain known non-executable boundaries before resolving payload owners.
            # Otherwise a disabled singleton silently becomes a member of its parent.
            unavailable_paths = {_registry_path(row) for row in registry
                                 if _registry_model(row) == model and _registry_path(row)} - set(paths)
            report = {"STATUS": "READY", "INPUT_ROWS": len(rows), "SELECTED_ROWS": 0,
                      "EXCLUDED_ROWS": 0, "DEFERRED_ROWS": 0, "BLOCKED_ROWS": 0,
                      "ROUTING_POLICY": "registry-first-v1", "ISSUES": []}
            selected = []
            for index, row in enumerate(rows):
                field = row.get("SOURCE_FIELD_NAME")
                original_path = str(row.get("OSCAL_ELEMENT_PATH") or "")
                classification, reason, flat_status = None, None, None
                try:
                    flat_status = _flat_mapping_status(row)
                except ValueError:
                    classification, reason = "BLOCKED_ROWS", "INVALID_EXECUTION_STATUS"
                path = (str(row.get("RUNTIME_TARGET_PATH") or "")
                        if flat_status in {"APPROVED", "BLOCKED_IF_POPULATED"} else original_path)
                label = _model_token(row.get("OSCAL_MODEL"))
                labelled = aliases.get(label)
                path_model = root_models.get(path.split(".", 1)[0])
                original_model = root_models.get(original_path.split(".", 1)[0])
                source_key = row.get("SOURCE_KEY")
                # The original row remains provenance. Explicit runtime paths
                # choose representation, but cannot silently move across models.
                if classification:
                    pass
                elif source_key and source_key not in mapping_rows:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_SOURCE_KEY"
                elif source_key and source_key != profile["SOURCE_KEY"]:
                    classification, reason = "EXCLUDED_ROWS", "OTHER_SOURCE"
                elif flat_status is not None and not source_key:
                    classification, reason = "BLOCKED_ROWS", "MISSING_SOURCE_KEY"
                elif flat_status in {"DEFERRED", "EXCLUDED"}:
                    classification = flat_status + "_ROWS"
                    reason = "EXPLICIT_" + flat_status
                elif labelled and path_model and labelled != path_model or (
                        flat_status and original_model and path_model and original_model != path_model):
                    classification, reason = "BLOCKED_ROWS", "MODEL_PATH_CONFLICT"
                elif flat_status is None and (label in deferred_labels or path in deferred_paths):
                    classification, reason = "DEFERRED_ROWS", "PLACEHOLDER_MAPPING"
                elif path_model and path_model != model or not path and labelled and labelled != model:
                    classification = "EXCLUDED_ROWS"
                elif flat_status is None and not row.get("APPROVAL_STATUS") and any(
                        row.get(key) not in (None, "") for key in (
                            "TRANSFORM_ID", "TRANSFORM_PARAMS", "REPRESENTATION",
                            "REPRESENTATION_PARAMS", "VALUE_CONSTRAINTS")):
                    classification, reason = "BLOCKED_ROWS", "UNAPPROVED_EXECUTABLE_METADATA"
                elif flat_status is None and contract.get("POLICY") == "metadata-v1" and not row.get("APPROVAL_STATUS"):
                    classification = "DEFERRED_ROWS" if contract.get("UNREVIEWED_ROWS") == "DEFER" else "BLOCKED_ROWS"
                    reason = "MISSING_APPROVED_METADATA"
                elif flat_status is None and (_model_token(row.get("STATUS")) in {"deferred", "blocked", "tbd", "moreinformationneeded", "notmapped"} or _model_token(row.get("MAPPING_TYPE")) == "tbd"):
                    classification, reason = "DEFERRED_ROWS", "UNAPPROVED_MAPPING"
                elif path and path_model is None:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif not field:
                    classification, reason = "BLOCKED_ROWS", "MISSING_SOURCE_FIELD"
                elif contract.get("SELECTED_FIELDS") and field not in contract["SELECTED_FIELDS"]:
                    classification = "EXCLUDED_ROWS"
                elif not path:
                    classification = "BLOCKED_ROWS" if flat_status else "DEFERRED_ROWS"
                    reason = "MISSING_TARGET_PATH"
                elif path_model != model:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                if classification:
                    report[classification] += 1
                    if reason:
                        report["ISSUES"].append({"row": index, "field": field, "reason": reason,
                                                 "severity": classification.removesuffix("_ROWS"),
                                                 "model_label": row.get("OSCAL_MODEL"),
                                                 "target_path": path, "resolved_model": path_model})
                    continue
                canonical = dict(row)
                canonical_path = path
                if any(path == boundary or path.startswith(boundary + ".")
                       for boundary in unavailable_paths):
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field,
                                             "reason": "REGISTRY_PATH_NOT_EXECUTABLE",
                                             "severity": "BLOCKED"})
                    continue
                owner = _owner_for_path(canonical_path, paths)
                if owner is None:
                    report["BLOCKED_ROWS"] += 1
                    report["ISSUES"].append({"row": index, "field": field, "reason": "UNREGISTERED_PATH",
                                             "severity": "BLOCKED"})
                    continue
                relative = canonical_path[len(owner):].lstrip(".")
                if "[]" in relative or flat_status and any(token in relative for token in ("[", "]", "..")):
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
            selected.sort(key=lambda row: (row["OWNER_ELEMENT_PATH"], row["CANONICAL_ELEMENT_PATH"], row["SOURCE_FIELD_NAME"]))
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
    MAPPING_INPUTS, REGISTRY_INPUT_ROWS, SOURCE_PROFILES, MODEL_CONTRACTS,
    routing_metadata=ROUTING_METADATA,
)
# Legacy SSP aliases are observational only; the active runner uses contexts.
_default_context = next((context for context in MAPPING_CONTEXTS
                         if context["config"]["OSCAL_MODEL"] == CONFIG["OSCAL_MODEL"]),
                        MAPPING_CONTEXTS[0])
CANONICAL_MAPPING_ROWS = _default_context["mapping_rows"]
MAPPINGS_BY_ELEMENT_PATH = _default_context["mappings_by_path"]
canonical_mapping_pdf = pd.DataFrame(CANONICAL_MAPPING_ROWS)
# The engine consumes compiled Python contexts, not a Snowpark mapping frame.
# Keep the inspection view local; uploading nested metadata adds no runtime value.
canonical_mapping_df = None
active_registry_paths = [_registry_path(row) for row in _default_context["registry_rows"]]
print("Mapping routes:", [
    {"source": context["source_key"], "model": context["config"]["OSCAL_MODEL"],
     **context["routing_report"]} for context in MAPPING_CONTEXTS
])
