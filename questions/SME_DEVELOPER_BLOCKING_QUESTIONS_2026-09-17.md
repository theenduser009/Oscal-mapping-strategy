# SME Questions — Technical OSCAL Mapping Blockers Only

Date: 2026-09-18
Branch reviewed: `simplify-metadata-boundary`
Baseline reviewed before this question pass: `001615b38642266d203e54bd7f0031cae7b77b80`

This supersedes the earlier wording in this file. The questions below are intentionally limited to places where the current mapping document cannot be compiled or emitted safely by the Python mapper because the target path is missing, ambiguous, duplicated, or inconsistent with the NIST OSCAL schema. They are not requests for general business-process explanation.

NIST references used:
- SSP: https://pages.nist.gov/OSCAL-Reference/models/v1.2.0/system-security-plan/json-definitions/
- Profile: https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/profile/json-definitions/
- Assessment Results: https://pages.nist.gov/OSCAL-Reference/models/v1.2.1/assessment-results/json-definitions/
- Catalog: https://pages.nist.gov/OSCAL-Reference/models/v1.2.0/catalog/json-definitions/

## 1. Allocated Controls -> SSP `implemented-requirements[]`

The mapping document identifies Allocated Controls / Control Implementation, but it does not provide the exact source-field-to-OSCAL-path mapping needed to construct an `implemented-requirement`.

**Question:**

> For an Allocated Control record, please provide the exact Archer field names and OSCAL target paths for the control identifier and the fields that should populate `control-implementation.implemented-requirements[]`, including any statement, `responsible-roles[]`, and `by-components[]` mappings that are intended.

**Technical blocker:** NIST models Control Implementation around individual `implemented-requirement` objects tied to controls. The current mapping does not provide enough exact field/path metadata for the Python compiler to build that structure without inventing mappings.

## 2. Control Implementation rows with blank/unspecified OSCAL paths

The Control Implementation mapping contains many rows with no exact OSCAL element path, including `COUNT_OF_CONTROLS`, `COUNT_OF_FULLY_IMPLEMENTED_CONTROLS`, `COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`, `INHERITED_CONTROL_SELECTION`, `INHERITABLE_CONTROLS`, `CONTROL_STANDARDS`, `MASTER_CONTROLS`, `CONTROL_SET_TO_ASSESS`, and others.

**Question:**

> For every Control Implementation row whose OSCAL path is blank or marked `Unspecified`, please provide one exact OSCAL target path and mapping type, or mark the row as not mapped/derived-only. If a value is intended to be calculated from `implemented-requirements[]` rather than stored, please mark it as calculated rather than assigning a new OSCAL path.

**Technical blocker:** the Python mapping contract requires one executable target path and transform/representation decision. It cannot compile `Unspecified` into a deterministic OSCAL node or property.

## 3. Profile `imports[].href`

The mapping document points `BASELINE_RECOMMENDATION` toward `profile.imports[]`, but it does not provide a value that can be emitted as `imports[].href`.

**Question:**

> Please identify the exact Archer source field/relationship and transformation that should populate `profile.imports[].href`, and the source mapping that supplies `include-all` or the specific `include-controls` selection.

**Technical blocker:** NIST defines `import.href` as a URI reference to the Catalog/Profile being imported, and the import contains the control-selection directives. A label alone cannot be emitted as a valid Profile import reference. citeturn678067view1

## 4. Profile `ADD_OVERLAY` has multiple possible OSCAL destinations

The mapping document says `ADD_OVERLAY` may route to Profile import, merge, or modify/alters, but it does not provide a deterministic value-to-path rule.

**Question:**

> Please provide the exact mapping rule for `ADD_OVERLAY`: for each source value, which OSCAL path should be populated — `imports[]`, `merge`, or `modify`/`alters` — and what transform should be applied?

**Technical blocker:** NIST treats `import`, `merge`, and `modify` as separate Profile structures. The mapper cannot route one source field to multiple structural destinations without an explicit rule. citeturn678067view0 citeturn920150view2 citeturn920150view3

## 5. Two SSP source fields target the same singleton `status.state`

The mapping document maps both `OPERATIONAL_STATUS` and `AUTHORIZATION_DECISION` to `system-security-plan.system-characteristics.status.state`.

**Question:**

> Please provide one canonical target decision for these two rows: which field owns `system-security-plan.system-characteristics.status.state`, and what exact OSCAL path should the other field use (or should it be marked not mapped)? If both are intentionally mapped to `status.state`, please provide the deterministic precedence/crosswalk rule.

**Technical blocker:** NIST defines System Characteristics `status` as the system's operational status and exposes one `state` value. The mapper cannot safely write two independently populated source fields into the same singleton member. citeturn454619view1

