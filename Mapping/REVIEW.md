# Consolidated mapping review

[Download the Excel review workbook](ARCHER_OSCAL_MAPPING_REVIEW.xlsx?raw=true).

This review draft compiles the eight uploaded mapping documents into one filterable worksheet: **147 listed entries, 146 distinct Archer field names**. It is a transcription review, not a new mapping approval or a replacement notebook input.

The Mappings tab contains the Archer field name, OSCAL model, exact target path, mapping type and Notes, plus a blank Reviewer comments column. Original Excel row numbers are retained where supplied. Source document/line references, component types and compilation notes are included to the right. Source notes retains the shared section wording and review gates.

| Source document | Listed entries |
| --- | ---: |
| [SSP_METADATA](SSP_METADATA.md) | 15 |
| [SSP_SYSTEM_CHARACTERISTICS](SSP_SYSTEM_CHARACTERISTICS.md) | 37 |
| [SSP_CONTROL_IMPLEMENTATION](SSP_CONTROL_IMPLEMENTATION.md) | 42 |
| [SYSTEM_SECURITY_PLAN](SYSTEM_SECURITY_PLAN.md) | 2 |
| [ASSESSMENT_RESULTS](ASSESSMENT_RESULTS.md) | 45 |
| [POAM](POAM.md) | 1 |
| [PROFILE](PROFILE.md) | 2 |
| [SECURITY_ASSESSMENT_PLAN](SECURITY_ASSESSMENT_PLAN.md) | 3 |
| **Total** | **147** |

## Items preserved for verification

- Both occurrences of HELPER_ALLOCATED_CONTROLS remain. No source occurrence was deduplicated.
- The 33 Control Implementation bullet candidates retain blank individual paths, mapping types and Notes because the documents do not supply those values.
- Only 53 entries include original Excel row numbers. The other 94 stay blank.
- The 18 Assessment Results alternative paths remain alternatives; none was silently changed into a property under an observation.
- Party and component paths supplied by section context are marked. The six components retain their System Implementation context.
- CONTROL_SET_VERSION_NUMBER keeps its original Control Implementation label and explicit system-characteristics path.
- Model labels use document/section context when no row-level model label is supplied. Markdown styling was removed without rewriting the wording.

These documents are partial screenshot transcriptions, **not the complete original 608-row workbook**. Existing accepted, blocked and deferred runtime statuses are unchanged. No mapper code, registry or database data was changed for this compilation.

**Next:** verify the workbook and enter corrections in Reviewer comments before using it for code reconciliation. No notebook rerun is requested.

Source snapshot: [the uploaded mapping documents](https://github.com/theenduser009/Oscal-mapping-strategy/tree/8f8d373e2c9de641ddd602852889e19fc8dd6769/Mapping).
