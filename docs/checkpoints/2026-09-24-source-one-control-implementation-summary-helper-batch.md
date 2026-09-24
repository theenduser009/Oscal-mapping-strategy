# Source One SSP Control Implementation summary/helper batch — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this batch: `d6abe9bf4037556ad8e4638ec04f7c726d8cc8f6`

## Scope and decision
This batch intentionally does **not** claim the missing per-control
`implemented-requirements[]` branch is complete. That core branch remains blocked
on the missing current Level-355 control dataset expected as
`ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`.

The owner previously chose properties for package-level count/summary values. The
current mapping metadata therefore resolves unambiguous package summaries without
pretending they are individual control implementations.

## Approved package-level SSP properties
The following 11 mapping rows are now APPROVED to:
`system-security-plan.system-characteristics.props[]`

Direct numeric summaries:
- COUNT_OF_CONTROLS -> count-of-controls
- COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS -> count-of-controls-without-implementation-details
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS_ANDOR_RBDS -> count-of-controls-with-open-poams-and-or-rbds
- NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS -> number-of-controls-being-inherited-by-others
- COUNT_OF_FULLY_IMPLEMENTED_CONTROLS -> count-of-fully-implemented-controls
- COUNT_OF_CONTROLS_WITH_OPEN_POAMS -> count-of-controls-with-open-poams
- COUNT_OF_CONTROLS_MISSING_POAMRBD -> count-of-controls-missing-poam-rbd
- COUNT_OF_INHERITED_CONTROLS -> count-of-inherited-controls
- COUNT_OF_ACTUAL_CONTROLS_IMPLEMENTED -> count-of-actual-controls-implemented

Archer select-value summaries:
- CONTROL_SET_VERSION_NUMBER -> control-set-version-number
- CONTROL_SET_VERSION_NUMBER_HRC -> control-set-version-number-hrc

These use existing generic `direct` / `archer-select` transforms and the
already-registered System Characteristics property collection. No new Python
field-specific branch is required.

## Excluded workflow/helper/calculated rows
The following are now EXCLUDED from executable OSCAL content:
- ALLOCATE_BASELINE_CONTROLS
- ARCHIVE_CONTROLS
- LINK_CNSS_CONTROLS_BY_CONFIDENTIALITY_RATING
- LINK_CNSS_CONTROLS_BY_INTEGRITY_RATING
- LINK_CNSS_CONTROLS_BY_AVAILABILITY_RATING
- HELPER_ALLOCATED_CONTROLS (both source occurrences)
- PRECONTROL_ALLOCATION_PROGRESS_VIEW
- HELPER_OTS_CONTROLS
- DATE_CONTINUE_TO_CONTROL_IMPLEMENTATION

These are package workflow/helper/calculated mechanics and are not substitutes for
the actual control-detail branch.

## Findings disposition
Source One FINDINGS already has the accepted OSCAL destination
`assessment-results.results[].findings[]`. Current Source One values are all
effectively empty sentinels, so no finding nodes are fabricated. This is not a
remaining OSCAL-path design question.

## Validation status
- CSV change committed in GitHub.
- No Snowflake compile/PREVIEW has yet been run for this Control Implementation batch.
- No registry change.
- No DIM/FACT DML.

## Next action
Refresh the current mapping CSV in Snowflake and run Source One SSP PREVIEW using
Cells 1, 2, 3 and 7. Reconcile only the new property delta from this batch.
