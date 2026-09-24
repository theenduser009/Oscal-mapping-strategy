# Control Implementation fast batch: 7 additional fields mapped — 2026-09-24

## Evidence basis
Owner ran sql/validation/2026-09-24_control_implementation_remaining21_shape_profile.sql and supplied the result screenshots.

The query returned 9 populated fields, all from AUTHORIZATION_PACKAGE; no remaining-field rows were returned for LEVEL355_ALLOCATED_CONTROL.

Observed populated Authorization Package fields:
- ALLOCATED_CONTROLS: 2,528 populated ARRAY rows; 2,528 ContentId-shaped.
- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS: 5 populated ARRAY rows; no recognized ContentId/UserList/GroupList/ValueList shape in the aggregate profile.
- ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA: 1,675 populated OBJECT rows; 1,675 UserList/GroupList-shaped.
- ARCHIVED_CONTROLS: 6 populated ARRAY rows; 6 ContentId-shaped.
- EXPORT_CONTROL_ASSESSOR_ECA_TEXT: 816 populated text rows; 39 distinct text values.
- GS_LAB_CONTROL_ENTITY: 225 populated ARRAY rows; 225 ContentId-shaped.
- INHERITABLE_CONTROLS: 44 populated ARRAY rows; no recognized ContentId/UserList/GroupList/ValueList shape in the aggregate profile.
- SECURITY_CONTROL_ASSESSOR_SCA: 2,799 populated OBJECT rows; 2,799 UserList/GroupList-shaped.
- SECURITY_CONTROL_ASSESSOR_SCA_TEXT: 966 populated text rows; 41 distinct text values.

The remaining 12 deferred fields produced no populated rows in either profiled source dataset for this snapshot.

## Mapping change
Repository: theenduser009/Oscal-mapping-strategy
Branch: simplify-metadata-boundary
Mapping commit: 51a940e3f19aa23c3323f9fceab682ea644329b1
Mapping blob after change: 766f56d90b1f21c1f59e532fa3dc6225f3e91079

Seven low-complexity fields were promoted from DEFERRED to APPROVED using existing seven-cell behavior only. No mapper code or registry change was added.

### Responsible-party reuse
- SECURITY_CONTROL_ASSESSOR_SCA -> system-security-plan.metadata.responsible-parties[]
  role-id: security-control-assessor
- ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA -> system-security-plan.metadata.responsible-parties[]
  role-id: alternate-security-control-assessor

Both reuse the existing generic UserList/GroupList responsible-party framework.

### Package-level extension properties
- EXPORT_CONTROL_ASSESSOR_ECA_TEXT -> system-security-plan.system-characteristics.props[] using text
- SECURITY_CONTROL_ASSESSOR_SCA_TEXT -> system-security-plan.system-characteristics.props[] using text
- ALLOCATED_CONTROLS -> system-security-plan.system-characteristics.props[] using reference-ids
- ARCHIVED_CONTROLS -> system-security-plan.system-characteristics.props[] using reference-ids
- GS_LAB_CONTROL_ENTITY -> system-security-plan.system-characteristics.props[] using reference-ids

The reference-id properties preserve source ContentIds only. They do not claim target-entity hydration or define Level-355 child identity.

## Intentionally not mapped in this batch
- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS
- INHERITABLE_CONTROLS

Their top-level source shape is ARRAY but the aggregate profile did not establish a safe reusable element representation. They remain DEFERRED rather than introducing a new parser or guessing their contents.

The 12 remaining fields with no current populated values also remain DEFERRED; no values are invented.

## Status after metadata change
Control Implementation mapping rows:
- APPROVED: 20
- EXCLUDED: 10
- DEFERRED: 14

Of the 20 approved rows, the previously verified Level-355 control-detail mappings CONTROL_NUMBER and IMPLEMENTATION_DETAILS remain unchanged.

## Validation actually performed
- Current branch and full mapping CSV read before modification.
- Existing generic responsible-party and property/reference-id operators inspected.
- CSV width and exact row presence checked.
- Exactly 7 planned rows changed from DEFERRED to APPROVED.
- Post-edit Control Implementation status counts checked: 20 / 10 / 14.
- No Snowflake execution has been performed for these seven new mappings yet.

## Next action
Refresh the latest mapping CSV in the notebook, then run Cell 2 -> Cell 3 -> Cell 7 with OSCAL_LOAD_MODE="PREVIEW".

Do not rerun cleanup, RUN_NOW.py, COMMIT_NOW.py, or change the seven-cell architecture.
