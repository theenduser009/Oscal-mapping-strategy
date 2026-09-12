# DEV registry column-cleanup checkpoint

Date: 2026-09-12

The owner explicitly approved physically removing the fifteen retired
experimental metadata columns from
`RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY`.

The one-time cleanup SQL is restricted to that exact table and allowlist. It
preflights the original nine plus three active columns, rejects any unexpected
schema, fingerprints every retained row, performs one multi-column drop with
`RESTRICT`, and verifies exactly twelve columns and the unchanged row
fingerprint afterward. It does not run DML or access DIM/FACT. DDL cannot be
transactionally rolled back, so other registry writers must be paused.

All 697 local tests pass, including six cleanup-scope tests. The SQL has not
been run in Snowflake; local tests are not live proof.

Next action: run the complete cleanup SQL once in a fresh DEV worksheet and
share its single returned object. Do not run the notebook yet.

