# OSCAL / Archer SME Open Questions

Updated: 2026-09-17
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

---

## Source 2 — consolidated issues and proposed resolutions (2026-09-17)

### Scope, evidence and decision boundary

Reviewed repository baseline: **`64cfe17782500db73f636280540f37b29d5a63e0`** on `simplify-metadata-boundary`.

This section consolidates the ten numbered issues from the Source 2 discussion, plus the related wider-scope questions already raised. It does not replace questions 1–5 or their dated evidence. The source record is the four GitHub review CSVs, the maintained code at the baseline above, and the owner's clarification in the OSCAL chat on 2026-09-17. This is a decision register, not a new mapping approval or a completed OSCAL schema audit.

The owner confirmed Source, Topic, Section and Sub-Section are in different tables. The first intended mapping scope is **Source -> Catalog Metadata**, not all four levels or every OSCAL model at once. Source 1 / Authorization Package remains unchanged; adding it to the review workbook is postponed. A consolidated executable CSV with explicit source bindings remains the proposed runtime delivery approach. The workbook/review CSVs do not automatically become executable metadata.

**Do not rewrite or duplicate the seven cells.** The earlier blanket assurance that no cell changes would ever be necessary is superseded by this narrower assessment: supported mappings should reuse existing operators; new source/model bindings belong in Cell 1; an optional property-name capability would require a separately reviewed, backward-compatible change to Cells 3/4 and the runtime metadata. No such enhancement is approved or implemented by this document. Moving one field to an already-supported representation does not itself justify rewriting the engine.

Statuses below describe this question register only. They do not change `EXECUTION_STATUS` in any CSV. `CORE TEXT CAPTURED` means transcription coverage, not semantic approval or runtime readiness.

### Issue index

| ID | Issue | Decision owner | Scope / status |
| --- | --- | --- | --- |
| S2-01 | Explicit property names versus source-field-derived names | Mapping SME + engineering | Catalog Metadata; open |
| S2-02 | `SOURCE_DESCRIPTION` / `INFORMATION` both target `remarks` | Mapping SME / source owner | Catalog Metadata; open, owner Notes clarification recorded |
| S2-03 | Competing publication dates | Source owner + mapping SME | Catalog Metadata; open |
| S2-04 | Competing last-modified dates | Source owner + mapping SME | Catalog Metadata; open; linked to question 5 |
| S2-05 | Review sheets are not the executable mapping contract | Engineering + mapping approver | Implementation gate; not a Source 1 defect |
| S2-06 | Catalog model/storage configuration and live DDL evidence | Engineering / database owner | Implementation gate; DDL committed, execution unverified here |
| S2-07 | Catalog registry hierarchy, identity and null behavior | Engineering + mapping owner | Implementation gate; live registry unverified here |
| S2-08 | Physical Source 2 bindings and actual source shapes | Source owner + engineering | Source pilot first; open |
| S2-09 | Clipped text and ambiguous source keys | Mapping document owner | Affected rows only; open/partly clarified |
| S2-10 | Cross-record hierarchy and Catalog document ownership | Source owner + architect | Full four-level mapping; unresolved design gate |
| S2-11 | Technical/helper/permission fields | Mapping SME + security/source owner | Affected rows; open |
| S2-12 | Alternative models and reference-field meaning | Mapping SME + source owner | Later controls/other models; open |
| S2-13 | Back-matter resources, links and attachments | Mapping SME + source owner | Later Back Matter branch; open |

### S2-01 — Explicit property names

**Evidence:** Source worksheet rows 5, 17, 19, 31, 32, 50 and 57 specify property names different from a slug of the Archer field name. Cell 4 `_metadata_instances` currently uses `_stable_property_name(field)`; Cell 3 `_compile_mapping` has no property-name override parameter.

| Exact Archer field | Property name recorded in the review sheet |
| --- | --- |
| `SOURCE_TRACKING_ID` | `tracking-id` |
| `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL` | `control-count` |
| `COUNT_OF_CONTROLS` | `total-controls` |
| `SOURCE_CRITICALITY_VALUE` | `criticality-value` |
| `AUTH_SOURCES_FILTER` | `filter-category` |
| `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_CONFIRMED_IN_ARCHER` | `confirmed-date` |
| `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_CONTENT_ID` | `archer-content-id` |

