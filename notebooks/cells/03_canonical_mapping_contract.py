# %% Cell 3 - Compile the mapping CSV against the element registry

import copy
import math
import re
from collections import Counter

LEAN_MAPPER_RELEASE = "lean-csv-registry-v1"
METADATA_TRANSFORM_IDS = {
    "direct", "text", "timestamp", "date", "identifier", "archer-select",
    "scalar-score", "security-objective", "status-crosswalk", "reject-populated",
    "skip", "canonical-text",
}
METADATA_INSTANCE_RULES = {
    "record": "SOURCE_RECORD_ID", "observations": "SOURCE_FIELD_NAME",
    "properties": "SOURCE_FIELD_NAME+VALUE", "values": "VALUE", "references": "CONTENT_ID",
    "roles": "SOURCE_FIELD_NAME", "parties": "ID", "assignments": "SOURCE_FIELD_NAME+ID",
}
METADATA_ITEM_PATHS = {operator: (None if operator in {"record", "observations"} else
                                "UserList[]" if operator in {"parties", "assignments"} else "$")
                       for operator in METADATA_INSTANCE_RULES}


def _meta_row(row):
    row = row.as_dict(recursive=True) if hasattr(row, "as_dict") else row
    result = {}
    for key, value in row.items():
        key = str(key).strip().upper()
        key = {"ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME", "MAPPING_STATUS": "STATUS"}.get(key, key)
        if key in result:
            raise ValueError("Ambiguous metadata column: " + key)
        result[key] = (None if value is None or isinstance(value, float) and math.isnan(value)
                       else value.strip() if isinstance(value, str) else value)
    return result


def _metadata_column_text(row, key, required=False):
    value = row.get(key)
    if value in (None, "") and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(key + " must contain nonblank text")
    return value.strip()


def _metadata_items(row, key):
    value = _metadata_column_text(row, key)
    items = [item.strip() for item in value.split("|")] if value else []
    if any(not item for item in items) or len(set(items)) != len(items):
        raise ValueError(key + " contains empty or duplicate entries")
    return items


def _registry_meta_bool(row, key):
    value = row.get(key)
    if type(value) is bool:
        return value
    if isinstance(value, str) and value.lower() in {"true", "false"}:
        return value.lower() == "true"
    raise ValueError(key + " must be true or false")


def _registry_path(row):
    return row.get("NODE_PATH") or ""


def _registry_model(row):
    return str(row.get("OSCAL_MODEL_KEY") or "").upper()


