# SSP Validation Runbook

**Created:** 2026-09-15  
**Mode:** READ ONLY until a defect is proven and separately approved for correction.  
**Purpose:** Validate the SSP scope already claimed as implemented without confusing historical load success with current OSCAL semantic correctness.

## Rules

1. Do not modify the mapping CSV, registry, or Cells 1-7 during this audit.
2. Validate only the currently APPROVED SSP mappings first. DEFERRED/EXCLUDED rows are coverage findings, not failures of the implemented subset.
3. Keep Profile/import-profile and Control Implementation explicitly separate. Current source-owner evidence supersedes the earlier `BASELINE_RECOMMENDATION -> profile.imports[].href` hypothesis, and Control Implementation remains deferred pending Allocated Controls source/SME validation.
4. Historical COMMIT/read-back results prove those historical executions only. Obtain a fresh report before claiming current runtime validation.
5. For every failure record: source field, CSV target path, transform, observed payload, expected OSCAL behavior, evidence, and recommended disposition. Do not silently fix during testing.

---

# Validation sequence

Run these checkpoints in order. Stop at the first material failure and investigate it before continuing.

## STEP 0 — Freeze and identify the exact version

Record:

- Git branch
- Git commit SHA
- mapping CSV path + SHA
- registry source/version
- Cells 01-07 SHAs
- Snowflake database/schema used for source and targets
- `EXECUTE_WRITES` value

**Pass:** all artifacts/versions are explicitly identified.  
**Fail:** any runtime artifact is unknown or differs from the version being reviewed.

No writes are required.

---

## STEP 1 — Inventory the SSP mapping CSV

Goal: establish exactly what the project currently claims to implement.

Produce counts grouped by:

- `OSCAL_MODEL`
- `EXECUTION_STATUS`
- top-level SSP branch from `RUNTIME_TARGET_PATH`

For every SSP row with `EXECUTION_STATUS = APPROVED`, capture:

- `SOURCE_FIELD_NAME`
- `RUNTIME_TARGET_PATH`
- `TRANSFORM_ID`
- `RULE_ID`
- `SOURCE_KEY`
- role/reference metadata where present

**Pass:** every approved SSP row has a nonblank runtime target and supported transform, and no DEFERRED/EXCLUDED row enters executable scope.

**Output:** `SSP_MAPPING_INVENTORY_<date>.md/csv`.

---

## STEP 2 — Validate registry coverage and hierarchy

Goal: prove that every structural collection/singleton required by the approved SSP mappings has a registry definition and valid parent chain.

For each approved runtime target:

1. Resolve its owning structural element.
2. Confirm the element exists in the registry.
3. Walk `PARENT_ELEMENT_PATH` to `system-security-plan`.
4. Confirm collection flags and instance-key rules.
5. Confirm there are no orphaned registered SSP paths.

At minimum review existing implemented branches:

```text
system-security-plan
system-security-plan.metadata
system-security-plan.system-characteristics
system-security-plan.system-implementation
```

Do not mark `import-profile` or `control-implementation` complete merely because the SSP root exists.

**Pass:** all APPROVED mappings have a complete registry parent chain and no contradictory collection identity.

---

## STEP 3 — Compile only; no source execution/write

Run Cells 01-03 with writes disabled.

Validate the compiled plan:

- zero unsupported transforms;
- zero duplicate `RULE_ID`s;
- zero conflicting singleton targets unless the framework has an explicit reviewed precedence rule;
- every approved source binding resolves;
- no deferred/excluded mapping is compiled.

Save the compile report.

**Pass:** compile succeeds with no blocked mappings.

---

## STEP 4 — SSP Metadata semantic tests

Review every APPROVED `SSP - Metadata` mapping against its source note and OSCAL target.

Required checks include:

### 4A. Published / last-modified

Inspect actual generated values for:

```text
system-security-plan.metadata.published
system-security-plan.metadata.last-modified
```

