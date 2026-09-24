# Trace Authorization Package ALLOCATED_CONTROLS through Archer CR/RR metadata — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `7ccc85c72dc5a09d62f06e3e7ad56a1034868200`

## Why this is the next step
Current Level-355 evidence shows:
- the expected Allocated Controls / Control RAW table exists;
- Authorization Package Level-355 reference IDs do not match the control table's top-level CONTENT_ID;
- a 100-reference recursive sample found only three IDs under
  `CONTROL_TO_INHERIT[].ContentId`, which is not enough to treat that inheritance
  field as the primary Authorization Package-to-Control join.

Earlier source-owner guidance says ALLOCATED_CONTROLS is a record-linkage field, and
the September 15 metadata research established CR_FieldID / RR_FieldID relationship
metadata as the correct technical source for discovering reciprocal Archer fields.

## Diagnostic prepared
Root `RUN_NOW.py` now performs one focused read-only trace:

1. identifies the exact Level 353 / Module 547 ALLOCATED_CONTROLS field ID;
2. discovers the current Archer metadata table containing CR_FIELD_ID + RR_FIELD_ID;
3. finds relationship rows where ALLOCATED_CONTROLS appears on either side;
4. resolves reciprocal field IDs back through ARCHER_META_FIELD;
5. isolates reciprocal fields owned by Level 355;
6. profiles those Level-355 fields in the current control RAW data;
7. tests whether their embedded ContentId references match current Authorization Package CONTENT_ID values.

No source values or record IDs are printed. No DML is performed.

## Decision gate
A unique populated Level-355 reciprocal field that links controls back to
Authorization Packages is sufficient evidence to adopt the reverse relationship
for Control Implementation lineage.

Do not infer the join from field names alone.
