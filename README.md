Yes. Cell 3 is now correct. ✅

Now **Cell 4 only**: move the **already-proven generic helper logic** into the production notebook. No SSP-specific element names appear here.

```python
# ============================================================
# Cell 4 — Generic OSCAL Mapping Functions
# PRODUCTION / REUSABLE
# ============================================================

import hashlib
import json
import re


# ------------------------------------------------------------
# A. Generic row helper
# ------------------------------------------------------------

def _row_to_dict(row):
    if row is None:
        return {}

    if isinstance(row, dict):
        return row

    if hasattr(row, "as_dict"):
        return row.as_dict()

    if hasattr(row, "_asdict"):
        return row._asdict()

    return dict(row)


# ------------------------------------------------------------
# B. Frozen deterministic identity contract
# DO NOT CHANGE
# ------------------------------------------------------------

def build_node_seed(source_system, source_table, content_id, node_type):
    cid = content_id.strip() if content_id is not None else ""
    return f"{source_system}|{source_table}|{cid}|{node_type}"


def compute_node_key(seed):
    return hashlib.md5(seed.encode("utf-8")).digest()


def compute_node_uuid(seed):
    return hashlib.md5(seed.encode("utf-8")).hexdigest().lower()


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
    return hashlib.md5(seed.encode("utf-8")).digest()


# ------------------------------------------------------------
# C. Generic JSON/path helpers
# ------------------------------------------------------------

def is_collection_node(node_path):
    return "[]" in str(node_path)


def resolve_json_path(obj, path):

    if obj is None or not path:
        return None

    # Archer commonly stores the source field directly
    if isinstance(obj, dict) and path in obj:
        return obj[path]

    current = obj

    for token in str(path).split("."):

        if not isinstance(current, dict):
            return None

        if token in current:
            current = current[token]
            continue

        # Case/format insensitive fallback
        expected = re.sub(
            r"[^a-z0-9]",
            "",
            token.lower()
        )

        found = False

        for key, value in current.items():

            normalized = re.sub(
                r"[^a-z0-9]",
                "",
                str(key).lower()
            )

            if normalized == expected:
                current = value
                found = True
                break

        if not found:
            return None

    return current


# ------------------------------------------------------------
# D. Resolve mapping ownership from registry
# ------------------------------------------------------------

def get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    oscal_model_key=None
):

    registry_rows = element_registry_df.collect()

    registry_paths = [
        r["NODE_PATH"]
        for r in registry_rows
        if r["NODE_PATH"]
    ]

    # Deepest registered path owns the mapping
    registry_paths = sorted(
        registry_paths,
        key=lambda p: len(str(p).split(".")),
        reverse=True
    )

    result = []

    for row in canonical_mapping_df.collect():

        mapping = _row_to_dict(row)

        full_path = mapping.get(
            "OSCAL_ELEMENT_PATH"
        )

        if not full_path:
            continue

        owner = None

        for registered_path in registry_paths:

            if (
                full_path == registered_path
                or full_path.startswith(
                    registered_path + "."
                )
            ):
                owner = registered_path
                break

        if owner != node_path:
            continue

        relative_path = full_path[
            len(owner):
        ].lstrip(".")

        mapping["OWNER_NODE_PATH"] = owner
        mapping["FIELD_RELATIVE_PATH"] = relative_path

        result.append(mapping)

    return result


# ------------------------------------------------------------
# E. Generic nested payload builder
# ------------------------------------------------------------

def set_nested_path(container, path_segments, value):

    if isinstance(path_segments, str):
        path_segments = [
            p for p in path_segments.split(".")
            if p
        ]

    if not path_segments:
        return

    current = container

    for index, segment in enumerate(path_segments):

        is_last = (
            index == len(path_segments) - 1
        )

        is_array = segment.endswith("[]")

        key = (
            segment[:-2]
            if is_array
            else segment
        )

        if is_last:

            if is_array:
                current[key] = (
                    value
                    if isinstance(value, list)
                    else [value]
                )
            else:
                current[key] = value

            return

        next_segment = path_segments[index + 1]
        next_is_array = next_segment.endswith("[]")

        if key not in current:
            current[key] = [] if is_array else {}

        if is_array:

            if not isinstance(current[key], list):
                current[key] = []

            if not current[key]:
                current[key].append({})

            current = current[key][0]

        else:

            if not isinstance(current[key], dict):
                current[key] = {}

            current = current[key]


def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):

    record = _row_to_dict(source_record)

    source_obj = record.get(
        source_json_field
    )

    if isinstance(source_obj, str):
        try:
            source_obj = json.loads(source_obj)
        except json.JSONDecodeError:
            source_obj = {}

    if not isinstance(source_obj, dict):
        source_obj = {}

    payload = {}

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        relative_path = mapping.get(
            "FIELD_RELATIVE_PATH"
        )

        if not source_field:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (None, "", [], {}):
            continue

        # Collection root mappings are handled
        # by collection extraction logic below.
        if not relative_path:
            continue

        set_nested_path(
            payload,
            relative_path,
            value
        )

    return payload


# ------------------------------------------------------------
# F. Generic collection helpers
# ------------------------------------------------------------

def _normalize_key_name(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


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

    # SOURCE FIELD + scalar value
    if (
        _normalize_key_name(rule)
        == _normalize_key_name(
            "SOURCE_FIELD_NAME+VALUE"
        )
    ):

        if not source_field:
            return None

        if isinstance(item, (dict, list)):
            return None

        return f"{source_field}|{item}"

    # SOURCE FIELD + nested item ID
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

        expected = _normalize_key_name("ID")

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

    # Dictionary key identity
    # Example: CONTENT_ID -> ContentId
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

    # Scalar identity
    # Example: VALUE
    return item


def _parse_source_json(source_record):

    record = _row_to_dict(source_record)

    value = record.get("CURATED_JSON")

    if isinstance(value, str):

        try:
            return json.loads(value)

        except json.JSONDecodeError:
            return {}

    if isinstance(value, (dict, list)):
        return value

    return {}


def _extract_collection_items(
    value,
    item_path
):

    path = str(
        item_path or "$"
    ).strip()

    # Existing direct collection behavior
    if path in ("", "$"):

        return (
            value
            if isinstance(value, list)
            else [value]
        )

    if path.startswith("$."):
        path = path[2:]

    current = [value]

    for token in path.split("."):

        token = token.strip()

        if not token:
            continue

        is_array = token.endswith("[]")

        key_name = (
            token[:-2]
            if is_array
            else token
        )

        next_values = []

        for obj in current:

            if not isinstance(obj, dict):
                continue

            child = None

            if key_name in obj:
                child = obj[key_name]

            else:

                expected = _normalize_key_name(
                    key_name
                )

                for key, candidate in obj.items():

                    if (
                        _normalize_key_name(key)
                        == expected
                    ):
                        child = candidate
                        break

            if child in (
                None,
                "",
                [],
                {}
            ):
                continue

            if (
                is_array
                and isinstance(child, list)
            ):
                next_values.extend(child)

            else:
                next_values.append(child)

        current = next_values

    return current


def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    item_path="$"
):

    source_obj = _parse_source_json(
        source_record
    )

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

                instances[instance_key] = {
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

This Cell 4 contains the exact concepts we already proved in the SSP notebook:

```text
Deterministic node/edge identities
Mapping-path ownership
Nested payload creation
CONTENT_ID
VALUE
SOURCE_FIELD_NAME + ID
SOURCE_FIELD_NAME + VALUE
ITEM_PATH
```

There are **no element names like metadata, props, components, responsible-parties, SSP, etc. inside the logic**.

Run **Cell 4 only**. It should simply finish with:

```text
Cell 4 complete - generic OSCAL functions ready
```

Then Cell 5 will finally be the clean `build_oscal_graph()` function using these helpers.
