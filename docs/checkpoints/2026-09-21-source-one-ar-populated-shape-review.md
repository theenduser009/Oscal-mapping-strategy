# Source One Assessment Results populated-shape review — 2026-09-21

## Repository basis
- Branch before targeted follow-up: `f3d3909eecb24c3488aafaa099e1e386512718f9`
- Targeted reference/select diagnostic added in commit:
  `55ff8174241f8646a4b3b4d9c60f570dccd49cda`

## Owner-provided live read-only evidence
The owner ran `2026-09-21_source_one_ar_populated_shape_check.py` in the
Snowflake notebook after Cells 1-3.

Nine of the twelve newly approved Source One Assessment Results mappings were
shape-compatible with their selected transforms. Three require correction before
Cells 4-7 are rerun.

### Compatible
- AVG_SECURITY_COMPLIANCE_REPORTING_SCORE — scalar-score; 13 null / 2,800 number
- AVG_SECURITY_COMPLIANCE_SCORE — scalar-score; 13 null / 2,800 number
- TOTAL_PACKAGE_INHERENT_RISK — scalar-score; 1 null / 2,812 number
- WORKFLOW_CURRENT_NODE — direct; 2,211 null / 602 string
- WORKFLOW_PROCESS_VERSION — direct; 2,198 null / 615 number
- WORKFLOW_STATUS — archer-select; 2,813 objects with OtherText/ValuesListIds and one select value each
- DUE_DATE — date; all 2,813 null
- WORKFLOW_CURRENT_NODE_HRTN — direct; 2,226 null / 587 string
- WORKFLOW_STATUS_CHANGED — date; 2,813 strings accepted by the date-shape validator

### Requires correction
1. `RISK_ACCEPTANCE_RBDS`
   - current mapping: direct -> results[].props[]
   - live shape: 2,812 null; 1 populated ARRAY containing one OBJECT
   - direct scalar property representation is not valid for the populated record.

2. `RISK_ASSESSMENT_REPORT`
   - current mapping: direct -> results[].props[]
   - live shape: 2,497 null; 316 populated ARRAYs of NUMBER
   - 217 arrays contain one number; 99 arrays contain multiple numbers.
   - the current SOURCE_FIELD_NAME property identity cannot safely represent all
     multi-valued rows as one direct scalar property.

3. `WORKFLOW_JOB_STATUS`
   - current mapping: direct -> results[].props[]
   - live shape: 2,198 null; 615 populated OBJECTs
   - every populated object has the key signature `OtherText,ValuesListIds`.
   - this matches the Archer select-value structure already handled by
     `WORKFLOW_STATUS`, so direct mapping is not appropriate.

## Status
- This is READ-ONLY Snowflake evidence.
- No DIM/FACT DML was performed.
- Cells 4-7 should remain paused until these three transform decisions are corrected.
- No existing mapping is declared committed/accepted by this shape check alone.

## Next action
Run:
`notebooks/validation/2026-09-21_source_one_ar_reference_select_check.py`

The targeted check prints only aggregate nested key/reference/select evidence for
the three problematic fields and compares numeric tokens to the already-loaded
Archer select-value lookup. Use that evidence to make one bulk CSV correction,
then rerun Cells 1-3 and the full PREVIEW.
