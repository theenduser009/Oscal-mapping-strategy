# Source One production QA pack — 2026-09-25

## Why this supersedes the older QA pack
The repository already contained sql/qa/SOURCE_ONE_E2E_QA.sql from 2026-09-22.
That file predates the final Level-355 Control Implementation, final Assessment
Results attachment/null-preservation mappings, and the final SSP source-preservation
batch. It must not be used unchanged as the final production sign-off.

## New current QA file
sql/qa/SOURCE_ONE_PRODUCTION_QA_2026-09-25.sql

It is read-only and uses current target contracts from Cell 1.

Coverage:
1. RAW CONTENT_ID uniqueness
2. current release graph cardinality and baseline counts
3. one root per CONTENT_ID per model
4. DIM PK/UUID/audit/lineage integrity
5. FACT PK/FK/orphan/UUID/self-edge/cross-record/cross-namespace integrity
6. one incoming parent for every non-root and zero for roots
7. cross-model CONTENT_ID coverage
8. Level-355 control-id multiplicity parity
9. POA&M item-count parity
10. direct native-field value parity
11. one-record drill-down across four models
12. idempotency sign-off procedure

## Legacy comparison gap
The exact old historical table name/columns are not present in the current repository.
Do not infer them from recollection. The owner should provide the fully qualified
legacy table name, its content-id column, and DESCRIBE TABLE output (or exact column
list). Then create a separate exact legacy-vs-OSCAL SQL comparison.

## Execution status
The assistant cannot execute Snowflake from this chat. The QA SQL is committed but
has not yet been run in the owner's Snowflake session. Results must be captured and
checkpointed after execution.
