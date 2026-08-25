Yes — now we have the exact picture. This is important.

Your 45 Assessment Results mappings break down as:

```text
1   → assessment-results.results[].findings[]
19  → assessment-results.results[].observations[]
18  → assessment-results.results[].observations[] or props[]
7   → assessment-results.results[].props[]
```

Two things matter before we touch the registry:

1. `observations[] or props[]` is **not a real executable OSCAL path**. It is a mapping/design choice recorded in the CSV. We eventually have to resolve those 18 rows to one real branch.
2. More importantly, everything sits underneath `results[]`, but there is **no direct mapping that creates/identifies a `results[]` instance**. Because `results[]` is itself a collection, we cannot safely assume how many result instances belong to each Authorization Package.

So **do not change the mapper or registry yet.**

### Next step — inspect the actual source data for all 45 fields

Add one read-only cell:

```python
# ============================================================
# Assessment Results — Source Data Profile
# READ ONLY
# ============================================================

assessment_mapping_rows = (
    assessment_results_paths
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .collect()
)

profiles = []

for m in assessment_mapping_rows:

    field = m["SOURCE_FIELD_NAME"]
    path = m["OSCAL_ELEMENT_PATH"]
    mapping_type = m["MAPPING_TYPE"]

    populated = 0
    value_types = set()
    max_list_length = 0
    samples = []

    for record in source_df.to_local_iterator():

        source_obj = _parse_source_json(record)
        value = resolve_json_path(source_obj, field)

        if value in (None, "", [], {}):
            continue

        populated += 1
        value_types.add(type(value).__name__)

        if isinstance(value, list):
            max_list_length = max(
                max_list_length,
                len(value)
            )

        if len(samples) < 2:
            samples.append(str(value)[:250])

    profiles.append({
        "field": field,
        "path": path,
        "mapping_type": mapping_type,
        "populated": populated,
        "types": ",".join(sorted(value_types)),
        "max_list_length": max_list_length,
        "samples": samples
    })


print("=== ASSESSMENT RESULTS SOURCE PROFILE ===")

for p in profiles:

    print("\nFIELD       :", p["field"])
    print("PATH        :", p["path"])
    print("MAPPING TYPE:", p["mapping_type"])
    print("POPULATED   :", p["populated"])
    print("TYPES       :", p["types"])
    print("MAX LIST    :", p["max_list_length"])

    for sample in p["samples"]:
        print("SAMPLE      :", sample)
```

What I'm particularly looking for is something like:

```text
FINDINGS
TYPE: list
SAMPLE: [{"ContentId": ..., "LevelId": ...}]

SECURITY_COMPLIANCE_SCORE
TYPE: int / float

RISK_ASSESSMENT
TYPE: list or scalar
```

That will tell us whether `results[]` should effectively be **one result per Authorization Package**, and which of those ambiguous 18 fields should become `observations[]` versus `props[]`.

Run this cell and show me the output, especially `FINDINGS` and a few of the score/risk fields. We won't touch the working generic mapper until the data answers that question.
