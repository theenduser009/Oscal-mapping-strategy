# Mapping notes vs runtime audit checkpoint

Date: 2026-09-14
Branch reviewed: `simplify-metadata-boundary`
Branch head before this checkpoint: `ba60f14702aebb4347bed3557853fa39ddc850bf`

## Scope

This is a read-only review of:

- `ARCHER_OSCAL_MAPPING_REVIEW.xlsx` (147 screenshot-derived review entries; not the original complete workbook)
- `Mapping/ARCHER_OSCAL_MAPPINGS.csv` (153 runtime rows: 86 APPROVED, 64 DEFERRED, 2 EXCLUDED, 1 BLOCKED_IF_POPULATED)
- the maintained seven-cell mapper contract in `notebooks/cells/`
- the dated project handoff/current-code bundle
- NIST OSCAL v1.1.3 model references for consequential model-shape checks

No runtime CSV, seven-cell code, registry, or Snowflake target was changed by this review.

## Executive result

The architecture is sound and the CSV is disciplined about keeping clearly unresolved Profile and Control Implementation rows deferred. The review also found several places where an `APPROVED` executable row is best understood as an accepted project decision or partial graph representation, **not proof that the original Excel review gate or full NIST object semantics have been completely satisfied**.

The highest-priority gaps are:

1. timestamp transform does not actually validate/normalize OSCAL `date-time-with-timezone` values;
2. SSP security-objective fallback can preserve reviewed legacy LOE labels instead of enforcing the review note's low/moderate/high normalization rule;
3. extension-property names are generated from source-field slugs, but the Excel notes requested explicit property-name/namespace approval for several fields;
4. System Implementation component nodes are graph-useful but do not currently materialize every NIST-required component member (notably `status`; some references also lack hydrated title/description);
5. Assessment Results score observations do not implement the workbook's stated reusable observation profile (method, subject, timestamp, unit, datatype, namespace); current observation payloads are essentially named scalar props under observation nodes;
6. Assessment Plan was owner-enabled with a deliberately minimal preassessment task, while the original review gate asked for timing/dependency/status semantics before task registration.

These findings do **not** invalidate historical SSP/AR graph readback checkpoints. They qualify what those checkpoints prove: persisted graph behavior for the accepted mapped subset, not full OSCAL-document conformance.

## Workbook-to-CSV preservation check

The 147 review rows were compared to the corresponding numeric `ORIGINAL_ROW_ID` rows in the runtime CSV.

There are 24 intentional differences rather than silent transcription drift:

- 15 Assessment Results ambiguous `observations[] or props[]` paths were resolved to `observations[]` by later owner decision;
- 3 deferred Assessment Results rows have the ambiguous executable path cleared rather than pretending to have an approved route;
- 2 Assessment Results source keys were corrected to owner-confirmed leading-underscore JSON keys;
- 3 Security Assessment Plan paths were normalized from the workbook's `security-assessment-plan...` wording to the actual OSCAL `assessment-plan...` model path;
- 1 `DAILY_LOSS_AMOUNT_FROM_OUTAGE` mapping-type change records the 2026-09-14 owner supersession of the earlier all-null deferral.

No other silent source-field/model/path/note drift was found in the 147 visible review rows.

## Model-by-model audit

### SSP Metadata

**Generally sound:** title/version support, responsible-party role/party construction, and scalar document metadata routing fit the intended branch.

**Needs correction / clarification:**

- Four approved timestamp mappings use `TRANSFORM_ID=timestamp`, but Cell 4 currently treats `timestamp` like nonblank text. The workbook notes say convert/validate OSCAL date-time. NIST metadata `published` and `last-modified` are `date-time-with-timezone`. A real timestamp validator/normalizer is still needed.
- `TRACKING_ID -> metadata.document-ids[].identifier` is reasonable, but the note says preserve identifier scheme when available. The current mapping supplies only `identifier`; no scheme/identifier-type member is populated, so the scheme is not actually preserved.

### SSP System Characteristics

**Generally sound:** native text fields, authorization boundary description, authorization date, operational status crosswalk, and named extension-property routing are reasonable.

**Needs correction / clarification:**

- The source review explicitly says all impact values must normalize to low/moderate/high. The current `security-objective` transform resolves ordinary Archer Low/Moderate/High values, but also allows reviewed legacy LOE labels to pass through as fallback values. That does not fully implement the review gate. Decide whether legacy LOE values should be translated to canonical impact levels or retained as a separate namespaced property instead.
- The review asks for explicit property name **and namespace** approval for extension properties. The runtime property operator generates a slug from `SOURCE_FIELD_NAME` and does not currently assign `ns`. This is satisfactory for explicitly named notes such as `fisma-reportable` where the slug matches, but it does not prove that fields such as `PACKAGE_TYPE`, `INFORMATION_SYSTEM_TYPE`, or `INFORMATION_CLASSIFICATION` completed the original name/namespace review.
- The review asks for precedence when recommended, override, ProgramSite, and CNSS impact sources disagree. Current singleton assignment safely blocks conflicting populated values rather than defining precedence. This is conservative, but the precedence decision remains unresolved.
- `DAILY_LOSS_AMOUNT_FROM_OUTAGE` is a documented owner supersession and uses null preservation; however, historical SSP COMMIT/readback predates that mapping, so live acceptance of this added field remains unverified.

