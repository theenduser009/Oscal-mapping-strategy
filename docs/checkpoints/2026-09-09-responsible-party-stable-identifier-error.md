# SSP Mapper checkpoint — responsible-party stable identifier failure

Date: 2026-09-09
Run ID: `20260909T204147Z`
Model: `SSP`

## Cell 7 failure

```text
ValueError: Responsible-party reference has no stable identifier
```

Traceback path visible in Snowflake:

```text
Cell 7 line 45: run_oscal_mapping(...)
Cell 7 line 15: build_oscal_graph(...)
Cell 5 line 424: build_element_instances(...)
Cell 4 line 610: _active_responsible_party_instances(...)
Cell 4 line 418: _party_uuid_values(source_record_id, source_value)
Cell 4 line 395: _party_reference_identifier(item)
Cell 4 line 365: raise ValueError(...)
```

## Relevant registry context from immediately preceding checkpoint

`system-security-plan.metadata.responsible-parties[]` is an active collection with:

- `ELEMENT_TYPE = responsible-parties`
- `PARENT_NODE_PATH = system-security-plan.metadata`
- `IS_COLLECTION = TRUE`
- `INSTANCE_KEY_RULE = SOURCE_FIELD_NAME+ID`
- `PROCESS_ORDER = 3`
- `ITEM_PATH = UserList[]`

## Engineering interpretation

The graph builder is now reaching the governed responsible-party collection logic, but at least one reference item extracted from `UserList[]` does not provide an identifier accepted by `_party_reference_identifier()` as stable. Do not invent an ID or silently fall back to list position/value. Inspect the actual reference shape and the helper's accepted identifier keys before changing identity logic.

Writes remain blocked/read-only until this is resolved.