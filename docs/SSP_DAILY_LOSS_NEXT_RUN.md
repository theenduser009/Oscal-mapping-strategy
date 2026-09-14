# SSP daily loss: CSV-only enablement

The owner approved `DAILY_LOSS_AMOUNT_FROM_OUTAGE`, including explicit nulls.
`INFORMATION_CLASSIFICATION` is already enabled. Both use
`system-security-plan.system-characteristics.props[]`.

The updated [mapping CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv) enables the
existing daily-loss row with `TRANSFORM_ID=direct` and `NULL_POLICY=preserve`.
There are 153 CSV rows in total and 49 selected SSP rows. Original Notes remain
as provenance; the old All Nulls deferral is superseded by the owner's decision.

## Run the preview

1. Upload the updated CSV to the notebook's configured mapping-file location.
2. Keep the current seven published cells. This release adds no runtime code;
   it reuses the generic CSV null handler in the matching v4 compiler/helpers.
   If the notebook still has an older release, update to the current published
   cells first; do not mix compiler/helper releases.
3. Select SSP in Cell One and PREVIEW in Cell Seven, then rerun all seven cells
   so the uploaded mapping is reread and compiled. Cell Three should select 49
   SSP rows. No registry reset or DDL is needed.

```python
# Cell One
SELECTED_MODELS = ("SSP",)

# Cell Seven
OSCAL_LOAD_MODE = "PREVIEW"
```

An explicit source null produces this property, linked to the existing
system-characteristics parent:

```json
{"name": "daily-loss-amount-from-outage", "value": null}
```

A missing source key remains absent. Existing empty-value behavior remains
unchanged. Zero is retained; non-null scalar values use the existing property
string formatting. No currency, unit or numeric conversion is inferred.
The null is a warehouse preservation representation; it is not a conformant
OSCAL string property for document export.

## Existing SSP changed-value restriction

SSP property identity is `SOURCE_FIELD_NAME+VALUE`. This release preserves that
shared registry rule. An initial property can be inserted and an identical retry
is unchanged. If its stored value later changes, including null to an amount,
the new candidate has a different key. The current loader then reports
`OBSOLETE_TARGET_ROWS_BLOCKED` before target writes. Do not interpret that as
permission to delete old rows or reset the registry. Such a transition needs a
separate identity/migration decision. This CSV release does not implement it.

Only proceed to COMMIT after the fresh preview passes and its actual changes
are reviewed. A live preview or committed readback for this field is not yet
recorded; prior SSP acceptance does not cover this new mapping.

## Validation

Local suite: 220 tests passed with three unavailable-Snowpark class skips.
Generated notebook pages remain synchronized and the runtime stays at 1,903
lines. Four dedicated regressions cover mapping selection, missing/null/zero
and scalar values, parent links, malformed shapes, initial load/readback,
unchanged retry, and the existing changed-value block using a local SQL adapter.
The private readable screenshot's exact null excerpt also passed graph checks;
the source screenshot and excerpt remain private. CI results follow below.
