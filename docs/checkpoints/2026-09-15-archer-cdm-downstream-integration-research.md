# Archer CDM downstream integration research

Date: 2026-09-15
Repository branch: `simplify-metadata-boundary`
Sanitization: company and individual names are intentionally replaced with `Company XYZ` or role-neutral wording.

## Purpose and evidence boundary

Preserve the Company XYZ Archer CDM research and business-process walkthrough so later OSCAL work can refer to durable repository evidence instead of chat memory. This is architectural/research evidence only. It does not approve OSCAL mappings, change mapper code or registry rows, establish Snowflake state, or prove physical cardinalities that have not been verified from source metadata.

Public Archer documentation supports conceptual architecture. Company XYZ Archer metadata is authoritative for actual field direction, FK/XREF design, single-versus-multi-value behavior, and cardinality.

## Core Archer CDM

Core Assessment & Testing concepts:

- Business
- SBU
- Entity
- Facility
- Compliance Engagement
- Control Procedure
- Control Testing Result
- Control Standard
- Evidence Repository
- Policy Level 1 / 2 / 3
- Authoritative Source / Topic / Section / Sub-section

Relationships under review:

- Control Procedure -> Policy Level 3
- Policy Level 3 -> Control Standard
- Direct Control Procedure <-> Control Standard only when Company XYZ Archer stores it independently
- Control Testing Result -> Control Standard for the specific evaluated/failed standard only when stored by the source

A Procedure -> Standard relationship derivable through Policy Level 3 should not automatically be duplicated physically. Explicit source relationships may remain independent even when another path is derivable.

## Company-specific policy hierarchy

The company implementation uses:

`Policy Level 1 -> Policy Level 2 -> Policy Level 3`

The levels have their own hierarchy and should not be described as connected only through Control Standards. This hierarchy is a Company XYZ implementation fact under review, not a claim about the newest generic Archer Core product structure.

The external-requirement hierarchy discussed is:

`Source -> Topic -> Section -> Sub-section`

Authoritative Source is the umbrella concept. Requirement/version specificity matters, not only the source name.

## Business objective

The assessment process connects three questions:

1. What is the organization required to do?
2. Is it actually doing those things?
3. What happens when a gap is found?

Site-assessment story:

`Choose a facility -> plan its assessment -> select relevant tests -> perform them -> document results -> manage gaps.`

Foundational distinctions:

- Generated test != performed test.
- Requirement mapping != requirement satisfaction.
- Completed testing != complete compliance.
- Closed assessment != all discovered issues remediated.

The business needs traceability from requirement -> assessment -> evidence -> gap -> response.

## Plain-language business concepts

Illustrative access-review example:

- Control: the actual safeguard/business activity, such as reviewing user access and removing unnecessary permissions.
- Control Standard: the specific requirement or expectation being supported.
- Control Procedure: reusable definition describing what to inspect/test.
- Compliance Engagement: assessment wrapper for a target and period.
- Control Testing Result: engagement-specific working/test/result record generated from a procedure.
- Evidence: information supporting the assessor's conclusion.

Control = what the business does. Procedure = what to check. Testing Result = engagement-specific assessment work/result.

## Assessment lifecycle

### A. Compliance Engagement

The engagement is the assessment wrapper/envelope. It organizes target, people, dates, scope, tests, and conclusions. One engagement can contain many Control Testing Results.

### B. Business context and facility

The walkthrough selected Business, SBU, Entity, and Facility. For the site-assessment flow, Facility is the assessment target and Compliance Engagement is the assessment of that target.

Business selection filtering facility choices is application behavior; it does not by itself prove the entire enterprise hierarchy. Demo selections are not certified hierarchy evidence.

### C. Scope

Scoping routes discussed:

- Previous engagement
- Control set/library
- Policy
- Authoritative source
- Tier 1 / pre-assessment information

Tier 1 details were not established and must not be invented. A screenshot reportedly mentioned four options while the walkthrough discussed five; resolve that discrepancy against the actual company application.

### D. Control Set / version

A Control Set is a collection of procedures. Its version identifies the edition used for an assessment. Changes in procedure/test counts between engagements may reflect scope or version changes and are not automatically data defects. Demonstrated counts such as 176/177 are examples, not universal rules.

### E. Refine scope

Available in master library != selected for this engagement. The initial checklist can be adjusted for the engagement.

### F. Generate tests

Control Procedure is reusable/master. Archer creates an engagement-specific Control Testing Result from it. Generation creates the assessment work item; it does not mean testing has already occurred.

