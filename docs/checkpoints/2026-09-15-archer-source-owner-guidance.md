# Archer source-owner guidance — OSCAL mapping checkpoint

**Evidence date:** 2026-09-15  
**Status:** Source-owner/technical-owner conversation supplied by project owner. This checkpoint records what was stated, separates confirmed guidance from suggestions/uncertainty, and supersedes earlier assumptions where explicitly noted below.

## 1. Why this checkpoint matters

This conversation clarified several source semantics that were previously being inferred from mapping notes, screenshots, and first-pass AI recommendations. The most consequential corrections concern:

- Authorization Package `ALLOCATED_CONTROLS`;
- how `{ContentId, LevelId}` references should be treated;
- where the actual Control Implementation detail lives;
- `BASELINE_RECOMMENDATION` and OSCAL Profile assumptions;
- Archer Values List resolution;
- `%` / `PCT` SQL field-name normalization;
- which transient Authorization Package control fields matter for the snapshot;
- the difference between source-owner technical guidance and final compliance/business approval.

This evidence does **not** by itself constitute final NIST/OSCAL business approval for unresolved mappings.

---

## 2. `ALLOCATED_CONTROLS` is a cross-reference/linkage field

### Source-owner guidance

The Authorization Package `ALLOCATED_CONTROLS` field does not contain the full Allocated Control business record. It contains references to Allocated Control records.

Observed source shape:

```json
[
  {
    "ContentId": 573482,
    "LevelId": 355
  }
]
```

The source owner described each `{ContentId, LevelId}` pair as the linkage between the Authorization Package record and an Allocated Control record.

### Confirmed metadata evidence already read back

For the example reference:

- `ContentId = 573482`
- `LevelId = 355`
- `ARCHER_META_CONTENT` confirmed `573482 -> 355`.
- `ARCHER_META_LEVEL` resolved Level 355 to:
  - `LEVEL_NAME = CONTROL`
  - `MODULE_ID = 549`
  - `MODULE_NAME = ALLOCATED CONTROLS`

The source Authorization Package level was resolved as Level 353.

### Cardinality guidance

The source owner stated that one Authorization Package generally has many Allocated Controls, with examples ranging roughly from 20 to 130 controls per package.

Treat that range as source-owner operational context, not as an enforced data-model cardinality constraint until profiled from current data.

### Development decision

Preserve the source reference information. Do not reinterpret the `ALLOCATED_CONTROLS` JSON itself as the complete OSCAL Control Implementation payload.

Recommended source lineage to preserve:

```text
Authorization Package ContentId
        -> ALLOCATED_CONTROLS[]
        -> referenced ContentId + LevelId
        -> Allocated Control record
```

Although the source owner stated that ContentIds are unique and could potentially be used alone, preserving both `ContentId` and `LevelId` is preferred for explicit source lineage and source-type resolution.

Do **not** replace the source `LevelId` with an OSCAL filename in the canonical source contract. The source owner mentioned that only as a possible implementation idea, not as an established rule.

---

## 3. Actual Control Implementation details belong to the Allocated Control dataset

The source owner stated that the Allocated Control record contains the substantive control information needed later, including concepts such as:

- whether/how the control is implemented or satisfied;
- implementation detail;
- control statement information;
- full/partial/inherited implementation concepts;
- testing/assessment-related information;
- whether testing is automated;
- other GRC control information.

The exact OSCAL destination for each source field is **not yet approved** by this conversation.

### Current OSCAL implication

The intended discovery chain is therefore:

```text
Authorization Package
    -> ALLOCATED_CONTROLS references
    -> Allocated Control records
    -> inspect actual Allocated Control fields
    -> map approved fields into SSP control-implementation
       / implemented-requirements[] and appropriate descendants
```

### Current source gap

At the time of this checkpoint, metadata for Module 549 / Level 355 exists, but a corresponding physical Allocated Controls content RAW table has not been read-back verified in the current Snowflake schema.

Do not claim that `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW` exists merely because ingestion naming logic could derive that name. Naming derivation is not proof of ingestion/existence.

If the dataset is not loaded, this is a **source-ingestion gap**, not an OSCAL-mapper defect.

---

## 4. Authorization Package control-related fields that may be transient

The source owner stated that fields such as:

- Inherited Control Selection
- Inheritable Controls

are transient/workflow-oriented and generally empty except while automation/work is occurring in the Allocated Controls process. The source owner said these do not need to be mapped for the intended snapshot.

`Archived Control` was not confirmed; the source owner said it would require additional review.

### Mapping rule

Do not automatically turn transient/helper control fields into OSCAL props merely because they exist in Archer metadata. Preserve their deferred/excluded status until the intended snapshot semantics are confirmed.

---

## 5. Control Implementation `props` and `ns`

The source owner did **not** confirm that Control Implementation requires a URL from Archer.

