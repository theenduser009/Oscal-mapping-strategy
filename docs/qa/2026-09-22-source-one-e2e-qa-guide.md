# Source One end-to-end QA handoff

**Date:** 2026-09-22  
**Repository branch:** `simplify-metadata-boundary`  
**Repository basis before this QA package:** `75db443a91c3151f3430a717b84aa4df3f8f74d5`

## Purpose

Give the SQL QA tester a repeatable way to trace one Archer Authorization Package
record from Source One through the current metadata-driven OSCAL targets.

The current Source One runtime source is:

`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`

A single `CONTENT_ID` can feed several OSCAL model routes. Current Cell 1 binds
Source One to:

- SSP
- Assessment Results
- POA&M
- Security Assessment Plan

**Catalog is not a Source One route.** Catalog belongs to Source Two in the current
Cell 1 configuration. **Profile is also not a current Source One runtime route.**

## What to give the tester

Give the tester:

1. `sql/qa/SOURCE_ONE_E2E_QA.sql`
2. this guide
3. the QA environment/database role needed to read RAW, registry, DIM and FACT tables

The SQL is read-only.

## Test flow

### Step 1 — choose a representative `CONTENT_ID`

Run section **01A** first.

It ranks Source One records by representative populated fields across the four
current routes. Prefer a row where `MODEL_GROUPS_WITH_DATA = 4`.

If no single record has meaningful data in all four routes, use the best SSP/AR
record as the primary record and use one additional record for the missing POA&M
or Assessment Plan case.

Set:

`SET QA_CONTENT_ID = '<chosen content id>';`

Then run the rest of the file.

### Step 2 — prove the source row and its mapped fields

Sections **01B** and **02** show:

- source-row uniqueness
- every current APPROVED / BLOCKED_IF_POPULATED Source One runtime mapping
- transform
- runtime target path
- null policy
- raw value/type/state for the chosen record
- config-provided fields such as OSCAL version and Assessment Plan task title/type

This is the tester's source-side evidence.

### Step 3 — prove the metadata rules

Section **03** reads the live `OSCAL_ELEMENT_REGISTRY` for all four Source One
routes and checks duplicate paths and orphan parents.

This is the tester's current hierarchy/operator/identity-rule evidence.

### Step 4 — prove each target model

Section **04** shows node/root counts per target model and the element-type
inventory for the chosen source record.

For a route that has actually been loaded in QA, expect exactly one model root for
that `CONTENT_ID`.

### Step 5 — validate SSP examples

Sections **05–07** cover:

- Authorization Package name -> SSP metadata title
- Authorization Package name -> system name
- acronym -> short system name
- mission purpose -> system description
- authorization boundary description
- system IDs/status/security-impact payloads
- roles / parties / responsible-party assignments
- system implementation components
- source reference count vs generated component count

The component query deduplicates source references by ContentId and type before
comparing them with generated component nodes.

### Step 6 — validate Assessment Results

Section **08** presents every currently approved Source One Assessment Results
field beside the generated observation/result-property payload for that record.

For Archer select fields, the raw source is the Archer select object while the
target should contain the resolved label. Scalar scores should appear as
observation properties.

### Step 7 — validate POA&M

Section **09** compares distinct source `POAMS[].ContentId` references with
generated `poam-items` nodes and shows the written target payloads.

### Step 8 — validate Assessment Plan

Section **10** shows the three Source One inputs:

- `REQUEST_TO_BEGIN_ASSESSMENT`
- `APPROVAL_TO_BEGIN_ASSESSMENT`
- `PREASSESSMENT_REVIEW_COMMENTS`

and then the generated Assessment Plan task/props payloads.

### Step 9 — graph integrity

Section **11** checks each loaded route for:

- missing parent nodes
- missing child nodes
- cross-record edges

All three counts must be zero for a structural PASS.

Section **12** optionally reconstructs the SSP tree for the selected record so the
tester can see the written parent/child OSCAL path and payload together.

## Known scope boundaries / do-not-fail items

These are current project boundaries, not QA defects:

- **SSP Control Implementation:** the actual Level-355 control-record source is
  expected to be `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`. It is not
  currently ingested/available. Do not expect the full
  `control-implementation.implemented-requirements[]` branch yet.
- **SSP AUTHORIZATION_DECISION:** mapping and PREVIEW were reconciled on
  2026-09-21 for 2,308 new nodes/edges, but the owner has not yet supplied a
  COMMIT/read-back result for that delta. Treat absence of that new property in a
  pre-commit environment as **NOT READY**, not a mapper defect.
- **Assessment Results RISK_ASSESSMENT_REPORT:** deferred until an approved
  current-runtime attachment/resource contract exists.
- **Assessment Results FINDINGS:** canonical destination is
  `assessment-results.results[].findings[]`; the reviewed current Source One
  value was null, so no output is expected for that current null case.
- **Profile:** not a current runtime route. `ADD_OVERLAY` was null across the
  reviewed 2,813-record snapshot; `BASELINE_RECOMMENDATION` still needs an
  approved baseline/control-set -> OSCAL href/control-selection crosswalk.
- **RECOMMENDED_SECURITY_CATEGORY:** current runtime status is
  `BLOCKED_IF_POPULATED`. A populated value is an intentional guard condition,
  not something QA should silently accept.

## Current persistence evidence to keep separate

- Source One Assessment Results: **COMMITTED_AND_VERIFIED** on 2026-09-21
  (106,501 nodes / 103,688 edges for 2,813 source records after the final batch).
- SSP responsible-party metadata refresh: PREVIEW reproduced the existing target
  with zero target delta.
- SSP authorization-decision addition: PREVIEW fully reconciled; COMMIT/read-back
  not yet established.
- Current repository does not contain a newer POA&M or Security Assessment Plan
  COMMIT/read-back checkpoint. A formal QA PASS for those routes should therefore
  be based on the tester's actual QA-environment load/read-back, not older preview
  evidence.

## Suggested evidence the tester should return

For each tested `CONTENT_ID`, capture:

| Evidence | Result |
|---|---|
| Source row unique | PASS / FAIL |
| Registry structural check | PASS / FAIL |
| SSP root/node/edge results | PASS / FAIL / NOT READY |
| SSP direct-value checks | PASS / FAIL / NOT READY |
| Responsible-party reconciliation | PASS / FAIL / NOT READY |
| Component reconciliation | PASS / FAIL / NOT READY |
| Assessment Results observations/props | PASS / FAIL / NOT READY |
| POA&M reference reconciliation | PASS / FAIL / NOT READY |
| Assessment Plan task/props | PASS / FAIL / NOT READY |
| Cross-record/orphan edge checks | PASS / FAIL |
| Known exceptions observed | list |
| QA CONTENT_ID(s) | list |

Attach the result grids or screenshots. Do not use an old project checkpoint as
proof of a newer QA run.
