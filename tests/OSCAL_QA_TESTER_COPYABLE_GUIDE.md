# OSCAL QA Data Validation Workflow

The goal is to validate the actual mapped data end to end for each OSCAL model.

For every executable Archer mapping, confirm that the source field is mapped to the correct OSCAL element, the transformation is correct, the payload contains the expected value, and the DIM/FACT relationships connect that node to the correct parent and root.

## 1. Test one OSCAL model at a time

Examples:

- System Security Plan
- POA&M
- Assessment Results
- Assessment Plan

For each model, identify the corresponding DIM table and FACT dependency table.

## 2. Start with one mapping row

For each Archer field being tested, capture:

- Archer source field
- source record ID
- source value
- OSCAL model
- OSCAL element path
- transformation
- expected target value

Only mappings that are currently executable should be expected in the target. Deferred or excluded mappings should not automatically be treated as defects.

## 3. Pick one real source record

Select one actual source record and use the same record throughout the validation.

Read the source JSON and confirm the Archer field value before checking the target.

## 4. Validate the transformation

Compare:

```text
Source value
    -> transformation rule
    -> expected OSCAL value
```

Examples of transformations that may need validation:

- direct
- text
- identifier
- date
- timestamp
- Values List lookup
- status crosswalk
- security-objective transformation
- property creation
- reference creation
- null-preservation behavior

A row simply existing is not enough. The transformed value must be correct.

## 5. Find the expected OSCAL node in the DIM table

Locate the DIM row for the selected source record and expected OSCAL element.

Validate:

- the expected element/node exists;
- the node belongs to the correct source record;
- the expected mapped data appears in `METADATA_JSON`;
- the payload member name is correct;
- the value is correct after transformation;
- the datatype/shape is correct;
- required content is present;
- unexpected duplicate content is not present.

## 6. Validate the DIM primary key and UUID

For every generated node verify:

- DIM primary key is not NULL;
- DIM primary key is unique;
- the same logical node is not duplicated unexpectedly;
- OSCAL UUID is valid where applicable;
- UUID does not incorrectly collide with another logical node.

## 7. Validate the FACT relationship

The FACT table connects parent and child DIM nodes.

Conceptually:

```text
Parent DIM PK
      |
      | FACT FK_SOURCE
      v
Relationship
      |
      | FACT FK_TARGET
      v
Child DIM PK
```

For each relationship verify:

- `FK_SOURCE_ELEMENT_HASH` resolves to an existing parent DIM row;
- `FK_TARGET_ELEMENT_HASH` resolves to an existing child DIM row;
- the parent is the expected OSCAL parent;
- the child is the expected OSCAL child;
- the relationship type is correct;
- there are no orphan FACT records.

## 8. Validate root-to-leaf hierarchy

Do not only search for the target value.

Prove that it exists at the correct OSCAL path.

Example:

```text
System Security Plan
    -> System Characteristics
        -> Props[]
```

Another example:

```text
System Security Plan
    -> Metadata
        -> Parties[]
```

Another example:

```text
Assessment Results
    -> Results[]
        -> Observations[]
```

The tester should be able to walk from the root to the leaf through DIM and FACT records.

## 9. Validate leaf-to-root ownership

Also validate the reverse direction.

Start from the mapped leaf node and follow its parent relationships back to the model root.

Confirm that every node belongs to the same intended source/root record.

A child from one Authorization Package, POA&M, Assessment Result, or Assessment Plan must not be linked to another root by mistake.

## 10. Validate collections

Any OSCAL path containing `[]` is a collection.

Examples:

- `props[]`
- `parties[]`
- `roles[]`
- `responsible-parties[]`
- `system-ids[]`
- `components[]`
- `poam-items[]`
- `observations[]`
- `findings[]`
- `tasks[]`

For collection mappings validate:

- expected number of child nodes;
- no missing valid source items;
- no unintended duplicate child nodes;
- every child has the correct parent;
- every child belongs to the correct root.

Do not assume one mapping row equals one DIM row. One mapping rule can apply to many source records, and a collection mapping can produce multiple DIM rows for one source record.

## 11. Validate source lineage

For every target node verify the source lineage fields point to the expected source record and source location.

Examples include:

- `SOURCE_RECORD_ID`
- `SOURCE_SYSTEM_NAME`
- `SOURCE_TABLE_NAME`

This helps detect cross-record or cross-source contamination.

## 12. Validate null and missing-value behavior

Distinguish between:

- source key missing;
- source key present with JSON null;
- source key present with blank text;
- source key present with a real value.

Validate the target behavior according to the mapping rule and null policy.

A missing key and an explicit JSON null should not automatically be treated as the same case.

## 13. Validate duplicates and integrity

Check for:

- duplicate DIM primary keys;
- duplicate OSCAL UUIDs where uniqueness is expected;
- duplicate logical nodes;
- duplicate FACT keys;
- duplicate parent-child relationships;
- orphan FACT foreign keys;
- child nodes linked to the wrong source/root.

## 14. Repeat the same pattern for every implemented model

### System Security Plan

Validate implemented paths under areas such as:

```text
SSP root
  -> Metadata
  -> System Characteristics
  -> System Implementation
```

Then validate their implemented child elements.

### POA&M

Validate:

```text
POA&M root
  -> POA&M Items[]
  -> implemented child content
```

Confirm every item belongs to the correct POA&M/root.

### Assessment Results

Validate:

```text
Assessment Results root
  -> Results[]
  -> implemented Observations[] / Findings[] / other children
```

Validate both mapped values and relationship integrity.

### Assessment Plan

Validate:

```text
Assessment Plan root
  -> implemented child elements / Tasks[]
```

Validate payloads, primary keys, foreign keys, and correct root ownership.

## 15. Record the result for every Archer field

Use the following test record:

```text
TEST CASE ID:

OSCAL MODEL:

SOURCE RECORD ID:

ARCHER SOURCE FIELD:

SOURCE VALUE:

MAPPING STATUS:

OSCAL ELEMENT PATH:

TRANSFORMATION:

EXPECTED TARGET VALUE:

TARGET DIM TABLE:

TARGET ELEMENT TYPE:

DIM PRIMARY KEY:

OSCAL UUID:

TARGET METADATA_JSON:

TARGET VALUE CORRECT: PASS / FAIL

FACT PARENT RELATIONSHIP FOUND: PASS / FAIL

FACT SOURCE FK RESOLVES: PASS / FAIL

FACT TARGET FK RESOLVES: PASS / FAIL

CORRECT PARENT: PASS / FAIL

CORRECT ROOT: PASS / FAIL

DUPLICATE CHECK: PASS / FAIL

COLLECTION COUNT CHECK: PASS / FAIL / N/A

FINAL RESULT: PASS / FAIL

COMMENTS / DEFECT:
```

## Main QA rule

For every Archer field, verify the source value, verify the transformation, verify the value in the correct OSCAL DIM node, validate the node payload and primary key, and then use the FACT table to prove that the node belongs to the correct parent and ultimately the correct model root.
