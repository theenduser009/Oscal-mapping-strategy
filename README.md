Perfect — now we have the Reference inventory.

For SSP, the Reference mappings feeding system-security-plan.system-implementation.components[] are these six Archer fields:

HARDWARE
INTERCONNECTIONS
INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM
SAP_INTAKE_FORM_INTERCONNECTIONS
SOFTWARE
SUBSYSTEMS

The other two shown are for different models:

FINDINGS → Assessment Results
POAMS    → POA&M

So we should not touch registry or Cells 1–7 yet. The next step is to inspect the physical reference structure for one SSP field first — start with HARDWARE.

Run this read-only cell:

import json
from snowflake.snowpark.functions import col

# Find one SSP record containing a HARDWARE reference
rows = (
    source_df
    .filter(
        col("CURATED_JSON")["HARDWARE"].is_not_null()
    )
    .select(
        "SOURCE_RECORD_ID",
        "CURATED_JSON"
    )
    .limit(1)
    .collect()
)

record = rows[0]

source_obj = _parse_source_json(record)

print("SOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])
print("\nHARDWARE:")
print(
    json.dumps(
        source_obj.get("HARDWARE"),
        indent=2,
        default=str
    )
)

What we expect is something like:

[
  {
    "ContentId": 572500,
    "LevelId": 354
  }
]

That is the starting point for Tim’s design:

HARDWARE → LevelId → resolve Archer table → ContentId → fetch referenced row.

Show me that output. Then we build the first resolver around one reference field only, prove it works, and generalize it to the other five.