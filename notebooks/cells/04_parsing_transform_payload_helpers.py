# %% Cell 4 - Generic parsing, transformation, and payload helpers

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
STATUS_ELEMENT_PATH = "system-security-plan.system-characteristics.status"
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


def _single_archer_label(value):
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

    resolved = ARCHER_VALUE_LOOKUP.get(key)
    if resolved is not None:
        label = str(resolved).strip()
        return label or None

    # An already resolved textual label is safe to preserve. An unknown
    # numeric ID is not: it must be added to ARCHER_META_VALUE first.
    if isinstance(item, str) and not key.isdigit():
        return key
    return None


def transform_security_objective(value):
    normalized = transform_fips_199(value)
    if isinstance(normalized, list):
        if len(normalized) != 1:
            raise ValueError(
                "Security objective resolved to multiple FIPS values"
            )
        normalized = normalized[0]
    if _has_value(normalized):
        return str(normalized)

    label = _single_archer_label(value)
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


def transform_status_state(value):
    label = _single_archer_label(value)
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


def transform_metadata_title(value):
    value = _to_python(value)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Metadata title source must be a nonblank string")
    return value


def _is_executable_responsible_party_mapping(mapping_row):
    source_field = str(mapping_row["SOURCE_FIELD_NAME"]).strip()
    if source_field not in RESPONSIBLE_PARTY_ROLE_DEFINITIONS:
        return False

    mapping_type = str(
        mapping_row.get("MAPPING_TYPE") or "Direct"
    ).strip().lower()
    status = str(mapping_row.get("STATUS") or "").strip().lower()
    return "tbd" not in mapping_type and "more information" not in status


def _active_responsible_party_role_instances(source_obj, source_record_id):
    instances = []
    emitted_role_ids = set()
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
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
        if not _party_uuid_values(source_record_id, source_value):
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


def _party_uuid(source_record_id, identifier):
    return _deterministic_uuid(
        CONFIG["SOURCE_SYSTEM_NAME"],
        source_record_id,
        "party",
        identifier,
    )


def _party_uuid_values(source_record_id, value):
    extracted = _extract_reference_ids(value)
    values = extracted if isinstance(extracted, list) else [extracted]
    party_uuids = []
    for item in values:
        if item is None:
            continue
        party_uuid = _party_uuid(
            source_record_id,
            _party_reference_identifier(item),
        )
        if party_uuid not in party_uuids:
            party_uuids.append(party_uuid)
    return party_uuids


def _active_responsible_party_instances(source_obj, source_record_id):
    instances = []
    emitted_party_uuids = set()
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
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

        for party_uuid in _party_uuid_values(source_record_id, source_value):
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
):
    assignments_by_role = {}
    mapping_rows = MAPPINGS_BY_ELEMENT_PATH.get(
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

        party_uuids = _party_uuid_values(source_record_id, source_value)
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


def transform_responsible_party(source_record_id, source_field, value):
    role_id = RESPONSIBLE_PARTY_ROLE_IDS.get(source_field)
    if role_id is None:
        return SKIP_VALUE
    party_uuids = _party_uuid_values(source_record_id, value)
    if not party_uuids:
        return SKIP_VALUE
    return {"role-id": role_id, "party-uuids": party_uuids}


def _target_field_name(mapping_row):
    explicit = mapping_row.get("OSCAL_FIELD_NAME")
    if explicit:
        return str(explicit).strip().replace("[]", "")
    return _stable_property_name(str(mapping_row["SOURCE_FIELD_NAME"]))


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

    owner_path = str(mapping_row.get("OWNER_ELEMENT_PATH") or "").strip()
    target_field = _target_field_name(mapping_row)

    if source_field in RESPONSIBLE_PARTY_ROLE_IDS:
        return transform_responsible_party(
            source_record_id, source_field, value
        )

    if (
        owner_path == SECURITY_IMPACT_ELEMENT_PATH
        and target_field in SECURITY_OBJECTIVE_FIELDS
    ):
        return transform_security_objective(value)

    if owner_path == STATUS_ELEMENT_PATH and target_field == "state":
        return transform_status_state(value)

    if owner_path == METADATA_ELEMENT_PATH and target_field == "published":
        return transform_published(value)

    if (
        owner_path == METADATA_ELEMENT_PATH
        and target_field == "last-modified"
    ):
        return transform_last_modified(value)

    if owner_path == DOCUMENT_IDS_ELEMENT_PATH and target_field == "identifier":
        return transform_document_identifier(value)

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
    resolved_cluster_fields = set()

    if element_path == METADATA_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_instances(
            source_obj,
            source_record_id,
        )

    if element_path == METADATA_ROLES_ELEMENT_PATH:
        return _active_responsible_party_role_instances(
            source_obj,
            source_record_id,
        )

    if element_path == RESPONSIBLE_PARTIES_ELEMENT_PATH:
        return _active_responsible_party_assignment_instances(
            source_obj,
            source_record_id,
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
            mapping_row, source_value, source_record_id
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

        if element_path == COMPONENTS_ELEMENT_PATH:
            component_type = _component_mapping_type(mapping_row)
            for content_id in _component_reference_content_ids(transformed):
                _append_unique_collection_instance(
                    instances,
                    {
                        "instance_key": content_id,
                        "payload": {"type": component_type},
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

    if element_path == COMPONENTS_ELEMENT_PATH:
        instances.sort(key=lambda item: item["instance_key"])
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
