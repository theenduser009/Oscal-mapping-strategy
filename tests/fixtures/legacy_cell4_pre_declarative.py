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
    metadata_spec = context.get("_metadata_hydration_spec") if context is not None else None
    hydration_contract = (metadata_spec["contracts"] if metadata_spec is not None else COMPONENT_HYDRATION_CONTRACT)
    source_types = (metadata_spec["source_types"] if metadata_spec is not None else COMPONENT_SOURCE_TYPES)
    hydration_routes = (metadata_spec["routes"] if metadata_spec is not None else COMPONENT_HYDRATION_SOURCE_FIELDS)
    if _context_config(context).get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Component hydration must be built before guarded writes"
        )
    if not isinstance(hydration_source_dfs, dict):
        raise RuntimeError("Component hydration sources are unavailable")
    if set(hydration_source_dfs) != set(hydration_contract):
        raise RuntimeError("Component hydration source contract is incomplete")
    source_contract = (
        context.get("lookups", {}).get("component_contract")
        if context is not None else globals().get("COMPONENT_HYDRATION_SOURCE_CONTRACT")
    )
    if metadata_spec is None and source_contract != hydration_contract:
        raise RuntimeError("Component hydration source contract has drifted")

    component_rows_by_field = {}
    unexpected_component_rows = 0
    for row in mapping_rows:
        source_field = str(row.get("SOURCE_FIELD_NAME") or "").strip()
        if source_field in source_types:
            component_rows_by_field.setdefault(source_field, []).append(row)
        else:
            unexpected_component_rows += 1

    if unexpected_component_rows:
        raise RuntimeError("Canonical component mapping contract has drifted")
    if set(component_rows_by_field) != set(source_types):
        raise RuntimeError("Canonical component mapping contract has drifted")
    for source_field, rows in component_rows_by_field.items():
        if len(rows) != 1:
            raise RuntimeError(
                "Canonical component mapping is duplicated"
            )
        actual_type = (rows[0].get("REPRESENTATION_PARAMS", {}).get("reference_type")
                       if metadata_spec is not None else _component_mapping_type(rows[0]))
        if actual_type != source_types[source_field]:
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
        hydration_routes.items()
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
    for component_type, contract in hydration_contract.items():
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
        description_required = (bool(contract.get("description_required")) if metadata_spec is not None
                                else component_type == "software")
        if description_required:
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


def _legacy_prepare_model_context(context, model_key, source_system, source_table):
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


# Metadata execution is deliberately separate from the compatibility functions
# above. Only reviewed declarative operations enter this path; names, models,
# paths, payload placement and identity parameters come from the compiled plan.
_METADATA_TRANSFORMS = frozenset({
    "direct", "text", "timestamp", "date", "identifier", "archer-select",
    "scalar-score", "security-objective", "status-crosswalk",
    "reject-populated", "skip", "canonical-text",
})
_METADATA_OPERATORS = frozenset({
    "object", "record", "properties", "values", "observations", "references",
    "roles", "parties", "assignments",
})


def _metadata_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + " must be nonblank text")
    return value


def _metadata_params(row):
    params = row.get("REPRESENTATION_PARAMS") or {}
    if not isinstance(params, dict):
        raise ValueError("Representation parameters must be an object")
    return params


def _metadata_target(row):
    params = _metadata_params(row)
    return params.get("target") or row.get("FIELD_RELATIVE_PATH") or row.get("OSCAL_FIELD_NAME")


def _metadata_transform(row, value, context):
    transform_id = row["TRANSFORM_ID"]
    params = row.get("TRANSFORM_PARAMS") or {}
    if transform_id == "skip":
        return SKIP_VALUE
    if not _has_value(value):
        if _metadata_params(row).get("required") or params.get("required"):
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
        member = params.get("target_member", "state")
        payload = {member: target}
        if target == params.get("other_value", "other"):
            prefix = params.get("other_remarks_prefix")
            if not isinstance(prefix, str):
                raise ValueError("Crosswalk fallback explanation is not configured")
            payload[params.get("remarks_member", "remarks")] = prefix + label + params.get("other_remarks_suffix", ".")
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
    name = _metadata_params(row).get("property_name")
    if name is None and parameters.get("property_name_rule") == "source-field-slug":
        name = _stable_property_name(row["SOURCE_FIELD_NAME"])
    return _metadata_text(name, "Reviewed property name")


