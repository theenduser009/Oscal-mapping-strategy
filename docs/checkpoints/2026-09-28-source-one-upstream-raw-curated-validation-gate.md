# Source One upstream raw-to-curated validation gate — 2026-09-28

Current Source One runtime mapper reads:
RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW.CURATED_JSON

The repository does not currently establish the exact physical pre-CURATED
payload column/table used by the upstream Matillion FieldID-to-name conversion.
Do not invent that source contract.

Added read-only discovery:
sql/qa/SOURCE_ONE_UPSTREAM_PAYLOAD_DISCOVERY_2026-09-28.sql

Next evidence required:
- output of the column inventory for ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW.

After the actual source-payload column is known, build and run an aggregate
raw-payload -> CURATED_JSON reconciliation covering:
- row/CONTENT_ID parity;
- mapped FieldID/key coverage;
- null preservation;
- source-to-curated value equality;
- duplicate or dropped fields;
- unexpected curated-only keys.

This upstream gate is separate from the already committed/read-back verified
OSCAL DIM/FACT checkpoints.
