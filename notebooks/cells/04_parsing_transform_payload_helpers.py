# %% Cell 4 - Shared metadata runtime and reusable transformations

import datetime
import hashlib
import json
import math
import re
import uuid
from decimal import Decimal

# Cell 3 owns the shared compiled-plan boundary.
try:
    _validate_compiled_metadata
    _metadata_plan_snapshot
except NameError:
    raise RuntimeError("Run the matching Cell 3 before Cell 4") from None
if not (_metadata_plan_snapshot({}) or b"").startswith(b"csv-registry-v2\0"):
    raise RuntimeError("Run the matching Cell 3 before Cell 4")

SKIP_VALUE = object()

ARCHER_SELECT_ID_CONTAINER_KEYS = {
    "valuelistid",
    "valuelistids",
    "valueslistid",
    "valueslistids",
}

# Shared source adapters, scalar transforms, identity and hydration query backend.

def _context_config(context=None):
    if not isinstance(context, dict) or not isinstance(context.get("config"), dict):
        raise ValueError("An explicit source/model context is required")
    return context["config"]


def _context_lookup(name, context=None):
    if not isinstance(context, dict):
        raise ValueError("An explicit source/model lookup context is required")
    return context.get("lookups", {}).get(name, {})


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
    value_lookup = _context_lookup("archer_values", context)
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


def _scalar_text(value, shape_error, value_error, allow_bool=False):
    """Canonical scalar text shared by properties and external identifiers."""
    value = _to_python(value)
    if value is None or isinstance(value, (dict, list)) or (isinstance(value, bool) and not allow_bool):
        raise ValueError(shape_error)
    if isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value).strip()
    if not text or text.lower() in {"nan", "inf", "+inf", "-inf"}:
        raise ValueError(value_error)
    return text


def _oscal_property_values(value):
    values = value if isinstance(value, list) else [value]
    return [_scalar_text(item, "OSCAL property value must resolve to a scalar",
                         "OSCAL property value must be a nonblank finite scalar", allow_bool=True)
            for item in values]


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


def _canonical_component_content_id(value):
    message = "Component reference has invalid ContentId"
    return _scalar_text(value, message, message)


def _component_reference_content_ids(value):
    value = _to_python(value)
    members = value if isinstance(value, list) else [value]
    content_ids = []
    for member in members:
        member = _to_python(member)
        if isinstance(member, dict):
            if "ContentId" not in member:
                raise ValueError("Component reference is missing ContentId")
            member = member["ContentId"]
        content_ids.append(_canonical_component_content_id(member))
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


