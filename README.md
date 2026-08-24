Yes — this output is useful, and **Cell 8 has finished its job. We do not need to revisit it.** ✅

From the actual mapping dataframe, the SSP structure we have discovered so far is:

```text
system-security-plan                         ACTIVE
│
├── metadata                                ACTIVE
│   ├── document-ids[]                      NOT REGISTERED
│   └── responsible-parties[]               NOT REGISTERED
│
├── system-characteristics                  ACTIVE
│   ├── props[]                             NOT REGISTERED
│   └── system-ids[]                        NOT REGISTERED
│
└── system-implementation                   ACTIVE
    └── components[]                        ACTIVE
```

And importantly, Cell 8 found **21 actual SSP mapping paths**. It did **not** show `control-implementation`, `back-matter`, or `import-profile` among these current SSP paths, so we should not invent them.

### What we need next

We have exactly **four unresolved collection nodes**:

```text
metadata.document-ids[]
metadata.responsible-parties[]
system-characteristics.props[]
system-characteristics.system-ids[]
```

We should **not blindly assign `CONTENT_ID`** like we did for `components[]`. These could contain normal OSCAL values/objects rather than Archer `{ContentId, LevelId}` references.

So the next step is one single read-only inspection — **all four together**, not four more cells.

Run this as the next temporary cell:

```python
# ============================================================
# Inspect Remaining SSP Collection Nodes
# READ ONLY — one-time inspection
# ============================================================

from snowflake.snowpark.functions import col

collection_paths = [
    "system-security-plan.metadata.document-ids[]",
    "system-security-plan.metadata.responsible-parties[]",
    "system-security-plan.system-characteristics.props[]",
    "system-security-plan.system-characteristics.system-ids[]"
]

for node_path in collection_paths:

    print("\n" + "=" * 80)
    print("NODE:", node_path)

    mappings = (
        canonical_mapping_df
        .filter(col("OSCAL_ELEMENT_PATH").startswith(node_path))
        .select(
            "SOURCE_FIELD_NAME",
            "OSCAL_ELEMENT_PATH"
        )
        .collect()
    )

    for m in mappings:

        source_field = m["SOURCE_FIELD_NAME"]

        print("\nSOURCE FIELD:", source_field)
        print("OSCAL PATH:", m["OSCAL_ELEMENT_PATH"])

        samples = 0

        for record in source_df.to_local_iterator():

            source_obj = _parse_source_json(record)
            value = resolve_json_path(source_obj, source_field)

            if value in (None, "", [], {}):
                continue

            print("TYPE:", type(value).__name__)
            print("VALUE:", str(value)[:700])

            samples += 1

            if samples >= 2:
                break

        print("Samples found:", samples)
```

This answers only one question:

**What are these four collections actually made of?**

Then we can set the correct registry identity for all four at once and continue the SSP hierarchy through DIM + FACT using the existing engine.

No changes to Cells 3–7. No more guessing.
