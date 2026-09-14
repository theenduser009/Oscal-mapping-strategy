# OSCAL / Archer SME Open Questions

Date: 2026-09-14
Branch: `simplify-metadata-boundary`

Purpose: keep the current unresolved SME questions in one place so they can be copied directly into chat/email and answered without losing the technical context.

## 1. Profile `imports[]` / `href`

In Archer, `BASELINE_RECOMMENDATION` is the candidate source for OSCAL `profile.imports[]`.

We verified that `BASELINE_RECOMMENDATION` is a **Values List field**, not a URL or cross-reference. Observed values resolve as:

- `162398` -> `LOE A`
- `162399` -> `LOE B`
- `162400` -> `LOE C`
- `162401` -> `LOE D`
- `162402` -> `DFARS`
- `162403` -> `GS Labs`
- `177494` -> `Basic`

OSCAL `profile.imports[]` requires an `href` identifying the Catalog/Profile being imported.

**Question for SME:**

> For values such as `DFARS`, `LOE A`, `LOE C`, `GS Labs`, etc., where do we get the actual Catalog/Profile reference that should become OSCAL `profile.imports[].href`? Is there another Archer field/application or an approved lookup that maps these Baseline Recommendation values to a specific Catalog/Profile resource?

Also confirm whether the import should use `include-all` or `include-controls`, and what Archer source determines that selection.

---

## 2. What exactly is Archer `Import Profile`?

The Archer relationship diagram shows `System Security Plan (SSP)` connected to `Import Profile`.

**Question for SME:**

> What Archer application/field/relationship does `Import Profile` represent? Is it a cross-reference to another Archer record, and if so, which application and field contain the actual Profile/Catalog identifier or location?

If possible, provide the Archer application name, field name, FieldId, field type, and referenced application.

---

## 3. Control Implementation source table / LevelId 355

For SSP Control Implementation, the Authorization Package field `ALLOCATED_CONTROLS` was read back as Archer cross-reference objects such as:

```json
{
  "ContentId": 573482,
  "LevelId": 355
}
```

We verified that `ARCHER_META_FIELD` contains many control-oriented fields for `LEVEL_ID = 355`, including examples such as:

- `CONTROL_NUMBER`
- `CONTROL_NAME`
- `IMPLEMENTATION_DETAILS`
- `OVERALL_IMPLEMENTATION_DETAILS`
- `IMPLEMENTATION_STATUS`
- `CONTROL_PARAMETERS`
- `RESPONSIBLE_ROLE`
- `CONTROL_ENTITY`
- `CONTROL_SET`

**Question for SME:**

> What Archer application/module does `LevelId = 355` belong to, and which physical RAW table contains the referenced `ContentId` records such as `573482`?

If there is a standard metadata relationship, please explain how to resolve:

`LevelId -> Level Name / Module Name -> RAW table`

We currently see these metadata tables in Snowflake:

- `ARCHER_META_CONTENT`
- `ARCHER_META_FIELD`
- `ARCHER_META_LEVEL`
- `ARCHER_META_VALUE`

If one of these is the authoritative way to resolve LevelId to the source application/table, please identify the join path and key columns.

---

## 4. How should Level 355 control records map into OSCAL SSP Control Implementation?

NIST OSCAL SSP expects the major branch:

```text
system-security-plan
  -> control-implementation
     -> implemented-requirements[]
```

with native structures such as `control-id`, `responsible-roles[]`, statements/by-components, parameter settings, and `props[]` for supplemental properties.

**Question for SME:**

> For the Level 355 Archer control record, which fields are considered authoritative for the actual implemented control and implementation response?

In particular, should we treat fields such as:

- `CONTROL_NUMBER` as the control identifier,
- `IMPLEMENTATION_DETAILS` / `OVERALL_IMPLEMENTATION_DETAILS` as implementation narrative,
- `RESPONSIBLE_ROLE` as responsibility,
- `CONTROL_PARAMETERS` as parameter settings,
- and fields like allocation status / helper flags / workflow data as supplemental `props[]`?

Please confirm the intended business meaning before we finalize the OSCAL mapping.

---

## 5. Cross-reference routing pattern

The current mapper already supports ContentId-based hydration when the lookup/source binding is known. What is still missing for this Control Implementation branch is the source binding for `LevelId 355`.

**Question for SME:**

> Is there an existing Archer metadata/API rule that maps every `{ContentId, LevelId}` cross-reference to its source application/module, or are these source bindings maintained manually/configured elsewhere?

If there is an existing registry, lookup, API operation, or metadata table for this, please point us to it so we can reuse the same approach generically rather than hardcoding Level 355.

---

## Current evidence status

Confirmed from owner-provided Snowflake read-back on 2026-09-14:

- `BASELINE_RECOMMENDATION` is a values-list field with the labels listed above.
- `ADD_OVERLAY` was null across the inspected Authorization Package snapshot.
- `ALLOCATED_CONTROLS` contains `{ContentId, LevelId}` reference objects.
- the observed control reference `LevelId` is `355`.
- `ARCHER_META_FIELD` returned 210 fields for `LEVEL_ID = 355`.

Not yet confirmed:

- Profile `href` source.
- Exact meaning/source of Archer `Import Profile`.
- Physical RAW table for Level 355 control records.
- Generic `LevelId -> source table` resolution rule.
- Final field-by-field OSCAL mapping for the Level 355 control record.
