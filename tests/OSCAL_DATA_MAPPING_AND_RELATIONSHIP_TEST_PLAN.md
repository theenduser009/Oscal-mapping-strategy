# OSCAL Data Mapping and Relationship Test Plan

**Date:** 2026-09-15  
**Branch:** `simplify-metadata-boundary`  
**Audience:** Data / QA tester validating committed OSCAL DIM and FACT data against Archer source data and the approved mapping artifact.  
**Primary mapping artifact:** `Mapping/ARCHER_OSCAL_MAPPINGS.csv`

## 1. Testing objective

The tester's job is to prove, with actual data, that:

1. an **executable mapping row** in the CSV reads the intended Archer source field;
2. the configured transformation is applied correctly;
3. the transformed value lands in the intended OSCAL node / JSON member in the model DIM table;
4. collection mappings create the correct number of child nodes without duplicates;
5. DIM primary keys and OSCAL UUIDs are valid and unique;
6. FACT foreign keys resolve to DIM rows and represent the correct parent-child relationship;
7. every child belongs to the correct source record / OSCAL root;
8. deferred or excluded mappings are **not** treated as expected executable mappings;
9. known open issues are reported, not silently "fixed" during testing.

This is **data validation**, not a rewrite of the mapper.

---

## 2. Important concept: mapping-rule count is NOT target-row count

One CSV row is a **mapping rule**, not one DIM row.

Example:

```text
CSV rule:
AUTHORIZATION_PACKAGE_NAME
  -> system-security-plan.system-characteristics.system-name
```

If 2,813 source Authorization Packages are processed, that one rule may contribute a value to 2,813 System Characteristics nodes.

A collection rule may create multiple DIM rows per source record. Therefore:

> **Do not compare "number of CSV rows" directly with "number of DIM rows".**

The tester must separately record:

- mapping-rule counts;
- source-record counts;
- generated node counts by `ELEMENT_TYPE`;
- generated relationship counts in FACT.

---

## 3. Mapping inventory the tester must create first

Use `Mapping/ARCHER_OSCAL_MAPPINGS.csv` as the runtime mapping inventory.

For each OSCAL model, report:

| Model | Total CSV rows | APPROVED | BLOCKED_IF_POPULATED | DEFERRED | EXCLUDED | Executable rules | Unique source fields | Unique runtime target paths |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SSP | | | | | | | | |
| POAM | | | | | | | | |
| Assessment Results | | | | | | | | |
| Security Assessment Plan | | | | | | | | |

**Executable rules = `APPROVED` + `BLOCKED_IF_POPULATED`.**

Do not test `DEFERRED` or `EXCLUDED` rows as expected target mappings. They should instead be listed in the test report as intentionally not executable.

### Current verified SSP checkpoint

Validation 02 on 2026-09-15 reported, for the current SSP mapping snapshot:

```text
CSV SSP rows              = 100
APPROVED                   = 48
BLOCKED_IF_POPULATED       = 1
DEFERRED                   = 49
EXCLUDED                   = 2
Executable SSP rules       = 49
```

These numbers are a dated checkpoint, not a permanent constant. Recalculate from the CSV before final sign-off.

### Quick mapping-count helper

```python
import pandas as pd

m = pd.read_csv("Mapping/ARCHER_OSCAL_MAPPINGS.csv")
print(m.groupby(["OSCAL_MODEL", "EXECUTION_STATUS"]).size())

executable = m[m["EXECUTION_STATUS"].isin(["APPROVED", "BLOCKED_IF_POPULATED"])]
print(executable.groupby("OSCAL_MODEL").agg(
    EXECUTABLE_RULES=("RULE_ID", "count"),
    UNIQUE_SOURCE_FIELDS=("SOURCE_FIELD_NAME", "nunique"),
    UNIQUE_TARGET_PATHS=("RUNTIME_TARGET_PATH", "nunique"),
))
```

---

## 4. Physical model tables to validate

The current seven-cell configuration defines these physical targets.

