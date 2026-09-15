# Archer CDM downstream integration research

Date: 2026-09-15
Repository branch: `simplify-metadata-boundary`
Branch head inspected before the original checkpoint: `2a0e018c6222b39d8f0d28800ba58373684aed64`

## Purpose

Preserve the Archer CDM research discussed in the OSCAL project so later modeling work does not depend on chat memory alone. This document is architectural/research evidence only. It does not approve new OSCAL mappings, change runtime code, change registry rows, or prove any Snowflake execution.

This checkpoint also preserves the detailed Company XYZ Archer business-process explanation derived from the company walkthrough and the follow-up synthesis supplied by the owner on September 15, 2026. That material clarifies business meaning and workflow but does not replace source metadata or establish physical relationship cardinalities by itself.

## Core Archer CDM context

The current Archer conceptual model under discussion contains a core Assessment & Testing area around Business/SBU/Entity/Facility context, Compliance Engagement, Control Procedure, Control Testing Result, Control Standard, Evidence, and policy/authoritative-source context.

Company XYZ-specific policy relationships currently under review are:

- Control Procedure -> Policy Level 3
- Policy Level 3 -> Control Standard
- Direct Control Procedure <-> Control Standard only if Company XYZ Archer stores that relationship independently
- Control Testing Result -> Control Standard for the specific standard evaluated/failed, if the company source stores that relationship

These relationships must remain semantically distinct. A Procedure -> Standard path derivable through Policy Level 3 should not automatically be duplicated as a physical relationship unless Archer stores it independently.

## Important version distinction

The Company XYZ implementation appears to use a Policy Level 1 -> Policy Level 2 -> Policy Level 3 hierarchy. That hierarchy should be modeled as a Company XYZ/current-client implementation detail, not as a claim about the newest generic Archer Core Compliance architecture.

Current public Archer material has evolved toward flatter policy structures and regulatory constructs such as authoritative sources/citations/obligations/sub-obligations around Control Standards. Public Archer documentation is useful for conceptual architecture, but Company XYZ Archer metadata is authoritative for actual physical relationships, field direction, and cardinality.

# Company XYZ Archer business story preserved from the September 15 walkthrough synthesis

## Business objective

The business goal is to connect three questions:

1. What is the organization required to do?
2. Is it actually doing those things?
3. What needs to happen when a gap is found?

For the Company XYZ site-assessment process demonstrated in the company walkthrough, the business story is:

`Choose a facility -> plan its assessment -> select the relevant tests -> perform them -> document the results -> manage anything that needs fixing.`

Two distinctions are foundational:

- Generating a test does not mean the test has been performed.
- Mapping a requirement does not mean the requirement has been satisfied.

The business needs traceability from requirement -> assessment -> evidence -> gap -> response.

## Plain-language GRC framing

- Governance: who sets expectations, makes decisions, and is accountable?
- Risk: what could go wrong and how serious could it be?
- Compliance: are the applicable requirements being met?

A simple illustrative access-review example can be used across the model:

- Control: managers review user access and remove unnecessary permissions.
- Control Standard: access must be reviewed according to the applicable requirement.
- Control Procedure: inspect access-review records and check whether required follow-up occurred.
- Compliance Engagement: the access/security assessment for a facility during a particular period.
- Control Testing Result: the engagement-specific test record for that assessment.
- Evidence: review records, approvals, account lists, and completed access-removal requests.

The control is what the business does. The procedure explains what to check. The testing result is the engagement-specific working/result record.

# Assessment lifecycle from the company walkthrough

## A. Create the Compliance Engagement

The Compliance Engagement acts as the wrapper/envelope/assessment folder. It organizes the target, people, dates, scope, tests, and conclusions.

Business question answered:

`What assessment are we carrying out, and what does it cover?`

It is not one individual test. One engagement can contain many Control Testing Result records.

## B. Identify business context and facility

The walkthrough selected Business, SBU, Entity, and Facility.

Their business roles are:

- Business: which business unit does the assessment relate to?
- SBU: which strategic business subdivision does it relate to?
- Entity: which organizational entity provides further context?
- Facility: which site is being assessed?

For the site-assessment workflow shown, Facility is the assessment target and Compliance Engagement is the assessment of that target.

The walkthrough showed business selection filtering the available facility choices. That is an application-selection behavior; it is not by itself proof of the entire enterprise hierarchy. Demo selections should not be treated as certified hierarchy relationships.

## C. Decide the scope

Scope means: what will be assessed this time?

The company walkthrough described several possible starting routes:

- Previous engagement
- Control set/library
- Policy
- Authoritative source
- Tier 1 / pre-assessment information

Tier 1 details were not established in the walkthrough and should not be invented.

