# Source selector reverted; preserve universal model-driven routing

Date: September 30, 2026
Status: The explicit SELECTED_SOURCE_KEYS change introduced earlier today has been reverted after owner review. This checkpoint supersedes docs/checkpoints/2026-09-30-source-one-assessment-results-route-isolated.md as the current routing decision.

## Owner decision

Do not add another source selector merely to bypass a failing Source Two route.

The seven-cell mapper is intended to remain universal and model-driven:
- SELECTED_MODELS chooses the OSCAL model(s);
- every configured source bound to those model(s) is routed through the same engine.

For SSP, only Source One is bound to SSP, so selecting SSP naturally executes only Source One.

For ASSESSMENT_RESULTS, both Source One and source-two-source are configured. Therefore selecting ASSESSMENT_RESULTS intentionally exercises both routes. A Source Two failure should be diagnosed rather than hidden by a source-selection switch.

## Revert

Maintained Cell 1 restored to the pre-selector universal routing behavior:
- commit c35cc1ac20711cfbc1f87296365defddcb7ee725
- blob 01b10f9ab20a88c227696992f7403aef1770af77

Generated mirrors resynchronized:
- cells_v2 Cell 1 commit 23299f827ef5d26385309e8b4f66e1ae750b56e3
- monolithic notebook commit fb7247d4fad7589f24366534b4d0934dde445ed5
- monolithic blob 8e660c82849ac627e732a70f8e2072385352ccaf

The temporary source-selector lean test was removed.

## Current Assessment Results evidence

Owner-posted Cell 7 output already proves:
- source-one / ASSESSMENT_RESULTS PREVIEW passed;
- 109,630 nodes;
- 106,817 edges;
- 2,813 source records;
- zero DIM inserts/updates;
- zero FACT inserts/updates;
- PREVIEW_PASSED_NO_TARGET_DML.

The overall pipeline then failed on:
- source-two-source / ASSESSMENT_RESULTS
- error_type = ValueError

The exact ValueError message was not visible in the owner screenshot and is still the missing fact.

## Next action

Keep SELECTED_MODELS = ("ASSESSMENT_RESULTS",).

Use the universal seven-cell flow and capture the exact Source Two ValueError from the current Cell 7 report/error output. Fix that specific Source Two issue without changing Source One's already-passing Assessment Results route.