### G. Perform/review tests

Outcomes discussed include Implemented, Partially implemented, Not implemented, Not tested, and Not applicable where used.

`Not tested` is not a pass. `Not applicable` is not automatically equivalent to Implemented. Testing progress and testing outcome are separate concepts.

### H. Close/wrap up

Entering conclusions and closing the engagement means the assessment activity has reached its workflow end. It does not prove every resulting issue is fixed. Exact company closure rules with outstanding issues were not established by the walkthrough.

## Background processing

Save/close/wait/reopen behavior can reflect asynchronous Archer processing for activities such as scoping or generating test records. That processing is not the assessor performing the test.

Keep system stages separate:

- Archer creates/updates business records.
- Matillion moves data into Snowflake.
- Power BI consumes reporting data.

A delay/failure in one stage does not prove failure in another. Demonstration timing is environment-specific, not an SLA.

## Evidence

Evidence answers: `Why should someone trust this result?`

Reuse is valid only when target, scope, period, and conclusion context support reuse. Preserve these questions:

- What does the evidence demonstrate?
- Which target does it cover?
- Which period does it cover?
- Which assessment conclusion does it support?

Evidence Repository is cross-cutting and may support control implementation, testing, engagement evidence requests, remediation, or exception decisions depending on the company implementation. Do not assume it belongs only beneath Control Testing Result.

## Gap / Issues Management flow

The company walkthrough supports the business flow:

`Test identifies a gap -> Deviation records the specific failure -> Finding manages the issue -> Remediation and/or Exception addresses the response.`

### Deviation

Deviation represents the specific requirement-level failure connected to an assessment result and the Control Standard requirement that was not met. It identifies what specifically failed rather than declaring an entire policy/control area failed.

Conceptually:

`Control Testing Result -> Deviation -> Finding`

and potentially:

`Deviation -> Control Standard`

The walkthrough establishes the business connection but not universal 1:1 cardinality. Physical relationships remain metadata-verification items.

### Finding

Finding is the managed issue/deficiency. It can carry affected area, description, ownership, status, and response context. Findings may originate from assessment/control testing but also from audits or manual identification. Control Testing Result therefore must not be the mandatory sole source of every Finding.

Deviation = what specifically failed in the test/requirement context. Finding = the broader issue the organization manages.

### Remediation Plan

Answers `How will we fix it?` and can document actions, owners, and timing. The research indicates Archer can support many-to-many Finding/Remediation relationships; the actual Company XYZ configuration must be verified.

### Remediation Plan Status Update

Tracks progress/status of remediation activity and remains distinct from the Remediation Plan itself.

### Exception Request

Represents a request to formally accept a departure from normal requirement/remediation expectations. It is subject to review, not automatic approval. An approved exception is not the same as repairing the control; it records an authorized decision and may include rationale, conditions, time limits, or compensating safeguards.

### Risk

Finding != Risk.

- Finding: known issue/deficiency.
- Risk: possible adverse consequence/exposure.

Keep Risk Register as a separate domain. Do not add a direct Finding <-> Risk Register relationship unless company metadata confirms it.

## Control Standards as requirement-level connector

Company examples indicate:

- Procedures link to Policy Level 3.
- Procedures may also link directly to Control Standards.
- Control Standards connect into the Authoritative Source structure.

Business meaning:

`This test/procedure supports this internal requirement, which is related to these external requirements.`

Control Standards also allow the assessor to identify the precise failed requirement. If an access-review area has requirements to perform the review, remove unnecessary access, and retain evidence, failure of only the access-removal requirement should not be represented as failure of the whole policy area.

## Assess once, comply many

The direction is to reduce repeated assessment work where requirements overlap.

Keep three concepts separate:

- Mapping: documented relationship between requirements/controls.
- Coverage: selected assessment content addresses relevant requirements.
- Compliance result: evidence/results support a conclusion about whether requirements are met.

Mapping is not proof of compliance. Complete mapping coverage on a chart is not complete compliance. Broader reuse/automation was described as a direction of travel, not proof that every current assessment already achieves it.

## Strong cardinality/business rule from the walkthrough

- One Control Testing Result belongs to one Compliance Engagement.
- One Compliance Engagement can contain many Control Testing Results.
- One reusable Control Procedure can generate many Control Testing Results across engagements and time.

Therefore:

`Compliance Engagement 1 -> N Control Testing Result`

`Control Procedure 1 -> N Control Testing Result`