**SME question:** Are these exact target property names required, and is an organization-specific property namespace required? For `SOURCE_TRACKING_ID`, confirm whether the intended result is a traceability property, an identifier, or another representation; its incomplete Note is not permission to invent a UUID conversion.

**Engineering proposal — not approved:** Support optional `PROPERTY_NAME` in executable metadata, validate it in Cell 3 and use it in Cell 4. When absent, retain current source-field-derived naming. Do not rename source keys, alter existing Source 1 property names/identities, or relax validation. Source 1 parity, invalid-override tests and deterministic identity checks would be required before publication of that enhancement. This is a capability extension, not seven new cells.

### S2-02 — Description versus additional information

**Evidence:** Source rows 4 (`SOURCE_DESCRIPTION`) and 7 (`INFORMATION`) both target `catalog.metadata.remarks`. `_metadata_assign` rejects different populated values assigned to one singleton member. Actual conflicting Source 2 values have not been inspected; this is a mapping collision risk, not a demonstrated production failure.

**Owner clarification, 2026-09-17:** `SOURCE_DESCRIPTION` describes the authoritative source; its Note also permits a Back Matter resource description. `INFORMATION` means additional information about the source. This clarifies the meaning hidden by the earlier clipped Note, but does not choose the final destination or change the review CSV.

**SME question:** Which field should populate `catalog.metadata.remarks`, and where should the other be preserved? Does `SOURCE_DESCRIPTION` describe the Catalog/source as a whole or a particular linked document? Is `INFORMATION` a simple scalar value, long narrative, formatted text, or something else?

**Previously suggested option — not approved:** `SOURCE_DESCRIPTION -> catalog.metadata.remarks`; `INFORMATION -> catalog.metadata.props[]` with `name=information`. Keep this as a candidate only: suitability depends on the actual content and the agreed OSCAL representation. The field's label alone is not sufficient to approve a property. The alternative mentioned in the source Notes is a description on an actual Back Matter resource; establish which resource before choosing it.

**Until resolved:** Preserve both source fields. No silent overwrite, guessed precedence, automatic concatenation, invented resource, or claim that the prior suggestion was SME-approved. A decision to reuse existing object/property behavior is separate from S2-01's optional naming enhancement.

### S2-03 — Publication-date ownership

**Evidence:** Source rows 46 and 48 map these distinct fields to `catalog.metadata.published`:

- `DATE_CREATED`
- `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_FIRST_PUBLISHED`

**SME/source-owner question:** What event does each date represent: Archer record creation, first publication in Archer, publication of the authoritative source, or publication of the OSCAL document? Which supplies `published`? If fallback is intended, specify its order and when fallback is allowed.

**Proposal — not approved:** Select one evidence-backed owner for the singleton member; retain the other only in an explicitly approved separate location. Do not choose the earliest/latest date or a field merely because its name appears more suitable. Compare the two on the same source records, including equal, different, missing and null cases. Timezone semantics remain governed by existing question 5.

### S2-04 — Last-modified ownership

**Evidence:** Source rows 47 and 49 map these fields to `catalog.metadata.last-modified`:

- `LAST_UPDATED`
- `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_LAST_UPDATED`

**SME/source-owner question:** Do these represent the same update event and extraction stage? Which is authoritative, and what should happen when they differ or one is absent? Does the selected event correctly represent the intended Catalog/document modification time?

**Proposal — not approved:** Define an explicit source and any approved fallback instead of depending on CSV row order or selecting the maximum value. Reuse the existing timestamp question 5 for timezone/serialization decisions; do not append `Z` or assume UTC without the extraction contract. Source 1 timestamp behavior remains unchanged.

### S2-05 — Review metadata versus executable metadata

