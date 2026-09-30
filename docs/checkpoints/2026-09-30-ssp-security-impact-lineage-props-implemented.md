# SSP security-impact lineage props implemented

Date: September 30, 2026
Branch: simplify-metadata-boundary
Status: IMPLEMENTED IN REPOSITORY; NOT YET OWNER-RUN IN SNOWFLAKE.

## Decision

Use OSCAL props for portable source-field lineage for the current SSP
security-impact mappings.

Native security-impact values remain in:
- security-objective-confidentiality
- security-objective-integrity
- security-objective-availability

Lineage is emitted separately under:
system-security-plan.system-characteristics.props[]

## Implemented generic capability

Cell 3 now supports:
- TRANSFORM_ID = source-field-name
- PROPERTY_NAME
- PROPERTY_NS
- PROPERTY_CLASS
- PROPERTY_GROUP

PROPERTY_NS must be an absolute URI.

Cell 4 now emits optional OSCAL Property members:
- ns
- class
- group

The source-field-name transform emits the exact SOURCE_FIELD_NAME only when
that source field is populated.

## Current security-impact lineage shape

For example:

{
  "name": "source-field",
  "ns": "urn:company:oscal:lineage:v1",
  "class": "security-objective-integrity",
  "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
}

The anonymized namespace is explicit mapping metadata and can later be replaced
with an organization-approved absolute URI.

## Scope

11 active security-impact source candidates now have lineage-property rows:
- 3 confidentiality candidates
- 4 integrity candidates
- 4 availability candidates

SECURITY_CATEGORY is not part of this lineage set because it maps to
security-sensitivity-level rather than a security-impact objective.
FULL_CONTROL_ASSESSMENT_HELPER remains excluded.

## Behavior

- Null/missing source field -> no lineage prop.
- One populated contributing source field -> one lineage prop.
- Multiple agreeing source fields -> multiple lineage props, preserving the truth.
- Conflicting native objective mappings continue to fail closed under the
  existing singleton-target conflict rule.
- Native OSCAL objective payloads are not changed by the lineage transform.

## Repository validation

- Maintained Cells 3 and 4 were updated.
- cells_v2 and NB_ARCHER_OSCAL_MAPPER_V1.py were regenerated from maintained cells.
- GitHub Actions run 36769347168 passed the generated-notebook synchronization check.
- In that run, both focused lineage tests passed:
  - test_namespaced_source_field_lineage_property_emits_exact_shape
  - test_property_namespace_must_be_absolute_uri
- The overall branch workflow still failed on unrelated pre-existing lean-suite
  issues that were already present before this lineage change; this checkpoint
  does not claim a clean full-suite release.
- A read-only preview inspection helper was added:
  notebooks/validation/15_ssp_security_impact_lineage_prop_preview.py

GitHub Actions on this branch already had unrelated pre-existing lean-suite
failures before this change. Do not treat the branch-wide workflow as a clean
release gate for this feature.

## Snowflake status

No live Snowflake run was performed from this chat.
No target DML is claimed.

## Next action

Owner reruns Cells 2-7 with EXECUTE_WRITES=False, then runs the read-only
lineage-prop preview helper. Review the emitted lineage props before any COMMIT.