## 6. SSP Metadata rows still marked TBD

The mapping document leaves `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER` as a generic metadata property with no property name, and leaves the following responsible-party mappings as TBD: `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO`, `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE`, `INFORMATION_SYSTEM_ADMINISTRATOR_ISA`, and `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR`.

**Question:**

> Please provide the exact property name for `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER`. For each of the four TBD responsible-party rows, please provide the exact OSCAL `role-id` to use, or mark the row not mapped.

**Technical blocker:** the mapper can already create metadata properties and responsible-party relationships, but these rows are missing the target metadata needed to compile them deterministically. The source document itself marks them TBD. fileciteturn471file0L2-L6

## 7. Assessment Results rows with alternative or missing target paths

The mapping document gives `RISK_ACCEPTANCE_RBDS` as `assessment-results.results[].observations[]` **or** `props[]`. `RISK_ASSESSMENT_REPORT` also does not have one resolved executable target.

**Question:**

> Please replace the alternative/blank mappings for `RISK_ACCEPTANCE_RBDS` and `RISK_ASSESSMENT_REPORT` with one exact OSCAL target path and mapping type for each. If either row is intended to create an `observations[]` object, please also provide the source mapping for the NIST-required observation content needed to build a valid observation; otherwise provide the exact `props[]`/link/resource target.

**Technical blocker:** the Python contract requires one target representation. NIST defines an Observation as an object representing an individual observation and requires its description, so a bare scalar cannot simply be routed to `observations[]` without the required structure. fileciteturn473file0L2-L6 citeturn920150view7

## 8. Source 2 `SOURCE_DESCRIPTION` and `INFORMATION` collide on one singleton path

The Source 2 mapping document maps both fields to `catalog.metadata.remarks`.

**Question:**

> `SOURCE_DESCRIPTION` and `INFORMATION` are separate source fields, but both are mapped to `catalog.metadata.remarks`. Please provide a separate exact OSCAL target path for each field, or provide an explicit combination/precedence rule if both are intentionally meant to populate the same `remarks` member.

**Technical blocker:** `remarks` is a single `[0..1]` member and the current Python mapper intentionally rejects two different populated values assigned to one singleton target. NIST also advises using `prop` or `link` for additional data rather than using `remarks` as a general data bucket. fileciteturn474file0L2-L6 citeturn920150view6

## 9. Source 2 `CONTROL_PROCEDURES` has two different model/path choices

The mapping document maps `CONTROL_PROCEDURES` to `Catalog or Component Definition` and supplies both a Catalog path and a Component Definition path.

**Question:**

> For `CONTROL_PROCEDURES`, please specify the single intended OSCAL model/path, or explicitly confirm that the field must be emitted to both models and provide the rule for each output. The current alternatives are `catalog.control[@id].part[@name='statement']` and `component-definition.component.control-implementation.implemented-requirement.statement`.

**Technical blocker:** the executable mapping contract needs a deterministic model binding and target path; `Catalog or Component Definition` is not directly compilable as one runtime mapping. fileciteturn474file0L2-L6

## 10. Component Definition required component members are missing

The Source 2 mapping sheet routes policy-related rows under `component-definition.components[]`, but it does not provide an approved mapping for the required Component members `type`, `title`, and `description`.

**Question:**

> For the Source-level Component Definition mapping, please provide the exact Archer source field and target mapping for `component-definition.components[].type`, `component-definition.components[].title`, and `component-definition.components[].description`. The mapper will generate the component UUID. If existing fields such as `SOURCE_NAME` or `SOURCE_DESCRIPTION` are intended to populate these members, please state that explicitly, and provide the intended component `type`.

**Technical blocker:** NIST OSCAL Component Definition v1.2.3 requires each Component to have `uuid`, `type`, `title`, and `description`. The current registry branch is ready, but the Python mapper cannot create a schema-complete Component from the current worksheet rows without inventing these required mappings.

## 11. Incomplete/clipped mapping rows

Several Source 2 transcriptions explicitly contain `[CLIPPED]` or `NEEDS SOURCE TEXT` for the OSCAL model/path or source field text.

**Question:**

> Please provide the original untruncated mapping row for any entry where the OSCAL model, OSCAL element path, Archer field name, or required mapping note is clipped/incomplete. We will use the authoritative row rather than reconstructing missing mapping syntax from screenshots.

**Technical blocker:** the mapper should not infer a missing model/path from partial screenshot text.

## Not included

This technical blocker list does not ask for general business-process definitions, generic ContentId/LevelId routing, timestamps/timezones, helper/system metadata, routine links/back-matter handling, or other mappings that the developer can resolve from the current source plus the NIST schema.
