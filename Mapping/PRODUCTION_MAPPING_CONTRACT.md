# Production Archer-to-OSCAL mapping contract

Date: 2026-10-01

The Source One CSV is bound to Source One by its configured file/profile, so it
does not repeat SOURCE_KEY on every row. OSCAL_MODEL uses canonical model keys,
and default controls are left blank so only exceptions stand out.

## Runtime columns

SOURCE_FIELD_NAME, OSCAL_MODEL, OSCAL_ELEMENT_PATH, EXECUTION_STATUS, TRANSFORM_ID, LINEAGE_REQUIRED, NULL_POLICY, VALUE_SOURCE, VALUE_REQUIRED, ALLOWED_VALUES, VALUE_MAP, OTHER_REMARKS_TEMPLATE, ROLE_ID, ROLE_TITLE, REFERENCE_TYPE, LOOKUP_KEY, DESCRIPTION_REQUIRED, NOTES.

Defaults:
- blank LINEAGE_REQUIRED = no lineage; Y = emit selective source-field lineage
- blank VALUE_SOURCE = FIELD; CONFIG is explicit
- blank VALUE_REQUIRED = false; true is explicit
- blank NULL_POLICY = omit; preserve is explicit

NOTES is temporarily retained for human review only; mapper execution does not
depend on it.

DESCRIPTION_REQUIRED remains in the CSV because it changes component hydration
behavior for a specific mapping. ROLE_ID/ROLE_TITLE, REFERENCE_TYPE/LOOKUP_KEY,
ALLOWED_VALUES, VALUE_MAP and OTHER_REMARKS_TEMPLATE also remain because they are
real mapping semantics, not development provenance.

Retired from Source One runtime:
MAPPING_TYPE, RUNTIME_TARGET_PATH, RULE_ID, SOURCE_KEY, ORIGINAL_ROW_ID,
SOURCE_DOCUMENT, SOURCE_LINE, ORIGINAL_EXCEL_ROW, EXECUTION_NOTE.

The exact v8 CSV that produced the verified SSP COMMIT is preserved under
Mapping/archive and is not a runtime input.

## Selective lineage prop

Only LINEAGE_REQUIRED=Y mappings that actually contribute a value emit:

```json
{
  "name": "source-field",
  "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
}
```

Traceability is:
SOURCE_RECORD_ID (Archer Content ID) + lineage prop value (Archer field name) +
mapping CSV OSCAL_ELEMENT_PATH + FACT containment relationship.
