Next: **remove the hardcoded 5 SSP registry rows from Cell 3 and load them from the Snowflake metadata table.**

### 1. Add one CONFIG entry in Cell 1

```python
"ELEMENT_REGISTRY_TABLE": "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY",
```

That is the only Cell 1 change.

### 2. In Cell 3, delete the hardcoded `element_registry_data = [...]` block

Replace that whole registry-creation section with:

```python
# ============================================================
# Element Registry — structural metadata from Snowflake
# ============================================================

element_registry_df = (
    session.table(CONFIG["ELEMENT_REGISTRY_TABLE"])
    .filter(
        col("OSCAL_MODEL_KEY") == CONFIG["OSCAL_MODEL"]
    )
)

print(
    "Element registry rows:",
    element_registry_df.count()
)

element_registry_df.sort(
    col("PROCESS_ORDER"),
    col("NODE_PATH")
).show()
```

That's it.

Now the architecture becomes:

```text
Mapping CSV
    ↓
canonical_mapping_df

Snowflake OSCAL_ELEMENT_REGISTRY
    ↓
element_registry_df

        BOTH
         ↓
generic engine
```

So SSP structure is no longer hardcoded in Python.

Run **Cell 1 → Cell 3** and show me the registry output. We should see the rows from `RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY`.
