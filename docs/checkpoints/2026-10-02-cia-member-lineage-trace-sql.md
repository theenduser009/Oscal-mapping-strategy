# 2026-10-02 CIA Member -> Archer Field Trace SQL

## Repository checkpoint
- Branch: `simplify-metadata-boundary`
- Helper commit: `427d2c938344f3a7137e7465df9aa0ab287de759`
- Added: `TRACE_CIA_MEMBER_TO_ARCHER_FIELD.sql`

## Purpose
Provide one simple, read-only Snowflake query that starts from a persisted
`security-impact-level` node and returns the Archer source-field lineage for one
selected CIA member.

The query uses:
1. the selected `security-impact-level` node for one `SOURCE_RECORD_ID`;
2. FACT to locate its `system-characteristics` parent;
3. sibling `props` lineage nodes with `name = source-field`;
4. the current 11-field CIA mapping inventory to keep only source fields that target
   the selected OSCAL member.

## Validation actually performed
- Current branch and current 11 `security-objective` mapping rows were inspected first.
- The SQL helper was committed and read back from GitHub.
- No Snowflake execution was performed from ChatGPT.

## Next action
Run the helper for one content ID and one member such as
`security-objective-availability`. Review the returned `ARCHER_SOURCE_FIELD` values.
