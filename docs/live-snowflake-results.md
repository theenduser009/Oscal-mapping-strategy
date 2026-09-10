# Live Snowflake Mapper Results

## 2026-09-10 — Cell 7 failure after component hydration
Run ID: `20260910T181836Z`; Model: `SSP`.
Component hydration: lookup 1435; interconnection 1428; interconnection descriptions 968; software 7; software descriptions 7.
Failure: `INFORMATION_SYSTEM_TYPE` has no approved transformation handler. Treat as mapping-dispatch gap, not hydration failure.

## 2026-09-10 — Next Cell 7 transformation-handler failure
Run ID: `20260910T183511Z`; Model: `SSP`.
Hydration remained successful. Failure advanced to `ATOIATO_DATE` -> `system-security-plan.system-characteristics.date-authorized`, with no approved transformation handler.

## 2026-09-10 — Mapping contract report
Canonical mapping rows inspected: **54**.
Rows rejected by handler contract regardless of source data: **2**.
No source values were read; no database queries or writes; not a graph acceptance.

Rejected row 1:
- canonical row: 16
- source field: `ATOIATO_DATE`
- OSCAL model: `SSP`
- OSCAL/canonical element path: `system-security-plan.system-characteristics.date-authorized`
- owner element path: `system-security-plan.system-characteristics`
- OSCAL field / relative path: `date-authorized`
- mapping type: `Transform`
- status: `In Progress`
- Notes: `Convert timestamp to DateDatatype`
- mapping notes: null
- transformation logic: null
- rejection: no approved transformation handler for this source/owner/target/mapping-type contract.

Rejected row 2:
- canonical row: 33
- source field: `RECOMMENDED_SECURITY_CATEGORY`
- OSCAL model: `SSP`
- OSCAL/canonical element path: `system-security-plan.system-characteristics.security-impact-level`
- owner element path: `system-security-plan.system-characteristics.security-impact-level`
- OSCAL field name: null
- field relative path: empty
- mapping type: `Extension Property`
- status: `In Progress`
- Notes: `All Nulls`
- mapping notes: null
- transformation logic: null
- rejection: `Security-impact mapping source is not approved`.

Engineering interpretation: the current blocker is explicitly a mapping-governance/handler-contract problem. Do not invent date conversion semantics or approve the security-impact source implicitly. Resolve the approved transform/dispatch contract first.

## 2026-09-10 — Successful SSP graph run after handler fixes
Run ID: `20260910T185412Z`; Model: `SSP`.

Component hydration completed successfully:
- lookup rows: **1435**
- interconnection rows: **1428**
- interconnection descriptions: **968**
- software rows: **7**
- software descriptions: **7**

Graph validation:
- graph nodes: **70,102**
- graph edges: **67,289**
- duplicate node keys: **0**
- duplicate edge keys: **0**
- dangling source edges: **0**
- dangling target edges: **0**
- pre-write validation: **PASSED**
- `EXECUTE_WRITES = False`
- DIM/FACT changes: **none**

Result: `OSCAL MAPPING RUN COMPLETE` with Nodes **70,102**, Edges **67,289**, Writes **False**.

Interpretation: the mapper now completes the in-memory SSP graph and pre-write graph integrity checks successfully at this checkpoint. This is not yet a production write-readiness/conformance claim because writes remain disabled and downstream semantic/schema readiness gates still apply.

Source: phone screenshots supplied in ChatGPT conversation on 2026-09-10.