# SSP pilot: replace cross-schema temporary views with snapshots

Date: 2026-09-11. Release: `ssp-one-record-write-v3-temp-materialization`.
Scope: the already approved one-record SSP development persistence pilot.

## What the uploaded evidence establishes

The [owner's query-history checkpoint](../ssp_dim_fact_physical_schema_checkpoint_2026-09-11.md)
records CREATE_VIEW failures with error 2003 for a Snowpark temporary backing
table looked up in the curated schema. The recorded session context differs
from that schema. The attempted pilot mode was PREVIEW: no persistent target
DML or SSP write acceptance occurred.

The pilot's graph-freezing helper created two fully qualified views over the
accepted graph DataFrames. Snowflake resolves a view's unqualified source
objects in the view's schema, which is consistent with this failure pattern.
Fully qualifying a view's own name does not qualify every dependency in its
definition. [Snowflake CREATE VIEW resolution rules](https://docs.snowflake.com/en/sql-reference/sql/create-view#general-usage-notes)

This evidence identifies the failing boundary; it does not conclusively rule
out expired source objects or missing privileges. No permissions are inferred
solely from the recorded role name. The separate raw-table SELECT failures in
the history are outside this correction and do not change configured sources.

## Bounded change

Both accepted graph frames are now materialized with
`frame.write.save_as_table(..., mode="errorifexists", table_type="temporary")`.
The API waits for completion by default. Each random pilot name receives a
session-temporary table, not a persistent table or a view definition. Existing
objects are not overwritten. [Snowpark save_as_table](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.DataFrameWriter.save_as_table)

All subsequent pilot SQL reads these snapshots. Full graph counts, one-record
tree selection, PK/FK checks, physical key/UUID conversion, baseline snapshots,
rollback rehearsal, repeat MERGEs, final commit and readback remain unchanged.
All temporary materialization is before target DML and explicit transactions.

The code changes no role, database/schema context, registry rows, target DDL,
source-table name, accepted graph identity or mapped JSON. It cannot resurrect
an expired source table or grant access. Materialization must use the same
active session/context as the accepted DataFrames and subsequent pilot SQL.

Materialization errors now identify whether nodes or edges failed and preserve
a valid Snowflake query ID when available. Generated SQL and source values are
not printed. No automatic retry, role switch, or source-data rebuild is added.

## Verification and next action

Local verification: **35 pilot tests; 298 repository tests pass**. New focused
checks require temporary-only synchronous materialization of both frames before
scoped graph SQL, disallow the former view path through the test interface, and
verify safe, actionable failure reporting without target DML. Local mocks do not
prove Snowflake runtime execution; the posted upload is an error checkpoint,
not a successful corrected run.

Replace only the separate [pilot Python cell](../../notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py)
with the full updated file. In the still-active accepted SSP session, set
`SSP_PILOT_MODE = "COMMIT"` near the top for the already approved one-record
DEV write. Leave normal `CONFIG["EXECUTE_WRITES"] = False`. Pause other target
writers and run no concurrent SQL in the pilot session. Run this pilot once,
then post its aggregate report. COMMIT includes all preflight checks and the
rollback rehearsal; an inaccessible staging source stops before target DML.

No registry setup, query-history rerun or mapper rerun is requested while the
accepted outputs remain available. Do not reuse a restarted/invalid source
session or blindly retry failures. Success is
`ONE_RECORD_COMMITTED_AND_VERIFIED` with `PERSISTED: true`. Bulk SSP and AR
persistence are still separate, unaccepted work.