| Model | DIM table | DIM PK | FACT table | FACT PK |
|---|---|---|---|---|
| SSP | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT` | `PK_OSCAL_SSP_ELEMENT_HASH` | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY` | `PK_FACT_OSCAL_DEPENDENCY_HASH` |
| POAM | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT` | `PK_DIM_OSCAL_POAM_ELEMENT_HASH` | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_POAM_DEPENDENCY` | `PK_FACT_OSCAL_POAM_DEPENDENCY_HASH` |
| Assessment Results | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT` | `PK_DIM_OSCAL_ASSESSMENT_RESULTS_ELEMENT_HASH` | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY` | `PK_FACT_OSCAL_ASSESSMENT_RESULTS_DEPENDENCY_HASH` |
| Security Assessment Plan | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT` | `PK_DIM_OSCAL_ASSESSMENT_PLAN_ELEMENT_HASH` | `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY` | `PK_FACT_OSCAL_ASSESSMENT_PLAN_DEPENDENCY_HASH` |

### Common DIM business/audit columns

The loader contract expects the model DIM to contain the model PK plus:

```text
ELEMENT_TYPE
OSCAL_UUID
METADATA_JSON
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
SOURCE_RECORD_ID
DW_PIPELINE_RUN_ID
DW_LOAD_TIMESTAMP
DW_LOAD_TIMESTAMP_TZ
```

### Common FACT columns

The model FACT contains the model FACT PK plus:

```text
FK_SOURCE_ELEMENT_HASH
FK_TARGET_ELEMENT_HASH
DEPENDENCY_TYPE
SOURCE_OSCAL_UUID
TARGET_OSCAL_UUID
```

The candidate graph uses `NODE_KEY`; the persisted DIM uses the model-specific physical PK shown above. Do not confuse the candidate graph column name with the physical DIM PK name.

---

## 5. Test procedure for EVERY executable mapping row

For every executable CSV mapping, capture at least the following evidence:

| Evidence | What tester records |
|---|---|
| Mapping rule | `RULE_ID` |
| Source field | `SOURCE_FIELD_NAME` |
| Source record | `CONTENT_ID` / `SOURCE_RECORD_ID` |
| Source raw/curated value | exact value from `CURATED_JSON` |
| Transform | `TRANSFORM_ID` plus any `VALUE_MAP`, allowed values, role/reference parameters |
| Expected OSCAL target | `RUNTIME_TARGET_PATH` |
| Owning OSCAL node | registry node / resulting `ELEMENT_TYPE` |
| Actual DIM row | model DIM PK + `SOURCE_RECORD_ID` + `ELEMENT_TYPE` |
| Actual generated value | value inside `METADATA_JSON` |
| Result | PASS / FAIL / BLOCKED / SME REVIEW |

### Minimum sample selection per mapping

Where data permits, test:

1. one normal populated value;
2. one NULL/missing value;
3. one multi-valued value for collection/reference fields;
4. one uncommon/edge-case value for crosswalk/select mappings;
5. more samples for high-risk transformations or any failed comparison.

For very small datasets, test all populated records.

---

## 6. Transformation tests

Use the CSV `TRANSFORM_ID` as the expected behavior.

### `direct`

Expected: source value is carried to the approved target without semantic conversion, subject to the node/operator representation.

Test:

- source value equals generated value;
- source type/shape is compatible with the target;
- collection values are not silently collapsed or duplicated.

### `text`

Expected: populated value becomes nonblank text.

Test exact textual equality unless the mapping note explicitly documents normalization.

### `canonical-text`

Expected: reviewed canonical text; no unintended leading/trailing whitespace or alternate labels.

### `identifier`

Expected: one finite, nonblank scalar identifier.

Example current SSP rule:

```text
TRACKING_ID -> metadata.document-ids[].identifier
```

### `date`

Expected: valid ISO calendar date (`YYYY-MM-DD`) derived without changing the intended source calendar date.

### `timestamp`

**Known open issue:** current SSP timestamp lexical validation failed because generated values did not contain an explicit timezone. Timezone remediation is `DEFERRED_SME`.

Tester should record the source and generated value, but should **not mark timezone semantics correct** until the Archer extraction timezone question is resolved.

### `archer-select`

Expected: Archer value-list ID resolves through:

```text
ARCHER_META_VALUE.SELECT_VALUE_ID
    -> ARCHER_META_VALUE.SELECT_VALUE_NAME
