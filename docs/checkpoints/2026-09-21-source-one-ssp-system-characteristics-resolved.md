# Source One SSP System Characteristics remaining rows resolved — 2026-09-21

## Owner-provided live evidence

### AUTHORIZATION_DECISION
Current Source One payload:
- 505 null
- 2,308 populated OBJECT values
- object shape: OtherText,ValuesListIds
- select cardinality: exactly one
- all select IDs resolved

Resolved labels:
- ATO = 2,087
- ATO with Conditions = 3
- Awaiting Decision = 217
- IATO = 1

Archer metadata relevant to Source One:
- FIELD_TYPE_ID = 4
- LEVEL_ID = 353
- MODULE_ID = 547
- SELECT_ID = 3816

Comparison:
`OPERATIONAL_STATUS` is already the approved owner of
`system-security-plan.system-characteristics.status.state` and carries a
different lifecycle vocabulary (Operational, Decommissioned, Under Development,
Reauthorize).

Decision:
- Do not map AUTHORIZATION_DECISION to the same singleton status.state.
- Preserve the authorization outcome as an SSP system-characteristics extension
  property:
  `system-security-plan.system-characteristics.props[]`
- transform: `archer-select`
- generic property name: `authorization-decision`

### FULL_CONTROL_ASSESSMENT_HELPER
Current Source One payload:
- 6 null
- 2,807 populated OBJECT values
- object shape: OtherText,ValuesListIds
- select cardinality: exactly one
- Yes = 1,996
- No = 811
- all select IDs resolved

Archer metadata:
- FIELD_TYPE_ID = 4
- LEVEL_ID = 353
- MODULE_ID = 547
- SELECT_ID = 509

Decision:
- EXCLUDE from runtime mapping.
- The historical proposed target
  `security-impact-level.security-objective-confidentiality` is incompatible
  with the observed Yes/No helper semantics.
- Do not convert a helper/calculated flag into a FIPS confidentiality objective.

## Repository change
Mapping/ARCHER_OSCAL_MAPPINGS.csv updated in commit:
`15e61a03d0966f8043e9d762b74e2e035fa2386f`

## Result
There are no longer any DEFERRED rows in the SSP System Characteristics section.
This does not change the separate remaining SSP Metadata exception
`ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER`, nor the larger
Control Implementation backlog.

## Status distinction
- GitHub mapping metadata: updated.
- Snowflake compile/preview for this correction: pending.
- No target DML performed by this checkpoint.

## Next action
Replace the notebook-visible ARCHER_OSCAL_MAPPINGS.csv with the current GitHub
version, rerun Cells 1-3 with SSP selected, and run root RUN_NOW.py. If compile
verification passes, rerun Cells 4-7 in PREVIEW.