Verify they are valid OSCAL-compatible date-time values and that timezone semantics are not silently lost.

**Known audit concern:** current reusable `timestamp` behavior previously appeared to validate nonblank text rather than fully normalize/validate OSCAL date-time-with-timezone. Treat this as a test target, not as a pre-proven defect.

### 4B. Document IDs

For `document-ids[].identifier`, verify:

- nonblank scalar identifier;
- no JSON object/list accidentally emitted as identifier;
- duplicate handling is deterministic.

### 4C. Responsible parties

For every approved responsible-party source field:

- role-id is the reviewed role;
- party reference resolves to an emitted party;
- no unresolved user/content identifier remains where an OSCAL UUID reference is expected;
- multiple parties remain distinct;
- deterministic UUID is stable for the same source identity.

**Pass for Metadata:** every approved mapping produces the expected payload shape and reference integrity.

---

## STEP 5 — SSP System Characteristics semantic tests

Test every approved mapping, with focused checks below.

### 5A. System identity

Validate:

- `system-name`
- `system-name-short`
- `system-ids[].id`
- description / authorization boundary

Check scalar type, blank values, and deterministic conflict behavior.

### 5B. Status crosswalk

Profile actual source values for `OPERATIONAL_STATUS` and compare them with the reviewed crosswalk.

**Pass:** every populated source label is either explicitly crosswalked or intentionally blocked; no unreviewed label is silently coerced.

### 5C. Security impact objectives

For confidentiality/integrity/availability mappings:

1. Capture actual Archer value IDs/labels.
2. Capture generated OSCAL values.
3. Verify the output uses the approved OSCAL semantic values.
4. Flag any legacy LOE label passed through as a final security-objective value unless explicitly SME-approved.

### 5D. Extension properties

For each approved `props[]` mapping:

- prove no native OSCAL element is a better approved target;
- confirm stable property `name`;
- confirm value is scalar/valid;
- confirm whether an `ns` convention is required/approved;
- do not map transient/helper workflow fields solely for completeness.

**Pass for System Characteristics:** all approved values have correct target semantics, datatype, and controlled-value handling.

---

## STEP 6 — SSP System Implementation tests

This step validates both hierarchy and cross-reference hydration.

### 6A. Component references

For every approved component reference:

1. Read one source reference from `CURATED_JSON`.
2. Capture its source `ContentId` and source type/binding.
3. Confirm the configured hydration lookup points to the intended source dataset.
4. Confirm the referenced source record exists.
5. Confirm the generated component UUID is deterministic.
6. Confirm required component payload members for the project's approved OSCAL representation are present.
7. Confirm no component identity collision exists across reference types.

### 6B. Parties / users / inventory or other implemented collections

For each approved collection:

- instance key is deterministic;
- duplicate source references do not create conflicting duplicate nodes;
- parent edge points to the correct SSP branch;
- payload corresponds to the source record that generated the node.

**Pass for System Implementation:** all references hydrate, all emitted nodes have valid parentage, and no source-reference identity is lost.

---

## STEP 7 — Build graph in PREVIEW mode

Run Cells 04-07 with:

```text
EXECUTE_WRITES = False
```

Capture the complete graph/validation report.

Required graph assertions:

- node key nulls = 0
- duplicate node-key groups = 0
- edge key nulls = 0
- duplicate edge-key groups = 0
- missing parent references = 0
- missing child references = 0
- graph status = PASS / non-blocked
- mapped/missing-value counts explained

Also record:

- total source records
- candidate DIM nodes
- candidate FACT edges
- counts by `ELEMENT_TYPE`
- counts by `DEPENDENCY_TYPE`

Do not compare only total counts; inspect branch-level counts.

---

## STEP 8 — Deterministic identity tests

Select a small fixed sample of SSP source records (at least 3, including one with multi-valued references).

Run preview twice against the identical source snapshot and code version.

For each sampled node compare:

