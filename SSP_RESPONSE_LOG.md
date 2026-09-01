# SSP Response Log

This file mirrors substantive project responses so the current guidance and code links are easy to copy from GitHub.

Publishing rules:

- Project decisions, notebook instructions, code links, and status updates are committed automatically.
- Executable code stays in dedicated source files and is linked from this log.
- Credentials, authentication data, and raw sensitive Archer records are never published because this repository is public.

## 2026-09-01 - Automatic publishing enabled

Automatic publishing is now active for the Archer-to-OSCAL SSP work.

### Current continuation point

The active target is `system-characteristics.props[]`.

The confirmed read-only notebook cells are available at:

- [`notebooks/ssp_props_read_only_cells.py`](notebooks/ssp_props_read_only_cells.py)

### Next action

1. Confirm `EXECUTE_WRITES = False`.
2. Run Cell 3, **count populated candidate prop fields across all SSPs**.
3. Paste only the output beginning with:

```text
=== POPULATED PROP FIELD COUNTS ===
```

Those counts determine which source fields need value-resolution rules and which can be excluded before the final OSCAL `props[]` transformation is designed.
