# Source One QA source-of-truth rule — 2026-09-25

Owner-confirmed validation rule:

1. Authorization Package and other Source One domains with an available historical
   structured table should be validated historical structured table -> current RAW
   -> OSCAL DIM/FACT.
2. Level-355 Allocated Controls has no readable historical structured table in the
   current Snowflake environment. Level-355 validation therefore uses current RAW:
   ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW -> SSP implemented-requirements
   DIM/FACT.
3. Do not infer or hard-code a nonexistent historical Level-355 table name.

The current history-vs-OSCAL QA SQL was corrected accordingly in commit
7db2bc040e19d5477caf6d46752d31c4904914a9.

This checkpoint supersedes the earlier assumption that every RAW table has a
readable historical counterpart with the trailing _RAW removed.
