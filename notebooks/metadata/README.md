# Metadata inputs - no catalog upload

The deployed notebook no longer reads a JSON catalog.

| Maintained input | Responsibility |
| --- | --- |
| [Mapping CSV](../../Mapping/ARCHER_OSCAL_MAPPINGS.csv) | Source field, original model/path/type/Notes, approval status, target and reusable conversion choices. |
| [Extended registry](../../docs/REGISTRY_METADATA_SETUP.md) | Active hierarchy, collection identity, operators, required mappings, UUID and assembly policies. |
| Cell One | Source/lookup locations, model selection and verified destination settings. |

The compiled plan is generated in memory, not maintained as another document.
Notes remain evidence, not code. Unknown transformations, conflicts and missing
required metadata stop execution; deferred rows are not silently approved.

The retired JSON is preserved as a [test-only frozen fixture](../../tests/fixtures/mapper_contract_pre_registry.json)
and in Git history. Do not upload or edit test fixtures for a notebook run.

This release preserves the 147 reviewed source occurrences, existing guard and
three existing required support values. It does not complete unresolved SSP
mappings or expand AR beyond the accepted seventeen fields.

**Start with the [one-time registry setup](../../docs/REGISTRY_METADATA_SETUP.md).**
No live setup or new notebook preview has been accepted yet. Normal DIM/FACT
writes remain disabled; AR storage remains unverified.