Seeing several engagement-specific results on a Control Procedure's Testing tab is expected and does not mean one Control Testing Result belongs to multiple engagements.

## A&A / Public Sector branch

Concepts under review:

- Authorization Package
- Allocated Control
- Finding
- POA&M
- Milestone

Keep Allocated Control distinct from Control Procedure unless company metadata proves otherwise. Their grains differ: Control Procedure is reusable/master testing logic; Allocated Control is closer to an assigned/instantiated control in an authorization context.

Conceptual direction only:

`Authorization Package -> Allocated Control -> assessment/authorization context -> Finding -> POA&M -> Milestone`

Do not lock arrows/cardinalities from generic documentation alone. Company relationship metadata must establish actual cross-reference direction and single/multi-value behavior.

## Legacy DPF crosswalk

Treat legacy DPF Control Standards as a migration/crosswalk concern, not another current-state hierarchy level.

Recommended conceptual pattern:

`LEGACY_DPF_CONTROL_STANDARD -> CONTROL_STANDARD_CROSSWALK -> CURRENT_CONTROL_STANDARD`

Do not contaminate the current Control Standard entity with many legacy identifiers unless a source requirement demands it. Crosswalk cardinality/attributes remain proposals until actual DPF/FCP evidence is reviewed.

## OSCAL intersection

Keep source CDM and OSCAL warehouse models distinct:

`ARCHER CDM -> mapping/transformation -> OSCAL representation`

Relevant current OSCAL evidence:

- `FINDINGS` exists in Assessment Results with proposed target `assessment-results.results[].findings[]`, but remains DEFERRED pending finding identity/reference semantics.
- SSP Control Implementation contains `ALLOCATED_CONTROLS`, `CONTROL_STANDARDS`, `MASTER_CONTROLS`, `ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE`, inheritance fields, assessor fields, and POA&M-related counts, but all 42 Control Implementation mappings remain DEFERRED.
- POA&M is conceptually downstream and has an approved source-reference mapping, but accepted evidence remains PREVIEW only, not verified COMMIT/readback.

## Modeling rules

1. Public Archer documentation supports conceptual architecture, not company physical truth.
2. Company walkthrough evidence supports business meaning; source metadata still governs physical implementation.
3. Company Archer metadata determines actual relationships, direction, cardinality, FK/XREF, and single/multi-value behavior.
4. Explicit source relationships may be modeled independently even when another path derives the association.
5. Do not materialize derived relationships automatically when doing so creates conflicting truths.
6. Keep current-state entities clean and isolate legacy crosswalk concerns.
7. Preserve grain: Finding != Risk; Allocated Control != Control Procedure unless proven; Exception Request != Remediation Plan; Deviation != Finding.
8. Generated test != performed test.
9. Requirement mapping != requirement satisfaction.
10. Completed assessment work != all discovered issues remediated.

## Existing OSCAL evidence boundaries

- Historical SSP committed/read-back acceptance does not prove the later `DAILY_LOSS_AMOUNT_FROM_OUTAGE` mapping.
- Historical AR30 committed/read-back acceptance does not prove later AR32/null-preservation/leading-underscore changes.
- POA&M has accepted PREVIEW evidence, not verified COMMIT/readback.
- Assessment Plan setup code and corrected registry SQL do not prove successful live setup or completed preview/commit.
- The 42 SSP Control Implementation mappings remain deferred until explicitly reviewed and approved.

## Immediate next checkpoint

Before changing Erwin cardinalities or enabling new OSCAL mappings, inspect Company XYZ Archer metadata for downstream applications and relationships. Capture:

- application/table
- primary identifier
- related-record field
- target application
- single-value versus multi-value
- relationship direction
- directly stored versus derivable

Priority objects:

Business; SBU; Entity; Facility; Compliance Engagement; Control Procedure; Control Set/Version; Policy Levels 1/2/3; Authoritative Source; Topic; Section; Sub-section; Control Standard; Control Testing Result; Evidence Repository; Deviation; Finding; Remediation Plan; Remediation Plan Status Update; Exception Request; Authorization Package; Allocated Control; Risk Register; POA&M; Milestone; Legacy DPF Control Standard.

This is read-only evidence collection. Do not infer missing values or approve mappings from conceptual similarity alone.

## Source completeness caveat

The owner-provided September 15 synthesis ended mid-sentence after `Also, reading the same result from the fa...`. No missing continuation is reconstructed. If supplied later, append it as a dated continuation rather than guessing.
