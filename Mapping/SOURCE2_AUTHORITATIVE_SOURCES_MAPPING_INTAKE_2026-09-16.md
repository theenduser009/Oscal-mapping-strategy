# Source 2 — Authoritative Sources mapping intake

Date: 2026-09-16

Repository branch at intake: `simplify-metadata-boundary`

Purpose: preserve the owner-supplied Source 2 mapping evidence in the same `Mapping/` area as the existing Source 1 mapping material before any runtime implementation.

## Status and guardrails

- This is **review/intake evidence**, not an executable mapping release.
- Do **not** mark these rows `APPROVED` from screenshot evidence alone.
- Do **not** infer clipped OSCAL paths or clipped Notes.
- Do **not** normalize apparent duplicate or misspelled Archer field names until source inspection confirms them.
- The existing executable `Mapping/ARCHER_OSCAL_MAPPINGS.csv` remains unchanged by this intake.
- Source 2 is the top four Authoritative Sources applications shown by the owner; `ARCHER_CONTENT_AUTHORIZATION_PACKAGE` is Source 1 and is not included here.

## Source 2 hierarchy in scope

1. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE`
2. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC`
3. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION`
4. `ARCHER_AUTHORITATIVE_SOURCES_SUB_SECTION`

Working business hierarchy to verify against Archer metadata/source data before implementation:

`Source -> Topic -> Section -> Sub-Section`

This relationship is a review hypothesis from the supplied mapping context, not yet a verified physical RAW-table join contract.

---

## Sheet 1 — Source (`archer_authoritative_sources_to`)

Visible mapping rows: 2-57.

Field inventory, preserving visible worksheet names:

1. `SOURCE_NAME`
2. `SOURCE_VERSION`
3. `SOURCE_DESCRIPTION`
4. `SOURCE_TRACKING_ID`
5. `SOURCE_LINKS`
6. `INFORMATION`
7. `DISCLAIMER`
8. `TOPIC_REFERENCES`
9. `ATTACHMENTS`
10. `CONTROL_STANDARDS`
11. `CONTROL_STANDARDS_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`
12. `CONTROL_STANDARDS__FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`
13. `MASTER_CONTROLS_AUTHORITATIVE_SOURCES`
14. `CONTROL_PROCEDURES`
15. `RELATED_CONTROL_PROCEDURES`
16. `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL`
17. `COMPLIANCE_RATING`
18. `COUNT_OF_CONTROLS`
19. `COUNT_OF_NONCOMPLIANT_CONTROLS`
20. `PCT_OF_NONCOMPLIANT_CONTROLS`
21. `_OF_NONCOMPLIANT_CONTROLS`
22. `RELATED_TO_KEY_CONTROLS`
23. `FINDINGS`
24. `FINDINGS_AUTHORITATIVE_SOURCES`
25. `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT`
26. `DEVIATIONS_AUTHORITATIVE_SOURCES`
27. `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`
28. `SOURCE_TYPE`
29. `CRITICALITY`
30. `SOURCE_CRITICALITY_VALUE`
31. `AUTH_SOURCES_FILTER`
32. `POLICIES_AUTHORITATIVE_SOURCE_REFERENCES`
33. `POLICY_LEVEL_3`
34. `POLICY_LEVEL_3_FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`
35. `POLICY_LEVEL_3__FROM_TOPIC_SECTION_AND_SUBSECTION_LEVELS`
36. `LINKED_TO_POLICY_SOURCE_LEVEL`
37. `NUMBER_OF_POLICIES_SOURCE_LEVEL`
38. `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`
39. `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES`
40. `QUESTION_LIBRARY`
41. `EVIDENCE_REPOSITORY`
42. `EFFECTIVE_DATE`
43. `OFFICIAL_RETIREMENT_DATE`
44. `RTX_RETIREMENT_DATE`
45. `DATE_CREATED`
46. `LAST_UPDATED`
47. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_FIRST_PUBLISHED`
48. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_LAST_UPDATED`
49. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_CONFIRMED_IN_ARCHER`
50. `RECORD_STATUS`
51. `DEFAULT_RECORD_PERMISSIONS`
52. `CONTENT_SOURCE`
53. `INSERT_DATE`
54. `UPDATE_DATE`
55. `CHECKSUM_VALUE`
56. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_CONTENT_ID`

### Clearly visible target examples from the supplied Source sheet

- `SOURCE_NAME` -> Catalog Metadata -> `catalog.metadata.title` -> Direct
- `SOURCE_VERSION` -> Catalog Metadata -> `catalog.metadata.version` -> Direct
- `SOURCE_DESCRIPTION` -> Catalog Metadata -> `catalog.metadata.remarks` -> Direct
- `SOURCE_TRACKING_ID` -> Catalog Metadata -> `catalog.metadata.prop[@name='tracking-id']` -> Transform
- `SOURCE_LINKS` -> Catalog Back Matter -> `catalog.back-matter.resource[@uuid].rlink.href` -> Direct
- `DISCLAIMER` -> Catalog Metadata -> `catalog.metadata.prop[@name='disclaimer']` -> Extension Property
- `TOPIC_REFERENCES` -> Catalog Back Matter -> `catalog.back-matter.resource[@uuid].citation` -> Extension Property
- `ATTACHMENTS` -> Catalog Back Matter -> `catalog.back-matter.resource[@uuid].base64` -> Direct
- `CONTROL_STANDARDS` -> Catalog -> `catalog.group[@id].control[@id]` -> Reference
- `RELATED_CONTROL_PROCEDURES` -> Catalog -> `catalog.control[@id].link[@rel='related']` -> Reference
- `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL` -> Catalog Metadata -> `catalog.metadata.prop[@name='control-count']` -> Extension Property
- `COUNT_OF_NONCOMPLIANT_CONTROLS` -> Assessment Results -> `assessment-results.result.prop[@name='noncompliant-count']` -> Extension Property
- `PCT_OF_NONCOMPLIANT_CONTROLS` -> Assessment Results -> `assessment-results.result.prop[@name='noncompliant-percentage']` -> Extension Property
- `FINDINGS` -> Assessment Results -> `assessment-results.result.finding[@uuid]` -> Reference
- `SOURCE_TYPE` -> Catalog Metadata -> `catalog.metadata.prop[@name='source-type']` -> Extension Property
- `CRITICALITY` -> Catalog Metadata -> `catalog.metadata.prop[@name='criticality']` -> Extension Property
- `SOURCE_CRITICALITY_VALUE` -> Catalog Metadata -> `catalog.metadata.prop[@name='criticality-value']` -> Extension Property
- `AUTH_SOURCES_FILTER` -> Catalog Metadata -> `catalog.metadata.prop[@name='filter-category']` -> Extension Property
- `POLICIES_AUTHORITATIVE_SOURCE_REFERENCES` -> Component Definition -> `component-definition.component.link[@rel='policy']` -> Reference
- `POLICY_LEVEL_3` -> Component Definition -> `component-definition.component.prop[@name='policy-level']` -> Extension Property
- `LINKED_TO_POLICY_SOURCE_LEVEL` -> Component Definition -> `component-definition.component.link[@rel='source-policy']` -> Reference
- `NUMBER_OF_POLICIES_SOURCE_LEVEL` -> Component Definition -> `component-definition.component.prop[@name='policy-count']` -> Extension Property
- `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE` -> Assessment Plan -> `assessment-plan.local-definitions.activity.prop[@name='scope']` -> Extension Property
- `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES` -> Assessment Plan -> `assessment-plan.local-definitions.activity.step` -> Direct
- `QUESTION_LIBRARY` -> Assessment Plan -> `assessment-plan.local-definitions.activity.prop[@name='question-library']` -> Extension Property
- `EVIDENCE_REPOSITORY` -> Assessment Results -> `assessment-results.result.finding.relevant-evidence.link.href` -> Direct
- `EFFECTIVE_DATE` -> Catalog Metadata -> `catalog.metadata.prop[@name='effective-date']` -> Transform
- `OFFICIAL_RETIREMENT_DATE` -> Catalog Metadata -> `catalog.metadata.prop[@name='retirement-date']` -> Transform
- `RTX_RETIREMENT_DATE` -> Catalog Metadata -> `catalog.metadata.prop[@name='rtx-retirement-date']` -> Transform
- `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_CONTENT_ID` -> Catalog Metadata -> `catalog.metadata.prop[@name='archer-content-id']` -> Extension Property

Several longer Source paths are clipped in the owner photographs and remain unresolved here rather than reconstructed.

---

## Sheet 2 — Topic (`source to topic`)

Visible mapping rows: 2-53.

Field inventory:

1. `TOPIC_NAME`
2. `TOPIC_ID`
3. `TOPIC_TRACKING_ID`
4. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC_CONTENT_ID`
5. `DOCUMENT_NUMBER`
6. `SOURCE_NAME_CALC_FIELD`
7. `CONTENT_SOURCE`
8. `TOPIC_DESCRIPTION`
9. `INFORMATION`
10. `CRITICALITY`
11. `TOPIC_CRITICALITY_VALUE`
12. `SOURCE_REFERENCES`
13. `SECTION_REFERENCES`
14. `TOTAL_NUMBER_OF_SECTIONS`
15. `CONTROL_STANDARDS`
16. `CONTROL_STANDARDS_FROM_SECTION_AND_SUBSECTION_LEVELS`
17. `MASTER_CONTROLS_AUTHORITATIVE_SOURCES`
18. `NUMBER_OF_CONTROL_STANDARDS_TOPIC_LEVEL`
19. `CONTROL_PROCEDURES`
20. `RELATED_CONTROL_PROCEDURES`
21. `COMPLIANCE_RATING`
22. `PCT_OF_NONCOMPLIANT_CONTROLS`
23. `COUNT_OF_CONTROLS`
24. `COUNT_OF_NONCOMPLIANT_CONTROLS`
25. `RELATED_TO_KEY_CONTROLS`
26. `FINDINGS`
27. `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT`
28. `DEVIATIONS_AUTHORITATIVE_SOURCES`
29. `DEVIATIONS_TOPICS_LINKED_HELPER`
30. `POLICY_LEVEL_3`
31. `POLICY_LEVEL_3_FROM_SECTION_AND_SUBSECTION_LEVELS`
32. `NUMBER_OF_POLICIES_TOPIC_LEVEL`
33. `LINKED_TO_POLICY_TOPIC_LEVEL`
34. `TOTAL_NUMBER_OF_SECTIONS_LINKED_TO_POLICY`
35. `PERCENT_OF_SECTIONS_LINKED_TO_POLICY`
36. `ENGAGEMENT_SCOPE_IN_CONTROL_TOPIC`
37. `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES`
38. `QUESTION_LIBRARY`
39. `EVIDENCE_REPOSITORY`
40. `ATTACHMENTS`
41. `DEFAULT_RECORD_PERMISSIONS`
42. `TOPIC_DATE_CREATED`
43. `TOPIC_LAST_UPDATED`
44. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC_FIRST_PUBLISHED`
45. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC_LAST_UPDATED`
46. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC_CONFIRMED_IN_ARCHER`
47. `INSERT_DATE`
48. `UPDATE_DATE`
49. `CHECKSUM_VALUE`
50. `_OF_NONCOMPLIANT_CONTROLS`
51. `CONTROL_STANDARDS__FROM_SECTION_AND_SUBSECTION_LEVELS`
52. `POLICY_LEVEL_3__FROM_SECTION_AND_SUBSECTION_LEVELS`

### Clearly visible target examples from the supplied Topic sheet

- `TOPIC_NAME` -> Catalog Group -> `catalog.group[@id].title` -> Direct
- `TOPIC_ID` -> Catalog Group -> `catalog.group.@id` -> Transform
- `TOPIC_TRACKING_ID` -> Catalog Group -> `catalog.group.prop[@name='tracking-id']` -> Extension Property
- `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_TOPIC_CONTENT_ID` -> Catalog Group -> `catalog.group.prop[@name='archer-content-id']` -> Extension Property
- `SOURCE_NAME_CALC_FIELD` -> Catalog Metadata -> `catalog.metadata.title` -> Reference
- `CONTENT_SOURCE` -> Catalog Group -> `catalog.group.prop[@name='content-source']` -> Extension Property
- `TOPIC_DESCRIPTION` -> Catalog Group -> `catalog.group.part[@name='overview'].prose` -> Direct
- `INFORMATION` -> Catalog Group -> `catalog.group.part[@name='information'].prose` -> Direct
- `CRITICALITY` -> Catalog Group -> `catalog.group.prop[@name='criticality']` -> Extension Property
- `TOPIC_CRITICALITY_VALUE` -> Catalog Group -> `catalog.group.prop[@name='criticality-value']` -> Extension Property
- `SOURCE_REFERENCES` -> Catalog Metadata -> `catalog.metadata.title` -> Reference
- `SECTION_REFERENCES` -> Catalog -> `catalog.group.group[@id]` -> Reference
- `TOTAL_NUMBER_OF_SECTIONS` -> Catalog Group -> `catalog.group.prop[@name='section-count']` -> Extension Property
- `CONTROL_STANDARDS` -> Catalog -> `catalog.group.control[@id]` -> Reference
- `MASTER_CONTROLS_AUTHORITATIVE_SOURCES` -> Catalog -> `catalog.group.group.control[@id].link[@rel='related']` -> Reference
- `NUMBER_OF_CONTROL_STANDARDS_TOPIC_LEVEL` -> Catalog Group -> `catalog.group.prop[@name='control-count']` -> Extension Property
- `RELATED_CONTROL_PROCEDURES` -> Catalog -> `catalog.control[@id].link[@rel='related']` -> Reference
- `FINDINGS` -> Assessment Results -> `assessment-results.result.finding[@uuid]` -> Reference
- `POLICY_LEVEL_3` -> Component Definition -> component property named `policy-level` -> Extension Property
- `ENGAGEMENT_SCOPE_IN_CONTROL_TOPIC` -> Assessment Plan -> activity property -> Extension Property
- `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES` -> Assessment Plan -> activity step -> Direct
- `QUESTION_LIBRARY` -> Assessment Plan -> activity property `question-library` -> Extension Property
- `EVIDENCE_REPOSITORY` -> Assessment Results -> finding relevant-evidence link -> Direct
- `ATTACHMENTS` -> Catalog Back Matter -> resource base64 -> Direct

Rows whose exact path text is clipped remain unresolved rather than inferred.

---

## Sheet 3 — Section (`source to section`)

Owner-supplied photograph received 2026-09-16.

Field inventory:

1. `SECTION_NAME`
2. `SECTION_ID`
3. `SECTION_TRACKING_ID`
4. `SECTION_DESCRIPTION`
5. `SECTION_SHORT_DESCRIPTION`
6. `SOURCE_NAME`
7. `TOPIC_NAME`
8. `CONTENT_SOURCE`
9. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_CONTENT_ID`
10. `SUB_SECTION_REFERENCES`
11. `TOPIC_REFERENCES`
12. `TOTAL_NUMBER_OF_SUB_SECTIONS`
13. `SECTION_MAPPING_STATUS`
14. `CONTROL_STANDARDS`
15. `CONTROL_STANDARDS_FROM_SECTION_LEVEL_AND_BELOW`
16. `CONTROL_STANDARDS__FROM_SECTION_LEVEL_AND_BELOW`
17. `MASTER_CONTROLS_AUTHORITATIVE_SOURCES`
18. `CONTROL_PROCEDURES`
19. `RELATED_CONTROL_PROCEDURES`
20. `NUMBER_OF_CONTROL_STANDARDS_SECTION_LEVEL`
21. `COMPLIANCE_RATING`
22. `COUNT_OF_CONTROLS`
23. `COUNT_OF_NONCOMPLIANT_CONTROLS`
24. `PCT_OF_NONCOMPLIANT_CONTROLS`
25. `RELATED_TO_KEY_CONTROLS`
26. `FINDINGS`
27. `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT`
28. `DEVIATIONS_AUTHORITATIVE_SOURCES`
29. `DEVIATIONS_SECTIONS_LINKED_HELPER`
30. `AS_DEVIATION_CREATE_FLAG_CREATE`
31. `AS_DEVIATION_CREATE_FLAG_CREATE`
32. `CREATE_DEVIATION_BINARY_AS`
33. `CRITICALITY`
34. `SECTION_CRITICALITY_VALUE`
35. `SUM_OF_SUB_SECTION_CRITICALITY_VALUE`
36. `INFORMATION`
37. `POLICY_LEVEL_3`
38. `POLICY_LEVEL_3_FROM_SECTION_LEVEL_AND_BELOW`
39. `LINKED_TO_POLICY_SECTION_LEVEL`
40. `NUMBER_OF_POLICIES_SECTION_LEVEL`
41. `TOTAL_NUMBER_OF_SUB_SECTIONS_LINKED_TO_POLICY`
42. `PERCENT_OF_SUB_SECTIONS_LINKED_TO_POLICY`
43. `POLICIES_NEW_AUTH_SOURCE_CALC_CROSSREF_SECTION`
44. `POLICIES_COPY_OF_NEW_AUTH_SOURCE_CALC_CROSSREF_SECTION`
45. `ENGAGEMENT_SCOPE_IN_CONTROL_SECTION`
46. `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES`
47. `QUESTION_LIBRARY`
48. `EVIDENCE_REPOSITORY`
49. `EVIDENCE_REPOSITORY_AUTHORITATIVE_SOURCE_SECTION_INPUT`
50. `EVIDENCE_REPOSITORY_AUTHORITATIVE_SOURCE_SECTION_INPUT`
51. `ATTACHMENTS`
52. `DEFAULT_RECORD_PERMISSIONS`
53. `SECTION_DATE_CREATED`
54. `SECTION_LAST_UPDATED`
55. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_FIRST_PUBLISHED`
56. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_LAST_UPDATED`
57. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SECTION_CONFIRMED_IN_ARCHER`
58. `INSERT_DATE`
59. `UPDATE_DATE`
60. `CHECKSUM_VALUE`
61. `_OF_NONCOMPLIANT_CONTROLS`

Visible Section targets span Catalog Group/Metadata, Catalog controls, Assessment Results findings/properties, Component Definition policy references, Assessment Plan activities, Assessment Results evidence and Catalog Back Matter.

Repeated fields above are intentionally preserved exactly as visible; no deduplication decision has been made.

---

## Sheet 4 — Sub-Section (`source subsection`)

Owner-supplied upper and lower photographs received 2026-09-16.

Field inventory:

1. `SUB_SECTION_NAME`
2. `SUB_SECTION_ID`
3. `SUB_SECTION_TRACKING_ID`
4. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SUB_SECTION_CONTENT_ID`
5. `SECTION_NAME`
6. `SOURCE_NAME`
7. `TOPIC_NAME`
8. `SUB_SECTION_DESCRIPTION`
9. `SUB_SECTION_SHORT_DESCRIPTION`
10. `INFORMATION`
11. `CRITICALITY`
12. `SUBSECTION_CRITICALITY_VALUE`
13. `IMPLEMENTATION_STATEMENT`
14. `ATO_GUIDANCE`
15. `SECTION_REFERENCES`
16. `ALL_RELATED_SUB_SECTION_RECORDS`
17. `ALL_SUB_SECTIONS_CALC`
18. `AUTHORITATIVE_SOURCES_ALL_RELATED_SUB_SECTION_RECORDS`
19. `AUTHORITATIVE_SOURCES_ALL_SUB_SECTIONS`
20. `AUTHORITATIVE_SOURCES_THIS_RECORD`
21. `THIS_RECORD`
22. `RELATED_SUB_SECTION_RECORDS__MANUAL_INPUT`
23. `RELATED_SUB_SECTION_RECORDS__MANUAL_INPUT_RELATED_RECORDS`
24. `SUB_SECTION_MAPPING_STATUS`
25. `CONTROL_STANDARDS`
26. `CONTROL_STANDARDS_ATCS_CONTROLS`
27. `MASTER_CONTROLS_AUTHORITATIVE_SOURCES`
28. `NUMBER_OF_CONTROL_STANDARDS_SUB_SECTION_LEVEL`
29. `CONTROL_PROCEDURES`
30. `RELATED_CONTROL_PROCEDURES`
31. `CONTROL_PROCEDURES_AUTHORITATIVE_SOURCES`
32. `CONTROL_PROCEDURES_SELECTED_AUTHORITATIVE_SOURCE__SUB_SECTION` [name visually clipped; verify original workbook]
33. `DPF_REFERENCE`
34. `COMPLIANCE_RATING`
35. `PCT_OF_NONCOMPLIANT_CONTROLS`
36. `COUNT_OF_CONTROLS`
37. `COUNT_OF_NONCOMPLIANT_CONTROLS`
38. `RELATED_TO_KEY_CONTROLS`
39. `DCMA_SCORE_VALUE`
40. `DCMA_SCORE_COMMENT`
41. `FINDINGS`
42. `CONTROL_TESTING_RESULTS_FAILED_EXTERNAL_CONTROL_REQUIREMENT`
43. `DEVIATIONS_AUTHORITATIVE_SOURCES`
44. `DEVIATIONS_AUTHORITATIVE_SOURCES_LINKED_TO_CONTROL_STANDARDS`
45. `POLICY_LEVEL_3`
46. `NUMBER_OF_POLICIES_SUB_SECTION_LEVEL`
47. `LINKED_TO_POLICY_SUB_SECTION_LEVEL`
48. `POLICIES_NEW_AUTH_SOURCE_CALC_CROSSREF`
49. `ENGAGEMENT_SCOPE_IN_CONTROL_SUB_SECTION`
50. `COMPLIANCE_ENGAGEMENTS_SCOPE_PROCEDURES_FROM_SELECTED_AUTHORITATIVE_SOURCES` [name visually clipped; verify original workbook]
51. `QUESTION_LIBRARY`
52. `EVIDENCE_REPOSITORY`
53. `EVIDENCE_REPOSITORY_NIST_SUB_SECTIONS`
54. `EVIDENCE_REPOSITORY_AUTHORITATIVE_SOURCE_SUBSECTION_INPUT`
55. `EVIDENCE_REPOSITORY_RELATED_AUTHORITATIVE_SOURCES`
56. `EVIDENCE_REPOSITORY_NEW_SUB_SECTION_SELECTOR`
57. `EVIDENCE_REPOSITORY_SELECTED_AUTHORITATIVE_SOURCE__SUB_SECTION` [verify exact underscores]
58. `EVIDENCE_REPOSITORY_RELATED_AUTHORITATIVE_SOURCE_SUB_SECTIONS`
59. `ATTACHMENTS`
60. `CONTENT_SOURCE`
61. `DEFAULT_RECORD_PERMISSIONS`
62. `SUB_SECTION_DATE_CREATED`
63. `SUB_SECTION_LAST_UPDATED`
64. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SUB_SECTION_FIRST_PUBLISHED`
65. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SUB_SECTION_LAST_UPDATED`
66. `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SUB_SECTION_CONFIRMED_IN_ARCHER`
67. `INSERT_DATE`
68. `UPDATE_DATE`
69. `CHECKSUM_VALUE`
70. `_OF_NONCOMPLIANT_CONTROLS`
71. `EVIDENCE_REPOSITORY_AUTHORITATIVE_SOURCE__SUBSECTION_INPUT`
72. `EVIDENCE_REPOSITORY_RELATED_AUTHORITATIVE_SOURCE__SUB_SECTION` [name visually clipped; verify exact text]
73. `EVIDENCE_REPOSITORY_SELECTED_AUTHORITATIVE_SOURCE__SUB_SECTION` [name visually clipped; verify exact text]

