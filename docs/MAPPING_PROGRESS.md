# Archer to OSCAL mapping progress

Last updated: 2026-09-11, after seventeen-field AR acceptance and approval/implementation of the next seventeen. Owner: Source One mapping implementation team.

This is the durable field-to-target register and the basis for daily reporting.
It covers the evidence-backed subset below, not every row in the external Excel
workbook. In the detailed SSP register, `system-security-plan` is abbreviated `SSP`.
`M`, `SC`, and `SI` mean OSCAL SSP Metadata, System Characteristics, and System
Implementation respectively. These labels are grouping aids; the path controls
the destination. An artifact row is not complete merely because it is accepted
by a dispatcher or a target node exists.

## Current direction — workflow fields and duplicate score deferred

On September 11, the owner confirmed **skip the seven workflow audit fields for
now**, then also directed us to **defer both Average Security Compliance Score
row occurrences** because their duplicate-field meaning is unresolved.
Neither duplicate is counted as complete. These workflow fields target
`assessment-results.results[].props[]`; they are deferred, not implemented or
complete. This is separate from the two parked value-conversion blockers,
`RISK_ACCEPTANCE_RBDS` and `RISK_ASSESSMENT_REPORT`.

| Remaining Archer field | Row occurrences | Exact Excel target | Current issue |
| --- | ---: | --- | --- |
| `AVG_SECURITY_COMPLIANCE_SCORE` | 2 | `assessment-results.results[].observations[]` | **Deferred by owner, 2026-09-11.** Duplicate meaning unresolved. Both original rows are preserved; no rename, deduplication or output is inferred. Reopen only after source-field identity is clarified. |
| `TOTAL_PACKAGE_INHERENT_RISK` | 1 | `assessment-results.results[].observations[]` | CSV says observation; earlier owner Notes evidence differs. Confirm the governing original row before selecting its contract. |
| `FINDINGS` | 1 | `assessment-results.results[].findings[]` | Notes require linking finding UUIDs; referenced finding identity/source and parent association are not established. |

**No action or notebook run is requested for the deferred score.**
The two remaining non-deferred rows are Total Package Inherent Risk and Findings,
with the unresolved contracts shown above. No code is changed by this status update.

Inventory is **45 row occurrences = 17 accepted + 15 implemented candidate-only
+ 2 parked after rejection + 7 workflow rows deferred + 2 duplicate score rows deferred
+ 2 remaining rows under review**.
Deferred rows remain in the inventory and are not completed mappings.

