Excellent — this is **exactly the expected POA&M graph**. ✅

```text
536 POA&M roots
2,563 poam-items[] references

Total nodes = 3,099
Total edges = 2,563
```

And the relationship is correct:

```text
plan-of-action-and-milestones
        |
        | parent_of
        v
plan-of-action-and-milestones.poam-items[]
```

This is also proof that **the same generic `build_oscal_graph()` works for POA&M**. We did not write a POA&M-specific graph builder.

### Next step only: validate this graph

Don't write anything yet. Add one temporary cell immediately below your POA&M graph test:

```python
# ============================================================
# POA&M Graph Validation
# READ ONLY
# ============================================================

POAM_CONFIG = dict(CONFIG)

POAM_CONFIG["OSCAL_MODEL"] = "POAM"

POAM_CONFIG["TARGET_DIM"] = (
    "RTX_ENTERPRISESERVICES_DEV."
    "ES_ESC_GRC_CURATED."
    "DIM_OSCAL_POAM_ELEMENT"
)

POAM_CONFIG["TARGET_FACT"] = (
    "RTX_ENTERPRISESERVICES_DEV."
    "ES_ESC_GRC_CURATED."
    "FACT_OSCAL_POAM_DEPENDENCY"
)

POAM_CONFIG["EXECUTE_WRITES"] = False


poam_validation = validate_and_load_oscal(
    canonical_nodes_df=poam_nodes_df,
    canonical_edges_df=poam_edges_df,
    config=POAM_CONFIG
)
```

We want:

```text
Nodes               : 3099
Edges               : 2563
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

**Do not turn writes on yet.**

After this passes, our next step is specifically to make the loader recognize the POA&M PK names:

```text
PK_DIM_OSCAL_POAM_ELEMENT_HASH
PK_FACT_OSCAL_POAM_DEPENDENCY_HASH
```

without hardcoding POA&M logic into the mapper. That is the only remaining piece before we can load these 3,099 / 2,563 rows.
