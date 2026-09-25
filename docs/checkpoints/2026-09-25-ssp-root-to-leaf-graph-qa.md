# SSP root-to-leaf graph QA — 2026-09-25

Added:
sql/qa/SSP_ROOT_TO_LEAF_GRAPH_2026-09-25.sql

Purpose:
- take one Source One Authorization Package SOURCE_RECORD_ID / CONTENT_ID;
- start at the system-security-plan root;
- follow FACT parent->child edges recursively;
- resolve every child back to the SSP DIM;
- label each row ROOT / BRANCH / LEAF;
- expose parent/child element types, UUIDs, dependency type, depth,
  reconstructed structural path and stored payload.

Core graph contract:
- DIM PK = node identity in storage.
- FACT FK_SOURCE_ELEMENT_HASH = parent node PK.
- FACT FK_TARGET_ELEMENT_HASH = child node PK.
- SOURCE_RECORD_ID scopes the whole SSP tree to one Authorization Package.

This is a read-only graph inspection query. No live Snowflake result has been
executed by the assistant.