```

Test both the source ID and the resolved generated label/value.

### `status-crosswalk`

Expected: source label maps according to the CSV `VALUE_MAP`.

For current SSP operational status, validate each observed source label against the explicit crosswalk. An unmapped populated label is a defect/blocker, not a value to guess.

### `security-objective`

Test source value/list ID, resolved label, and final generated security objective. Pay particular attention to legacy LOE labels versus `low` / `moderate` / `high`; semantic issues must be logged rather than silently accepted.

### `scalar-score`

Expected: one finite scalar score per generated observation/property as configured. Test numeric and NULL behavior.

### `reject-populated`

Expected: source must not be populated for the accepted execution contract. If populated, the route should block rather than silently map the value.

---

## 7. DIM-table tests for each model

Run these tests independently for SSP, POAM, Assessment Results, and Assessment Plan wherever a committed target exists.

### 7.1 Primary key integrity

Expected:

- DIM PK is never NULL;
- DIM PK is unique;
- the same logical source/model/node identity does not create multiple different PKs in the same accepted snapshot.

Template:

```sql
SELECT
    COUNT(*) AS TOTAL_ROWS,
    COUNT_IF(<DIM_PK> IS NULL) AS NULL_PK_ROWS,
    COUNT(DISTINCT <DIM_PK>) AS DISTINCT_PK_ROWS
FROM <DIM_TABLE>;
```

Pass condition:

```text
NULL_PK_ROWS = 0
TOTAL_ROWS = DISTINCT_PK_ROWS
```

### 7.2 OSCAL UUID integrity

Expected:

- `OSCAL_UUID` is populated for stored nodes under the current graph/storage contract;
- no duplicate logical node UUID exists inside the same model target.

```sql
SELECT OSCAL_UUID, COUNT(*)
FROM <DIM_TABLE>
GROUP BY OSCAL_UUID
HAVING OSCAL_UUID IS NULL OR COUNT(*) > 1;
```

Expected: zero problem rows.

### 7.3 Source lineage

Every DIM row must retain:

```text
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
SOURCE_RECORD_ID
DW_PIPELINE_RUN_ID
```

Test that a sampled target row can be traced back to the source record that produced it.

### 7.4 Root-row integrity

Expected one model root per processed source record for the accepted snapshot.

Current root element types:

```text
SSP                -> system-security-plan
POAM               -> plan-of-action-and-milestones
Assessment Results -> assessment-results
Assessment Plan    -> assessment-plan
```

Example:

```sql
SELECT SOURCE_RECORD_ID, COUNT(*) AS ROOT_ROWS
FROM <DIM_TABLE>
WHERE ELEMENT_TYPE = '<ROOT_ELEMENT_TYPE>'
GROUP BY SOURCE_RECORD_ID
HAVING COUNT(*) <> 1;
```

Expected: zero rows.

### 7.5 Node count by element type

```sql
SELECT ELEMENT_TYPE, COUNT(*) AS ROW_COUNT
FROM <DIM_TABLE>
GROUP BY ELEMENT_TYPE
ORDER BY ELEMENT_TYPE;
```

Use this to reconcile expected singleton versus collection behavior. Do not assume every element type should equal the root count; collections can be zero-to-many per root.

---

## 8. FACT-table and relationship-integrity tests

This is critical. The FACT table is the parent-child relationship graph.

### 8.1 FACT PK integrity

```sql
SELECT
    COUNT(*) AS TOTAL_ROWS,
    COUNT_IF(<FACT_PK> IS NULL) AS NULL_PK_ROWS,
    COUNT(DISTINCT <FACT_PK>) AS DISTINCT_PK_ROWS
FROM <FACT_TABLE>;
```

Expected:

```text
NULL_PK_ROWS = 0
TOTAL_ROWS = DISTINCT_PK_ROWS
```

### 8.2 No NULL foreign keys

```sql
SELECT COUNT(*) AS BAD_ROWS
FROM <FACT_TABLE>
WHERE FK_SOURCE_ELEMENT_HASH IS NULL
   OR FK_TARGET_ELEMENT_HASH IS NULL;
```

Expected: `0`.

### 8.3 Every FACT source FK resolves to DIM

```sql
SELECT COUNT(*) AS MISSING_SOURCE_PARENTS
FROM <FACT_TABLE> f
LEFT JOIN <DIM_TABLE> p
  ON f.FK_SOURCE_ELEMENT_HASH = p.<DIM_PK>
WHERE p.<DIM_PK> IS NULL;
```

Expected: `0`.

### 8.4 Every FACT target FK resolves to DIM

```sql
SELECT COUNT(*) AS MISSING_TARGET_CHILDREN
FROM <FACT_TABLE> f
LEFT JOIN <DIM_TABLE> c
  ON f.FK_TARGET_ELEMENT_HASH = c.<DIM_PK>
