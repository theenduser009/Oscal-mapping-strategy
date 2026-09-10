# Assessment Results — grouped mapping work

Active source: Source One, Archer Authorization Package `CURATED_JSON`.
SSP is parked and preserved. These are implementation batches, not completed
Assessment Results mappings.

## Four groups in the posted CSV

Source: [transcribed mapping rows](transcribed_mapping_rows.csv), added on
2026-09-10. This is a 51-record transcription, not the complete original workbook.
Of those records, 45 target Assessment Results and represent 44 distinct Archer
field names. The difference is a duplicated `AVG_SECURITY_COMPLIANCE_SCORE` row.
Counts include that duplicate and do not count multiline Notes as rows.

| Group | Literal target in CSV | Type | Row occurrences | Next work |
| --- | --- | --- | ---: | --- |
| Observation scores | `assessment-results.results[].observations[]` | Extension Property | 20 | Define the observation payload carrying each source score, then reuse the handler. 19 distinct fields; duplicate requires reconciliation. |
| Observation or property | `assessment-results.results[].observations[] or props[]` | Extension Property | 17 | Select one exact destination and value representation. The literal `or` is an alternative, not a nested property path. |
| Workflow audit properties | `assessment-results.results[].props[]` | Extension Property | 7 | Notes make inclusion conditional on audit-trail need. Confirm inclusion and property name/value rules. Model label is `Extension Properties`, but the path targets Assessment Results. |
| Finding references | `assessment-results.results[].findings[]` | Reference | 1 | Establish reference shape, finding identity and result-parent association. Keep separate from scores. |

Group by **exact target, mapping type, target member and Notes/transformation**.
Grouping shares code; it does not combine field values into one score, merge
distinct observations, or discard source/parent identity. Different Notes remain
separate contracts even when paths match.

## First batch and remaining decision

Start with `VULNERABILITY_SCORE`, `ANTIVIRUS_SCORE`, `PATCH_SCORE`, and
`SECURITY_COMPLIANCE_SCORE`. The CSV Notes say to map these as observations.
The target stops at the observation collection; it does not specify which payload
member holds the score.

**Proposed, not approved:** one observation per source field within each result,
carrying the original score as a named property. Confirm this representation
before adding a nested property path or selecting property names, namespace and
conversion rules. No score recalculation is proposed.

## Evidence to preserve

- This CSV supersedes the earlier summary that placed all scores directly at
  `assessment-results.results[].observations[].props[]`. No AR emission code was
  released under that interpretation.
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

Nine focused local grouping tests passed. No production mapper cell, accepted
SSP graph, registry, DIM or FACT was changed. Live Assessment Results execution
remains unverified. Track decisions in [Mapping Progress](MAPPING_PROGRESS.md#modelpath-status-and-clarification-queue).
