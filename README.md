Perfect — this is **exactly the result we wanted.** ✅

```text
Assessment Results graph

assessment-results : 2,165
results[]           : 2,165
--------------------------------
Total nodes         : 4,330

assessment-results → results[]
Edges               : 2,165
```

So the new generic `SOURCE_RECORD_ID` rule is working correctly: **one logical `results[]` instance per Authorization Package record**.

We have **not** created `observations[]`, `props[]`, or `findings[]` yet. That is intentional.

### Next step only: validate this graph

Add one new read-only cell:

```python
# ============================================================
# Assessment Results — Graph Validation
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

node_keys_df = (
    assessment_nodes_df
    .select(col("NODE_KEY"))
    .distinct()
)

null_node_keys = (
    assessment_nodes_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

duplicate_node_keys = (
    assessment_nodes_df
    .group_by("NODE_KEY")
    .count()
    .filter(col("COUNT") > 1)
    .count()
)

null_edge_keys = (
    assessment_edges_df
    .filter(col("EDGE_KEY").is_null())
    .count()
)

duplicate_edge_keys = (
    assessment_edges_df
    .group_by("EDGE_KEY")
    .count()
    .filter(col("COUNT") > 1)
    .count()
)

missing_parents = (
    assessment_edges_df
    .select(
        col("SOURCE_NODE_KEY").alias("NODE_KEY")
    )
    .join(
        node_keys_df,
        ["NODE_KEY"],
        "left_anti"
    )
    .count()
)

missing_children = (
    assessment_edges_df
    .select(
        col("TARGET_NODE_KEY").alias("NODE_KEY")
    )
    .join(
        node_keys_df,
        ["NODE_KEY"],
        "left_anti"
    )
    .count()
)

print("=== ASSESSMENT RESULTS VALIDATION ===")
print("Nodes               :", assessment_nodes_df.count())
print("Edges               :", assessment_edges_df.count())
print("Null node keys      :", null_node_keys)
print("Duplicate node keys :", duplicate_node_keys)
print("Null edge keys      :", null_edge_keys)
print("Duplicate edge keys :", duplicate_edge_keys)
print("Missing parents     :", missing_parents)
print("Missing children    :", missing_children)

if (
    null_node_keys == 0
    and duplicate_node_keys == 0
    and null_edge_keys == 0
    and duplicate_edge_keys == 0
    and missing_parents == 0
    and missing_children == 0
):
    print("\nValidation PASSED")
else:
    print("\nValidation FAILED")
```

Expected:

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
```

Run only this and show me the result.
