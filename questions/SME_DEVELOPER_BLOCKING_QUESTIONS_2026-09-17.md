# SME Questions That Actually Block OSCAL Mapping

Date: 2026-09-17
Branch reviewed: `simplify-metadata-boundary`
Baseline reviewed before this question pass: `e802f04d3c0767b2d0eea28934699366e0f18559`

Purpose: this is the short, email-ready list of questions where the developer cannot complete the mapping without a business/mapping decision. It is intentionally narrower than `SME_OPEN_QUESTIONS.md`.

NIST references used for this review:
- SSP Control Implementation v1.2.x reference: https://pages.nist.gov/OSCAL-Reference/models/v1.2.0/system-security-plan/json-definitions/
- SSP index showing implemented-requirement, responsible-role, and by-component structure: https://pages.nist.gov/OSCAL-Reference/models/v1.2.0/system-security-plan/json-index/
- Profile v1.2.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/profile/json-definitions/
- Assessment Results concepts: https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/
- Assessment Results observation reference: https://pages.nist.gov/OSCAL-Reference/models/v1.2.1/assessment-results/json-definitions/
- Catalog reference: https://pages.nist.gov/OSCAL-Reference/models/v1.2.0/catalog/json-definitions/
- Component Definition v1.2.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/component-definition/json-reference/

## 1. Allocated Controls -> SSP Control Implementation

The mapping document identifies Allocated Controls / Control Implementation, but it does not identify the exact Archer fields needed to build an OSCAL `implemented-requirement`.

**Ask the SME:**

> For each Allocated Control assigned to an Authorization Package, which Archer fields contain: (a) the actual control identifier, (b) the implementation narrative, (c) implementation status/origination, (d) responsible role/person, and (e) component-specific implementation details? Please identify the exact Archer field names we should use for the OSCAL `implemented-requirements[]`, `responsible-roles[]`, and `by-components[]` structure.

**Why this blocks development:** NIST models control implementation around an individual `implemented-requirement` that references a control and can carry statements, responsible roles, parameters, and by-component implementation. We cannot safely build those objects from summary/helper fields alone.

## 2. Control Implementation fields with no OSCAL path in the mapping sheet

The Control Implementation section contains many fields where the mapping document gives no exact OSCAL element path. Examples include `COUNT_OF_CONTROLS`, `COUNT_OF_FULLY_IMPLEMENTED_CONTROLS`, `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`, `INHERITED_CONTROL_SELECTION`, `INHERITABLE_CONTROLS`, `CONTROL_STANDARDS`, `MASTER_CONTROLS`, `CONTROL_SET_TO_ASSESS`, and similar fields.

**Ask the SME:**

> For the Control Implementation fields where the mapping sheet has no OSCAL element path, which ones are supposed to become actual OSCAL data, which ones should be calculated from `implemented-requirements[]`, and which ones are Archer-only summary/workflow values that should not be mapped? For any field that must be stored in OSCAL, please provide the intended OSCAL object/path.

**Why this blocks development:** NIST `control-implementation` is not a general container for arbitrary summary fields; its core structure is the implementation description, parameter settings, and `implemented-requirements[]`. We should not invent a `props[]` location when the mapping document does not specify one.

## 3. Profile `imports[].href` and control selection

The mapping document currently points `BASELINE_RECOMMENDATION` toward `profile.imports[]`, but the observed values are business labels such as LOE/baseline recommendations, not a resolvable Catalog/Profile reference.

**Ask the SME:**

> What exact Archer field or relationship gives us the actual Catalog or Profile resource that should populate OSCAL `profile.imports[].href`? Please identify the source field that contains or can resolve to the Catalog/Profile URI/reference. Also, what Archer field tells us whether that import should use `include-all` or specific `include-controls`?

**Why this blocks development:** NIST defines `import.href` as a resolvable reference to the Catalog/Profile being tailored, and the import must then select controls using `include-all`, `include-controls`, and/or exclusions. A baseline recommendation label by itself is not enough to construct that structure.

## 4. Profile `ADD_OVERLAY` -> import vs merge vs modify

