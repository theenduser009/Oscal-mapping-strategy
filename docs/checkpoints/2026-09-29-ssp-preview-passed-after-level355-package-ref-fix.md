# SSP PREVIEW passed after Level-355 package-reference join correction

Date: September 29, 2026
Status: Owner-posted Snowflake PREVIEW report accepted. No target DML or COMMIT occurred.

## Repository basis

Branch:
- simplify-metadata-boundary

Code baseline before this checkpoint:
- 1fc1a4a4848dd0a7d526ff04255b7c1d529cdef6

This baseline includes the corrected allocated-controls joined lookup:
- allocated-control row CONTENT_ID remains its own RequestedObject.Id;
- parent Authorization Package linkage is derived from CURATED_JSON.AUTHORIZATION_PACKAGE[0];
- child identity remains ALLOCATED_CONTROL_ID.

## Owner-posted PREVIEW evidence

Source One / SSP returned:
- pipeline mode = PREVIEW
- pipeline status = PREVIEW_COMPLETE
- source = source-one
- model = SSP
- release = oscal-lean-daily-v3.1
- writes_executed = false
- persisted = false
- committed = false
- target_dml_attempted = false
- pre_write_validation_passed = true
- source_records = 2,813
- nodes = 546,799
- edges = 543,986
- validation_passed = true
- storage_verified = true

Expected target changes:
- DIM inserts = 0
- DIM updates = 0
- DIM unchanged = 546,799
- FACT inserts = 0
- FACT updates = 0
- FACT unchanged = 543,986

Route status:
- PREVIEW_PASSED_NO_TARGET_DML

Temporary cleanup:
- REMOVED

Aggregate:
- writes_executed = false
- commit_attempted = false

## Interpretation

The current persisted SSP target exactly matches the freshly generated candidate graph under the corrected Level-355 parent-link contract.

The earlier OBSOLETE_TARGET_ROWS_BLOCKED failure is resolved by deriving package lineage from AUTHORIZATION_PACKAGE[0] rather than reusing allocated-control CONTENT_ID as package identity.

Because expected inserts and updates are both zero for DIM and FACT, there is no downstream SSP COMMIT required for this current graph state.

This PREVIEW does not independently prove when or by which earlier process the current target rows were persisted. It proves only that the current target and current candidate graph now reconcile exactly.

## Next action

Do not run an SSP COMMIT merely to force a no-op write.

Proceed to the remaining downstream work:
- update the OSCAL responsible-party mapper to consume persisted ResolvedUser EEID/name if those attributes are required in party payloads;
- keep GroupList / Meta Group support pending;
- preserve this PREVIEW as the accepted post-Matillion SSP zero-delta checkpoint.
