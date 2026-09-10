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

Before the metadata-completion release is run for the first time, use the
[guarded metadata registry setup cell](../setup/SETUP_SSP_METADATA_ROLE_PARTY_REGISTRY.py)
to add only the missing `metadata.roles[]` and `metadata.parties[]` rows. Its
registry-write flag is separate from the mapper and is `False` by default.

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
preserve those values unchanged for now. Cell 4 also sources the required
metadata title from `AUTHORIZATION_PACKAGE_NAME`; Cell 5 injects the controlled
OSCAL version and SSP document version `1.0` without changing timestamps.

The repository baseline keeps `EXECUTE_WRITES = False`.

## Current post-revision checkpoint

Pinned run `20260908T220830Z` passed graph and pre-write validation with
51,500 nodes, 48,687 edges, zero duplicate/dangling keys, and no writes. The
minimum-required-scope audit then found eight of thirteen required paths in the
registry, five absent paths, incomplete components, required payload gaps, and
zero of 2,813 records meeting the complete minimum contract.

The required-source readiness, mapping-artifact progress, metadata timestamp,
OSCAL-version, and document-ID checks have been executed. The latest accepted
read-only mapper run has 67,671 nodes and 64,858 edges with every structural
gate passing and no writes. The metadata branch remains accepted.

The system-characteristics property and system-ID collection contracts across
[Cell 4](04_parsing_transform_payload_helpers.py) and
[Cell 5](05_registry_graph_builder.py) are now runtime-accepted. The live run
retained 67,683 nodes and 64,870 edges, passed every structural gate, and made
no writes. Do not rerun the metadata setup or the accepted mapper cells for
that release.

The one-time aggregate
[component source-contract extraction](../validation/RUN_AFTER_07_ssp_component_source_contract.py)
is complete. It proved arrays of `ContentId,LevelId` objects plus one scalar-ID
array, all six declared component types, and 12 IDs shared across fields.

The component identity/type release in [Cell 4](04_parsing_transform_payload_helpers.py)
and [Cell 5](05_registry_graph_builder.py) is runtime-accepted at 67,671 nodes
and 64,858 edges, with all structural gates passing and no writes. Do not rerun
it. The one-time aggregate-only
[lookup-source discovery](../validation/RUN_AFTER_07_ssp_component_lookup_source_discovery.py)
is also complete: all 1,436 governed IDs were found, zero profiling stages
failed, and no writes occurred. Do not rerun that broad discovery.

The read-only
[Excel-driven component source-routing audit](../validation/RUN_AFTER_07_ssp_component_source_routing_audit.py)
is complete. It proved one unambiguous RAW route for software and one for both
active interconnection fields, while hardware has no hydration-bearing source.
Its JSON-null reporting false positive is corrected and did not affect route,
field, or graph results. Do not rerun this audit.

The owner-approved partial hydration release is runtime-accepted. Software
uses `SOFTWARE_NAME` and required `DESCRIPTION`; the two active
interconnection routes use `INTERCONNECTION_NAME` and include `DESCRIPTION`
only when populated. Hardware, subsystems, the inactive SAP route, and every
component status field remain deferred because the Excel/source evidence does
not supply those values.

The next release hardens Cell 4 against mapping-contract drift and adds the
read-only
[mapped-scope assembler](../validation/RUN_AFTER_07_ssp_mapped_scope_assembly.py).
Run updated Cells 1 through 7 once with writes disabled, then run the assembler
in the same session. It assembles one transient mapped-scope JSON document per
source record and prints only aggregate counts. It is not a complete-SSP or
OSCAL-schema-validity claim.

The latest Cell 7 failure names `INFORMATION_SYSTEM_TYPE`: Cell 3 assigned an
approved extension property to the parent instead of `props[]`. The current
[Cell 3](03_canonical_mapping_contract.py) fixes that routing for the eight
screenshot-confirmed property sources. It preserves the original artifact
path and leaves the strict Cell 4 guards unchanged.

The next live failure is `ATOIATO_DATE` → `date-authorized`, whose mapping
type/Notes are not fully recorded. **Do not rerun the mapper or assembler.**
In the current session run only the
[in-memory mapping contract report](../validation/RUN_AFTER_04_ssp_mapping_contract_report.py)
and post its output. It prints every unsupported row with its Excel Notes;
no database query or source-value access is involved. Keep writes disabled.
193 local tests pass; live acceptance is still pending and no date rule is guessed.

The current graph is healthy but is not a complete SSP. Component hydration,
required whole-document branches, assembled-document schema validation, and
constraint validation remain gates. Keep `EXECUTE_WRITES = False`.

Cell 4 now stabilizes responsible-party identity across roles, deduplicates
repeated references and mapping rows, and emits the five approved roles plus
their reusable `person` party objects. Cell 5 requires real `metadata.roles[]`
and `metadata.parties[]` registry rows, uses each party payload UUID as the
party node OSCAL UUID, and fails closed unless every role and party reference
resolves exactly once. The four `TBD` responsible-party rows remain excluded.
