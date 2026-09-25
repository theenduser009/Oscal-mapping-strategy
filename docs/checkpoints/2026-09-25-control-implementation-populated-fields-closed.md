# Source One Control Implementation populated-field closeout — 2026-09-25

## Repository basis
- Branch: simplify-metadata-boundary
- Starting head before mapping change: 85a828ae11fceeb34656f40fcc213af153d3484c
- Mapping commit: 130fd1cae3e549d2d5a852bc3d8b07832a2c6d3d
- Mapping CSV blob after change: 31503e40725b1efaa9bed4e9d854bcf22b2f1590

## Owner-provided Snowflake evidence
The closeout query for the only two populated deferred Control Implementation arrays returned:

- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS
  - ITEM_TYPE = INTEGER
  - ITEM_COUNT = 26
  - HAS_CONTENT_ID = 0
  - HAS_CONTENT_IDS = 0
  - HAS_ID = 0
  - HAS_USER_LIST = 0
  - HAS_GROUP_LIST = 0
  - HAS_VALUE_LIST_IDS = 0

- INHERITABLE_CONTROLS
  - ITEM_TYPE = INTEGER
  - ITEM_COUNT = 877
  - HAS_CONTENT_ID = 0
  - HAS_CONTENT_IDS = 0
  - HAS_ID = 0
  - HAS_USER_LIST = 0
  - HAS_GROUP_LIST = 0
  - HAS_VALUE_LIST_IDS = 0

The prior one-pass profile established 5 populated arrays for
ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS and 44 populated arrays for
INHERITABLE_CONTROLS. The new result establishes their array-member shape.

## Mapping decision
Both fields are preserved as source-reference extension properties under:

system-security-plan.system-characteristics.props[]

using the existing reference-ids transform.

This is intentionally source-preserving only:
- integer members are retained as string property values by the existing property emitter;
- no ContentId, user, group, value-list, provider UUID, or target entity resolution is inferred;
- no new parser/operator/registry row is added.

## Control Implementation status after change
- APPROVED: 22
- EXCLUDED: 10
- DEFERRED: 12
- Total runtime rows: 44

The 12 remaining deferred Control Implementation rows had no populated values in the 2026-09-24 one-pass current-source profile. They remain explicit no-current-value deferrals rather than fabricated mappings.

## Validation actually performed
- Current GitHub branch and complete mapping CSV inspected before modification.
- Exactly the two intended DEFERRED rows were changed.
- Existing transform/operator support reviewed; no runtime code change required.
- CSV row widths preserved.
- Post-edit Control Implementation counts checked: 22 APPROVED / 10 EXCLUDED / 12 DEFERRED.
- No Snowflake PREVIEW or COMMIT has yet been performed for these two new mappings.

## Next action
Refresh the latest mapping CSV and run Cell 2 -> Cell 3 -> Cell 7 with SSP in PREVIEW.

If clean, proceed to the Source One all-model closeout PREVIEW using:
SSP, ASSESSMENT_RESULTS, POAM, SECURITY_ASSESSMENT_PLAN.

Do not add mappings for the 12 currently empty Control Implementation fields merely to force a numeric completion percentage.
