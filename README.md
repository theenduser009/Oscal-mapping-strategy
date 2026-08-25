Yep — these outputs are very useful. We **should not send all 18 ambiguous fields to `observations[]` or `props[]` blindly**.

From what you showed, they split naturally:

* **10 populated scalar risk/score fields** → treat as `observations[]`
* **5 reference/list fields** → leave unresolved for now; these likely point to other Archer records/tables, similar to what we discovered with POA&M
* **3 currently empty fields** → no nodes for now

For example, these are clearly scalar measurements:

```text
TOTAL_PACKAGE_INHERENT_RISK
TOTAL_PACKAGE_RESIDUAL_RISK
ADJUSTED_TOTAL_RISK_SCORE
ADJUSTED_AVERAGE_RISK_SCORE
CURRENT_HIGHEST_DEVICE_RISK_SCORE
CURRENT_AVERAGE_DEVICE_RISK_SCORE
CURRENT_CONTROL_RISK_SCORE
BASELINE_HIGHEST_DEVICE_RISK_SCORE
BASELINE_AVERAGE_DEVICE_RISK_SCORE
BASELINE_CONTROL_RISK_SCORE
```

But these need separate reference handling later:

```text
RISK_ACCEPTANCE_RBDS
RISK_ASSESSMENT
_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD
_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD
RISK_ASSESSMENT_REPORT
```

For example, `RISK_ACCEPTANCE_RBDS` contains `ContentId` + `LevelId 349`, which is a strong signal that it's a reference rather than a score value.

### Next step only

Don't change the registry. Add a **temporary resolved Assessment Results mapping** in the notebook:

```python
# ============================================================
# Assessment Results — Resolve Scalar Ambiguous Mappings
# ============================================================

from snowflake.snowpark.functions import col, lit, when

scalar_observation_fields = [
    "TOTAL_PACKAGE_INHERENT_RISK",
    "TOTAL_PACKAGE_RESIDUAL_RISK",
    "ADJUSTED_TOTAL_RISK_SCORE",
    "ADJUSTED_AVERAGE_RISK_SCORE",
    "CURRENT_HIGHEST_DEVICE_RISK_SCORE",
    "CURRENT_AVERAGE_DEVICE_RISK_SCORE",
    "CURRENT_CONTROL_RISK_SCORE",
    "BASELINE_HIGHEST_DEVICE_RISK_SCORE",
    "BASELINE_AVERAGE_DEVICE_RISK_SCORE",
    "BASELINE_CONTROL_RISK_SCORE"
]

ambiguous_path = (
    "assessment-results.results[].observations[] or props[]"
)

observation_path = (
    "assessment-results.results[].observations[]"
)

assessment_mapping_resolved_df = (
    assessment_mapping_df
    .with_column(
        "OSCAL_ELEMENT_PATH",
        when(
            (col("OSCAL_ELEMENT_PATH") == ambiguous_path)
            &
            (col("SOURCE_FIELD_NAME").isin(scalar_observation_fields)),
            lit(observation_path)
        ).otherwise(col("OSCAL_ELEMENT_PATH"))
    )
)

print(
    "Resolved scalar mappings:",
    assessment_mapping_resolved_df
    .filter(
        (col("OSCAL_ELEMENT_PATH") == observation_path)
        &
        (col("SOURCE_FIELD_NAME").isin(scalar_observation_fields))
    )
    .count()
)
```

Expected:

```text
Resolved scalar mappings: 10
```

Stop there and send me that result.

If it says **10**, then we will use this resolved DataFrame in the existing graph test. Based on the source counts you showed, those 10 fields should contribute another **17,360 observation nodes**, so we have a very strong reconciliation number to test against next.
