# Source 2 mapping sheets

Updated: September 16, 2026. Branch: `simplify-metadata-boundary`.

**The mapping data is now in the four CSV sheets below, not in prose inventories.** This replaces the summary-only intake at commit `c738f8872ef9d50cb83c9a29f2ecb5e5c3489c31`. That earlier version remains in Git history. This update is a screenshot transcription review, not a runtime mapping release.

## Open a mapping sheet

| Mapping sheet | Archer entity name supplied by the owner | Photographed worksheet rows | Mapping rows | Rows needing core text clarification |
|---|---|---:|---:|---:|
| [Source](SOURCE2_SOURCE_MAPPING.csv) | `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE` | 2-57 | 56 | 3 |
| [Topic](SOURCE2_TOPIC_MAPPING.csv) | `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC` | 2-53 | 52 | 24 |
| [Section](SOURCE2_SECTION_MAPPING.csv) | `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION` | 2-63 | 62 | 39 |
| [Sub-Section](SOURCE2_SUB_SECTION_MAPPING.csv) | `ARCHER_AUTHORITATIVE_SOURCES_SUB_SECTION` | 2-74 | 73 | 54 |
| **Total** | | | **243** | **120** |

These are photographed row occurrences, not unique fields, approved mappings or proof of complete original-workbook coverage. Archer entity names above are the owner's supplied names, not verified physical Snowflake RAW bindings. Authorization Package is Source 1 and is not included in these sheets.

## What each row contains

Each CSV has the same columns: **Worksheet row, Archer field name, OSCAL model, OSCAL element path, Mapping type, Original Notes, Cardinality, Archer data type, Transcription status, Clarification needed, Evidence, Transformation logic, OSCAL data type**.

Original Notes are separate from reviewer questions. Mapping type retains the source's Direct / Transform / Extension Property / Reference / System Metadata wording. The original path syntax is retained, including singular elements, `[@id]`, `[@name=...]`, `ssp`, composite paths and alternatives. These expressions have not been converted into approved runtime paths or checked for schema conformance in this transcription step.

## Reading the uncertainty markers

- `[CLIPPED]` is an editorial marker: the remaining source cell text was cut off or unreadable. It is not part of an Archer field name or OSCAL path. Do not use marked cells as runtime inputs.
- `[NOT VISIBLE]` identifies a column or value not shown in the supplied view.
- `NEEDS SOURCE TEXT` means at least one core field-name/model/path/type/Notes cell is clipped or uncertain, including flagged underscore counts.
- `CORE TEXT CAPTURED` means those core cells were readable in the supplied views. It is not a mapping approval, a full-row completeness claim, or a schema-validation result. Cardinality or optional datatype details may still have a question.
- Blank Transformation logic / OSCAL data type cells are not invented values. No populated entries in those columns could be transcribed from the supplied views; unseen cells have not been verified as empty.

There are 159 rows with a clarification question when optional cardinality/data-type visibility is included. The 120 count above is the subset with a core transcription gap. Review questions identify exact original worksheet rows; no missing tails are completed from similar rows on another sheet.

## Preserved row-level distinctions

Section worksheet row 40 (`POLICY_LEVEL_3__FROM_SECTION_LEVEL_AND_BELOW`) was omitted from the earlier prose inventory and is now present. Duplicate-looking fields remain separate rows. Uncertain underscore positions/counts are explicitly flagged. Source `CONTROL_PROCEDURES` retains both visible target alternatives. Topic row 32's Reference instruction and row 53's Extension Property instruction remain different as supplied; no reconciliation has been inferred.

## Private evidence index

The original screenshots remain private in the OSCAL project, not in this public repository.

| Evidence code | Owner-supplied image filename | Scope |
|---|---|---|
| S01 | `image-1789591839609.jpg` | Source upper fields |
| S02 | `image-1789591873886.jpg` | Source upper paths and Notes |
| S03 | `image-1789591900226.jpg` | Source lower fields |
| S04 | `image-1789591931405.jpg` | Source lower paths and Notes |
| T01 | `image-1789592013407.jpg` | Topic upper |
| T02 | `image-1789592086864.jpg` | Topic lower |
| T03 | `image-1789592147143.jpg` | Topic upper complementary view |
| T04 | `image-1789592159456.jpg` | Topic lower complementary view |
| SEC01 | `image-1789596556306.jpg` | Section |
| SUB01 | `image-1789596613636.jpg` | Sub-Section upper |
| SUB02 | `image-1789596630959.jpg` | Sub-Section lower |

Original worksheet labels: `archer_authoritative_sources_to`, `source to topic`, `source to section`, and `source subsection`.

## Workbook and next clarification

A formatted Excel companion, `ARCHER_OSCAL_SOURCE2_MAPPING_REVIEW_2026-09-16.xlsx`, was prepared for attachment in the OSCAL project chat. It contains Read Me, Source, Topic, Section, Sub-Section and Clarifications sheets, with filters, wrapped text, highlighted uncertainty and blank reviewer-response cells. The native workbook is attached in the project chat; this GitHub release publishes the four CSVs.

**Requested from the owner:** the original Excel workbook containing these four worksheets, or CSV exports of the four sheets, to recover the exact clipped field names, paths and Notes. No Snowflake run is needed to finish the mapping-sheet transcription.

`ARCHER_OSCAL_MAPPINGS.csv`, the seven notebook cells, registry setup and target DDL are unchanged. No Source 2 row has been marked APPROVED or enabled. Physical source contracts, relationships and runtime compatibility remain separate implementation checks after the mapping text is confirmed.

See the [dated publication checkpoint](../docs/checkpoints/2026-09-16-source2-tabular-mapping-review.md).
