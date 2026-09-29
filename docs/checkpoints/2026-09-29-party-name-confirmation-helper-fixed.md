# Party-name PREVIEW confirmation helper corrected

Date: September 29, 2026
Status: Owner-posted Snowflake error reviewed. The SSP PREVIEW itself remains accepted; only the follow-up read-only confirmation helper failed to compile. No target DML or COMMIT occurred.

## Error

The helper used Snowpark Column.contains('"name"'), which Snowflake interpreted as an identifier rather than a string literal and raised:
- SQL compilation error
- invalid identifier '"name"'

This error is isolated to the diagnostic helper. It does not invalidate the already successful SSP PREVIEW:
- PREVIEW_COMPLETE
- pre_write_validation_passed = true
- DIM inserts = 0
- DIM updates = 22,976
- FACT inserts = 0
- FACT updates = 0
- PREVIEW_PASSED_NO_TARGET_DML

## Fix

Updated:
- notebooks/validation/13_ssp_party_name_preview_confirmation.py
- commit: 2164cc812d3ea94119862fc228d5a47661d7076d
- blob: 51ef91ef262409d4dc6ce8f6d5b24cd178ec3bda

The helper now counts named parties with:
PARSE_JSON(METADATA_JSON):name IS NOT NULL

No mapper code, mapping CSV, registry, target table, or source data was changed.

## Next action

In the same notebook session, rerun only the corrected confirmation helper. Do not rerun Cell 7 and do not COMMIT yet.
