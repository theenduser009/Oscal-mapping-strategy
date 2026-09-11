# SSP daily loading in the shared seven-cell workflow

The earlier SSP-only Cells Six/Seven revision is superseded by the
[shared multi-model workflow](SHARED_SEVEN_CELL_MAPPER.md). Use that guide,
not an old `SSP_LOAD_MODE` setting or a separate execution cell.

SSP full DEV reload is accepted: 2,813 records, 70,102 DIM / 67,289 FACT.
Shared daily preview/commit acceptance is still pending. No reload is needed.

## Daily policy retained

- Insert new keys; update existing keys only for changed business values.
- Preserve unchanged rows and their audit values.
- Validate unique keys, UUIDs, payloads, parent links and source-record coverage.
- Preflight before target DML; use one DIM/FACT transaction per source/model.
- Second merge pass must insert/update zero rows; verify saved data before and after commit.
- Preserve absent input records. Obsolete keys in selected records block writes.
- No DELETE, TRUNCATE, permanent backup creation or implicit deletion policy.
- Unknown commit, rollback failure or failed post-commit readback requires review; no automatic retry.

The shipped Source One selection includes AR, whose actual destination schema
is unverified. It is therefore PREVIEW-only. Do not remove the AR route merely
to bypass this boundary without agreeing the intended write scope.

Temporary input snapshots/staging are session-local. Pause other target
writers for an authorized commit; baseline comparisons are not an exclusive lock.
Matillion daily scheduling/deployment and production readiness are not established
by local tests or by the prior one-time DEV reload.
