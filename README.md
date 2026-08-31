Right — don’t hard-code or search for a SOURCE_RECORD_ID first. Let the notebook find a record whose actual parsed CURATED_JSON contains HARDWARE.

Run this read-only cell:

import json

found = False

for record in source_df.collect():

    source_obj = _parse_source_json(record)

    hardware_value = resolve_json_path(
        source_obj,
        "HARDWARE"
    )

    if hardware_value not in (
        None,
        "",
        [],
        {}
    ):

        print(
            "SOURCE_RECORD_ID:",
            record["SOURCE_RECORD_ID"]
        )

        print("\nHARDWARE:")

        print(
            json.dumps(
                hardware_value,
                indent=2,
                default=str
            )
        )

        found = True
        break


if not found:
    print("NO HARDWARE VALUE FOUND")

This removes the questionable Snowpark JSON filter entirely.

What we want next is an actual result like:

[
  {
    "ContentId": 123456,
    "LevelId": 354
  }
]

Once we get that, that exact LevelId + ContentId pair becomes our first Reference traversal test. Don’t change any production cells yet.