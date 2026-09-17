# Source 2 sources_source Assessment Results — all 10 fields represented — 2026-09-17

## Repository version

Branch: `simplify-metadata-boundary`
Repository version after the runtime mapping update: `f6b4744723cdeddf346cb67b3006cdabdc78e081`.

## Owner-run PREVIEW evidence

Owner-provided Snowflake notebook screenshots on 2026-09-17 show the Assessment Results PREVIEW completed successfully after the first deduplicated additions:

- Source One: 2,813 source records; 90,016 nodes; 87,203 edges; 0 inserts / 0 updates; PREVIEW_PASSED_NO_TARGET_DML.
- Source Two sources_source: 148 source records; 444 nodes; 296 edges; 0 inserts / 0 updates; 444 DIM unchanged / 296 FACT unchanged; PREVIEW_PASSED_NO_TARGET_DML.
- writes_executed=false; commit_attempted=false.

The unchanged Source Two counts are expected because the newly activated `PCT_OF_NONCOMPLIANT_CONTROLS` and `FINDINGS` mappings are empty in the current snapshot, while `_OF_NONCOMPLIANT_CONTROLS` is explicitly excluded as the duplicate/truncated alias of the canonical noncompliant-count field.

## Full Assessment Results field coverage in Mapping/sources_source_runtime.csv

All 10 workbook Assessment Results fields are now represented in the executable/runtime mapping artifact so none are silently missing:

1. COMPLIANCE_RATING — mapped target recorded; runtime guarded pending reviewed-control identity.
2. COUNT_OF_NONCOMPLIANT_CONTROLS — APPROVED and already committed/read-back verified.
3. PCT_OF_NONCOMPLIANT_CONTROLS — APPROVED; current source empty.
4. _OF_NONCOMPLIANT_CONTROLS — EXCLUDED duplicate alias; canonical owner is COUNT_OF_NONCOMPLIANT_CONTROLS.
5. FINDINGS — APPROVED to assessment-results.results[].findings[]; current source empty.
6. FINDINGS_AUTHORITATIVE_SOURCES — mapped target recorded; runtime guarded pending finding/observation identity.
7. CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT — mapped target recorded; runtime guarded pending finding parent identity.
8. DEVIATIONS_AUTHORITATIVE_SOURCES — mapped target recorded; runtime guarded pending finding parent identity.
9. DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS — mapped target recorded; live source populated but runtime guarded pending explicit finding/observation/control identity relationship.
10. EVIDENCE_REPOSITORY — mapped target recorded; runtime guarded pending observation parent and URI-reference evidence value.

`DEFERRED` in the runtime CSV is being used only as a loader guard for rows whose target mapping is already defined but whose stable parent/relationship identity is not yet executable. It does not mean the field is omitted from the mapping contract.

## Duplicate-safety decision

`_OF_NONCOMPLIANT_CONTROLS` must never execute and must never create a second `noncompliant-count` property. The canonical executable mapping is `COUNT_OF_NONCOMPLIANT_CONTROLS` only.

## Next action

Stay on Assessment Results. Resolve the two currently populated guarded rows first: `COMPLIANCE_RATING` and `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`. Do not move to another OSCAL model until the Assessment Results scope is closed.
