# SSP PREVIEW obsolete-target failure likely explained by empty allocated-controls lookup

Date: September 29, 2026
Status: Current Cell 2 / Cell 4 code inspected after owner reported ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW is still loading and currently empty. No Snowflake write performed.

## Why this can produce OBSOLETE_TARGET_ROWS_BLOCKED

Source One SSP config binds joined-record lookup "allocated-controls" to:
RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW

Current Cell 2 cache_result() freezes that joined lookup when Cell 2 runs.

Current Cell 4 then:
1. joins the cached allocated-controls frame to Source One SOURCE_RECORD_ID values;
2. builds joined child collections only from rows returned by that join;
3. if the lookup frame is empty, produces no allocated-control children for any source record.

Previously persisted SSP target rows contain Level-355 implemented-requirement children derived from this lookup. If the refreshed candidate graph contains none because the lookup snapshot was empty, Cell 6 correctly identifies those existing target DIM/FACT rows as obsolete and raises OBSOLETE_TARGET_ROWS_BLOCKED during PREPARATION.

This mechanism is directly supported by the current code and is a strong explanation for the observed failure. It is not yet a database-count proof because the assistant has no live Snowflake access.

## Important cache boundary

Even after ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW finishes loading, the current notebook's Cell-2 joined lookup remains the earlier cached snapshot if Cell 2 was run while the table was empty.

Therefore do not rerun Cell 7 against the stale Cell-2 cache.

## Next action

Wait for ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW to finish loading. Confirm it is populated. Then rerun Cell 2 so the joined-record lookup is cached from the completed table, followed by the dependent mapping/graph cells and Cell 7 in PREVIEW.

The previously published obsolete-row diagnostic remains available only if PREVIEW still fails after the lookup has been refreshed from a populated table.
