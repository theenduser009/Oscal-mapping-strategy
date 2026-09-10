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

## 2026-09-10 — Next Cell 7 transformation-handler failure

Run ID: `20260910T183511Z`
Model: `SSP`

Component hydration again completed first:
- lookup rows: 1435
- interconnection rows: 1428
- interconnection descriptions: 968
- software rows: 7
- software descriptions: 7

New failure:
`ValueError: Mapping has no approved transformation handler: source_field=ATOIATO_DATE; owner_path=system-security-plan.system-characteristics; target_field=date-authorized; ...`

Traceback remains the same dispatch path:
- Cell 7 `run_oscal_mapping`
- Cell 5 `build_oscal_graph`
- Cell 4 `build_element_instances`
- Cell 4 `apply_mapping_transform`
- Cell 4 `_mapping_handler_for_row`

Interpretation: component hydration remains successful. Execution has advanced to the next unmapped/unapproved transformation-dispatch case, now `ATOIATO_DATE` -> `system-characteristics.date-authorized`. Do not invent timestamp/date semantics or a handler; reconcile this row against the mapping artifact Notes and approved transform contract.

Source: phone screenshots supplied in ChatGPT conversation on 2026-09-10.