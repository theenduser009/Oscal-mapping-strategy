# POAM-only rebuild approved — September 28, 2026

## Decision and supersession
The owner accepts discarding the old POAM output and rebuilding the current approved POAM graph. This authorization is limited to the POAM DIM/FACT pair; it does not mean rebuilding every OSCAL model. Retaining the old POAM records is not an owner requirement. This supersedes the backup-first recovery proposal and makes write-history investigation optional rather than the next recovery prerequisite. It does not erase the recorded orphan findings or establish their cause.

## Repository checked
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Head read before this documentation update: 8b63cdb22a89841c41a8ed338a6eee4b19a84577.

Actual source read at that head:
- notebooks/cells/01_initialization_and_configuration.py, lines 1–242; blob f64fe16dc45e89c3b42cda36eccbcfe43d0ecd75.
- notebooks/cells/07_mapper_orchestrator.py, complete; blob 78166e558cf99600d75e2995a7bae4144dad9534.
- Mapping/ARCHER_OSCAL_MAPPINGS.csv, POAMS row in lines 138–146; blob e00466381404571bcf0d570ad44992801946d248.
- AGENTS.md, lines 1–110. Its older scope paragraphs do not supersede the later dated evidence and current owner request.

## Why other model loads are not required
Cell One binds POAM only to source-one. Source Two binds CATALOG and ASSESSMENT_RESULTS, not POAM. The source-selection loop intersects SELECTED_MODELS with each source's MODEL_BINDINGS. Therefore SELECTED_MODELS=("POAM",) produces only the source-one/POAM route in this checked-in configuration. Cell Seven executes the compiled routes, not every configured model.

The POAM storage contract writes only:
- RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_POAM_ELEMENT
- RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_POAM_DEPENDENCY

No SSP, Assessment Results, Assessment Plan or Catalog reload is required by these reviewed runtime bindings. No RAW/source deletion, registry reset, schema recreation, mapping change or shared-loader change is authorized by this recovery decision. External consumers and live notebook overrides were not inventoried; the checked-in route isolation is not a claim that no external system reads POAM data. Coordinate a maintenance window for the reset/load if readers or writers use those tables.

## Mapping retained
The existing APPROVED POAMS reference mapping targets plan-of-action-and-milestones.poam-items[]. It is a package-scoped reference graph. Rebuilding reuses that mapping and the existing identity rules; it is not a new mapping design and does not add full POAM item-detail hydration or full-document OSCAL conformance.

## Current evidence preserved
The owner-posted September 28 diagnostics establish 2,583 POAM FACT rows: 2,575 with both hash endpoints missing and eight with both present. Neither endpoint UUID of the 2,575 was found in current POAM DIM; the searched current SSP, Assessment Results and Assessment Plan tables also returned no matches. Cause is unresolved, but historical recovery is not required by the owner.

The batch-scoped loader orphan-check gap remains open. A passing candidate PREVIEW or COMMIT is not a substitute for post-rebuild whole-table relationship QA. The upstream RAW_DATA-to-CURATED_JSON saved-reference match remains separate evidence.

## Recovery sequence
1. Build a fresh POAM-only candidate graph and confirm it can be validated before clearing the current output.
2. Replace only the reviewed POAM output using a controlled reset/load. The old POAM data need not be backed up to satisfy the owner's stated requirement. Pause competing writers; keep the other tables untouched. Destructive reset instructions follow the candidate result, not this document.
3. Require successful POAM COMMIT/readback and fresh table-wide orphan, key, UUID, ownership and cardinality checks against the replacement graph. Counts come from the current source; the historical eight relationships are not a forced target.

## Immediate action — candidate PREVIEW only
Use the existing current seven-cell notebook and mapping CSV. Change the selector in Cell One:

```python
SELECTED_MODELS = ("POAM",)
```

Keep the existing CONFIG entry `"EXECUTE_WRITES": False` unchanged. In Cell Seven use:

```python
OSCAL_LOAD_MODE = "PREVIEW"
```

Run Cells One through Seven in order so the selected source snapshot, CSV, registry and compiled contexts are refreshed for POAM. Keep the notebook session open. No target DIM/FACT rows should be modified in this step; normal preview may create session-local temporary tables.

Inspect OSCAL_PIPELINE_REPORT for exactly one group: source=source-one, model=POAM. The intended outcome is PREVIEW_COMPLETE with route status PREVIEW_PASSED_NO_TARGET_DML, positive source coverage, graph/storage/pre-write checks true and target write flags false. Record the actual node/edge counts and proposed changes. If any other route appears, stop before a write because the live notebook does not match the checked-in selection used for this plan. If preview fails, resolve that failure before reset.

This preview builds the replacement; it does not clear or re-diagnose the already-known 2,575 orphan facts. A no-change preview does not remove those facts.

## Validation and execution state
Performed: read current branch, relevant configuration/routing code and mapping row; manual inspection of the one-source/one-model selection and exact target names. This is a documentation-only decision/procedure update. No new runtime tests, synthetic tests, CI runs or live Snowflake operations were performed for it. No mapper/CSV/registry/loader code was changed.

State: rebuild scope approved; first replacement PREVIEW pending; reset not executed; reload not committed; post-rebuild readback and whole-table QA pending. GitHub publication/readback of this document does not change those database states.
