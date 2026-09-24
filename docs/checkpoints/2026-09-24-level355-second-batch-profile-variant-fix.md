# Level-355 second-batch profile VARIANT parsing fix — 2026-09-24

## Owner-provided live evidence
The read-only second-batch field profiler reached the matched Level-355 working
set successfully:

- MATCHED_LEVEL355_ROWS = 127,496

It then stopped with Snowflake error:

`100069 (22P02): Error parsing JSON: unknown keyword "All", pos 4`

No mapping, registry, source, DIM or FACT write was attempted.

## Cause
The diagnostic used `ARRAY_SIZE` / `OBJECT_KEYS` in a CASE expression against
mixed-shape VARIANT fields. Snowflake can evaluate those expressions on scalar
text values, which can trigger an implicit JSON parse of ordinary text such as
values beginning with "All...".

This is a diagnostic-helper issue, not evidence that the Level-355 source is bad.

## Correction
Root `RUN_NOW.py` now:
- uses `IS_NULL_VALUE` for JSON null detection;
- uses `TO_JSON` to recognize empty arrays/objects safely;
- uses `TRY_TO_VARCHAR` for blank scalar text;
- uses `TO_JSON` for distinct/length aggregates.

The helper remains read-only.

## Next action
Run only the corrected root `RUN_NOW.py` again in the current session.
