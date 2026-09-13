# %% Cell 3 - Canonical mapping contract

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
import pickle
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
METADATA_INSTANCE_RULES = {
    "record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",
    "properties": "SOURCE_FIELD_NAME+VALUE", "values": "VALUE",
    "references": "CONTENT_ID", "roles": "SOURCE_FIELD_NAME",
    "parties": "ID", "assignments": "SOURCE_FIELD_NAME+ID",
}
METADATA_ITEM_PATHS = {
    "record": None, "observations": None,
    "properties": "$", "values": "$", "references": "$", "roles": "$",
    "parties": "UserList[]", "assignments": "UserList[]",
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


def _metadata_column_text(row, key, required=False):
    value = row.get(key)
    if value in (None, "") and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + " must contain nonblank text")
    return value.strip()


def _metadata_items(row, key):
    value = _metadata_column_text(row, key)
    if value is None:
        return []
    items = [item.strip() for item in value.split("|")]
    if any(not item for item in items) or len(set(items)) != len(items):
        raise ValueError(key + " contains empty or duplicate entries")
    return items


def _metadata_bool(value, label):
    if type(value) is bool:
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(label + " must be true or false")


def _compile_flat_mapping(row, elements):
    """Translate readable sheet columns to inert runtime parameters, never code."""
    status = _flat_mapping_status(row)
    if status not in {"APPROVED", "BLOCKED_IF_POPULATED"}:
        raise ValueError("Non-executable row cannot enter the compiled plan")
    transform = _metadata_column_text(row, "TRANSFORM_ID", required=True)
    if transform not in METADATA_TRANSFORM_IDS:
        raise ValueError("Unknown reusable transform identifier")
    if status == "BLOCKED_IF_POPULATED" and transform != "reject-populated":
        raise ValueError("Populated-only guard requires reject-populated transform")
    rule_id = _metadata_column_text(row, "RULE_ID", required=True)
    _metadata_column_text(row, "RUNTIME_TARGET_PATH", required=True)
    owner = row["OWNER_ELEMENT_PATH"]
    if owner not in elements:
        raise ValueError("Mapping has no metadata-defined element operator")
    operator = elements[owner]["operator"]
    transform_params, representation_params = {}, {}
    allowed = {"VALUE_SOURCE", "VALUE_REQUIRED"}
    value_source = _metadata_column_text(row, "VALUE_SOURCE") or "FIELD"
    if value_source not in {"FIELD", "CONFIG"}:
        raise ValueError("VALUE_SOURCE must be FIELD or CONFIG")
    if value_source == "CONFIG":
        if operator not in {"object", "record"} or not row.get("FIELD_RELATIVE_PATH"):
            raise ValueError("Config values require an explicit object member target")
        representation_params["value_source"] = "CONFIG"
    required = row.get("VALUE_REQUIRED")
    if required not in (None, ""):
        representation_params["required"] = _metadata_bool(required, "VALUE_REQUIRED")
    if transform == "security-objective":
        allowed.add("ALLOWED_VALUES")
        labels = _metadata_items(row, "ALLOWED_VALUES")
        if labels:
            transform_params["approved_legacy_values"] = labels
    if transform == "status-crosswalk":
        allowed.update({"VALUE_MAP", "OTHER_REMARKS_TEMPLATE"})
        crosswalk = {}
        for entry in _metadata_items(row, "VALUE_MAP"):
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
        template = _metadata_column_text(row, "OTHER_REMARKS_TEMPLATE")
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
            role_id=_metadata_column_text(row, "ROLE_ID", required=True),
            role_title=_metadata_column_text(row, "ROLE_TITLE", required=True),
        )
    if operator == "references":
        allowed.update({"REFERENCE_TYPE", "LOOKUP_KEY", "DESCRIPTION_REQUIRED"})
        representation_params["reference_type"] = _metadata_column_text(row, "REFERENCE_TYPE", required=True)
        binding = _metadata_column_text(row, "LOOKUP_KEY")
        if binding is not None:
            representation_params["hydrate_lookup"] = binding
        required = row.get("DESCRIPTION_REQUIRED")
        if required not in (None, ""):
            if binding is None:
                raise ValueError("DESCRIPTION_REQUIRED needs a LOOKUP_KEY")
            representation_params["description_required"] = _metadata_bool(required, "DESCRIPTION_REQUIRED")
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


