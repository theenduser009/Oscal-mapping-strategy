# Level-355 cleanup stopped: inspect actual failed state before further writes
Date: 2026-09-24

## Repository and source evidence
- Repository: theenduser009/Oscal-mapping-strategy
- Branch: simplify-metadata-boundary
- Failing cleanup revision inspected: 9cf0cd05ec4090f3fd19895595ae7d61a926a992.
- Cleanup file: sql/validation/2026-09-24_cleanup_one_invalid_level355_implemented_requirement.sql.
- Cleanup blob: 58d3d479b959c4ede4e6a9f9225b90634b3244bc.
- Maintained Cell 1 and Cell 5 inspected at the same commit.
- New read-only inspection SQL committed at c9c30d215da9477a12f208c2786067352b090f93.
- Project continuity reviewed: 00_START_HERE.txt already read in this conversation; source inventory and live-data limitations from the first 135 lines of 03_COVERAGE_AND_HISTORICAL_SUPPORT.txt reviewed. Historical bundled checkpoints are not current target exports.

## Current owner-provided evidence
The latest screenshot reports STALE_SHAPE / LEVEL355_STALE_TARGET_SHAPE_CHANGED: expected exactly one target implemented-requirement outside the current valid source set.

In the inspected cleanup, that exception is raised when the count of TMP_LEVEL355_STALE_IR differs from one. It is before BEGIN TRANSACTION and both target DELETE statements. This failed attempt did not reach either target DELETE. It did create temporary diagnostic tables before stopping.

The screenshot does NOT disclose the count. It could be zero or greater than one. It does not establish the reason for the mismatch.

Prior same-day evidence remains historical and scoped:
- Level-355 first-batch COMMIT/readback reported 250,845 DIM nodes and 248,032 FACT edges. That establishes the then-current graph was stored, not that every payload was semantically correct.
- Later source checks found 127,495 usable CONTROL_NUMBER values out of 127,496 matched control rows, with one row lacking the tested number/name fallbacks.
- Later decoding, description, and malformed-child changes have not received a successful current commit/readback in the evidence available here.

## Corrections to earlier claims
This checkpoint supersedes the earlier assertions that:
1. the obsolete-row error had already been proved to mean exactly one stale target node;
2. the repeated identity exception had been proved to be duplicate counting of two equivalent hashes;
3. the final set-difference rewrite no longer depended on reconstructing historical identities.

The latest rewrite STILL calculates decoded and JSON-serialized historical hashes for all valid sibling controls. Neither their agreement with the stored target keys nor the exact stored namespace/type filters has been demonstrated by returned counts. One malformed source row is not proof of one stale target row.

## Accepted decisions retained
- Do not invent control-id values.
- Parent/package linkage and ALLOCATED_CONTROL_ID child identity decisions are not changed here.
- Keep the current loader's obsolete-row protection; no broad deletion, truncation, or forced COMMIT.
- Do not treat current read-only inspection as a cleanup or as a repaired load.

## Change and validation actually performed
Added sql/validation/READ_LEVEL355_FAILED_CLEANUP_STATE.sql, a SELECT-only inspection of the temporary objects left by the failed cleanup and the configured DIM target.

It returns tall aggregate counts, including stale-row count, distinct stale keys, valid-key matches, before/after exact metadata filters, and actual stored source/type labels for the affected package. It does not print source record IDs, control text, or hashes. It does not compute new hashes, change mappings, alter tables, or delete rows.

Nine synthetic SQLite tests passed with all write operations prohibited while the inspection statement ran. Tests cover zero/one/multiple stale rows, duplicate candidate keys, duplicate stale rows, null candidate keys, mismatched type/source namespace, and package mismatch. Only the three-part physical target identifier was substituted in the local test. This tests relational counting and read-only execution locally; it is NOT live Snowflake compilation or acceptance. Test script and log accompany this conversation checkpoint.

Official Snowflake documentation checked: temporary tables are scoped to their creating session; DDL has separate transaction behavior. The inspection requires the same SQL session/database/schema as the failed cleanup.

## Next single action and remaining gap
Run the read-only inspection SQL in the still-open SQL session where STALE_SHAPE occurred. Return its count table. Do not rerun the cleanup or notebook to produce it.

If those temporary objects no longer exist, stop and report that exact gap; do not recreate them by executing a script containing DELETE. A repair is pending actual candidate-count/target-label evidence. No new target write was performed by the assistant.
