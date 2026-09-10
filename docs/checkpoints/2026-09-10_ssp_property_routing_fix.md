# SSP extension-property routing correction — 2026-09-10

## Evidence and root cause

The latest `docs/live-snowflake-results.md` reports a Cell 7 failure after
component hydration loaded 1,435 rows. The offending source is
`INFORMATION_SYSTEM_TYPE`, mapping type `extension-property`, registry owner
`system-security-plan.system-characteristics`. The target-field suffix is
truncated in the posted evidence and is not reconstructed here.

Cell 3 previously used only the deepest registry prefix to determine owner.
A parent-level extension mapping therefore reached Cell 4 on the singleton
parent, while the governed property handler requires `props[]`. The older
property tests built already-canonical rows and missed this input-routing
defect. The stricter handler exposed it; it was not a component source failure.

## Narrow correction

The [recorded Excel evidence](../MAPPING_ARTIFACT_SCREENSHOT_EVIDENCE_2026-09-09.md)
explicitly identifies eight approved extension-property sources:

- `INFORMATION_SYSTEM_TYPE`
- `FISMA_REPORTABLE`
- `FINANCIAL_SYSTEM`
- `MISSION_CRITICAL`
- `CRITICAL_INFRASTRUCTURE`
- `PACKAGE_TYPE`
- `PIA_REQUIRED`
- `INFORMATION_CLASSIFICATION`

Cell 3 routes these sources only when their type is `Extension Property` and
their artifact destination is the characteristics parent, an unregistered
direct leaf under it, or its actual property collection. It does not guess
the spelling of a pseudo-field. Other registered branches and arbitrary nested
paths are not rewritten. The active properties registry path is required.

`OSCAL_ELEMENT_PATH` and an explicit `OSCAL_FIELD_NAME` retain their artifact
values; `CANONICAL_ELEMENT_PATH` determines registry ownership and derives the
target only when the artifact has no explicit target. The source artifact
DataFrame is not modified. The existing Cell 4 property converter still emits
stable name/value strings, deduplicates by source plus value, and rejects
unresolved values. Unknown handlers still fail. Authorization comments remain
on status remarks; helper/deferred mappings still skip.

Only copy-ready Cell 3 and its synchronized section in the authoritative
notebook change production behavior. There is no DDL, DML, registry setup,
new source lookup, or timezone conversion in this correction.

## Verification and next run

189 local tests passed using the bundled Python runtime with Pandas installed.
The eight new regressions cover the failing parent-owned row before/after
canonicalization, all eight approved sources, provenance, repeatability,
missing/inactive registry, unchanged unknown/other-path rules, skipped rows,
status remarks, monolith synchronization, and real graph construction.
The graph fixture uses two source records and verifies separate singleton
parents, string property payloads, deduplication, unique keys, and within-record
containment links. Only Snowflake transport and unrelated hydration I/O are
faked. No live Snowflake success is claimed.

Replace Cell 3 only. In an open session run 3, 4, 5, 6, 7; in a restarted
session run 1 through 7. Keep `EXECUTE_WRITES = False`. No registry setup or
separate dispatcher diagnostic is required for this known correction.
Run the mapped-scope assembler only after Cell 7 succeeds, then post the output.
The external full workbook has not been executed locally, so any new rejected
mapping remains a concrete follow-up rather than a claim of total coverage.