def _build_component_hydration_lookups(
    source_dataframe, mapping_rows, hydration_source_dfs, context=None,
):
    """Validate reference routes, join their lookup rows, and collect only the payloads."""
    if not isinstance(context, dict):
        raise RuntimeError("A compiled reference hydration context is required")
    contracts, source_types, fields_to_hydrate = {}, {}, {}
    duplicate_fields = False
    declared_lookups = context.get("lookups", {}).get("component_contract") or {}
    for row in mapping_rows:
        params = _metadata_params(row)
        type_name = _metadata_text(params.get("reference_type"), "Reference type")
        field = row["SOURCE_FIELD_NAME"]
        if field in source_types:
            if source_types[field] != type_name:
                raise ValueError("Source reference has conflicting type declarations")
            duplicate_fields = True
        source_types[field] = type_name
        binding = params.get("hydrate_lookup")
        if not binding:
            continue
        contract = declared_lookups.get(binding)
        if not isinstance(contract, dict):
            raise ValueError("Reviewed reference lookup source is absent")
        contract = dict(contract, lookup_binding=binding,
                        description_required=bool(params.get("description_required", False)))
        if type_name in contracts and contracts[type_name] != contract:
            raise ValueError("Reference type has contradictory hydration contracts")
        contracts[type_name] = contract
        fields_to_hydrate[field] = type_name
    if not fields_to_hydrate:
        return {}
    if duplicate_fields:
        raise RuntimeError("Canonical component mapping is duplicated")
    if _context_config(context).get("EXECUTE_WRITES", False):
        raise RuntimeError("Component hydration must be built before guarded writes")
    if not isinstance(hydration_source_dfs, dict):
        raise ValueError("Reference lookup dataframes are unavailable")
    if any(contract["lookup_binding"] not in hydration_source_dfs for contract in contracts.values()):
        raise ValueError("Reference lookup dataframe binding is missing")

    from snowflake.snowpark import functions as F

    def kind(value):
        return F.upper(F.typeof(value))

    def nonblank(value):
        return value.is_not_null() & (F.length(F.trim(value.cast("string"))) > F.lit(0))

    def checked_count(frame, checks, unique_key=None):
        # Each condition identifies invalid rows; collect one aggregate, never source JSON.
        aggregates = [F.count(F.lit(1)).alias("_TOTAL")]
        for index, (condition, message) in enumerate(checks):
            aggregates.append(F.count(F.when(condition, F.lit(1))).alias(f"_INVALID_{index}"))
        if unique_key is not None:
            aggregates.append(F.count_distinct(unique_key).alias("_UNIQUE"))
        summary = frame.agg(*aggregates).collect()[0]
        for index, (condition, message) in enumerate(checks):
            if _component_row_value(summary, f"_INVALID_{index}"):
                raise RuntimeError(message)
        total = int(_component_row_value(summary, "_TOTAL") or 0)
        if unique_key is not None and total != int(_component_row_value(summary, "_UNIQUE") or 0):
            raise RuntimeError("Approved component lookup contains duplicate ContentId values")
        return total

    source_columns = {str(name).strip().upper(): name for name in source_dataframe.columns}
    if not {"SOURCE_RECORD_ID", "CURATED_JSON"}.issubset(source_columns):
        raise RuntimeError("Component hydration source columns are missing")
    source_json = F.parse_json(F.col(source_columns["CURATED_JSON"]).cast("string"))
    scalar_types = ("VARCHAR", "INTEGER", "DECIMAL", "NUMBER", "FIXED", "REAL", "DOUBLE")
    routes = None
    for field, component_type in fields_to_hydrate.items():
        roots = source_dataframe.select(
            F.lit(component_type).alias("_COMPONENT_TYPE"),
            source_json.getItem(field).alias("_REFERENCE_ROOT"),
        )
        root = F.col("_REFERENCE_ROOT")
        if roots.filter(root.is_not_null() & ~kind(root).isin("ARRAY", "NULL_VALUE")).count():
            raise RuntimeError("Approved component reference root has invalid shape")
        members = roots.filter(kind(root) == F.lit("ARRAY")).join_table_function("flatten", root)
        member = F.col("VALUE")
        content_id = member.getItem("ContentId")
        member_id = (
            F.when((kind(member) == F.lit("OBJECT")) & kind(content_id).isin(*scalar_types), content_id)
            .when(kind(member).isin(*scalar_types), member)
            .otherwise(F.lit(None))
        )
        ids = members.select(
            F.col("_COMPONENT_TYPE"), F.trim(member_id.cast("string")).alias("_COMPONENT_ID"),
        )
        if ids.filter(~nonblank(F.col("_COMPONENT_ID"))).count():
            raise RuntimeError("Approved component reference contains an invalid ContentId")
        routes = ids if routes is None else routes.union_all(ids)
    collisions = (routes.distinct().group_by(F.col("_COMPONENT_ID"))
                  .agg(F.count_distinct(F.col("_COMPONENT_TYPE")).alias("_TYPE_COUNT")))
    if collisions.filter(F.col("_TYPE_COUNT") > F.lit(1)).count():
        raise RuntimeError("Component hydration identity has a type collision")

    lookups = {}
    for component_type, contract in contracts.items():
        routed_ids = (routes.filter(F.col("_COMPONENT_TYPE") == F.lit(component_type))
                      .select(F.col("_COMPONENT_ID").alias("_ROUTE_ID")).distinct())
        lookup_source = hydration_source_dfs[contract["lookup_binding"]]
        columns = {str(name).strip().upper(): name for name in lookup_source.columns}
        if not {"CONTENT_ID", "CURATED_JSON"}.issubset(columns):
            raise RuntimeError("Approved component lookup source columns are missing")
        lookup_rows = lookup_source.select(
            F.trim(F.col(columns["CONTENT_ID"]).cast("string")).alias("_LOOKUP_ID"),
            F.parse_json(F.col(columns["CURATED_JSON"]).cast("string")).alias("_LOOKUP_JSON"),
        )
        lookup_id, lookup_json = F.col("_LOOKUP_ID"), F.col("_LOOKUP_JSON")
        # Validate the full approved lookup source, including currently unreferenced rows.
        checked_count(lookup_rows, [
            (~nonblank(lookup_id), "Approved component lookup contains a missing ContentId"),
            (kind(lookup_json) != F.lit("OBJECT"), "Approved component lookup contains invalid curated JSON"),
        ], unique_key=lookup_id)
        matched = routed_ids.join(lookup_rows, routed_ids["_ROUTE_ID"] == lookup_rows["_LOOKUP_ID"], "left")
        title = lookup_json.getItem(contract["title_field"])
        description = lookup_json.getItem(contract["description_field"])
        title_valid = (kind(title) == F.lit("VARCHAR")) & nonblank(title)
        description_text = kind(description) == F.lit("VARCHAR")
        description_nonblank = description_text & nonblank(description)
        description_absent = description.is_null() | (kind(description) == F.lit("NULL_VALUE"))
        description_valid = description_nonblank
        if not contract.get("description_required"):
            description_valid = description_absent | description_text
        routed_count = checked_count(matched, [
            (lookup_id.is_null(), "Approved component hydration lookup record is missing"),
            (~title_valid, "Approved component hydration title is missing or invalid"),
            (~description_valid, "Approved component hydration description is invalid"),
        ])
        projected = matched.select(
            F.col("_ROUTE_ID").alias("COMPONENT_ID"),
            F.trim(title.cast("string")).alias("TITLE"),
            F.when(description_nonblank, F.trim(description.cast("string")))
             .otherwise(F.lit(None)).alias("DESCRIPTION"),
        )
        type_lookup = {}
        for row in projected.to_local_iterator():
            content_id = _canonical_component_content_id(_component_row_value(row, "COMPONENT_ID"))
            if content_id in type_lookup:
                raise RuntimeError("Component hydration lookup contains duplicate routed IDs")
            type_lookup[content_id] = {
                "title": _component_row_value(row, "TITLE"),
                "description": _component_row_value(row, "DESCRIPTION"),
            }
        if len(type_lookup) != routed_count:
            raise RuntimeError("Component hydration lookup collection is incomplete")
        lookups[component_type] = type_lookup

    print("Component hydration lookup rows:", sum(map(len, lookups.values())))
    for component_type in sorted(lookups):
        payloads = lookups[component_type]
        print(f"Component hydration {component_type} rows:", len(payloads))
        print(f"Component hydration {component_type} descriptions:",
              sum(payload.get("description") is not None for payload in payloads.values()))
    return lookups


