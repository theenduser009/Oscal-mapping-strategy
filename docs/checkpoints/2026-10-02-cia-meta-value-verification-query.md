# 2026-10-02 CIA Meta-Value Verification Query

## Repository checkpoint
- Branch: `simplify-metadata-boundary`
- Source commit inspected before change: `ef9ac282d2798f04ebe785e0ed0db8ded91dda86`
- Query commit: `02cad265b938f734ccf5c4f643cb2e912782f42b`
- Added: `VERIFY_CIA_VALUE_IDS_AGAINST_ARCHER_META.sql`

## Why this was added
The owner requested direct proof that populated CIA/FIPS `ValuesListIds` resolve to the labels stored in `ARCHER_META_VALUE`, specifically to determine whether observed `Legacy LOE ...` values actually originate in Archer metadata.

## What the query proves
For the 11 approved CIA source fields, the query compares:
1. source `ValuesListIds`
2. Matillion `ResolvedValues[].ValueId/ValueName/LookupStatus`
3. `ARCHER_META_VALUE.SELECT_VALUE_ID/SELECT_VALUE_NAME`

It classifies each unique meta label as:
- `CANONICAL_FIPS` for Low/Moderate/High
- `LEGACY_LOE` only when the Archer meta label itself starts with `Legacy LOE`
- `OTHER`
- `META_MISSING`
- `META_AMBIGUOUS`

No LOE-to-FIPS crosswalk is introduced.

## Validation actually performed
- Current runtime CSV and Cell 4 behavior were inspected before the query was written.
- The SQL file was committed and read back from GitHub.
- No Snowflake execution was performed from this chat.

## Remaining gap / next action
Run `VERIFY_CIA_VALUE_IDS_AGAINST_ARCHER_META.sql` in Snowflake and review RESULT 1. The live output is required before concluding whether each observed Legacy LOE label is sourced from Archer metadata.
