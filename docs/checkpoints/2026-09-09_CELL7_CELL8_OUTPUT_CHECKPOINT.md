# Cell 7 + Cell 8 Output Checkpoint

Captured from Snowflake notebook `NB_ARCHER_OSCAL_MAPPER_V2` on 2026-09-09.

## Cell 7 — OSCAL mapping run

- Model: SSP
- Run ID: `20260909T162019Z`
- Graph nodes: **51,500**
- Graph edges: **48,687**
- Duplicate node keys: **0**
- Duplicate edge keys: **0**
- Dangling source edges: **0**
- Dangling target edges: **0**
- Pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`
- No DIM/FACT changes were made
- Writes: **False**

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

Latest screenshot result:

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

This confirms one valid metadata node per source record and valid `oscal-version` coverage across all 2,813 records, with no duplicate/orphan/malformed metadata findings and no writes performed.
