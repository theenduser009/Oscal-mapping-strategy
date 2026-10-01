# %% Cell 4 - Reusable transforms and registry operators

import copy
import datetime
import hashlib
import json
import math
import re
import uuid
from decimal import Decimal

SKIP_VALUE = object()
ARCHER_SELECT_ID_CONTAINER_KEYS = {"valuelistid", "valuelistids", "valueslistid", "valueslistids"}


def _to_python(value):
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    return value.as_list() if hasattr(value, "as_list") else value


def _has_value(value):
    return value not in (None, "", [], {})


def resolve_json_path(source_obj, field_path, default=None):
    """Read a literal source key first, then a dotted/slash path or list index."""
    if not field_path:
        return default
    if isinstance(source_obj, dict) and field_path in source_obj:
        return _to_python(source_obj[field_path])
    current = source_obj
    for token in filter(None, re.split(r"[./]", str(field_path))):
        current = _to_python(current)
        if isinstance(current, dict):
            current = current.get(token, current.get(token.upper(), default))
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return default
    return _to_python(current)


def _stable_property_name(field):
    return re.sub(r"[^a-z0-9]+", "-", field.lower()).strip("-")


def _deterministic_uuid(*parts):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "|".join(map(str, parts))))


def _deterministic_hash(*parts):
    return hashlib.md5("|".join(map(str, parts)).encode("utf-8")).hexdigest()


def _json_text(value):
    return json.dumps(value, sort_keys=True, default=str, allow_nan=False)


def _scalar_text(value, shape_error, value_error, allow_bool=False):
    value = _to_python(value)
    if value is None or isinstance(value, (dict, list)) or isinstance(value, bool) and not allow_bool:
        raise ValueError(shape_error)
    text = ("true" if value else "false") if isinstance(value, bool) else str(value).strip()
    if not text or text.lower() in {"nan", "inf", "+inf", "-inf"}:
        raise ValueError(value_error)
    return text


def _oscal_property_values(value):
    return [_scalar_text(item, "Property value must be scalar", "Property value must be finite and nonblank", True)
            for item in (value if isinstance(value, list) else [value])]


def _extract_reference_ids(value):
    value = _to_python(value)
    if isinstance(value, dict):
        for key in ("UserList", "ValuesListIds", "ValueListIds", "ContentId", "ContentIds", "Ids", "Value"):
            if key in value and _has_value(value[key]):
                return _extract_reference_ids(value[key])
        for key, item in value.items():
            if re.sub(r"[^a-z0-9]", "", str(key).lower()) in ARCHER_SELECT_ID_CONTAINER_KEYS and _has_value(item):
                return _extract_reference_ids(item)
    if isinstance(value, list):
        result = []
        for item in value:
            extracted = _extract_reference_ids(item)
            result.extend(extracted if isinstance(extracted, list) else [extracted])
        return result
    return value


def _contains_archer_select_id_container(value):
    value = _to_python(value)
    if isinstance(value, dict):
        return any(re.sub(r"[^a-z0-9]", "", str(key).lower()) in ARCHER_SELECT_ID_CONTAINER_KEYS
                   or _contains_archer_select_id_container(item) for key, item in value.items())
    return isinstance(value, list) and any(_contains_archer_select_id_container(item) for item in value)


def resolve_archer_select_value(value, context):
    lookup = context["lookups"].get("archer_values", {})
    strict = _contains_archer_select_id_container(value)
    extracted = _extract_reference_ids(value)

    def resolve(item):
        item = _to_python(item)
        if item is None:
            return None
        if isinstance(item, (dict, list, bool)):
            if strict:
                raise ValueError("Archer select-value container is invalid")
            return item
        key = str(item).strip()
        if strict and (key not in lookup or not _has_value(lookup[key])):
            raise ValueError("Archer select-value ID is unresolved")
        return lookup.get(key, item)

    if isinstance(extracted, list):
        return [result for item in extracted if (result := resolve(item)) is not None]
    return resolve(extracted)


def _single_archer_label(value, context):
    extracted = _extract_reference_ids(value)
    values = [item for item in (extracted if isinstance(extracted, list) else [extracted]) if item is not None]
    if len(values) != 1 or isinstance(values[0], (dict, list)):
        return None
    item, key = values[0], str(values[0]).strip()
    label = context["lookups"].get("archer_values", {}).get(key)
    if label is not None:
        return str(label).strip() or None
    return key if isinstance(item, str) and key and not key.isdigit() else None


