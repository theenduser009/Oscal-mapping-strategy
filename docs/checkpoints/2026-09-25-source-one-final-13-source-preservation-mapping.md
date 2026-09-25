# Source One final 13 deferred-field source-preservation mapping — 2026-09-25

## Owner-provided profile evidence
The owner supplied a Snowflake result for the final 13 non-Profile DEFERRED Source One fields.

All 13 have POPULATED_ROWS = 0 in the current Authorization Package snapshot.

Observed current-source states:
- Explicit JSON null in all 2,813 rows:
  - ADD_ADDITIONAL_CONTROLS
  - ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE
  - ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA_TEXT
  - CHANGE_CONTROL
  - CONTROL_OWNER_CO
  - CONTROL_SET_TO_ASSESS
  - CONTROL_STANDARDS
  - INHERITED_CONTROL_SELECTION
  - MASTER_CONTROLS
- SQL-null-or-missing in all 2,813 rows:
  - ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
  - CURRENT_CONTROL_RISK_THRESHOLD
  - EXPORT_CONTROLLED_DATA_ITARAR_IF_APPLICABLE
  - OF_SATISFIED_CONTROLS

No current arrays, objects, text, number, or boolean populated values were reported for any of these fields.

## Mapping decisions
All 13 rows were promoted from DEFERRED to APPROVED using existing generic property behavior.

### SSP Metadata
ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
-> system-security-plan.metadata.props[]

- transform = direct
- NULL_POLICY = preserve
- VALUE_REQUIRED = false
- missing key remains omitted
- explicit JSON null, if it appears later, is preserved
- no value is fabricated for the currently missing key

A registry row for system-security-plan.metadata.props[] was added via:
sql/registry/ENABLE_SSP_METADATA_PROPS.sql

Registry contract:
- model SSP
- parent system-security-plan.metadata
- collection true
- instance identity SOURCE_FIELD_NAME
- item path $
- operator properties
- UUID policy omit

### SSP Control Implementation
The remaining 12 fields map to:
system-security-plan.system-characteristics.props[]

with:
- transform = direct
- NULL_POLICY = preserve
- VALUE_REQUIRED = false

This is explicitly source-preservation only. It does not assert native OSCAL relationship semantics for CONTROL_STANDARDS, MASTER_CONTROLS, CONTROL_OWNER_CO, or any other future populated value.

Current fail-safe behavior is retained:
- explicit JSON null emits a null-valued property;
- an absent key emits nothing;
- a future incompatible populated object shape fails rather than being silently coerced.

## Mapping status after update
Source One mapping rows:
- APPROVED: 139
- EXCLUDED: 13
- BLOCKED_IF_POPULATED: 1
- DEFERRED: 2

The only remaining DEFERRED rows are Profile:
- ADD_OVERLAY
- BASELINE_RECOMMENDATION

Profile is not part of the four Source One executable runtime routes.

## Repository
- Mapping commit: fe5111c03c9772a21bc228b001403031fbd5b848
- SSP metadata props registry commit: feff9a2098b85586f3d42be5f720539398283f31
- Current branch head before this checkpoint: feff9a2098b85586f3d42be5f720539398283f31

## Validation actually performed
- Full current mapping CSV read before modification.
- Exactly 13 intended Source One rows changed from DEFERRED to APPROVED.
- Post-edit status counts checked.
- No notebook runtime code changed.
- New registry SQL is metadata-only and guarded/idempotent.
- No live Snowflake registry execution, PREVIEW, or COMMIT has yet been performed for this 13-field batch.

## Next action
1. Run sql/registry/ENABLE_SSP_METADATA_PROPS.sql once.
2. Refresh the latest mapping CSV.
3. Run Cell 2 -> Cell 3 -> Cell 7 with SELECTED_MODELS=("SSP",) and OSCAL_LOAD_MODE="PREVIEW".
4. If PREVIEW reconciles, COMMIT and capture read-back verification.

Expected qualitative effect:
- nine explicit-JSON-null Control Implementation fields each emit one null-valued system-characteristics property per Source One record;
- four missing fields emit no property in the current snapshot;
- no new Python transformations or lookups are introduced.
