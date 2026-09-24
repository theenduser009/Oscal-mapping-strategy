# Source One SSP PREVIEW zero-row source diagnosis prepared — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `60fdbe26f468a043de13dca44dc97b6bfe5da3ea`

## Owner-provided live diagnostic evidence
The SSP graph-build diagnostic showed:
- PIPELINE_STATUS = FAILED_BEFORE_COMMIT
- WRITES_EXECUTED = false
- COMMIT_ATTEMPTED = false
- MATCHING_CONTEXTS = 1
- ROUTING_STATUS = READY
- SELECTED_MAPPING_ROWS = 54
- SOURCE_SELECTED_ROWS = 0
- EXECUTE_WRITES = false
- STORAGE_CONTRACT_VERIFIED = true
- populated-value guard present for RECOMMENDED_SECURITY_CATEGORY
- GRAPH_BUILD = FAILED
- UNDERLYING_ERROR_MESSAGE = Graph builder produced no nodes
- GRAPH_REPORT SOURCE_RECORDS = 0
- GRAPH_REPORT STATUS = NOT_RUN

## Interpretation
The immediate failure is not a mapping-path or target-write failure. The compiled
SSP route is ready, but the frozen Source One input contains zero records.

Cell 2 snapshots the RAW source into a session-local frozen cache. Source One RAW
is delivered by a truncate-and-load process, so a zero-row frozen snapshot can
occur if Cell 2 executes during an upstream empty window. This is a hypothesis
until the live RAW count is checked.

## Next diagnostic
Root `RUN_NOW.py` now compares:
- current live Authorization Package RAW row/distinct-ID count
- the existing Cell-2 selection metadata
- the frozen `source_df` count
- the frozen snapshot count

No DML is performed.

## Next action
Run only the current root `RUN_NOW.py` in the same session. If live RAW is
populated while the frozen Cell-2 input remains zero, refresh the input boundary
rather than changing mapper logic.
