# Source One SSP Control Implementation bulk evidence classification — 2026-09-21

## Owner-provided live read-only evidence
The owner ran the bulk profiler across all currently deferred SSP Control
Implementation mappings.

Current runtime CSV scope:
- 42 deferred rows
- 41 unique source field names
- duplicate deferred field name: HELPER_ALLOCATED_CONTROLS

## High-value live findings

### Core control-reference driver
ALLOCATED_CONTROLS:
- 2,528 populated Source One records / 285 null
- ARRAY of OBJECT
- 252,165 referenced objects
- object shape: ContentId,LevelId
- all observed referenced LevelIds = 355
- Archer field type includes Cross-Reference for the current Source One level

This is the strongest current-runtime evidence that the actual SSP control
implementation should be built from referenced Archer Level-355 control records,
rather than from the package-level count/helper fields.

ARCHIVED_CONTROLS also references Level 355, but only six Source One records are
populated and those arrays are large. Treat archived controls separately from the
active implemented-requirement population.

### Derived numeric summary fields
The following are populated numeric summaries and are candidates to be derived
from the eventual implemented-requirement / POA&M graph instead of becoming the
canonical control implementation itself:
- COUNT_OF_CONTROLS
- COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS
- NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS
- COUNT_OF_FULLY_IMPLEMENTED_CONTROLS
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS
- COUNT_OF_CONTROLS_MISSING_POAMRBD
- COUNT_OF_INHERITED_CONTROLS
- COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED

No CSV status change is made by this checkpoint.

### Workflow/helper/calculated signals
Live evidence shows several package-level helper/process fields rather than
native control implementations:
- ALLOCATE_BASELINE_CONTROLS: single select, currently Not Ready for all 2,813
- ARCHIVE_CONTROLS: Archive Controls / Do Not Archive action vocabulary
- HELPER_ALLOCATED_CONTROLS: Yes/No helper; duplicate mapping row exists
- PRECONTROL_ALLOCATION_PROGRESS_VIEW: display/progress text
- LINK_CNSS_CONTROLS_BY_*: currently empty; Archer CAST-field-value metadata
- HELPER_OTS_CONTROLS: currently empty helper values-list field
- CHANGE_CONTROL: currently empty Sub-Form
- DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION: process date

These should not be promoted into implemented-requirements solely because they
appear in the Control Implementation worksheet section.

### Existing-framework candidates
- SECURITY_CONTROL_ASSESSOR_SCA: populated Users/Groups shape, candidate for the
  existing SSP role/party framework.
- ALTERNATE_SECURITY_CONTROL_ASSESSOR_SCA: populated Users/Groups shape, same
  candidate framework.
- CONTROL_OWNER_CO: same Archer Users/Groups field type but current values are null.
- CONTROL_SET_VERSION_NUMBER and CONTROL_SET_VERSION_NUMBER_HRC: populated
  values-list fields; likely package/system extension properties, not individual
  implemented-requirements.

### Other reference/related-record fields
Several fields need target-semantics review after the core Level-355 binding is
resolved, including INHERITABLE_CONTROLS, GS_LAB_CONTROL_ENTITY,
ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS, CONTROL_STANDARDS,
MASTER_CONTROLS, CONTROL_SET_TO_ASSESS and other currently empty reference fields.

## NIST structural direction
The SSP control-implementation branch is control-based: an implemented
requirement describes how the system satisfies an individual control. Therefore
the Level-355 control-record binding must be resolved before package-level
summary/helper fields are used to claim Control Implementation completion.

## Status distinction
- Bulk source/metadata profiling: owner-reported live PASS/read-only.
- Mapping classification: partially established; no bulk CSV status changes yet.
- Level-355 physical/current RAW source binding: still unresolved.
- Control Implementation runtime implementation: not yet established.
- DIM/FACT DML: none from this review.

## Next action
Resolve one current Source One ALLOCATED_CONTROLS Level-355 reference to the
actual current Archer *_RAW table. Do not use historical structured/STG tables.
Then inspect aggregate key/shape coverage for CONTROL_NUMBER, CONTROL_NAME,
IMPLEMENTATION_DETAILS, OVERALL_IMPLEMENTATION_DETAILS, IMPLEMENTATION_STATUS,
CONTROL_PARAMETERS, RESPONSIBLE_ROLE and inheritance fields before designing
implemented-requirements[].
