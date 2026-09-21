# Source One Assessment Results compiled mapping + population checkpoint — 2026-09-21

## Repository basis
- Branch before this checkpoint: `2a19b6c916aa5b7bcfd391dec6b202450ddf01e0`
- Populated-shape validation added in commit:
  `78e7df21e6fc5cefcf45165e309f44a8a31bbdb5`

## Owner-provided Snowflake notebook evidence
After replacing the notebook-visible `ARCHER_OSCAL_MAPPINGS.csv` with the
current GitHub runtime CSV, the owner reran Cells 1-3 and then the read-only
compiled mapping check.

Observed:
- route status: `READY`
- selected Assessment Results rows: `44`
- newly approved fields compiled: `12`

The 12 compiled transforms/targets matched the repository decisions:
- 3 scalar score fields -> `assessment-results.results[].observations[]`
- RISK_ACCEPTANCE_RBDS / RISK_ASSESSMENT_REPORT and workflow metadata ->
  `assessment-results.results[].props[]`
- WORKFLOW_STATUS -> `archer-select`
- DUE_DATE / WORKFLOW_STATUS_CHANGED -> `date`

## Population counts from the owner-provided current Source One snapshot
All counts are across 2,813 Source One records.

| Field | Present | Null | Populated |
|---|---:|---:|---:|
| AVG_SECURITY_COMPLIANCE_REPORTING_SCORE | 2813 | 13 | 2800 |
| AVG_SECURITY_COMPLIANCE_SCORE | 2813 | 13 | 2800 |
| TOTAL_PACKAGE_INHERENT_RISK | 2813 | 1 | 2812 |
| RISK_ACCEPTANCE_RBDS | 2813 | 2812 | 1 |
| RISK_ASSESSMENT_REPORT | 2813 | 2497 | 316 |
| WORKFLOW_CURRENT_NODE | 2813 | 2211 | 602 |
| WORKFLOW_PROCESS_VERSION | 2813 | 2198 | 615 |
| WORKFLOW_JOB_STATUS | 2813 | 2198 | 615 |
| WORKFLOW_STATUS | 2813 | 0 | 2813 |
| DUE_DATE | 2813 | 2813 | 0 |
| WORKFLOW_CURRENT_NODE_HRTN | 2813 | 2226 | 587 |
| WORKFLOW_STATUS_CHANGED | 2813 | 0 | 2813 |

## Important superseded assumption
Earlier September 21 discussion used one inspected record in which several
workflow/report fields were null. The aggregate check proves those fields are
populated in other Source One records. Therefore that one-record null evidence
must not be used to justify the selected transforms.

In particular:
- RISK_ASSESSMENT_REPORT is populated in 316 records.
- workflow current node/process/job/HRTN fields are populated in hundreds of records.
- WORKFLOW_STATUS and WORKFLOW_STATUS_CHANGED are populated in all 2,813 records.
- RISK_ACCEPTANCE_RBDS has one populated record.

## Why Cells 4-7 are paused
The compiled-mapping check was intentionally run after Cells 1-3 only, so
`PREVIEW_GROUP: NOT_FOUND` is expected and is not a failure.

Before rerunning Cells 4-7, the populated values need a privacy-safe structural
shape check. A field mapped with `direct` to `results[].props[]` must resolve
to exactly one scalar value per source field; a populated object/array would
require a different transform instead of being silently flattened.

## Next action
Run:
`notebooks/validation/2026-09-21_source_one_ar_populated_shape_check.py`

This is read-only and prints only aggregate type/key signatures. It determines
whether the 12 approved transforms are compatible with the actual populated
Source One values before the next full PREVIEW.

No DIM/FACT DML is authorized by this checkpoint.
