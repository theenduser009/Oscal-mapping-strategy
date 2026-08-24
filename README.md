Perfect. ✅ Cell 6 is now proven and should be frozen.

We are at the final production step: **Cell 7 = one orchestrator function**. This is what Matillion will eventually call conceptually.

For now, keep `EXECUTE_WRITES=False`.

```python
# ============================================================
# Cell 7 — Production OSCAL Mapper Orchestrator
# ============================================================

def run_oscal_mapping(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    config
):
    """
    Execute one complete metadata-driven OSCAL mapping run.

    Flow:
        1. Build canonical OSCAL graph
        2. Validate graph
        3. Load DIM/FACT only when EXECUTE_WRITES=True

    Returns:
        canonical_nodes_df
        canonical_edges_df
        load_result
    """

    print("=" * 70)
    print("OSCAL MAPPING RUN")
    print("Model :", config["OSCAL_MODEL"])
    print("Run ID:", config["RUN_ID"])
    print("=" * 70)

    # --------------------------------------------------------
    # 1. Build graph
    # --------------------------------------------------------

    nodes_df, edges_df = build_oscal_graph(
        source_df=source_df,
        canonical_mapping_df=canonical_mapping_df,
        element_registry_df=element_registry_df,
        model_key=config["OSCAL_MODEL"],
        source_system=config["SOURCE_SYSTEM_NAME"],
        source_table=config["SOURCE_TABLE_NAME"]
    )

    # --------------------------------------------------------
    # 2. Validate / optionally load
    # --------------------------------------------------------

    result = validate_and_load_oscal(
        canonical_nodes_df=nodes_df,
        canonical_edges_df=edges_df,
        config=config
    )

    print("\n" + "=" * 70)
    print("OSCAL MAPPING RUN COMPLETE")
    print("Nodes :", result["nodes"])
    print("Edges :", result["edges"])
    print("Writes:", result["writes_executed"])
    print("=" * 70)

    return nodes_df, edges_df, result


# ============================================================
# Execute configured model
# ============================================================

final_nodes_df, final_edges_df, run_result = run_oscal_mapping(
    source_df=source_df,
    canonical_mapping_df=canonical_mapping_df,
    element_registry_df=element_registry_df,
    config=CONFIG
)
```

Expected result:

```text
OSCAL MAPPING RUN
Model : SSP

Nodes : 92880
Edges : 90715

Null node keys      : 0
Duplicate node keys : 0
Null edge keys      : 0
Duplicate edge keys : 0
Missing parents     : 0
Missing children    : 0

Validation PASSED

EXECUTE_WRITES = False
No DIM/FACT changes were made.

OSCAL MAPPING RUN COMPLETE
Nodes : 92880
Edges : 90715
Writes: False
```

This is the important architectural milestone: the caller no longer needs to understand `props[]`, `responsible-parties[]`, `components[]`, SSP hierarchy, hashes, or parent/child FACT construction.

Eventually the caller simply runs:

```python
run_oscal_mapping(...)
```

while the **mapping CSV + element registry drive the model**.

Run Cell 7. If it reproduces **92,880 / 90,715**, we freeze it. Then we do one final cleanup pass so Cells 5 and 6 only define functions rather than also executing them independently.