- `PK_ELEMENT_HASH`
- `OSCAL_UUID`
- `ELEMENT_TYPE`
- source record ID
- payload

For each sampled edge compare:

- edge PK/hash
- source element hash
- target element hash
- dependency type
- sequence

**Pass:** identical inputs produce identical identities and graph relationships.

This proves UUID/hash determinism rather than merely assuming it from the implementation.

---

## STEP 9 — Source-to-node lineage tests

For each major implemented SSP branch choose at least one real source record.

Trace manually:

```text
Archer source row
 -> CURATED_JSON source field
 -> mapping CSV rule
 -> registry structural element
 -> generated DIM node
 -> FACT parent edge
```

Save the evidence for:

- Metadata
- System Characteristics
- System Implementation

For cross-reference nodes additionally trace:

```text
source {ContentId, LevelId/reference}
 -> configured source binding
 -> referenced source record
 -> generated OSCAL node
```

**Pass:** every sampled payload can be explained end-to-end without guessing.

---

## STEP 10 — Reconstruct one SSP graph and inspect payload shape

Choose one Authorization Package/source root and recursively walk FACT from its SSP root.

Produce a readable tree of:

```text
ELEMENT_TYPE
PK_ELEMENT_HASH
OSCAL_UUID
parent -> child
```

Then inspect the payload for every node in that one-record tree.

Questions to answer:

- Does each payload live on the correct OSCAL structural node?
- Are collection instances separate where they should be?
- Are parent-only structural nodes incorrectly carrying child payload?
- Are props being used only where intended?
- Are UUID references resolvable within the graph?

**Pass:** one complete sampled SSP tree is internally coherent.

---

## STEP 11 — Current target read-back comparison (only if target tables already contain an accepted SSP load)

This is READ ONLY.

For the same sampled source records compare PREVIEW candidate nodes/edges with current DIM/FACT rows.

Report separately:

- candidate-only rows
- target-only rows
- matching keys with differing payload
- matching edges with differing relationship metadata

Do not treat historical acceptance as proof of current preview equivalence.

**Pass:** either exact equivalence is demonstrated or every difference is explained and classified.

---

## STEP 12 — Coverage classification

Produce final SSP coverage matrix with four statuses only:

- `VALIDATED_IMPLEMENTED`
- `DEFERRED_SOURCE_OR_SME`
- `EXCLUDED_INTENTIONALLY`
- `DEFECT_FOUND`

At minimum keep these unresolved branches explicit:

### Profile / import-profile

Earlier `BASELINE_RECOMMENDATION -> profile.imports[].href` assumption is superseded. Source-owner evidence says Baseline Recommendation is a values-list/LOE-scope concept. Control Set / authoritative source is a stronger candidate but remains SME/compliance validation work.

### Control Implementation

Authorization Package `ALLOCATED_CONTROLS` is a `{ContentId, LevelId}` relationship to Allocated Control records. Do not treat the reference array as the complete implementation. Final mapping is deferred until the Allocated Controls dataset and field semantics are validated.

**Pass:** no deferred area is presented as implemented and no implemented area lacks validation evidence.

---

# Final validation report template

Create a dated report with:

```text
Date:
Branch:
Commit:
Mapping CSV SHA:
Registry version:
Snowflake source snapshot/as-of:
EXECUTE_WRITES: False

SSP branch                         Status
--------------------------------------------------
Metadata                           ...
System Characteristics             ...
System Implementation              ...
Import Profile                     ...
Control Implementation             ...
Back Matter                        ...

Graph nodes:
Graph edges:
Null/duplicate keys:
Missing parents/children:
Determinism sample:
Source-lineage sample:
Target read-back comparison:

Defects found:
Deferred items:
Evidence gaps:
Next action:
```

# Immediate next checkpoint

**Do STEP 0 only.** Record the exact current Git branch/commit and the exact mapping CSV, registry, and Cell 01-07 versions that will be validated. Do not run or change the mapper until that checkpoint is recorded.
