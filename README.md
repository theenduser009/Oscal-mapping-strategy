Perfect — the registry is correct. ✅ I can see the two new rows at the top:

```text
ASSESSMENT_RESULTS | assessment-results
                   | FALSE | SINGLETON | order 1

ASSESSMENT_RESULTS | assessment-results.results[]
                   | TRUE  | SOURCE_RECORD_ID | order 2
```

The other 15 rows are just your existing POA&M/SSP registry entries. Leave them alone.

### Next step only: build Assessment Results graph read-only

In **`NB_ARCHER_OSCAL_MAPPER_V1`**, add a new Python cell at the bottom:

```python
# ============================================================
# Assessment Results — Graph Test
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

assessment_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(
            "assessment-results"
        )
    )
)

assessment_registry_df = (
    session.table(CONFIG["REGISTRY_TABLE"])
    .filter(
        (col("OSCAL_MODEL_KEY") == "ASSESSMENT_RESULTS")
        & (col("IS_ACTIVE") == True)
    )
)

assessment_nodes_df, assessment_edges_df = build_oscal_graph(
    source_df=source_df,
    canonical_mapping_df=assessment_mapping_df,
    element_registry_df=assessment_registry_df,
    model_key="ASSESSMENT_RESULTS",
    source_system=CONFIG["SOURCE_SYSTEM_NAME"],
    source_table=CONFIG["SOURCE_TABLE_NAME"]
)

print("=== ASSESSMENT RESULTS GRAPH TEST ===")
print("Nodes :", assessment_nodes_df.count())
print("Edges :", assessment_edges_df.count())

assessment_nodes_df.group_by(
    "ELEMENT_TYPE"
).count().show()

assessment_edges_df.group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().show()
```

Based on the source profiling, I expect approximately:

```text
assessment-results          2165
results                     2165
--------------------------------
Nodes                       4330

assessment-results
      ↓
results[]                   2165 edges
```

But **don’t assume those numbers yet** — run it and show me the actual output.

No DIM/FACT writes yet.