def transform_fips_199(value, context=None):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    normalized = []
    for item in values:
        if item is None:
            continue
        key = str(item).strip()
        label = _context_lookup("fips_values", context).get(key)
        if label is None:
            candidate = str(_context_lookup("archer_values", context).get(key, item)).strip().lower()
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

    resolved = _context_lookup("archer_values", context).get(key)
    if resolved is not None:
        label = str(resolved).strip()
        return label or None

    # An already resolved textual label is safe to preserve. An unknown
    # numeric ID is not: it must be added to ARCHER_META_VALUE first.
    if isinstance(item, str) and not key.isdigit():
        return key
    return None


def transform_document_identifier(value):
    return _scalar_text(value, "Document identifier must be a single scalar value",
                        "Document identifier is empty or non-finite")


def transform_authorization_date(value):
    # Reusable timestamp-to-date operation: retain the source calendar date.
    # Field selection and approved target placement belong to compiled metadata.
    value = _to_python(value)
    if not _has_value(value):
        return SKIP_VALUE
    error_message = (
        "Date conversion requires a valid ISO date or ISO timestamp "
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


def _element_type(element_path):
    return element_path.split(".")[-1].replace("[]", "")


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


def _canonical_registry_rows(element_registry_dataframe, model_key, context=None):
    # Cell 3 is the sole transport-normalization and registry-validation
    # boundary. Cell 4 only adapts that compiled contract to graph row names.
    del element_registry_dataframe, model_key
    if not isinstance(context, dict) or not isinstance(context.get("compiled_plan"), dict):
        raise ValueError("Compiled metadata context is required for registry validation")
    normalized_rows = context.get("registry_rows")
    if normalized_rows is None:
        raise ValueError("Compiled metadata context requires normalized registry rows")

    rows = []
    for registry_row in normalized_rows:
        path = _registry_path(registry_row)
        level = path.count(".") + 1
        process_order = registry_row.get("PROCESS_ORDER")
        rows.append({
            "element_path": path,
            "element_type": registry_row.get("ELEMENT_TYPE"),
            "raw": registry_row,
            "parent_path": registry_row.get("PARENT_NODE_PATH") or None,
            "level": level,
            "process_order": int(process_order) if process_order is not None else level * 1000000,
            "is_collection": _registry_meta_bool(registry_row, "IS_COLLECTION"),
            "instance_key_rule": registry_row.get("INSTANCE_KEY_RULE") or None,
            "item_path": registry_row.get("ITEM_PATH") or None,
        })
    _metadata_registry_policy(rows, context)
    rows.sort(key=lambda row: (row["process_order"], row["level"], row["element_path"]))

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


def _metadata_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be nonblank text")
    return value


def _metadata_transform(row, value, context):
    transform_id = row["TRANSFORM_ID"]
    params = row.get("TRANSFORM_PARAMS") or {}
    if transform_id == "skip":
        return SKIP_VALUE
    if not _has_value(value):
        if _metadata_params(row).get("required"):
            raise ValueError("Required mapped source value is absent")
        return SKIP_VALUE
    if transform_id == "direct":
        return _to_python(value)
    if transform_id in {"text", "timestamp"}:
        return _metadata_text(_to_python(value), "Mapped value")
    if transform_id == "canonical-text":
        value = _metadata_text(_to_python(value), "Controlled value")
        if value != value.strip():
            raise ValueError("Controlled value must be canonical text")
        return value
    if transform_id == "date":
        try:
            return transform_authorization_date(value)
        except (TypeError, ValueError, ArithmeticError):
            raise ValueError("Mapped date requires a valid ISO date or timestamp") from None
    if transform_id == "identifier":
        return transform_document_identifier(value)
    if transform_id == "archer-select":
        result = resolve_archer_select_value(value, context)
        return result if _has_value(result) else SKIP_VALUE
    if transform_id == "scalar-score":
        value = _score_value(value, context)
        return value if value is not None else SKIP_VALUE
    if transform_id == "security-objective":
        result = transform_fips_199(value, context)
        if isinstance(result, list):
            if len(result) != 1:
                raise ValueError("Security objective resolved to multiple values")
            result = result[0]
        if _has_value(result):
            return str(result)
        label = _single_archer_label(value, context)
        if label is None or label not in params.get("approved_legacy_values", ()):
            raise ValueError("Security objective contains an unreviewed label")
        return label
    if transform_id == "status-crosswalk":
        label = _single_archer_label(value, context)
        if label is None:
            raise ValueError("Crosswalk source label is unresolved or multivalued")
        crosswalk = params.get("crosswalk")
        if not isinstance(crosswalk, dict):
            raise ValueError("Crosswalk metadata is missing")
        target = crosswalk.get(_stable_property_name(label))
        if target is None:
            raise ValueError("Label is absent from reviewed crosswalk")
        payload = {"state": target}
        if target == "other":
            prefix = params.get("other_remarks_prefix")
            if not isinstance(prefix, str):
                raise ValueError("Crosswalk fallback explanation is not configured")
            payload["remarks"] = prefix + label + params.get("other_remarks_suffix", ".")
        return payload
    if transform_id == "reject-populated":
        raise ValueError("Populated source has no reviewed transformation")
    raise ValueError("Unsupported metadata transform")


def _metadata_assign(payload, target, value, preserve_existing=False):
    target = _metadata_text(target, "Payload member")
    tokens = target.split(".")
    if any(not token or "[" in token or "]" in token for token in tokens):
        raise ValueError("Nested collections require explicit registry ownership")
    current = payload
    for token in tokens[:-1]:
        if token not in current:
            current[token] = {}
        if not isinstance(current[token], dict):
            raise ValueError("Nested payload member conflicts with scalar")
        current = current[token]
    member = tokens[-1]
    if member in current and current[member] != value:
        if preserve_existing:
            return
        raise ValueError("Singleton target has conflicting populated mappings")
    current[member] = value


def _metadata_get(payload, target):
    current = payload
    for token in str(target).split("."):
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def _metadata_parent_key(parameters, source_record_id):
    rule = parameters.get("parent_instance_rule")
    if rule in (None, "none"):
        return None
    if rule == "singleton":
        return "singleton"
    if rule == "source-record":
        return source_record_id
    raise ValueError("Unsupported metadata parent-instance rule")


def _metadata_property_name(row, parameters):
    if parameters.get("property_name_rule") != "source-field-slug":
        raise ValueError("Reviewed property name requires the registry naming policy")
    return _metadata_text(_stable_property_name(row["SOURCE_FIELD_NAME"]), "Reviewed property name")


def _metadata_registry_policy(rows, context):
    by_path = {row["element_path"]: row for row in rows}
    plan = context["compiled_plan"]
    if not set(plan["elements"]).issubset(by_path):
        raise ValueError("Metadata plan names an unregistered element")
    for path, row in by_path.items():
        specification = plan["elements"].get(path)
        if specification is None:
            continue
        parameters = specification.get("parameters") or {}
        expected = parameters.get("registry_contract") or {}
        for key in ("parent_path", "is_collection", "instance_key_rule", "item_path"):
            if key in expected and row.get(key) != expected[key]:
                raise ValueError("Registry identity contradicts reviewed metadata")
        if row["parent_path"] and row["parent_path"] not in by_path:
            raise ValueError("Registry parent is absent")
        operator = specification["operator"]
        if operator in METADATA_INSTANCE_RULES and not row["is_collection"]:
            raise ValueError("Collection representation requires collection registry row")
        # Linked families validate their established registry contract above.
        if operator not in {"roles", "parties", "assignments"} and operator in METADATA_INSTANCE_RULES and (
                row["instance_key_rule"] != METADATA_INSTANCE_RULES[operator]):
            raise ValueError(f"Collection requires {METADATA_INSTANCE_RULES[operator]} identity")
    for group in plan.get("reference_groups", ()):
        paths = [group.get(key) for key in ("roles_path", "parties_path", "assignments_path")]
        if any(path not in by_path for path in paths) or len(set(paths)) != 3:
            raise ValueError("Reference group requires distinct governed collection paths")
        if len({by_path[path]["parent_path"] for path in paths}) != 1:
            raise ValueError("Reference group collections must share the reviewed parent")
    return rows


def _metadata_prepare(source_df, context):
    plan = context["compiled_plan"]
    fields = list(dict.fromkeys(row["SOURCE_FIELD_NAME"] for row in plan["mappings"]
                               if row["TRANSFORM_ID"] != "skip"))
    report = context["graph_report"]
    report.update(MODEL=context["config"]["OSCAL_MODEL"], SELECTED_FIELDS=fields,
                  FIELDS={field: {"emitted": 0, "missing": 0, "invalid": 0} for field in fields},
                  WRITES_EXECUTED=False, FULL_MODEL_COMPLETE=False, SCHEMA_VALIDATED=False,
                  MAPPING_CONTRACT_ERRORS=[], REGISTRY_CONTRACT_ERRORS=[],
                  MAPPING_ROWS_NOT_PROCESSED=0)
    descriptive = plan.get("report") or {}
    allowed_report_keys = {"MAPPING_RELEASE", "REPRESENTATION", "TARGET_PATH"}
    if set(descriptive) - allowed_report_keys:
        raise ValueError("Metadata report cannot override runtime safety evidence")
    report.update(descriptive)
    reference_rows = [
        row for row in plan["mappings"]
        if plan["elements"][row["OWNER_ELEMENT_PATH"]]["operator"] == "references"
        and row["TRANSFORM_ID"] != "skip"
    ]
    if reference_rows:
        context["component_hydration_lookups"] = _build_component_hydration_lookups(
            source_df, reference_rows, context.get("lookups", {}).get("component_sources"), context,
        )


def _metadata_parse(record, context):
    value = _to_python(record["CURATED_JSON"])
    options = context["compiled_plan"].get("options") or {}
    if value is None and options.get("null_source_as_empty", False):
        return {}
    if isinstance(value, str):
        value = json.loads(value, parse_float=Decimal) if options.get("parse_decimal", True) else json.loads(value)
    if not isinstance(value, dict):
        raise ValueError("Source JSON must resolve to an object")
    return value


def _metadata_validate_value(value, rules):
    """Check converted values, without coercion, source-name branches or value logging."""
    if not rules:
        return
    absent = value is SKIP_VALUE
    cardinality = rules.get("cardinality") or {}
    count = 0 if absent else len(value) if isinstance(value, list) else 1
    lower = max(cardinality.get("min", 0), 1 if rules.get("required") else 0)
    upper = cardinality.get("max")
    if absent and rules.get("null_policy") == "reject":
        raise ValueError("Mapped value is absent under reject policy")
    if count < lower or upper is not None and count > upper:
        raise ValueError("Mapped value violates cardinality")
    if absent:
        return
    validation = rules.get("validation") or {}
    # Graph JSON uses native numbers; Decimal would otherwise become a string.
    numeric = type(value) in (int, float) and (type(value) is int or math.isfinite(value))
    types = {"string": isinstance(value, str), "integer": type(value) is int,
             "number": numeric, "boolean": type(value) is bool,
             "object": isinstance(value, dict), "array": isinstance(value, list)}
    if "type" in validation and not types[validation["type"]]:
        raise ValueError("Mapped value violates declared type")
    if "enum" in validation:
        # Compare JSON representations, distinguishing nested booleans/numbers.
        # No default=str: unsupported JSON types must not silently change type.
        encoded = json.dumps(value, sort_keys=True, allow_nan=False)
        if encoded not in [json.dumps(allowed, sort_keys=True, allow_nan=False)
                           for allowed in validation["enum"]]:
            raise ValueError("Mapped value is outside approved enum")
    if "minimum" in validation or "maximum" in validation:
        if not numeric:
            raise ValueError("Numeric validation requires a finite JSON-native number")
        number = Decimal(str(value))
        if "minimum" in validation and number < Decimal(str(validation["minimum"])):
            raise ValueError("Mapped value is below approved minimum")
        if "maximum" in validation and number > Decimal(str(validation["maximum"])):
            raise ValueError("Mapped value is above approved maximum")


def _metadata_mapped_value(row, source_obj, context):
    field = row["SOURCE_FIELD_NAME"]
    counts = context["graph_report"]["FIELDS"].get(field)
    try:
        source_kind = _metadata_params(row).get("value_source", "FIELD")
        if source_kind not in {"FIELD", "CONFIG"}:
            raise ValueError("Unknown mapped value source")
        raw_value = (context["config"].get(field) if source_kind == "CONFIG"
                     else resolve_json_path(source_obj, field))
        value = _metadata_transform(row, raw_value, context)
        required = _metadata_params(row).get("required")
        if required and (value is SKIP_VALUE or not _has_value(value)):
            raise ValueError("Required mapped value is absent after conversion")
        _metadata_validate_value(value, row.get("VALUE_CONSTRAINTS") or {})
    except (TypeError, ValueError, ArithmeticError):
        if counts is not None:
            counts["invalid"] += 1
            options = context["compiled_plan"].get("options") or {}
            if options.get("aggregate_invalid", True):
                return SKIP_VALUE
        raise
    if counts is not None:
        counts["missing" if value is SKIP_VALUE else "emitted"] += 1
    return value


def _metadata_party_uuid(group, source_record_id, identifier, context):
    config = context["config"]
    namespace = {"SOURCE_SYSTEM_NAME": config["SOURCE_SYSTEM_NAME"],
                 "SOURCE_TABLE_NAME": config["SOURCE_TABLE_NAME"], "MODEL_KEY": config["OSCAL_MODEL"]}
    if group["source_namespace"] == namespace:
        return _deterministic_uuid(config["SOURCE_SYSTEM_NAME"], source_record_id, "party", identifier)
    return _deterministic_uuid(config["IDENTITY_VERSION"], config["SOURCE_SYSTEM_NAME"],
                               config["SOURCE_TABLE_NAME"], source_record_id,
                               config["OSCAL_MODEL"], "party", identifier)


def _metadata_party_instances(path, source_obj, source_record_id, operator, parameters, context):
    groups = [group for group in context["compiled_plan"].get("reference_groups", ())
              if path in (group.get("roles_path"), group.get("parties_path"), group.get("assignments_path"))]
    if len(groups) != 1:
        raise ValueError("Linked-identity element requires exactly one reference group")
    group = groups[0]
    cache = context.setdefault("_metadata_reference_cache", {})
    cache_key = (source_record_id, group["assignments_path"])
    if cache_key not in cache:
        # Index each identity once; insertion order preserves reviewed output order.
        roles, parties, assignments = {}, {}, {}
        for row in context["mappings_by_path"].get(group["assignments_path"], ()):
            params = _metadata_params(row)
            value = _metadata_mapped_value(row, source_obj, context)
            if value is SKIP_VALUE:
                continue
            extracted = _extract_reference_ids(value)
            members = extracted if isinstance(extracted, list) else [extracted]
            party_ids = dict.fromkeys(
                _metadata_party_uuid(group, source_record_id, _party_reference_identifier(member), context)
                for member in members if member is not None
            )
            if not party_ids:
                continue
            role_id = _metadata_text(params.get("role_id"), "Reviewed role identity")
            role_title = _metadata_text(params.get("role_title"), "Reviewed role title")
            if roles.setdefault(role_id, role_title) != role_title:
                raise ValueError("Collection identity resolves to conflicting payloads")
            party_type = _metadata_text(group.get("party_type"), "Reviewed party type")
            parties.update(dict.fromkeys(party_ids, party_type))
            source_field, assigned_parties = assignments.setdefault(role_id, (row["SOURCE_FIELD_NAME"], {}))
            assigned_parties.update(party_ids)
        cache[cache_key] = {
            "roles": [(key, {"id": key, "title": title}) for key, title in roles.items()],
            "parties": [(key, {"uuid": key, "type": kind}) for key, kind in parties.items()],
            "assignments": [(field, {"role-id": role, "party-uuids": list(refs)})
                            for role, (field, refs) in assignments.items()],
        }
    parent_key = _metadata_parent_key(parameters, source_record_id)
    return [{"instance_key": key, "payload": payload, "parent_instance_key": parent_key}
            for key, payload in cache[cache_key][operator]]


def _metadata_reference_instances(source_obj, source_record_id, rows, parameters, context):
    references = {}
    for row in rows:
        value = _metadata_mapped_value(row, source_obj, context)
        if value is SKIP_VALUE:
            continue
        params = _metadata_params(row)
        type_name = _metadata_text(params.get("reference_type"), "Reference type")
        for reference_id in _component_reference_content_ids(value):
            previous = references.get(reference_id)
            if previous and previous["reference_type"] != type_name:
                raise ValueError("Referenced identity has contradictory types")
            if previous is None or params.get("hydrate_lookup"):
                references[reference_id] = params
    result = []
    for reference_id in sorted(references):
        params = references[reference_id]
        type_name = params["reference_type"]
        payload = {"type": type_name}
        if params.get("hydrate_lookup"):
            lookup = context.get("component_hydration_lookups", {}).get(type_name, {})
            if reference_id not in lookup:
                raise ValueError("Referenced hydration record is unavailable")
            candidate = lookup[reference_id]
            payload["title"] = _component_text(candidate.get("title"), "title", True)
            description = _component_text(candidate.get("description"), "description",
                                          bool(params.get("description_required", False)))
            if description is not None:
                payload["description"] = description
        result.append({"instance_key": reference_id, "payload": payload,
                       "parent_instance_key": _metadata_parent_key(parameters, source_record_id)})
    return result


def _metadata_instances(source_obj, source_record_id, registry_row, context):
    path = registry_row["element_path"]
    specification = context["compiled_plan"]["elements"].get(path)
    if specification is None:
        return []
    operator = specification["operator"]
    parameters = specification.get("parameters") or {}
    rows = context["mappings_by_path"].get(path, ())
    parent = _metadata_parent_key(parameters, source_record_id)
    if operator in {"roles", "parties", "assignments"}:
        return _metadata_party_instances(path, source_obj, source_record_id,
                                         operator, parameters, context)
    if operator == "references":
        return _metadata_reference_instances(source_obj, source_record_id, rows, parameters, context)
    payload, instances, deferred_merges = {}, [], []
    for row in rows:
        value = _metadata_mapped_value(row, source_obj, context)
        if value is SKIP_VALUE:
            continue
        field = row["SOURCE_FIELD_NAME"]
        target = _metadata_target(row)
        if operator in {"properties", "observations"}:
            name = _metadata_property_name(row, parameters)
            values = _oscal_property_values(value)
            if operator == "observations" and len(values) != 1:
                raise ValueError("One scalar value is required per observation")
            for item in values:
                property_payload = {"name": name, "value": item}
                instance_payload = ({"props": [property_payload]} if operator == "observations"
                                    else property_payload)
                key = field if operator == "observations" else _source_value_instance_key(field, item)
                _append_unique_collection_instance(instances, {
                    "instance_key": key, "payload": instance_payload, "parent_instance_key": parent,
                })
            continue
        if operator == "values":
            members = value if isinstance(value, list) else [value]
            for member in members:
                item_payload = dict(member) if isinstance(member, dict) else {}
                raw = _metadata_get(item_payload, target) if isinstance(member, dict) else member
                values = _oscal_property_values(raw)
                if len(values) != 1:
                    raise ValueError("Value identity requires exactly one scalar")
                normalized = values[0]
                # Replace only the governed identity value with its canonical form.
                if isinstance(member, dict):
                    cursor = item_payload
                    tokens = str(target).split(".")
                    for token in tokens[:-1]:
                        cursor = cursor[token]
                    cursor[tokens[-1]] = normalized
                else:
                    _metadata_assign(item_payload, target, normalized)
                _append_unique_collection_instance(instances, {
                    "instance_key": _value_instance_key(normalized),
                    "payload": item_payload, "parent_instance_key": parent,
                })
            continue
        if registry_row["is_collection"] and isinstance(value, list):
            if not parameters.get("allow_list_instances") or parameters.get("list_identity") != "source-field-index":
                raise ValueError("Collection list identity is not reviewed")
            for index, member in enumerate(value):
                member_payload = dict(member) if isinstance(member, dict) else {}
                if not isinstance(member, dict):
                    _metadata_assign(member_payload, target, member)
                _append_unique_collection_instance(instances, {
                    "instance_key": field + ":" + str(index), "payload": member_payload,
                    "parent_instance_key": parent,
                })
            continue
        if row["TRANSFORM_ID"] == "status-crosswalk":
            if not isinstance(value, dict):
                raise ValueError("Object merge transform must return an object")
            deferred_merges.append(value)
        else:
            _metadata_assign(payload, target, value)
    for values in deferred_merges:
        for member, value in values.items():
            _metadata_assign(payload, member, value, preserve_existing=member == "remarks")
    required = parameters.get("required_members") or ()
    if any(not _has_value(_metadata_get(payload, member)) for member in required):
        if parameters.get("optional_assembly"):
            return []
        raise ValueError("Required payload member is missing")
    if operator in {"object", "record"} and (payload or parameters.get("materialize_empty") or operator == "record"):
        key = source_record_id if operator == "record" else "singleton"
        instances.insert(0, {"instance_key": key, "payload": payload, "parent_instance_key": parent})
    return instances


def _metadata_uuid(path, instance, source_system, source_table, source_id, model_key, context):
    parameters = context["compiled_plan"]["elements"].get(path, {}).get("parameters") or {}
    if parameters.get("uuid_from_instance"):
        instance_uuid = _canonical_uuid(instance["instance_key"], "Instance identity")
        if instance["payload"].get("uuid") != instance_uuid:
            raise ValueError("Reference instance UUID conflicts with its payload")
        return instance_uuid
    return _deterministic_uuid(context["config"]["IDENTITY_VERSION"], source_system,
                               source_table, source_id, model_key, path, instance["instance_key"])


def _metadata_payload(path, payload, node_uuid, context):
    parameters = context["compiled_plan"]["elements"].get(path, {}).get("parameters") or {}
    if not isinstance(payload, dict):
        raise ValueError("Element payload must be an object")
    if parameters.get("include_uuid"):
        if payload.get("uuid") not in (None, "", node_uuid):
            raise ValueError("Payload UUID conflicts with node UUID")
        return dict(payload, uuid=node_uuid)
    return payload


def _metadata_record_complete(nodes_by_path, context):
    for group in context["compiled_plan"].get("reference_groups", ()):
        roles, parties, assignments = [nodes_by_path.get(group[key], ()) for key in (
            "roles_path", "parties_path", "assignments_path")]
        role_ids, party_ids = set(), set()
        for node in roles:
            payload = _metadata_reference_payload(node, "Role")
            role = _metadata_text(payload.get("id"), "Role identity")
            if role in role_ids or node["INSTANCE_KEY"] != role:
                raise ValueError("Role identities must be unique and agree")
            role_ids.add(role)
        for node in parties:
            payload = _metadata_reference_payload(node, "Party")
            key = _canonical_uuid(node["OSCAL_UUID"], "Party UUID")
            if key in party_ids or payload.get("uuid") != key or node["INSTANCE_KEY"] != key:
                raise ValueError("Party UUID identities must be unique and agree")
            if payload.get("type") != group.get("party_type"):
                raise ValueError("Party type conflicts with reviewed metadata")
            party_ids.add(key)
        used_roles, used_parties = set(), set()
        for node in assignments:
            payload = _metadata_reference_payload(node, "Assignment")
            role, refs = payload.get("role-id"), payload.get("party-uuids")
            if role not in role_ids or role in used_roles:
                raise ValueError("Role association is unresolved or duplicated")
            if not isinstance(refs, list) or not refs or len(refs) != len(set(refs)):
                raise ValueError("Party association must be nonempty and unique")
            if not set(refs).issubset(party_ids):
                raise ValueError("Party association is unresolved")
            used_roles.add(role)
            used_parties.update(refs)
        if used_roles != role_ids or used_parties != party_ids:
            raise ValueError("Linked identity collections contain unreferenced members")
    context.pop("_metadata_reference_cache", None)


def _metadata_finish(nodes, edges, context):
    report = context["graph_report"]
    invalid = report["INVALID_SOURCE_RECORDS"] + report["DUPLICATE_SOURCE_RECORDS"]
    invalid += sum(counts["invalid"] for counts in report["FIELDS"].values())
    report.update(CANDIDATE_NODES=len(nodes), CANDIDATE_EDGES=len(edges), COUNTS_ARE_CANDIDATES=True)
    if invalid or not report["SOURCE_RECORDS"]:
        report.update(STATUS="BLOCKED", OUTPUTS_PUBLISHED=False)
        raise ValueError("Metadata mappings rejected source values: " + json.dumps(report, sort_keys=True))
    report.update(STATUS="MAPPED_SCOPE_BUILT", OUTPUTS_PUBLISHED=True, NODES=len(nodes),
                  EDGES=len(edges), DOCUMENTS=report["SOURCE_RECORDS"], COUNTS_ARE_CANDIDATES=False,
                  FIELDS_WITH_POPULATED_EVIDENCE=sum(v["emitted"] > 0 for v in report["FIELDS"].values()))


def _prepare_model_context(context, model_key, source_system, source_table):
    if not isinstance(context, dict) or context.get("model_contract", {}).get("POLICY") != "metadata-v1":
        raise ValueError("Run the matching Cell 3: a compiled metadata-v1 context is required")
    config, contract = context["config"], context["model_contract"]
    if any(config.get(key) != value for key, value in (
        ("OSCAL_MODEL", model_key), ("SOURCE_SYSTEM_NAME", source_system), ("SOURCE_TABLE_NAME", source_table),
    )) or contract.get("MODEL_KEY") != model_key:
        raise ValueError("Graph arguments conflict with compiled metadata context")
    _metadata_text(config.get("IDENTITY_VERSION"), "Identity version")
    plan = context.get("compiled_plan")
    snapshot = _metadata_plan_snapshot(plan)
    if snapshot is None or snapshot != context.get("_compiled_plan_snapshot"):
        _validate_compiled_metadata(plan, contract.get("ROOT_PATH"))
        context["_compiled_plan_snapshot"] = snapshot
    if contract.get("ROOT_PATH") not in plan["elements"]:
        raise ValueError("Compiled plan must describe the configured root")
    grouped = {}
    for row in plan["mappings"]:
        grouped.setdefault(row["OWNER_ELEMENT_PATH"], []).append(row)
    context["mappings_by_path"] = grouped
    context.pop("_metadata_reference_cache", None)
    context["graph_report"] = {
        "SOURCE_RECORDS": 0, "INVALID_SOURCE_RECORDS": 0, "DUPLICATE_SOURCE_RECORDS": 0,
        "STATUS": "NOT_RUN", "OUTPUTS_PUBLISHED": False,
    }
    return context


print("Cell 4 metadata runtime initialized")