The mapping document says `ADD_OVERLAY` may affect Profile import, merge behavior, or modify/alters, but it does not define which source values mean which behavior.

**Ask the SME:**

> For `ADD_OVERLAY`, what are the possible Archer values and what does each value mean? Specifically, which values mean “select/import controls,” which mean “restructure/merge controls,” and which mean “modify/tailor control content or parameters”?

**Why this blocks development:** NIST treats Profile `import`, `merge`, and `modify` as different operations. We cannot route one Archer field among them without an explicit business rule.

## 5. `AUTHORIZATION_DECISION` conflicts with OSCAL operational status

The mapping document points both `OPERATIONAL_STATUS` and `AUTHORIZATION_DECISION` toward `system-security-plan.system-characteristics.status.state`.

**Ask the SME:**

> Is `AUTHORIZATION_DECISION` intended to represent the system's operational lifecycle state, or an authorization/ATO decision? If it is an authorization decision, where do you want that decision represented in OSCAL instead of `system-characteristics.status.state`?

**Why this blocks development:** NIST defines `system-characteristics.status.state` as the system's current operating status (for example operational, under-development, under-major-modification, disposition, or other). We should not write two different business concepts into the same singleton OSCAL field.

## 6. Assessment Results rows where the mapping sheet gives alternative meanings

The mapping document still leaves `RISK_ACCEPTANCE_RBDS` as `observations[]` **or** `props[]`, and `RISK_ASSESSMENT_REPORT` is not defined as an observation, property, link, or report/evidence reference.

**Ask the SME:**

> For `RISK_ACCEPTANCE_RBDS`, is this an actual assessment observation produced by an assessment activity, or is it a package/result-level business value? For `RISK_ASSESSMENT_REPORT`, is the source value the report itself, a URL/document reference to the report, or a result/score? Please confirm the intended OSCAL representation for these two fields.

**Why this blocks development:** NIST uses an Observation for an individual assessment observation/evidence and gives observations their own description, method, subject/origin, and evidence structure. A package-level value or report reference should not be promoted to an Observation just because `observations[]` is available.

## 7. Source 2 `SOURCE_DESCRIPTION` and `INFORMATION` both target Catalog metadata remarks

The Source 2 mapping document maps both `SOURCE_DESCRIPTION` and `INFORMATION` to `catalog.metadata.remarks`.

**Ask the SME:**

> Which field should be the authoritative value for `catalog.metadata.remarks`: `SOURCE_DESCRIPTION` or `INFORMATION`? Where should the other field be represented if both need to be retained?

**Why this blocks development:** these are two separate source fields targeting one singleton OSCAL member. We cannot safely overwrite, concatenate, or choose precedence without an explicit decision. NIST also states that `remarks` should not be used as a general bucket for arbitrary data.

## 8. Source 2 `CONTROL_PROCEDURES` is ambiguous between Catalog and Component Definition

The Source 2 mapping document labels `CONTROL_PROCEDURES` as `Catalog or Component Definition`, and the supplied path text is incomplete.

**Ask the SME:**

> What does `CONTROL_PROCEDURES` represent in Archer: the actual requirement/procedure text that is part of a control, or a separate documented procedure that implements/supports controls? If it is control requirement text, confirm the Catalog control/part mapping. If it is a separate documented procedure, confirm that it should be modeled as a documentary component in Component Definition.

**Why this blocks development:** NIST Catalog represents controls and their statement/part content, while Component Definition explicitly supports documentary components such as processes, procedures, and policies. We need the business meaning before choosing the model.

## Mapping-document text needed

For any Source 2 row where the supplied worksheet transcription is visibly clipped or the OSCAL model/path is incomplete, please provide the original untruncated row from the authoritative mapping workbook. We should not reconstruct a missing path from a screenshot.

## Deliberately not included in this email

This short list does **not** ask about generic ContentId/LevelId routing, warehouse/system helper fields, timestamps/timezones, routine links/back-matter handling, or already-resolved implementation mechanics. Those are not the current SME decisions preventing the developer from mapping the fields above.
