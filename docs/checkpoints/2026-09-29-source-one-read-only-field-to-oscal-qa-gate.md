# Source One read-only field-to-OSCAL QA gate published

Date: September 29, 2026
Status: Generic read-only QA notebook helper committed and repository read-back verified. No Snowflake execution has occurred for this QA helper yet.

## Repository basis

Branch:
- simplify-metadata-boundary

Head before QA publication:
- f9cc22328be91110020bb8db54b405fed4daa61c

Current runtime mapping CSV:
- Mapping/ARCHER_OSCAL_MAPPINGS.csv
- blob e00466381404571bcf0d570ad44992801946d248
- 155 runtime rows in the current artifact.

## QA helper

Path:
- notebooks/validation/14_source_one_mapping_qa.py

Publication / hardening commits:
- 53cd227b809449f685d28538333add2e662a1e53
- 48e89a109bee9a480e88f52fb19156817bb69664
- 2a4e102e975dd4919072a06f5d4b2e0518e01296
- 27dce9f1b4079958b729d96ec8f6cfb5f071fdb6

Current read-back blob:
- 5b14c6d9b9ab46c3f41a40fc9e569a1a797e41d5

## What the helper validates

For the currently selected Source One model route(s), after an accepted Cell 7 PREVIEW or COMMIT/verification:

1. Reviews every active runtime mapping row.
2. Counts source presence, populated source values and explicit nulls.
3. Requires mapping-specific target evidence:
   - exact property name for props[];
   - exact observation/source-field identity for observations[];
   - exact target member for object/record/joined-record mappings;
   - exact role/source-field identity for responsible-party assignments;
   - exact referenced instance identity for reference collections.
   Finding only a shared props/observations container is not accepted as evidence.
4. Separates:
   - populated source -> target evidence present;
   - populated source -> target empty;
   - no populated source data.
5. Resolves Archer Dev FIELD_ID and FIELD_TYPE_ID from ARCHER_META_FIELD using source-table RequestedObject.LevelId context.
   - one candidate = RESOLVED;
   - zero = NOT_FOUND;
   - multiple = AMBIGUOUS.
   The helper never silently picks an ambiguous Field ID.
6. Flags Archer FIELD_TYPE_ID 9 and 23 as relationship/reference exceptions rather than forcing scalar equality.
7. Produces a full disposition inventory for DEFERRED, EXCLUDED, BLOCKED_IF_POPULATED and blank/TBD target paths.
8. Uses a deterministic 15-Content-ID sample cohort for source-to-target value checks on non-relationship mappings.

## Outputs

- QA_SUMMARY
- QA_COVERAGE_DF
- QA_ATTENTION_DF
- QA_DISPOSITION_DF
- QA_SAMPLE_DF

## Evidence boundary

Repository read-back was performed after the final Snowpark argument hardening.

No Snowflake execution, source read, target query, QA result, mapping change, Field ID CSV write, DML or COMMIT has been performed by ChatGPT for this helper.

The helper uses the Cell 7 runtime context and canonical graph that the guarded loader has already verified against the persisted target. This avoids treating an unverified in-memory graph as proof of target state.

## Immediate next action

Run notebooks/validation/14_source_one_mapping_qa.py in the current SSP notebook session first.

Return:
- SOURCE_ONE_QA_SUMMARY;
- SOURCE_ONE_QA_ATTENTION;
- SOURCE_ONE_QA_SAMPLE_VALUE_CHECKS.

Do not change mappings from the QA output until each exception is classified.
