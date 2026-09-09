# SSP Metadata `last-modified` Readiness Audit — 2026-09-09

Source: user-provided Snowflake read-only audit screenshots. Aggregate evidence only; no source record IDs or payload values are included.

## Target

- OSCAL path: `system-security-plan.metadata.last-modified`
- Loaded mapping artifact rows: **608**
- Candidate mappings found: **2**
- Expected two-candidate contract matched: **True**
- Candidate order is approved precedence: **False**
- Source records: **2813**
- Source identities unique and metadata-reconciled: **True**
- Generated metadata nodes: **2813**

## Candidate A

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

## Candidate B

- Mapping rows: **1**
- Populated records: **2813**
- Strict RFC3339 + timezone: **0**
- Parseable timezone-aware: **0**
- Parseable but timezone-naive: **2813**
- Date-only: **0**
- Non-scalar: **0**
- High precision requiring explicit support: **0**
- Non-timestamp scalar: **0**
- Unrecognized: **0**

## Candidate overlap

- Neither candidate: **0**
- Only Candidate A: **0**
- Only Candidate B: **2813**
- Both candidates: **0**
- Both candidates raw-equal: **0**
- Both candidates raw-different: **0**
- Both candidates normalized-equal: **0**
- Both candidates normalized-different: **0**
- Candidate A later: **0**
- Candidate B later: **0**
- Normalized comparison blocked: **0**
- Raw-different and comparison blocked: **0**

## Generated `last-modified` output

- Populated: **2813**
- Missing: **0**
- Strict RFC3339 + timezone: **0**
- Canonical UTC `Z`: **0**
- Parseable but timezone-naive: **2813**
- Date-only: **0**
- Non-scalar: **0**
- High precision requiring explicit support: **0**
- Non-timestamp scalar: **0**
- Unrecognized: **0**
- Generated raw match Candidate A only: **0**
- Generated raw match Candidate B only: **2813**
- Generated raw match both: **0**
- Generated raw match neither: **0**
- Generated normalized match both: **0**
- Generated normalized match Candidate A only: **0**
- Generated normalized match Candidate B only: **0**
- Generated normalized match neither: **0**

## Configuration / policy readiness

- Source precedence setting present: **False**
- Source precedence setting valid: **False**
- Source precedence setting invalid: **False**
- Source timezone setting present: **False**
- Source timezone setting valid: **False**
- Source timezone setting invalid: **False**
- Named timestamp transform helper present: **False**
- Precedence decision required: **False**
- Comparison/format policy required: **False**
- Timezone decision required: **True**
- Source format review required: **False**
- Source completeness required: **False**
- Existing output normalization required: **True**
- Diagnostic performed writes: **False**
- Whole-SSP conformance established: **False**

## Decision

**RESULT: DECISION REQUIRED**

The current generated `last-modified` values are fully populated, but all **2813** are timezone-naive. The generated output exactly follows Candidate B in raw form. The next decision is therefore not candidate precedence; it is an explicit timezone/normalization policy.

Do **not** choose mapping order, latest timestamp, or a timezone implicitly. Define the approved source timezone and normalization behavior first, then implement a named transform that emits OSCAL-compliant RFC3339 timestamps with timezone/UTC normalization.

Keep `EXECUTE_WRITES = False` until that policy is approved and validated.
