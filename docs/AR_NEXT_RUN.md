# Assessment Results - preview the two additional threshold fields

Use the existing seven cells on simplify-metadata-boundary and the updated
[ARCHER_OSCAL_MAPPINGS.csv](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).

## What changes

| Archer source field | Runtime target | Transform |
| --- | --- | --- |
| CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD | assessment-results.results[].observations[] | scalar-score |
| CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD | assessment-results.results[].observations[] | scalar-score |

Both fields use their exact unprefixed Excel names. A populated scalar creates
one observation with one named inline property. Zero is preserved, empty values
are omitted, and multiple values or unsupported objects fail. No threshold is calculated and no
underscore/PCT aliases are added. Original path wording and Notes remain
unchanged; RUNTIME_TARGET_PATH selects the one executable destination.

The 13 additions already enabled on this branch stay in place with their ar30
rule IDs. This increment adds two rows' execution metadata, yielding **32 enabled
AR rows and 13 deferred rows**. Existing SSP and POAM mappings are preserved.
No new notebook logic, registry rows, tables or DDL are required.

## Run the expanded preview

1. Upload this branch's updated CSV to notebook Files, replacing the existing
   mapping file used by Cell Two.
2. In Cell One set `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)`.
   Keep `CONFIG["EXECUTE_WRITES"] = False`.
3. In Cell Seven set `OSCAL_LOAD_MODE = "PREVIEW"`.
4. Run matching Cells One through Seven in order to reload and compile the CSV.
   The current POAM-capable cell code needs no replacement.
5. Post Cell Three's routing summary and the complete pipeline report.

Expected: Cell Three is READY with SELECTED_ROWS = 32. Cell Seven reports
PREVIEW_COMPLETE and PREVIEW_PASSED_NO_TARGET_DML, with graph, storage and
pre-write validation true and writes/commit false. Inspect actual counts;
missing or null threshold fields may produce no new observations. An approved
mapping and an unchanged preview do not prove populated-field coverage.

The existing [AR COMMIT/readback](checkpoints/2026-09-13-assessment-results-commit-completed-and-verified.md)
accepted 73,189 DIM elements and 70,376 FACT relationships for 2,813 source
records. Preserve that checkpoint and populated tables. This preview reviews
the changed mapping scope, not a repeat of an unchanged acceptance run.
After reviewing its differences, select COMMIT in Cell Seven for the planned
write and retain the committed readback report.

## Validation and remaining scope

Local checks ran 194 tests without failures; three Snowpark classes were
unavailable locally. The new regression proves exactly two added observations,
unchanged AR30 keys/payloads, preserved zero and no underscore aliasing.
[CI passed all 207 tests with zero skips](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34789244811)
on code commit 2e215d3867e4a0e0f3881d451fbe3c4e9212b097, including AR
insert/update/readback and POAM isolation. CI uses installed Snowpark and an
explicit relational SQL adapter; it is not a live Snowflake write. Saved private excerpts do not
contain these two threshold fields, so their populated-source coverage remains
a live verification gap.

The 13 deferred AR rows remain: two average-compliance fields, RISK_ACCEPTANCE_RBDS,
RISK_ASSESSMENT_REPORT, TOTAL_PACKAGE_INHERENT_RISK, FINDINGS and seven workflow
audit rows. Their unresolved semantics are not changed by this increment.
The [POAM preview](https://github.com/theenduser009/Oscal-mapping-strategy/blob/f5677398faf9da2c9919e6fa29d0db0264816d4e/docs/checkpoints/2026-09-13-poam-preview-complete.md)
is accepted; POAM committed readback is still pending verification.