### SSP System Implementation

**Architecture is good:** the existing ContentId hydration pattern is reusable and the six current reference fields are consistently routed to `system-implementation.components[]`.

**Conformance qualification:** NIST v1.1.3 component objects require title, description, and status. Current component reference payloads always supply UUID/type, hydrate title/description only for configured lookup bindings, and do not currently populate component `status`. Therefore the accepted graph is useful but should not be described as a fully materialized NIST component object for every reference.

### SSP Control Implementation

**Correctly deferred:** all 42 review rows remain DEFERRED. This matches the workbook note that most visible fields lacked an approved individual OSCAL path and required design review.

The new 2026-09-14 `ALLOCATED_CONTROLS -> {ContentId, LevelId=355}` discovery is promising but does not yet justify changing those statuses. Resolve Level 355 to the actual source record/table and inspect control identity/implementation fields first.

### Assessment Results

**Decision history is preserved correctly:** owner-approved rows that originally said `observations[] or props[]` now consistently route to observations, and the two leading-underscore source-key corrections are documented.

**Important remaining semantic gap:** the workbook's validation gate asked for a reusable risk-score observation profile including method, subject, timestamp, unit, datatype, and namespace before writes. Current `scalar-score` handling creates one observation node per field with a named inline scalar property. It does not populate that broader observation profile. This supports the project's graph use case but is not evidence that the review gate or a complete NIST assessment observation has been satisfied.

Historical AR30 COMMIT/readback remains valid for that historical mapped graph. It does not prove later AR32/null/source-name changes have a separate current committed readback.

### POA&M

The single `POAMS` mapping is intentionally a Source One reference graph. Its execution note correctly says no item-detail hydration or complete OSCAL document conformance is claimed. The accepted evidence is PREVIEW only; committed readback remains unverified.

### Profile

Both rows remain DEFERRED, which is correct.

- `BASELINE_RECOMMENDATION` is a values-list selector (LOE A/B/C/D, DFARS, GS Labs, Basic), not itself an OSCAL `href`.
- `ADD_OVERLAY` did not provide usable current source evidence in the reviewed snapshot.

Do not activate `profile.imports[]` until an authoritative catalog/profile reference and selection policy are known.

### Security Assessment Plan

The runtime normalization to `assessment-plan...` is correct for OSCAL. Task properties and remarks are structurally reasonable, and the two support mappings provide task title/type.

However, the original review gate said task identity, timing, dependency, and status semantics should be defined before task registration. The implemented project decision intentionally creates a minimal preassessment task without inferring timing/dependency/status. Treat this as an owner-approved scope reduction, not proof that the original gate was fully satisfied. A successful current SAP setup/preview/commit report is still unverified in the handoff.

## What is safe to keep

Do **not** redesign the seven-cell architecture. Its separation of CSV mapping semantics, registry hierarchy/identity, reusable transforms, graph construction, and guarded loading remains appropriate.

Keep Profile and Control Implementation deferred until their specific source semantics are resolved.

Keep historical SSP/AR commit/readback checkpoints as evidence of their bounded mapped graph states; do not relabel them as full OSCAL-document validation.

## Recommended correction order

1. Fix/strengthen the reusable `timestamp` transform and regression-test the four affected SSP Metadata mappings.
2. Decide the canonical policy for the 11 `security-objective` mappings: strict low/moderate/high normalization vs separate legacy property preservation; then encode and test it.
3. Review extension-property naming/namespace policy, especially `PACKAGE_TYPE`, `INFORMATION_SYSTEM_TYPE`, and `INFORMATION_CLASSIFICATION`.
4. Continue the Level 355 Control Implementation source trace before approving any of the 42 deferred rows.
5. Decide whether Assessment Results is intentionally a graph-only extension or must produce NIST-complete observation objects; if the latter, add the missing observation profile metadata before claiming conformance.
6. Obtain current SAP and POAM live evidence before changing their verification status.

## NIST references consulted

- OSCAL SSP v1.1.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.1.3/system-security-plan/
- OSCAL Assessment Results v1.1.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.1.3/assessment-results/
- OSCAL Assessment Plan v1.1.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.1.3/assessment-plan/
- OSCAL Profile v1.1.3 reference: https://pages.nist.gov/OSCAL-Reference/models/v1.1.3/profile/
