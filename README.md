Yes — **that is the right approach**, and your diagram exposes something important we missed.

Our earlier SSP inventory logic mainly surfaced:

* direct children of `system-security-plan`
* anything containing `[]`

So it **did not surface deeper singleton objects** such as:

```text
system-characteristics
├── system-information
├── security-impact-level
├── status
├── authorization-boundary
├── network-architecture
└── data-flow
```

Those can absolutely need registry nodes too, depending on what is actually mapped and populated.

So from here, the rule should be:

> **Mapping file tells us the OSCAL path → raw data tells us whether/population shape → registry defines the structural node.**

We keep expanding SSP downward until the mapped SSP hierarchy is exhausted. We do **not** production-wrap yet.

### Next step only

Let's inspect the **actual mapped paths and source values under `system-characteristics`**, because your diagram shows that branch clearly.

Run this read-only cell:

```python
# ============================================================
# Inspect all deeper System Characteristics mappings
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

BASE_PATH = "system-security-plan.system-characteristics"

sc_mappings = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(BASE_PATH + ".")
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH"
    )
    .distinct()
    .sort("OSCAL_ELEMENT_PATH", "SOURCE_FIELD_NAME")
    .collect()
)

print("System-characteristics mapping rows:", len(sc_mappings))

for m in sc_mappings:

    source_field = m["SOURCE_FIELD_NAME"]
    oscal_path = m["OSCAL_ELEMENT_PATH"]

    print("\n" + "=" * 80)
    print("SOURCE FIELD:", source_field)
    print("OSCAL PATH :", oscal_path)

    samples = 0

    for record in source_df.to_local_iterator():

        source_obj = _parse_source_json(record)
        value = resolve_json_path(source_obj, source_field)

        if value in (None, "", [], {}):
            continue

        print("TYPE       :", type(value).__name__)
        print("VALUE      :", str(value)[:500])

        samples += 1

        if samples >= 2:
            break

    print("Samples found:", samples)
```

This will tell us, from your **real 608-row mapping and real Archer data**, whether mappings exist for things like:

```text
status.*
authorization-boundary.*
network-architecture.*
data-flow.*
system-information.*
security-impact-level.*
```

Then we add only the confirmed structural nodes to the registry.

And yes — **we continue doing this downward through SSP** before moving to POA&M or wrapping the production mapper. This is the complete cycle we were aiming for.
