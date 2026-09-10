# Assessment Results — grouped mapping work

Active source: Source One, Archer Authorization Package `CURATED_JSON`.
SSP is parked and preserved. The first four observation-score mappings are now
implemented in a separate read-only cell; live Snowflake acceptance is pending.
The remaining grouped rows are not implemented by this release.

## Four groups in the posted CSV

Source: [transcribed mapping rows](transcribed_mapping_rows.csv), added on
2026-09-10. This is a 51-record transcription, not the complete original workbook.
Of those records, 45 target Assessment Results and represent 44 distinct Archer
field names. The difference is a duplicated `AVG_SECURITY_COMPLIANCE_SCORE` row.
Counts include that duplicate and do not count multiline Notes as rows.

| Group | Literal target in CSV | Type | Row occurrences | Next work |
| --- | --- | --- | ---: | --- |
| Observation scores | `assessment-results.results[].observations[]` | Extension Property | 20 | First four fields implemented; live run pending. Remaining rows are not enabled. 19 distinct fields; duplicate requires reconciliation. |
| Observation or property | `assessment-results.results[].observations[] or props[]` | Extension Property | 17 | Select one exact destination and value representation. The literal `or` is an alternative, not a nested property path. |
| Workflow audit properties | `assessment-results.results[].props[]` | Extension Property | 7 | Notes make inclusion conditional on audit-trail need. Confirm inclusion and property name/value rules. Model label is `Extension Properties`, but the path targets Assessment Results. |
| Finding references | `assessment-results.results[].findings[]` | Reference | 1 | Establish reference shape, finding identity and result-parent association. Keep separate from scores. |

Group by **exact target, mapping type, target member and Notes/transformation**.
Grouping shares code; it does not combine field values into one score, merge
distinct observations, or discard source/parent identity. Different Notes remain
separate contracts even when paths match.

## First batch — implemented; live run pending

Start with `VULNERABILITY_SCORE`, `ANTIVIRUS_SCORE`, `PATCH_SCORE`, and
`SECURITY_COMPLIANCE_SCORE`. The CSV Notes say to map these as observations.
The target stops at the observation collection. The owner subsequently approved
one observation per field, with its score in a named property inside the collection
item. Properties are inline in the observation payload, not extra graph nodes.

| Archer field | Property name inside its observation |
| --- | --- |
| `VULNERABILITY_SCORE` | `vulnerability-score` |
| `ANTIVIRUS_SCORE` | `antivirus-score` |
| `PATCH_SCORE` | `patch-score` |
| `SECURITY_COMPLIANCE_SCORE` | `security-compliance-score` |

Names reuse the mapper's existing lowercase/hyphen convention. No namespace,
score formula, assessment method, timestamp or finding is invented. Numeric
scores bypass the Archer select-ID fallback; explicit select-ID containers use
the existing governed lookup. One resolved scalar becomes property text using
the existing value convention. Zero is retained, decimal precision is preserved,
null/empty values are omitted and counted, and invalid/multi-value inputs block
the batch without publishing partial outputs.

The cell creates one root and result per source record and one observation per
populated selected field. Result identity is the source record; observation
identity is the source field within that record. Keys/UUIDs reuse the shared
identity functions; every containment edge references its actual parent.
The current registry must confirm these three existing paths and their rules.
The cell neither inserts registry rows nor uses the SSP DIM/FACT loader.

### Run one mapping cell

Copy [Assessment Results score mapper](../notebooks/assessment_results/01_map_observation_scores.py)
into one new Python cell and run it in the existing notebook session. It needs
the inputs from Cell 2 and helpers from Cell 4; keep `EXECUTE_WRITES = False`.
**Do not replace SSP Cells 4 or 5, change the model in CONFIG, or rerun Cell 7.**
If the session closed, initialize the unchanged Cells 1, 2 and 4, then run this
new cell. Cell 4 only defines helpers, so Cell 3 is not required for this batch.

Post only `AR_SCORE_RUN_REPORT`, which is printed automatically. Do not post
source payloads or the document objects. A successful result says
`MAPPED_SCOPE_BUILT` and reports per-field emitted/missing counts and key checks.
`BLOCKED` means inspect the listed contract errors or invalid counts; no batch
outputs are released. Missing source values do not count as exercised mappings.

Actual in-memory outputs are `AR_SCORE_NODES`, `AR_SCORE_EDGES` and
`AR_SCORE_DOCUMENTS`. These are separate from accepted SSP outputs; they are not
persisted Snowflake tables. This is the mapped score subset, not a complete or
schema-validated Assessment Results document. No further grouping cell is needed
before running this mapping cell.

## Evidence to preserve

- This CSV supersedes the earlier summary that placed all scores directly at
  `assessment-results.results[].observations[].props[]`. No AR emission code was
  released under that interpretation. The later owner-approved inline score
  property representation above applies only to the first four fields.
- The owner verbally confirmed “Archer specific risk scoring, map as observation
  or property” for Excel rows 74, 75, 98, 99, 134, 135, 136, 141, 143, 156, 157,
  158, 460, 571, 573, 599 and 604. Row 460 is `RISK_ASSESSMENT`. That wording
  does not resolve the alternative destination. The CSV puts
  `TOTAL_PACKAGE_INHERENT_RISK` in the observation-only group, unlike the earlier
  row-74 Notes discussion; reconcile against the original loaded artifact.
- Keep both `AVG_SECURITY_COMPLIANCE_SCORE` occurrences visible until the
  original sheet establishes whether one is a different field. Preserve the
  leading underscores in the two transcribed current-risk-threshold fields.
- Blank `NULL%` cells do not establish zero nulls or live source coverage.

## Bounded read when loaded-artifact or registry evidence is needed

**No notebook run is needed just to obtain these four groups.** They are already
grouped from the posted CSV.

[Optional combined mapping/registry read](../notebooks/validation/READ_ONCE_assessment_results_mapping_groups.py)
reconciles the actual artifact already loaded by Cell 2 with the current
nine-column registry in one pass. It prints only mapping/registry metadata.
Ambiguous paths and duplicate occurrences remain visible. Syntactic validity
does not establish registry, identity, semantics or handler readiness.

If that evidence is requested, copy the whole file into one new Python cell in
the session where Cell 2 ran. Run only that cell. Do not change `OSCAL_MODEL`,
rerun Cell 7, or enable writes. If the session expired, run unchanged Cells 1 and
2 first; mapper Cells 3–7 and registry setup are not required.

The historical registry has result and observation identity conventions, but
does not prove the current nested-property contract. Registry writes require a
separately approved setup after the schema and collection rules are known.

Nine focused local grouping tests passed before this implementation release.
The separate score mapper passes 20 focused payload/identity tests; the full
repository suite passes 232 local tests. These are not live Snowflake results. The
accepted SSP cells, registry, DIM and FACT remain unchanged. Live Assessment
Results execution is unverified until its report is posted. Track decisions in
[Mapping Progress](MAPPING_PROGRESS.md#modelpath-status-and-clarification-queue).
