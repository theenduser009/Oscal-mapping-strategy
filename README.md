# OSCAL Mapping Strategy

One metadata-driven Archer-to-OSCAL mapper, maintained as seven Snowflake notebook cells.

## Start here — updated October 1, 2026

Read [current status](docs/CURRENT_STATUS.md), then [project handoff](docs/PROJECT_HANDOFF.md). These are the current entry points for code, decisions, verified evidence, gaps, and the next action. The [project walkthrough](docs/PROJECT_WALKTHROUGH.md) retains the historical explanation; older counts and source line references are not current acceptance evidence.

## Published matching seven-cell set

- [Seven maintained cells, in order](notebooks/cells/README.md).
- [Combined notebook generated from those cells](notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py).
- [Generated copy-ready pages](notebooks/cells_v2/README.md).
- [Read-only property reader](notebooks/validation/15_ssp_universal_lineage_prop_preview.py).
- [Publication checkpoint and validation boundaries](docs/checkpoints/2026-10-01-seven-cells-published-to-github.md).
- [Exact source and generated-file hashes](docs/checkpoints/2026-10-01-seven-cell-publication-manifest.json).

Compiler/helpers: `lean-csv-registry-v5-lineage`. Loader: `oscal-lean-daily-v3.2-lineage`. Use all seven together. The runtime files are now in GitHub, not only in conversation attachments. They remain a locally tested candidate, not a production-approved deployment.

The delivered candidate's 73 scenarios and 53 focused tests were rerun locally before publication: **126 passed**. Native non-lineage graph parity passed across five synthetic models/six routes. This used the limited Python/SQLite adapter, not a Snowflake service. Full maintained repository CI, current production mappings/registry, native Snowflake integration, and complete OSCAL export validation remain separate gates.

## Decisions preserved

Native approved mappings stay native. Approved business extensions use props at their approved owner. Needed source attribution also uses props, captured only from actual contributions to surviving objects. No new lineage table, per-field lineage switch, or duplicate mapping rows. Unmapped/TBD/DEFERRED/EXCLUDED data is not automatically approved or dumped into props.

One-to-one attribution relies on matching versioned mapping definitions. Namespace governance, portable export consumption, and controlled reconciliation of obsolete lineage remain open release requirements. See current status for detail.

## Safety and maintenance

Keep `CONFIG["EXECUTE_WRITES"] = False` and Cell 7 `OSCAL_LOAD_MODE = "PREVIEW"`. Publication to GitHub does not authorize a database write. Unknown transaction outcomes require readback, not a blind retry.

Edit only `notebooks/cells`, then generate packaging outputs:

```shell
python tools/sync_notebook_cells.py
python tools/sync_notebook_cells.py --check
```

The existing `tests/lean` suite remains an additional compatibility gate; the 126 local checks are not a claim that it passes. Do not remove failing assertions to declare a release ready.

[Mapping CSV](Mapping/ARCHER_OSCAL_MAPPINGS.csv), [architecture context](docs/ARCHITECTURE_CONTEXT.md), [mapping progress](docs/MAPPING_PROGRESS.md), and [decision history](docs/DECISION_LOG.md) remain available. No mapping CSV, registry, DDL, or Snowflake target was changed by this publication.

## Historical material

The full pre-publication README is preserved [at revision 94e41f8](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/README.md). Dated checkpoints retain their original evidence. Older Profile/SAP next-step instructions and historical CI passes do not override the current status or prove this release.
