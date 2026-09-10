# Live Snowflake Mapper Results

## 2026-09-10 — Cell 7 failure after component hydration

Run ID: `20260910T181836Z`
Model: `SSP`

Component hydration completed before the failure:
- lookup rows: 1435
- interconnection rows: 1428
- interconnection descriptions: 968
- software rows: 7
- software descriptions: 7

Cell 7 then failed while building element instances / applying a mapping transform.

Error:
`ValueError: Mapping has no approved transformation handler: source_field=INFORMATION_SYSTEM_TYPE; owner_path=system-security-plan.system-characteristics; target_field=information-system-...; mapping_type=extension-property`

Traceback path shown in Snowflake:
- Cell 7 `run_oscal_mapping`
- Cell 5 `build_oscal_graph`
- Cell 4 `build_element_instances`
- Cell 4 `apply_mapping_transform`
- Cell 4 `_mapping_handler_for_row`

Important: this is now a specific mapping-dispatch/handler gap for `INFORMATION_SYSTEM_TYPE`, not a component-hydration failure. Do not invent a transform. Inspect the canonical mapping row/Notes and the approved handler-dispatch contract before changing Cell 4.

Source: phone screenshot supplied in ChatGPT conversation on 2026-09-10.