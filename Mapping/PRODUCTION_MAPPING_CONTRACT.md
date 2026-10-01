# Production Archer-to-OSCAL mapping contract

Date: 2026-10-01

The runtime CSV contains only executable mapping metadata. Historical spreadsheet
coordinates, Markdown/GitHub provenance, development notes, duplicate target-path
fields, and hand-maintained rule IDs are not runtime inputs.

## Runtime columns

SOURCE_FIELD_NAME, OSCAL_MODEL, OSCAL_ELEMENT_PATH, EXECUTION_STATUS,
TRANSFORM_ID, SOURCE_KEY, NULL_POLICY, LINEAGE_REQUIRED, VALUE_SOURCE,
VALUE_REQUIRED, ALLOWED_VALUES, VALUE_MAP, OTHER_REMARKS_TEMPLATE, ROLE_ID,
ROLE_TITLE, REFERENCE_TYPE, LOOKUP_KEY, DESCRIPTION_REQUIRED.

Retired from runtime: MAPPING_TYPE, NOTES, RUNTIME_TARGET_PATH, RULE_ID,
ORIGINAL_ROW_ID, SOURCE_DOCUMENT, SOURCE_LINE, ORIGINAL_EXCEL_ROW, EXECUTION_NOTE.
The exact pre-cleanup CSV is preserved under Mapping/archive for history only.

## Selective lineage prop

Only LINEAGE_REQUIRED=Y mappings that actually contribute a value emit:

```json
{
  "name": "source-field",
  "ns": "urn:company:oscal:lineage:v1",
  "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
}
```

The namespace marks the property as the organization's OSCAL extension and v1
versions those extension semantics. There is no class, target path, target UUID,
source-table property, or lineage-group property; the mapping CSV already records
the target.

The production runtime does not depend on Mapping/*.md files, original Excel row
numbers, GitHub line numbers, or the archive CSV.
