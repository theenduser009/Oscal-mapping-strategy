# Archer Metadata Relationship Guide

## Purpose

This document explains how Archer metadata tables can be used to understand application structure, fields, values lists, and cross-reference relationships. It is intended as technical discovery support for conceptual/logical data modeling. Metadata relationships should be treated as technical evidence and validated against business meaning before becoming final CDM relationships.

## Metadata Structure

A useful mental model is:

```text
Levels / Applications
    ↓
Fields
    ↓
Relationships or Values
```

### `Archer_Meta_Levels`

Represents Archer applications/levels. Use this table to determine which application or level a field belongs to.

### `Archer_Meta_Fields`

Represents fields defined within Archer levels/applications. It can provide field identifiers, field names, field types, descriptions when maintained, and the owning level.

Use it to answer questions such as:
- Which fields belong to an application?
- What type is a field?
- Which level owns a field?
- Is a field description available?

### `Archer_Meta_Field_Relationships`

Represents metadata describing cross-reference/related-record relationships between Archer fields and applications.

This is configuration/schema relationship metadata rather than row-level business data. It is useful for discovering which reference fields connect one Archer application to another.

### `Archer_Meta_Values`

Contains values associated with values-list fields, such as dropdown or selectable-list options.

If a field is identified as a Values List field, this table can be used to inspect its configured values.

## CR and RR Field IDs

### `CR_FieldID`

`CR_FieldID` represents the Cross-Reference Field ID.

Conceptually, this is the source-side reference field: the field containing or defining a reference to another Archer record/application.

### `RR_FieldID`

`RR_FieldID` represents the Related Record Field ID.

Conceptually, this identifies the related-record side associated with the cross-reference relationship.

A simplified interpretation is:

```text
Source application / cross-reference field
                  ↓
             CR_FieldID
                  ↓
       Field relationship metadata
                  ↓
             RR_FieldID
                  ↓
Target application / related-record field
```

## Why One CR Field Can Have Multiple Relationship Rows

A cross-reference definition can be associated with multiple related-record definitions. Therefore the same `CR_FieldID` may occur in multiple rows with different `RR_FieldID` values.

Do not automatically interpret repeated metadata rows as duplicate data. They may represent a valid one-to-many or multi-target metadata configuration that needs further inspection.

## Relationship Discovery Procedure

To trace a relationship:

1. Identify the source field in `Archer_Meta_Fields`.
2. Capture its field ID and owning level ID.
3. Search `Archer_Meta_Field_Relationships` for that field ID as `CR_FieldID`.
4. Retrieve the associated `RR_FieldID` value(s).
5. Join the `RR_FieldID` value(s) back to `Archer_Meta_Fields`.
6. Use the source and target level IDs to join to `Archer_Meta_Levels`.
7. Translate the numeric metadata into a readable relationship:

```text
Source Application / Field → Target Application / Field
```

This process provides technical evidence that an Archer reference relationship exists.

## Field-Type Guidance

### Values List

For a Values List field, inspect `Archer_Meta_Values` to understand configured selectable values.

### Cross Reference / Related Record

For Cross Reference or Related Record fields, inspect `Archer_Meta_Field_Relationships` to understand application/field relationships.

## Field Descriptions

Field descriptions in Archer metadata may be incomplete:

- some fields have maintained descriptions;
- some descriptions may contain HTML/SDML-style formatting;
- some descriptions may be null.

Therefore metadata descriptions are useful input for a data dictionary but should not be assumed to constitute a complete business glossary or authoritative business definition.

## CDM / MVP Modeling Use

For the current modeling scope, metadata should primarily be used for:

1. **Field ownership** — confirm which Archer application owns each field.
2. **Relationship discovery** — identify technical reference links between applications.
3. **Cardinality clues** — identify relationships that may require one-to-many or bridge-table treatment.
4. **Data dictionary support** — obtain field names, types, descriptions, and configured values where available.

For the current four-entity assessment/testing scope, metadata can help investigate relationships among:

- Compliance Engagement
- Control Procedure
- Control Standard
- Control Testing Result

Priority validation questions include:

- Which Control Testing Result field references Compliance Engagement?
- Which Control Testing Result field references Control Procedure?
- Is Control Procedure ↔ Control Standard technically direct, many-to-many, or mediated through another construct?
- Which Archer cross-references represent meaningful business relationships versus optional/configuration-only links?

## Important Modeling Rule

Archer metadata is a **technical discovery source**, not automatically the final business model.

Use:

```text
Archer metadata = technical relationship evidence
Business/process validation = business meaning
CDM = relationship accepted after both are understood
```

A relationship discovered in metadata should not automatically become a direct CDM foreign key. Validate its business meaning, cardinality, current usage, and whether it is in MVP scope first.

## Practical Takeaway

Together, these metadata tables provide a map of Archer's configured structure:

- **Meta Levels** → applications/levels
- **Meta Fields** → fields within applications
- **Meta Field Relationships** → cross-reference/related-record links
- **Meta Values** → configured values-list options

The metadata is especially valuable for systematically discovering potential relationships before validating them with business/process knowledge and incorporating them into the curated/CDM design.
