# Assessment Results Source One bulk mapping checkpoint — 2026-09-21

## Repository basis
- Branch: `simplify-metadata-boundary`
- Starting head reviewed before this change: `d17ee32d2bbea4a6ccdcf152fa7ab447242f4548`
- CSV update commit: `04bda37aeb20884c77ab3c8f0365eebc1fac30f8`
- Result-properties registry setup commit: `982418a069be3e443815b74c0427dad98c1536d6`

## Owner-reviewed Source One decisions
This checkpoint records the September 21 owner review of the current Source One
Assessment Results payload. It supersedes the older DEFERRED status for the rows
listed below. No private source values are recorded.

### Newly approved observations
- AVG_SECURITY_COMPLIANCE_REPORTING_SCORE -> assessment-results.results[].observations[] / scalar-score
- AVG_SECURITY_COMPLIANCE_SCORE -> assessment-results.results[].observations[] / scalar-score
- TOTAL_PACKAGE_INHERENT_RISK -> assessment-results.results[].observations[] / scalar-score

The owner confirmed each is a single scalar; numeric zero is valid and must not
be treated as missing.

### Newly approved result properties
The following map under `assessment-results.results[].props[]`:
- RISK_ACCEPTANCE_RBDS -> direct
- RISK_ASSESSMENT_REPORT -> direct, with representation to be revisited if a future populated value proves to be a structured document/reference
- WORKFLOW_CURRENT_NODE -> direct
- WORKFLOW_PROCESS_VERSION -> direct
- WORKFLOW_JOB_STATUS -> direct
- WORKFLOW_STATUS -> archer-select
- DUE_DATE -> date
- WORKFLOW_CURRENT_NODE_HRTN -> direct
- WORKFLOW_STATUS_CHANGED -> date

Current nulls are omitted. The reviewed WORKFLOW_STATUS shape is an Archer
value-list container, so the existing Archer lookup resolver is used. For fields
approved as direct while currently null, a future non-scalar value will block
rather than being silently flattened.

### FINDINGS
FINDINGS remains DEFERRED in the runtime CSV in this checkpoint. Its canonical
destination is `assessment-results.results[].findings[]`. The repository already
contains finding-branch registry support, but the current Source One sample is
null and the Source One finding reference/payload contract is not changed by
this bulk property/observation update.

## Files changed
- `Mapping/ARCHER_OSCAL_MAPPINGS.csv`
- `sql/registry/ENABLE_ASSESSMENT_RESULTS_RESULT_PROPS.sql`
- this checkpoint

## Status
- IMPLEMENTED IN REPOSITORY: 12 previously deferred AR mappings were enabled in CSV.
- REGISTRY SETUP PREPARED: result-level props setup SQL is committed.
- NOT EXECUTED IN SNOWFLAKE: this chat has no live Snowflake connection.
- NOT PREVIEWED: the seven-cell mapper has not been rerun against live Source One.
- NOT COMMITTED TO DIM/FACT: no Snowflake target DML was performed.
- READ-BACK VERIFIED: repository writes above are recorded; live Snowflake readback remains pending.

## Expected metadata count effect
Using the pre-change 153-row inventory as the basis:
- APPROVED: 86 -> 98
- DEFERRED: 64 -> 52
- EXCLUDED: 2 unchanged
- BLOCKED_IF_POPULATED: 1 unchanged
Assessment Results selected rows should increase from 32 to 44 after the updated
CSV is reloaded, with FINDINGS remaining the only deferred AR row from the former
13-row backlog.

## Next action
Run `sql/registry/ENABLE_ASSESSMENT_RESULTS_RESULT_PROPS.sql` in Snowflake and
confirm `AR_RESULT_PROPS_REGISTRY_VERIFIED`. Then rerun Cells 1-7 with
`ASSESSMENT_RESULTS` selected in PREVIEW so Cell 2 reloads the CSV and registry.
Review routing count, graph counts, and proposed DIM/FACT changes before any COMMIT.
