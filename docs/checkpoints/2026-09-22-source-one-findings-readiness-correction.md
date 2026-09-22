# Source One FINDINGS readiness correction — 2026-09-22

## Supersedes
This checkpoint supersedes the FINDINGS readiness interpretation in:
`docs/checkpoints/2026-09-22-source-one-mapping-resume-findings.md`

## Owner-provided live evidence
The first FINDINGS helper returned:
- SOURCE_RECORDS = 2,813
- POPULATED = 2,813
- SHAPES = STRING for all 2,813
- finding registry branch ready = true
- prior helper reported cross-reference metadata found = true
- prior helper result = SOURCE_ONE_FINDINGS_REFERENCE_MAPPING_READY

## Correction
The prior helper searched every Archer metadata row named FINDINGS and considered
the presence of FIELD_TYPE_ID=9 anywhere as sufficient. That is too broad because
FINDINGS exists on many Archer levels/modules.

The Source One Authorization Package row visible in the owner screenshot is:
- FIELD_ID = 22925
- SQL_FIELD_NAME = FINDINGS
- FIELD_TYPE_ID = 23
- LEVEL_ID = 353
- MODULE_ID = 547
- SELECT_ID = null

Therefore Source One FINDINGS is currently evidenced as a Related Records field,
not as the Cross-Reference field type used by some other Archer modules.

The earlier result `SOURCE_ONE_FINDINGS_REFERENCE_MAPPING_READY` must NOT be used
to promote the mapping.

## Next action
Run the corrected root `RUN_NOW.py`. It:
- restricts metadata to Source One LEVEL_ID=353 / MODULE_ID=547
- classifies the 2,813 string values without printing raw IDs/values
- determines whether the strings are empty sentinels, JSON-encoded collections,
  numeric-reference text, UUID text, or another serialization
- rereads the existing finding registry branch

Only after this serialization contract is understood should FINDINGS move from
DEFERRED to an executable transform.

## Status
- OSCAL destination remains accepted:
  `assessment-results.results[].findings[]`
- registry finding branch is live
- source serialization contract is not yet established
- no mapping CSV change made
- no target DML performed
