# Resume Source One mapping after QA detour — 2026-09-22

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before this resume helper: `88918c028707b08151cf61c0f8a10fa8a8e804ee`

## Where mapping paused
Core SSP Control Implementation is explicitly source-blocked on the missing
`ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW` dataset for Level-355 CONTROL
records. Do not substitute package-level summary/helper fields for
`implemented-requirements[]`.

Outside that blocked area, the current Source One DEFERRED remainder is:
- SSP Metadata: ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER
- Assessment Results: FINDINGS
- Assessment Results: RISK_ASSESSMENT_REPORT
- Profile: ADD_OVERLAY
- Profile: BASELINE_RECOMMENDATION

The accepted design direction for FINDINGS is
`assessment-results.results[].findings[]`. Current reviewed Source One values
were null, so no current finding output is expected.

Profile remains non-runtime in current Cell 1:
- ADD_OVERLAY: null across the reviewed 2,813-record snapshot.
- BASELINE_RECOMMENDATION: populated, but still missing the approved
  baseline/control-set -> OSCAL href + include-all/include-controls crosswalk.

RISK_ASSESSMENT_REPORT remains blocked on the current-runtime attachment/resource
contract. CONFIRMED_IN_ARCHER had no current source value.

## Immediate next action
Root `RUN_NOW.py` now performs a read-only final readiness check for Source One
FINDINGS:
- current value/shape coverage
- ARCHER_META_FIELD type/level/module metadata
- live Assessment Results finding-branch registry rows

If the field is confirmed as Archer Cross-Reference and the branch is active,
the next material change is to promote FINDINGS using the existing generic
reference-id/finding-branch pattern. No new per-field Python branch should be
added.

## Validation status
This checkpoint records the resume decision only. The new FINDINGS helper has not
yet been executed in Snowflake by this chat.
