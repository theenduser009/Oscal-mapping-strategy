No — I do not need the whole JSON. That output is too much and will just slow us down.

What we need is only the 10 props[] Archer fields, and preferably only the ones that actually have values. Since those fields live inside CURATED_JSON, use our existing parser instead of source_df.select(...).

Run this temporary read-only cell:

prop_fields = [
    "FISMA_REPORTABLE",
    "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL",
    "CRITICAL_INFRASTRUCTURE",
    "PACKAGE_TYPE",
    "HELPER_PTA_CALC",
    "PACKAGE_TYPE_HELPER_CALC",
    "PIA_REQUIRED",
    "INFORMATION_CLASSIFICATION",
    "DAILY_LOSS_AMOUNT_FROM_OUTAGE"
]

shown = 0

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)

    populated = {}

    for field in prop_fields:
        value = resolve_json_path(source_obj, field)

        if value not in (None, "", [], {}):
            populated[field] = value

    if populated:
        print(
            "\nSOURCE_RECORD_ID:",
            record["SOURCE_RECORD_ID"]
        )

        for field, value in populated.items():
            print(field, "=", value)

        shown += 1

    if shown >= 10:
        break

This will give us 10 real SSP records with only populated prop fields, for example:

SOURCE_RECORD_ID: 565189
PACKAGE_TYPE = [80658]
PACKAGE_TYPE_HELPER_CALC = 0

That is exactly the information we need. No full JSON, no writes, no changes to Cells 4–6.

Run this and show me the output. Then we can design props[] correctly.