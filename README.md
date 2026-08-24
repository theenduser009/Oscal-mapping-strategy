This is a very useful result. Now we can say something much stronger about the **actual Archer data**, not just the OSCAL registry.

Your raw Authorization Package has:

```text
Populated raw fields     : 393
Already present in mapping: 388
Populated but unmapped     : 5
```

The only populated source fields outside the mapping are:

```text
INHERENT_RISK_OVERALL_SCORE                         2165 records
FIELD_31745                                         2165
FIELD_31744                                          531
HELPER_BUSINESS_CRITICALITY_MOST_RECENT_OVERALL_SCORE 13
FIELD_31747                                            6
```

So we should **not start exploding hundreds of fields again**. We have reduced the actual source-data gap to these five.

Also, don't automatically map these five into SSP. Names like `HELPER_...` or risk scores may be Archer operational/calculated fields rather than OSCAL SSP content. And `FIELD_31745`, etc. are opaque, so we need to see what they actually contain before deciding.

### Next step only: inspect these five

Run this read-only cell:

```python
# ============================================================
# Inspect populated unmapped Archer fields
# READ ONLY
# ============================================================

UNMAPPED_FIELDS = [
    "INHERENT_RISK_OVERALL_SCORE",
    "FIELD_31745",
    "FIELD_31744",
    "HELPER_BUSINESS_CRITICALITY_MOST_RECENT_OVERALL_SCORE",
    "FIELD_31747"
]

for field_name in UNMAPPED_FIELDS:

    print("\n" + "=" * 80)
    print("FIELD:", field_name)

    samples = 0

    for record in source_df.to_local_iterator():

        source_obj = _parse_source_json(record)

        value = resolve_json_path(
            source_obj,
            field_name
        )

        if value in (None, "", [], {}):
            continue

        print(
            "SOURCE_RECORD_ID:",
            record["SOURCE_RECORD_ID"]
        )
        print("TYPE :", type(value).__name__)
        print("VALUE:", str(value)[:1000])

        samples += 1

        if samples >= 5:
            break

    print("Samples found:", samples)
```

Then we classify each one as either:

```text
Should map to SSP
Should map to another OSCAL model
Archer helper/calculated field — intentionally excluded
Unknown — mapping team needs to identify it
```

One important clarification: this 393-vs-388 audit proves **top-level Archer field coverage**. Our separate SSP path audit already proved the mapped SSP hierarchy has `0` missing structural nodes. Together, these two checks are getting us very close to genuinely saying: **we examined the actual data and the SSP mapping end-to-end**, rather than simply trusting the CSV.
