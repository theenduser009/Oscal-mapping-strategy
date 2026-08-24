Perfect — this proves the **clean production execution path** works end-to-end in dry-run mode:

```text
Nodes      : 92,880
Edges      : 90,715
Validation : PASSED
Writes     : False
```

So yes: **freeze Cells 1–5.** The old SSP notebook is now reference/evidence only, not part of production execution.

### Next step: add post-load verification — without creating another cell

Put this function at the **bottom of Cell 6**, after `validate_and_load_oscal()`:

```python
def verify_oscal_load(
    canonical_nodes_df,
    canonical_edges_df,
    config
):
    """
    Verify that every node/edge produced by this run
    exists in the target DIM/FACT tables.
    """

    expected_dim = canonical_nodes_df.count()
    expected_fact = canonical_edges_df.count()

    canonical_nodes_df.select(
        col("NODE_KEY").alias("PK_OSCAL_SSP_ELEMENT_HASH")
    ).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_DIM"
    )

    canonical_edges_df.select(
        col("EDGE_KEY").alias("PK_FACT_OSCAL_DEPENDENCY_HASH")
    ).create_or_replace_temp_view(
        "TMP_OSCAL_VERIFY_FACT"
    )

    dim_matches = session.sql(f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_DIM s
        JOIN {config["TARGET_DIM"]} t
          ON s.PK_OSCAL_SSP_ELEMENT_HASH
           = t.PK_OSCAL_SSP_ELEMENT_HASH
    """).collect()[0]["CNT"]

    fact_matches = session.sql(f"""
        SELECT COUNT(*) AS CNT
        FROM TMP_OSCAL_VERIFY_FACT s
        JOIN {config["TARGET_FACT"]} t
          ON s.PK_FACT_OSCAL_DEPENDENCY_HASH
           = t.PK_FACT_OSCAL_DEPENDENCY_HASH
    """).collect()[0]["CNT"]

    print("\n=== Post-Load Verification ===")
    print("DIM expected :", expected_dim)
    print("DIM matched  :", dim_matches)
    print("FACT expected:", expected_fact)
    print("FACT matched :", fact_matches)

    if (
        dim_matches != expected_dim
        or fact_matches != expected_fact
    ):
        raise ValueError(
            "OSCAL post-load verification FAILED"
        )

    print("LOAD VERIFIED")

    return {
        "dim_expected": expected_dim,
        "dim_matched": dim_matches,
        "fact_expected": expected_fact,
        "fact_matched": fact_matches
    }
```

Then in **Cell 7**, immediately after:

```python
result = validate_and_load_oscal(
    canonical_nodes_df=nodes_df,
    canonical_edges_df=edges_df,
    config=config
)
```

add:

```python
if result["writes_executed"]:
    result["verification"] = verify_oscal_load(
        nodes_df,
        edges_df,
        config
    )
```

That's all.

Keep:

```python
"EXECUTE_WRITES": False
```

for this run and use **Run All** again. It should still finish at:

```text
Nodes : 92880
Edges : 90715
Validation PASSED
Writes: False
```

The verification won't execute yet. Once that passes, the next move is turning writes on for the first production-mapper test.
