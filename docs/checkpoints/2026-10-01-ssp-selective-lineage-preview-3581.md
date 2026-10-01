# SSP selective lineage preview checkpoint — 2026-10-01

Previous repository checkpoint: `d9f07dcc7fe682c5650f3c65ca0ffac15a42ec88`.

Owner-provided Snowflake PREVIEW evidence after loading the updated mapping sheet:
- pipeline `PREVIEW_COMPLETE`
- source/model `source-one / SSP`
- `writes_executed=false`
- `target_dml_attempted=false`
- validation and storage checks passed
- 2,813 source records
- 550,380 candidate nodes / 547,567 candidate edges
- DIM expected changes: 3,581 inserts / 0 updates / 546,799 unchanged
- FACT expected changes: 3,581 inserts / 0 updates / 543,986 unchanged
- `LINEAGE_PROPS=3581`
- `LINEAGE_GAPS=0`
- `LINEAGE_COMPLETE=true`

Interpretation: this supersedes the immediately prior preview where `LINEAGE_PROPS=0`. It is PREVIEW evidence only, not COMMIT/read-back evidence.

This update adds the read-only notebook helper:
`notebooks/validation/16_ssp_selective_lineage_sample.py`
at commit `46340d7be6b91b968a85fd1c4121cbe226ec6339`.

Evidence boundary: the user loaded an updated mapping sheet directly into the notebook. This checkpoint does not establish that that notebook-loaded mapping sheet is already committed to GitHub or packaged for the eventual remote deployment.

Next action: use the helper to inspect a small sample of candidate lineage props and confirm the minimal `source-field` structure before any COMMIT.


## Helper correction — 2026-10-01

The first helper version passed the lineage namespace as a bare Python string to
Snowpark `Column.contains()`. In the live notebook Snowpark compiled that string
as a quoted column identifier, causing SQL compilation error `invalid identifier
'"urn:company:oscal:lineage:v1"'`.

Corrected helper commit: `e71e17e6abdaee477277f4280b60e64d2fa54c93`.

The helper now imports `lit` and uses:

```python
col("METADATA_JSON").contains(lit("urn:company:oscal:lineage:v1"))
```

This is a read-only diagnostic correction only. It does not change mapper
runtime behavior, the mapping sheet, lineage generation, or target data.


## Display helper correction — 2026-10-01

The live notebook confirmed `CANDIDATE LINEAGE NODES = 3581`, so the lineage filter
itself is working. The subsequent display-only call failed because this Snowpark
environment does not accept `DataFrame.show(..., truncate=False)`.

Corrected helper commit: `1641d94db423fdd51aa77a8d25bf9802f8e50583`.

The helper now uses `.limit(20).collect()` and prints the returned rows, an API
pattern already used by the maintained mapper code. This is a read-only
diagnostic-only correction. It does not alter the mapper, mapping sheet, graph,
lineage generation, or target data.


## Full selective-lineage contract validator added — 2026-10-01

Read-only validation helper:
`notebooks/validation/17_ssp_selective_lineage_contract_validation.py`

Added at commit `c3ce068908429032a0e84a73d1b88ad31da47e7c`.

Purpose: validate all candidate SSP lineage props already built by PREVIEW against
the compiled `LINEAGE_REQUIRED` contract. It requires exactly 12 configured
lineage fields, the expected namespace, exactly the four approved property keys,
the expected class for each source field, no duplicate source-record/field/class
lineage props, and agreement between candidate lineage-node count and the PREVIEW
`LINEAGE_PROPS` count.

This helper has been published and read back from GitHub, but has **not yet been
executed in Snowflake**. No mapper runtime, mapping CSV, registry, or target data
was changed by adding it.

Next action: run only this helper against the existing in-memory SSP PREVIEW graph.
Do not rerun Cells 1-7 and do not COMMIT until its live result is reviewed.
