# SSP Security Impact / FIPS 199 mapping — end-to-end guide

Date: September 30, 2026
Repository branch: simplify-metadata-boundary

This guide records the current executable behavior. It supersedes any interpretation of the older screenshot-transcription note that all 13 visible rows are active FIPS-199 objective mappings.

## 1. The 13 visible workbook rows are not all active FIPS objective mappings

The historical System Characteristics mapping section contains 13 rows in this area.

Current executable status:

### Confidentiality candidates
1. RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY
2. CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE
3. CNSS_CONFIDENTIALITY_RATING

Target:
system-security-plan.system-characteristics.security-impact-level.security-objective-confidentiality

### Integrity candidates
4. RECOMMENDED_INTEGRITY_CONTROL_CATEGORY
5. INTEGRITY_CONTROL_CATEGORY_OVERRIDE
6. PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY
7. CNSS_INTEGRITY_RATING

Target:
system-security-plan.system-characteristics.security-impact-level.security-objective-integrity

### Availability candidates
8. AVAILABILITY_CONTROL_CATEGORY_OVERRIDE
9. RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY
10. PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY
11. CNSS_AVAILABILITY_RATING

Target:
system-security-plan.system-characteristics.security-impact-level.security-objective-availability

### The other two rows
12. SECURITY_CATEGORY
    - active, but NOT a security-objective mapping
    - target: system-security-plan.system-characteristics.security-sensitivity-level
    - direct text; no FIPS transform

13. FULL_CONTROL_ASSESSMENT_HELPER
    - EXCLUDED
    - live review showed Yes/No helper values, not a confidentiality impact value
    - no executable OSCAL target is emitted

There is also a separate support guard, RECOMMENDED_SECURITY_CATEGORY, with status BLOCKED_IF_POPULATED. It is not one of the 13 visible historical rows above.

Therefore the current executable FIPS/security-impact candidate count is 11, not 13.

## 2. Correct OSCAL destination

OSCAL security-impact-level contains exactly three required objective members:
- security-objective-confidentiality
- security-objective-integrity
- security-objective-availability

The 11 active Archer candidate fields route into one of those three singleton members.

## 3. Source shape

For the reviewed Archer data, the impact fields are Archer select/value-list fields. CURATED_JSON preserves the select container, for example:

{
  "ValuesListIds": [12345]
}

Matillion does not turn that select ID into the final OSCAL impact label.

## 4. Mapper lookup load

Cell 2 reads:

RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE

using:
- SELECT_VALUE_ID
- SELECT_VALUE_NAME

It builds:

archer_values:
SELECT_VALUE_ID -> SELECT_VALUE_NAME

and a second lookup:

fips_values:
SELECT_VALUE_ID -> lowercase label

but only where SELECT_VALUE_NAME lowercases exactly to:
- low
- moderate
- high

## 5. security-objective transform

Each of the 11 mapping rows uses:

TRANSFORM_ID = security-objective

Cell 4 then:

1. extracts the select ID from the Archer value-list container;
2. looks up the ID;
3. if the resolved label is Low, Moderate, or High, lowercases it;
4. otherwise checks whether the resolved label is one of the explicitly approved legacy labels;
5. if neither rule applies, fails closed.

Standard example:

ValuesListIds = [123]
  -> ARCHER_META_VALUE
  -> SELECT_VALUE_NAME = "Moderate"
  -> security-objective transform
  -> "moderate"

Approved legacy example:

ValuesListIds = [456]
  -> ARCHER_META_VALUE
  -> SELECT_VALUE_NAME = "Legacy LOE C + DFARS"
  -> approved legacy-label check
  -> "Legacy LOE C + DFARS"

No unreviewed label is silently converted.

## 6. Important FIPS-199 distinction

FIPS 199 impact values for an information system are LOW, MODERATE, or HIGH for confidentiality, integrity, and availability.

The current mapper correctly normalizes labels that actually resolve to Low / Moderate / High.

However, the current executable mapping also explicitly permits reviewed Legacy LOE labels and preserves them as strings. There is currently no approved Legacy-LOE-to-FIPS-199 crosswalk in the mapper.

Therefore:
- OSCAL path placement is correct;
- Low/Moderate/High normalization is correct;
- legacy labels are source-preserving, not a FIPS-199 normalization;
- if strict FIPS-199-only output is required, a business-approved legacy crosswalk is still required.

Do not invent that crosswalk.

## 7. Multiple Archer candidates do not use precedence

Several Archer fields target the same singleton OSCAL objective.

The current mapper does not say "override always wins" or "CNSS wins".

For a given source record/objective:
- zero populated candidates -> objective cannot be assembled from that dimension;
- one populated candidate -> its transformed value is used;
- multiple populated candidates with the SAME transformed value -> accepted;
- multiple populated candidates with DIFFERENT transformed values -> mapper raises:
  "Singleton target has conflicting populated mappings"

This is deliberate fail-closed behavior.

The older screenshot-transcription review gate saying "Define precedence when ... values disagree" was not implemented as a precedence hierarchy. The current executable behavior is conflict detection.

## 8. security-impact-level node assembly

The registry defines security-impact-level as an optional object with required members:
- security-objective-confidentiality
- security-objective-integrity
- security-objective-availability

Therefore the node is emitted only when all three required objective members are present after mapping.

## 9. End-to-end validation

Use:
sql/qa/SSP_SECURITY_IMPACT_ALL_FIELDS_END_TO_END.sql

For each populated active candidate it shows:
- source Content ID
- Archer field
- objective
- Archer select ID
- resolved Archer label
- expected mapper output
- actual OSCAL objective value
- number of distinct transformed candidates for that Content ID/objective
- validation status

Expected clean status:
MATCH

If more than one candidate for the same objective resolves differently:
CONFLICTING_SOURCE_CANDIDATES

That condition should be investigated, not silently ranked.