**Evidence:** The four `SOURCE2_*_MAPPING.csv` files are photographed-worksheet review records. Cell 2 reads CSV, not a multi-tab XLSX. The existing runtime contract uses `SOURCE_FIELD_NAME`, `OSCAL_MODEL`, `EXECUTION_STATUS`, `TRANSFORM_ID`, `RUNTIME_TARGET_PATH`, `RULE_ID`, `SOURCE_KEY` and optional execution columns. An original Note or `Direct` label does not supply all those instructions.

**Question for mapping approver:** Which exact Source/Catalog Metadata rows are approved, and what are their required-value/null rules? Review-path notation, including `prop[@name=...]`, must remain recorded as evidence while the exact canonical runtime destination is validated separately. Do not equate a readable path with confirmed OSCAL conformance.

**Engineering action after approval:** Build executable rows in the agreed consolidated CSV using distinct, verified source bindings. Preserve Source 1 rows and original Notes. Do not load the XLSX into the current CSV reader, auto-approve the workbook, or upload a new duplicate mapper. A new Excel-reading runtime is not requested.

### S2-06 — Catalog model and destination readiness

**Evidence:** The reviewed Cell 1 contains SSP, Assessment Results, POAM and Assessment Plan contracts but no `CATALOG` contract or Source 2 route. `sql/CREATE_CATALOG_TABLES.sql` was committed at `64cfe17782500db73f636280540f37b29d5a63e0` and has now been read back. It defines:

- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_CATALOG_ELEMENT`
- `RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_CATALOG_DEPENDENCY`

**Engineering/database-owner question:** Has this DDL already run, and do the current `DESC TABLE` results match the selected physical contract? No execution result is established by the GitHub file alone. Inspect any newer owner result before asking for a rerun.

**Proposed integration:** Add the Catalog source/model/storage binding in Cell 1 only after the contracts are settled. Catalog Metadata is element/payload data inside the Catalog DIM, with dependency rows in its FACT. A separate physical Catalog Metadata table is not part of the agreed design. Keep the shared loader and Source 1 destinations unchanged.

### S2-07 — Catalog registry, collection identity and null policy

**Evidence:** Cell 3 requires a valid active registry hierarchy. The current live Catalog rows have not been supplied or queried in this review. Setup SQL is not an export of the live registry.

**Engineering/mapping-owner questions:** Which existing registry rows can be reused? For the initial mapped scope, confirm `catalog`, `catalog.metadata`, and `catalog.metadata.props[]` when property mappings are included; their parent paths, `IS_COLLECTION`, `INSTANCE_KEY_RULE`, `ITEM_PATH`, `OPERATOR`, `UUID_POLICY`, `PROCESS_ORDER` and required-member policy must agree with the compiler.

For Catalog properties, should a changed value retain the same element identity or represent a new value-keyed instance? The existing code supports distinct field-based and field-plus-value policies; do not copy an identity policy without deciding the intended update behavior. Value-keyed changes can encounter the loader's obsolete-row block. Also decide actual JSON null versus absent key handling per approved field, without treating string `null` as JSON null.

**Proposal — not approved:** Register only the branch needed for the pilot, preserving every existing Source 1 registry row and identity. Use the existing inspection/setup pattern after read-only checks. Do not weaken obsolete-row protection, reset the registry, or assume every scalar mapped field needs its own registry row. Full-document completeness and warehouse graph validity remain separate gates.

### S2-08 — Source binding and actual data contract

**Owner-confirmed scope:** Source, Topic, Section and Sub-Section are distinct tables. Their physical Snowflake RAW names, key columns and JSON shapes must still be verified; application labels alone are not physical bindings.

**Question for source owner/engineering:** For the Source pilot, identify the fully qualified RAW table, actual record identity column, payload column, any approved duplicate-selection ordering and exact JSON keys. Confirm whether fields arrive as scalars, value-list containers, cross-references, arrays or formatted text, and whether lookup resolution is required.

**Proposal:** Begin with one governed Source record and a focused read-only field-shape/coverage inspection. Extend the same binding checklist to the other three tables when they enter scope. Reuse known `{ContentId, LevelId}` metadata discovery from question 4 rather than claiming it does not exist; verify the Source 2-specific relationship and delivered RAW object. No full source dump or invented `_RAW` table name is required in this register. Keep private record values out of public GitHub.

### S2-09 — Missing text, duplicate-looking keys and evidence coverage

**Evidence:** The 2026-09-16 transcription checkpoint records 56 Source, 52 Topic, 62 Section and 73 Sub-Section occurrences: 243 total, with 120 core-text gaps at that checkpoint. These are historical transcription counts, not approved runtime counts. Source rows 4, 5 and 13 carry clipped Notes. The owner's S2-02 clarification addresses part of row 4's missing meaning; the stored CSV has not been edited and the aggregate gap count has not been reclassified.

**Question for mapping-document owner:** Supply only the exact still-missing cell text that blocks an in-scope decision. For the Source pilot, resolve the full `SOURCE_TRACKING_ID` Note; resolve the duplicate-control Note when controls enter scope. Do not request all four files again: their GitHub review CSVs are already accessible. The original native workbook, when actually accessible, can resolve hidden text but is not a blanket blocker to reviewing readable rows.

**Related source-owner question:** Are underscore variants and apparent duplicate fields genuine separate keys, legacy aliases or duplicated exports? Examples already recorded include `CONTROL_STANDARDS_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS` versus `CONTROL_STANDARDS__FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`, the corresponding `POLICY_LEVEL_3` variants, and `_OF_NONCOMPLIANT_CONTROLS`. Preserve every exact occurrence until confirmed; no automatic normalization, deduplication or substitution of percentage fields for counts.

### S2-10 — Four-table hierarchy and document ownership

**Evidence:** The reviewed Cell 5 resolves parents within each current source record. Cell 6 explicitly rejects `CROSS_RECORD_EDGE`. This is an intentional existing guardrail, not evidence of a Source 1 defect. Four independent source profiles do not by themselves assemble one cross-table Catalog hierarchy.

**SME/source-owner questions:** Does one Source record own one Catalog, or is the document grain different? Which exact reference fields establish Topic -> Source, Section -> Topic and Sub-Section -> Section ownership? Can a child have multiple parents? Which links are ownership, rollups or other cross-references? How should ancestor-sourced and child-sourced metadata interact without creating duplicate Catalog roots or conflicting metadata values?

**Engineering follow-up after evidence:** Review one connected four-record example plus the relevant relationship metadata. Determine whether a governed assembly/input stage or another generic relationship capability is actually necessary; no option is selected here. Do not remove the cross-record guard to make the hierarchy run or claim configuration alone already supports it. A clearly scoped Source-only metadata pilot can precede full hierarchy work, but does not prove the remaining three levels are supported or complete.

### Other questions already raised in the wider Source 2 review

These are deferred from the first Metadata pilot unless a selected field requires them.

| ID | Evidence / exact issue | Question and proposed handling |
| --- | --- | --- |
| S2-11 | Source rows 54–56: `INSERT_DATE`, `UPDATE_DATE`, `CHECKSUM_VALUE`; row 52: `DEFAULT_RECORD_PERMISSIONS -> catalog.metadata.role` | Confirm ETL/helper retention versus explicit OSCAL exclusion. Confirm whether record permissions actually describe OSCAL roles; do not create roles simply from an access-control field name. Proposed: keep ETL fields as provenance unless explicitly approved for OSCAL; leave permission semantics unresolved rather than making them executable. |
| S2-12 | Source row 15 `CONTROL_PROCEDURES` says `Catalog or Component Definition`; other sheets contain alternative/clipped model labels and reference mappings | Which model owns the information, and when are multiple outputs intended? Do references contain IDs, narrative, links or full records? Proposed: resolve source meaning, referenced identity and destination before enabling controls, policies, findings, Assessment Results or Assessment Plan mappings. The sheet's alternatives are not permission to select one silently. |
| S2-13 | Source rows 6, 9, 10: `SOURCE_LINKS`, `TOPIC_REFERENCES`, `ATTACHMENTS`; description alternative in row 4 | What concrete document/resource does each value identify? Are attachments binary/base64 content, attachment metadata, IDs or URLs? Which description belongs to which resource? Proposed: create resources and links only from an explicit source/resource contract; do not fabricate resource UUID relationships or treat arbitrary text as attachment content. |

### Minimum-change plan and next decision

The recommendation is to **resolve meaning before changing execution**. Ask the SME first for S2-02, S2-03 and S2-04: destination ownership for the two text fields, publication-date ownership and last-modified ownership, linked to the existing timezone question. Engineering can prepare the source/target/registry read-only checks without changing the seven cells.

Once the relevant decisions and source shapes are confirmed, select a small Source/Catalog Metadata pilot. Promote only its approved rows, add the required source/model and registry metadata, and test any genuinely needed generic enhancement separately. Preserve Source 1 output/identity parity. PREVIEW comes before an explicitly authorized COMMIT and separate read-back verification. Do not block unrelated readable fields on later controls or full hierarchy questions; do not call a partial pilot a complete Catalog.

| Change category | Current decision |
| --- | --- |
| Seven-cell rewrite, mirror or second Catalog mapper | Not proposed; preserve the existing framework |
| Source 1 mapping, identity, registry and loader changes | Not authorized by this documentation request |
| New Source 2 / Catalog bindings in Cell 1 | Future configuration task; not performed here |
| Optional `PROPERTY_NAME` in Cells 3/4 and CSV | Proposal only; review and regression evidence required |
| Changes to Cells 2, 5, 6 or 7 for the Metadata pilot | None requested by this register; do not promise full four-table reuse before S2-10 |
| `SOURCE_DESCRIPTION` / `INFORMATION` remapping | Awaiting SME decision; previous assistant suggestion is not approval |
| Catalog table creation in Snowflake | DDL exists; live execution/definition evidence not established here |

### Decision capture

For each answered ID, record the exact decision, approver/role, evidence date, affected field/path, implementation status and validation reference. A reply that clarifies business meaning is not proof that the CSV, registry or database has changed.

| Issue ID | Decision / approver / evidence date | Runtime implementation | PREVIEW | COMMIT / read-back |
| --- | --- | --- | --- | --- |
| S2-01–S2-13 | Pending unless explicitly recorded above as owner clarification | Not implemented by this update | Not performed by this update | Not performed by this update |

### Evidence references

All code statements above refer to the reviewed baseline, not an assumed current Snowflake session.

- [Source review sheet](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/Mapping/SOURCE2_SOURCE_MAPPING.csv); [Topic](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/Mapping/SOURCE2_TOPIC_MAPPING.csv); [Section](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/Mapping/SOURCE2_SECTION_MAPPING.csv); [Sub-Section](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/Mapping/SOURCE2_SUB_SECTION_MAPPING.csv).
- [September 16 transcription checkpoint](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/docs/checkpoints/2026-09-16-source2-tabular-mapping-review.md).
- [Cell 1: configuration](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/01_initialization_and_configuration.py); [Cell 2: inputs](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/02_source_mapping_registry_inputs.py).
- [Cell 3: compiler](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/03_canonical_mapping_contract.py); [Cell 4: transforms, property construction and singleton assignment](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/04_parsing_transform_payload_helpers.py).
- [Cell 5: record-scoped parent resolution](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/05_registry_graph_builder.py); [Cell 6: graph, storage and cross-record guard](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/06_validation_and_guarded_loader.py); [Cell 7: PREVIEW/COMMIT orchestration](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/notebooks/cells/07_mapper_orchestrator.py).
- [Catalog DDL](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/sql/CREATE_CATALOG_TABLES.sql); [September 16 Validation 11 evidence](https://github.com/theenduser009/Oscal-mapping-strategy/blob/64cfe17782500db73f636280540f37b29d5a63e0/docs/checkpoints/2026-09-16-validation-11-component-reconciliation-pass.md). Source 1 PREVIEW evidence does not establish Source 2 execution or full OSCAL conformance.
- Owner clarification: this OSCAL project conversation, 2026-09-17, concerning `SOURCE_DESCRIPTION` and `INFORMATION`; business meaning clarified, final mapping not approved.

This publication changes question documentation only. No mapping CSV, notebook cell, registry SQL, target DDL or Snowflake data is modified by this register update.
