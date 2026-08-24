Great — this result gives us the answer cleanly. ✅

```text
Mapped prop fields:              10
Total prop instances:        12,028
Maximum items from one field:     9
Multi-value occurrences:        929
```

So **`SOURCE_FIELD_NAME` alone is not enough**. One field such as `INFORMATION_CLASSIFICATION` can produce several values for the same SSP.

For `props[]`, the correct deterministic instance identity is therefore:

```text
SOURCE_FIELD_NAME + VALUE
```

Example:

```text
INFORMATION_CLASSIFICATION | 162484
INFORMATION_CLASSIFICATION | 162486
INFORMATION_CLASSIFICATION | 162488
```

Those must become three separate `props[]` nodes.

### Next step: one generic enhancement

We already support:

```text
CONTENT_ID
VALUE
SOURCE_FIELD_NAME+ID
```

Now add support for:

```text
SOURCE_FIELD_NAME+VALUE
```

Inside your existing `_get_instance_key()` in Cell 5, add this block **immediately after**:

```python
rule = str(instance_key_rule or "").strip()
```

Add:

```python
# Generic identity for collections where
# one mapped source field can contain multiple scalar values.
if _normalize_key_name(rule) == _normalize_key_name("SOURCE_FIELD_NAME+VALUE"):

    if not source_field:
        return None

    if isinstance(item, (dict, list)):
        return None

    return f"{source_field}|{item}"
```

Nothing else in Cell 5 changes.

Then **do not register `props[]` yet**. Rerun Cell 5 first.

Because `props[]` is still inactive/not registered, our baseline must remain exactly:

```text
Nodes: 76,083
Edges: 73,918
```

If those stay identical, we have safely added the final generic identity pattern needed by the currently mapped SSP branches.

Then we register `props[]` with:

```text
ITEM_PATH         = $
INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+VALUE
```

and the engine should create those **12,028 prop instances automatically**.