Visible Sub-Section targets span Catalog Group, SSP Control Implementation, Catalog controls, Component Definition control implementation/policy links, Assessment Results findings/evidence, Assessment Plan activities, Catalog Back Matter, Catalog Metadata and system metadata.

---

## Evidence completeness / unresolved items before executable integration

The following are intentionally **not** inferred in this intake:

1. Exact Source 2 RAW table names for all four applications.
2. Exact record identity column and `CURATED_JSON` contract for each table.
3. Canonical physical parent references for Topic -> Source, Section -> Topic, Sub-Section -> Section.
4. Whether every child has exactly one canonical parent.
5. Exact clipped OSCAL paths and Notes.
6. Which duplicate-looking field names are real separate Archer fields versus workbook duplicates.
7. Which system/calculated/helper fields should be excluded from OSCAL execution.
8. Registry hierarchy/identity rows needed for Source 2.
9. Whether the existing same-record graph parent resolution is sufficient for cross-table Source 2 ownership without one reusable generic extension.

## Next implementation checkpoint

Before editing `ARCHER_OSCAL_MAPPINGS.csv` or the seven-cell runtime for Source 2, perform a read-only source-contract review using one connected chain:

`Source record -> Topic record -> Section record -> Sub-Section record`

Capture the actual table names, record IDs, `CURATED_JSON` payloads, and the exact parent-reference fields. Then reconcile every row in this intake against the full mapping text and decide executable/deferred/excluded status without guessing.