def _model_token(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


def _metadata_params(row):
    return row.get("REPRESENTATION_PARAMS") or {}


def _metadata_target(row):
    return _metadata_params(row).get("target") or row.get("FIELD_RELATIVE_PATH") or row.get("OSCAL_FIELD_NAME")


def _owner_for_path(path, paths):
    return max((p for p in paths if path == p or path.startswith(p + ".")), key=len, default=None)


def _registry_operator(row):
    operator = _metadata_column_text(row, "OPERATOR")
    if operator:
        if operator not in {"object", *METADATA_INSTANCE_RULES}:
            raise ValueError("Unknown registry OPERATOR")
        return operator
    if not _registry_meta_bool(row, "IS_COLLECTION"):
        return "object"
    identity = (row.get("INSTANCE_KEY_RULE"), row.get("ITEM_PATH"))
    for candidate in METADATA_INSTANCE_RULES:
        if identity == (METADATA_INSTANCE_RULES[candidate], METADATA_ITEM_PATHS[candidate]):
            return candidate
    raise ValueError("Collection requires a supported registry OPERATOR and identity")


def _registry_elements(rows, selected, profile, model):
    """Validate hierarchy once, retaining mapped/explicit paths and their ancestors."""
    by_path = {_registry_path(row): row for row in rows}
    if not by_path or "" in by_path or len(by_path) != len(rows):
        raise ValueError("Enabled model requires unique active registry paths")
    parents = {path: row.get("PARENT_NODE_PATH") or None for path, row in by_path.items()}
    roots = [path for path, parent in parents.items() if parent is None]
    if len(roots) != 1 or "." in roots[0]:
        raise ValueError("Enabled model requires one registry root")
    root = roots[0]
    for path, row in by_path.items():
        order = row.get("PROCESS_ORDER")
        order = 0 if order in (None, "") else order
        if isinstance(order, bool) or int(order) != float(order):
            raise ValueError("Registry PROCESS_ORDER must be an integer")
        row["PROCESS_ORDER"] = int(order)
        if _registry_meta_bool(row, "IS_COLLECTION") != path.endswith("[]"):
            raise ValueError("Registry collection flag conflicts with its path")
        if path != root and (parents[path] not in by_path or not path.startswith(parents[path] + ".")):
            raise ValueError("Registry child requires its active path ancestor")
    included = {root} | {row["OWNER_ELEMENT_PATH"] for row in selected}
    included.update(path for path, row in by_path.items() if row.get("OPERATOR"))
    groups, linked = [], set()
    for path in sorted(included):
        if _registry_operator(by_path[path]) != "assignments":
            continue
        siblings = {"roles": [], "parties": []}
        for other, row in by_path.items():
            if parents[other] != parents[path]:
                continue
            try:
                operator = _registry_operator(row)
            except ValueError:
                if row.get("OPERATOR"):
                    raise
                continue
            if operator in siblings:
                siblings[operator].append(other)
        if any(len(paths) != 1 for paths in siblings.values()):
            raise ValueError("Assignment requires one role and one party registry sibling")
        role, party = siblings["roles"][0], siblings["parties"][0]
        if {path, role, party} & linked:
            raise ValueError("Reference families require distinct registry paths")
        linked.update((path, role, party))
        groups.append({"roles_path": role, "parties_path": party, "assignments_path": path,
                       "party_type": "person", "source_namespace": {
                           "SOURCE_SYSTEM_NAME": profile["SOURCE_SYSTEM_NAME"],
                           "SOURCE_TABLE_NAME": profile["SOURCE_TABLE_NAME"], "MODEL_KEY": model}})
    included.update(linked)
    for path in tuple(included):
        parent = parents[path]
        while parent is not None and parent not in included:
            included.add(parent)
            parent = parents[parent]
    elements = {}
    for path in sorted(included):
        row, parent = by_path[path], parents[path]
        operator, collection = _registry_operator(row), _registry_meta_bool(row, "IS_COLLECTION")
        if operator != "object" and not collection:
            raise ValueError("Collection operator requires IS_COLLECTION=true")
        parameters = {"registry_contract": {"parent_path": parent, "is_collection": collection}}
        if collection:
            identity = (row.get("INSTANCE_KEY_RULE"), row.get("ITEM_PATH"))
            expected = ("VALUE", "$") if operator == "object" else (METADATA_INSTANCE_RULES[operator], METADATA_ITEM_PATHS[operator])
            if identity != expected:
                raise ValueError("Registry identity conflicts with OPERATOR")
            parameters["registry_contract"].update(instance_key_rule=identity[0], item_path=identity[1])
        if parent and _registry_meta_bool(by_path[parent], "IS_COLLECTION"):
            if _registry_operator(by_path[parent]) != "record":
                raise ValueError("Nested collection requires a record parent identity")
            parameters["parent_instance_rule"] = "source-record"
        elif operator == "record":
            parameters["parent_instance_rule"] = "singleton"
        policy = _metadata_column_text(row, "UUID_POLICY", required=bool(row.get("OPERATOR"))) or "omit"
        if policy not in {"omit", "node", "instance"} or (policy == "instance") != (operator == "parties"):
            raise ValueError("Invalid registry UUID policy")
        if policy != "omit":
            parameters["include_uuid"] = True
        if policy == "instance":
            parameters["uuid_from_instance"] = True
        members = _metadata_items(row, "REQUIRED_MEMBERS")
        if members:
            if operator != "object" or any(not re.fullmatch(r"[\w-]+(?:\.[\w-]+)*", member) for member in members):
                raise ValueError("REQUIRED_MEMBERS requires scalar object member paths")
            parameters.update(required_members=members, optional_assembly=True)
        elif operator == "object" and not collection:
            parameters["materialize_empty"] = True
        if operator in {"properties", "observations"}:
            parameters["property_name_rule"] = "source-field-slug"
        if operator in {"roles", "parties"} and path not in linked:
            raise ValueError("Linked identity operator lacks an assignment family")
        elements[path] = {"operator": operator, "parameters": parameters}
    if elements[root]["operator"] != "object":
        raise ValueError("Registry root requires an object operator")
    return root, [row for row in rows if _registry_path(row) in included], elements, groups


def _compile_mapping(row, elements):
    """Translate explicit CSV columns to the parameters used by Cell Four."""
    transform = _metadata_column_text(row, "TRANSFORM_ID", True)
    rule = _metadata_column_text(row, "RULE_ID", True)
    if transform not in METADATA_TRANSFORM_IDS:
        raise ValueError("Unknown reusable TRANSFORM_ID")
    if row["EXECUTION_STATUS"] == "BLOCKED_IF_POPULATED" and transform != "reject-populated":
        raise ValueError("Populated-only guard requires reject-populated")
    operator = elements[row["OWNER_ELEMENT_PATH"]]["operator"]
    target = row["FIELD_RELATIVE_PATH"]
    params, representation = {}, {}
    if target:
        if operator not in {"object", "record", "values"} or not re.fullmatch(r"[\w-]+(?:\.[\w-]+)*", target):
            raise ValueError("Member target conflicts with its element operator")
        representation["target"] = target
    source = row.get("VALUE_SOURCE") or "FIELD"
    if source not in {"FIELD", "CONFIG"} or source == "CONFIG" and (operator not in {"object", "record"} or not target):
        raise ValueError("CONFIG values require an explicit object member target")
    if source == "CONFIG":
        representation["value_source"] = source
    if row.get("VALUE_REQUIRED") not in (None, ""):
        representation["required"] = _registry_meta_bool(row, "VALUE_REQUIRED")
    if transform == "skip" and representation.get("required"):
        raise ValueError("Skip transform cannot supply a required value")
    allowed = {"VALUE_SOURCE", "VALUE_REQUIRED"}
    if transform == "security-objective":
        allowed.add("ALLOWED_VALUES")
        if row.get("ALLOWED_VALUES"):
            params["approved_legacy_values"] = _metadata_items(row, "ALLOWED_VALUES")
    if transform == "status-crosswalk":
        allowed.update(("VALUE_MAP", "OTHER_REMARKS_TEMPLATE"))
        crosswalk = {}
        for entry in _metadata_items(row, "VALUE_MAP"):
            if entry.count("=") != 1:
                raise ValueError("VALUE_MAP entries must be source=target")
            source, target = (part.strip() for part in entry.split("=", 1))
            source = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
            if not source or not target or source in crosswalk:
                raise ValueError("VALUE_MAP contains empty or conflicting labels")
            crosswalk[source] = target
        if not crosswalk:
            raise ValueError("Crosswalk requires VALUE_MAP")
        params["crosswalk"] = crosswalk
        template = row.get("OTHER_REMARKS_TEMPLATE")
        if template:
            if template.count("{label}") != 1 or any(c in template.replace("{label}", "") for c in "{}"):
                raise ValueError("OTHER_REMARKS_TEMPLATE requires one {label} placeholder")
            params["other_remarks_prefix"], params["other_remarks_suffix"] = template.split("{label}")
        elif "other" in crosswalk.values():
            raise ValueError("Crosswalk other value requires an explanation")
    if operator == "assignments":
        allowed.update(("ROLE_ID", "ROLE_TITLE"))
        representation.update(role_id=_metadata_column_text(row, "ROLE_ID", True),
                              role_title=_metadata_column_text(row, "ROLE_TITLE", True))
    if operator == "references":
        allowed.update(("REFERENCE_TYPE", "LOOKUP_KEY", "DESCRIPTION_REQUIRED"))
        representation["reference_type"] = _metadata_column_text(row, "REFERENCE_TYPE", True)
        if row.get("LOOKUP_KEY"):
            representation["hydrate_lookup"] = _metadata_column_text(row, "LOOKUP_KEY")
        if row.get("DESCRIPTION_REQUIRED") not in (None, ""):
            if not row.get("LOOKUP_KEY"):
                raise ValueError("DESCRIPTION_REQUIRED needs LOOKUP_KEY")
            representation["description_required"] = _registry_meta_bool(row, "DESCRIPTION_REQUIRED")
    columns = {"ALLOWED_VALUES", "VALUE_MAP", "OTHER_REMARKS_TEMPLATE", "ROLE_ID", "ROLE_TITLE",
               "REFERENCE_TYPE", "LOOKUP_KEY", "DESCRIPTION_REQUIRED", "VALUE_SOURCE", "VALUE_REQUIRED"}
    if any(row.get(key) not in (None, "") for key in columns - allowed):
        raise ValueError("CSV parameter does not apply to the selected operation")
    return dict(row, TRANSFORM_PARAMS=params, REPRESENTATION=operator, REPRESENTATION_PARAMS=representation,
                APPROVAL_STATUS=row["EXECUTION_STATUS"], RULE_ID=rule)


def _mapping_route(row, profile, model, paths, inactive, aliases, roots, routing, source_keys, unreviewed):
    """Return exclusion reason, or the canonical registered owner and member path."""
    status = row.get("EXECUTION_STATUS")
    original = row.get("OSCAL_ELEMENT_PATH") or ""
    path = row.get("RUNTIME_TARGET_PATH") or "" if status in {"APPROVED", "BLOCKED_IF_POPULATED"} else original
    label = _model_token(row.get("OSCAL_MODEL"))
    owner_model, label_model = roots.get(path.split(".", 1)[0]), aliases.get(label)
    source = row.get("SOURCE_KEY")
    reason, severity = None, "BLOCKED"
    if status not in {None, "", "APPROVED", "BLOCKED_IF_POPULATED", "DEFERRED", "EXCLUDED"} or (
            not status and row.get("RUNTIME_TARGET_PATH")):
        reason = "INVALID_EXECUTION_STATUS"
    elif source and source not in source_keys:
        reason = "UNKNOWN_SOURCE_KEY"
    elif source and source != profile["SOURCE_KEY"]:
        reason, severity = "OTHER_SOURCE", "EXCLUDED"
    elif status and not source:
        reason = "MISSING_SOURCE_KEY"
    elif status in {"DEFERRED", "EXCLUDED"}:
        reason, severity = "EXPLICIT_" + status, status
    elif label_model and owner_model and label_model != owner_model or (
            status and roots.get(original.split(".", 1)[0]) not in {None, owner_model}):
        reason = "MODEL_PATH_CONFLICT"
    elif label in routing["labels"] or path in routing["paths"]:
        reason, severity = "PLACEHOLDER_MAPPING", "DEFERRED"
    elif owner_model and owner_model != model or not path and label_model and label_model != model:
        reason, severity = "OTHER_MODEL", "EXCLUDED"
    elif any(row.get(key) not in (None, "") for key in (
            "TRANSFORM_PARAMS", "REPRESENTATION_PARAMS", "REPRESENTATION", "VALUE_CONSTRAINTS", "APPROVAL_STATUS")):
        reason = "RETIRED_MAPPING_METADATA"
    elif not status:
        reason, severity = "MISSING_APPROVED_METADATA", "DEFERRED" if unreviewed == "DEFER" else "BLOCKED"
    elif not row.get("SOURCE_FIELD_NAME"):
        reason = "MISSING_SOURCE_FIELD"
    elif not path or owner_model is None:
        reason = "UNKNOWN_MODEL_OR_PATH"
    elif any(path == boundary or path.startswith(boundary + ".") for boundary in inactive):
        reason = "REGISTRY_PATH_NOT_EXECUTABLE"
    owner = _owner_for_path(path, paths)
    relative = path[len(owner):].lstrip(".") if owner else ""
    if not reason and (owner is None or any(token in relative for token in ("[", "]", ".."))):
        reason = "UNREGISTERED_COLLECTION"
    if reason:
        return None, {"reason": reason, "severity": severity, "field": row.get("SOURCE_FIELD_NAME")}
    return dict(row, ARTIFACT_MODEL=row.get("OSCAL_MODEL"), CANONICAL_ELEMENT_PATH=path,
                OWNER_ELEMENT_PATH=owner, FIELD_RELATIVE_PATH=relative, OSCAL_MODEL=model,
                OSCAL_FIELD_NAME=row.get("OSCAL_FIELD_NAME") or (relative.split(".")[-1] if relative else None)), None


def compile_mapping_contexts(mapping_rows, registry_rows, source_profiles, model_contracts, routing_metadata=None):
    """One input boundary: pure compilation, no source reads or executable metadata."""
    registry = [_meta_row(row) for row in registry_rows]
    active = [row for row in registry if _registry_meta_bool(row, "IS_ACTIVE")]
    mappings = {key: [_meta_row(row) for row in rows] for key, rows in mapping_rows.items()}
    source_keys = {profile["SOURCE_KEY"] for profile in source_profiles}
    if len(source_keys) != len(source_profiles) or source_keys != set(mappings):
        raise ValueError("Each source needs one explicit mapping input")
    for profile in source_profiles:
        models = profile["MODEL_KEYS"]
        if not models or len(set(models)) != len(models) or set(models) - set(model_contracts):
            raise ValueError("Source route requires distinct configured models")
    aliases, roots = {}, {}
    for model, contract in model_contracts.items():
        if contract.get("MODEL_KEY") != model or {"ELEMENTS", "ROOT_PATH", "DEFAULT_ELEMENT", "MAPPING_RULES",
                "PATH_RULES", "SELECTED_FIELDS", "EXCLUDED_FIELDS", "REFERENCE_GROUPS"} & contract.keys():
            raise ValueError("Model settings cannot override CSV mappings or registry structure")
        for label in [model, *contract.get("MODEL_ALIASES", ())]:
            token = _model_token(label)
            if not token or aliases.get(token, model) != model:
                raise ValueError("Ambiguous model alias")
            aliases[token] = model
    for row in active:
        model, root = _registry_model(row), _registry_path(row).split(".", 1)[0]
        if not model or not root or roots.get(root, model) != model:
            raise ValueError("Registry root requires one model owner")
        roots[root] = model
        for label in (model, root, row.get("OSCAL_MODEL"), row.get("MODEL_NAME")):
            token = _model_token(label)
            if token and aliases.get(token, model) != model:
                raise ValueError("Registry label conflicts with configured ownership")
            if token:
                aliases[token] = model
    routing_metadata = routing_metadata or {}
    if set(routing_metadata) - {"DEFERRED_MODEL_LABELS", "DEFERRED_TARGET_PATHS"}:
        raise ValueError("Unknown routing setting")
    if any(not isinstance(values, (tuple, list)) or any(not isinstance(v, str) or not v.strip() for v in values)
           for values in routing_metadata.values()):
        raise ValueError("Routing placeholders must be lists of nonblank text")
    routing = {"labels": {_model_token(v) for v in routing_metadata.get("DEFERRED_MODEL_LABELS", ())},
               "paths": set(routing_metadata.get("DEFERRED_TARGET_PATHS", ()))}
    if "" in routing["labels"] or routing["labels"] & set(aliases) or routing["paths"] & {_registry_path(row) for row in active}:
        raise ValueError("Placeholder conflicts with a registered model or path")
    contexts = []
    for profile in source_profiles:
        for model in profile["MODEL_KEYS"]:
            settings = copy.deepcopy(model_contracts[model])
            model_rows = [row for row in active if _registry_model(row) == model]
            paths = {_registry_path(row) for row in model_rows}
            inactive = {_registry_path(row) for row in registry if _registry_model(row) == model} - paths
            selected, issues = [], []
            for index, row in enumerate(mappings[profile["SOURCE_KEY"]]):
                canonical, issue = _mapping_route(row, profile, model, paths, inactive, aliases, roots,
                                                   routing, source_keys, settings.get("UNREVIEWED_ROWS"))
                if issue:
                    issues.append(dict(issue, row=index))
                else:
                    selected.append(canonical)
            selected.sort(key=lambda row: (row["OWNER_ELEMENT_PATH"], row["CANONICAL_ELEMENT_PATH"], row["SOURCE_FIELD_NAME"]))
            root, model_rows, elements, groups = _registry_elements(model_rows, selected, profile, model)
            namespaces = {(p["SOURCE_SYSTEM_NAME"], p["SOURCE_TABLE_NAME"])
                          for p in source_profiles if model in p["MODEL_KEYS"]}
            if groups and len(namespaces) != 1:
                raise ValueError("Existing party UUID identity requires one source namespace per model")
            report = dict(settings.get("REPORT") or {})
            if report:
                observations = [path for path, spec in elements.items() if spec["operator"] == "observations"]
                if len(observations) != 1 or "TARGET_PATH" in report:
                    raise ValueError("Report requires one registry observation path")
                report["TARGET_PATH"] = observations[0]
            settings.update(ROOT_PATH=root, ELEMENTS=elements, ELEMENT_PATHS=tuple(elements), REFERENCE_GROUPS=groups, REPORT=report)
            storage = copy.deepcopy(profile.get("MODEL_STORAGE_CONTRACTS", {}).get(model, settings.get("STORAGE_CONTRACT")))
            settings["STORAGE_CONTRACT"] = storage
            config = dict(copy.deepcopy(profile.get("BASE_CONFIG", {})), OSCAL_MODEL=model, ROOT_PATH=root,
                          ROOT_ELEMENT_TYPE=next(row for row in model_rows if _registry_path(row) == root).get("ELEMENT_TYPE") or root,
                          STORAGE_CONTRACT=storage, EXECUTE_WRITES=False)
            config.update({key: profile[key] for key in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "RAW_TABLE")})
            for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
                config.pop(key, None)
                if storage:
                    config[key] = storage[key]
            plan, contract_error = None, None
            if not any(issue["severity"] == "BLOCKED" for issue in issues):
                try:
                    selected = [_compile_mapping(row, elements) for row in selected]
                    identities = [(row["OWNER_ELEMENT_PATH"], row["SOURCE_FIELD_NAME"], row["FIELD_RELATIVE_PATH"]) for row in selected]
                    if len({row["RULE_ID"] for row in selected}) != len(selected) or len(set(identities)) != len(selected):
                        raise ValueError("Duplicate mapping rule or field target")
                    options = {key: value for key, value in settings.get("RUNTIME_OPTIONS", {}).items()
                               if key in {"parse_decimal", "null_source_as_empty"}}
                    plan = dict(version=1, release=LEAN_MAPPER_RELEASE, elements=elements, mappings=selected,
                                reference_groups=groups, options=options, report=report)
                except ValueError as error:
                    contract_error = str(error)
                    issues.append(dict(row=None, field=None, reason="METADATA_CONTRACT_ERROR", severity="BLOCKED", affected_rows=len(selected)))
                    selected = []
            counts = Counter()
            reasons = Counter()
            for issue in issues:
                counts[issue["severity"]] += issue.get("affected_rows", 1)
                reasons[issue["reason"]] += issue.get("affected_rows", 1)
            route_report = dict(STATUS="BLOCKED" if counts["BLOCKED"] else "READY",
                                INPUT_ROWS=len(mappings[profile["SOURCE_KEY"]]), SELECTED_ROWS=len(selected),
                                EXCLUDED_ROWS=counts["EXCLUDED"], DEFERRED_ROWS=counts["DEFERRED"], BLOCKED_ROWS=counts["BLOCKED"],
                                REASON_COUNTS=dict(reasons), SEVERITY_COUNTS=dict(counts), ROUTING_POLICY="registry-first-v1",
                                ISSUE_EVENTS_TOTAL=len(issues), ISSUE_SAMPLE_LIMIT=25, ISSUE_SAMPLES_TRUNCATED=len(issues) > 25,
                                ISSUES=sorted(issues, key=lambda issue: issue["severity"] != "BLOCKED")[:25])
            if contract_error:
                route_report["CONTRACT_ERROR"] = contract_error
            by_path = {}
            for row in selected:
                by_path.setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
            contexts.append(dict(source_key=profile["SOURCE_KEY"], config=config, model_contract=settings,
                                 mapping_rows=selected, registry_rows=model_rows, mappings_by_path=by_path,
                                 compiled_plan=plan, routing_report=route_report))
    return contexts


MAPPING_CONTEXTS = compile_mapping_contexts(MAPPING_INPUTS, REGISTRY_INPUT_ROWS, SOURCE_PROFILES,
                                            MODEL_CONTRACTS, ROUTING_METADATA)
print("Mapping routes:", [(c["source_key"], c["config"]["OSCAL_MODEL"], c["routing_report"]) for c in MAPPING_CONTEXTS])
