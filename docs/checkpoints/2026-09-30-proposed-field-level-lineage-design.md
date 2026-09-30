# Proposed field-level lineage design for curated OSCAL

Date: September 30, 2026
Status: PROPOSAL — no table/code change implemented yet.

## Confirmed current behavior

The curated DIM nodes preserve source-record lineage (source system/table/record) and final OSCAL payloads, but they do not preserve the contributing Archer SOURCE_FIELD_NAME or RULE_ID for each mapped target member.

This is especially visible for SSP security-impact-level, where multiple Archer fields can feed the same singleton OSCAL member (confidentiality, integrity, availability).

A single SOURCE_FIELD_NAME column on DIM_OSCAL_SSP_ELEMENT would be incorrect because one target member may be supported by more than one agreeing source field.

## Recommended design

Keep OSCAL DIM payloads clean and add a separate lineage fact table:

FACT_OSCAL_SSP_FIELD_LINEAGE

Recommended minimal columns:

- PK_LINEAGE_HASH
- FK_TARGET_ELEMENT_HASH
- SOURCE_SYSTEM_NAME
- SOURCE_TABLE_NAME
- SOURCE_RECORD_ID
- SOURCE_FIELD_NAME
- RULE_ID
- TARGET_ELEMENT_PATH
- TARGET_JSON_POINTER
- MAPPED_VALUE_JSON
- DW_PIPELINE_RUN_ID
- DW_LOAD_TIMESTAMP

One row represents one source-field contribution to one target OSCAL member.

Example:

SOURCE_RECORD_ID: 866211
SOURCE_FIELD_NAME: INTEGRITY_CONTROL_CATEGORY_OVERRIDE
RULE_ID: ssp:INTEGRITY_CONTROL_CATEGORY_OVERRIDE:7
TARGET_ELEMENT_PATH: system-security-plan.system-characteristics.security-impact-level
TARGET_JSON_POINTER: /security-objective-integrity
MAPPED_VALUE_JSON: "low"
FK_TARGET_ELEMENT_HASH: <security-impact-level DIM key>

If two Archer fields both resolve to the same target value, store two lineage rows. If they conflict, existing mapper fail-closed behavior remains unchanged.

## Why not add SOURCE_FIELD_NAME to the DIM

The DIM row represents an OSCAL element, not one source mapping rule. One element can contain multiple target members, and one target member can have multiple agreeing source contributors. A scalar DIM source-field column would lose that cardinality.

## Implementation location

The mapper already has the required information while iterating mapping rows in Cell 4:
- current mapping row
- source field
- rule id
- transformed value
- target member/path
- source record id

Lineage should be captured at that point, carried with the graph result, and written after normal DIM/FACT validation.

No change is proposed to OSCAL METADATA_JSON.
No lineage DML has been implemented yet.
