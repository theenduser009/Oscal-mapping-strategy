# Assessment Results — score mapping

Active source: Source One, Archer Authorization Package `CURATED_JSON`.
SSP is parked and preserved. All seventeen selected observation-score mappings
are now live accepted, including the thirteen-field extension. The [September 11
run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/05fdb9e25bd7e28661f6fbd2d868d360c8d9e0bd/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-11) passed with no writes.
That accepted release needs no repeat run. The owner has now approved the next
seventeen alternative-path rows. Their implementation is **pending live
acceptance**, with 34 cumulative selected fields and 11 other row occurrences
not enabled. This is not full-model completeness or schema validity.

## Current direction — workflow fields and duplicate score deferred

On September 11, the owner confirmed **skip the seven workflow audit fields for
now**, then also directed us to **defer both Average Security Compliance Score
row occurrences** because their duplicate-field meaning is unresolved.
Neither duplicate is counted as complete. These workflow fields target
`assessment-results.results[].props[]`; they are deferred, not implemented or
complete. This is separate from the two parked value-conversion blockers,
`RISK_ACCEPTANCE_RBDS` and `RISK_ASSESSMENT_REPORT`.

| Remaining Archer field | Row occurrences | Exact Excel target | Current issue |
| --- | ---: | --- | --- |
| `AVG_SECURITY_COMPLIANCE_SCORE` | 2 | `assessment-results.results[].observations[]` | **Deferred by owner, 2026-09-11.** Duplicate meaning unresolved. Both original rows are preserved; no rename, deduplication or output is inferred. Reopen only after source-field identity is clarified. |
| `TOTAL_PACKAGE_INHERENT_RISK` | 1 | `assessment-results.results[].observations[]` | CSV says observation; earlier owner Notes evidence differs. Confirm the governing original row before selecting its contract. |
| `FINDINGS` | 1 | `assessment-results.results[].findings[]` | Notes require linking finding UUIDs; referenced finding identity/source and parent association are not established. |

**No action or notebook run is requested for the deferred score.**
The two remaining non-deferred rows are Total Package Inherent Risk and Findings,
with the unresolved contracts shown above. No code is changed by this status update.

Inventory is **45 row occurrences = 17 accepted + 15 implemented candidate-only
+ 2 parked after rejection + 7 workflow rows deferred + 2 duplicate score rows deferred
+ 2 remaining rows under review**.
Deferred rows remain in the inventory and are not completed mappings.

