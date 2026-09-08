# %% Cell 4 - Generic parsing, transformation, and payload helpers

SKIP_VALUE = object()

RESPONSIBLE_PARTY_ROLE_IDS = {
    "INFORMATION_OWNER_IO": "information-owner",
    "INFORMATION_SYSTEM_OWNER_ISO": "system-owner",
    "AUTHORIZING_OFFICIAL_AO": "authorizing-official",
    "INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO": (
        "system-security-officer"
    ),
    "PRIVACY_OFFICER_PO": "privacy-officer",
}

TRANSIENT_SOURCE_FIELDS = {
    "PACKAGE_TYPE_HELPER_CALC",
}


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
            "ValuesListIds",
            "ValueListIds",
            "ContentIds",
            "Ids",
            "Value",
        ):
            if key in value and _has_value(value[key]):
                return _extract_reference_ids(value[key])
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


def resolve_archer_select_value(value):
    extracted = _extract_reference_ids(value)

    def resolve_one(item):
        if item is None:
            return None
        return ARCHER_VALUE_LOOKUP.get(str(item).strip(), item)

    if isinstance(extracted, list):
        resolved = [resolve_one(item) for item in extracted]
        return [item for item in resolved if item is not None]
    return resolve_one(extracted)


def transform_fips_199(value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    normalized = []
    for item in values:
        if item is None:
            continue
        key = str(item).strip()
        label = FIPS_199_VALUE_LOOKUP.get(key)
        if label is None:
            candidate = str(ARCHER_VALUE_LOOKUP.get(key, item)).strip().lower()
            if candidate in {"low", "moderate", "high"}:
                label = candidate
        if label is not None:
            normalized.append(label)
    if not normalized:
        return None
    return normalized[0] if len(normalized) == 1 else normalized


def _party_uuid_values(source_record_id, source_field, value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    party_uuids = []
    for item in values:
        if item is None:
            continue
        if isinstance(item, dict):
            identifier = (
                item.get("Id")
                or item.get("UserId")
                or item.get("ContentId")
                or json.dumps(item, sort_keys=True, default=str)
            )
        else:
            identifier = item
        party_uuids.append(
            _deterministic_uuid(
                CONFIG["SOURCE_SYSTEM_NAME"],
                source_record_id,
                source_field,
                identifier,
            )
        )
    return party_uuids


def transform_responsible_party(source_record_id, source_field, value):
    role_id = RESPONSIBLE_PARTY_ROLE_IDS.get(source_field)
    if role_id is None:
        return SKIP_VALUE
    party_uuids = _party_uuid_values(source_record_id, source_field, value)
    if not party_uuids:
        return SKIP_VALUE
    return {"role-id": role_id, "party-uuids": party_uuids}


def _target_field_name(mapping_row):
    explicit = mapping_row.get("OSCAL_FIELD_NAME")
    if explicit:
        return str(explicit).strip().replace("[]", "")
    return _stable_property_name(str(mapping_row["SOURCE_FIELD_NAME"]))


def apply_mapping_transform(mapping_row, value, source_record_id):
    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    mapping_type = str(mapping_row.get("MAPPING_TYPE") or "Direct").lower()
    transform_logic = str(
        mapping_row.get("TRANSFORMATION_LOGIC") or ""
    ).lower()
    status = str(mapping_row.get("STATUS") or "").lower()

    if source_field in TRANSIENT_SOURCE_FIELDS:
        return SKIP_VALUE
    if "tbd" in mapping_type or "more information" in status:
        return SKIP_VALUE
    if not _has_value(value):
        return SKIP_VALUE

    if source_field in RESPONSIBLE_PARTY_ROLE_IDS:
        return transform_responsible_party(
            source_record_id, source_field, value
        )

    if "fips" in transform_logic or "security objective" in transform_logic:
        transformed = transform_fips_199(value)
        return transformed if _has_value(transformed) else SKIP_VALUE

    if (
        "archer" in transform_logic
        or "select value" in transform_logic
        or "lookup" in transform_logic
        or "extension" in mapping_type
    ):
        transformed = resolve_archer_select_value(value)
        return transformed if _has_value(transformed) else SKIP_VALUE

    return _to_python(value)


def build_element_instances(
    source_obj,
    source_record_id,
    element_path,
    mapping_rows,
):
    is_collection = "[]" in element_path
    instances = []
    aggregate_payload = {}

    for mapping_row in mapping_rows:
        source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
        source_value = resolve_json_path(source_obj, source_field)
        transformed = apply_mapping_transform(
            mapping_row, source_value, source_record_id
        )
        if transformed is SKIP_VALUE:
            continue

        target_field = _target_field_name(mapping_row)

        # The registry path owns node cardinality.  An Extension mapping may
        # resolve a value, but it must create a separate OSCAL property node
        # only when its owning registry node is actually props[].  Treating
        # every Extension mapping as a collection created multiple instances
        # of singleton parents such as system-characteristics.
        if element_path.endswith("props[]"):
            values = transformed if isinstance(transformed, list) else [transformed]
            for index, item in enumerate(values):
                payload = {
                    "name": _stable_property_name(source_field),
                    "value": item,
                }
                instances.append(
                    {
                        "instance_key": f"{source_field}:{index}",
                        "payload": payload,
                        "parent_instance_key": None,
                    }
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

        aggregate_payload[target_field] = transformed

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
