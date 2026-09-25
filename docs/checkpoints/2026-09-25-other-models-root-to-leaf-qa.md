# Source One other-model root-to-leaf graph QA — 2026-09-25

Added:
sql/qa/SOURCE_ONE_OTHER_MODELS_ROOT_TO_LEAF_2026-09-25.sql

Repository basis:
- branch: simplify-metadata-boundary
- starting head: 920c8e6658aff16080968df2fe517210aa690817

The file reuses one QA_CONTENT_ID across:
- Assessment Results
- POA&M
- Security Assessment Plan

For each model it:
- scopes DIM rows to Source One and one SOURCE_RECORD_ID;
- anchors at the model root;
- recursively follows FACT FK_SOURCE -> FK_TARGET;
- resolves every child back to DIM;
- labels ROOT / BRANCH / LEAF;
- returns depth, parent/child type, parent/child UUID, dependency type,
  child count, reconstructed structural path and payload.

Expected current shapes:
- Assessment Results: root -> results -> observations/props; optional findings branch can go deeper when native finding records exist.
- POA&M: root -> poam-items.
- Assessment Plan: root -> tasks -> props; task title/type/remarks are payload members.

No Snowflake execution has been performed by the assistant.
