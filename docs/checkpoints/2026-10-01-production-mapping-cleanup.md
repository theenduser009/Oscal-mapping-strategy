# Production mapping cleanup and minimal lineage prop — 2026-10-01

Base inspected: theenduser009/Oscal-mapping-strategy / simplify-metadata-boundary at 5590ac35c24cb691f9476b50f2f925f25bcb5bbc.

Implemented:
- runtime CSV reduced from 27 to 18 columns
- all 155 rows retained; operational settings preserved
- one canonical OSCAL_ELEMENT_PATH; INFORMATION_SYSTEM_TYPE normalized to props[]
- pre-cleanup CSV archived verbatim
- production header enforced for the configured Source One profile
- RUNTIME_TARGET_PATH and CSV RULE_ID removed from execution logic
- LINEAGE_REQUIRED compiled directly
- lineage prop simplified to name + ns + value; no class
- one lineage prop per contributing source field/host
- cells_v2 and combined notebook synchronized
- validator 17 and focused lineage tests updated
- production CSV contract test added

Unchanged intentionally: namespace urn:company:oscal:lineage:v1, 12 Y mappings,
transforms, null policies, role/reference behavior, graph containment, loader
safety, and destination schemas.

Evidence boundary:
The earlier live PREVIEW with 3,581 four-key lineage props belongs to the
superseded runtime. This repository change performs no Snowflake DML and does not
prove the new three-key payload live.

Next action:
Upload the cleaned CSV and matching seven cells, run SSP PREVIEW, then run
notebooks/validation/17_ssp_selective_lineage_contract_validation.py. No COMMIT
until the fresh PREVIEW and validator are reviewed.


## Repository validation actually performed

Code commit: `f5e5755d3e4eaeb733452fd1b65352def49188e0`

GitHub Actions run: `36897565862`

Confirmed:
- generated notebook synchronization check passed
- `test_production_mapping_contract` passed
- all 9 selective-lineage focused tests in `test_universal_lineage_props` passed
- the production CSV has 155 rows, exactly 18 runtime columns, and 12 LINEAGE_REQUIRED=Y rows
- read-back inspection confirmed Cell 5 no longer emits a lineage `class`

The full historical `tests/lean` suite remains red: 270 tests ran with 38
failures and 96 errors. The log includes known historical/fixture compatibility
issues, stale expectations for removed provenance/RULE_ID columns and older
153-row counts, plus local end-to-end fixtures that do not provision newer
Source One lookup tables. This full-suite failure is **not** being treated as a
successful production release.

No live Snowflake PREVIEW has yet been run for the new three-key lineage payload.