def _metadata_spec(path, context, registry_row=None):
    specification = context["compiled_plan"]["elements"].get(path)
    if specification is not None:
        return specification
    if registry_row and not registry_row["is_collection"]:
        fallback = context["compiled_plan"].get("default_element")
        if fallback is not None:
            scope = fallback.get("scope", "noncollection")
            if scope not in {"noncollection", "singletons-without-collection-ancestors"}:
                raise ValueError("Unknown default element scope")
            if scope == "singletons-without-collection-ancestors" and "[]" in path:
                return None
            return fallback
    return None


def _metadata_registry_policy(rows, context):
    by_path = {row["element_path"]: row for row in rows}
    plan = context["compiled_plan"]
    if not set(plan["elements"]).issubset(by_path):
        raise ValueError("Metadata plan names an unregistered element")
    for path, row in by_path.items():
        specification = _metadata_spec(path, context, row)
        if specification is None:
            if context["_metadata_by_path"].get(path):
                raise ValueError("Mapped element has no reviewed representation")
            continue
        parameters = specification.get("parameters") or {}
        expected = parameters.get("registry_contract") or {}
        for key in ("parent_path", "is_collection", "instance_key_rule", "item_path"):
            if key in expected and row.get(key) != expected[key]:
                raise ValueError("Registry identity contradicts reviewed metadata")
        if row["parent_path"] and row["parent_path"] not in by_path:
            raise ValueError("Registry parent is absent")
        operator = specification["operator"]
        if operator in {"record", "observations", "properties", "values", "references",
                        "roles", "parties", "assignments"} and not row["is_collection"]:
            raise ValueError("Collection representation requires collection registry row")
        if operator == "record" and row["instance_key_rule"] != "SOURCE_RECORD_ID":
            raise ValueError("Record collection requires source-record identity")
        if operator == "observations" and row["instance_key_rule"] != "SOURCE_FIELD_NAME":
            raise ValueError("Observation collection requires source-field identity")
        if operator == "properties" and row["instance_key_rule"] != "SOURCE_FIELD_NAME+VALUE":
            raise ValueError("Property collection requires source-field/value identity")
        if operator == "values" and row["instance_key_rule"] != "VALUE":
            raise ValueError("Value collection requires value identity")
        if operator == "references" and row["instance_key_rule"] != "CONTENT_ID":
            raise ValueError("Reference collection requires referenced-record identity")
    context["_metadata_registry"] = by_path
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
    types, routes, source_types = {}, {}, {}
    component_contract = context.get("lookups", {}).get("component_contract") or {}
    for path, rows in context["_metadata_by_path"].items():
        spec = plan["elements"].get(path)
        if not spec or spec["operator"] != "references":
            continue
        for row in rows:
            if row["TRANSFORM_ID"] == "skip":
                continue
            params = _metadata_params(row)
            type_name = _metadata_text(params.get("reference_type"), "Reference type")
            field = row["SOURCE_FIELD_NAME"]
            if field in source_types and source_types[field] != type_name:
                raise ValueError("Source reference has conflicting type declarations")
            source_types[field] = type_name
            binding = params.get("hydrate_lookup")
            if not binding:
                continue
            contract = component_contract.get(binding)
            if not isinstance(contract, dict):
                raise ValueError("Reviewed reference lookup source is absent")
            contract = dict(contract)
            contract["description_required"] = bool(params.get("description_required", False))
            contract["lookup_binding"] = binding
            if type_name in types and types[type_name] != contract:
                raise ValueError("Reference type has contradictory hydration contracts")
            types[type_name] = contract
            routes[field] = type_name
    if routes:
        sources = context.get("lookups", {}).get("component_sources")
        if not isinstance(sources, dict):
            raise ValueError("Reference lookup dataframes are unavailable")
        dfs = {type_name: sources[contract["lookup_binding"]]
               for type_name, contract in types.items()
               if contract["lookup_binding"] in sources}
        if set(dfs) != set(types):
            raise ValueError("Reference lookup dataframe binding is missing")
        context["_metadata_hydration_spec"] = {
            "contracts": types, "routes": routes, "source_types": source_types,
        }
        context["component_hydration_lookups"] = _build_component_hydration_lookups(
            source_df, [row for row in plan["mappings"]
                        if row["SOURCE_FIELD_NAME"] in source_types], dfs, context,
        )


