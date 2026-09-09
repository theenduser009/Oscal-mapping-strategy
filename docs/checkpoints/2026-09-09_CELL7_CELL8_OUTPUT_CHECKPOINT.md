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

Target OSCAL path:

`system-security-plan.metadata.last-modified`

Observed audit state:

- Loaded mapping artifact rows: **608**
- Candidate mappings found: **2**
- Expected two-candidate contract matched: **True**
- Candidate order is approved precedence: **False**
- Source records: **2,813**
- Source identities unique and metadata-reconciled: **True**
- Generated metadata nodes: **2,813**

### Candidate A

- Mapping rows: **1**
- Populated records: **0**
- Strict RFC3339 + timezone: **0**
- Parseable timezone-aware: **0**
- Parseable but timezone-naive: **0**
- Date-only: **0**
- Non-scalar: **0**
- High precision requiring explicit support: **0**
- Non-timestamp scalar: **0**
- Unrecognized: **0**

### Candidate B

- Mapping rows: **1**
- Populated records: **2,813**
- Strict RFC3339 + timezone: **0**
- Parseable timezone-aware: **0**
- Parseable but timezone-naive: **2,813**
- Date-only: **0**
- Non-scalar: **0**
- High precision requiring explicit support: **0**
- Non-timestamp scalar: **0**
- Unrecognized: **0**

### Candidate overlap

- Records with neither candidate: **0**
- Records with only Candidate A: **0**
- Records with only Candidate B: **2,813**
- Records with both candidates: **0**
- Both candidates raw-equal: **0**
- Both candidates raw-different: **0**
- Both candidates normalized-equal: **0**
- Both candidates normalized-different: **0**
- Candidate A later: **0**
- Candidate B later: **0**
- Normalized comparison blocked: **0**
- Raw-different and comparison blocked: **0**

### Generated `last-modified`

- Populated: **2,813**
- Missing: **0**
- Strict RFC3339 + timezone: **0**
- Canonical UTC `Z`: **0**
- Parseable but timezone-naive: **2,813**
- Date-only: **0**
- Non-scalar: **0**
- High precision requiring explicit support: **0**
- Non-timestamp scalar: **0**
- Unrecognized: **0**
- Raw match both: **0**
- Raw match Candidate A only: **0**
- Raw match Candidate B only: **2,813**
- Raw match neither: **0**
- Normalized match both: **0**
- Normalized match Candidate A only: **0**
- Normalized match Candidate B only: **0**
- Normalized match neither: **0**

### Policy/config state

- Source precedence setting present: **False**
- Source precedence setting valid: **False**
- Source precedence setting invalid: **False**
- Source timezone setting present: **False**
- Source timezone setting valid: **False**
- Source timezone setting invalid: **False**
- Named timestamp transform helper present: **False**
- Precedence decision required: **False**
- Comparison/format policy required: **False**
- **Timezone decision required: True**
- Source format review required: **False**
- Source completeness required: **False**
- **Existing output normalization required: True**
- Diagnostic performed writes: **False**
- Whole-SSP conformance established: **False**

## Current decision

**RESULT: DECISION REQUIRED**

The active blocker is not candidate precedence. Candidate B is the only populated source for all 2,813 records. The blocker is that every generated `last-modified` value is timezone-naive, while the repository currently has no approved source-timezone policy and no named timestamp normalization helper.

Do not invent a timezone, do not choose a latest timestamp implicitly, and do not enable writes until the timezone/normalization rule is explicitly approved and implemented.