def _metadata_params(row):
    params = row.get("REPRESENTATION_PARAMS") or {}
    if not isinstance(params, dict):
        raise ValueError("Representation parameters must be an object")
    return params


def _metadata_target(row):
    params = _metadata_params(row)
    return params.get("target") or row.get("FIELD_RELATIVE_PATH") or row.get("OSCAL_FIELD_NAME")


def _metadata_plan_snapshot(plan):
    # Compare exact types, including tuple/list and bool/int; never deserialize.
    try:
        return b"csv-registry-v2\0" + pickle.dumps(plan, protocol=4)
    except (TypeError, AttributeError, pickle.PickleError):
        return None  # Uncacheable provenance still uses the full validator.


def _validate_compiled_metadata(plan, root_path, constraints_compiled=False):
    """One contract for compiler output and independently supplied runtime plans."""
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("A compiled metadata plan is required")
    if not isinstance(plan.get("elements"), dict) or not isinstance(plan.get("mappings"), list):
        raise ValueError("Compiled metadata element and mapping plans are required")
    if root_path not in plan["elements"]:
        raise ValueError("Compiled plan must describe the configured root")
    if plan.get("default_element") is not None:
        raise ValueError("Retired runtime metadata; use maintained CSV and registry columns")
    for specification in plan["elements"].values():
        if not isinstance(specification, dict) or specification.get("operator") not in METADATA_OPERATORS:
            raise ValueError("Unsupported reviewed element representation")
        if not isinstance(specification.get("parameters", {}), dict):
            raise ValueError("Element parameters must be an object")
        if {"controlled_fields", "type_member", "forbidden_members", "nonblank_text_members"} & specification.get("parameters", {}).keys():
            raise ValueError("Retired runtime metadata; use maintained CSV and registry columns")
    for group in plan.get("reference_groups", ()):
        namespace = group.get("source_namespace")
        if ("party_uuid_parts" in group or not isinstance(namespace, dict)
                or set(namespace) != {"SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "MODEL_KEY"}
                or any(not isinstance(value, str) or not value.strip() for value in namespace.values())):
            raise ValueError("Retired runtime metadata; use maintained CSV and registry columns")
    seen = set()
    for row in plan["mappings"]:
        if row.get("TRANSFORM_ID") not in METADATA_TRANSFORM_IDS:
            raise ValueError("Unknown metadata transformation")
        approval = str(row.get("APPROVAL_STATUS") or "").lower().replace("_", "-")
        if approval not in {"approved", "accepted", "runtime-accepted", "runtime-accepted-in-memory"} and not (
                approval == "blocked-if-populated" and row["TRANSFORM_ID"] == "reject-populated"):
            raise ValueError("Unapproved mapping cannot enter runtime plan")
        _metadata_column_text(row, "SOURCE_FIELD_NAME", required=True)
        _metadata_column_text(row, "OWNER_ELEMENT_PATH", required=True)
        path = row["OWNER_ELEMENT_PATH"]
        if path not in plan["elements"]:
            raise ValueError("Mapped element lacks a reviewed representation")
        if str(row.get("REPRESENTATION") or "").lower() not in {
                "", "scalar", plan["elements"][path]["operator"]}:
            raise ValueError("Unknown metadata mapping representation")
        if not isinstance(row.get("TRANSFORM_PARAMS", {}), dict):
            raise ValueError("Transform parameters must be an object")
        if ({"target_member", "other_value", "remarks_member", "default_members", "required"} & row.get("TRANSFORM_PARAMS", {}).keys()
                or {"namespace", "property_name"} & _metadata_params(row).keys()):
            raise ValueError("Retired runtime metadata; use maintained CSV and registry columns")
        if not isinstance(row.get("VALUE_CONSTRAINTS", {}), dict):
            raise ValueError("Compiled value constraints must be an object")
        if not constraints_compiled:
            _compile_value_constraints(row.get("VALUE_CONSTRAINTS"))
        identity = (path, row["SOURCE_FIELD_NAME"], str(_metadata_target(row) or ""))
        if identity in seen:
            raise ValueError("Duplicate compiled mapping row")
        seen.add(identity)


def compile_metadata_plan(context):
    """Combine the registry's decoded operators with approved flat CSV mappings."""
    contract = context["model_contract"]
    elements = copy.deepcopy(contract["ELEMENTS"])
    mappings = [_compile_flat_mapping(row, elements) for row in context["mapping_rows"]]
    rule_ids = [row["RULE_ID"] for row in mappings]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError("Duplicate flat mapping RULE_ID within source/model")
    plan = {"version": 1, "elements": elements, "mappings": mappings,
            "reference_groups": copy.deepcopy(contract["REFERENCE_GROUPS"]),
            "options": copy.deepcopy(contract.get("RUNTIME_OPTIONS", {})),
            "report": copy.deepcopy(contract.get("REPORT", {})),
            "default_element": None}
    _validate_compiled_metadata(plan, contract["ROOT_PATH"], constraints_compiled=True)
    context["_compiled_plan_snapshot"] = _metadata_plan_snapshot(plan)
    return plan


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


def _registry_meta_enum(row, key, choices, required=False):
    value = _metadata_column_text(row, key, required)
    if value is not None and value not in choices:
        raise ValueError("Unknown registry policy: " + key)
    return value


def _registry_meta_bool(row, key):
    value = row.get(key)
    return _metadata_bool(value.strip() if isinstance(value, str) else value, "Registry " + key)


def _registry_operator(row):
    """Resolve a reusable collection shape from the original registry contract."""
    explicit = _registry_meta_enum(row, "OPERATOR", METADATA_OPERATORS)
    if explicit:
        return explicit
    if not _registry_meta_bool(row, "IS_COLLECTION"):
        return "object"
    rule = _metadata_column_text(row, "INSTANCE_KEY_RULE", True).upper()
    item_path = _metadata_column_text(row, "ITEM_PATH")
    for operator, identity in METADATA_INSTANCE_RULES.items():
        if rule == identity and item_path == METADATA_ITEM_PATHS[operator]:
            return operator
    raise ValueError("Collection requires an explicit reusable OPERATOR")


def _registry_model_rows(registry, model):
    rows = [row for row in registry if _metadata_active(row) and _registry_model(row) == model]
    paths = [_registry_path(row) for row in rows]
    if not paths or any(not path for path in paths) or len(paths) != len(set(paths)):
        raise ValueError("Enabled model requires unique active registry paths")
    by_path = dict(zip(paths, rows))
    parents = {path: _metadata_column_text(row, "PARENT_NODE_PATH") for path, row in by_path.items()}
    roots = [path for path, parent in parents.items() if parent is None]
    if len(roots) != 1 or "." in roots[0]:
        raise ValueError("Enabled model requires exactly one registry root")
    root = roots[0]
    for path, row in by_path.items():
        collection = _registry_meta_bool(row, "IS_COLLECTION")
        if collection != path.endswith("[]"):
            raise ValueError("Registry collection flag conflicts with path")
        parent = parents[path]
        if path != root and (parent not in by_path or not path.startswith(parent + ".")):
            raise ValueError("Registry child requires its active path ancestor")
    return by_path, root


def _executable_registry_paths(mapping_rows, source_profiles, model, registry_paths, root):
    owners = set()
    for profile in source_profiles:
        if model not in profile.get("MODEL_KEYS", ()):
            continue
        for row in mapping_rows.get(profile["SOURCE_KEY"], ()):
            try:
                status = _flat_mapping_status(row)
            except ValueError:
                continue  # The routing report retains the invalid row as blocked.
            if status not in {"APPROVED", "BLOCKED_IF_POPULATED"}:
                continue
            declared_source = row.get("SOURCE_KEY")
            if declared_source and declared_source != profile["SOURCE_KEY"]:
                continue
            path = str(row.get("RUNTIME_TARGET_PATH") or "").strip()
            if not (path == root or path.startswith(root + ".")):
                continue
            owner = _owner_for_path(path, registry_paths)
            if owner:
                owners.add(owner)
    return owners


def _decode_registry_element(row, by_path):
    operator = _registry_operator(row)
    collection = _registry_meta_bool(row, "IS_COLLECTION")
    parent = _metadata_column_text(row, "PARENT_NODE_PATH")
    # INSTANCE_KEY_RULE and ITEM_PATH describe collection instances.  Some
    # established scalar registry rows retain legacy values in those columns;
    # they do not change scalar identity and must not make a valid path fail.
    key_rule = _metadata_column_text(row, "INSTANCE_KEY_RULE") if collection else None
    item_path = _metadata_column_text(row, "ITEM_PATH") if collection else None
    if operator != "object" and not collection:
        raise ValueError("Registry operator requires a collection")
    if operator in METADATA_INSTANCE_RULES and key_rule != METADATA_INSTANCE_RULES[operator]:
        raise ValueError("Registry instance rule conflicts with operator")
    if operator in METADATA_ITEM_PATHS and item_path != METADATA_ITEM_PATHS[operator]:
        raise ValueError("Registry item path conflicts with operator: " + operator)
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
        required=_metadata_column_text(row, "OPERATOR") is not None) or "omit"
    if operator == "parties" and uuid_policy != "instance":
        raise ValueError("Party identity requires the instance UUID policy")
    if uuid_policy == "instance" and operator != "parties":
        raise ValueError("Instance UUID policy is supported only for parties")
    if uuid_policy != "omit":
        parameters["include_uuid"] = True
        if uuid_policy == "instance":
            parameters["uuid_from_instance"] = True
    members = _metadata_items(row, "REQUIRED_MEMBERS")
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
    registry = [_meta_row(row) for row in registry_rows]
    mappings = {key: [_meta_row(row) for row in rows]
                for key, rows in (mapping_rows or {}).items()}
    return _decode_registry_model_contracts(
        registry, source_profiles, model_contracts, mappings)


