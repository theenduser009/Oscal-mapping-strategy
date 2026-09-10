# SSP mapped-scope assembly accepted — 2026-09-10

The live Snowflake mapped-scope assembly passed and is accepted.
No rerun is required for this checkpoint.

## Evidence

The accepted output is recorded in
[live Snowflake results](../live-snowflake-results.md).
The evidence was verified on remote commit
`62269551a53bd4b24110bfdbe5a2122a432fff29`.

## Accepted run

| Measure | Accepted value |
| --- | --- |
| OSCAL model | `SSP` |
| Root path | `system-security-plan` |
| Documents assembled | 2,813 |
| Graph nodes consumed | 70,102 |
| Graph edges consumed | 67,289 |
| Root nodes consumed | 2,813 |
| Writes executed | `False` |
| Result | `MAPPED-SCOPE ASSEMBLY PASSED` |
| Complete SSP claim | `False` |
| OSCAL schema-valid claim | `False` |

The existing `notebooks/validation/RUN_AFTER_07_ssp_mapped_scope_assembly.py`
assembled the accepted graph into one mapped-scope SSP document per source
record. Its node and edge totals match the accepted Cell 7 run.

## Scope and retained state

Acceptance covers assembly of the currently mapped graph only. It does not
establish complete SSP coverage, OSCAL schema validity, or coverage of new
fields.

The assembled document objects and canonical JSON remain transient notebook
state; they have not been persisted. `MAPPED_SCOPE_SSP_DOCUMENTS`,
`MAPPED_SCOPE_SSP_CANONICAL_JSON`, and `MAPPED_SCOPE_ASSEMBLY_RESULT` are the
assembly outputs. This checkpoint requires no new validation cell or rerun.
