# Project handoff — read before resuming

Updated October 1, 2026. Active branch: `simplify-metadata-boundary`.

## Where the work stands

The owner selected props-based source attribution, one universal seven-cell engine, no extra lineage table, no per-field flags, and no unnecessary duplication. After local hardening, the owner explicitly requested publishing the matching delivered candidate into GitHub. The current publication now replaces all seven maintained runtime files and their generated copies. It is not a Snowflake deployment or production acceptance.

Start with [CURRENT_STATUS.md](CURRENT_STATUS.md), [the publication checkpoint](checkpoints/2026-10-01-seven-cells-published-to-github.md), and [the exact file manifest](checkpoints/2026-10-01-seven-cell-publication-manifest.json). Inspect the actual current branch/ref before editing; do not assume every project source or latest owner report has been retrieved.

## Current code and responsibility

| Location | Responsibility |
|---|---|
| `notebooks/cells` | Single maintained seven-cell implementation |
| `notebooks/cells_v2` | Generated copies of those same seven files |
| `notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py` | Combined generated notebook |
| `tools/sync_notebook_cells.py` | Existing packaging tool; run generator and `--check`, not as a Snowflake cell |
| `notebooks/validation/15_ssp_universal_lineage_prop_preview.py` | Separate read-only parsed-JSON property reader for built route graphs |
| Mapping CSVs referenced by Cell 1 | Exact source names, approved target paths, reusable transforms and null policies |
| `OSCAL_ELEMENT_REGISTRY` | Model hierarchy, collection identity, registered operators and ownership |

Matching versions: `lean-csv-registry-v5-lineage` and `oscal-lean-daily-v3.2-lineage`. Use all seven together, not a mixture of old helpers/plans. Configuration sources and destinations are defined by the current Cell 1, not by historical handoff counts.

The seven steps remain configuration, frozen inputs, mapping compilation, transformation/assembly, graph/attribution, guarded load, and orchestration. Matillion's upstream enrichment supplies CURATED_JSON; this notebook does not execute Matillion.

## Decisions to retain exactly

Native approved values stay native. Approved non-native business fields use props at the approved owner. Needed source attribution uses grouped props from actual successful contributions to retained targets. Unknown/TBD/DEFERRED/EXCLUDED fields are not automatically approved or routed to props.

The shared compiler detects ambiguous targets and joined-source context from approved metadata. The runtime preserves exact object-instance ownership; it does not guess from a similar field name or outer package. One-to-one attribution depends on the matching versioned mapping definition being available. `source-field` is the exact SOURCE_FIELD_NAME, not an invented Archer UI display label.

`source-field` and `target-path` share a stable group; joined data adds source-system/table/record. Ancestor attribution for repeated objects requires their existing validated native UUID, otherwise the graph reports a gap. The parsed reader handles both separate prop nodes and inline props. Exporters reordering inline props must preserve/recompute pointers.

No mapping approval, new FIPS/Legacy equivalence, group resolver, automatic href, deletion policy, native key seed change, or table change accompanied publication. Namespace governance remains pending for the existing development namespace. Preserve explicit source-null policies and absence distinction; warehouse JSON null is not automatically conformant exported OSCAL property text.

## Evidence that is actually established

Before publication the delivered code was byte-checked against its manifest, the 73 candidate scenarios and 53 focused tests were rerun, and all 126 passed. Native non-lineage parity passed across five synthetic models and six source/model routes: 384 native nodes, 312 native edges. The existing generator compiled and synchronized the packaging outputs.

These are limited Python/SQLite local-adapter checks. They are not official Snowpark, native SQL, permissions, real data, concurrency, performance, the entire maintained test suite, full production CSV/current registry, or complete OSCAL schema validation. No new live database run or COMMIT/readback was performed. Repository readback and CI must be reported separately at the publication revision.

## Safety and next action

Keep shared EXECUTE_WRITES false and Cell 7 PREVIEW. Preview may create temporary staging; it does not write target DIM/FACT. Route commits are separate transactions. Preserve obsolete-row, schema, PK/FK/UUID, source/instance ownership, rollback and readback safeguards. Contributor removal or already-stored broad-lineage rows need controlled reconciliation. Unknown commit outcomes require inspection, not a retry.

Next: maintained-suite and native compatibility validation of the exact published set before a bounded, explicitly authorized Dev integration. Check newer SAP/POAM and other owner results before requesting repeat runs. Historical AR30 cannot establish AR32; historical SSP cannot establish later daily-loss or lineage changes.

## Context inventory and history

The OSCAL Project's `00_START_HERE.txt`, `01_CURRENT_CODE_AND_METADATA.txt`, `02_PROJECT_HISTORY_AND_GUIDES.txt`, and `03_COVERAGE_AND_HISTORICAL_SUPPORT.txt` are dated reference bundles. They do not transfer a live database session, original complete mapping workbook, private screenshots, or current full registry. Partial screenshot-derived Excel and collection-only registry excerpts must not be upgraded into those missing originals.

Use [PROJECT_WALKTHROUGH.md](PROJECT_WALKTHROUGH.md), [ARCHITECTURE_CONTEXT.md](ARCHITECTURE_CONTEXT.md), [MAPPING_PROGRESS.md](MAPPING_PROGRESS.md), [DECISION_LOG.md](DECISION_LOG.md), and dated checkpoints for historical detail. Older cell walkthrough line numbers and run instructions require comparison with current code. No mapping inventory is refreshed by this publication because no CSV changed.

The full previous handoff remains [at revision 94e41f8](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/docs/PROJECT_HANDOFF.md). All old checkpoints remain intact. This current page supersedes their old next-action prose, not their dated evidence.

For future material changes: inspect source/ref, publish the authorized code and dated evidence, update current status and handoff, verify remote content, and retain Project attachments. Do not claim permanent memory, automatic synchronization, new Source membership, or background monitoring without actual supported actions.
