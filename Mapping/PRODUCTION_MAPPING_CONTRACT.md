# Production Archer-to-OSCAL mapping contract

Date: 2026-10-01

The runtime CSV is intentionally lean. `NOTES` is temporarily retained as a human review aid, but execution does not depend on it. Historical spreadsheet coordinates, Markdown/GitHub provenance, duplicate target-path fields, and hand-maintained rule IDs are not runtime inputs.

## Runtime columns

SOURCE_FIELD_NAME, OSCAL_MODEL, OSCAL_ELEMENT_PATH, NOTES, EXECUTION_STATUS,
TRANSFORM_ID, SOURCE_KEY, NULL_POLICY, LINEAGE_REQUIRED, VALUE_SOURCE,
VALUE_REQUIRED, ALLOWED_VALUES, VALUE_MAP, OTHER_REMARKS_TEMPLATE, ROLE_ID,
ROLE_TITLE, REFERENCE_TYPE, LOOKUP_KEY, DESCRIPTION_REQUIRED.

Retired from runtime: MAPPING_TYPE, RUNTIME_TARGET_PATH, RULE_ID,
ORIGINAL_ROW_ID, SOURCE_DOCUMENT, SOURCE_LINE, ORIGINAL_EXCEL_ROW, EXECUTION_NOTE.
The exact pre-cleanup CSV is preserved under Mapping/archive for history only.

## Selective lineage prop

Only LINEAGE_REQUIRED=Y mappings that actually contribute a value emit:

```json
{
  "name": "source-field",
  "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
}
```

There is no namespace, class, target path, target UUID, source-table property, or lineage-group property. `value` is the exact Archer source field name. Traceability uses the lineage node's SOURCE_RECORD_ID together with the mapping CSV's SOURCE_FIELD_NAME -> OSCAL_ELEMENT_PATH contract and the FACT containment edge.

The production runtime does not depend on Mapping/*.md files, original Excel row
numbers, GitHub line numbers, or the archive CSV.


## Temporary NOTES column

`NOTES` is kept for the current review period. The mapper ignores it. Cell 2 treats it as an explicitly allowed optional column, so NOTES can be removed later without redesigning the mapping contract.
