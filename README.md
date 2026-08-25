Perfect. ✅ Now **do not write yet**. Next we point the already-built Assessment Results graph at those new tables and run the standard loader with the write gate OFF.

Add one new cell at the bottom of `NB_ARCHER_OSCAL_MAPPER_V1`:

```python
# ============================================================
# Assessment Results — Target Validation
# READ ONLY
# ============================================================

ASSESSMENT_RESULTS_CONFIG = dict(CONFIG)

ASSESSMENT_RESULTS_CONFIG["OSCAL_MODEL"] = "ASSESSMENT_RESULTS"

ASSESSMENT_RESULTS_CONFIG["TARGET_DIM"] = (
    "RTX_ENTERPRISESERVICES_DEV."
    "ES_ESC_GRC_CURATED."
    "DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT"
)

ASSESSMENT_RESULTS_CONFIG["DIM_PK_COLUMN"] = (
    "PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT_HASH"
)

ASSESSMENT_RESULTS_CONFIG["TARGET_FACT"] = (
    "RTX_ENTERPRISESERVICES_DEV."
    "ES_ESC_GRC_CURATED."
    "FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY"
)

ASSESSMENT_RESULTS_CONFIG["FACT_PK_COLUMN"] = (
    "PK_FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY_HASH"
)

ASSESSMENT_RESULTS_CONFIG["EXECUTE_WRITES"] = False


assessment_validation = validate_and_load_oscal(
    canonical_nodes_df=assessment_nodes_df,
    canonical_edges_df=assessment_edges_df,
    config=ASSESSMENT_RESULTS_CONFIG
)
```

Expected result should be:

```text
Nodes               : 4330
Edges               : 2165
Null node keys      : 0
Duplicate node keys : 0
Null edge keys      : 0
Duplicate edge keys : 0
Missing parents     : 0
Missing children    : 0

Validation PASSED

EXECUTE_WRITES = False
No DIM/FACT changes were made.
```

Run only this and send me the output. **Do not switch `EXECUTE_WRITES` to `True` yet.**