A documentation discrepancy was noted: an instruction screenshot reportedly mentioned four scoping options while the walkthrough discussed five. This is a documentation/configuration question to resolve against the actual Company XYZ application, not a reason to alter the overall business model.

## D. Choose the control-set version

A Control Set is a collection of procedures used together. A version identifies which edition of that collection applies.

Business meaning:

`We are using this edition of the assessment checklist.`

The assessment scope can change between versions. Therefore a difference in the number of tests between engagements is not automatically a data defect.

The 176/177 test counts seen in demonstrations are examples from those records, not universal business rules.

## E. Refine the scope

The selected procedures can be reviewed, added, or removed for the specific engagement.

Important distinction:

- Available in the master library != selected for this engagement.
- Standard starting checklist != final engagement-specific checklist.

## F. Generate test records

This is a critical modeling point.

The company walkthrough described Control Procedure as the reusable/master definition. Archer then creates an engagement-specific Control Testing Result from that procedure.

Example:

- Master: `Check user-access reviews.`
- Generated test: `Check user-access reviews for Facility A in this engagement.`

At generation time the test record exists, but the assessor may not yet have performed the assessment work.

Therefore `Control Testing Result` is also a working assessment record; its name does not imply that a completed conclusion already exists.

## G. Perform and review tests

The assessor examines information, reviews evidence, records observations, and selects an outcome.

Outcomes discussed in the walkthrough include:

- Implemented
- Partially implemented
- Not implemented
- Not tested
- Not applicable, where used

Important distinctions:

- `Not tested` is not a pass.
- `Not applicable` is not automatically the same as implemented.
- Testing progress and testing outcome are separate concepts.
- A test can be completed while identifying a compliance gap.
- Completed testing does not mean complete compliance.

## H. Wrap up the engagement

The workflow ends with conclusions and engagement closure.

Business distinction:

`We finished assessing the facility` is not the same as `every issue found at the facility has been fixed.`

The walkthrough did not establish the exact Company XYZ business rules for closing an engagement with outstanding findings/issues, so those rules must not be inferred from status labels alone.

# Background processing / asynchronous Archer behavior

The walkthrough showed save/close/wait/reopen behavior for some operations. Selecting Ready and saving can trigger background activities such as scoping or generating test records.

Business meaning:

`The user submitted the selection and the application is processing it.`

This background processing is not the same as the assessor performing the test.

Keep the downstream systems separate:

- Archer creates/updates business records.
- Matillion moves data into Snowflake.
- Power BI consumes reporting data.

Delay or failure in one stage does not automatically prove failure in the others.

Any timing mentioned for demonstration jobs running every few minutes should be treated as environment-specific, not a contractual SLA.

# Evidence business meaning

Evidence answers:

`Why should someone trust this result?`

For an access-review example, evidence might include account listings, documented reviews, approvals, and records proving unnecessary access was removed.

Evidence can be reusable only when its scope, target, and time period make that reuse valid.

Retain these business questions:

- What does the evidence demonstrate?
- Which target does it cover?
- Which time period does it cover?
- Which assessment conclusion does it support?

The walkthrough establishes evidence as part of the process but does not establish every physical Evidence-to-Test cardinality in the Company XYZ data model.

# Issues / gap-management flow from the company walkthrough

The owner's supplied synthesis records the Company XYZ demonstrated flow as:

`Test identifies a gap -> Deviation records the specific failure -> Finding manages the issue -> Remediation and/or Exception addresses the response.`

This is important Company XYZ-specific business evidence and qualifies the earlier conservative note that Deviation was unverified in generic Archer documentation.

## Deviation

In the company walkthrough, Deviation represents the specific requirement-level failure connected to the assessment result and the Control Standard requirement that was not met.

Illustrative example:

`Required follow-up from the access review was not completed.`

Business purpose:

- identify the specific failed requirement
- avoid an imprecise statement such as `access management failed`
- connect the test-specific gap to the relevant standard/requirement

The walkthrough establishes the business connection, but it does not prove one-to-one cardinality between Test Result, Deviation, Finding, or Control Standard.

Therefore the conceptual Company XYZ flow may include:

`Control Testing Result -> Deviation -> Finding`

and

`Deviation -> Control Standard`

but physical cardinalities must still come from actual relationship metadata.

## Finding

Finding is the managed issue/deficiency.

It may contain business context such as affected area, issue description, ownership, status, and required response.

Findings can originate from assessments and control testing, but may also originate from audits or manual identification. Therefore Control Testing Result should not be modeled as the only possible Finding source.

Business distinction:

- Deviation = what specifically failed in the test/requirement context.
- Finding = the broader issue the organization manages.

## Remediation Plan

Remediation Plan answers: `How will we fix it?`

It can document actions, ownership, and timing.

