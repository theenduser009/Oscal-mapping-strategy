# Source One historical-to-OSCAL real-data QA — 2026-09-25

Owner confirmed historical structured-table naming: use the same Archer table name
as current RAW with trailing _RAW removed.

Added:
sql/qa/SOURCE_ONE_HISTORY_VS_OSCAL_2026-09-25.sql

The query is read-only and compares:
- historical Authorization Package vs current RAW CONTENT_ID sets;
- every current approved/guarded Source One source field that also exists as a
  historical structured column;
- historical common CONTENT_IDs to one current OSCAL root in all four models;
- historical direct/native SSP values to final SSP payload values;
- historical Assessment Results scalar-score columns to final observation values;
- historical Level-355 control rows to current Level-355 RAW and final
  implemented-requirements control-id values;
- one real CONTENT_ID across historical, RAW and final SSP payloads.

Use together with:
sql/qa/SOURCE_ONE_PRODUCTION_QA_2026-09-25.sql

No Snowflake query was executed by the assistant. Owner execution results are
required before any PASS/FAIL production sign-off.
