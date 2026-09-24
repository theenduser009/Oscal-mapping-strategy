# Level-355 projected VARIANT decode correction — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head after correction: `63d961e08ce1c7f579b491239293284c0c454bd9`

## Owner-provided PREVIEW evidence
After adding `IMPLEMENTATION_DETAILS -> implemented-requirement.description`, the
fresh SSP PREVIEW returned:

- nodes = 250,845
- edges = 248,032
- DIM inserts = 0
- DIM updates = 127,496
- DIM unchanged = 123,349
- FACT inserts = 0
- FACT updates = 0
- FACT unchanged = 248,032
- status = PREVIEW_PASSED_NO_TARGET_DML

The update count exactly equals the total number of Level-355
`implemented-requirements[]` rows.

## Diagnosis
The joined-record optimization projected individual VARIANT members with Snowpark
`GET(...)` and passed the collected scalar value directly into the mapper.

Snowpark can return projected VARIANT scalars in JSON-serialized string form:
- JSON null may arrive as the Python string `"null"`;
- JSON strings may arrive quoted/serialized.

The generic mapper's existing `_to_python()` does not JSON-decode scalar strings.
Therefore a JSON null can be mistaken for populated text, which can cause every
implemented-requirement row to receive a description such as `"null"`.

This also means the first committed `CONTROL_NUMBER -> control-id` batch may
have preserved JSON serialization around projected string values. That must be
corrected/read-back verified, not ignored.

## Correction
Cell 4 now JSON-decodes projected joined-record VARIANT values before mapping:
- JSON null -> Python None
- JSON string -> Python string
- JSON object/array -> Python object/list
- already-plain non-JSON text remains unchanged

Updated:
- `notebooks/cells/04_parsing_transform_payload_helpers.py`
- `notebooks/cells_v2/04_parsing_transform_payload_helpers.py`

No target DML was performed by this correction.

## Next action
Refresh the latest Cell 4 in the current notebook session, rerun Cell 4 and then
Cell 7 in PREVIEW mode.

Do not COMMIT the 127,496-update preview shown before this correction.

The corrected PREVIEW should tell us:
- whether existing control-id payloads require normalization updates;
- how many rows truly gain IMPLEMENTATION_DETAILS descriptions.
