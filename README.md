# ============================================================
# G. COLLECTION INSTANCE HELPERS
# ============================================================

def _normalize_instance_key_name(name):
    """
    Normalize key names for comparison.

    Example:
        CONTENT_ID -> contentid
        ContentId  -> contentid
    """
    if name is None:
        return ""

    return "".join(
        ch for ch in str(name).lower()
        if ch.isalnum()
    )


def get_collection_instance_key(
    instance_value,
    instance_key_rule
):
    """
    Get stable instance key from one collection item.

    Dictionary reference example:
        {"ContentId": 634658, "LevelId": 17}

    INSTANCE_KEY_RULE:
        CONTENT_ID

    -> returns 634658

    Scalar reference example:
        942565

    -> returns 942565
    """

    if instance_value is None:
        return None

    # Object/reference
    if isinstance(instance_value, dict):

        target_key = _normalize_instance_key_name(
            instance_key_rule
        )

        for key, value in instance_value.items():

            if (
                _normalize_instance_key_name(key)
                == target_key
            ):
                return value

        return None

    # Scalar reference
    return instance_value


def extract_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    source_json_field="CURATED_JSON"
):
    """
    Extract unique instances for one collection node.

    Generic:
      - no SSP-specific fields
      - driven by mapping rows
      - driven by INSTANCE_KEY_RULE
      - deduplicates repeated references

    Returns list like:

        {
            "INSTANCE_KEY": "634658",
            "SOURCE_VALUE": {
                "ContentId": 634658,
                "LevelId": 17
            },
            "SOURCE_FIELDS": ["SOFTWARE"]
        }
    """

    source_record_dict = _row_to_dict(
        source_record
    )

    json_data = source_record_dict.get(
        source_json_field
    )

    if isinstance(json_data, str):

        try:
            source_obj = json.loads(json_data)

        except json.JSONDecodeError:
            source_obj = {}

    elif isinstance(json_data, (dict, list)):
        source_obj = json_data

    else:
        source_obj = {}

    instances = {}

    for mapping in mappings:

        source_field_name = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field_name:
            continue

        source_value = resolve_json_path(
            source_obj,
            source_field_name
        )

        if source_value in (None, "", [], {}):
            continue

        values = (
            source_value
            if isinstance(source_value, list)
            else [source_value]
        )

        for item in values:

            instance_key = get_collection_instance_key(
                item,
                instance_key_rule
            )

            if instance_key is None:
                continue

            instance_key = str(instance_key).strip()

            if not instance_key:
                continue

            # Deduplicate same instance inside same source record
            if instance_key not in instances:

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "SOURCE_VALUE": item,
                    "SOURCE_FIELDS": [
                        source_field_name
                    ]
                }

            else:

                if (
                    source_field_name
                    not in
                    instances[instance_key]["SOURCE_FIELDS"]
                ):
                    instances[instance_key][
                        "SOURCE_FIELDS"
                    ].append(source_field_name)

                # Prefer richer dictionary representation
                if (
                    not isinstance(
                        instances[instance_key]["SOURCE_VALUE"],
                        dict
                    )
                    and isinstance(item, dict)
                ):
                    instances[instance_key][
                        "SOURCE_VALUE"
                    ] = item

    return list(instances.values())


def build_collection_node_seed(
    source_system,
    source_table,
    content_id,
    node_type,
    instance_key
):
    """
    Collection identity extension.

    Existing singleton identity remains unchanged.

    Format:
    SOURCE_SYSTEM|SOURCE_TABLE|CONTENT_ID|NODE_TYPE|INSTANCE_KEY
    """

    base_seed = build_node_seed(
        source_system,
        source_table,
        content_id,
        node_type
    )

    instance_key = (
        str(instance_key).strip()
        if instance_key is not None
        else ""
    )

    return f"{base_seed}|{instance_key}"
