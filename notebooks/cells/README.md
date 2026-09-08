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

After that result is recorded, run the
[required-source readiness audit](../validation/RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py).
It classifies registry, mapping-artifact, populated-source, current-owner,
nested-shaping, controlled-configuration, and generated-output evidence without
printing source names or values.

The repository baseline keeps `EXECUTE_WRITES = False`.

## Current post-revision checkpoint

Pinned run `20260908T220830Z` passed graph and pre-write validation with
51,500 nodes, 48,687 edges, zero duplicate/dangling keys, and no writes. The
minimum-required-scope audit then found eight of thirteen required paths in the
registry, five absent paths, incomplete components, required payload gaps, and
zero of 2,813 records meeting the complete minimum contract.

If the same Snowflake session is active, run only the
[required-source readiness audit](../validation/RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py)
in a new Python cell. It will establish which gaps already have aggregate
mapping/source candidates and which need registry, configuration, or mapper
shaping work. Do not rerun Cells 1-7 solely for this diagnostic.

The current graph is healthy but is not a complete SSP. Component hydration,
required whole-document branches, assembled-document schema validation, and
constraint validation remain gates. Keep `EXECUTE_WRITES = False`.
