# SSP metadata title provenance and null-policy clarification

Date: September 30, 2026
Status: Repository/history and the partial Excel review workbook were inspected. No runtime mapping/code change is authorized by this checkpoint.

## Excel evidence boundary

The available ARCHER_OSCAL_MAPPING_REVIEW.xlsx explicitly states that it is a partial transcription of 147 listed entries and is not the full original 608-row workbook.

Within that partial review:
- AUTHORIZATION_PACKAGE_NAME appears under SSP - System Characteristics -> system-security-plan.system-characteristics.system-name.
- No reviewed Excel row maps AUTHORIZATION_PACKAGE_NAME to SSP metadata.title.

Therefore the available workbook does not establish metadata.title as an original Excel mapping.

## Why metadata.title exists in the runtime CSV

Current Mapping/ARCHER_OSCAL_MAPPINGS.csv contains:
- SOURCE_FIELD_NAME = AUTHORIZATION_PACKAGE_NAME
- OSCAL_MODEL = SSP - Metadata
- RUNTIME_TARGET_PATH = system-security-plan.metadata.title
- RULE_ID = support:metadata-title
- MAPPING_TYPE = Existing support mapping
- SOURCE_DOCUMENT = tests/fixtures/mapper_contract_pre_registry.json
- EXECUTION_NOTE = Existing support behavior, not an additional completed Excel row.

Repository history confirms:
- commit a07607cfb5368e870c8d2814a86c9cf788500a48 did not yet contain the support:metadata-title CSV row;
- commit 1e58f05c9e54bdf4f258ca30be9ede4a0bf1d13a added it during the registry-driven migration.

The frozen pre-registry contract already had metadata controlled_fields:
- title <- AUTHORIZATION_PACKAGE_NAME, text, required
- oscal-version <- CONFIG.OSCAL_VERSION, required
- version <- CONFIG.SSP_DOCUMENT_VERSION, required

So metadata.title was not copied from the original Excel review. It was an existing mapper support behavior moved into the governed CSV so executable field rules were not hidden in structural configuration.

## OSCAL requirement context

NIST OSCAL metadata requires a document title in the model structure. This explains why the mapper had a required title support value even when the source workbook did not provide a separate metadata-title mapping row.

## Null policy clarification

For OSCAL prop, name and value are required and prop.value is a string. A native OSCAL property with value=null is not schema-conformant.

Current runtime rows FISMA_REPORTABLE, FINANCIAL_SYSTEM and PIA_REQUIRED have no NULL_POLICY=preserve setting, so their JSON-null source values are omitted from generated props.

The mapper can preserve explicit null for selected warehouse mappings when NULL_POLICY=preserve is explicitly approved, but that is source-preservation behavior in the warehouse graph; it must not be described as a conformant OSCAL prop value.

No change to those three null policies is approved by this checkpoint.
