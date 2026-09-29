# SSP obsolete rows isolated to all Level-355 implemented requirements

Date: September 29, 2026
Status: Owner-posted output from notebooks/validation/12_ssp_obsolete_target_rows_diagnostic.py reviewed. Diagnostic partially completed before a query-only classification error. No target write or commit occurred.

## Observed failed-PREVIEW temp-stage evidence

The diagnostic successfully attached to the failed PREVIEW temporary stage and reported:

- OBSOLETE_DIM_ROWS = 127,495
- OBSOLETE_FACT_ROWS = 127,495
- AFFECTED_SOURCE_RECORDS = 1,895
- CANDIDATE_DIM_ROWS = 419,304
- CANDIDATE_FACT_ROWS = 616,491

Obsolete DIM by element type:
- ELEMENT_TYPE = implemented-requirements
- OBSOLETE_ROWS = 127,495
- SOURCE_RECORDS = 1,895

This isolates the loader block to the previously persisted Level-355 implemented-requirement population. Other SSP element types are not shown as obsolete in the successfully completed section.

The 1,895 affected source-record count exactly matches the earlier verified count of distinct Authorization Package CONTENT_ID values that joined to ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW by p.CONTENT_ID = s.CONTENT_ID on September 24.

## Diagnostic script defect

The next classification query failed with Snowflake SQL compilation error:
CLASSIFICATION is not a valid group by expression.

That error belongs to the read-only diagnostic query, not the OSCAL mapper or loader. The classification block has been corrected in GitHub:
- update commit: ffaa839c8d3434805fd9f3070498ce057c5fdfc8
- corrected blob: f754aee2e90bc6b023202c8794dbdd273105227f

No need to rerun the whole mapper to correct this diagnostic.

## Leading cause to verify

Historical evidence established that ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW.CONTENT_ID is package-grain lineage used to join controls to Authorization Package records, while ALLOCATED_CONTROL_ID is child identity.

The recent generic raw-to-curated candidate changed CONTENT_ID to RequestedObject.Id. If that generic update was applied to the allocated-controls table, it may have replaced the package-grain join key with the allocated-control row's RequestedObject.Id and thereby removed/re-keyed the entire previously persisted implemented-requirement population from the current candidate graph.

This is a strong evidence-based hypothesis, not yet a confirmed current-table fact.

## Focused read-only diagnostic

Published:
- sql/validation/2026-09-29_level355_post_refresh_join_key_diagnostic.sql
- commit: 79de1e4d328506a268be343e187090715f552556

It compares current allocated-controls:
- stored CONTENT_ID
- RequestedObject.Id
- Authorization Package field
against current Authorization Package CONTENT_ID and reports join coverage/counts without returning sensitive payload values.

## Next action

Run only the focused Level-355 join-key diagnostic. Do not delete/re-key target SSP rows and do not commit. The result will determine whether the generic CONTENT_ID correction must be scoped to Authorization Package only and whether allocated-controls must retain/rebuild its package-grain CONTENT_ID.
