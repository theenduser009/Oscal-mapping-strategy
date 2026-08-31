Yes — we can make the lookup fully dynamic so Cell 2 loads all values, including Legacy LOE values, instead of maintaining IDs by hand.

But there are two separate concerns:

1. Resolve Archer ID → Archer label        ✅ fully dynamic
2. Convert that label → FIPS low/mod/high  ⚠ needs a rule for legacy labels

And yes, we can preserve NULL too so those source records do not disappear.

Update Cell 2

Replace the current FIPS_199_VALUE_LOOKUP section with this:

# ====================================================================
# Archer value lookup for Direct/Transform mappings
# Loads ALL Archer select values dynamically
# ====================================================================

from snowflake.snowpark.functions import col

archer_meta_value_df = (
    session.table(
        "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE"
    )
    .select(
        col("SELECT_ID"),
        col("SELECT_VALUE_ID"),
        col("SELECT_VALUE_NAME")
    )
)

# ------------------------------------------------------------
# Full Archer lookup
#
# Example:
# 80654  -> "Low"
# 80655  -> "Moderate"
# 80656  -> "High"
# 162405 -> "Legacy LOE A"
# 162409 -> "Legacy LOE C + DFARS"
# etc.
# ------------------------------------------------------------

ARCHER_VALUE_LOOKUP = {}

for row in archer_meta_value_df.collect():

    value_id = row["SELECT_VALUE_ID"]
    value_name = row["SELECT_VALUE_NAME"]

    if value_id is None:
        continue

    ARCHER_VALUE_LOOKUP[
        str(value_id).strip()
    ] = (
        str(value_name).strip()
        if value_name is not None
        else None
    )


# ------------------------------------------------------------
# FIPS-199 lookup
#
# Current explicit FIPS values are derived dynamically
# from their Archer display names.
# ------------------------------------------------------------

FIPS_199_VALUE_LOOKUP = {}

for value_id, value_name in ARCHER_VALUE_LOOKUP.items():

    if value_name is None:
        continue

    normalized_name = value_name.strip().lower()

    if normalized_name in (
        "low",
        "moderate",
        "high"
    ):
        FIPS_199_VALUE_LOOKUP[
            value_id
        ] = normalized_name


print("=== ARCHER VALUE LOOKUP ===")
print("Total Archer values:", len(ARCHER_VALUE_LOOKUP))

print("\n=== FIPS-199 LOOKUP ===")
print(FIPS_199_VALUE_LOOKUP)

That means no hard-coded 80654, 80655, 80656 anymore. It discovers them from ARCHER_META_VALUE.

Cell 4 — preserve NULL

Your existing transform_mapping_value() should stay, except change its behavior for an unresolved/null value.

At the very beginning, after mapping_type, add:

# Preserve source NULL
if value is None:
    return None

Then inside build_element_payload(), we need to stop automatically throwing away None for Direct/Transform.

Replace:

if value in (
    None,
    "",
    [],
    {}
):
    continue

with:

mapping_type = str(
    mapping.get("MAPPING_TYPE") or ""
).strip().lower()

# For normal mappings, empty values are skipped.
if mapping_type != "direct/transform":
    if value in (
        None,
        "",
        [],
        {}
    ):
        continue

# For Direct/Transform:
# preserve explicit NULL but skip empty structures/strings.
else:
    if value in (
        "",
        [],
        {}
    ):
        continue

So a Direct/Transform source that is NULL can now reach:

set_nested_path(...)

and be represented explicitly as:

"security-objective-confidentiality": null

instead of silently removing the record.

Legacy values

Cell 2 will now dynamically know:

162405 → Legacy LOE A
162406 → Legacy LOE B
162407 → Legacy LOE C
162409 → Legacy LOE C + DFARS
162410 → Legacy LOE D
162411 → Legacy LOE D + DFARS

But I would not automatically turn those labels into low/moderate/high yet. The metadata tells us their names, but not their FIPS equivalence.

So after these changes we have:

NULL                  → preserved
80654 / Low           → low
80655 / Moderate      → moderate
80656 / High          → high
Legacy LOE IDs        → dynamically recognized,
                         awaiting FIPS equivalence rule

That gives us a clean system: all Archer values are loaded dynamically, nothing is forgotten, and the only remaining business rule is Legacy LOE → FIPS-199.