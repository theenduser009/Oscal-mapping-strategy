# Source Two Catalog additive COMMIT/readback accepted; independent QA pending

Evidence date: September 28, 2026.
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Head inspected before this update: 44e444f656d77009872d344b5e9cc42de753be8f.
New QA SQL commit: 8e8b4fc6ac8a92d913adef836143fb51d7960518.
QA SQL path: sql/qa/SOURCE_TWO_CATALOG_POST_COMMIT_QA_2026-09-28.sql.
Read-back SQL blob: 5c8f3e3e9147237848b2977fc7a4b87df57fe87a, matching the tested local file.

## New owner-provided COMMIT evidence
The owner supplied a September 28 screenshot of OSCAL_PIPELINE_REPORT with mode COMMIT and overall status COMMITTED_AND_VERIFIED. The displayed group is source-two-source / CATALOG; loader release oscal-lean-daily-v3.1.

Visible flags writes_executed, persisted, committed, target_dml_attempted, pre_write_validation_passed, validation_passed and storage_verified are true.
Source records: 148. Candidate nodes: 1697. Candidate edges: 1549.

| Phase | DIM inserts | DIM updates | DIM unchanged | FACT inserts | FACT updates | FACT unchanged |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Expected changes in the successful committed run | 148 | 0 | 1549 | 148 | 0 | 1401 |
| Post-commit verification | 0 | 0 | 1697 | 0 | 0 | 1549 |

The lower report tail is outside the photo; no temporary_cleanup value is inferred. The screenshot reports the loader release, not the exact live notebook Git SHA. The evidence is the owner's live result, not a Snowflake query executed by this chat. No private image, source record ID or business payload is published here.

## Supersession and scope
This supersedes the additive COMMIT/readback-pending status in docs/checkpoints/2026-09-28-source2-catalog15-preview-passed.md and the corresponding project checkpoint. The September 17 14-rule accepted batch remains historical evidence; this is a distinct new additive acceptance.

The current mapping CSV has 15 Source-level Catalog rules. SOURCE_TRACKING_ID maps directly to catalog.metadata.props[] with PROPERTY_NAME=tracking-id and RULE_ID=catalog:SOURCE_TRACKING_ID:property. The 148 additional nodes/edges are consistent with this increment. The aggregate COMMIT does not independently prove the identity and value of each added field. Independent value and whole-table QA remain pending.

Source Two's Topic/Section/Sub-Section hierarchy, policies and Control Standard associations are separate from this Source-level metadata batch. Preserve the owner's clarification that Control Standard links to both Topic and Policy; do not collapse the two relationships or treat the document review as proof of loaded relationships. The repaired Source One POAM tables are not part of this action. The shared loader's whole-table orphan-detection improvement remains open before unattended operational sign-off.

## New read-only QA artifact
Run the complete SQL above as-is; no substitutions, no mapper rerun, no truncation and no DDL/DML. It returns 22 rows: 21 checks and an overall result.

The SQL reads the complete Catalog DIM/FACT pair, plus the current Source Two Source RAW.CURATED_JSON. Whole-table structural checks are not filtered by source-record membership. The expected baseline is 148 source records, 1697 DIM rows, 1549 FACT rows, 148 roots, 148 tracking-id properties and 148 exact string matches after the reviewed source trim-to-string conversion.

Checks cover key/UUID duplicates and missing values, target namespace and source membership, one root and metadata element per current source record, object payloads, expected element types, both orphan directions, null-safe endpoint UUID equality, same-record/namespace edges, catalog-to-metadata-to-props containment and incoming parent counts. Tracking-id checks require one property per eligible source and compare both value and target string type.

Acceptance labels:
- PASS: that check matches its expected value.
- DRIFT: a count baseline differs; investigate current source/target changes rather than treating the old count as permanent.
- FAIL: a structural or value check differs; current-source drift can also produce a source/target difference and needs interpretation.
- BLOCKED: source IDs are noncanonical/duplicate or source tracking values need review. No arbitrary latest-row selection or unreviewed shape conversion is performed.

The overall observed count is the number of non-PASS checks, not distinct bad rows. Input ambiguity takes priority over FAIL and DRIFT. Individual defect counts can overlap, and duplicate DIM keys can multiply joined counts.

Limits: source parity uses the current RAW snapshot, not the notebook's retained snapshot. JSON objects and JSON text containing objects are handled. Populated INTEGER and nonblank VARCHAR tracking values are compared; null, absent, other numeric representation or other shape needs review. This conservative QA input gate does not change or disable the mapping. TYPEOF can expose some stored numeric values as DECIMAL; that would need interpretation, not an invented value. This query does not revalidate all 15 fields, regenerate deterministic identities, inspect every payload member or UUID syntax, prove full OSCAL conformance, or implement the loader safeguard. Future group/control stages need their own updated hierarchy contract.

## Source inspection and validation actually performed
Read the September 14 handoff/coverage context already supplied; its historical counts do not supersede the latest owner results. Retrieved the current branch, AGENTS.md, current-action sections of PROJECT_HANDOFF.md and CURRENT_STATUS.md, configuration/target bindings, the 15-rule Catalog CSV, prior Catalog acceptance, and Catalog root/metadata setup SQL. Setup SQL was read for its structural contract, not treated as proof of execution. No full current registry export is claimed.

Reviewed official Snowflake documentation for GET, TYPEOF, IS_OBJECT and string/integer predicates for the new diagnostic. References: https://docs.snowflake.com/en/sql-reference/functions/get and https://docs.snowflake.com/en/sql-reference/functions/typeof.

Built the SQL locally and ran 14 synthetic cases through SQLite 3.46.1. Qualified table names and CURRENT_TIMESTAMP syntax were adapted; Python UDFs simulated the limited VARIANT operations used. A read-only authorizer denied writes during query evaluation. Cases covered clean full-size baseline, disconnected facts, incorrect/numeric/null tracking values, duplicated target keys/tracking properties, duplicate source IDs, missing source tracking, JSON-text sources, invalid JSON, wrong parents, null endpoint UUID, baseline count drift, and empty tables. All cases returned 22 rows with expected checks and overall outcomes. A static scan confirmed one SELECT-only statement.

These are local synthetic checks, not a Snowflake compile/run or CI result. SQL was published and its full content/blob read back successfully. Only a standalone QA SQL file and this checkpoint are added; no mapping, registry, runtime, loader or database changes were made.

## Immediate next action
Run sql/qa/SOURCE_TWO_CATALOG_POST_COMMIT_QA_2026-09-28.sql once and share the 22-row summary, including the overall row and any non-PASS checks. No more COMMIT or truncation for this accepted batch. Independent Catalog structural/tracking-id acceptance awaits that result; Topic hierarchy review follows this checkpoint, not another Source-level reload.
