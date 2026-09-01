Yes — now we finally have the complete system-characteristics.props[] mapping group in front of us.

There are 10 source fields mapped to props[]:

7 Extension Property mappings

2 Calculated mappings

1 TBD mapping (DAILY_LOSS_AMOUNT_FROM_OUTAGE appears to be the TBD row)


And for our test SSP 565189, the DIM currently contains only three raw-looking prop values:

0
80658
0

So I would not mark props[] done. The node exists, but those values clearly haven't yet been shaped into meaningful OSCAL prop objects such as name/value metadata.

Next step — identify exactly which source fields produced those values

Don’t change Cell 4 or Cell 5. Run this read-only temporary notebook cell:

from snowflake.snowpark.functions import col

prop_mappings = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH") ==
        "system-security-plan.system-characteristics.props[]"
    )
    .collect()
)

test_record = (
    source_df
    .filter(col("SOURCE_RECORD_ID") == "565189")
    .collect()[0]
)

source_obj = _parse_source_json(test_record)

print("=== SYSTEM CHARACTERISTICS PROP SOURCES ===")

for mapping in prop_mappings:

    source_field = mapping["SOURCE_FIELD_NAME"]
    mapping_type = mapping["MAPPING_TYPE"]

    raw_value = resolve_json_path(
        source_obj,
        source_field
    )

    print(
        source_field,
        "|",
        mapping_type,
        "|",
        raw_value
    )

This gives us, for the same SSP 565189:

CRITICAL_INFRASTRUCTURE | Extension Property | ...
FINANCIAL_SYSTEM        | Extension Property | ...
...

Then we can directly identify where 0, 80658, and 0 came from and decide how an Extension Property is supposed to become an OSCAL prop.

That is the real next step. No writes, no mapper changes yet.