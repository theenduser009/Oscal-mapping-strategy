Yes — **19 exact `observations[]` mappings confirmed.** ✅

But before we add `observations[]` to the registry, we caught an important issue: many of those score fields have the value `0`. Your current `_get_instance_key()` does **not explicitly implement `SOURCE_FIELD_NAME` for scalar values**; it eventually falls back to the value itself. That could collapse several different score fields with value `0` into one observation.

### Next step only

In **Mapper V1 → Cell 4 → `_get_instance_key()`**, immediately after this:

```python
rule = str(
    instance_key_rule or ""
).strip()
```

add:

```python
# SOURCE FIELD identity
if (
    _normalize_key_name(rule)
    == _normalize_key_name("SOURCE_FIELD_NAME")
):
    if not source_field:
        return None

    return str(source_field).strip()
```

So it becomes:

```python
rule = str(
    instance_key_rule or ""
).strip()

# SOURCE FIELD identity
if (
    _normalize_key_name(rule)
    == _normalize_key_name("SOURCE_FIELD_NAME")
):
    if not source_field:
        return None

    return str(source_field).strip()

# SOURCE FIELD + scalar value
...
```

**Change nothing else.**

Then rerun **Cell 4 only** and make sure you get:

```text
Cell 4 complete - generic OSCAL functions ready
```

This also makes the existing `SOURCE_FIELD_NAME` registry rule behave exactly as its name says. After that we'll safely add `observations[]` without the zero-score fields collapsing together.
