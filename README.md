Perfect — those three counts are exactly right:

```text
POA&M source packages : 536
POA&M mapping rows    : 1
POA&M registry rows   : 2
```

So **stop changing the dev/reference notebook now**. That notebook has done its job: we proved which records participate.

### Next step: test POA&M with the generic mapper

Go to **`NB_ARCHER_OSCAL_MAPPER_V1`**. Keep:

```python
"EXECUTE_WRITES": False
```

Do **not change Cells 1–7 yet**.

Add one temporary Python cell at the bottom and paste:

```python
# ============================================================
# POA&M Graph Test
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

# Only Authorization Packages containing POAMS
poam_ids = []

for record in source_df.to_local_iterator():

    source_obj = _parse_source_json(record)
    poams = resolve_json_path(source_obj, "POAMS")

    if poams not in (None, "", [], {}):
        poam_ids.append(str(record["SOURCE_RECORD_ID"]))


poam_source_df = (
    source_df
    .filter(col("SOURCE_RECORD_ID").isin(*poam_ids))
)


poam_mapping_df = (
    canonical_mapping_df
    .filter(
        col("OSCAL_ELEMENT_PATH").startswith(
            "plan-of-action-and-milestones"
        )
    )
)


poam_registry_df = (
    session.table(CONFIG["ELEMENT_REGISTRY_TABLE"])
    .filter(
        (col("OSCAL_MODEL_KEY") == "POAM")
        & (col("IS_ACTIVE") == True)
    )
)


poam_nodes_df, poam_edges_df = build_oscal_graph(
    source_df=poam_source_df,
    canonical_mapping_df=poam_mapping_df,
    element_registry_df=poam_registry_df,
    model_key="POAM",
    source_system=CONFIG["SOURCE_SYSTEM_NAME"],
    source_table=CONFIG["SOURCE_TABLE_NAME"]
)


print("\n=== POA&M GRAPH TEST ===")
print("Nodes :", poam_nodes_df.count())
print("Edges :", poam_edges_df.count())

poam_nodes_df.group_by("ELEMENT_TYPE").count().show()

poam_edges_df.group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().show()
```

Based on the data we already proved, I expect roughly:

```text
536 plan-of-action-and-milestones roots
2563 poam-items[]

Total nodes = 3099
Total edges = 2563
```

Conceptually:

```text
536 POA&M roots
   │
   └── 2,563 parent_of relationships
            ↓
       POA&M reference items
       {ContentId, LevelId}
```

**Do not load the POA&M DIM/FACT yet.** First I want this generic graph-builder test to return approximately **3,099 nodes / 2,563 edges**. Then we handle the POA&M target-column names cleanly without changing the graph logic.