def transform_fips_199(value, context):
    # A singleton objective must not discard unrecognized members of a list.
    extracted = _extract_reference_ids(value)
    items = extracted if isinstance(extracted, list) else [extracted]
    if not items:
        return None
    if len(items) != 1:
        raise ValueError("Security objective requires exactly one input value")
    item, lookups = items[0], context["lookups"]
    if item is None:
        return None
    key = str(item).strip()
    label = lookups.get("fips_values", {}).get(key)
    if label is None:
        candidate = str(lookups.get("archer_values", {}).get(key, item)).strip().lower()
        label = candidate if candidate in {"low", "moderate", "high"} else None
    return label


def transform_document_identifier(value):
    return _scalar_text(value, "Document identifier must be scalar", "Document identifier must be finite and nonblank")


def transform_authorization_date(value):
    """Keep the source calendar date; never reinterpret an offset as UTC."""
    value = _to_python(value)
    if not _has_value(value):
        return SKIP_VALUE
    try:
        if isinstance(value, (datetime.datetime, datetime.date)):
            return datetime.date(value.year, value.month, value.day).isoformat()
        if isinstance(value, str):
            text = value.strip()
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", text):
                return datetime.date.fromisoformat(text).isoformat()
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt ][0-9]{2}:[0-9]{2}:[0-9]{2}"
                            r"(?:\.[0-9]{1,9})?(?:[Zz]|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])?", text):
                text = text[:10] + "T" + text[11:]
                if text[-1:] in {"Z", "z"}:
                    text = text[:-1] + "+00:00"
                return datetime.datetime.fromisoformat(text).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        pass
    raise ValueError("Mapped date requires a valid ISO date or timestamp")


def _score_value(value, context):
    if not _has_value(value):
        return None
    if _contains_archer_select_id_container(value):
        value = resolve_archer_select_value(value, context)
    values = value if isinstance(value, list) else [value]
    if len(values) != 1 or not isinstance(values[0], (str, int, float, bool, Decimal)):
        raise ValueError("One scalar score is required per observation")
    item = values[0]
    if isinstance(item, float) and not math.isfinite(item) or isinstance(item, Decimal) and not item.is_finite():
        raise ValueError("Score must be finite")
    result = _oscal_property_values(item)[0]
    if result.lower() in {"infinity", "+infinity", "-infinity"}:
        raise ValueError("Score must be finite")
    return result


def _metadata_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be nonblank text")
    return value


