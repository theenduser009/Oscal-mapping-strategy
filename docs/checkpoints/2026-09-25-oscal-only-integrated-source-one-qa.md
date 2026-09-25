# OSCAL-only integrated Source One QA — 2026-09-25

Added:
sql/qa/SOURCE_ONE_OSCAL_ONLY_INTEGRATED_QA_2026-09-25.sql

Purpose:
- query only the four OSCAL DIM/FACT model pairs;
- aggregate to one row per Source One SOURCE_RECORD_ID before cross-model join;
- validate within-model FACT relationships;
- validate all four models exist for the same business key;
- provide one-content-id node and edge drilldowns.

Cross-model linkage is SOURCE_RECORD_ID. FACT foreign keys are intentionally
model-local and are not used to create fake cross-model edges.

No persistent curated view was created because the current project constraint
does not use curated views. The final SELECT can later be wrapped in a view if
the architecture permits it.

No Snowflake execution has been performed by the assistant.
