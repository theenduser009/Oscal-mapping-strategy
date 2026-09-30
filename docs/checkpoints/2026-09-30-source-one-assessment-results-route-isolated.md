# Source One Assessment Results PREVIEW passed; Source Two route caused aggregate failure

Date: September 30, 2026
Status: Owner-posted Cell 7 report reviewed. Source One Assessment Results itself passed zero-delta PREVIEW. The overall pipeline failed only when it advanced to a second Assessment Results route bound to Source Two. Explicit source selection has now been added to Cell 1. No target DML was performed by the failed run.

## Owner-posted evidence

First route:
- source = source-one
- model = ASSESSMENT_RESULTS
- mode = PREVIEW
- pre_write_validation_passed = true
- nodes = 109,630
- edges = 106,817
- source_records = 2,813
- validation_passed = true
- storage_verified = true
- DIM inserts = 0
- DIM updates = 0
- DIM unchanged = 109,630
- FACT inserts = 0
- FACT updates = 0
- FACT unchanged = 106,817
- route status = PREVIEW_PASSED_NO_TARGET_DML

Aggregate failure:
- status = FAILED_BEFORE_COMMIT
- writes_executed = false
- commit_attempted = false
- failed_route = source-two-source / ASSESSMENT_RESULTS
- error_type = ValueError

The screenshot does not show the exact ValueError text for the Source Two route, so no root cause is asserted for Source Two here.

## Root routing issue for Source One QA

Cell 1 bound ASSESSMENT_RESULTS to both:
- source-one
- source-two-source

Selecting only the model therefore ran both sources. That is inappropriate for source-isolated QA because the second route can fail even after the Source One route passes.

## Implemented fix

Maintained Cell 1 now exposes:
- SELECTED_SOURCE_KEYS
- SELECTED_MODELS

Current default source selection:
- SELECTED_SOURCE_KEYS = ("source-one",)

Implementation:
- notebooks/cells/01_initialization_and_configuration.py
- commit 430be53b381e76d6fc47020a0e79deab1126cecb
- blob d3d7ad4b5363abd7ed7194d92bbdfbb6276deda5

Generated mirrors synchronized:
- cells_v2 Cell 1 commit 80f801ff42e7409b83b27895ad2407e58a631d70
- monolithic notebook commit f052070eb3c2101e7a7630bceeed2e106a9f0dbf
- monolithic blob c68ba603640755e7ba8502eafbfe519586b13c92

Focused route-selection tests added:
- tests/lean/test_source_route_selection.py
- commit 845a1d8e8b37fb27b3e337071e3a9f8f24b852fb

## Immediate next action

For Source One Assessment Results QA:
- SELECTED_SOURCE_KEYS = ("source-one",)
- SELECTED_MODELS = ("ASSESSMENT_RESULTS",)
- Cell 7 remains PREVIEW

Run Cells 1 through 7, then run:
- notebooks/validation/14_source_one_mapping_qa.py

Do not debug the Source Two Assessment Results route as part of the Source One completion gate. Track it separately when Source Two work resumes.
