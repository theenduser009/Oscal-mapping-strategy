Excellent — that proves the **40,008 observation nodes are fully reconciled to the 19 exact mappings**. ✅

So this branch is now trustworthy:

```text
assessment-results
    └── results[]
          ├── props[]          6,730
          └── observations[]  40,008   ✅ reconciled
```

Now **do not change the registry yet**. The next thing is to inspect the **18 ambiguous mappings** that say:

```text
assessment-results.results[].observations[] or props[]
```

Run this one read-only cell:

```python
# ============================================================
# Assessment Results — Ambiguous Observation/Prop Profiling
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

ambiguous_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        == "assessment-results.results[].observations[] or props[]"
    )
)

ambiguous_rows = ambiguous_mapping_df.collect()

print("=== AMBIGUOUS OBSERVATION / PROP MAPPINGS ===")
print("Mapping rows:", len(ambiguous_rows))

for mapping_row in ambiguous_rows:

    field = mapping_row["SOURCE_FIELD_NAME"]

    populated = 0
    types_seen = set()
    max_list_length = 0
    samples = []

    for record in source_df.to_local_iterator():

        source_obj = _parse_source_json(record)

        value = resolve_json_path(
            source_obj,
            field
        )

        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        populated += 1
        types_seen.add(
            type(value).__name__
        )

        if isinstance(value, list):
            max_list_length = max(
                max_list_length,
                len(value)
            )

        if len(samples) < 2:
            samples.append(value)

    print("\nFIELD        :", field)
    print("POPULATED    :", populated)
    print("TYPES        :", sorted(types_seen))
    print("MAX LIST     :", max_list_length)

    for sample in samples:
        print("SAMPLE       :", sample)
```

What we want to determine is very simple:

```text
Which of those 18 really belong in observations[]?
Which really belong in props[]?
Which are references and need separate treatment?
```

Run that and send me the output. We won’t guess from the phrase **“or props[]”**.
