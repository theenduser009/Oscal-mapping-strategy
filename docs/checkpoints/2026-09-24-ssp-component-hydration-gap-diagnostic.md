# SSP component hydration lookup gap diagnostic prepared — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `bf95d658199cebcdf6ba9fc1c34294586f96b7eb`

## Owner-provided live evidence
After Source One RAW repopulated to 2,813 records, the read-only SSP graph
diagnostic reported:

- SOURCE_SELECTED_ROWS = 2,813
- ROUTING_STATUS = READY
- SELECTED_MAPPING_ROWS = 54
- EXECUTE_WRITES = false
- STORAGE_CONTRACT_VERIFIED = true
- GRAPH_BUILD = FAILED
- UNDERLYING_ERROR_TYPE = ValueError
- UNDERLYING_ERROR_MESSAGE = `Component hydration lookup record is missing`

No target write or commit was attempted.

## Code-path interpretation
The current Cell 4 raises this exact error when the complete set of referenced
component ContentIds for a hydrated reference type is not present in its configured
lookup snapshot.

Current hydrated SSP component contracts are:
- SOFTWARE -> software lookup -> ARCHER_CONTENT_SOFTWARE_RAW
- INTERCONNECTIONS -> interconnection lookup -> ARCHER_CONTENT_INTERCONNECTIONS_RAW
- INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM -> same interconnection lookup

SUBSYSTEMS, HARDWARE and SAP_INTAKE_FORM_INTERCONNECTIONS do not require lookup
hydration under the current mapping.

## Next diagnostic
Root `RUN_NOW.py` now compares, by component type:
- distinct Source One referenced ContentIds
- frozen Cell-2 lookup row/ID counts
- current live lookup RAW row/ID counts
- matched and missing reference counts in frozen and live lookup data

The helper prints aggregate counts only; it does not expose ContentIds and performs
no DML.

## Next action
Run only the current root `RUN_NOW.py` in the same populated notebook session.
Do not weaken the hydration contract or run COMMIT until the missing lookup type
and coverage are known.
