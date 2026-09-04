# SSP Notebook Cell Library

Copy these cells into the existing SSP notebook and run them in numerical order.

> **Safety:** Keep `EXECUTE_WRITES = False`. These cells inspect Archer source values and do not write to SSP DIM or FACT tables.

## Prerequisites

The existing notebook must already provide:

- `source_df`
- `_parse_source_json(record)`
- `resolve_json_path(source_obj, field)`

## Cells

1. [Cell 1 - Shared configuration and safety guard](01-configuration-and-safety.md)
2. [Cell 2 - Show up to 10 SSPs with populated candidate prop fields](02-sample-populated-props.md)
3. [Cell 3 - Count populated candidate prop fields across all SSPs](03-count-populated-props.md)

## Complete source

- [`notebooks/ssp_props_read_only_cells.py`](../../notebooks/ssp_props_read_only_cells.py)

Last synchronized from the complete source on 2026-09-04.