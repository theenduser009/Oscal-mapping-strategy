Yes — I’m thinking the same thing looking at this output. This inventory gives us a much clearer priority.

The strongest **model #3 candidate is Assessment Results**:

```text
Assessment Results        38 mappings
Extension Properties       7 mappings
                           ──
assessment-results root   ~45 mappings potentially
```

Compare that with:

```text
Security Assessment Plan   3 mappings
Profile                    2 mappings
POA&M                      1 mapping   ✅ already done
```

Also, just like SSP was split across labels such as `SSP - Metadata`, `SSP - System Characteristics`, etc., we should **not assume `OSCAL_MODEL` alone defines the complete model**. The important thing is the actual `OSCAL_ELEMENT_PATH`.

So I would go next with:

```text
assessment-results
```

But **do not register anything yet**.

### Next step only

Let's inventory every path underneath `assessment-results`, including those labeled `Extension Properties`.

Run:

```python
from snowflake.snowpark.functions import col

assessment_results_paths = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(
            "assessment-results"
        )
    )
    .select(
        "SOURCE_FIELD_NAME",
        "OSCAL_MODEL",
        "OSCAL_ELEMENT_PATH",
        "MAPPING_TYPE"
    )
    .sort("OSCAL_ELEMENT_PATH")
)

print(
    "Assessment-results mapping rows:",
    assessment_results_paths.count()
)

assessment_results_paths.show()
```

That will tell us the **real branch structure** for Assessment Results before we touch the registry.

Send me that output next.
