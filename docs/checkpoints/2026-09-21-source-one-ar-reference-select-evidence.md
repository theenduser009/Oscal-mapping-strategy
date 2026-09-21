# Source One Assessment Results targeted reference/select evidence — 2026-09-21

## Owner-provided live read-only evidence
The targeted Source One AR reference/select check produced the following:

### RISK_ACCEPTANCE_RBDS
- 2,812 null records
- 1 populated array
- array length = 1
- array element shape = OBJECT
- object keys = `ContentId,LevelId`
- one ContentId object and one LevelId object
- no Archer select container
- the one numeric token does not match ARCHER_META_VALUE

Interpretation: this is Archer cross-reference structure, not a direct scalar
property and not an Archer select-value container.

### RISK_ASSESSMENT_REPORT
- 2,497 null records
- 316 populated arrays
- 742 total numeric members
- every numeric member is unique in the current snapshot
- array lengths range from 1 up to 100
- 610 numeric tokens happen to match an entry in the global ARCHER_META_VALUE lookup
- 132 do not match ARCHER_META_VALUE
- no ContentId/LevelId wrapper objects
- no select-value container object

Interpretation: the shape is multi-valued numeric-reference-like data. The global
ARCHER_META_VALUE collision count is not enough to call it a select field because
the payload is not a select container and all 742 members are unique. The Archer
field metadata must be checked before choosing a final runtime transform/path.

### WORKFLOW_JOB_STATUS
- 2,198 null records
- 615 populated OBJECT records
- all populated objects use `OtherText,ValuesListIds`
- all 615 contain a select-value container
- select cardinality is exactly one for all 615 populated records
- the single observed select token resolves in ARCHER_META_VALUE

Interpretation: `WORKFLOW_JOB_STATUS` should use the existing `archer-select`
transform, matching the already-approved `WORKFLOW_STATUS` pattern.

## Mapping decision state
Resolved:
- WORKFLOW_JOB_STATUS: change `direct` -> `archer-select`
- RISK_ACCEPTANCE_RBDS: current `direct` transform is invalid; treat as an Archer
  reference. Final representation will preserve the owner's earlier result-property
  decision only if the reference can be represented without losing cardinality.

Still unresolved:
- RISK_ASSESSMENT_REPORT: final transform/path requires Archer field metadata.

## No-write status
This checkpoint records read-only notebook evidence. Cells 4-7 remain paused.
No DIM/FACT DML is established by this check.

## Next action
Run:
`sql/validation/2026-09-21_source_one_ar_remaining_reference_metadata.sql`

Use the returned ARCHER_META_FIELD metadata to classify
`RISK_ASSESSMENT_REPORT` before making one final bulk CSV correction for the
three fields.
