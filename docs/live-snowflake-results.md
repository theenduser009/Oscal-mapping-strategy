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

## 2026-09-10 — SSP mapped-scope assembly passed
Mapped-scope assembly consumed the successful in-memory graph checkpoint.

- documents assembled: **2,813**
- graph nodes consumed: **70,102**
- graph edges consumed: **67,289**
- root nodes consumed: **2,813**
- writes executed: **False**
- result: **MAPPED-SCOPE ASSEMBLY PASSED**
- complete SSP claim: **False**
- OSCAL schema-valid claim: **False**

Interpretation: all 2,813 SSP source/root records were assembled successfully for the currently mapped scope. This validates mapped-scope assembly only; it deliberately does not claim complete SSP coverage or OSCAL schema validity. No writes were executed.

## 2026-09-10 — Control Implementation mapping-artifact screenshot checkpoint
Phone screenshots of `archer_to_oscal_mapping.xlsx` filtered to `OSCAL_Model = SSP - Control Implementation` were reviewed.

Observed mapping-artifact state:
- approximately **50 of 609** workbook records are visible under this filter.
- the displayed Control Implementation rows are predominantly `Mapping_Type = Extension Property`.
- many displayed rows have a **blank `OSCAL_Element_Path`** rather than an approved concrete Control Implementation target path.
- repeated note pattern: `May map to props[] or calculated from implemented-requirements count`.
- visible examples include `COUNT_OF_CONTROLS`, `ALLOCATE_BASELINE_CONTROLS`, `CONTROL_SET_VERSION_NUMBER`, `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`, `COUNT_OF_CONTROLS_WITH_OPEN_POAMS`, `NUMBER_OF_CONTROLS_BEING_INHERITED_BY_OTHERS`, `ARCHIVE_CONTROLS`, `BASELINE_CONTROLS_ALLOCATED_DATE`, `FULL_CONTROL_ASSESSMENT_HELPER`, `CONTROL_RISK_APPETITE`, `CONTROL_OWNER_CO`, `ALLOCATED_CONTROLS`, `INHERITED_CONTROLS`, `MASTER_CONTROLS`, and other control-related fields.

Interpretation: this screenshot evidence does **not** establish Control Implementation completion. The workbook still contains many Control Implementation candidates whose final OSCAL target/semantics are unresolved. In particular, a note suggesting `props[]` or a calculation from `implemented-requirements` is design evidence, not an approved mapping contract. Do not auto-map these fields or claim Control Implementation completeness from the current artifact.

Next validation should be against the generated OSCAL DIM/FACT and registry to establish which `control-implementation` / `implemented-requirements` branches actually materialize and reconcile, separately from the unresolved Excel backlog.

## 2026-09-10 — Broader mapping-workbook screenshot evidence
Five additional screenshots of `archer_to_oscal_mapping.xlsx` were reviewed as visual evidence of the mapping artifact across multiple model areas. These screenshots expand the previous Control Implementation-only checkpoint; they do not replace the workbook as the authoritative source.

Visible SSP / related mappings include:
- authorization-package metadata timestamp fields mapped to SSP metadata timestamp targets with `Transform` semantics.
- `TRACKING_ID` mapped under SSP metadata/document identifiers.
- `SAP_ID` and authorization-package/system-characteristics fields visible in the SSP section.
- `OPERATIONAL_STATUS` mapped to the SSP system-characteristics status/state area with transform semantics.
- `INFORMATION_SYSTEM_TYPE`, `FISMA_REPORTABLE`, `FINANCIAL_SYSTEM`, `MISSION_CRITICAL`, `CRITICAL_INFRASTRUCTURE`, `PACKAGE_TYPE`, `PIA_REQUIRED`, and related system-characteristics fields shown as direct/extension/calculated/TBD candidates depending on row.
- security-impact candidate rows for confidentiality, integrity, and availability are visibly targeted to `system-security-plan.system-characteristics.security-impact-level` child objectives with Direct/Transform semantics and FIPS-199-oriented notes.
- responsible-party candidate fields (`INFORMATION_OWNER_IO`, `INFORMATION_SYSTEM_OWNER_ISO`, `AUTHORIZING_OFFICIAL_AO`, `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO`, `PRIVACY_OFFICER_PO`, etc.) visibly target `system-security-plan.metadata.responsible-parties[]`; some are Transform and some remain TBD / need analysis.
- component reference rows for `SOFTWARE`, `HARDWARE`, `INTERCONNECTIONS`, `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM`, and `SAP_INTAKE_FORM_INTERCONNECTIONS` target the SSP system-implementation components branch.

Control Implementation evidence remains consistent with the prior checkpoint: many control-related rows are `Extension Property` candidates with blank concrete OSCAL element paths and notes such as `May map to props[] or calculated from implemented-requirements count`. Examples visible across the screenshots include control counts, allocated/inherited/archived controls, control risk thresholds, assessor fields, master controls, helper fields, and POA&M-related control counts. This is unresolved mapping-design backlog, not proof of a populated `control-implementation` branch.

The screenshots also visibly contain Assessment Results rows. Risk/scoring fields such as vulnerability, antivirus, patch, compliance, authorization-package risk, and device-risk scores target Assessment Results observation/property paths and are generally marked `Extension Property` with notes indicating Archer-specific risk scoring mapped as observations. This confirms that the workbook is multi-model and that these rows must not be counted as SSP Control Implementation completion.

Accuracy guardrail: only text/paths sufficiently legible in the supplied screenshots are recorded here. No obscured cell value, truncated path, null percentage, or off-screen workbook row is inferred. For exact row-level reconciliation, use the actual workbook/CSV rather than these images.

Source: phone screenshots supplied in ChatGPT conversation on 2026-09-10.