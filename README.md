Yes — now I have the exact Cell 5. We can make this **surgically** without rewriting the working engine.

Do **only these 3 edits in Cell 5**. This enhancement adds `ITEM_PATH` support while preserving the current SSP baseline.

### 1. Replace `_get_instance_key()` with this

```python
def _get_instance_key(item, instance_key_rule, source_field=None):
    if item is None:
        return None

    rule = str(instance_key_rule or "").strip()

    # Generic composite identity:
    # source mapping field + nested item ID
    if _normalize_key_name(rule) == _normalize_key_name("SOURCE_FIELD_NAME+ID"):
        if not isinstance(item, dict) or not source_field:
            return None

        expected = _normalizeize_key_name("ID")
        for key, value in item.items():
            if _normalize_key_name(key) == expected:
                if value is None:
                    return None
                return f"{source_field}|{value}"

        return None

    # Existing dictionary-key behavior
    if isinstance(item, dict):
        expected = _normalize_key_name(rule)

        for key, value in item.items():
            if _normalize_key_name(key) == expected:
                return value

        return None

    # Existing scalar behavior
    return item
```

**Important typo correction:** use `_normalize_key_name`, not `_normalizeize_key_name`.

So this line:

```python
expected = _normalizeize_key_name("ID")
```

must actually be:

```python
expected = _normalize_key_name("ID")
```

### 2. Add this helper immediately before `_get_collection_instances()`

```python
def _extract_collection_items(value, item_path):
    """
    Generic extraction of collection items from a mapped source value.

    Examples:
        $            -> value itself
        UserList[]   -> value["UserList"]
    """

    path = str(item_path or "$").strip()

    # Existing behavior
    if path in ("", "$"):
        return value if isinstance(value, list) else [value]

    if path.startswith("$."):
        path = path[2:]

    current = [value]

    for token in path.split("."):
        token = token.strip()

        if not token:
            continue

        is_array = token.endswith("[]")
        key_name = token[:-2] if is_array else token

        next_values = []

        for obj in current:
            if not isinstance(obj, dict):
                continue

            child = None

            # Exact key first
            if key_name in obj:
                child = obj[key_name]
            else:
                # Case/format-insensitive fallback
                expected = _normalize_key_name(key_name)

                for key, candidate in obj.items():
                    if _normalize_key_name(key) == expected:
                        child = candidate
                        break

            if child in (None, "", [], {}):
                continue

            if is_array and isinstance(child, list):
                next_values.extend(child)
            else:
                next_values.append(child)

        current = next_values

    return current
```

Then replace your current `_get_collection_instances()` with:

```python
def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    item_path="$"
):
    source_obj = _parse_source_json(source_record)
    instances = {}

    for mapping in mappings:
        source_field = mapping.get("SOURCE_FIELD_NAME")

        if not source_field:
            continue

        value = resolve_json_path(source_obj, source_field)

        if value in (None, "", [], {}):
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

            instance_key = str(instance_key).strip()

            if not instance_key:
                continue

            if instance_key not in instances:

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "PAYLOAD": item
                }

            else:
                # Preserve existing richer-dictionary behavior
                existing = instances[instance_key]["PAYLOAD"]

                if (
                    not isinstance(existing, dict)
                    and isinstance(item, dict)
                ):
                    instances[instance_key]["PAYLOAD"] = item

    return list(instances.values())
```

### 3. Tiny change around your current lines 118–124

You currently have:

```python
is_collection = registry_row["IS_COLLECTION"]
instance_key_rule = registry_row["INSTANCE_KEY_RULE"]
mappings = mappings_by_node.get(node_path, [])

if is_collection or "[]" in node_path:
    instances = _get_collection_instances(
        source_record,
        mappings,
        instance_key_rule
    )
```

Change **only that section** to:

```python
is_collection = registry_row["IS_COLLECTION"]
instance_key_rule = registry_row["INSTANCE_KEY_RULE"]
item_path = registry_row["ITEM_PATH"] or "$"

mappings = mappings_by_node.get(node_path, [])

if is_collection or "[]" in node_path:

    instances = _get_collection_instances(
        source_record,
        mappings,
        instance_key_rule,
        item_path
    )
```

That's it. **Nothing else in Cell 5 changes.**

Before running Cell 5, rerun **Cell 3 once** so `element_registry_df` sees the new `ITEM_PATH` column.

Then run Cell 5.

### Critical checkpoint

Because `responsible-parties[]` is **not registered yet**, the output must remain exactly:

```text
Canonical nodes: 66,118
Canonical edges: 63,953
```

If those numbers change, **stop**. We do not proceed.

If they remain identical, we have proven the enhancement is backward-compatible. Then we register:

```text
responsible-parties[]
ITEM_PATH         = UserList[]
INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+ID
```

and let the same engine handle it.
