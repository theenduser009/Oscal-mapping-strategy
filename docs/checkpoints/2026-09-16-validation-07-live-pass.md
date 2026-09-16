# Validation 07 live result — remaining SSP System Characteristics mappings

Date: **2026-09-16**

Evidence: owner-provided Snowflake notebook screenshots from the existing SSP PREVIEW session.

## Live result

Validator: `07_SSP_SYSTEM_CHARACTERISTICS_REMAINING_MAPPINGS`
Validator version: `2026-09-16-r1`
Status: **PASS**
Writes performed by validator: **false**

Reported counts visible in the owner screenshots:

- SOURCE_RECORDS: 2,813
- APPROVED_RULES_IN_SCOPE: 25
- EXPECTED_INSTANCES_BY_PATH:
  - `system-security-plan.system-characteristics`: 2,813
  - `system-security-plan.system-characteristics.authorization-boundary`: 2,813
  - `system-security-plan.system-characteristics.props[]`: 17,279
  - `system-security-plan.system-characteristics.security-impact-level`: 270
  - `system-security-plan.system-characteristics.status`: 2,813
- ACTUAL_INSTANCES_BY_PATH matched the expected counts above.
- RELEVANT_EDGES_CHECKED: 25,988
- FAILURE_COUNTS: `{}`

The report shows the in-scope approved source fields include the remaining System Characteristics mappings after Validation 06, including examples such as:

- `ATOIATO_DATE`
- `AUTHORIZATION_BOUNDARY_DESCRIPTION`
- `AUTHORIZATION_COMMENTS`
- `AVAILABILITY_CONTROL_CATEGORY_OVERRIDE`
- `CNSS_AVAILABILITY_RATING`
- `CNSS_CONFIDENTIALITY_RATING`
- `CNSS_INTEGRITY_RATING`
- `CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE`
- `CRITICAL_INFRASTRUCTURE`
- `DAILY_LOSS_AMOUNT_FROM_OUTAGE`
- `FINANCIAL_SYSTEM`
- `FISMA_REPORTABLE`
- `INFORMATION_CLASSIFICATION`
- `INFORMATION_SYSTEM_TYPE`
- `INTEGRITY_CONTROL_CATEGORY_OVERRIDE`
- `MISSION_CRITICAL`
- `OPERATIONAL_STATUS`
- `PACKAGE_TYPE`
- `PIA_REQUIRED`
- `PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY`
- `PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY`
- `RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY`
- `RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY`
- `RECOMMENDED_INTEGRITY_CONTROL_CATEGORY`
- `SECURITY_CATEGORY`

## Interpretation

This PASS provides mapping-driven live evidence that the remaining currently approved SSP System Characteristics mappings covered by Validation 07 produced the expected candidate graph instances and payload structures for the frozen Source 1 snapshot used by the preview.

The expected and actual instance counts matched for the System Characteristics owner paths exercised by the validator, and the checked relevant parent-child edges had no reported failures.

## Explicit exclusions preserved from the validator

Validation 07 does **not** establish:

- the four core fields already covered by Validation 06 (`system-name`, `system-name-short`, `description`, `system-ids[].id`);
- Metadata timestamp correctness; the known timezone/lexical issue remains deferred to SME;
- deferred, excluded, or blocked-if-populated mappings;
- System Implementation or Control Implementation;
- full OSCAL schema conformance;
- business/SME approval of field meanings;
- target persistence / COMMIT readback.

## Current Source 1 checkpoint

Source 1 SSP evidence now includes:

- Validation 01 — registry validation: PASS
- Validation 02 — mapping CSV / registry compilation: PASS
- Validation 03 — timestamp lexical validation: known FAIL, remediation deferred to SME
- Validation 04 — document IDs: PASS
- Validation 05 — Metadata graph/reference validation: PASS
- Validation 06 — System Characteristics core mappings: PASS
- Validation 07 — remaining approved System Characteristics mappings: PASS

This materially strengthens the case that the currently approved SSP Metadata and System Characteristics mapping scope is functioning as designed in preview. It does not yet close System Implementation, Control Implementation, timestamp remediation, full schema conformance, or committed target readback.

## Next action

Do not rerun Validation 07 unchanged. The next mapping-driven checkpoint should focus on the next implemented SSP branch that is actually in scope (for example System Implementation) and should first confirm the currently approved mapping rows for that branch before creating another validator.
