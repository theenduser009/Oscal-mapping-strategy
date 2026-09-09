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

After the readiness result is recorded, run the
[SSP mapping-artifact progress audit](../validation/RUN_AFTER_07_ssp_mapping_artifact_progress_audit.py).
It evaluates the complete Cell 2 crosswalk, including SSP-labeled rows with a
blank target path, keeps artifact-declared status separate from technical
runtime evidence, and prints the next implementation-ready SSP path in
root-to-leaf order, with an unresolved-review fallback. It does not infer a
missing target from a model label, field name, or note.

The metadata last-modified audit has now been executed. `LAST_UPDATED` supplies
all 2,813 current values, and every value is timezone-naive. The user chose to
preserve those values unchanged for now. Cell 5 therefore leaves timestamps
alone and injects only the controlled `OSCAL_VERSION` into each singleton
metadata payload.

The repository baseline keeps `EXECUTE_WRITES = False`.

## Current post-revision checkpoint

Pinned run `20260908T220830Z` passed graph and pre-write validation with
51,500 nodes, 48,687 edges, zero duplicate/dangling keys, and no writes. The
minimum-required-scope audit then found eight of thirteen required paths in the
registry, five absent paths, incomplete components, required payload gaps, and
zero of 2,813 records meeting the complete minimum contract.

The required-source readiness, mapping-artifact progress, and metadata
last-modified audits have now been executed. The updated Cell 5 and complete
mapper have also been rerun successfully. In the same active Snowflake
session, the metadata OSCAL-version and document-ID validations then passed for
all 2,813 records. The next production release updates both
[Cell 4](04_parsing_transform_payload_helpers.py) and
[Cell 5](05_registry_graph_builder.py): replace both, then run Cells 4, 5, 6,
and 7. It resolves metadata timestamp collisions without changing source
strings and makes optional security-impact emission complete-or-omit. Do not
run another standalone validator for this step.

The current graph is healthy but is not a complete SSP. Component hydration,
required whole-document branches, assembled-document schema validation, and
constraint validation remain gates. Keep `EXECUTE_WRITES = False`.

Cell 4 now also stabilizes responsible-party identity across roles and
deduplicates repeated references. This is an intermediate production
foundation for future `metadata.parties[]` nodes; do not rerun the notebook for
this change alone. Cell 4 now has controlled definitions for the five approved
roles, while Cell 5 requires a real `metadata.roles[]` registry row and never
synthesizes it. Party type is not inferred from the role name.
