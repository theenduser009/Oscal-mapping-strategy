# Profile / Import Profile — Questions for Archer SME

Date: 2026-09-14

## Context

We are mapping Archer Authorization Package data to NIST OSCAL. For the OSCAL Profile model, the candidate target is:

`profile.imports[]`

An OSCAL import needs an actual referenced Catalog/Profile resource (`href`) and a control-selection rule such as `include-all` or `include-controls`.

Current Archer source discovery has confirmed:

- `BASELINE_RECOMMENDATION` is populated with values such as `DFARS`, `LOE A`, `LOE B`, `LOE C`, `LOE D`, `GS Labs`, and `Basic`.
- Those recommendation values do **not** uniquely identify one control-set version in the current source snapshot.
- `ADD_OVERLAY` is currently null in the inspected Authorization Package snapshot.
- The Archer relationship diagram shows a `Profile` node and an `Import Profile` relationship/node associated with SSP.
- Searching the Authorization Package JSON for keys containing PROFILE/IMPORT found `COLLINS_IMPORT`.
- `COLLINS_IMPORT` is null for 2,617 records and populated for 196 records as an Archer select-value object with `ValuesListIds = [160361]`.
- We have **not** established that `COLLINS_IMPORT` is the diagram's `Import Profile` relationship.

## Questions to ask

### 1. What exactly is “Import Profile” in Archer?

In the Archer relationship/data-model diagram, `System Security Plan (SSP)` is connected to `Import Profile`.

**Which Archer application, field, cross-reference, or related record does “Import Profile” represent?**

Please provide, if possible:

- Archer application/module name
- Archer field name
- Field ID
- Whether it is a cross-reference, related-record, values-list, text, URL, or another field type
- The target application/table if it references another Archer record

### 2. Where is the actual Profile/Catalog reference stored?

For OSCAL we ultimately need something equivalent to:

```json
"imports": [
  {
    "href": "<actual catalog-or-profile-reference>",
    "include-all": {}
  }
]
```

**Which Archer value should provide the referenced Catalog/Profile represented by `href`?**

For example, is there an Archer record containing:

- a URL/path,
- a ContentId,
- a document/file reference,
- a catalog/profile identifier,
- a UUID,
- or another value from which the OSCAL reference is derived?

### 3. How does BASELINE_RECOMMENDATION relate to Import Profile?

`BASELINE_RECOMMENDATION` currently contains values such as:

- DFARS
- LOE A
- LOE B
- LOE C
- LOE D
- GS Labs
- Basic

**Is this field only a business recommendation, or is there an approved mapping from each value to a specific Profile/Catalog artifact?**

Example question:

> If an Authorization Package has `BASELINE_RECOMMENDATION = DFARS`, which exact Profile or Catalog should the SSP import?

If there is a mapping table/business rule, please provide it.

### 4. What determines the control selection?

Once the Profile/Catalog is identified, should the OSCAL Profile:

- import all controls (`include-all`), or
- import a specific list (`include-controls`)?

If specific controls are selected, **which Archer field/application is the authoritative source for that list?**

### 5. What is COLLINS_IMPORT?

The Authorization Package source contains `COLLINS_IMPORT`. In the current snapshot it is populated for 196 records with Archer ValuesListId `160361`.

**What business field does `COLLINS_IMPORT` represent, and is it related to the `Import Profile` relationship shown in the Archer diagram?**

If yes, what does value-list ID `160361` mean and how does it lead to the referenced Profile/Catalog?

## Example of the answer we need

An ideal answer would look something like this (example only — not an assumed mapping):

> `Import Profile` is field `<FIELD NAME>` / FieldID `<ID>` on `<ARCHER APPLICATION>`. It cross-references `<TARGET APPLICATION>`. The referenced record's `<FIELD>` contains the authoritative catalog/profile identifier or location. For DFARS, follow that reference rather than deriving the import from the `BASELINE_RECOMMENDATION` label. Use `<FIELD/RULE>` to determine whether all or selected controls are imported.

That information will allow us to implement `profile.imports[]` without hardcoding or inventing an OSCAL `href`.
