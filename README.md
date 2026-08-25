Yes — now I can see the whole relevant section. This confirms we **do not need to replace `build_oscal_graph()`**. Its current behavior is correct:

```text
singleton parent → collection child     ✅ supported
collection parent → collection child    ⛔ deliberately blocked
```

For Assessment Results, our first step is only:

```text
assessment-results            singleton
        ↓
assessment-results.results[]  collection
```

So the only missing generic capability is: **create one `results[]` instance using `SOURCE_RECORD_ID`.**

### Replace only `_get_collection_instances()` with this full function

Do **not** change `_get_instance_key()` or `build_oscal_graph()`.

```python
def _get_collection_instances(
    source_record,
    mappings,
    instance_key_rule,
    item_path="$"
):
    """
    Return collection instances for one source record.

    Supported patterns:

    1. Normal source collection
       Example:
           POAMS -> [{"ContentId": 123}, {"ContentId": 456}]
       INSTANCE_KEY_RULE = CONTENT_ID

    2. Record-scoped synthetic collection
       Example:
           assessment-results.results[]
       There is no physical results[] array in Archer.
       One logical result instance represents the source record.
       INSTANCE_KEY_RULE = SOURCE_RECORD_ID
    """

    source_obj = _parse_source_json(source_record)

    rule = _normalize_key_name(
        instance_key_rule or ""
    )

    # ========================================================
    # A. Record-scoped logical collection
    #    One collection instance per source record.
    # ========================================================

    if rule == _normalize_key_name("SOURCE_RECORD_ID"):

        record = _row_to_dict(source_record)

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

        # Do not create an empty logical result when none of
        # the mappings owned by this node have source data.
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

        # Structural payload intentionally empty.
        #
        # The actual observations / props / findings are
        # separate deeper OSCAL structures. We are NOT
        # collapsing those values into the results[] node.
        return [
            {
                "INSTANCE_KEY": instance_key,
                "PAYLOAD": {}
            }
        ]

    # ========================================================
    # B. Existing physical collection behavior
    #    Keep SSP / POA&M behavior unchanged.
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

                instances[instance_key] = {
                    "INSTANCE_KEY": instance_key,
                    "PAYLOAD": item
                }

            else:

                existing = instances[
                    instance_key
                ]["PAYLOAD"]

                # Preserve richer dictionary representation
                # when the same logical reference appears
                # through multiple mapped source fields.
                if (
                    not isinstance(existing, dict)
                    and isinstance(item, dict)
                ):
                    instances[
                        instance_key
                    ]["PAYLOAD"] = item

    return list(
        instances.values()
    )
```

### Why I want the payload `{}` right now

This is intentional.

We discovered fields like:

```text
ANTIVIRUS_SCORE
VULNERABILITY_SCORE
TOTAL_PACKAGE_RISK_SCORE
RISK_ASSESSMENT_REPORT
...
```

are mapped deeper under:

```text
results[].observations[]
results[].props[]
```

and 18 mappings even say:

```text
observations[] or props[]
```

We should **not shove those values into `results[]`** just to make the node nonempty. The `results[]` node is currently a structural parent.

And importantly, **leave this existing protection exactly as it is**:

```python
if len(parent_nodes) != 1:
    raise ValueError(...)
```

We are not ready to enable nested collection relationships yet.

### After replacing the function

Rerun Cell 4 only. It should simply end with:

```text
Cell 4 complete - generic OSCAL functions ready
```

**Do not insert Assessment Results registry rows yet.** After Cell 4 succeeds, tell me `correct`, and I'll give you the exact two registry INSERT rows next.