def _decode_registry_model_contracts(registry, source_profiles, model_contracts,
                                     mapping_rows):
    """Resolve model contracts from already normalized metadata rows."""
    result = copy.deepcopy(model_contracts)
    enabled = {model for profile in source_profiles for model in profile.get("MODEL_KEYS", ())}
    forbidden = {"ROOT_PATH", "ELEMENTS", "ELEMENT_PATHS", "REFERENCE_GROUPS", "DEFAULT_ELEMENT",
                 "REQUIRED_RULE_IDS", "MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS", "SELECTED_FIELDS"}
    for model in sorted(enabled):
        if model not in result:
            raise ValueError("Source route names an unconfigured model")
        contract = result[model]
        if {"MAPPING_RULES", "PATH_RULES", "EXCLUDED_FIELDS", "SELECTED_FIELDS"} & contract.keys():
            raise ValueError("Field rules belong in the mapping artifact, not model settings")
        if forbidden & contract.keys() or contract.get("MODEL_KEY") != model or \
                contract.get("POLICY") != "metadata-v1":
            raise ValueError("Lean registry model identity is invalid")
        by_path, root = _registry_model_rows(registry, model)
        mapped = _executable_registry_paths(mapping_rows, source_profiles, model,
                                             tuple(by_path), root)
        explicit = {path for path, row in by_path.items()
                    if _metadata_column_text(row, "OPERATOR") is not None}
        included = mapped | explicit | {root}

        # Resolve each assignment family once and add its role/party siblings.
        groups, linked = [], set()
        for path in sorted(included):
            if _registry_operator(by_path[path]) != "assignments":
                continue
            parent = _metadata_column_text(by_path[path], "PARENT_NODE_PATH")
            siblings = {"roles": [], "parties": []}
            for candidate, row in by_path.items():
                if _metadata_column_text(row, "PARENT_NODE_PATH") != parent:
                    continue
                try:
                    operator = _registry_operator(row)
                except ValueError:
                    if _metadata_column_text(row, "OPERATOR") is not None:
                        raise
                    continue
                if operator in siblings:
                    siblings[operator].append(candidate)
            if any(len(paths) != 1 for paths in siblings.values()):
                raise ValueError("Assignment mapping requires one role and one party registry sibling")
            roles_path, parties_path = siblings["roles"][0], siblings["parties"][0]
            group_paths = {path, roles_path, parties_path}
            if group_paths & linked:
                raise ValueError("Reference family registry paths must be distinct")
            groups.append({
                "roles_path": roles_path, "parties_path": parties_path,
                "assignments_path": path, "party_type": "person",
            })
            linked.update(group_paths)
        included.update(linked)
        # Ancestors already visited through another mapped path need no repeat walk.
        for path in tuple(included):
            parent = _metadata_column_text(by_path[path], "PARENT_NODE_PATH")
            while parent is not None and parent not in included:
                included.add(parent)
                parent = _metadata_column_text(by_path[parent], "PARENT_NODE_PATH")
        elements = {path: _decode_registry_element(by_path[path], by_path) for path in sorted(included)}
        if elements[root]["operator"] != "object":
            raise ValueError("Registry root requires an object operator")
        if any(spec["operator"] in {"roles", "parties"} and path not in linked
               for path, spec in elements.items()):
            raise ValueError("Linked identity operator lacks an assignment family")
        if groups:
            namespaces = {(profile["SOURCE_SYSTEM_NAME"], profile["SOURCE_TABLE_NAME"])
                          for profile in source_profiles if model in profile.get("MODEL_KEYS", ())}
            if len(namespaces) != 1:
                raise ValueError("Reference family requires one source namespace")
            source_system, source_table = next(iter(namespaces))
            for group in groups:
                group["source_namespace"] = {"SOURCE_SYSTEM_NAME": source_system,
                                             "SOURCE_TABLE_NAME": source_table, "MODEL_KEY": model}

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
    from collections import Counter

    issues = report["ISSUES"]
    reason_counts, severity_counts = Counter(), Counter()
    for issue in issues:
        count = issue.get("affected_rows", 1)
        reason_counts[issue["reason"]] += count
        severity_counts[issue["severity"]] += count
    ordered = sorted(issues, key=lambda issue: (
        0 if issue["severity"] == "BLOCKED" else 1,
        issue.get("row") if issue.get("row") is not None else -1,
    ))
    report.update(
        REASON_COUNTS=dict(reason_counts), SEVERITY_COUNTS=dict(severity_counts),
        ISSUE_EVENTS_TOTAL=len(issues), ISSUE_SAMPLE_LIMIT=sample_limit,
        ISSUE_SAMPLES_TRUNCATED=len(issues) > sample_limit,
        ISSUES=ordered[:sample_limit],
    )


