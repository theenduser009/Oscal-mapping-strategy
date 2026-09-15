# OSCAL / Archer SME Open Questions

Updated: 2026-09-15
Branch: `simplify-metadata-boundary`

Purpose: keep the current unresolved SME questions in one place so they can be copied directly into chat/email and answered without losing the technical context. Newer verified evidence supersedes older assumptions below where stated.

## 1. Profile `imports[]` / `href`

`BASELINE_RECOMMENDATION -> profile.imports[].href` is **not approved**. Source-owner discussion on 2026-09-15 identified Baseline Recommendation as an LOE/control-scope concept; Control Set / authoritative-source information is a stronger candidate, but final OSCAL Profile semantics require SME/compliance confirmation.

Observed Baseline Recommendation values include LOE A/B/C/D, DFARS, GS Labs, and Basic.

**Question for SME:**

> What RTX Archer source identifies the actual Catalog/Profile resource that should become OSCAL `profile.imports[].href`? Is Control Set, Authoritative Source, or another relationship the authoritative source? Also, what determines `include-all` versus `include-controls`?

---

## 2. What exactly is Archer `Import Profile`?

**Question for SME:**

> What Archer application/field/relationship represents the source concept corresponding to OSCAL Profile/import behavior? If it is a cross-reference, which application and field contain the authoritative Catalog/Profile identifier/location?

---

## 3. Allocated Controls / Control Implementation source

Newer 2026-09-15 evidence established that the Authorization Package `ALLOCATED_CONTROLS` field is a cross-reference and that Archer metadata can resolve its LevelId to the Allocated Controls module/Control level. Source-owner discussion also described Allocated Controls as copies of Control Standards assigned specifically to an Authorization Package.

The physical/new source-table delivery for Allocated Controls and the final field-by-field OSCAL Control Implementation mapping remain deferred until that dataset and semantics are validated.

**Question for SME:**

> For an Allocated Control record assigned to an Authorization Package, which fields are authoritative for OSCAL `control-implementation.implemented-requirements[]` (control identifier, implementation narrative/status, responsible roles, parameters, by-component details), and which fields are workflow/helper data that should not be mapped?

---

## 4. Generic `{ContentId, LevelId}` cross-reference routing

2026-09-15 metadata read-back showed that `ARCHER_META_LEVEL` can identify the module/level behind a LevelId, and existing source naming logic can derive Archer content names from module/level metadata. This supersedes the earlier assumption that no LevelId-to-source information was available.

**Question for SME / source owner:**

> Is `ARCHER_META_LEVEL` plus the standard Archer content naming convention the authoritative generic routing rule for all `{ContentId, LevelId}` cross-references, or are there RTX exceptions/overrides we must maintain explicitly?

---

## 5. Archer Date/Date-Time timezone semantics for OSCAL

SSP Validation 03 on 2026-09-15 tested the current executable Metadata timestamp mappings (`FIRST_PUBLISHED` / `LAST_UPDATED` and their prefixed equivalents). The mapping contract itself passed, but all **5,626 populated generated timestamp values** lacked an explicit timezone and therefore failed the current OSCAL timezone-bearing date-time lexical check.

Example source/generated shape:

```text
2022-06-22 18:34:18.577
```

Cell 4 currently treats `timestamp` like nonblank text; it does not add/convert timezone information.

Public Archer product documentation indicates Date/Date-Time values are stored as UTC and converted for user display, but that does **not by itself prove** whether the RTX extraction/data-feed preserves the database UTC value or performs another conversion before `CURATED_JSON`.

**Question for SME / Archer source owner:**

> Are the `FIRST_PUBLISHED`, `LAST_UPDATED`, and other Archer Date/Date-Time values delivered into our Snowflake `CURATED_JSON` preserved as UTC database values? If yes, may the OSCAL transform safely serialize a value such as `2022-06-22 18:34:18.577` as `2022-06-22T18:34:18.577Z`? If not, what timezone/conversion rule does the RTX extraction apply?

**Status:** DEFERRED_SME. Do not change Cell 4 timestamp semantics until this source contract is confirmed.

---

## Current evidence status — 2026-09-15

Confirmed/read-back:

- SSP Validation 01: live registry mechanical structure passed.
- SSP Validation 02: current executable SSP CSV mappings compile cleanly against the live registry.
- SSP Validation 03: mapping contract passed, but 5,626/5,626 populated Metadata timestamp values lacked explicit timezone under the current transform.
- Authorization Package `ALLOCATED_CONTROLS` uses `{ContentId, LevelId}` cross-reference objects.
- LevelId metadata can identify the related Archer module/level.
- Source-owner discussion identifies Allocated Controls as package-specific copies of Control Standards.

Deferred / requires SME confirmation:

- Profile/import `href` authoritative source.
- Final Allocated Control -> OSCAL Control Implementation field semantics.
- Whether generic LevelId routing has RTX-specific exceptions.
- RTX extraction timezone semantics for Archer Date/Date-Time fields.