The supplied synthesis notes that Archer can support many-to-many relationships between findings and remediation plans. The exact Company XYZ configured relationship still requires source metadata verification.

## Exception Request

Exception Request represents a request to formally accept a departure from the normal requirement/remediation expectation.

It is subject to review and is not automatic approval. An approved exception is not the same as fixing the control. It records an authorized decision about the gap, potentially with rationale, conditions, time limits, and compensating safeguards.

## Risk

Finding and Risk are distinct:

- Finding: a known issue/deficiency.
- Risk: a possible adverse consequence/exposure.

Example:

- Finding: unnecessary access was not removed.
- Risk: someone could use that access inappropriately.

This distinction supports keeping Risk Register separate from Finding in the CDM.

# Policy and authoritative-source business meaning

## Internal policy hierarchy in Company XYZ

The walkthrough uses:

`Policy Level 1 -> Policy Level 2 -> Policy Level 3`

This is the Company XYZ implementation hierarchy and should be preserved as such.

The levels have their own hierarchy. They should not be described as connected only through Control Standards.

The company walkthrough evidence indicates that the policy levels are represented separately in the Snowflake extract.

## Authoritative Sources

The external-requirement side was described as:

`Source -> Topic -> Section -> Sub-section`

Examples mentioned include NIST, ISO, HIPAA, and CMMC. `Authoritative Source` is the umbrella business term; the underlying instruments are not all the same kind of source.

The important business meaning is requirement and version specificity, not just source name.

## Control Standards as requirement-level connector

The company walkthrough emphasized Control Standards as a requirement-level linking structure.

In the Company XYZ examples:

- Procedures link to Policy Level 3.
- Procedures may also have direct links to Control Standards.
- Control Standards connect into the Authoritative Source structure.

Business meaning:

`This test/procedure supports this internal requirement, which is related to these external requirements.`

Control Standards also allow the assessor to identify the exact requirement that failed instead of declaring an entire policy area failed.

Example:

1. Perform access review.
2. Remove unnecessary access.
3. Retain evidence.

If only #2 fails, the useful conclusion is that the access-removal requirement failed, not that the whole policy area failed.

# Assess once, comply many

The company direction is to reduce repeated assessment work where requirements overlap.

Important distinctions:

- Mapping = a documented relationship between requirements/controls.
- Coverage = the selected assessment content addresses relevant requirements.
- Compliance result = evidence/results support a conclusion that applicable requirements are met or not met.

A mapping is not itself proof of compliance.

Likewise, an Authoritative Sources mapping chart showing complete mapping coverage should not be read as complete compliance.

The walkthrough indicated that the broader reuse/automation goal is not yet fully realized. Treat it as a direction of travel, not a claim that all Company XYZ assessments already achieve full reuse.

# Explicit cardinality/business rule corrected in the company walkthrough

This is one of the strongest business rules captured in the walkthrough:

- One Control Testing Result belongs to one Compliance Engagement.
- One Compliance Engagement can contain many Control Testing Results.
- One reusable Control Procedure can generate many Control Testing Results across engagements and time.

Illustrative example:

| Test record | Engagement | Master procedure | Outcome |
| --- | --- | --- | --- |
| Test A | Facility A assessment | Access-review procedure | Implemented |
| Test B | Facility B assessment | Access-review procedure | Partially implemented |
| Test C | Facility A later assessment | Access-review procedure | Not tested yet |

Therefore:

`Compliance Engagement 1 -> N Control Testing Result`

`Control Procedure 1 -> N Control Testing Result`

The Control Procedure is reusable. The Control Testing Result is specific to the engagement in which that test was generated/performed.

Seeing several engagement-specific results on a Control Procedure's Testing tab is expected and does not mean a single Control Testing Result belongs to multiple engagements.

## Source completeness caveat

The owner's pasted September 15 ChatGPT response ended mid-sentence after:

`Also, reading the same result from the fa...`

No missing continuation is reconstructed here. If the remaining text is supplied later, append it as a dated continuation rather than guessing its content.

# Issues Management branch

Treat Issues Management as a downstream domain attached to the core rather than redesigning the core around it.

Primary concepts:

- Deviation (Company XYZ demonstrated business flow; physical metadata/cardinality still to verify)
- Finding
- Remediation Plan
- Remediation Plan Status Update
- Exception Request

Conceptual workflow now supported by the combined company walkthrough and generic Archer research:

- Control Testing Result may produce one or more Deviations when specific requirements fail.
- A Deviation may point to the specific Control Standard that was not satisfied.
- A Finding can be created/managed from the gap context.
- Findings may also originate from other sources such as audits/manual processes.
- Remediate path: Finding -> one or more Remediation Plans -> Remediation Plan Status Updates.
- Accept-risk path: Finding -> Exception Request.

Do not force Control Testing Result to be the mandatory sole parent