def compile_mapping_contexts(mapping_rows, registry_rows, source_profiles, model_contracts,
                             routing_metadata=None):
    """Pure source/model routing. No data reads, globals mutation or writes."""
    registry = [_meta_row(row) for row in registry_rows]
    mappings = {key: [_meta_row(row) for row in rows]
                for key, rows in mapping_rows.items()}
    model_contracts = _decode_registry_model_contracts(
        registry, source_profiles, model_contracts, mappings)
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
        rows = mappings[profile["SOURCE_KEY"]]
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
                owner = _owner_for_path(path, paths)
                relative = path[len(owner):].lstrip(".") if owner is not None else ""
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
                elif flat_status is None and row.get("APPROVAL_STATUS"):
                    classification, reason = "BLOCKED_ROWS", "RETIRED_MAPPING_METADATA"
                elif flat_status is None and any(
                        row.get(key) not in (None, "") for key in (
                            "TRANSFORM_ID", "TRANSFORM_PARAMS", "REPRESENTATION",
                            "REPRESENTATION_PARAMS", "VALUE_CONSTRAINTS")):
                    classification, reason = "BLOCKED_ROWS", "UNAPPROVED_EXECUTABLE_METADATA"
                elif flat_status is None:
                    classification = "DEFERRED_ROWS" if contract.get("UNREVIEWED_ROWS") == "DEFER" else "BLOCKED_ROWS"
                    reason = "MISSING_APPROVED_METADATA"
                elif path and path_model is None:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif not field:
                    classification, reason = "BLOCKED_ROWS", "MISSING_SOURCE_FIELD"
                elif not path:
                    classification = "BLOCKED_ROWS" if flat_status else "DEFERRED_ROWS"
                    reason = "MISSING_TARGET_PATH"
                elif path_model != model:
                    classification, reason = "BLOCKED_ROWS", "UNKNOWN_MODEL_OR_PATH"
                elif any(path == boundary or path.startswith(boundary + ".") for boundary in unavailable_paths):
                    classification, reason = "BLOCKED_ROWS", "REGISTRY_PATH_NOT_EXECUTABLE"
                elif owner is None:
                    classification, reason = "BLOCKED_ROWS", "UNREGISTERED_PATH"
                elif "[]" in relative or flat_status and any(token in relative for token in ("[", "]", "..")):
                    classification, reason = "BLOCKED_ROWS", "UNREGISTERED_COLLECTION"
                if classification:
                    report[classification] += 1
                    if reason:
                        issue = {"row": index, "field": field, "reason": reason,
                                 "severity": classification.removesuffix("_ROWS")}
                        if reason not in {"REGISTRY_PATH_NOT_EXECUTABLE", "UNREGISTERED_PATH", "UNREGISTERED_COLLECTION"}:
                            issue.update(model_label=row.get("OSCAL_MODEL"), target_path=path, resolved_model=path_model)
                        report["ISSUES"].append(issue)
                    continue
                canonical = dict(row)
                canonical.update(ARTIFACT_MODEL=row.get("ARTIFACT_MODEL", row.get("OSCAL_MODEL")),
                                 CANONICAL_ELEMENT_PATH=path,
                                 OWNER_ELEMENT_PATH=owner, FIELD_RELATIVE_PATH=relative,
                                 OSCAL_MODEL=model, SOURCE_KEY=profile["SOURCE_KEY"])
                if not canonical.get("OSCAL_FIELD_NAME"):
                    canonical["OSCAL_FIELD_NAME"] = relative.split(".")[-1].replace("[]", "") if relative else None
                canonical["MAPPING_TYPE"] = canonical.get("MAPPING_TYPE") or "Direct"
                canonical["STATUS"] = canonical.get("STATUS") or "In Progress"
                selected.append(canonical)
                report["SELECTED_ROWS"] += 1
            selected.sort(key=lambda row: (row["OWNER_ELEMENT_PATH"], row["CANONICAL_ELEMENT_PATH"], row["SOURCE_FIELD_NAME"]))
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
            for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
                if cfg["STORAGE_CONTRACT"]:
                    cfg[key] = cfg["STORAGE_CONTRACT"][key]
                else:
                    cfg.pop(key, None)
            context = {"source_key": profile["SOURCE_KEY"], "config": cfg,
                             "mapping_rows": selected,
                             "model_contract": contract, "registry_rows": model_registry,
                             "routing_report": report}
            if report["STATUS"] == "READY":
                try:
                    context["compiled_plan"] = compile_metadata_plan(context)
                    context["mapping_rows"] = context["compiled_plan"]["mappings"]
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
            for row in context["mapping_rows"]:
                context["mappings_by_path"].setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
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
