# Mapper V1 — copy-ready Snowflake cells

These files are synchronized copies of the seven sections in
[the authoritative complete notebook](../NB_ARCHER_OSCAL_MAPPER_V1.py).

Copy each file into one Snowflake Python cell and run them in numerical order.
The files depend on state initialized by the preceding cells. Do not maintain a
separate implementation here; future mapper corrections must update the
complete notebook and the affected split cell together.

## Run order

1. [Initialization and configuration](01_initialization_and_configuration.py)
2. [Source, mapping, and registry inputs](02_source_mapping_registry_inputs.py)
3. [Canonical mapping contract](03_canonical_mapping_contract.py)
4. [Parsing, transformation, and payload helpers](04_parsing_transform_payload_helpers.py)
5. [Registry graph builder](05_registry_graph_builder.py)
6. [Validation and guarded loader](06_validation_and_guarded_loader.py)
7. [Mapper orchestrator](07_mapper_orchestrator.py)

## Read-only checkpoint after Cell 7

After Cell 7 completes with writes disabled, run the separate
[SSP scope and coverage validation](../validation/RUN_AFTER_07_ssp_scope_validation.py).
It is a temporary diagnostic cell, not an eighth production cell.

Once scope validation passes, run the separate
[SSP payload-semantics validation](../validation/RUN_AFTER_07_ssp_payload_semantics_validation.py).
It checks security-impact, status, property, responsible-party, document-ID,
and component-reference payload shapes without printing source payloads or
writing to DIM/FACT tables. The corrected version distinguishes optional
absent security-impact from partial C/I/A assemblies under pinned OSCAL
SSP 1.2.3.

If that validator reports semantic failures, run the privacy-safe
[semantic failure diagnostic](../validation/RUN_AFTER_07_ssp_semantic_failure_diagnostic.py).
It reports aggregate dispatch, type, key-shape, and collision evidence only;
it does not print source record IDs or payload values.

When security or status mappings still need a business crosswalk, run the
[controlled-vocabulary crosswalk review](../validation/RUN_AFTER_07_ssp_crosswalk_review.py).
It prints only lookup metadata labels and aggregate counts—never Archer IDs,
source record IDs, or complete payloads.

After the mapped-scope diagnostics, run the separate
[OSCAL 1.2.3 minimum-required-scope audit](../validation/RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py).
It checks the required SSP skeleton and minimum required fields against the
pinned version contract. It remains aggregate-only and read-only, and does not
replace assembled-document schema or constraint validation.

The repository baseline keeps `EXECUTE_WRITES = False`.

## Current post-revision checkpoint

Run `20260908T201705Z` passed graph and pre-write validation with 51,500
nodes, 48,687 edges, zero duplicate/dangling keys, and no writes. The reviewed
semantic revision behaved as expected. The OSCAL target is now pinned to SSP
1.2.3 in authoritative Cell 1 and this split copy.

The narrow version-specific review found 179 missing security-objective
occurrences inside 90 partial optional assemblies and 42 missing required
`status.state` values, affecting 131 unique records. It found no source/output
transformation loss.

If the same Snowflake session is still active, run only the
[minimum-required-scope audit](../validation/RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py)
in a new Python cell. A pre-pin session is accepted; a conflicting configured
version fails closed. If the session was restarted, use the updated Cell 1 and
run Cells 1-7 first.

The current 17-path subset is not a complete SSP. Component hydration, required
whole-document branches, assembled-document schema validation, and constraint
validation remain gates. Keep `EXECUTE_WRITES = False`.
