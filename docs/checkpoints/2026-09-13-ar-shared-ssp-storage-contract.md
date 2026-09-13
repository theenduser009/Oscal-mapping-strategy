# AR uses the shared SSP storage contract

Owner decision: September 13, 2026, current task voice clarification.

The owner confirmed that AR and subsequent model tables use SSP's timestamp,
hash, UUID, column length and nullability rules. Only model, table and primary-key
names differ. The NTZ timestamp/omitted second timestamp in the earlier posted
AR definition are mistakes to reconcile, not a separate physical profile.

Use the full-name DIM/FACT pair and keys in the
[owner-posted evidence](2026-09-13-assessment-results-dim-fact-target-evidence.md).
The abbreviated AR DIM remains unselected. The intended DIM includes both
DW_LOAD_TIMESTAMP and DW_LOAD_TIMESTAMP_TZ as TIMESTAMP_TZ(9). Hashes are
BINARY(16); stored UUIDs are VARCHAR(32), with existing canonical graph UUIDs
and identities unchanged.

Cell One now binds AR to that owner-confirmed contract. VERIFIED in deployment
configuration confirms the chosen contract; it is not a live schema readback.
The unchanged Cell Six still runs DESC TABLE and checks exact column types,
lengths and nullability before staging or target DML. A mismatch stops the run.
No separate timestamp transform, loader, runtime branch or registry change is
introduced. The seven maintained cells total 1,850 lines (12 configuration lines
added). The field scope remains 30 enabled AR rows and 15 deferred rows.

The owner authorized proceeding to AR loading and offered to correct/recreate
AR tables if needed. No table has been altered, dropped or written by this code
publication. The [target definition](../../sql/CREATE_ASSESSMENT_RESULTS_TABLES.sql)
creates missing tables only and leaves existing tables/rows untouched; it does
not fix existing schema mismatches. Preserve existing rows when reconciling them.

Validation at preparation: local suite ran 182 tests, passing with three
Snowpark-dependent classes skipped because the package is absent locally.
Four exact private screenshot scalar examples also passed mapping/graph
validation (12 nodes, 8 edges), with no target writes. Real values remain outside
GitHub. New CI coverage exercises AR inserts, one payload update, unchanged
commit/readback, SSP isolation and rejection of incorrect timestamp columns.
CI completion and live AR load are separate evidence; neither is claimed here.

Next action: follow [AR next run](../AR_NEXT_RUN.md). Align existing AR tables to
the shared definition if needed, replace Cell One, select AR only, and run the
seven cells with Cell Seven COMMIT. The runner performs all route previews and
schema/graph/storage checks before target DML. Capture COMMITTED_AND_VERIFIED
plus DIM/FACT changes and committed readback. An unknown commit outcome must be
inspected rather than automatically retried.