Discussion around OSCAL `props[]` included `name`, `ns`, `value`, and `remarks`, but the source owner was uncertain about the OSCAL meaning of `ns` and did not approve a source mapping for it.

### Development rule

Do not invent a URL or namespace from Archer source values.

If Archer-specific attributes are ultimately preserved as OSCAL extension properties, the project needs an approved OSCAL property-name and namespace convention. That remains a design/compliance decision.

---

## 6. `BASELINE_RECOMMENDATION` — earlier Profile assumption superseded

### Archer behavior confirmed by source owner

`BASELINE_RECOMMENDATION` is an Archer Values List field (the source owner described it as Field Type 4).

Fields containing `ValuesListIds` are resolved through `ARCHER_META_VALUE`.

Example discussed:

```text
ValuesListId 162402 -> DFARS
```

The text/business value for that field is therefore `DFARS`.

### Consequential correction

The source owner explicitly characterized the earlier interpretation of:

```text
BASELINE_RECOMMENDATION -> OSCAL profile.imports[].href
```

as an **AI mismatch** based on the actual Archer semantics.

Therefore the previous hypothesis that `BASELINE_RECOMMENDATION` should directly supply or determine `profile.imports[].href` is **SUPERSEDED as of 2026-09-15**.

Do not implement that mapping unless later business/compliance evidence explicitly approves a transformation/crosswalk.

### Source-owner semantic explanation

The source owner described `BASELINE_RECOMMENDATION` as more like a subset/risk modifier influencing which controls are required under a control set, rather than the authoritative control-set/profile resource reference itself.

The environment can use multiple NIST control sets/versions, so a value such as `DFARS` alone does not uniquely establish the OSCAL imported Profile/Catalog resource.

### Potential better source — not yet approved

The source owner suggested that a control-set-related field such as `CONTROL_SET_VERSION_NUMBER` may be a better candidate for the control-set concept.

This is a **proposal requiring compliance/business SME validation**, not an approved mapping.

Suggested review note:

> Source owner believes this may map more naturally to control-set semantics; validate with compliance/business SME before approving an OSCAL target.

---

## 7. Values List resolution contract

For Archer fields whose payload contains `ValuesListIds`, the intended technical lookup is:

```text
RAW JSON ValuesListIds[]
    -> ARCHER_META_VALUE.SELECT_VALUE_ID
    -> readable select-value name
```

Example:

```text
162402 -> DFARS
```

This is distinct from a cross-reference payload containing `{ContentId, LevelId}`.

### Important distinction

```text
ValuesListIds[]
    = select/dropdown/value-list semantics

{ContentId, LevelId}
    = record/reference linkage semantics
```

Do not process these two source shapes as though they are equivalent.

---

## 8. `%` / `PCT` field-name normalization issue

The source owner explained that some Archer developers historically used special characters such as `%` at the beginning of field names.

An older normalization implementation explicitly replaced `%` with `PCT` so the result could become a valid/readable SQL field name.

A newer manually written large `REPLACE()` expression stripped the special character instead, causing inconsistent normalized field names between metadata and other transformation logic.

### Example consequence

A field expected under a normalized name such as:

```text
PCT_CURRENT_AVERAGE_RISK
```

may not be found if `%` was stripped rather than translated consistently to `PCT`.

### Source-owner acknowledgement

The source owner acknowledged that if `ARCHER_META_FIELD.SQL_FIELD_NAME` normalization and the content transformation normalization do not match, that is an upstream naming/ETL consistency issue that should be fixed.

### Development rule

Do **not** compensate for inconsistent `%` / `PCT` normalization inside the OSCAL mapper.

Fix or standardize the Archer metadata/content normalization upstream, then keep OSCAL mappings based on the canonical normalized source field names.

---

## 9. Generic Archer JSON normalization pattern

The project currently uses/has discussed a generic Snowflake/Matillion pattern for Archer JSON:

```text
RAW_DATA
  -> normalize array/object wrapper
  -> RequestedObject.FieldContents
  -> LATERAL FLATTEN (dynamic FieldIds become rows)
  -> join FieldId to ARCHER_META_FIELD
  -> resolve SQL_FIELD_NAME
  -> use Archer Type to preserve/convert datatype
  -> process nested FieldContents where applicable
  -> combine fields
  -> rebuild normalized representation / materialize downstream structure
```

### Why `LATERAL FLATTEN` matters

Archer uses dynamic numeric FieldIds as keys beneath `RequestedObject.FieldContents`. The parser should not hardcode each FieldId.

`LATERAL FLATTEN` allows Snowflake to enumerate every child under `FieldContents` regardless of its key name, while retaining the parent record context.

Conceptually:

```text
FieldContents JSON object
    -> one row per dynamic FieldId
    -> metadata lookup
    -> readable field name + typed value
```

This avoids application-specific Python loops for FieldId discovery.

---

## 10. Physical-column requirement vs current CURATED_JSON approach

