# Cell 7 + Cell 8 Output Checkpoint

Captured from Snowflake notebook `NB_ARCHER_OSCAL_MAPPER_V2` on 2026-09-09.

## Cell 7 — OSCAL mapping run

### Latest run

- Model: SSP
- Run ID: `20260909T175146Z`
- Graph nodes: **48,957**
- Graph edges: **46,144**
- Duplicate node keys: **0**
- Duplicate edge keys: **0**
- Dangling source edges: **0**
- Dangling target edges: **0**
- Pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`
- No DIM/FACT changes were made
- Writes: **False**

### Prior recorded run

- Run ID: `20260909T162019Z`
- Graph nodes: **51,500**
- Graph edges: **48,687**
- Duplicate node keys: **0**
- Duplicate edge keys: **0**
- Dangling source edges: **0**
- Dangling target edges: **0**
- Pre-write validation: **PASSED**
- Writes: **False**

The node/edge count changed between read-only runs, so this delta must remain visible and should be explained before writes are enabled.

## Cell 8 — `metadata.last-modified` readiness audit

Target OSCAL path: `system-security-plan.metadata.last-modified`

- Loaded mapping artifact rows: **608**
- Candidate mappings found: **2**
- Expected two-candidate contract matched: **True**
- Candidate order is approved precedence: **False**
- Source records: **2,813**
- Source identities unique and metadata-reconciled: **True**
- Generated metadata nodes: **2,813**
- Candidate A populated records: **0**
- Candidate B populated records: **2,813**
- Candidate B parseable but timezone-naive: **2,813**
- Generated `last-modified` populated: **2,813**
- Generated strict RFC3339 + timezone: **0**
- Generated canonical UTC Z: **0**
- Generated parseable but timezone-naive: **2,813**
- Source timezone setting present: **False**
- Named timestamp transform helper present: **False**
- Timezone decision required: **True**
- Existing output normalization required: **True**
- Diagnostic performed writes: **False**
- Whole-SSP conformance established: **False**

**RESULT: DECISION REQUIRED**

Do not invent a timezone, choose a latest timestamp implicitly, or enable writes until timezone/normalization policy is approved.

## Metadata `oscal-version` read-only validation

- Source rows: **2,813**
- Unique source records: **2,813**
- Graph source records: **2,813**
- Metadata nodes: **2,813**
- Missing metadata nodes: **0**
- Orphan metadata nodes: **0**
- Duplicate metadata nodes: **0**
- Non-singleton metadata nodes: **0**
- Malformed metadata payloads: **0**
- Missing `oscal-version` fields: **0**
- Non-string `oscal-version` fields: **0**
- Blank `oscal-version` fields: **0**
- Wrong `oscal-version` fields: **0**
- Valid `oscal-version` fields: **2,813**
- Validation performed writes: **False**
- **RESULT: PASSED**

## Metadata `document-id` read-only validation

- Document-id mapping rows: **1**
- Mapping contract valid: **True**
- Source rows: **2,813**
- Unique source records: **2,813**
- Blank source record IDs: **0**
- Duplicate source record IDs: **0**
- Source parse errors: **0**
- Populated `TRACKING_ID` values: **2,813**
- Absent `TRACKING_ID` values: **0**
- Invalid `TRACKING_ID` values: **0**
- Graph source records: **2,813**
- Blank graph source record IDs: **0**
- Missing graph records: **0**
- Orphan graph records: **0**
- Expected document-id nodes: **2,813**
- Generated document-id nodes: **2,813**
- Missing document-id nodes: **0**
- Unexpected document-id nodes: **0**
- Duplicate document-id nodes: **0**
- Non-singleton document-id nodes: **0**
- Malformed document-id payloads: **0**
- Unexpected payload shapes: **0**
- Missing identifiers: **0**
- Non-string identifiers: **0**
- Blank identifiers: **0**
- Identifier value mismatches: **0**
- Exact identifier matches: **2,813**
- Validation performed writes: **False**
- **RESULT: PASSED**

This confirms the `TRACKING_ID` → OSCAL metadata document-id mapping is complete and exact for all 2,813 SSP source records, with zero duplicate/orphan/malformed/mismatch findings and no writes performed.

## Registry inspection — `metadata.responsible-parties[]`

Snowflake inspection confirms the current registry table schema contains nine columns:

`OSCAL_MODEL_KEY`, `NODE_PATH`, `ELEMENT_TYPE`, `PARENT_NODE_PATH`, `IS_COLLECTION`, `INSTANCE_KEY_RULE`, `PROCESS_ORDER`, `IS_ACTIVE`, `ITEM_PATH`.

Current SSP registry row observed for `system-security-plan.metadata.responsible-parties[]`:

- `OSCAL_MODEL_KEY`: **SSP**
- `NODE_PATH`: `system-security-plan.metadata.responsible-parties[]`
- `ELEMENT_TYPE`: `responsible-parties`
- `PARENT_NODE_PATH`: `system-security-plan.metadata`
- `IS_COLLECTION`: **TRUE**
- `INSTANCE_KEY_RULE`: `SOURCE_FIELD_NAME+ID`
- `PROCESS_ORDER`: **3**
- `IS_ACTIVE`: **TRUE**
- `ITEM_PATH`: `UserList[]`

This is a metadata checkpoint only; no registry mutation was performed from this capture.