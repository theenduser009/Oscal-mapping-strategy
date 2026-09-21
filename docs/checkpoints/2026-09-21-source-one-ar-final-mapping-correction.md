# Source One Assessment Results final mapping correction — 2026-09-21

## Repository basis
- Branch before correction: `a72850b5128ddc11873ed73a36b7bae0f450770c`
- Mapping CSV correction commit: `7fa1b44be027086f20fb7488e76873a410ab23a4`

## Live evidence used
The owner supplied Snowflake read-only evidence for the remaining three Source One
Assessment Results fields.

### WORKFLOW_JOB_STATUS
Confirmed:
- Archer `FIELD_TYPE_ID = 4` (Values List)
- `SELECT_ID = 2848`
- 615 populated payloads, all shaped `{OtherText, ValuesListIds}`
- select cardinality = 1
- observed select token resolves in `ARCHER_META_VALUE`

Decision:
- target remains `assessment-results.results[].props[]`
- transform corrected from `direct` to `archer-select`

### RISK_ACCEPTANCE_RBDS
Confirmed:
- Archer `FIELD_TYPE_ID = 9` (Cross-Reference)
- current Source One payload has one populated array containing one
  `{ContentId, LevelId}` object
- not an Archer select container

Decision:
- owner-selected target remains `assessment-results.results[].props[]`
- mapping type corrected to Reference
- transform corrected from `direct` to existing `reference-ids`
- current reference cardinality is one, so the existing SOURCE_FIELD_NAME property
  identity remains valid for the current snapshot
- no historical structured/STG table dependency is introduced

### RISK_ASSESSMENT_REPORT
Confirmed:
- Archer `FIELD_TYPE_ID = 11` (Attachment)
- `LEVEL_ID = 353`, `MODULE_ID = 547`
- current Source One payload contains 316 populated arrays / 742 numeric attachment
  IDs, including multi-valued rows
- historical structured/STG tables expose similarly named columns, but the owner
  explicitly excluded those historical tables from the future OSCAL runtime contract
- no valid current-runtime attachment href/resource identifier has been established

Decision:
- status returned to `DEFERRED`
- no executable transform/runtime target
- do not flatten multiple attachment IDs into a single property
- do not invent a URL/URN
- do not add a runtime dependency on historical structured/STG Archer tables
- revisit only when the current RAW + authoritative metadata contract exposes an
  approved attachment identifier/resource representation

## Net Assessment Results state
Of the 13 rows that were historically deferred at the September 14 handoff:
- 11 are now executable/approved through the September 21 review
- FINDINGS remains separate, with canonical `results[].findings[]` destination but
  Source One current sample null and its Source One reference contract still separate
- RISK_ASSESSMENT_REPORT is a documented attachment exception, deferred for lack of
  a valid current-runtime attachment identifier/resource contract

This is a mapping/code-metadata checkpoint only. It is not a new Snowflake PREVIEW
or COMMIT result.

## Next action
Replace the notebook-visible `ARCHER_OSCAL_MAPPINGS.csv` with the current GitHub
version, rerun Cells 1-3, verify the corrected compiled mapping set, then run Cells
4-7 in PREVIEW only. No DIM/FACT COMMIT is authorized by this checkpoint.