A technical discussion clarified a possible/desired upstream requirement different from the current `CURATED_JSON` VARIANT pattern.

### Current normalization pattern

The current generic SQL resolves fields and ultimately aggregates them into a readable `CURATED_JSON` VARIANT object.

### Alternative requirement discussed

The technical requirement may instead be to materialize each resolved Archer field as an actual Snowflake column:

```text
FieldId
 -> ARCHER_META_FIELD.SQL_FIELD_NAME
 -> Archer Type -> Snowflake datatype
 -> physical Snowflake column
 -> source Value
```

Example concept:

```text
FieldId 23229
Type 21
Value 2020-07-30T12:10:29.5
    -> resolve SQL_FIELD_NAME
    -> timestamp-compatible datatype after approved type mapping
    -> populate physical column
```

The existing `norm -> flat -> mapped -> typed` logic is reusable for this. The major design change would occur after typing: instead of only `OBJECT_AGG -> CURATED_JSON`, dynamically create/pivot/populate physical columns.

### Important caution

The exact Archer-Type-to-Snowflake-datatype crosswalk must be confirmed. Do not assume, for example, that Type 21 is Snowflake `DATE` if the source value contains time-of-day; a `DATE` would discard that information.

---

## 11. RAW ingestion (`COPY INTO`) context

The generic Matillion/Snowflake RAW load uses a dynamic target table variable and Snowflake staged-file metadata.

Key concepts:

- `${jv_raw_table_name}` = Matillion variable identifying the current RAW target table.
- `t.$1` = first staged-file field; for the Archer JSON load this is the JSON payload loaded into `RAW_DATA`.
- `METADATA$FILENAME` = Snowflake-provided staged-file metadata giving the source filename/path.
- `METADATA$START_SCAN_TIME` = Snowflake-provided staged-file metadata giving scan timing.
- `${jv_year}`, `${jv_month}`, `${jv_day}`, `${jv_stage_name}`, `${jv_stage_path}`, `${jv_file_format_name}` = Matillion variables/configuration.

The ingestion component is upstream of Archer normalization and upstream of OSCAL mapping.

---

## 12. New `ARCHER_OSCAL_*` physical naming direction

A planned naming change was communicated for OSCAL-source RAW tables, with Authorization Package shown as moving from an older `ARCHER_CONTENT_*` style to an `ARCHER_OSCAL_*` style.

At the time of discussion, this was a **planned/communicated naming direction**, not yet read-back verified as existing physical Snowflake tables.

### Development rule

Do not rewrite the seven-cell OSCAL mapper for a physical source-table rename.

Update logical source bindings / Matillion table-name configuration after the new tables are actually created and read-back verified. Keep logical CSV source keys stable where possible.

---

## 13. What is confirmed vs unresolved

### Confirmed / strong source-owner guidance

- `ALLOCATED_CONTROLS` is linkage to Allocated Control records, not the full control payload.
- `{ContentId, LevelId}` is the relevant Archer reference shape.
- One Authorization Package can reference many Allocated Controls.
- Actual control implementation detail is expected in the Allocated Control dataset.
- `BASELINE_RECOMMENDATION` is a Values List and example `162402` resolves to `DFARS`.
- Direct `BASELINE_RECOMMENDATION -> profile.imports[].href` is an AI mismatch and is superseded.
- Values List IDs should be resolved through Archer value metadata.
- `%`/`PCT` naming inconsistency is upstream normalization/ETL behavior, not an OSCAL semantic rule.
- Dynamic FieldIds under `FieldContents` can be enumerated without hardcoded loops using Snowflake `LATERAL FLATTEN`.

### Still unresolved / requires additional evidence

- Final OSCAL destination for `BASELINE_RECOMMENDATION`.
- Whether/how `CONTROL_SET_VERSION_NUMBER` or other control-set fields map into OSCAL Profile/Catalog concepts.
- Exact physical RAW dataset/table for Allocated Controls and whether it is currently ingested.
- Exact mapping of Allocated Control fields into `implemented-requirements[]`, statements, by-components, responsible roles, parameters, props, and assessment structures.
- Approved OSCAL extension property namespace (`ns`) convention.
- Exact Archer Type -> Snowflake physical datatype crosswalk for the proposed relational-column materialization.
- Whether the new `ARCHER_OSCAL_*` tables have been physically created and loaded.

---

## 14. Consequential supersedence statement

**As of 2026-09-15, this checkpoint supersedes any earlier project statement that treated `BASELINE_RECOMMENDATION` as an established source for OSCAL `profile.imports[].href`.**

The field remains useful source data, but its final OSCAL semantic mapping is unresolved pending business/compliance review.

This checkpoint also strengthens the treatment of Authorization Package `ALLOCATED_CONTROLS` as a source cross-reference whose target records must be mapped from the Allocated Controls dataset rather than interpreting the reference array itself as the complete Control Implementation object.
