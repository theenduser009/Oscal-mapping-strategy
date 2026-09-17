# Source 2 `sources_source` full-tab completion reset — 2026-09-17

## Repository checkpoint

Branch inspected before this reset: `simplify-metadata-boundary` at `b0b5234462a4eedb19c8d7dc454d69e131777d42` (`Checkpoint Source 2 Topic mapping start`).

This checkpoint supersedes the earlier assumption that Topic should be the immediate next mapping step. The owner correctly called out that the Source worksheet itself is not yet complete.

A new comprehensive read-only Source readiness script was then committed as `6a01244a2b1588589f514cdf5357501d942f648f`:

`sql/SOURCE2_SOURCE_FULL_MAPPING_READINESS.sql`

## Confirmed Source-tab status

The Source worksheet (`Mapping/SOURCE2_SOURCE_MAPPING.csv`) contains **56 row occurrences** (worksheet rows 2-57).

The current executable Source runtime (`Mapping/sources_source_runtime.csv`) contains **14 APPROVED rows**. Those 14 are the Source-level Catalog Metadata batch already previewed, committed, and owner read-back verified.

Therefore **42 Source-tab rows are not yet executable runtime mappings**.

The 56 workbook rows break down by the worksheet's supplied model labels as follows:

- Catalog Metadata: 24 rows total
- Catalog Back Matter: 3 rows
- Catalog: 6 rows
- Catalog or Component Definition: 1 row
- Assessment Results: 10 rows
- Component Definition: 6 rows
- Assessment Plan: 3 rows
- N/A / System Metadata: 3 rows

Because 14 current runtime rows are all from the Catalog Metadata subset, the 42 remaining rows consist of:

- 10 additional Catalog Metadata rows
- 3 Catalog Back Matter rows
- 6 Catalog rows
- 1 Catalog-or-Component-Definition row
- 10 Assessment Results rows
- 6 Component Definition rows
- 3 Assessment Plan rows
- 3 System Metadata rows

## Why the other 42 were not promoted earlier

The first live Source commit intentionally promoted only the evidence-safe Catalog Metadata subset. The remaining rows were not silently ignored; they include one or more of the following unresolved conditions:

- competing singleton destinations, such as `SOURCE_DESCRIPTION` and `INFORMATION` both targeting metadata remarks;
- document timestamp semantics, including `DATE_CREATED` / `LAST_UPDATED` versus long prefixed publication/update fields;
- structured permissions that are not proven to be OSCAL roles;
- Back Matter links/attachments whose populated source shapes were not yet established;
- cross-record/cross-table relationships to Topics, controls, findings, policies, and other entities;
- rows belonging to Assessment Results, Component Definition, or Assessment Plan rather than Catalog;
- clipped/duplicate-looking source evidence that must not be guessed;
- technical system metadata that may be excluded rather than mapped.

## Correct completion definition

"Finish `sources_source`" does **not** mean force all 56 rows into the Catalog runtime.

It means every Source worksheet row receives a final evidence-backed disposition:

1. executable mapping to its correct OSCAL model;
2. relationship/hierarchy input with a defined generic implementation path;
3. explicitly deferred with the exact missing evidence or model-grain decision;
4. explicitly excluded when it is system/warehouse metadata.

Only rows with resolved semantics and source shapes should be promoted to runtime.

## New read-only evidence package

`sql/SOURCE2_SOURCE_FULL_MAPPING_READINESS.sql` profiles the complete Source tab without exposing business values. It checks:

- Source identity and CURATED_JSON completeness;
- every one of the 56 worksheet fields for population and observed JSON type;
- `SOURCE_DESCRIPTION` versus `INFORMATION` co-population/conflict;
- competing publication/update timestamp fields;
- relationship/back-matter/other-model source shapes;
- array relationship item types and object keys;
- Archer value-list object shapes and `ARCHER_META_VALUE` lookup coverage;
- `DEFAULT_RECORD_PERMISSIONS` object structure;
- system-metadata field presence in CURATED_JSON.

It performs no DDL or DML.

## Status distinction

- 14-row Source Catalog Metadata runtime batch: **implemented, previewed, committed, read-back verified**.
- Remaining 42 Source worksheet rows: **reviewed at workbook level but not yet complete as runtime/model dispositions**.
- Topic mapping review/discovery artifacts: **committed but paused as the next execution step** until Source-tab completion is resolved.
- Universal Cell 1: **implemented/tested/committed**; its live Catalog re-preview remains separate from this Source-tab completion audit.

## Next action

Run `sql/SOURCE2_SOURCE_FULL_MAPPING_READINESS.sql` read-only and return the aggregate outputs. Use that one result package to complete the remaining Source rows by model before resuming Topic.
