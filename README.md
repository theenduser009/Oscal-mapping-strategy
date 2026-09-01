Yes — what you’re seeing is expected. The temporary test cell still calls:

build_element_payload(test_record, mappings)

That tests the Cell 4 mapping function, not the Cell 5 collection builder we just changed. So it will still show the Archer-field names and the TBD fields exactly like your screenshot.

Now we need to test the actual Cell 5 result. Don’t change anything else.

Run this new temporary cell:

from snowflake.snowpark.functions import col

(
    canonical_nodes_df
    .filter(
        (col("ELEMENT_TYPE") == "responsible-parties")
        & (col("SOURCE_RECORD_ID") == "565189")
    )
    .select(
        "SOURCE_RECORD_ID",
        "OSCAL_UUID",
        "ELEMENT_JSON"
    )
    .show(50, truncate=False)
)

This is the important test now.

For record 565189, we want separate rows whose ELEMENT_JSON looks like:

{
  "role-id": "system-owner",
  "party-ids": ["111016"]
}

{
  "role-id": "authorizing-official",
  "party-ids": ["217958"]
}

{
  "role-id": "system-security-officer",
  "party-ids": ["218665"]
}

The old test cell can be ignored now. Cell 5 is what we need to validate.

Run the cell above and show me the result. If those rows look right, then we move to Cell 6 validation/load.