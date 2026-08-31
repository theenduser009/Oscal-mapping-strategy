Yep — let’s simplify this completely. You only need 3 updates. No more mixed versions.

First, Cell 2: add the Archer lookup loader at the end of Cell 2. Keep your existing Cell 2 code, then append this:

# ====================================================================
# Archer value lookup for Direct/Transform mappings
# ====================================================================

from snowflake.snowpark.functions import col

archer_meta_value_df = (
    session.table(
        "RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE"
    )
    .select(
        col("SELECT_VALUE_ID"),
        col("SELECT_VALUE_NAME")
    )
    .filter(
        col("SELECT_VALUE_NAME").is_not_null()
    )
)

FIPS_199_VALUE_LOOKUP = {}

for row in archer_meta_value_df.collect():

    value_id = row["SELECT_VALUE_ID"]

    value_name = str(
        row["SELECT_VALUE_NAME"]
    ).strip().lower()

    if value_name in (
        "low",
        "moderate",
        "high"
    ):
        FIPS_199_VALUE_LOOKUP[
            str(value_id)
        ] = value_name


print("=== FIPS-199 LOOKUP ===")
print(FIPS_199_VALUE_LOOKUP)

You should see at least:

80654 -> low
80655 -> moderate
80656 -> high

Second, Cell 4: delete the old hard-coded block you added earlier:

FIPS_199_VALUE_MAP = {
    "80654": "low",
    "80655": "moderate",
    "80656": "high",
}

Delete that old transform_mapping_value() too.

Then, in Cell 4, immediately before build_element_payload(), add this replacement:

# ====================================================================
# Direct/Transform handler
# ====================================================================

def transform_mapping_value(
    value,
    mapping
):

    mapping_type = str(
        mapping.get("MAPPING_TYPE") or ""
    ).strip().lower()

    # Direct stays unchanged
    if mapping_type == "direct":
        return value

    # Reference is Phase 2
    if mapping_type == "reference":
        return value

    # Other mapping types stay unchanged
    if mapping_type != "direct/transform":
        return value

    target_path = str(
        mapping.get("OSCAL_ELEMENT_PATH") or ""
    ).strip().lower()

    # Only FIPS-199 objectives for now
    if not (
        target_path.endswith(
            "security-objective-confidentiality"
        )
        or target_path.endswith(
            "security-objective-integrity"
        )
        or target_path.endswith(
            "security-objective-availability"
        )
    ):
        return value

    # Archer select values are usually arrays
    if isinstance(value, list):

        for item in value:

            resolved = FIPS_199_VALUE_LOOKUP.get(
                str(item).strip()
            )

            if resolved is not None:
                return resolved

        return None

    return FIPS_199_VALUE_LOOKUP.get(
        str(value).strip()
    )

Third, still in Cell 4, go inside your existing build_element_payload().

Find this:

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

Replace only that little section with:

value = resolve_json_path(
    source_obj,
    source_field
)

value = transform_mapping_value(
    value,
    mapping
)

if value in (
    None,
    "",
    [],
    {}
):
    continue

That’s it. Do not change Cell 5 or Cell 6. Do not change registry.

For testing, keep Cell 1:

"EXECUTE_WRITES": False

Then run:

Cell 2
Cell 4
Cell 5

After that, rerun the same security-impact-level payload test for record 866211.

We want to see:

{
  "security-objective-confidentiality": "low",
  "security-objective-integrity": "low",
  "security-objective-availability": "low"
}

If you get that, the first Direct/Transform implementation is working.