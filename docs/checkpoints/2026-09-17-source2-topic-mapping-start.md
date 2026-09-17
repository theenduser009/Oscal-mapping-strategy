# Source 2 Topic mapping start — 2026-09-17

## Repository checkpoint

Branch inspected before Topic work: `simplify-metadata-boundary` at `f86f7059aecb70d3020856f8a1e79de6e4c57429` (`Checkpoint Source 2 Catalog commit and readback verification`).

Topic review/discovery changes are now committed through `b4a996870f4d07333251a7313488c40c8156a355`.

## What was reviewed

The complete screenshot-transcribed Topic worksheet is `Mapping/SOURCE2_TOPIC_MAPPING.csv`, photographed rows 2-53, 52 row occurrences. The source inventory explicitly says 24 Topic rows contain a core transcription gap; `[CLIPPED]` remains evidence notation and is not executable metadata.

A complete row-by-row review has now been published as:

`Mapping/sources_topic_mapping_review.csv`

Every Topic worksheet row is classified. No clipped source key/path was invented or promoted to runtime.

## Standards check used for Catalog paths

The review converts only unambiguous Catalog structure into candidate runtime notation. NIST OSCAL Catalog JSON uses a `groups` array for control groups; a group exposes `id`, required `title`, `props`, nested `groups`, `controls`, and `parts`. This is why reviewed runtime candidates use paths such as `catalog.groups[]` rather than treating the photographed singular XPath-like notation as an executable path.

Official references checked on 2026-09-17:

- https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/catalog/json-reference/
- https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/catalog/json-definitions/
- https://pages.nist.gov/OSCAL/learn/tutorials/control/basic-catalog/

## Candidate Topic fields

The review identifies these as evidence-supported Catalog-group candidates pending live Topic source proof and the parent-link architecture:

- `TOPIC_NAME` -> group title
- `TOPIC_TRACKING_ID` -> `tracking-id` property
- `CONTENT_SOURCE` -> `content-source` property, source shape determines direct vs Archer-select
- `CRITICALITY` -> `criticality` property, source shape determines direct vs Archer-select
- `TOPIC_CRITICALITY_VALUE` -> `criticality-value` property
- `TOTAL_NUMBER_OF_SECTIONS` -> `section-count` property
- `NUMBER_OF_CONTROL_STANDARDS_TOPIC_LEVEL` -> `control-count` property
- `COUNT_OF_CONTROLS` -> `total-controls` property

`TOPIC_ID` remains a candidate group id, but the current reusable `identifier` transform preserves scalar text; it does not implement the workbook's requested normalization. Live shape/uniqueness evidence is required before a generic normalization rule is added.

`TOPIC_DESCRIPTION` and `INFORMATION` preserve the workbook's separate named-part intent, but runtime promotion requires a generic parts collection capability. They are not collapsed into remarks.

## Critical hierarchy requirement

`SOURCE_REFERENCES` is treated as the parent-link input, not as a second `catalog.metadata.title` mapping. The Topic group must attach to the already committed Source-level Catalog document.

The current shared Cell 5 builds `by_path` independently inside each source record and resolves parents from that record's in-memory paths. Current graph validation also preserves record-scoped ownership. Therefore the existing seven-cell implementation does **not yet prove a safe cross-table Source->Topic parent edge** when Source and Topic arrive from separate RAW tables.

No Topic-specific hack is approved. If live evidence proves `SOURCE_REFERENCES.ContentId` joins Topic rows to Source `CONTENT_ID`, the next implementation must add a generic metadata-driven cross-source parent-resolution capability that can later be reused for Topic->Section and Section->Sub-Section.

## Read-only discovery prepared

A comprehensive read-only Snowflake script is published at:

`sql/SOURCE2_TOPIC_READ_ONLY_DISCOVERY.sql`

It checks:

- exact Topic RAW table name and columns,
- row/CONTENT_ID/CURATED_JSON completeness,
- all top-level JSON keys and observed types,
- population/type coverage for the full Topic field list,
- Topic name/id coverage,
- Source reference cardinality,
- aggregate join coverage of `SOURCE_REFERENCES.ContentId` to the committed Source RAW `CONTENT_ID`,
- reference object key shapes,
- likely value-list/security object shapes,
- candidate scalar/date field shapes.

It returns no source business values or IDs and performs no DDL/DML.

## Status distinction

- Source-level Catalog batch: committed and read-back verified from owner-provided live evidence.
- Universal Cell 1: implemented/tested/committed; separate live universal-Cell-1 preview remains a later confirmation checkpoint.
- Topic worksheet review: completed and committed as review metadata.
- Topic physical RAW binding: not yet live verified.
- Topic runtime CSV: not created.
- Topic registry nodes: not created.
- Cross-table Source->Topic graph support: not implemented.
- Topic PREVIEW/COMMIT: not run.

## Next action

Run `sql/SOURCE2_TOPIC_READ_ONLY_DISCOVERY.sql` read-only. First confirm query 1 returns the exact physical Topic RAW table; if it does, run the remaining statements and return the aggregate results. That one evidence package is intended to avoid repeated field-by-field discovery before the Topic runtime/registry/framework change is made.
