# ALLOCATED_CONTROLS CR/RR table not found by literal column names — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `2a6acd94ebbfdd67762437ece7cf5ecb46e6d752`

## Owner-provided live Snowflake evidence
The first CR/RR trace confirmed:
- one Source One ALLOCATED_CONTROLS metadata row
- FIELD_ID = 23429
- FIELD_TYPE_ID = 9
- LEVEL_ID = 353
- MODULE_ID = 547
- SELECT_ID = null

It found zero current ARCHER_META* tables with literal normalized
`CR_FIELD_ID` + `RR_FIELD_ID` columns.

Result:
`ARCHER_CR_RR_RELATIONSHIP_TABLE_NOT_FOUND`

## Interpretation
This does not invalidate the earlier source-owner relationship guidance. It means
the current Snowflake metadata schema does not expose those relationship columns
under the expected literal names/table prefix.

## Next action
Root `RUN_NOW.py` now performs a narrow exact-ID search for field 23429 across
metadata/relationship/reference/xref tables and field-id-like columns. If nothing
matches there, it widens only to exact field-ID matches across ES_ESC_GRC columns
whose names contain both FIELD and ID.

The output is limited to metadata-like columns; no business/source record values
are printed.

Use the resulting table/column location to identify the reciprocal Archer field
without guessing from Level-355 field names.
