# POAM both-endpoint orphans confirmed - 2026-09-28

## Repository basis
- Branch: simplify-metadata-boundary.
- Head inspected before this work: e0f9b7dff2c26481b88c8dd1892ccddb52a567a4.
- New SQL commit: 8daf3d519ee0d17c86a46c856b3a0bd8018cc5ea.
- SQL: sql/qa/POAM_ORPHAN_UUID_DIAGNOSTIC_2026-09-28.sql.
- SQL blob read back: 5ce02aa841b4650b7b185e6e92ff5cb77f87066f, matching the locally tested file.

## Newly supplied owner result
The bottom POAM_TABLE_SCOPE rows from the single-Content-ID inspection show:
- BOTH_ENDPOINTS_MISSING = 2,575 / REVIEW_TABLE_WIDE_ORPHANS.
- BOTH_ENDPOINTS_PRESENT = 8 / INFO_NOT_FULL_QA.

These mutually exclusive buckets sum to 2,583 POAM FACT rows for that result. This query section uses the entire POAM FACT and DIM tables, with no Content-ID or source-namespace filter. These are not counts for one Authorization Package. The eight rows have resolvable hash endpoints; that alone does not certify full graph QA.

## Supersession
This resolves the overlap uncertainty in 2026-09-28-poam-orphans-and-content-id-inspection.md. The earlier ORPHAN_SOURCE_FK=2,575 and ORPHAN_TARGET_FK=2,575 counts concern both missing endpoints of the same set of FACT rows, not 5,150 separate facts.

POAM table-wide relationship QA remains open. Earlier September 25 COMMIT/readback checkpoints remain dated batch evidence, not proof that the whole current table is clean. Upstream RAW_DATA-to-CURATED_JSON saved-reference reconciliation remains a separate gate.

Cause remains unverified. Do not label these rows obsolete history, deleted nodes, a hash-generator failure or misrouted data without evidence. No current package can be assigned from the missing DIM hash links alone. No deletion, truncation, rekeying or reload is approved or performed.

## Next diagnostic prepared
The new SQL is one SELECT-only statement with no parameter substitutions. It returns ten aggregate rows: total FACT rows, facts missing hash endpoints, seven mutually exclusive UUID-resolution categories, and a count-balance check. Zero-count categories remain visible.

It compares endpoint UUIDs against the full current POAM DIM after diagnostic case/hyphen/outer-space normalization. Duplicate normalized UUIDs are ambiguous, not arbitrarily resolved. Unique same-owner UUID matches would provide candidates for investigation, not prove valid parent-child semantics or approve repair. No UUID match does not prove a row is disposable. Other-model DIMs, history/Time Travel and raw-source identities are not searched by this step.

## Validation actually performed
- Retrieved the current branch and actual single-record query table/key/UUID bindings and bucket logic.
- Executed the new query locally through SQLite with only qualified-table/time-function adapters and a regex function: 16 synthetic FACT rows passed; duplicate DIM-hash and empty FACT variants passed.
- Checked missing/invalid UUIDs, formatting normalization, duplicate normalized UUIDs, same owner, missing/conflicting owner, source-only/target-only/neither matches, NULL FK and retained duplicate FACT rows. Verified ten output rows and classification balance.
- No Snowflake dialect parser was available. Local tests are not a live Snowflake compilation or execution.
- SQL is committed and blob read-back verified. No mapper, mapping CSV, registry, loader or database data changes.
- No live result for the new UUID diagnostic is yet available.

## Immediate next action
Run sql/qa/POAM_ORPHAN_UUID_DIAGNOSTIC_2026-09-28.sql in Snowflake and share its ten aggregate rows. Diagnose that result before proposing any corrective write. No rerun of column discovery, upstream reconciliation or the OSCAL mapper is requested.
