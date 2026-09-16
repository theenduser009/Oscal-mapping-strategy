# Source 2 tabular mapping review - September 16, 2026

## Scope and supersession

Repository: `theenduser009/Oscal-mapping-strategy`.
Branch: `simplify-metadata-boundary`.
Verified base commit: `c738f8872ef9d50cb83c9a29f2ecb5e5c3489c31`.
Base tree: `3b3f3cf0ef2770655b78100f7db7d3a727f905a5`.

The owner rejected the summary-only intake as an inadequate mapping-sheet deliverable and requested row-by-row Archer field, OSCAL model/path, mapping instruction and Notes, with questions rather than assumptions. This release supersedes that intake's presentation and incomplete row inventory. It does not approve mappings or supersede Source 1 runtime decisions or live acceptance evidence.

## Files prepared for this publication

Four CSV sheets are added under Mapping, with 13 consistently named columns. The old intake becomes a small index explaining the evidence and uncertainty, not the mapping data itself.

| File | Data rows | Original worksheet rows | Core text gaps | Git blob |
|---|---:|---|---:|---|
| Mapping/SOURCE2_SOURCE_MAPPING.csv | 56 | 2-57 | 3 | `48ee6ed1250ebdee1e197f0eaec3845d63c29aab` |
| Mapping/SOURCE2_TOPIC_MAPPING.csv | 52 | 2-53 | 24 | `2d7e6f8e2a01537dc22fc219e97a636ca3de882c` |
| Mapping/SOURCE2_SECTION_MAPPING.csv | 62 | 2-63 | 39 | `af6da8befd71d8893ebd07ea8de2d50de8fe77ce` |
| Mapping/SOURCE2_SUB_SECTION_MAPPING.csv | 73 | 2-74 | 54 | `7bf520318175bca3dc88616bf7cc45b1c78212f8` |

Total: 243 photographed row occurrences; 120 have a core transcription gap. Including optional column visibility, 159 have a clarification question. Original worksheet row numbers preserve occurrence identity; repeated field names are not silently deduplicated. Section row 40 is restored after its omission from the old prose inventory.

## Evidence and actual validation

Read the project handoff and coverage supplement, the actual branch head, Mapping directory and existing intake. Visually reviewed the eight Source/Topic screenshots in the uploaded package plus the Section screenshot and two Sub-Section screenshots. No OCR, full original workbook, live RAW records or registry export was used. The screenshot index is in the Mapping index document.

Local CSV parsing checked 13 columns, the four row counts and contiguous original worksheet ranges. Locally computed Git blob hashes match the four create_blob responses above. The Excel companion was created from the same transcription records, with six sheets and formula-driven count summaries; its ZIP integrity passed, key counts were inspected, no formula errors were found in the scan, and a representative mapping range was rendered and visually checked. These are artifact/transcription checks, not mapper tests or live Snowflake validation.

The Excel companion is prepared as a project-chat attachment, not included as a binary file in this GitHub publication. Private screenshots, credentials and source-record payloads are not published.

## Status boundaries

- Transcribed review artifacts: created locally; the Git commit containing this checkpoint records their repository publication.
- Runtime mapping implementation: unchanged. No new executable rows or source routes.
- Preview, Snowflake COMMIT and database readback: not performed or claimed.
- GitHub post-publication readback: must be checked after the branch ref is updated; the attached final project checkpoint records that result. Blob creation alone is not branch publication.
- Source 1 runtime CSV baseline blob: `869cc29a07d9def2bdcf3005026caed1bf1248e2`; it must remain unchanged. The seven notebook cells and all SQL are outside this change.

## Remaining gaps and one next action

The marked source cells are not fully readable. Original path notation and model alternatives are preserved rather than converted to JSON/runtime syntax. Underscore variants, duplicate-looking fields and differing instructions remain unresolved. Blank transformation/datatype cells are not proof that hidden source cells were empty. This is not full original-workbook coverage or OSCAL schema validation.

Ask the owner for the original four-sheet workbook or four CSV exports to resolve the exact clipped field names, paths and Notes. No database access or notebook rerun is needed for this transcription step. Physical source/identity/relationship contracts and Source 2 execution compatibility remain separate later checks; historical Source 1 acceptance does not prove them.