WHERE c.<DIM_PK> IS NULL;
```

Expected: `0`.

### 8.5 FACT UUIDs must agree with DIM UUIDs

```sql
SELECT COUNT(*) AS UUID_MISMATCHES
FROM <FACT_TABLE> f
JOIN <DIM_TABLE> p
  ON f.FK_SOURCE_ELEMENT_HASH = p.<DIM_PK>
JOIN <DIM_TABLE> c
  ON f.FK_TARGET_ELEMENT_HASH = c.<DIM_PK>
WHERE f.SOURCE_OSCAL_UUID <> p.OSCAL_UUID
   OR f.TARGET_OSCAL_UUID <> c.OSCAL_UUID;
```

Expected: `0`.

### 8.6 Parent and child must belong to the same source/root record

```sql
SELECT COUNT(*) AS CROSS_RECORD_RELATIONSHIPS
FROM <FACT_TABLE> f
JOIN <DIM_TABLE> p
  ON f.FK_SOURCE_ELEMENT_HASH = p.<DIM_PK>
JOIN <DIM_TABLE> c
  ON f.FK_TARGET_ELEMENT_HASH = c.<DIM_PK>
WHERE p.SOURCE_RECORD_ID <> c.SOURCE_RECORD_ID;
```

Expected: `0` for the current same-source model graph.

This is one of the strongest tests that a child was not accidentally attached to another Authorization Package / root record.

### 8.7 Current relationship type

The current generic graph builder creates parent-child edges as:

```text
DEPENDENCY_TYPE = 'CONTAINS'
```

Test unexpected values:

```sql
SELECT DEPENDENCY_TYPE, COUNT(*)
FROM <FACT_TABLE>
GROUP BY DEPENDENCY_TYPE;
```

Any unexpected dependency type should be investigated against the code/version being tested.

### 8.8 Every non-root current node has a parent

For the committed snapshot under test, every generated non-root node should be reachable by an incoming FACT edge.

```sql
SELECT COUNT(*) AS ORPHAN_CHILD_NODES
FROM <DIM_TABLE> d
LEFT JOIN <FACT_TABLE> f
  ON d.<DIM_PK> = f.FK_TARGET_ELEMENT_HASH
WHERE d.ELEMENT_TYPE <> '<ROOT_ELEMENT_TYPE>'
  AND f.FK_TARGET_ELEMENT_HASH IS NULL;
```

Expected: `0`, unless a specifically approved model exception is documented.

---

## 9. Root / ancestry integrity

The tester must prove that sampled leaf/child rows trace through FACT relationships to **one and only one correct model root**.

For each model, select at least:

- 5 ordinary source records;
- 2 records with multi-valued collections;
- 2 records with reference/cross-reference mappings;
- every record involved in a discovered defect.

For each sample, document:

```text
Source record
 -> root DIM node
 -> parent DIM node
 -> child DIM node(s)
 -> FACT FK_SOURCE / FK_TARGET
 -> leaf payload value
