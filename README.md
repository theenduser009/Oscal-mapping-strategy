Perfect — **the third level is clean.** ✅

```text
assessment-results            2,165
    └── results[]             2,165
          └── props[]         6,730

Nodes                         11,060
Edges                          8,895
Validation PASSED
```

Yes, we continue deeper. The next branch is `observations[]`, but we have to be careful because the CSV contains both:

```text
assessment-results.results[].observations[]
```

and the ambiguous:

```text
assessment-results.results[].observations[] or props[]
```

We must **not accidentally map those 18 ambiguous fields into observations**.

### Next step only — isolate the clean observation mappings

Run this read-only cell:

```python
# ============================================================
# Assessment Results — Clean Observation Mapping Check
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

clean_observation_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH")
        == "assessment-results.results[].observations[]"
    )
)

print(
    "Exact observation mappings:",
    clean_observation_mapping_df.count()
)

clean_observation_mapping_df.select(
    "SOURCE_FIELD_NAME",
    "OSCAL_ELEMENT_PATH",
    "MAPPING_TYPE"
).show()
```

I expect **19 exact mappings**.

Once that confirms 19, we'll add `observations[]` in a way that uses only those exact mappings and leaves the 18 `"or props[]"` rows untouched for later.