def _metadata_transform(row, value, context):
    transform, params = row["TRANSFORM_ID"], row.get("TRANSFORM_PARAMS") or {}
    if transform == "skip" or not _has_value(value):
        return SKIP_VALUE
    if transform == "direct":
        return _to_python(value)
    if transform in {"text", "timestamp", "canonical-text"}:
        value = _metadata_text(_to_python(value), "Mapped value")
        if transform == "canonical-text" and value != value.strip():
            raise ValueError("Controlled value must be canonical text")
        return value
    if transform == "date":
        return transform_authorization_date(value)
    if transform == "identifier":
        return transform_document_identifier(value)
    if transform == "archer-select":
        result = resolve_archer_select_value(value, context)
        return result if _has_value(result) else SKIP_VALUE
    if transform == "reference-ids":
        result = _extract_reference_ids(value)
        return result if _has_value(result) else SKIP_VALUE
    if transform == "json-text":
        try:
            return json.dumps(_to_python(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError):
            raise ValueError("Mapped JSON text value is not serializable") from None
    if transform == "scalar-score":
        return _score_value(value, context)
    if transform == "security-objective":
        result = transform_fips_199(value, context)
        if isinstance(result, list):
            raise ValueError("Security objective resolved to multiple values")
        if _has_value(result):
            return str(result)
        label = _single_archer_label(value, context)
        if label is None or label not in params.get("approved_legacy_values", ()):
            raise ValueError("Security objective contains an unreviewed label")
        return label
    if transform == "status-crosswalk":
        label = _single_archer_label(value, context)
        if label is None:
            raise ValueError("Crosswalk source label is unresolved or multivalued")
        target = params["crosswalk"].get(_stable_property_name(label))
        if target is None:
            raise ValueError("Label is absent from reviewed crosswalk")
        result = {"state": target}
        if target == "other":
            result["remarks"] = params["other_remarks_prefix"] + label + params.get("other_remarks_suffix", ".")
        return result
    raise ValueError("Populated source has no reviewed transformation")


def _metadata_mapped_value(row, source_obj, context):
    field, params = row["SOURCE_FIELD_NAME"], _metadata_params(row)
    raw = (context["config"].get(field) if params.get("value_source") == "CONFIG"
           else resolve_json_path(source_obj, field, default=SKIP_VALUE))
    try:
        if raw is SKIP_VALUE:
            value = SKIP_VALUE
        elif (raw is None and (params.get("preserve_null") or (
              row["TRANSFORM_ID"] == "scalar-score" and row["REPRESENTATION"] == "observations"
              and context["compiled_plan"]["options"].get("preserve_null_observations", False)))):
            value = None
        else:
            value = _metadata_transform(row, raw, context)
        if params.get("required") and (value is SKIP_VALUE or not _has_value(value)):
            raise ValueError("Required mapped value is absent after conversion")
    except (TypeError, ValueError, ArithmeticError):
        context["graph_report"]["STATUS"] = "BLOCKED"
        raise ValueError("Mapping failed for field " + field + " (" + str(row.get("RULE_ID", "")) + ")") from None
    context["graph_report"]["MISSING_VALUES" if value is SKIP_VALUE else "MAPPED_VALUES"] += 1
    return value


def _oscal_prop(name, value, namespace=None, prop_class=None, group=None):
    """One property constructor for business props and selective lineage props."""
    prop = {"name": _metadata_text(name, "Property name"), "value": value}
    if value is not None and not isinstance(value, str):
        raise ValueError("Property value must be text or an explicitly preserved warehouse null")
    if namespace is not None:
        if (not isinstance(namespace, str) or re.search(r"\s", namespace)
                or not re.fullmatch(r"[A-Za-z][A-Za-z0-9+.-]*:[^\s]+", namespace)):
            raise ValueError("Lineage namespace must be an absolute URI without whitespace")
        prop["ns"] = namespace
    if prop_class is not None:
        prop["class"] = _metadata_text(prop_class, "Property class")
    if group is not None:
        prop["group"] = _metadata_text(group, "Property group")
    return prop


def _capture_contribution(contributions, row, target, context, origin=None):
    rule = context["compiled_plan"]["lineage_rules"].get(row["RULE_ID"])
    if rule is not None and target in rule["targets"]:
        contribution = {"rule_id": row["RULE_ID"], "source_field": rule["source_field"],
                        "target": target, "origin": origin}
        if contribution not in contributions:
            contributions.append(contribution)


def _assign_mapped(payload, row, target, value, contributions, context, origin=None,
                   preserve_existing=False):
    if _metadata_assign(payload, target, value, preserve_existing):
        _capture_contribution(contributions, row, target, context, origin)


def _metadata_assign(payload, target, value, preserve_existing=False):
    current, tokens = payload, target.split(".")
    for token in tokens[:-1]:
        current = current.setdefault(token, {})
        if not isinstance(current, dict):
            raise ValueError("Nested payload member conflicts with scalar")
    member = tokens[-1]
    if member in current and _json_text(current[member]) != _json_text(value):
        if preserve_existing:
            return False
        raise ValueError("Singleton target has conflicting populated mappings")
    current[member] = copy.deepcopy(value)
    return True


def _metadata_get(payload, target):
    current = payload
    for token in target.split("."):
        current = current.get(token) if isinstance(current, dict) else None
    return current


def _metadata_parent_key(parameters, source_record_id):
    rule = parameters.get("parent_instance_rule")
    if rule == "source-record":
        return source_record_id
    return "singleton" if rule == "singleton" else None


def _append_unique_collection_instance(instances, instance):
    for existing in instances:
        if existing["instance_key"] == instance["instance_key"]:
            if _json_text(existing["payload"]) != _json_text(instance["payload"]):
                raise ValueError("Collection identity resolves to conflicting payloads")
            for contribution in instance.get("contributions", ()):
                if contribution not in existing.setdefault("contributions", []):
                    existing["contributions"].append(contribution)
            return
    instances.append(instance)


def _party_reference_identifier(item):
    item = _to_python(item)
    if isinstance(item, dict):
        item = item.get("Id") or item.get("UserId") or item.get("ContentId")
        if not _has_value(item):
            raise ValueError("Responsible-party reference has no stable identifier")
        return str(item).strip()
    return _scalar_text(item, "Responsible-party reference identifier is invalid", "Responsible-party reference identifier is empty")


def _party_resolved_user(item):
    item = _to_python(item)
    if not isinstance(item, dict) or "ResolvedUser" not in item:
        return None
    resolved = _to_python(item.get("ResolvedUser"))
    if not isinstance(resolved, dict):
        raise ValueError("ResolvedUser must be an object")
    if resolved.get("ContractVersion") != "archer-meta-user-v1":
        raise ValueError("ResolvedUser contract version is unsupported")
    status = resolved.get("LookupStatus")
    if status not in {"MATCHED", "MATCHED_MISSING_EEID", "USER_NOT_FOUND"}:
        raise ValueError("ResolvedUser lookup status is unsupported")
    return resolved


def _party_resolved_text(resolved, name):
    value = resolved.get(name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("ResolvedUser " + name + " must be text")
    value = value.strip()
    return value or None


def _party_payload(item, party_uuid, party_type, context):
    payload = {"uuid": party_uuid, "type": party_type}
    resolved = _party_resolved_user(item)
    if resolved is None or resolved["LookupStatus"] == "USER_NOT_FOUND":
        return payload

    name_parts = [
        value for name in ("FIRST_NAME", "MIDDLE_NAME", "LAST_NAME")
        if (value := _party_resolved_text(resolved, name)) is not None
    ]
    if name_parts:
        payload["name"] = " ".join(name_parts)

    eeid = _party_resolved_text(resolved, "EEID")
    if resolved["LookupStatus"] == "MATCHED" and eeid is None:
        raise ValueError("ResolvedUser MATCHED record is missing EEID")

    scheme = context["config"].get("ARCHER_EEID_SCHEME")
    if eeid is not None and scheme is not None:
        if not isinstance(scheme, str) or not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", scheme.strip()):
            raise ValueError("ARCHER_EEID_SCHEME must be an absolute URI")
        payload["external-ids"] = [{"scheme": scheme.strip(), "id": eeid}]
    return payload


def _merge_party_payload(existing, candidate):
    if existing["uuid"] != candidate["uuid"] or existing["type"] != candidate["type"]:
        raise ValueError("Party identity resolves to conflicting core payload")
    merged = copy.deepcopy(existing)
    for member in ("name", "external-ids"):
        if member not in candidate:
            continue
        if member in merged and _json_text(merged[member]) != _json_text(candidate[member]):
            raise ValueError("Party identity resolves to conflicting enriched payload")
        merged[member] = copy.deepcopy(candidate[member])
    return merged


def _component_reference_content_ids(value):
    result = []
    for item in (value if isinstance(value, list) else [value]):
        item = _to_python(item)
        item = item.get("ContentId") if isinstance(item, dict) else item
        result.append(_scalar_text(item, "Component reference has invalid ContentId", "Component reference has invalid ContentId"))
    return result


def _component_text(value, label, required):
    if value is None or isinstance(value, str) and not value.strip():
        if required:
            raise ValueError("Component hydration " + label + " is missing")
        return None
    if not isinstance(value, str):
        raise ValueError("Component hydration " + label + " must be text")
    return value.strip()


def _build_component_hydration_lookups(source_df, mapping_rows, source_dfs, context):
    """Stream frozen references once; fetch only needed lookup IDs in bounded SQL batches."""
    from snowflake.snowpark import functions as F
    contracts, fields = {}, {}
    for row in mapping_rows:
        params = _metadata_params(row)
        kind, binding = params["reference_type"], params.get("hydrate_lookup")
        if not binding:
            continue
        contract = dict(context["lookups"]["component_contract"][binding], binding=binding,
                        description_required=bool(params.get("description_required")))
        if contracts.setdefault(kind, contract) != contract:
            raise ValueError("Reference type has contradictory hydration contracts")
        fields[row["SOURCE_FIELD_NAME"]] = kind
    if not fields:
        return {}
    ids, types = {kind: set() for kind in contracts}, {}
    for record in source_df.to_local_iterator():
        source = _metadata_parse(record, context)
        for field, kind in fields.items():
            value = resolve_json_path(source, field)
            if not _has_value(value):
                continue
            if not isinstance(value, list):
                raise ValueError("Approved component reference root must be an array")
            for identifier in _component_reference_content_ids(value):
                if types.setdefault(identifier, kind) != kind:
                    raise ValueError("Component hydration identity has a type collision")
                ids[kind].add(identifier)
    lookups = {}
    for kind, contract in contracts.items():
        frame = source_dfs[contract["binding"]]
        columns = {str(name).strip('"').upper(): name for name in frame.columns}
        identifier_col = F.trim(F.col(columns["CONTENT_ID"]).cast("string"))
        identifiers, found = sorted(ids[kind]), {}
        for start in range(0, len(identifiers), 1000):
            batch = frame.filter(identifier_col.isin(identifiers[start:start + 1000])).select(
                identifier_col.alias("CONTENT_ID"), F.col(columns["CURATED_JSON"]).alias("CURATED_JSON"))
            for record in batch.to_local_iterator():
                identifier = record["CONTENT_ID"]
                if identifier in found:
                    raise ValueError("Component lookup contains duplicate ContentId values")
                payload = _metadata_parse(record, context)
                found[identifier] = {
                    "title": _component_text(resolve_json_path(payload, contract["title_field"]), "title", True),
                    "description": _component_text(resolve_json_path(payload, contract["description_field"]),
                                                   "description", contract["description_required"]),
                }
        if found.keys() != ids[kind]:
            raise ValueError("Component hydration lookup record is missing")
        lookups[kind] = found
    return lookups


def _joined_variant_value(value, context):
    """Decode scalar/object/array VARIANT values returned by Snowpark projection."""
    value = _to_python(value)
    if isinstance(value, str):
        try:
            return (json.loads(value, parse_float=Decimal)
                    if context["compiled_plan"].get("options", {}).get("parse_decimal", True)
                    else json.loads(value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return value
    return value


def _build_joined_record_lookups(source_df, mapping_rows, context):
    """Project only mapped child fields before streaming joined records to Python."""
    from snowflake.snowpark import functions as F

    rows_by_binding = {}
    for row in mapping_rows:
        params = _metadata_params(row)
        binding = params.get("joined_lookup")
        if not binding:
            raise ValueError("Joined-record mapping requires LOOKUP_KEY")
        rows_by_binding.setdefault(binding, []).append(row)

    source_ids = source_df.select(
        F.trim(F.col("SOURCE_RECORD_ID").cast("string")).alias("_JOIN_ID")
    ).distinct()

    result = {}
    for binding, binding_rows in rows_by_binding.items():
        frame = context["lookups"].get("joined_sources", {}).get(binding)
        if frame is None:
            raise ValueError("Joined-record lookup source is unavailable: " + binding)

        columns = {str(name).strip('"').upper(): name for name in frame.columns}
        if not {"CONTENT_ID", "CURATED_JSON", "_SOURCE_RECORD_ID"}.issubset(columns):
            raise ValueError("Joined-record lookup requires parent, child identity, and CURATED_JSON")

        owner_paths = {row["OWNER_ELEMENT_PATH"] for row in binding_rows}
        if len(owner_paths) != 1:
            raise ValueError("Joined-record lookup binding must belong to one collection path")
        owner_path = next(iter(owner_paths))
        parameters = context["compiled_plan"]["elements"][owner_path]["parameters"]
        identity_field = parameters.get("joined_instance_field")
        if not identity_field:
            raise ValueError("Joined-record collection requires a registry identity field")

        required_fields = [identity_field]
        for row in binding_rows:
            field = row["SOURCE_FIELD_NAME"]
            if field not in required_fields:
                required_fields.append(field)

        json_col = F.col(columns["CURATED_JSON"])
        projected = [
            F.trim(F.col(columns["CONTENT_ID"]).cast("string")).alias("_JOIN_ID"),
            F.col(columns["_SOURCE_RECORD_ID"]).cast("string").alias("_SOURCE_RECORD_ID"),
        ]
        for field in required_fields:
            projected.append(F.get(json_col, F.lit(field)).alias(field))

        joined = frame.select(*projected).join(source_ids, "_JOIN_ID", "inner")

        by_parent = {}
        for record in joined.to_local_iterator():
            parent_id = str(record["_JOIN_ID"]).strip()
            payload = {}
            for field in required_fields:
                raw = _to_python(record[field])
                # Preserve the joined child identity exactly as the first accepted
                # Level-355 batch saw it. Decode mapped payload fields separately.
                payload[field] = raw if field == identity_field else _joined_variant_value(raw, context)
            source_record_id = _scalar_text(record["_SOURCE_RECORD_ID"],
                                            "Joined source identity must be scalar",
                                            "Joined source identity must be nonblank")
            by_parent.setdefault(parent_id, []).append({
                "source_record_id": source_record_id, "payload": payload})

        result[binding] = by_parent

    return result


def _metadata_joined_record_instances(source_id, rows, parameters, context):
    bindings = {_metadata_params(row).get("joined_lookup") for row in rows}
    if len(bindings) != 1 or None in bindings:
        raise ValueError("Joined-record collection requires exactly one lookup binding")
    binding = next(iter(bindings))
    children = context.get("joined_record_lookups", {}).get(binding, {}).get(source_id, ())
    identity_field = parameters.get("joined_instance_field")
    if not identity_field:
        raise ValueError("Joined-record collection requires a registry identity field")
    contract = context["lookups"]["joined_contract"][binding]
    instances = []
    for record in children:
        child = record["payload"]
        identity = resolve_json_path(child, identity_field, default=SKIP_VALUE)
        if identity is SKIP_VALUE:
            raise ValueError("Joined-record identity field is absent")
        key = _scalar_text(identity, "Joined-record identity must be scalar",
                           "Joined-record identity must be nonblank")
        origin = {"source_system": context["config"]["SOURCE_SYSTEM_NAME"],
                  "source_table": contract["source_table"],
                  "source_record_id": record["source_record_id"]}
        payload, crosswalks, contributions = {}, [], []
        for row in rows:
            value = _metadata_mapped_value(row, child, context)
            if value is SKIP_VALUE:
                continue
            if row["TRANSFORM_ID"] == "status-crosswalk":
                crosswalks.append((row, value))
            else:
                _assign_mapped(payload, row, _metadata_target(row), value, contributions, context, origin)
        for row, members in crosswalks:
            for member, value in members.items():
                _assign_mapped(payload, row, member, value, contributions, context, origin,
                               preserve_existing=member == "remarks")
        if any(not _has_value(_metadata_get(payload, member))
               for member in parameters.get("required_members", ())):
            context["graph_report"]["SKIPPED_JOINED_RECORDS"] = context["graph_report"].get("SKIPPED_JOINED_RECORDS", 0) + 1
            continue
        _append_unique_collection_instance(instances, {
            "instance_key": key, "payload": payload,
            "parent_instance_key": _metadata_parent_key(parameters, source_id),
            "contributions": contributions})
    return instances


def _metadata_party_uuid(group, source_record_id, identifier, context):
    # Cell 3 permits one source namespace per linked model; preserve its accepted seed.
    return _deterministic_uuid(context["config"]["SOURCE_SYSTEM_NAME"], source_record_id, "party", identifier)


def _metadata_party_instances(path, source_obj, source_id, operator, parameters, context):
    group = next(group for group in context["compiled_plan"]["reference_groups"]
                 if path in (group["roles_path"], group["parties_path"], group["assignments_path"]))
    cache = context.setdefault("_metadata_reference_cache", {})
    if group["assignments_path"] not in cache:
        roles, parties, assignments, contributors = {}, {}, {}, {}
        for row in context["mappings_by_path"].get(group["assignments_path"], ()):
            value = _metadata_mapped_value(row, source_obj, context)
            if value is SKIP_VALUE:
                continue
            # An explicitly empty user/group selection is absence, not a person.
            # Do not hide null, malformed, or populated unresolved references.
            if (isinstance(value, dict) and {"UserList", "GroupList"}.intersection(value)
                    and value.get("UserList", []) == [] and value.get("GroupList", []) == []):
                continue
            params, extracted = _metadata_params(row), _extract_reference_ids(value)
            members = extracted if isinstance(extracted, list) else [extracted]
            party_ids = {}
            for item in members:
                if item is None:
                    continue
                identifier = _party_reference_identifier(item)
                party_uuid = _metadata_party_uuid(group, source_id, identifier, context)
                candidate = _party_payload(item, party_uuid, group["party_type"], context)
                parties[party_uuid] = (
                    _merge_party_payload(parties[party_uuid], candidate)
                    if party_uuid in parties else candidate
                )
                party_ids.setdefault(party_uuid, None)
            if not party_ids:
                continue
            role, title = params["role_id"], params["role_title"]
            if roles.setdefault(role, title) != title:
                raise ValueError("Role identity resolves to conflicting titles")
            field, references = assignments.setdefault(role, (row["SOURCE_FIELD_NAME"], {}))
            references.update(party_ids)
            _capture_contribution(contributors.setdefault(role, []), row, "party-uuids", context)
        cache[group["assignments_path"]] = {
            "roles": [(key, {"id": key, "title": title}) for key, title in roles.items()],
            "parties": [(key, payload) for key, payload in parties.items()],
            "assignments": [(field, {"role-id": role, "party-uuids": list(references)})
                            for role, (field, references) in assignments.items()],
            "contributions": contributors,
        }
    family = cache[group["assignments_path"]]
    return [{"instance_key": key, "payload": payload,
             "contributions": family["contributions"].get(payload.get("role-id"), []) if operator == "assignments" else [],
             "parent_instance_key": _metadata_parent_key(parameters, source_id)}
            for key, payload in family[operator]]


def _metadata_reference_instances(source_obj, source_id, rows, parameters, context):
    references, contributors = {}, {}
    for row in rows:
        value, params = _metadata_mapped_value(row, source_obj, context), _metadata_params(row)
        if value is SKIP_VALUE:
            continue
        for identifier in _component_reference_content_ids(value):
            _capture_contribution(contributors.setdefault(identifier, []), row, "", context)
            previous = references.get(identifier)
            if previous and previous["reference_type"] != params["reference_type"]:
                raise ValueError("Referenced identity has contradictory types")
            if previous is None or params.get("hydrate_lookup"):
                references[identifier] = params
    result = []
    for identifier, params in sorted(references.items()):
        payload = {"type": params["reference_type"]} if params["reference_type"] else {}
        if params.get("hydrate_lookup"):
            hydrated = context["component_hydration_lookups"][params["reference_type"]][identifier]
            payload["title"] = hydrated["title"]
            if hydrated["description"] is not None:
                payload["description"] = hydrated["description"]
        result.append({"instance_key": identifier, "payload": payload,
                       "contributions": contributors.get(identifier, []),
                       "parent_instance_key": _metadata_parent_key(parameters, source_id)})
    return result


def _metadata_descendant_has_value(path, source_obj, context):
    prefix = path + "."
    for mapped_path, rows in context["mappings_by_path"].items():
        if mapped_path != path and not mapped_path.startswith(prefix):
            continue
        for row in rows:
            params = _metadata_params(row)
            raw = (context["config"].get(row["SOURCE_FIELD_NAME"], SKIP_VALUE)
                   if params.get("value_source") == "CONFIG"
                   else resolve_json_path(source_obj, row["SOURCE_FIELD_NAME"], default=SKIP_VALUE))
            if raw is not SKIP_VALUE and _has_value(raw):
                return True
    return False


def _metadata_instances(source_obj, source_id, registry_row, context):
    path = registry_row["element_path"]
    specification = context["compiled_plan"]["elements"].get(path)
    if specification is None:
        return []
    operator, parameters = specification["operator"], specification["parameters"]
    rows, parent = context["mappings_by_path"].get(path, ()), _metadata_parent_key(parameters, source_id)
    if operator in {"roles", "parties", "assignments"}:
        return _metadata_party_instances(path, source_obj, source_id, operator, parameters, context)
    if operator == "references":
        return _metadata_reference_instances(source_obj, source_id, rows, parameters, context)
    if operator == "joined-records":
        return _metadata_joined_record_instances(source_id, rows, parameters, context)
    payload, instances, crosswalks, contributions = {}, [], [], []
    for row in rows:
        value = _metadata_mapped_value(row, source_obj, context)
        if value is SKIP_VALUE:
            continue
        field, target = row["SOURCE_FIELD_NAME"], _metadata_target(row)
        if operator in {"properties", "observations"}:
            values = [None] if value is None else _oscal_property_values(value)
            field_identity = (operator == "observations" or
                              parameters["registry_contract"].get("instance_key_rule") == "SOURCE_FIELD_NAME")
            if field_identity and len(values) != 1:
                raise ValueError("One scalar value is required per field identity")
            for item in values:
                property_name = _metadata_params(row).get("property_name") or _stable_property_name(field)
                prop = _oscal_prop(property_name, item)
                item_contributions = []
                _capture_contribution(item_contributions, row,
                                      "props.0.value" if operator == "observations" else "value", context)
                item_payload = {"props": [prop]} if operator == "observations" else prop
                key = field if field_identity else field + ":" + _deterministic_hash("source-field-value-v1", field, item)
                _append_unique_collection_instance(instances, {"instance_key": key, "payload": item_payload,
                                                               "contributions": item_contributions,
                                                               "parent_instance_key": parent})
        elif operator == "values":
            for member in (value if isinstance(value, list) else [value]):
                item_payload = copy.deepcopy(member) if isinstance(member, dict) else {}
                raw = _metadata_get(item_payload, target) if isinstance(member, dict) else member
                values = _oscal_property_values(raw)
                if len(values) != 1:
                    raise ValueError("Value identity requires exactly one scalar")
                normalized = values[0]
                cursor, tokens = item_payload, target.split(".")
                for token in tokens[:-1]:
                    cursor = cursor.setdefault(token, {})
                cursor[tokens[-1]] = normalized
                item_contributions = []
                _capture_contribution(item_contributions, row, target, context)
                _append_unique_collection_instance(instances, {"instance_key": _deterministic_hash("value-v1", normalized),
                                                               "payload": item_payload, "parent_instance_key": parent,
                                                               "contributions": item_contributions})
        elif row["TRANSFORM_ID"] == "status-crosswalk":
            crosswalks.append((row, value))
        else:
            _assign_mapped(payload, row, target, value, contributions, context)
    for row, members in crosswalks:
        for member, value in members.items():
            _assign_mapped(payload, row, member, value, contributions, context,
                           preserve_existing=member == "remarks")
    if any(not _has_value(_metadata_get(payload, member)) for member in parameters.get("required_members", ())):
        if parameters.get("optional_assembly"):
            return []
        raise ValueError("Required payload member is missing")
    if operator == "optional-record":
        if payload or _metadata_descendant_has_value(path, source_obj, context):
            instances.append({"instance_key": source_id, "payload": payload, "parent_instance_key": parent,
                              "contributions": contributions})
    elif operator in {"object", "record"} and (payload or parameters.get("materialize_empty") or operator == "record"):
        instances.append({"instance_key": source_id if operator == "record" else "singleton",
                          "payload": payload, "parent_instance_key": parent, "contributions": contributions})
    return instances


def _metadata_uuid(path, instance, source_system, source_table, source_id, model_key, context):
    if context["compiled_plan"]["elements"][path]["parameters"].get("uuid_from_instance"):
        return instance["instance_key"]
    return _deterministic_uuid(context["config"]["IDENTITY_VERSION"], source_system,
                               source_table, source_id, model_key, path, instance["instance_key"])


def _metadata_payload(path, payload, node_uuid, context):
    if context["compiled_plan"]["elements"][path]["parameters"].get("include_uuid"):
        if payload.get("uuid") not in (None, "", node_uuid):
            raise ValueError("Payload UUID conflicts with node UUID")
        return dict(payload, uuid=node_uuid)
    return payload


def _metadata_record_complete(nodes_by_path, context):
    # Linked collections were built together from the same role/party sets.
    context.pop("_metadata_reference_cache", None)


def _element_type(path):
    return path.rsplit(".", 1)[-1].replace("[]", "")


def _canonical_registry_rows(element_registry_df, model_key, context):
    rows = []
    for row in context["registry_rows"]:
        path = _registry_path(row)
        rows.append({"element_path": path, "element_type": row.get("ELEMENT_TYPE") or _element_type(path),
                     "parent_path": row.get("PARENT_NODE_PATH") or None, "level": path.count(".") + 1,
                     "process_order": row.get("PROCESS_ORDER"), "is_collection": _registry_meta_bool(row, "IS_COLLECTION")})
    return sorted(rows, key=lambda row: (row["level"], row["process_order"] if row["process_order"] is not None else 0,
                                         row["element_path"]))


def _metadata_parse(record, context):
    value, options = _to_python(record["CURATED_JSON"]), context["compiled_plan"].get("options", {})
    if value is None and options.get("null_source_as_empty", False):
        return {}
    if isinstance(value, str):
        value = json.loads(value, parse_float=Decimal) if options.get("parse_decimal", True) else json.loads(value)
    if not isinstance(value, dict):
        raise ValueError("Source JSON must resolve to an object")
    return value


def _prepare_model_context(context, model_key, source_system, source_table):
    if context["compiled_plan"].get("release") != "lean-csv-registry-v6-lineage-required":
        raise ValueError("Run the matching lean Cell 3 before building the graph")
    config = context["config"]
    config["LINEAGE_GAP_COUNT"] = 0
    if (config["OSCAL_MODEL"], config["SOURCE_SYSTEM_NAME"], config["SOURCE_TABLE_NAME"]) != (model_key, source_system, source_table):
        raise ValueError("Graph arguments conflict with compiled metadata context")
    context.pop("_metadata_reference_cache", None)
    context["graph_report"] = {"SOURCE_RECORDS": 0, "INVALID_SOURCE_RECORDS": 0, "DUPLICATE_SOURCE_RECORDS": 0,
                               "MAPPED_VALUES": 0, "MISSING_VALUES": 0, "STATUS": "NOT_RUN", "OUTPUTS_PUBLISHED": False,
                               "LINEAGE_PROPS": 0, "LINEAGE_GAPS": 0, "LINEAGE_GAP_SAMPLES": []}
    return context


def _metadata_prepare(source_df, context):
    plan = context["compiled_plan"]
    references = [row for row in plan["mappings"] if row["TRANSFORM_ID"] != "skip"
                  and plan["elements"][row["OWNER_ELEMENT_PATH"]]["operator"] == "references"]
    joined_records = [row for row in plan["mappings"] if row["TRANSFORM_ID"] != "skip"
                      and plan["elements"][row["OWNER_ELEMENT_PATH"]]["operator"] == "joined-records"]
    context["component_hydration_lookups"] = _build_component_hydration_lookups(
        source_df, references, context["lookups"].get("component_sources", {}), context) if references else {}
    context["joined_record_lookups"] = _build_joined_record_lookups(
        source_df, joined_records, context) if joined_records else {}


def _metadata_finish(nodes, edges, context):
    report = context["graph_report"]
    if not report["SOURCE_RECORDS"] or report["INVALID_SOURCE_RECORDS"] or report["DUPLICATE_SOURCE_RECORDS"]:
        report["STATUS"] = "BLOCKED"
        raise ValueError("Source is empty or contains invalid or duplicate record identities")
    report.update(STATUS="MAPPED_SCOPE_BUILT", OUTPUTS_PUBLISHED=True, NODES=len(nodes), EDGES=len(edges),
                  DOCUMENTS=report["SOURCE_RECORDS"], FULL_MODEL_COMPLETE=False, SCHEMA_VALIDATED=False,
                  LINEAGE_COMPLETE=report["LINEAGE_GAPS"] == 0)


print("Cell 4 transforms and registry operators ready")

_metadata_instances._oscal_mapper_release = "lean-csv-registry-v6-lineage-required"