The [two-field diagnostic](https://github.com/theenduser009/Oscal-mapping-strategy/blob/ac3e8b348eabc708960ccdd51f00e3a0383613dc/docs/ssp_mapping_progress_checkpoint.md#assessment-results-rejected-value-shape-diagnostic--2026-09-11)
is complete and matched the blocked run: 2,813 records, zero parse failures,
1 reference-shaped rejection and 99 multi-number-array rejections, zero writes.
The field meanings and output rules remain parked. No rerun is requested.
The blocked 34-field batch is not accepted. SSP, mapper code, registry and the
original CSV remain unchanged.

## Four groups in the posted CSV

Source: [transcribed mapping rows](transcribed_mapping_rows.csv), added on
2026-09-10. This is a 51-record transcription, not the complete original workbook.
Of those records, 45 target Assessment Results and represent 44 distinct Archer
field names. The difference is a duplicated `AVG_SECURITY_COMPLIANCE_SCORE` row.
Counts include that duplicate and do not count multiline Notes as rows.

| Group | Literal target in CSV | Type | Row occurrences | Next work |
| --- | --- | --- | ---: | --- |
| Observation scores | `assessment-results.results[].observations[]` | Extension Property | 20 | 17 fields live accepted; seven have source gaps. Three occurrences / two distinct fields remain excluded for duplicate/Notes questions. |
| Observation or property | `assessment-results.results[].observations[] or props[]` | Extension Property | 17 | Owner approved observation items with inline named properties on September 11. All 17 implemented; pending live. Original alternative path/Notes preserved and checked exactly. |
| Workflow audit properties | `assessment-results.results[].props[]` | Extension Property | 7 | Deferred by owner on September 11. Do not implement or request a run now. Model label is `Extension Properties`, but the path targets Assessment Results. |
| Finding references | `assessment-results.results[].findings[]` | Reference | 1 | Establish reference shape, finding identity and result-parent association. Keep separate from scores. |

Group by **exact target, mapping type, target member and Notes/transformation**.
Grouping shares code; it does not combine field values into one score, merge
distinct observations, or discard source/parent identity. Different Notes remain
separate contracts even when paths match.

## First batch — live accepted

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

The [original four-field run](https://github.com/theenduser009/Oscal-mapping-strategy/blob/683b0de290334cdc82675cda302f4244b10c9e0e/docs/ssp_mapping_progress_checkpoint.md#assessment-results-mapped-scope-checkpoint--2026-09-10)
records 2,813 emitted observations for **each** of these four fields, zero missing
or invalid values, 16,878 nodes, 14,065 edges and 2,813 partial documents. Mapping
and registry errors, duplicate keys and dangling edges are all zero. No database
writes occurred. This establishes live acceptance for those four fields, not
full-model completeness or independent source-to-payload equality for every value.

<a id="expanded-batch--thirteen-additional-fields-pending-live"></a>

## Expanded batch — thirteen additional fields, live accepted

The owner requested continuing the matching score group. All fields below use
the same exact Excel path `assessment-results.results[].observations[]`,
`Extension Property` type, and Notes `Archer-specific risk scoring - map as observation`.
Each source scalar becomes the value of one named property inside its own
observation. These are source-provided scores and grades: **do not calculate new
averages, totals or grade bands from their names**.

| Additional Archer field | Property name inside its observation |
| --- | --- |
| `STANDARD_OPERATING_ENVIRONMENT_SCORE` | `standard-operating-environment-score` |
| `COMPUTER_PASSWORD_AGE_SCORE` | `computer-password-age-score` |
| `VULNERABILITY_REPORTING_SCORE` | `vulnerability-reporting-score` |
| `SECURITY_COMPLIANCE_REPORTING_SCORE` | `security-compliance-reporting-score` |
| `TOTAL_AUTHORIZATION_PACKAGE_RISK_SCORE` | `total-authorization-package-risk-score` |
| `AVG_AUTHORIZATION_PACKAGE_RISK_SCORE` | `avg-authorization-package-risk-score` |
| `RISK_SCORE_GRADE` | `risk-score-grade` |
| `AVG_VULNERABILITY_SCORE` | `avg-vulnerability-score` |
| `AVG_PATCH_SCORE` | `avg-patch-score` |
| `AVG_ANTIVIRUS_SCORE` | `avg-antivirus-score` |
| `AVG_STANDARD_OPERATING_ENVIRONMENT_SCORE` | `avg-standard-operating-environment-score` |
| `AVG_COMPUTER_PASSWORD_AGE_SCORE` | `avg-computer-password-age-score` |
| `AVG_VULNERABILITY_REPORTING_SCORE` | `avg-vulnerability-reporting-score` |

The original four remain selected and their payload/identity rules are unchanged.
`AVG_SECURITY_COMPLIANCE_SCORE` remains excluded because it appears twice in the
transcription. `TOTAL_PACKAGE_INHERENT_RISK` remains excluded because the earlier
owner-provided Notes differ from the CSV. Neither uncertainty blocks these
thirteen matching fields. Findings, result-level workflow properties and the
literal `observations[] or props[]` group remain outside this release.

Against the posted 45-row inventory: **17 live accepted + 28 not enabled = 45**.
The expanded report confirms 2,813 source records, 46,960 emitted observations,
52,586 nodes, 49,773 edges and 2,813 partial documents. Contract errors, duplicate
keys, dangling edges, invalid source records and invalid field values are zero.
All seventeen fields have populated evidence; no database writes occurred.

Ten fields cover all records. Seven have missing source values: risk grade 267,
average vulnerability 13, average patch 1, average antivirus 13, average operating
environment 541, average password age 13 and average vulnerability reporting 13.
These are field-specific counts, not distinct missing-record totals. Missing
values were omitted. Their upstream cause has not been established.
See the [exact per-field register](MAPPING_PROGRESS.md#assessment-results-field-register).

## Approved alternative-path batch — seventeen more fields, pending live

On September 11 the owner approved using the accepted pattern for the seventeen
rows whose original Excel path is
`assessment-results.results[].observations[] or props[]` and Notes are
`Archer-specific risk scoring - map as observation or property`.

The explicit decision is **one observation per source field, containing one
named inline property**. The emitted node path is
`assessment-results.results[].observations[]`; the value lives in that item's
`props[]`. The CSV is not rewritten. The mapper checks each field's original
path and Notes against its own approved group, so the choice is not generalized
to other rows or to the result-level workflow-property group.

| Newly selected Archer field | Property name inside its observation |
| --- | --- |
| `RISK_ACCEPTANCE_RBDS` | `risk-acceptance-rbds` |
| `TOTAL_PACKAGE_RESIDUAL_RISK` | `total-package-residual-risk` |
| `ADJUSTED_TOTAL_RISK_SCORE` | `adjusted-total-risk-score` |
| `ADJUSTED_AVERAGE_RISK_SCORE` | `adjusted-average-risk-score` |
| `CURRENT_HIGHEST_DEVICE_RISK_SCORE` | `current-highest-device-risk-score` |
| `CURRENT_AVERAGE_DEVICE_RISK_SCORE` | `current-average-device-risk-score` |
| `CURRENT_CONTROL_RISK_SCORE` | `current-control-risk-score` |
| `PCT_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | `pct-current-highest-device-risk-threshold` |
| `PCT_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | `pct-current-average-device-risk-threshold` |
| `BASELINE_HIGHEST_DEVICE_RISK_SCORE` | `baseline-highest-device-risk-score` |
| `BASELINE_AVERAGE_DEVICE_RISK_SCORE` | `baseline-average-device-risk-score` |
| `BASELINE_CONTROL_RISK_SCORE` | `baseline-control-risk-score` |
| `RISK_ASSESSMENT` | `risk-assessment` |
| `_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | `current-average-device-risk-threshold` |
| `_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | `current-highest-device-risk-threshold` |
| `INITIAL_RISK_ASSESSMENT` | `initial-risk-assessment` |
| `RISK_ASSESSMENT_REPORT` | `risk-assessment-report` |

All seventeen reuse the existing source-scalar conversion. No scores, thresholds,
percentages, averages, risk bands, assessment objects or finding references are
calculated or inferred from field names. Leading underscores remain part of the
source lookup and observation identity; only the displayed property name follows
the existing lowercase/hyphen convention. Zero is retained and decimal precision
is preserved. Missing/null/empty values are omitted and counted; populated
object, attachment/reference or multi-value shapes that do not resolve through
the already-supported select wrapper block publication and are reported in
aggregate. The blocked run establishes per-field candidate coverage; the completed
shape diagnostic above explains the two rejected shapes, which are now parked.

**Registry:** the same root, results and observations rows are checked. Properties
remain inline, so this batch adds no graph path and requires no registry insert.
It changes neither the accepted registry identity rules nor any database data.

The existing seventeen mappings keep their payloads, UUIDs and node/edge keys.
Current inventory: **45 rows = 17 live accepted + 17 implemented/pending live
+ 11 not enabled**. The eleven are three observation-only occurrences with
duplicate/Notes questions, seven conditional workflow fields and one finding
reference. The inherent-risk Notes conflict remains unresolved.

### Run the expanded AR cell once

**This run was completed and blocked. The instructions below are retained as
release history, not a request to repeat it.** The shape diagnostic is also complete.
Current direction is the remaining-eleven review described at the top of this page.

1. Refresh [Assessment Results mapping cell](../notebooks/assessment_results/01_map_observation_scores.py).
2. Replace the entire separate AR cell and run it once in the active notebook
   session with `EXECUTE_WRITES = False`.
3. Do not replace SSP cells, change CONFIG's model, rerun Cell 7, run the grouping
   report, or run registry setup. If the session expired, first run the unchanged
   Cells 1, 2 and 4 to initialize inputs and shared helpers, then this AR cell.
4. Post only the printed `AR_SCORE_RUN_REPORT`. Check release
   `ar-observation-scores-v3-34-fields`, 34 selected fields and, for the same
   45 mapping rows, 11 other rows not processed. New field coverage is unknown
   at release time; the posted blocked report now records candidate per-field
   counts in the progress register. A blocked result is not a successful partial run.

The report keeps the two input mapping groups visible and names the common
inline-property representation. No additional validation cell is required.

### Prior seventeen-field run instructions — historical reference only

**The following instructions describe the already accepted v2 run.** They are
retained as history, not today's run request. Use the expanded v3 instructions above.

Refresh [Assessment Results score mapper](../notebooks/assessment_results/01_map_observation_scores.py),
copy the complete file, and **replace the separate AR cell you just ran**. Run
that cell once in the existing notebook session. This is the actual mapper,
not the grouping report or SSP assembler. It needs
the inputs from Cell 2 and helpers from Cell 4; keep `EXECUTE_WRITES = False`.
**Do not replace SSP Cells 4 or 5, change the model in CONFIG, or rerun Cell 7.**
If the session closed, initialize the unchanged Cells 1, 2 and 4, then run this
AR cell. Cell 4 only defines helpers, so Cell 3 is not required for this batch.

Post only `AR_SCORE_RUN_REPORT`, which is printed automatically. Do not post
source payloads or the document objects. A successful result says
`MAPPED_SCOPE_BUILT` and reports per-field emitted/missing counts and key checks.
Confirm `MAPPING_RELEASE` is `ar-observation-scores-v2-17-fields` and the
report lists 17 selected fields. With the same 45 mapping rows, 28 other rows
should be reported as not processed; changed inputs may have different totals.
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
  property representation first applied to the matching observation-only scores.
  September 11 approval extends it to the seventeen specifically listed alternative
  rows, not arbitrary alternatives or workflow/finding groups.
- The owner verbally confirmed “Archer specific risk scoring, map as observation
  or property” for Excel rows 74, 75, 98, 99, 134, 135, 136, 141, 143, 156, 157,
  158, 460, 571, 573, 599 and 604. Row 460 is `RISK_ASSESSMENT`. That wording
  did not itself resolve the alternative destination. The later September 11
  approval above resolves the seventeen listed alternative-path rows. The CSV puts
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

The v2 release passed 236 local tests before its separately posted live acceptance.
The current v3 release passes **242 local tests**, including 30 focused AR tests.
A check using the unchanged posted CSV and synthetic source values confirms
34 selected fields, 11 excluded rows and zero duplicate/dangling keys.
Local verification covers both exact input contracts,
all accepted seventeen identities/payloads, parent-child integrity, source value
boundaries and eleven exclusions. Local checks do not establish live acceptance
of the seventeen additions. SSP cells, registry, DIM and FACT remain unchanged. Track decisions in
[Mapping Progress](MAPPING_PROGRESS.md#modelpath-status-and-clarification-queue).
