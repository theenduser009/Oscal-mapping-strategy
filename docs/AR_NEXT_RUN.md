# Assessment Results - preserve explicit nulls in warehouse observations

The 32 approved AR scalar-score mappings retain one observation per source field
when its exact source key is present with JSON null or a supported populated value.
The source binding remains Source One, and the target remains
`assessment-results.results[].observations[]` with an inline named property.

| Source state | Result |
| --- | --- |
| Key present, JSON null | Observation with `props[].value: null` |
| Supported non-null value, including zero/false | Existing string-valued property |
| Key absent | No observation; no alias or invented null |
| Empty string/list/object | Existing omission behavior |
| Unsupported populated value | Run blocks before writing |

For example, source `INITIAL_RISK_ASSESSMENT: null` retains a property named
`initial-risk-assessment` with actual JSON null. The observation key, UUID and
parent link stay the same when the value changes later. The string "null" is
never substituted. Deferred mappings remain deferred.

## Replace three cells, then preview

1. Replace these files in the existing notebook:
   - [Cell One](../notebooks/cells/01_initialization_and_configuration.py)
   - [Cell Three](../notebooks/cells/03_canonical_mapping_contract.py)
   - [Cell Four](../notebooks/cells/04_parsing_transform_payload_helpers.py)
2. Keep the current [AR32 mapping CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
   This null-policy change does not modify it. Keep the other four cells from
   the same simplification branch; no registry setup, DDL or table reset is needed.
3. Set `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)` in Cell One and retain
   `CONFIG["EXECUTE_WRITES"] = False`. Its AR runtime options now include
   `preserve_null_observations: True`.
4. Set Cell Seven's `OSCAL_LOAD_MODE = "PREVIEW"`, then run Cells One through
   Seven in order. Matching compiler/helper release is `lean-csv-registry-v3`;
   old compiled plans reject instead of silently losing the new behavior.
5. Review Cell Three's 32 selected rows and Cell Seven's complete preview report.
   Newly represented nulls create observations and their parent links. Existing
   score-to-null changes update the same DIM identity without changing FACT links.
   Counts depend on the selected source snapshot; no fixed live count is assumed.

Expected completion: `PREVIEW_COMPLETE` / `PREVIEW_PASSED_NO_TARGET_DML`, with
validation and storage checks passed and writes/commit false. After reviewing
those differences, use Cell Seven COMMIT for the planned write and retain its
committed readback. No live run of this null-preserving release is accepted yet.

## Warehouse fidelity and validation

The [NIST OSCAL property definition](https://pages.nist.gov/OSCAL-Reference/models/v1.2.2/assessment-results/json-reference/)
requires a string property value. Literal null is the owner's warehouse
representation, not a schema-valid OSCAL property. Graph/storage success does
not establish a valid complete OSCAL export; `FULL_MODEL_COMPLETE` and
`SCHEMA_VALIDATED` remain false.

Local checks ran 203 tests without failures, with three unavailable-Snowpark
class skips. Focused regressions cover explicit null versus absent keys, all 32
approved null fields, stable UUID/hash/link identities, preserved zero and false,
invalid inputs, old plans, JSON-null insert/readback and unchanged retries. A
seven-cell null/readback test passed with installed Snowpark.
[CI passed all 217 tests with zero skips](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34793258107)
on code commit 8a598cf64fbb54f23bc4f024b78bc3375fc98b19. The SQL boundary uses the
explicit local relational adapter, not a live Snowflake connection.

Four readable private source score examples still produce identical payloads,
identities and links. They were tested as independent partial excerpts, not a
complete source dataset. The newly reported initial-risk null is owner-reported;
its behavior is covered by a synthetic null fixture, not a newly fetched export.
No private source values or identifiers are published.

The existing SSP and AR committed-readback checkpoints remain accepted. POAM's
2,821-node / eight-edge preview is accepted; POAM committed readback remains
unverified. The 13 deferred AR mappings and unresolved exact threshold-source
names are separate from this null policy.