The [two-field diagnostic](https://github.com/theenduser009/Oscal-mapping-strategy/blob/ac3e8b348eabc708960ccdd51f00e3a0383613dc/docs/ssp_mapping_progress_checkpoint.md#assessment-results-rejected-value-shape-diagnostic--2026-09-11)
is complete and matched the blocked run: 2,813 records, zero parse failures,
1 reference-shaped rejection and 99 multi-number-array rejections, zero writes.
The field meanings and output rules remain parked. No rerun is requested.
The blocked 34-field batch is not accepted. SSP, mapper code, registry and the
original CSV remain unchanged.

## Latest attempted run — blocked, not accepted

The [v3 thirty-four-field checkpoint](https://github.com/theenduser009/Oscal-mapping-strategy/blob/c4279208c3d13554c5fe667755f0e8a2b6cabba5/docs/ssp_mapping_progress_checkpoint.md) passed mapping/registry contracts
and candidate key integrity, but has 100 rejected field values: 1 in
`RISK_ACCEPTANCE_RBDS` and 99 in `RISK_ASSESSMENT_REPORT`. No outputs or database
writes were published. The seventeen earlier accepted mappings remain accepted;
the seventeen additions are still pending live acceptance. The shape diagnostic
is complete and matched both rejected counts. The owner parked those two fields
and directed work to the remaining eleven, as detailed above.
Rejection does not prove defective source data.

## Current position

- [September 10 end-of-day report](daily/2026-09-10.md): accepted SSP hydration,
  date/property release and mapped-scope assembly are separated from AR planning.
  Current inventory is 43 distinct Archer fields / 44 implemented source-target
  entries (metadata 11, system characteristics 27, components 6), not 44 fully
  verified Excel rows. The count includes the package-type route with its open
  naming correction and excludes the unimplemented PTA helper, unreconciled
  security category, controlled versions and deferred fields. That 5 PM snapshot
  preceded the AR implementation below. No full-workbook percentage is established.

- **September 11 accepted v2 run:** the seventeen-field AR mapper
  is live accepted [E18]. All 2,813 records were processed, producing 46,960
  observations, 52,586 nodes and 49,773 edges with zero contract/key/invalid-value
  errors and no writes. Ten fields cover every record; seven have source gaps.
  Current AR inventory: **45 rows = 17 live accepted + 17 implemented/pending live
  + 11 not enabled**. SSP counts above
  are unchanged. This is not full model completion or independent proof of every
  source-to-payload value.

- **Owner direction:** park the remaining SSP corrections and review other
  Excel-defined models. Preserve accepted work. Assessment Results is now the
  selected model; [start here](ASSESSMENT_RESULTS_START_HERE.md). The owner
  requested grouping by matching path/type/Notes. The new CSV has four AR-target
  groups: 45 row occurrences, 44 distinct field names, not completed mappings.
  Observation-only and observation-or-property targets are separate. The first
  seventeen score fields are now accepted under that representation [E18].
  The next seventeen alternative-path rows now have owner approval for the same
  inline-property representation and are implemented, pending live [E19].
  Conditional workflow and finding-reference groups remain separate [E15, E16].

- Start with [SSP — done and next](SSP_DONE_AND_NEXT.md) for the short summary.
  Clearer Excel Notes supersede the old helper classification: `HELPER_PTA_CALC`
  should map to SC `props[]` but is skipped. `PACKAGE_TYPE` has a property-name
  discrepancy. Neither correction has been coded; Control Implementation is parked.

- Last accepted live baseline: 70,102 nodes, 67,289 edges, zero duplicate keys,
  zero dangling edges; pre-write validation passed and no DIM/FACT writes [E13].
- Mapped-scope JSON assembly is now live accepted: 2,813 documents and roots,
  consuming that exact graph with no writes. Full SSP/schema-valid claims
  remain false; this is an assembly milestone, not new mapping rows [E14].
- That run included partial component hydration: 1,435 lookup rows, comprising
  7 software and 1,428 interconnection rows; descriptions available for 7 and
  968 respectively [E4]. These are lookup counts, not completed SSP counts.
- The latest full mapper run succeeded after the date/property fixes [E13].
  The preceding contract report inspected 54 canonical mappings and rejected
  two contracts. Those historical classifier counts are not completed-field
  counts; graph success is not independent value-by-value proof.
- Authorization-date handler is implemented; local verification passed (203 tests).
  Its artifact contract is
  `Transform`, destination `SC.date-authorized`, Notes `Convert timestamp to
  DateDatatype`. The current release is live accepted [E13].
- The second rejection has type `Extension Property`, destination
  `SC.security-impact-level`, Notes `All Nulls`. That note does not establish an
  approved property destination or transformation. It remains unresolved.
- Keep `EXECUTE_WRITES = False`. A healthy prior graph does not establish final
  OSCAL schema conformance or field-specific payload equality.

## Status vocabulary

| Status | What it establishes |
| --- | --- |
| Implemented | Repository behavior exists; local verification is stated separately. |
| Live accepted | A successful recorded live run includes that release; not automatic field-value proof. |
| Payload proven | A recorded field-specific check proves the stated output property for its tested population. |
| In progress / pending live | Work or deployment verification remains; no live-success claim. |
| Missing source | The observed population lacks a source value or a governed lookup. |
| Deferred / unresolved | No approved executable contract, business decision, or concrete target yet. |

## Model/path status and clarification queue

This is the quick view of **what is done, what is not, why, and what information
is needed**. The source-field detail and evidence follow. Grouped rows are not
an Excel-row count. "Done in scope" means the stated implementation/release is
accepted, not full model completeness or independent proof of every value.
No business question and no field-level test evidence are different things.

### SSP — accepted work preserved; remaining corrections parked

| OSCAL model | Full OSCAL element path | Field / scope | Status | Why / evidence | Additional information or clarification needed |
| --- | --- | --- | --- | --- | --- |
| SSP | `system-security-plan.metadata.document-ids[].identifier` | `TRACKING_ID` | Done in scope | Exact match for 2,813 records [E2]. | None. |
| SSP | `system-security-plan.metadata.title` | Approved `AUTHORIZATION_PACKAGE_NAME` reuse | Done in scope | Completion rule implemented; metadata release accepted [E7, E8]. | No current business question; separate exact title proof not recorded. |
| SSP | `system-security-plan.metadata.version` | Controlled `1.0` | Done in scope | Approved configuration, not an Excel source row [E7]. | None. |
| SSP | `system-security-plan.metadata.oscal-version` | Configured OSCAL version | Done in scope | All 2,813 metadata nodes checked [E2]. | None. |
| SSP | `system-security-plan.metadata.last-modified` | Two Last Updated sources | Implemented; accepted exception | Resolver accepted; one source empty, populated timestamps timezone-naive [E3, E7]. | Preserve values now. Source timezone only needed for later conformance work. |
| SSP | `system-security-plan.metadata.published` | Two First Published sources | Done in scope | Resolver in accepted release; conflicting populated values fail [E1, E7]. | No current business question; field-specific completeness proof not recorded. |
| SSP | `system-security-plan.metadata.props` (literal Excel path) | Confirmed-in-Archer field | Deferred | TBD, source-empty, literal path not the active collection path [E1, E7]. | Approved target and property name/value rule; populated source evidence. |
| SSP | `system-security-plan.metadata.responsible-parties[]` | Five approved assignments | Done in scope | Role/party references implemented; release accepted [E7, E8]. | None for those five fields. |
| SSP | `system-security-plan.metadata.responsible-parties[]` | Four TBD fields listed below | Deferred | ISSE, ISA, AODR and SISSO are separate unresolved rows [E1, E7]. | Approved role assignment, reference semantics and Notes for each field. |
| SSP | `system-security-plan.metadata.roles[]`; `system-security-plan.metadata.parties[]` | Support for five approved assignments | Done in scope | Definitions, stable identity and reference closure implemented [E7, E8]; not extra Excel rows. | None for current scope. |
| SSP | `system-security-plan.system-characteristics.system-ids[].id` | `SAP_ID` | Done in scope | Accepted identity rule; prior valid coverage 2,813 [E6, E7]. | None. |
| SSP | `system-security-plan.system-characteristics.system-name` | `AUTHORIZATION_PACKAGE_NAME` | Done in scope | Accepted release; prior valid coverage 2,813 [E6, E7]. | None. |
| SSP | `system-security-plan.system-characteristics.system-name-short` | `ACRONYM` | Done in scope | Implemented and live accepted [E1, E6]. | No current business question; exact equality not separately recorded. |
| SSP | `system-security-plan.system-characteristics.description` | `MISSION_PURPOSE` | Implemented; source gap | 33 missing source descriptions [E6, E7]. | Missing descriptions from the source owner for full record coverage. |
| SSP | `system-security-plan.system-characteristics.status.state` | `OPERATIONAL_STATUS` | Implemented; source gap | Crosswalk accepted; 42 missing source values [E6, E7]. | Missing source statuses for full record coverage. |
| SSP | `system-security-plan.system-characteristics.authorization-boundary.description` | Boundary description | Implemented; source gap | 294 missing source descriptions [E6, E7]. | Missing source boundary descriptions. |
| SSP | `system-security-plan.system-characteristics.status.remarks` | `AUTHORIZATION_COMMENTS` | Implemented | Explicit remarks handler exists despite Extension Property label [E1, E8]. | No current question; separate field proof not recorded. |
| SSP | `system-security-plan.system-characteristics.date-authorized` | `ATOIATO_DATE` | Done in scope | Date handler tested and live accepted [E12, E13]. | None; no timezone conversion requested. |
| SSP | `system-security-plan.system-characteristics.props[]` | Seven approved fields other than `PACKAGE_TYPE`, listed below | Done in routing scope | Property routes included in accepted release [E5, E13]; not every field's exact Notes/value agreement is proven. | No newly identified question for these seven; retain field-level review separately. |
| SSP | `system-security-plan.system-characteristics.props[]` | `PACKAGE_TYPE` | Pending correction; parked | Code name is `package-type`; Notes example says `authorization-package-type`. | No additional source table needed for naming correction. The sample value is not a constant. |
| SSP | `system-security-plan.system-characteristics.props[]` | `HELPER_PTA_CALC` | Not implemented; parked | Calculated/custom-property row is incorrectly skipped. | Full Notes and expected property name/value rule if not available in the artifact. Do not invent a PTA formula. |
| SSP | `system-security-plan.system-characteristics.props[]` | `PACKAGE_TYPE_HELPER_CALC` | Intentionally excluded | Notes explicitly say transient calculation field — do not map. | None; exclusion is not a completed mapping. |
| SSP | `system-security-plan.system-characteristics.security-impact-level` | Eleven CIA source-to-member mappings below | Done in complete-only assembly scope | Conversion and omission of incomplete CIA assemblies accepted [E6, E7, E13]. | Missing objectives are source gaps; no invented defaults or precedence. |
| SSP | `system-security-plan.system-characteristics.security-impact-level` | `RECOMMENDED_SECURITY_CATEGORY` | Deferred | All Nulls does not define a populated-value rule [E12]. | Approved destination and transform/value policy. |
| SSP | `system-security-plan.system-characteristics.security-sensitivity-level` | `SECURITY_CATEGORY` | Review pending; parked | Clearer screenshot shows Direct row absent from prior register; implementation not reconciled. | Engineering must compare this exact row with canonical output before claiming completion. |
| SSP | `system-security-plan.system-implementation.components[]` | Six Reference fields below | Done in agreed reference scope | Identity/type and approved partial hydration accepted [E4, E9]. Some input/hydration gaps remain. | None for current reference scope. Extra hydration requires separate source proof; no unlisted component-status mapping. |
| SSP | **Unconfirmed**; Notes propose `system-security-plan.control-implementation.props[]` | Control-count candidate and other blank-target control rows | Deferred; parked | Notes placement conflicts with pinned standard; alternative not approved. | Owner-approved target, source count versus calculation, property name/value policy and namespace; see [proposal](checkpoints/2026-09-10_ssp_control_count_mapping_proposal.md). |

CIA member suffixes are `security-objective-confidentiality`,
`security-objective-integrity`, and `security-objective-availability` on the full
security-impact path above. Their exact source-field grouping is retained below.

### Assessment Results progress and other model review queue

| OSCAL model | Excel target path | Field / scope | Status | Evidence / remaining work | Additional information or clarification needed |
| --- | --- | --- | --- | --- | --- |
| Assessment Results | `assessment-results.results[].observations[]` | `VULNERABILITY_SCORE`, `ANTIVIRUS_SCORE`, `PATCH_SCORE`, `SECURITY_COMPLIANCE_SCORE` | Live accepted | Each emitted for 2,813 records with zero missing/invalid values. Contracts and graph keys passed; no writes [E17]. | None for batch-one runtime acceptance. It is not a full-model/schema-valid claim. |
| Assessment Results | `assessment-results.results[].observations[]` | Thirteen additions listed in the AR register below | Live accepted; seven fields have source gaps | Expanded run passed for all 17 selected fields with zero invalid values; missing counts recorded below [E18]. | No rerun. Source owner can investigate absent values; no score defaults or recalculation. |
| Assessment Results | `assessment-results.results[].observations[]` | `AVG_SECURITY_COMPLIANCE_SCORE` (two occurrences) | **Deferred by owner, 2026-09-11; not implemented** | Duplicate field meaning unresolved [E15, E16]. Both rows remain recorded and neither is counted complete. | Reopen only after the original sheet clarifies duplicate versus mistaken source-field name. No inferred rename or deduplication. |
| Assessment Results | `assessment-results.results[].observations[]` | `TOTAL_PACKAGE_INHERENT_RISK` | Not enabled; clarification needed | Earlier owner Notes and CSV evidence conflict [E15, E16]. | Confirm the governing original row and Notes. No inferred destination. |
| Assessment Results | `assessment-results.results[].observations[] or props[]` (original Excel choice) | 17 risk rows listed below | Implemented; pending live | Owner approved one observation per field with a named inline property on September 11 [E19]. Original path/Notes checked exactly; emitted node path ends at observations[]. | Expanded run blocked by 100 rejected values in two fields. Inspect their shapes before changing conversion; do not rerun unchanged. No registry insertion or score recalculation. |
| Extension Properties label; Assessment Results destination | `assessment-results.results[].props[]` | Seven workflow audit fields | Grouped; conditional scope | Notes say to include if needed for audit trail [E15]. | Confirm audit-trail inclusion and property name/value rules; keep result-level properties separate from observation properties. |
| Assessment Results | `assessment-results.results[].findings[]` | `FINDINGS` | Review pending | Reference target visible; lookup and result-parent association not established. | Reference shape, finding identity, source/lookup and parent-result relationship. |
| Profile | `profile.imports[]` | `BASELINE_RECOMMENDATION` | Review pending | Conditional import example in Notes does not supply an approved import reference. | Baseline-to-URI mapping, intended import structure and selection rule; reconcile Extension Property label with target. |
| POA&M | `plan-of-action-and-milestones.poam-items[]` | `POAMS` | Review pending | New CSV confirms Reference target and linking Notes [E15]; no handler accepted. | Reference shape, identity and parent relationship. |
| Assessment Plan | **Full paths/Notes still to reconcile** | Request, approval and preassessment-review fields | Review pending | Separate model rows visible; no accepted implementation release. | Exact targets/Notes, task grouping, property/value rules and source shape. |

The new [CSV transcription](transcribed_mapping_rows.csv) [E15] contains 51 records,
including 45 with Assessment Results targets. It is not the full workbook and
has one duplicated `AVG_SECURITY_COMPLIANCE_SCORE` occurrence. The
[group details](ASSESSMENT_RESULTS_START_HERE.md) preserve that duplicate and the
conflict between earlier verbal Notes and the inherent-risk transcription.
The former blanket nested-observation-property target in this queue is superseded;
no AR mapper was implemented under that interpretation. The subsequent approved
inline-property representation is implemented for the seventeen selected score
fields and creates no extra property registry nodes [E16]. Those seventeen are live
accepted [E18]. Seventeen alternative-path additions now use the explicitly
approved same representation but remain pending live [E19]. The
[historical registry snapshot](checkpoints/2026-09-09-oscal-element-registry-collection-snapshot.md)
shows Assessment Results collections for results, result properties and
observations; it does not establish observation properties. This is not a fresh
live schema check. The [generic graph contract](ARCHITECTURE_CONTEXT.md)
requires parent-instance context for nested collections; do not guess it.

Update this queue with every accepted change. Keep a code defect, missing source,
business question, unreviewed row and intentional exclusion distinct. Unknown
paths stay unknown; no question silently becomes an approved mapping. No global
completion percentage is asserted.

### Assessment Results field register

All rows below target model **Assessment Results**, exact path
`assessment-results.results[].observations[]`, with `Extension Property` type
and Notes `Archer-specific risk scoring - map as observation`. Transformation:
preserve the source scalar as property text inside one observation per field;
property names use the existing lowercase/hyphen rule. Numeric-looking field
names do not authorize calculating scores, averages, totals or grades.

| Archer field | Status | Evidence / remaining work |
| --- | --- | --- |
| `VULNERABILITY_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `ANTIVIRUS_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `PATCH_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `SECURITY_COMPLIANCE_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `STANDARD_OPERATING_ENVIRONMENT_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `COMPUTER_PASSWORD_AGE_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `VULNERABILITY_REPORTING_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `SECURITY_COMPLIANCE_REPORTING_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `AVG_AUTHORIZATION_PACKAGE_RISK_SCORE` | Live accepted | 2,813 emitted; 0 missing; 0 invalid [E18]. |
| `RISK_SCORE_GRADE` | Live accepted; source gap | 2,546 emitted; 267 missing; 0 invalid [E18]. |
| `AVG_VULNERABILITY_SCORE` | Live accepted; source gap | 2,800 emitted; 13 missing; 0 invalid [E18]. |
| `AVG_PATCH_SCORE` | Live accepted; source gap | 2,812 emitted; 1 missing; 0 invalid [E18]. |
| `AVG_ANTIVIRUS_SCORE` | Live accepted; source gap | 2,800 emitted; 13 missing; 0 invalid [E18]. |
| `AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE` | Live accepted; source gap | 2,272 emitted; 541 missing; 0 invalid [E18]. |
| `AVG_COMPUTER_PASSWORD_AGE_SCORE` | Live accepted; source gap | 2,800 emitted; 13 missing; 0 invalid [E18]. |
| `AVG_VULNERABILITY_REPORTING_SCORE` | Live accepted; source gap | 2,800 emitted; 13 missing; 0 invalid [E18]. |

### Approved alternative-path additions — pending live

Model **Assessment Results**. Original input path:
`assessment-results.results[].observations[] or props[]`. Original Notes:
`Archer-specific risk scoring - map as observation or property`. The owner
approved one observation per field with its source scalar inside an inline
named property on September 11 [E19]. Emitted node path:
`assessment-results.results[].observations[]`. No new score or formula is derived.

| Archer field | Status | Evidence / remaining work |
| --- | --- | --- |
| `RISK_ACCEPTANCE_RBDS` | Blocked: scalar conversion rejected values | 0 candidate emissions; 2,812 missing; 1 invalid [E20]. Inspect actual source shape; no inferred conversion. |
| `TOTAL_PACKAGE_RESIDUAL_RISK` | Implemented; candidate evidence only | 2,811 candidate emissions; 2 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `ADJUSTED_TOTAL_RISK_SCORE` | Implemented; candidate evidence only | 2,813 candidate emissions; 0 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `ADJUSTED_AVERAGE_RISK_SCORE` | Implemented; candidate evidence only | 2,813 candidate emissions; 0 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `CURRENT_HIGHEST_DEVICE_RISK_SCORE` | Implemented; candidate evidence only | 2,812 candidate emissions; 1 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `CURRENT_AVERAGE_DEVICE_RISK_SCORE` | Implemented; candidate evidence only | 2,813 candidate emissions; 0 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `CURRENT_CONTROL_RISK_SCORE` | Implemented; candidate evidence only | 2,743 candidate emissions; 70 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | Implemented; no populated evidence | 0 candidate emissions; 2,813 missing; 0 invalid [E20]. Missing-source cause not established. |
| `PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | Implemented; no populated evidence | 0 candidate emissions; 2,813 missing; 0 invalid [E20]. Missing-source cause not established. |
| `BASELINE_HIGHEST_DEVICE_RISK_SCORE` | Implemented; candidate evidence only | 1,094 candidate emissions; 1,719 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `BASELINE_AVERAGE_DEVICE_RISK_SCORE` | Implemented; candidate evidence only | 1,093 candidate emissions; 1,720 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `BASELINE_CONTROL_RISK_SCORE` | Implemented; candidate evidence only | 1,096 candidate emissions; 1,717 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `RISK_ASSESSMENT` | Implemented; candidate evidence only | 515 candidate emissions; 2,298 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | Implemented; candidate evidence only | 1 candidate emissions; 2,812 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | Implemented; candidate evidence only | 1 candidate emissions; 2,812 missing; 0 invalid [E20]. Whole batch blocked; not runtime accepted. |
| `INITIAL_RISK_ASSESSMENT` | Implemented; no populated evidence | 0 candidate emissions; 2,813 missing; 0 invalid [E20]. Missing-source cause not established. |
| `RISK_ASSESSMENT_REPORT` | Blocked: scalar conversion rejected values | 217 candidate emissions; 2,497 missing; 99 invalid [E20]. Inspect actual source shape; no inferred conversion. |

The expanded cell remains read-only and cumulative, retaining all seventeen
accepted fields. Eleven row occurrences remain outside its allowlist: three
observation-only occurrences requiring clarification, seven conditional workflow
rows and one finding-reference row. Properties remain inline, so no registry
insertion is needed. A missing source value is reported separately from a contract
error and is not evidence that a populated mapping was exercised.

## Metadata register

| Archer field / controlled input | Model and OSCAL destination | Current evidence and next gap |
| --- | --- | --- |
| `TRACKING_ID` | M: `SSP.metadata.document-ids[].identifier` | Implemented, live accepted, payload proven: exact match for 2,813/2,813; all failure counts zero [E2]. |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` | M: `SSP.metadata.last-modified` | Implemented source-preserving resolver, live accepted; source empty for all 2,813 in audit [E3, E7]. |
| `LAST_UPDATED` | M: `SSP.metadata.last-modified` | Implemented, live accepted; raw equality proven for 2,813, but all timestamps timezone-naive. Approved preservation retains the conformance gap [E3, E7]. |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_FIRST_PUBLISHED` | M: `SSP.metadata.published` | Implemented source-preserving resolver, live accepted; separate transformed-value completeness proof not recorded [E1, E7]. |
| `FIRST_PUBLISHED` | M: `SSP.metadata.published` | Same resolver: differing populated candidates fail; do not infer timezone or candidate precedence [E1, E7]. |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER` | M: literal `SSP.metadata.props` | Deferred: `TBD`, source-empty, and literal path is not active collection registry path [E1, E7]. |
| `AUTHORIZATION_PACKAGE_NAME` (approved reuse) | M: `SSP.metadata.title` | Implemented approved metadata completion rule; prior metadata release accepted. Separate exact title payload proof not recorded [E7, E8]. |
| Controlled SSP document version | M: `SSP.metadata.version` | Implemented approved value `1.0`; prior metadata release accepted; not an Excel source-field mapping [E7]. |
| `CONFIG["OSCAL_VERSION"]` | M: `SSP.metadata.oscal-version` | Implemented, live accepted, payload proven: 2,813 valid configured values with zero failures [E2]. |
| `INFORMATION_OWNER_IO` | M: `SSP.metadata.responsible-parties[]` | Implemented `information-owner` assignment with referenced role/person party; metadata release live accepted [E7, E8]. |
| `INFORMATION_SYSTEM_OWNER_ISO` | M: `SSP.metadata.responsible-parties[]` | Implemented `system-owner` assignment with role/party closure; live accepted [E7, E8]. |
| `AUTHORIZING_OFFICIAL_AO` | M: `SSP.metadata.responsible-parties[]` | Implemented `authorizing-official` assignment with role/party closure; live accepted [E7, E8]. |
| `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO` | M: `SSP.metadata.responsible-parties[]` | Implemented `system-security-officer` assignment with role/party closure; live accepted [E7, E8]. |
| `PRIVACY_OFFICER_PO` | M: `SSP.metadata.responsible-parties[]` | Implemented `privacy-officer` assignment with role/party closure; live accepted [E7, E8]. |
| `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE`, `INFORMATION_SYSTEM_ADMINISTRATOR_ISA`, `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR`, `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO` | M: `SSP.metadata.responsible-parties[]` | Four `TBD` rows deferred; no generic party emission [E1, E7]. |

Role and party objects at `SSP.metadata.roles[]` and `SSP.metadata.parties[]`
support the five approved assignments. Stable identities, deduplication and
reference closure are implemented; graph acceptance is not separate proof of
every party attribute [E7, E8].

## System characteristics register

| Archer field | Model and OSCAL destination | Current evidence and next gap |
| --- | --- | --- |
| `SAP_ID` | SC: `SSP.system-characteristics.system-ids[].id` | Implemented governed collection identity; live accepted. Prior presence/valid coverage 2,813 [E1, E6, E7]. |
| `AUTHORIZATION_PACKAGE_NAME` | SC: `SSP.system-characteristics.system-name` | Implemented, live accepted; prior generated-valid coverage 2,813 [E6, E7]. |
| `ACRONYM` | SC: `SSP.system-characteristics.system-name-short` | Implemented, live accepted; artifact/presence evidence, not independent exact-value proof [E1, E6, E10]. |
| `MISSION_PURPOSE` | SC: `SSP.system-characteristics.description` | Implemented, live accepted; 2,780 generated valid, 33 missing source values [E6, E7]. |
| `OPERATIONAL_STATUS` | SC: `SSP.system-characteristics.status.state` | Implemented crosswalk, live accepted; 2,771 generated valid, 42 missing source values [E6, E7, E8]. |
| `AUTHORIZATION_BOUNDARY_DESCRIPTION` | SC: `SSP.system-characteristics.authorization-boundary.description` | Artifact targets boundary parent; handler supplies description. Live accepted; 2,519 generated valid, 294 missing source values [E1, E6, E7, E8]. |
| `AUTHORIZATION_COMMENTS` | SC: `SSP.system-characteristics.status.remarks` | Explicit remarks handler implemented; preserve artifact target despite Extension Property label [E1, E8]. |
| `ATOIATO_DATE` | SC: `SSP.system-characteristics.date-authorized` | Implemented, locally tested and included in the successful live release: ISO date/timestamp to `YYYY-MM-DD`, no timezone shift; null skips, invalid/non-ISO rejects. Separate field-population/equality proof not recorded [E12, E13]. |
| `RECOMMENDED_SECURITY_CATEGORY` | SC: `SSP.system-characteristics.security-impact-level` | Unresolved rejected Extension Property contract; Notes All Nulls are not a completion or routing rule. |

The following eight screenshot-approved Extension Property sources route to
`SSP.system-characteristics.props[]`, with stable name/value property payloads:

| Archer source | Implementation / acceptance |
| --- | --- |
| `INFORMATION_SYSTEM_TYPE` | Routing correction implemented, locally tested and included in live accepted release; per-field population/equality not recorded [E5, E13]. |
| `FISMA_REPORTABLE` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |
| `FINANCIAL_SYSTEM` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |
| `MISSION_CRITICAL` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |
| `CRITICAL_INFRASTRUCTURE` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |
| `PACKAGE_TYPE` | Collection route implemented and included in accepted release, but clearer Notes example specifies `authorization-package-type` while code emits `package-type`. Naming correction pending; not fully complete [E5, E13, short summary]. |
| `PIA_REQUIRED` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |
| `INFORMATION_CLASSIFICATION` | Same approved collection route, included in accepted release; field-specific proof not recorded [E5, E13]. |

Their original artifact paths remain provenance; canonical routing does not
authorize rewriting arbitrary unregistered fields [E5].

Security-impact mappings below share prefix
`SSP.system-characteristics.security-impact-level` [E1, E8]:

| Archer sources | OSCAL member |
| --- | --- |
| `RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY`, `CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE`, `CNSS_CONFIDENTIALITY_RATING` | `security-objective-confidentiality` |
| `RECOMMENDED_INTEGRITY_CONTROL_CATEGORY`, `INTEGRITY_CONTROL_CATEGORY_OVERRIDE`, `PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY`, `CNSS_INTEGRITY_RATING` | `security-objective-integrity` |
| `RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY`, `AVAILABILITY_CONTROL_CATEGORY_OVERRIDE`, `PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY`, `CNSS_AVAILABILITY_RATING` | `security-objective-availability` |

The FIPS conversion and complete-only assembly have prior live acceptance;
the newer strict source/target dispatch release also completed its live run [E13].
The assembly emits only when
all three objectives exist: prior evidence identified 270 complete, 90 partial
and 2,453 empty assemblies. Empty/partial assemblies are omitted; no defaults or
unapproved recommended/override precedence are invented [E6, E7].

## Components and remaining branches

All six reference fields below target SI:
`SSP.system-implementation.components[]` [E1, E8, E9].

| Archer field | Implemented mapping / remaining work |
| --- | --- |
| `SUBSYSTEMS` | Type `system`, stable reference identity/UUID; no observed active references; hydration deferred. |
| `SOFTWARE` | Type `software`; approved RAW lookup `SOFTWARE_NAME` → `title`, `DESCRIPTION` → `description`; 7/7 descriptions. Status deferred. |
| `HARDWARE` | Type `hardware`, stable reference identity/UUID; one reference has no proved hydration source. |
| `INTERCONNECTIONS` | Type `interconnection`; approved RAW lookup `INTERCONNECTION_NAME` → `title`, populated `DESCRIPTION` → `description`; status source absent. |
| `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM` | Same approved interconnection hydration; duplicates merge by governed identity/type. |
| `SAP_INTAKE_FORM_INTERCONNECTIONS` | Type `interconnection`, stable reference identity/UUID; no observed active references; hydration deferred. |

Identity/type and the approved partial hydration are live accepted [E4, E9].
**Excel scope reconfirmed 2026-09-10:** the recorded screenshot and component
contract evidence contains six `Reference` rows, all targeting
`system-security-plan.system-implementation.components[]`, with notes declaring
their component types [E1, E9]. All six reference handlers are implemented.
`SUBSYSTEMS` and `SAP_INTAKE_FORM_INTERCONNECTIONS` had no populated references
in the recorded run; that is not live proof of populated-input behavior.
No separate Excel row for `components[].status.state` is confirmed in this
evidence. Do not promote that conformance gap into the next mapping task.
The owner-approved partial hydration remains valid; it is not authorization
to add other unlisted child fields. This is a bounded evidence statement, not
a claim to have parsed the complete current workbook.

**Focused validation 2026-09-10:** 13 component-source-contract tests and 23
partial-hydration tests passed. Current six-row source/type contracts match the
recorded evidence. One prevention gap remains: `_component_mapping_type` checks
source, Reference type and notes but not the exact target path/field. A synthetic
row aimed at `components[].title` can still emit a whole component because its
owner is `components[]`. This does not prove a defect in the current accepted
six-row live mapping. No code change has been made; an exact-target guard and
regression test are proposed, not implemented. Two source fields remain without
populated live evidence, and two-SSP shared-ContentId graph integration is not
covered by the focused test files reviewed.

Interconnection lookup coverage is 1,428 titles and 968 descriptions: 460
descriptions remain absent. Component status is not emitted. These are missing
source/decision gaps, not completed components.

| Pending area | Concrete gap |
| --- | --- |
| `SSP.import-profile.href` | Approved profile URI and governed registry/config mapping required [E7, E11]. |
| `SSP.system-characteristics.system-information.information-types[]` | Registry, collection identity and title/description sources not established [E7, E11]. |
| `SSP.control-implementation` / `implemented-requirements[]` | Structural mapping, description and control IDs needed; screenshot control rows largely have blank paths, so model labels cannot supply targets [E1, E7]. |
| `HELPER_PTA_CALC` | Pending correction: clearer row 35 Notes specify a Calculated custom property at `SSP.system-characteristics.props[]`; current Cell 4 incorrectly skips it. Removing the skip alone is insufficient because the property dispatcher currently accepts only Extension Property. |
| `PACKAGE_TYPE_HELPER_CALC` | Intentionally excluded: separate row 36 Notes explicitly say transient calculation field - do not map. |
| Whole SSP acceptance | Required-source gaps, timestamp conformance and downstream branches remain; full assembled schema/constraint validation not established [E7, E11]. |

## Reporting and update rules

**Newest Excel evidence:** row 66's Notes contain an Option 1 property example
for `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`, not merely the generic
properties-or-calculation note. The example's control-implementation parent
does not allow properties in the pinned standard. A
[metadata property correction](checkpoints/2026-09-10_ssp_control_count_mapping_proposal.md)
is proposed to the mapping owner; target, value policy and namespace are not yet
approved. No code changed and no mapping completion is claimed for that row.

**Completed step:** Model **SSP**, assembly root `system-security-plan`, including
`system-security-plan.system-implementation.components[]`. All 2,813 mapped-scope
documents assembled successfully [E14]. No repeated run is needed. This is
assembly acceptance, not an additional field mapping or full SSP conformance.
Every subsequent mapping handoff names the model, full OSCAL path, source field
and transformation rule.

The earlier request for **ten additional SSP mapping rows** is retained as
history; the current priority is Source One across Excel-defined models, starting
with Assessment Results. The two System Characteristics corrections are parked
by owner direction. Clearer screenshots invalidate the earlier blanket
claim that every concrete evidenced row already has a handler. They do not yet
establish ten new executable contracts or a full-workbook completion percentage.
Do not relabel previous work as ten new rows or wait for a full export before
addressing the already evidenced corrections.

1. Update this register after each material implementation or accepted run and
   add a dated manager report under `docs/daily/YYYY-MM-DD.md`.
2. Record source field, original artifact path/type/Notes, implemented target,
   local verification, live evidence and remaining gap separately. Preserve
   conflicting artifact evidence rather than silently selecting a version.
3. Promote to live accepted only with a successful checkpoint for that release.
   Promote to payload proven only for the exact property/population checked.
4. Keep the last accepted baseline and latest failed attempt visible together.
   Test totals, graph counts, dispatch acceptance and source presence are not
   completed-field counts or final OSCAL conformance.
5. No overall completion percentage until workbook identity/version and scope
   reconcile. Historical audit: 608 loaded versus 609 screenshot rows, 104 SSP
   rows, 17 presence-reconciled and zero explicitly marked complete [E10].
   Do not sum this register's grouped rows into that historical denominator.
6. Daily reports state today's change, cumulative accepted progress, blockers
   and next step. Use aggregate facts; exclude source IDs and payload values.
   Preparing a report does not authorize sending it to a manager.

## Evidence index

- [E1: Excel screenshot transcription](MAPPING_ARTIFACT_SCREENSHOT_EVIDENCE_2026-09-09.md) — filtered view, not full workbook.
- [E2: Metadata field-level checks](checkpoints/2026-09-09_CELL7_CELL8_OUTPUT_CHECKPOINT.md) — exact document ID and configured OSCAL version proof.
- [E3: Timestamp source/readiness audit](checkpoints/2026-09-09_SSP_METADATA_LAST_MODIFIED_READINESS_AUDIT.md) — historical timezone findings; later preservation decision in E7.
- [E4: Accepted partial hydration run](checkpoints/2026-09-10_ssp_component_hydration_run.md).
- [E5: Property routing correction and local verification](checkpoints/2026-09-10_ssp_property_routing_fix.md).
- [E6: Accepted system-characteristics release](checkpoints/2026-09-09-ssp-system-characteristics-contract-run.md).
- [E7: Consolidated status and owner decisions](CURRENT_STATUS.md) — historical sections retain their original context.
- [E8: Executable field/role/component contracts](../notebooks/cells/04_parsing_transform_payload_helpers.py).
- [E9: Component route reconciliation](checkpoints/2026-09-10_ssp_component_source_routing_audit.md).
- [E10: Historical artifact scope/progress audit](checkpoints/2026-09-09_SSP_MAPPING_ARTIFACT_PROGRESS_AUDIT.md).
- [E11: Pinned minimum SSP contract](OSCAL_SSP_1_2_3_MINIMUM_CONTRACT.md).
- [E12: Authorization-date contract and implementation checkpoint](checkpoints/2026-09-10_ssp_authorization_date_mapping.md).
- [E13: Successful date/property release and next-ten scope](checkpoints/2026-09-10_ssp_date_property_run_accepted.md).
- [E14: Successful mapped-scope SSP JSON assembly](checkpoints/2026-09-10_ssp_mapped_scope_assembly_accepted.md).
- [E15: Newly posted mapping CSV transcription](transcribed_mapping_rows.csv) — reviewed at source commit `3533260a0c739444b02b0fc88a25cd0c3c456c87`; 51 records, not the complete original workbook.
- [E16: Assessment Results score mappings and accepted release](ASSESSMENT_RESULTS_START_HERE.md) — seventeen live-accepted fields; exact exclusions and source gaps; no repeat run required.
- [E17: Uploaded Assessment Results batch-one run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/683b0de290334cdc82675cda302f4244b10c9e0e/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-10) — all four fields emitted for 2,813 records; 16,878 nodes, 14,065 edges, zero contract/key errors and no writes. Snapshot at source commit `683b0de290334cdc82675cda302f4244b10c9e0e`.

- [E18: Uploaded seventeen-field AR run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/05fdb9e25bd7e28661f6fbd2d868d360c8d9e0bd/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-11) — 2,813 records; 52,586 nodes; 49,773 edges; 17 fields with populated evidence, seven with source gaps; zero contract/key errors or writes.

- [E19: Approved seventeen alternative-path additions](ASSESSMENT_RESULTS_START_HERE.md#approved-alternative-path-batch--seventeen-more-fields-pending-live) — owner approved the existing inline-property-per-observation representation on September 11; release `ar-observation-scores-v3-34-fields` is implemented but pending live. Original Excel/CSV unchanged; no registry or DIM/FACT writes.

- [E20: Blocked v3 thirty-four-field run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/c4279208c3d13554c5fe667755f0e8a2b6cabba5/docs/ssp_mapping_progress_checkpoint.md) — mapping/registry checks pass; 73,408 candidate nodes and 70,595 candidate edges with zero duplicate/dangling keys; two fields have 100 rejected values; outputs and writes false. Field totals reconcile; precise source shapes/reasons still unknown.

### Shared-engine design status

One shared mapping entry point, reusable mechanics and model-specific contracts
were discussed. This consolidation is **not implemented**. The accepted SSP
seven-cell pipeline and separate AR mapper remain unchanged; any future refactor
must preserve their accepted behavior. The registry paths required by those
accepted runs were present in Snowflake at execution. No pending insertion is
identified for accepted scopes; this is not blanket readiness for future models.

Latest 54-row/two-rejection evidence is the owner-supplied live report at remote
commit `23c61dc6c92804fb833ff9ede0c62ceb8c37f34a`,
`docs/live-snowflake-results.md`, summarized in E12. The daily progress heartbeat
is scheduled for 5 PM America/New_York; it should refresh evidence and prepare
the daily report, without independently sending manager messages.