def _metadata_parse(record, context):
    value = _to_python(record["CURATED_JSON"])
    options = context["_metadata_options"]
    if value is None and options.get("null_source_as_empty", False):
        return {}
    if isinstance(value, str):
        value = json.loads(value, parse_float=Decimal) if options.get("parse_decimal", True) else json.loads(value)
    if not isinstance(value, dict):
        raise ValueError("Source JSON must resolve to an object")
    return value


def _metadata_mapped_value(row, source_obj, context):
    field = row["SOURCE_FIELD_NAME"]
    counts = context["graph_report"]["FIELDS"].get(field)
    try:
        value = _metadata_transform(row, resolve_json_path(source_obj, field), context)
    except (TypeError, ValueError, ArithmeticError):
        if counts is not None:
            counts["invalid"] += 1
        if context["policy"]["aggregate_invalid"]:
            return SKIP_VALUE
        raise
    if counts is not None:
        counts["missing" if value is SKIP_VALUE else "emitted"] += 1
    return value


def _metadata_party_uuid(group, source_record_id, identifier, context):
    parts = group.get("party_uuid_parts")
    if not isinstance(parts, (tuple, list)) or not parts:
        raise ValueError("Reference UUID policy must be explicit")
    config = context["config"]
    namespace = group.get("source_namespace")
    if namespace is not None:
        if not isinstance(namespace, dict) or set(namespace) != {"SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "MODEL_KEY"}:
            raise ValueError("Legacy reference namespace must be explicit")
        actual = {"SOURCE_SYSTEM_NAME": config["SOURCE_SYSTEM_NAME"],
                  "SOURCE_TABLE_NAME": config["SOURCE_TABLE_NAME"], "MODEL_KEY": config["OSCAL_MODEL"]}
        if namespace != actual:
            parts = ["$identity_version", "$source_system", "$source_table", "$source_record", "$model", "party", "$reference_id"]
    values = {"$source_system": config["SOURCE_SYSTEM_NAME"],
              "$source_table": config["SOURCE_TABLE_NAME"],
              "$source_record": source_record_id, "$source_record_id": source_record_id,
              "$reference_id": identifier, "$model": config["OSCAL_MODEL"],
              "$identity_version": config["IDENTITY_VERSION"]}
    resolved = []
    for part in parts:
        if not isinstance(part, str) or not part:
            raise ValueError("Invalid reference UUID token")
        if part.startswith("$") and part not in values:
            raise ValueError("Unknown reference UUID token")
        resolved.append(values.get(part, part))
    return _deterministic_uuid(*resolved)


def _metadata_party_instances(path, source_obj, source_record_id, operator, parameters, context):
    groups = [group for group in context["compiled_plan"].get("reference_groups", ())
              if path in (group.get("roles_path"), group.get("parties_path"), group.get("assignments_path"))]
    if len(groups) != 1:
        raise ValueError("Linked-identity element requires exactly one reference group")
    group = groups[0]
    cache = context.setdefault("_metadata_reference_cache", {})
    cache_key = (source_record_id, group["assignments_path"])
    if cache_key not in cache:
        roles, parties, assignments = [], [], {}
        for row in context["_metadata_by_path"].get(group["assignments_path"], ()):
            params = _metadata_params(row)
            value = _metadata_mapped_value(row, source_obj, context)
            if value is SKIP_VALUE:
                continue
            extracted = _extract_reference_ids(value)
            members = extracted if isinstance(extracted, list) else [extracted]
            party_ids = []
            for member in members:
                if member is None:
                    continue
                identifier = _party_reference_identifier(member)
                key = _metadata_party_uuid(group, source_record_id, identifier, context)
                if key not in party_ids:
                    party_ids.append(key)
            if not party_ids:
                continue
            role_id = _metadata_text(params.get("role_id"), "Reviewed role identity")
            role_title = _metadata_text(params.get("role_title"), "Reviewed role title")
            _append_unique_collection_instance(roles, {
                "instance_key": role_id, "payload": {"id": role_id, "title": role_title},
                "parent_instance_key": None,
            })
            for key in party_ids:
                _append_unique_collection_instance(parties, {
                    "instance_key": key,
                    "payload": {"uuid": key, "type": _metadata_text(group.get("party_type"), "Reviewed party type")},
                    "parent_instance_key": None,
                })
            assignment = assignments.setdefault(role_id, {
                "instance_key": row["SOURCE_FIELD_NAME"],
                "payload": {"role-id": role_id, "party-uuids": []},
                "parent_instance_key": None,
            })
            for key in party_ids:
                if key not in assignment["payload"]["party-uuids"]:
                    assignment["payload"]["party-uuids"].append(key)
        cache[cache_key] = {"roles": roles, "parties": parties,
                           "assignments": list(assignments.values())}
    instances = cache[cache_key][operator]
    parent_key = _metadata_parent_key(parameters, source_record_id)
    return [dict(instance, parent_instance_key=parent_key) for instance in instances]


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
        payload = {parameters.get("type_member", "type"): type_name}
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
    specification = _metadata_spec(path, context, registry_row)
    if specification is None:
        return []
    operator = specification["operator"]
    parameters = specification.get("parameters") or {}
    rows = context["_metadata_by_path"].get(path, ())
    parent = _metadata_parent_key(parameters, source_record_id)
    if operator in {"roles", "parties", "assignments"}:
        return _metadata_party_instances(path, source_obj, source_record_id,
                                         operator, parameters, context)
    if operator == "references":
        return _metadata_reference_instances(source_obj, source_record_id, rows, parameters, context)
    payload, instances, deferred_merges = {}, [], []
    for controlled in parameters.get("controlled_fields", ()):
        keys = [name for name in ("config_key", "source_field", "value") if name in controlled]
        if len(keys) != 1:
            raise ValueError("Controlled field needs exactly one reviewed value source")
        source_kind = keys[0]
        if source_kind == "config_key":
            value = context["config"].get(controlled["config_key"])
        elif source_kind == "source_field":
            value = resolve_json_path(source_obj, controlled["source_field"])
        else:
            value = controlled["value"]
        synthetic = {"TRANSFORM_ID": controlled.get("transform_id", "direct"),
                     "TRANSFORM_PARAMS": controlled.get("transform_params", {}),
                     "REPRESENTATION_PARAMS": {"required": controlled.get("required", True)}}
        value = _metadata_transform(synthetic, value, context)
        if value is not SKIP_VALUE:
            _metadata_assign(payload, controlled["target"], value)
    for row in rows:
        value = _metadata_mapped_value(row, source_obj, context)
        if value is SKIP_VALUE:
            continue
        params = _metadata_params(row)
        field = row["SOURCE_FIELD_NAME"]
        target = _metadata_target(row)
        if operator in {"properties", "observations"}:
            name = _metadata_property_name(row, parameters)
            values = _oscal_property_values(value)
            if operator == "observations" and len(values) != 1:
                raise ValueError("One scalar value is required per observation")
            for item in values:
                property_payload = {"name": name, "value": item}
                if "namespace" in params:
                    property_payload["ns"] = _metadata_text(params["namespace"], "Property namespace")
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
        representation = str(row.get("REPRESENTATION") or "").lower()
        if representation == "merge-object" or row["TRANSFORM_ID"] == "status-crosswalk":
            if not isinstance(value, dict):
                raise ValueError("Object merge transform must return an object")
            deferred_merges.append((row, value))
        else:
            _metadata_assign(payload, target, value)
    for row, values in deferred_merges:
        defaults = set((row.get("TRANSFORM_PARAMS") or {}).get("default_members", ("remarks",)))
        for member, value in values.items():
            _metadata_assign(payload, member, value, preserve_existing=member in defaults)
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
    parameters = (_metadata_spec(path, context, context["_metadata_registry"].get(path)) or {}).get("parameters") or {}
    if parameters.get("uuid_from_instance"):
        instance_uuid = _canonical_uuid(instance["instance_key"], "Instance identity")
        if instance["payload"].get("uuid") != instance_uuid:
            raise ValueError("Reference instance UUID conflicts with its payload")
        return instance_uuid
    return _deterministic_uuid(context["config"]["IDENTITY_VERSION"], source_system,
                               source_table, source_id, model_key, path, instance["instance_key"])


def _metadata_payload(path, payload, node_uuid, context):
    parameters = (_metadata_spec(path, context, context["_metadata_registry"].get(path)) or {}).get("parameters") or {}
    if not isinstance(payload, dict):
        raise ValueError("Element payload must be an object")
    if set(parameters.get("forbidden_members", ())) & set(payload):
        raise ValueError("Payload contains an unapproved member")
    for member in parameters.get("nonblank_text_members", ()):
        if member in payload:
            _metadata_text(payload[member], "Governed payload member")
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
    if context is None or context.get("model_contract", {}).get("POLICY") != "metadata-v1":
        # Compatibility only: historical standalone diagnostics and parity oracles.
        # The current compiler always emits metadata-v1 plus a compiled plan.
        return _legacy_prepare_model_context(context, model_key, source_system, source_table)
    config, contract = context["config"], context["model_contract"]
    if any(config.get(key) != value for key, value in (
        ("OSCAL_MODEL", model_key), ("SOURCE_SYSTEM_NAME", source_system), ("SOURCE_TABLE_NAME", source_table),
    )) or contract.get("MODEL_KEY") != model_key:
        raise ValueError("Graph arguments conflict with compiled metadata context")
    _metadata_text(config.get("IDENTITY_VERSION"), "Identity version")
    plan = context.get("compiled_plan")
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise ValueError("A compiled metadata plan is required")
    if not isinstance(plan.get("elements"), dict) or not isinstance(plan.get("mappings"), list):
        raise ValueError("Compiled metadata element and mapping plans are required")
    if contract.get("ROOT_PATH") not in plan["elements"]:
        raise ValueError("Compiled plan must describe the configured root")
    specifications = list(plan["elements"].values())
    if plan.get("default_element") is not None:
        specifications.append(plan["default_element"])
    for specification in specifications:
        if not isinstance(specification, dict) or specification.get("operator") not in _METADATA_OPERATORS:
            raise ValueError("Unsupported reviewed element representation")
        if not isinstance(specification.get("parameters", {}), dict):
            raise ValueError("Element parameters must be an object")
        for field in specification.get("parameters", {}).get("controlled_fields", ()):
            if field.get("transform_id", "direct") not in _METADATA_TRANSFORMS:
                raise ValueError("Unknown controlled-field transform")
    grouped, seen = {}, set()
    for row in plan["mappings"]:
        if row.get("TRANSFORM_ID") not in _METADATA_TRANSFORMS:
            raise ValueError("Unknown metadata transformation")
        approval = str(row.get("APPROVAL_STATUS") or "").lower().replace("_", "-")
        approved = approval in {"approved", "accepted", "runtime-accepted", "runtime-accepted-in-memory"}
        guarded_null = approval == "blocked-if-populated" and row["TRANSFORM_ID"] == "reject-populated"
        if not approved and not guarded_null:
            raise ValueError("Unapproved mapping cannot enter runtime plan")
        _metadata_text(row.get("SOURCE_FIELD_NAME"), "Source field")
        path = _metadata_text(row.get("OWNER_ELEMENT_PATH"), "Owner element")
        if path not in plan["elements"]:
            raise ValueError("Mapped element lacks a reviewed representation")
        representation = str(row.get("REPRESENTATION") or "").lower()
        operator = plan["elements"][path]["operator"]
        if representation not in {"", "scalar", "merge-object", operator}:
            raise ValueError("Unknown metadata mapping representation")
        if not isinstance(row.get("TRANSFORM_PARAMS", {}), dict):
            raise ValueError("Transform parameters must be an object")
        _metadata_params(row)
        identity = (path, row["SOURCE_FIELD_NAME"], str(_metadata_target(row) or ""))
        if identity in seen:
            raise ValueError("Duplicate compiled mapping row")
        seen.add(identity)
        grouped.setdefault(path, []).append(row)
    options = dict(contract.get("RUNTIME_OPTIONS") or {})
    options.update(plan.get("options") or {})
    context["_metadata_options"] = options
    context["_metadata_by_path"] = grouped
    context["policy"] = {
        "registry": _metadata_registry_policy, "prepare": _metadata_prepare,
        "parse": _metadata_parse, "instances": _metadata_instances,
        "uuid": _metadata_uuid, "payload": _metadata_payload,
        "record_complete": _metadata_record_complete, "finish": _metadata_finish,
        "aggregate_invalid": bool(options.get("aggregate_invalid", True)),
        "allow_nan": bool(options.get("allow_nan", False)),
    }
    context["graph_report"] = {
        "SOURCE_RECORDS": 0, "INVALID_SOURCE_RECORDS": 0, "DUPLICATE_SOURCE_RECORDS": 0,
        "STATUS": "NOT_RUN", "OUTPUTS_PUBLISHED": False,
    }
    return context
