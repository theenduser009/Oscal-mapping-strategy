Perfect. ✅ The POA&M graph itself is now proven:

```text
Nodes               : 3,099
Edges               : 2,563
Null/duplicate keys : 0
Missing parents     : 0
Missing children    : 0
Validation PASSED
Writes              : False
```

So **do not turn writes on yet**. The graph logic needs no change.

The next step is to make the **generic loader** understand that POA&M has different PK column names than SSP. We should solve this once, generically, rather than put POA&M-specific SQL in the loader.

### Next step only

In your temporary `POAM_CONFIG`, add these two values:

```python
POAM_CONFIG["DIM_PK_COLUMN"] = "PK_DIM_OSCAL_POAM_ELEMENT_HASH"
POAM_CONFIG["FACT_PK_COLUMN"] = "PK_FACT_OSCAL_POAM_DEPENDENCY_HASH"
```

So that section becomes:

```python
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

POAM_CONFIG["DIM_PK_COLUMN"] = "PK_DIM_OSCAL_POAM_ELEMENT_HASH"
POAM_CONFIG["FACT_PK_COLUMN"] = "PK_FACT_OSCAL_POAM_DEPENDENCY_HASH"

POAM_CONFIG["EXECUTE_WRITES"] = False
```

**Just add those two lines for now. Don't run with `True`.**

After that, we'll make one small generic change inside `validate_and_load_oscal()` so it uses:

```python
config["DIM_PK_COLUMN"]
config["FACT_PK_COLUMN"]
```

instead of assuming the SSP PK names.

That will make the same loader work for **SSP, POA&M, and the models we add later**.