```

At every hop verify:

- both DIM PKs exist;
- parent/child FACT edge exists;
- FACT UUIDs equal endpoint DIM UUIDs;
- all nodes have the same `SOURCE_RECORD_ID`;
- the chain terminates at the expected model root.

If one child reaches two different roots, or reaches a root with another `SOURCE_RECORD_ID`, log a **relationship-integrity defect**.

---

## 10. Model-specific focus areas

### SSP

Tester should prioritize:

- Metadata fields and document IDs;
- responsible roles / parties / responsible-party references;
- System Characteristics name, short name, description, system IDs;
- authorization boundary;
- status / remarks;
- properties;
- security impact objectives;
- System Implementation component references and hydration;
- Control Implementation remains separately deferred where source/SME semantics are unresolved.

Known timestamp timezone issue must remain separately tracked.

### POAM

Validate:

- POAM root and `poam-items[]` structure;
- each item belongs to the correct source/root;
- item-level fields match approved CSV transforms;
- parent-child FACT relationships resolve correctly;
- no duplicate item identities for the same source record.

Do not infer completeness from historical POAM preview counts; use the actual committed/test snapshot.

### Assessment Results

Validate:

- Assessment Results root and `results[]`/observation/findings structures that are currently executable;
- scalar-score transformations;
- preserved NULL behavior where explicitly configured;
- any finding/reference mapping only if its CSV status is executable;
- relationship integrity from result/observation nodes back to the correct Assessment Results root.

Do not assume that an OSCAL model name implies a separate Archer RAW table. The current source binding is defined by the mapper configuration/mapping, not by the OSCAL target name.

### Security Assessment Plan

Validate only mappings currently executable in the CSV and only against a target that has actually been committed/populated for the tested run. Use the same source-to-DIM and FACT-integrity procedure above.

---

## 11. Excel/notes versus runtime CSV

The Excel review material and mapping notes are important semantic evidence, but the executable runtime artifact is:

```text
Mapping/ARCHER_OSCAL_MAPPINGS.csv
```

Tester procedure:

1. use the CSV to determine what the current code actually executes;
2. use Excel/notes to confirm the intended business/OSCAL meaning and transformations;
3. if Excel/notes conflict with the executable CSV, **do not silently choose one**;
4. record the discrepancy as a mapping defect / SME-review item.

The tester is validating both:

```text
technical correctness
AND
mapping intent
```

but business/SME semantic approval remains separate from a purely technical PASS.

---

## 12. Tester defect categories

Use these labels in the test report:

```text
SOURCE_VALUE_MISMATCH
TRANSFORM_MISMATCH
WRONG_OSCAL_TARGET
MISSING_TARGET_NODE
EXTRA_TARGET_NODE
DUPLICATE_DIM_PK
DUPLICATE_OSCAL_UUID
MISSING_FACT_PARENT
MISSING_FACT_CHILD
FACT_UUID_MISMATCH
CROSS_ROOT_RELATIONSHIP
WRONG_COLLECTION_CARDINALITY
UNRESOLVED_REFERENCE
UNEXPECTED_NULL
UNEXPECTED_POPULATED_VALUE
CSV_EXCEL_CONFLICT
KNOWN_DEFERRED_SME
```

For every defect capture:

```text
model
source record ID
source field/value
RULE_ID
TRANSFORM_ID
expected target path/value
actual DIM PK/ELEMENT_TYPE/METADATA_JSON
related FACT PK/FKs
expected result
actual result
screenshot/query evidence
```

---

## 13. Minimum sign-off checklist per model

A model should not be signed off until the tester can answer **YES** to all applicable items:

- [ ] Mapping inventory/counts reconciled to current CSV.
- [ ] Every executable mapping rule has test evidence or an approved sampling rationale.
- [ ] Transformation results match source + CSV rules.
- [ ] DIM PKs are non-null and unique.
- [ ] OSCAL UUID integrity passes.
- [ ] Exactly one correct root exists per processed source record.
- [ ] FACT PKs are non-null and unique.
- [ ] Every FACT source FK resolves to DIM.
- [ ] Every FACT target FK resolves to DIM.
- [ ] FACT source/target UUIDs match the corresponding DIM UUIDs.
- [ ] Parent and child belong to the same source/root record.
- [ ] No unexpected orphan child nodes exist.
- [ ] Sampled leaf-to-root ancestry is correct.
- [ ] Collection cardinality is correct for sampled multi-valued source fields.
- [ ] Deferred/excluded mappings were not incorrectly populated as approved mappings.
- [ ] Known open issues are explicitly listed rather than hidden inside a PASS.
- [ ] Excel/notes versus CSV conflicts are documented for SME decision.

---

## 14. Expected tester deliverable

For each model produce one short result table:

| Test area | Result | Evidence |
|---|---|---|
| Mapping inventory | PASS/FAIL | counts + CSV version |
| Source-to-target values | PASS/FAIL | sampled RULE_IDs / SQL |
| Transformations | PASS/FAIL | source vs expected vs actual |
| DIM PK/UUID integrity | PASS/FAIL | SQL results |
| FACT FK integrity | PASS/FAIL | SQL results |
| Same-root relationship integrity | PASS/FAIL | joined parent/child evidence |
| Collection cardinality | PASS/FAIL | sample source vs node counts |
| Deferred/excluded behavior | PASS/FAIL | CSV/status evidence |
| Known SME/open issues | OPEN/CLOSED | issue references |

Final conclusion must distinguish:

```text
DATA_MAPPING_VALIDATED
RELATIONSHIPS_VALIDATED
SEMANTIC_SME_REVIEW_PENDING
KNOWN_DEFECTS
TARGET_NOT_YET_COMMITTED / NOT_TESTABLE
```

Do not use a single generic "PASS" if any of these statuses differ.
