# Level-355 CONTENT_ID match sample SQL published — 2026-09-24

## Repository version
- Branch: `simplify-metadata-boundary`
- Head after SQL publication: `e1f80e6508af0f5885e5183577bf94ccb575521c`

## Change
Published a read-only SQL sample to inspect the direct `CONTENT_ID` matches between:
- `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`
- `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`

The query selects:
- CONTROL_NUMBER
- CONTROL_NAME
- IMPLEMENTATION_DETAILS
- IMPLEMENTATION_STATUS
- ALLOCATED_CONTROL_ID
- AUTHORIZATION_PACKAGE

No DML is included.

## Next action
Run the SQL in Snowflake and use the returned values to confirm whether these matched rows are the correct per-control records for OSCAL `implemented-requirements[]`.
