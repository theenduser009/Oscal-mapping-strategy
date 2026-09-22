# Source One end-to-end QA package — 2026-09-22

## Repository version
- Branch: `simplify-metadata-boundary`
- Head after QA guide + SQL publication: `2e09f6eefbb2e92dc3a6400accd86f3b09ffabe1`

## Material update
Published a read-only QA handoff for testing one Source One Authorization Package
record across the current runtime routes.

Files:
- `sql/qa/SOURCE_ONE_E2E_QA.sql`
- `docs/qa/2026-09-22-source-one-e2e-qa-guide.md`

The SQL was generated from the current Source One runtime mapping CSV on this
branch:
- 103 APPROVED / BLOCKED_IF_POPULATED runtime rows represented
- 4 CONFIG-sourced rows explicitly separated
- 43 current Assessment Results runtime rows represented in the AR comparison
- 9 responsible-party role mappings represented

## Runtime scope captured
Current Cell 1 Source One routes:
- SSP
- ASSESSMENT_RESULTS
- POAM
- SECURITY_ASSESSMENT_PLAN

The QA package explicitly prevents Source One / Source Two confusion:
- Catalog is Source Two, not Source One.
- Profile is not a current Source One runtime route.

## Tests included
- representative CONTENT_ID discovery
- source-record uniqueness
- approved/guarded source-field inventory with raw value/type/state
- live registry hierarchy/operator/identity rules
- target root/node counts
- SSP direct source-to-target examples
- responsible-party review
- system-implementation component reconciliation
- Assessment Results observation/result-property review
- POA&M reference/item comparison
- Security Assessment Plan source/task review
- per-model graph orphan/cross-record integrity checks
- optional recursive SSP tree/path reconstruction

## Known open items preserved
- Level-355 SSP Control Implementation remains blocked on missing
  `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`.
- SSP AUTHORIZATION_DECISION 2,308-node/edge delta is PREVIEW-reconciled but
  current COMMIT/read-back has not been supplied.
- Assessment Results RISK_ASSESSMENT_REPORT remains deferred.
- FINDINGS destination is known; current reviewed Source One value was null.
- RECOMMENDED_SECURITY_CATEGORY remains BLOCKED_IF_POPULATED.
- No newer repository checkpoint proves POAM or Security Assessment Plan
  COMMIT/read-back; QA must use actual environment evidence.

## Validation actually performed
- Current branch and current Cell 1 were inspected before authoring.
- Current `Mapping/ARCHER_OSCAL_MAPPINGS.csv` was parsed to generate the QA
  mapping inventory.
- The two new GitHub files were read back successfully after commit.
- No Snowflake execution was performed by this chat; SQL runtime syntax/results
  remain to be verified by the QA tester/owner in Snowflake.

## Next action
Have the QA tester run section 01A of the SQL first, choose a representative
`CONTENT_ID`, set `QA_CONTENT_ID`, then run the remaining sections and return
the result grids/screenshots. Do not treat an old project checkpoint as proof of
that new QA run.
