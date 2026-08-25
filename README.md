Yes. Replace the **entire Cell 4 in `NB_ARCHER_OSCAL_MAPPER_V1`** with this version. It keeps the existing SSP/POA&M behavior, keeps the frozen MD5 identities, keeps `SOURCE_RECORD_ID`, and adds the new proper `SOURCE_FIELD_NAME` identity.

```python
# ============================================================
# Cell 4 — Generic OSCAL Helper Functions
# ============================================================

import json
import hashlib


# ============================================================
# 1. Generic row helper
# ============================================================

def _row_to_dict(row):

    if row is None:
        return {}

    if isinstance(row, dict):
        return row

    try:
        return row.as_dict()
    except Exception:
        pass

    try:
        return dict(row)
    except Exception:
        return {}


# ============================================================
# 2. Normalize key names
#
# CONTENT_ID  == ContentId
# source_field_name == SOURCE_FIELD_NAME
# ============================================================

def _normalize_key_name(value):

    if value is None:
        return ""

    return "".join(
        ch
        for ch in str(value).upper()
        if ch.isalnum()
    )


# ============================================================
# 3. Frozen node / edge identity contract
# DO NOT CHANGE
# ============================================================

def build_node_seed(
    source_system,
    source_table,
    content_id,
    node_type
):

    cid = (
        content_id.strip()
        if content_id is not None
        else ""
    )

    return (
        f"{source_system}|"
        f"{source_table}|"
        f"{cid}|"
        f"{node_type}"
    )


def compute_node_key(seed):

    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


def compute_node_uuid(seed):

    return hashlib.md5(
        seed.encode("utf-8")
    ).hexdigest().lower()


def build_edge_seed(
    source_node_key_hex,
    target_node_key_hex,
    edge_type="parent_of"
):

    return (
        f"{source_node_key_hex}::"
        f"{target_node_key_hex}::"
        f"{edge_type}"
    )


def compute_edge_key(seed):

    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


# ============================================================
# 4. Collection path helper
# ============================================================

def is_collection_node(node_path):

    return "[]" in str(
        node_path or ""
    )


# ============================================================
# 5. Resolve JSON path
#
# Important:
# Archer fields are frequently direct dictionary keys.
# Therefore exact-key lookup happens FIRST.
# ============================================================

def resolve_json_path(obj, path):

    if obj is None:
        return None

    if path is None:
        return None

    path = str(path).strip()

    if not path:
        return None

    # Exact Archer field-name lookup first
    if isinstance(obj, dict):

        if path in obj:
            return obj[path]

        expected = _normalize_key_name(path)

        for key, value in obj.items():

            if (
                _normalize_key_name(key)
                == expected
            ):
                return value

    # Root
    if path == "$":
        return obj

    # Remove JSONPath root marker
    if path.startswith("$."):
        path = path[2:]

    elif path.startswith("$"):
        path = path[1:].lstrip(".")

    if not path:
        return obj

    segments = [
        part
        for part in path.split(".")
        if part
    ]

    current = obj

    for segment in segments:

        is_array = segment.endswith("[]")

        key_name = (
            segment[:-2]
            if is_array
            else segment
        )

        # --------------------------------------------
        # Current object is dictionary
        # --------------------------------------------

        if isinstance(current, dict):

            if key_name in current:

                current = current[key_name]

            else:

                expected = _normalize_key_name(
                    key_name
                )

                matched = False

                for key, value in current.items():

                    if (
                        _normalize_key_name(key)
                        == expected
                    ):
                        current = value
                        matched = True
                        break

                if not matched:
                    return None

        # --------------------------------------------
        # Current object is list
        # Resolve same property against each item
        # --------------------------------------------

        elif isinstance(current, list):

            resolved_values = []

            for item in current:

                if not isinstance(item, dict):
                    continue

                if key_name in item:

                    value = item[key_name]

                else:

                    expected = _normalize_key_name(
                        key_name
                    )

                    value = None
                    found = False

                    for key, candidate in item.items():

                        if (
                            _normalize_key_name(key)
                            == expected
                        ):
                            value = candidate
                            found = True
                            break

                    if not found:
                        continue

                if isinstance(value, list):
                    resolved_values.extend(value)
                else:
                    resolved_values.append(value)

            current = resolved_values

        else:
            return None

    return current


# ============================================================
# 6. Mapping ownership
#
# Each CSV mapping belongs to the deepest ACTIVE registry node
# that is a valid prefix of the OSCAL_ELEMENT_PATH.
# ============================================================

def get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    oscal_model_key=None
):

    registry_rows = (
        element_registry_df.collect()
    )

    active_paths = []

    for row in registry_rows:

        r = _row_to_dict(row)

        if (
            r.get("IS_ACTIVE") is False
        ):
            continue

        if oscal_model_key is not None:

            row_model = r.get(
                "OSCAL_MODEL_KEY"
            )

            if (
                str(row_model).strip()
                != str(oscal_model_key).strip()
            ):
                continue

        path = r.get("NODE_PATH")

        if path:
            active_paths.append(
                str(path).strip()
            )

    # Deepest paths first
    active_paths = sorted(
        set(active_paths),
        key=lambda p: (
            p.count("."),
            len(p)
        ),
        reverse=True
    )

    owned_mappings = []

    for row in canonical_mapping_df.collect():

        mapping = _row_to_dict(row)

        mapping_path = mapping.get(
            "OSCAL_ELEMENT_PATH"
        )

        if mapping_path is None:
            continue

        mapping_path = str(
            mapping_path
        ).strip()

        if not mapping_path:
            continue

        owner_path = None

        for candidate in active_paths:

            if (
                mapping_path == candidate
                or mapping_path.startswith(
                    candidate + "."
                )
            ):
                owner_path = candidate
                break

        if owner_path != node_path:
            continue

        relative_path = mapping_path[
            len(owner_path):
        ].lstrip(".")

        mapping["OWNER_NODE_PATH"] = (
            owner_path
        )

        mapping["FIELD_RELATIVE_PATH"] = (
            relative_path
        )

        owned_mappings.append(mapping)

    return owned_mappings


# ============================================================
# 7. Nested payload builder
# ============================================================

def set_nested_path(
    container,
    path_segments,
    value
):

    if isinstance(path_segments, str):

        path_segments = [
            x
            for x in path_segments.split(".")
            if x
        ]

    if not path_segments:
        return

    current = container

    for index, raw_segment in enumerate(
        path_segments
    ):

        raw_segment = str(
            raw_segment
        ).strip()

        if not raw_segment:
            continue

        is_array = raw_segment.endswith(
            "[]"
        )

        key = (
            raw_segment[:-2]
            if is_array
            else raw_segment
        )

        is_last = (
            index
            == len(path_segments) - 1
        )

        # --------------------------------------------
        # Final segment
        # --------------------------------------------

        if is_last:

            if is_array:

                if isinstance(value, list):
                    current[key] = value
                else:
                    current[key] = [value]

            else:
                current[key] = value

            return

        # --------------------------------------------
        # Intermediate segment
        # --------------------------------------------

        if is_array:

            if (
                key not in current
                or not isinstance(
                    current[key],
                    list
                )
                or len(current[key]) == 0
                or not isinstance(
                    current[key][0],
                    dict
                )
            ):
                current[key] = [{}]

            current = current[key][0]

        else:

            if (
                key not in current
                or not isinstance(
                    current[key],
                    dict
                )
            ):
                current[key] = {}

            current = current[key]


# ============================================================
# 8. Build singleton payload from owned mappings
# ============================================================

def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):

    source_obj = _parse_source_json(
        source_record
    )

    payload = {}

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        relative_path = mapping.get(
            "FIELD_RELATIVE_PATH"
        )

        relative_path = (
            str(relative_path).strip()
            if relative_path is not None
            else ""
        )

        # Mapping terminates at this node.
        # Preserve Archer field name as payload key.
        if not relative_path:

            payload[
                source_field
            ] = value

        else:

            set_nested_path(
                payload,
                relative_path.split("."),
                value
            )

    return payload


# ============================================================
# 9. Collection instance identity
# ============================================================

def _get_instance_key(
    item,
    instance_key_rule,
    source_field=None
):

    if item is None:
        return None

    rule = str(
        instance_key_rule or ""
    ).strip()

    # ========================================================
    # SOURCE FIELD identity
    #
    # Example:
    # ANTIVIRUS_SCORE      -> ANTIVIRUS_SCORE
    # VULNERABILITY_SCORE  -> VULNERABILITY_SCORE
    #
    # Important for OSCAL props / observations where many
    # scalar values may all be 0.
    # ========================================================

    if (
        _normalize_key_name(rule)
        == _normalize_key_name(
            "SOURCE_FIELD_NAME"
        )
    ):

        if not source_field:
            return None

        return str(
            source_field
        ).strip()

    # ========================================================
    # SOURCE FIELD + scalar value
    # ========================================================

    if (
        _normalize_key_name(rule)
        == _normalize_key_name(
            "SOURCE_FIELD_NAME+VALUE"
        )
    ):

        if not source_field:
            return None

        if isinstance(
            item,
            (dict, list)
        ):
            return None

        return (
            f"{source_field}|{item}"
        )

    # ========================================================
    # SOURCE FIELD + nested item ID
    # ========================================================

    if (
        _normalize_key_name(rule)
        == _normalize_key_name(
            "SOURCE_FIELD_NAME+ID"
        )
    ):

        if (
            not isinstance(item, dict)
            or not source_field
        ):
            return None

        expected = _normalize_key_name(
            "ID"
        )

        for key, value in item.items():

            if (
                _normalize_key_name(key)
                == expected
            ):

                if value is None:
                    return None

                return (
                    f"{source_field}|{value}"
                )

        return None

    # ========================================================
    # Dictionary-key identity
    #
    # Example:
    # CONTENT_ID -> ContentId
    # ========================================================

    if isinstance(item, dict):

        expected = _normalize_key_name(
            rule
        )

        for key, value in item.items():

            if (
                _normalize_key_name(key)
                == expected
            ):
                return value

        return None

    # ========================================================
    # Scalar identity
    # Example:
    # VALUE
    # ========================================================

    return item


# ============================================================
# 10. Parse CURATED_JSON
# ============================================================

def _parse_source_json(source_record):

    record = _row_to_dict(
        source_record
    )

    value = record.get(
        "CURATED_JSON"
    )

    if isinstance(value, str):

        try:
            return json.loads(value)

        except json.JSONDecodeError:
            return {}

    if isinstance(
        value,
        (dict, list)
    ):
        return value

    return {}


# ============================================================
# 11. Extract collection items
# ============================================================

def _extract_collection_items(
    value,
    item_path="$"
):

    if value in (
        None,
        "",
        [],
        {}
    ):
        return []

    path = str(
        item_path or "$"
    ).strip()

    # Source value itself is the collection
    if path in (
        "",
        "$"
    ):

        if isinstance(value, list):
            return value

        return [value]

    extracted = resolve_json_path(
        value,
        path
    )

    if extracted in (
        None,
        "",
        [],
        {}
    ):
        return []

    if isinstance(extracted, list):
        return extracted

    return [extracted]


# ============================================================
# 12. Build collection instances
#
# Supports:
#
#   CONTENT_ID
#   VALUE
#   SOURCE_FIELD_NAME
#   SOURCE_FIELD_NAME+VALUE
#   SOURCE_FIELD_NAME+ID
#   SOURCE_RECORD_ID
# ============================================================

def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    item_path="$"
):

    source_obj = _parse_source_json(
        source_record
    )

    rule = _normalize_key_name(
        instance_key_rule or ""
    )

    # ========================================================
    # A. Record-scoped logical collection
    #
    # Example:
    # assessment-results.results[]
    #
    # There is no physical results[] array in Archer.
    # One logical results[] instance represents one source row.
    # ========================================================

    if (
        rule
        == _normalize_key_name(
            "SOURCE_RECORD_ID"
        )
    ):

        record = _row_to_dict(
            source_record
        )

        raw_record_id = record.get(
            "SOURCE_RECORD_ID"
        )

        if raw_record_id is None:
            return []

        instance_key = str(
            raw_record_id
        ).strip()

        if not instance_key:
            return []

        # Create result only when this logical branch
        # actually has mapped source data.
        has_mapped_data = False

        for mapping in mappings:

            source_field = mapping.get(
                "SOURCE_FIELD_NAME"
            )

            if not source_field:
                continue

            value = resolve_json_path(
                source_obj,
                source_field
            )

            if value not in (
                None,
                "",
                [],
                {}
            ):
                has_mapped_data = True
                break

        if not has_mapped_data:
            return []

        # Structural logical collection parent.
        # Child props / observations own their payload.
        return [
            {
                "INSTANCE_KEY":
                    instance_key,

                "PAYLOAD":
                    {}
            }
        ]

    # ========================================================
    # B. Physical source collection behavior
    #
    # Keeps SSP / POA&M behavior unchanged.
    # ========================================================

    instances = {}

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        items = _extract_collection_items(
            value,
            item_path
        )

        for item in items:

            instance_key = _get_instance_key(
                item,
                instance_key_rule,
                source_field
            )

            if instance_key is None:
                continue

            instance_key = str(
                instance_key
            ).strip()

            if not instance_key:
                continue

            if instance_key not in instances:

                instances[
                    instance_key
                ] = {
                    "INSTANCE_KEY":
                        instance_key,

                    "PAYLOAD":
                        item
                }

            else:

                existing = instances[
                    instance_key
                ]["PAYLOAD"]

                # Preserve richer dictionary payload
                # if duplicate logical reference is seen.
                if (
                    not isinstance(
                        existing,
                        dict
                    )
                    and isinstance(
                        item,
                        dict
                    )
                ):

                    instances[
                        instance_key
                    ]["PAYLOAD"] = item

    return list(
        instances.values()
    )


print(
    "Cell 4 complete - generic OSCAL functions ready"
)
```

After replacing it, run **Cell 4 only**.

You should get:

```text
Cell 4 complete - generic OSCAL functions ready
```

Then stop there — **don’t rerun the Assessment Results graph yet**. Send me `done`, and we’ll add `observations[]` next.
