# Validation 06 — SSP System Characteristics core checkpoint

Date: **2026-09-15**  
Branch: `simplify-metadata-boundary`  
Repository head before checkpoint publication: `5804baf19e951ca2d32e993beaf9c1f81d1a54d0`

## What was added

Validator:

`notebooks/validation/06_ssp_system_characteristics_core_validation.py`

Validator commit: `752bf5a7dc65d0623731e36ac18ba23ea38dba0f`

Regression tests:

`tests/lean/test_ssp_validation_06.py`

Test publication commit: `5804baf19e951ca2d32e993beaf9c1f81d1a54d0`

Both files were read back from GitHub after publication.

## Scope

This is a bounded read-only validation of the current generated SSP System Characteristics core payload. It tests only these currently approved mappings:

- `AUTHORIZATION_PACKAGE_NAME -> system-security-plan.system-characteristics.system-name`
- `ACRONYM -> system-security-plan.system-characteristics.system-name-short`
- `MISSION_PURPOSE -> system-security-plan.system-characteristics.description`
- `SAP_ID -> system-security-plan.system-characteristics.system-ids[].id`

It uses the actual current seven-cell runtime contract retained by Cell 7 (`MODEL_GRAPHS[(source_key, 'SSP')]`) and validates against the frozen source snapshot used by that same preview.

The validator checks:

- exact compiled source field / target / transform contract for the four mappings;
- exactly one `system-characteristics` node per source record;
- generated scalar values equal their selected source values;
- generated system IDs equal the source `SAP_ID` values under the current `values` operator contract;
- no duplicate system ID within one SSP;
- current run/source namespace consistency;
- tested core parent edges remain within the same SSP and edge UUIDs match their actual endpoints.

## Explicitly not tested here

- System Characteristics extension `props[]`;
- operational status / remarks;
- authorization boundary;
- `date-authorized`;
- security-impact-level / CIA objectives;
- full OSCAL schema conformance;
- business/SME approval of field semantics;
- target persistence / COMMIT readback.

Those remain separate validation work.

## Validation actually performed before publication

A local regression harness used the actual repository Cells 1–7 functions extracted from the current project handoff whose cell blob hashes match the current branch cell blobs. It created a synthetic two-record SSP preview, used the current mapping CSV rows for these four mappings, and exercised the actual compiler, payload assembler, graph builder, Cell 6 targetless graph validator, and Cell 7 orchestration through a minimal dataframe/session adapter. No Snowflake connection or target-table access was available in that harness.

**12 local regression tests passed, zero failures/errors.** Tests include:

- successful source-to-payload equality;
- wrong system name;
- wrong short name;
- wrong description;
- wrong/extra system ID;
- missing System Characteristics node;
- stale run context;
- wrong candidate schema (`PK_ELEMENT_HASH` substituted for `NODE_KEY`);
- no-mutation check;
- report does not expose private synthetic record values;
- standalone validation-cell entrypoint.

This is local regression evidence only. It is **not live Snowflake acceptance**.

## Current status

**Implemented:** Validation 06 validator and regression test file are committed and read-back verified in GitHub.

**Locally validated:** 12/12 regression tests passed.

**Live Snowflake result:** **PENDING.** No live PASS/FAIL is claimed until the owner runs Validation 06 inside the existing successful SSP PREVIEW session and supplies the aggregate report.

**Writes:** validator is read-only and reports `WRITES_PERFORMED_BY_VALIDATOR = false`; no mapper/CSV/registry/target table was changed by this checkpoint.

## Next action

Run only `notebooks/validation/06_ssp_system_characteristics_core_validation.py` in the existing successful SSP PREVIEW notebook session. Do not rerun unchanged prior validations solely for this step. Capture the output beginning:

```text
=== SSP VALIDATION 06 ===
```

If Validation 06 passes, the next bounded System Characteristics batch should cover authorization boundary, status/remarks, date-authorized, properties, and security-impact semantics separately rather than broadening this PASS beyond its implemented scope.
