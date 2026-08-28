Good — now we finally have the full Cell 4, and I would not change it yet.

The missing piece is not the code anymore. It is this:

What exactly is inside TRANSFORMATION_LOGIC for the Direct/Transform rows?

We should not invent transformation behavior. First inspect the actual rules your CSV defines.

Run this one read-only cell:

from snowflake.snowpark.functions import col

print("=== DIRECT / TRANSFORM RULES ===")

(
    canonical_mapping_df
    .filter(
        col("MAPPING_TYPE") == "Direct/Transform"
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE",
        "TRANSFORMATION_LOGIC"
    )
    .sort(
        "OSCAL_ELEMENT_PATH",
        "SOURCE_FIELD_NAME"
    )
    .show(100)
)

If the output is too wide, run this instead:

rows = (
    canonical_mapping_df
    .filter(
        col("MAPPING_TYPE") == "Direct/Transform"
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "TRANSFORMATION_LOGIC"
    )
    .collect()
)

for r in rows:
    print(
        r["SOURCE_FIELD_NAME"],
        "->",
        r["OSCAL_ELEMENT_PATH"],
        "| LOGIC:",
        r["TRANSFORMATION_LOGIC"]
    )

Why this is the next step

Right now we know:

Direct             ✅ implemented
Direct/Transform   ❌ copied directly today
Reference          ⏸ Phase 2

But before I modify Cell 4, I need to know whether TRANSFORMATION_LOGIC contains things like:

map ID → label
take first value
convert date
normalize Yes/No
lookup security category
strip HTML
concatenate fields

Each needs different behavior.

So do not touch Cell 4 yet. Run this and send me the transformation-rule output. Then we can design one controlled transformation handler instead of creating another week of patches.