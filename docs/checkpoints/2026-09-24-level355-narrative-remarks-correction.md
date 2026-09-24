# Level-355 narrative member correction — 2026-09-24

## Version and evidence
Repository: theenduser009/Oscal-mapping-strategy.
Branch: simplify-metadata-boundary.
Before update: 2332bf37515f934edfe9bef088443cd6f93247e7.
Mapping update commit: 02435d74edcf02d7f1dfdb9526b205401d7016ec.
Test publication commit: 37572c5119641c15a0a8bc9b55afa126feaec548.
Old mapping blob: 7790f23e52767a7d4f5bc31226c1e26198e60557.
New mapping blob: 9fab56f3d5950d94773848df5ee2598417c4adc2.

The repository branch and complete mapping CSV were read at the pinned starting
commit. The local before-file reproduces the exact Git blob; the edited file
matches the blob returned by GitHub. Exactly one of 155 mapping rows changed.
All other mapping rows are byte-preserved; no runtime or registry code changed.

The September 14 handoff and coverage limitations remain historical. Recent owner
screenshots supersede their run counts, not their warning against equating stored
graph verification with full OSCAL conformance. Latest supplied SSP PREVIEW:
250,844 nodes / 248,031 edges / 2,813 source records; DIM 0 inserts, 127,495 updates,
123,349 unchanged; FACT 0 inserts, 0 updates, 248,031 unchanged. A later COMMIT was
recommended but its result has NOT been provided. No current database state is
inferred from that recommendation.

## Correction implemented
Source field: IMPLEMENTATION_DETAILS.
Both OSCAL_ELEMENT_PATH and RUNTIME_TARGET_PATH now target:

system-security-plan.control-implementation.implemented-requirements[].remarks

Status remains APPROVED. The text transform, allocated-controls lookup, source-one
binding, VALUE_REQUIRED=false, source field name, and historical RULE_ID are
unchanged. The old rule-id suffix ':description' is retained as an audit identifier,
not as the executable destination. Current target paths own routing.

The previous direct implemented-requirement.description approval was incorrect
for OSCAL 1.2.3 and is superseded. The schema permits remarks on that assembly;
component-level implementation description belongs under by-components[].
Primary source reviewed:
https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml

This is explicitly an INTERIM source-narrative preservation mapping, not completion
of component-level implementation. No implementing component ownership, UUID,
status, or control origination is inferred. A verified component reference and
valid by-component assembly remain needed for that separate mapping. The earlier
proposal to immediately move this text into by-components[] has therefore NOT
been silently claimed as implemented.

The package join and ALLOCATED_CONTROL_ID child identity are unchanged. Existing
handling of the one missing-control-number source child is unchanged. The current
candidate builder emits a fresh payload, so this row no longer emits the unsupported
'description' member. A subsequent ordinary payload MERGE, after PREVIEW review,
can replace a previously stored payload; no DELETE or rekey is required by this
mapping change. No target write was performed in this turn.

## Validation actually performed
- Exact before-file Git-blob equality verified locally.
- All 155 CSV rows parse with the existing 26-column header.
- Only the IMPLEMENTATION_DETAILS row changes: two paths and four documentation
  columns. All other rows and all identity settings are preserved.
- 13 local pure-Python compiler/emitter regression tests passed. The local test
  harness used reviewed function excerpts from the current compiler and joined
  emitter, assembled with unchanged helper definitions from the handoff. This is
  not a complete checkout integration run. The published test extracts those
  functions directly from maintained cells in the repository when run there.
- Covered: supported remarks member, compiler acceptance, null/empty omission,
  literal-null distinction, multiline Unicode, identity stability, duplicate
  conflict rejection, repeated control numbers with different allocation IDs,
  malformed control skip, and non-text rejection.
- Existing whitespace-only text remains fail-closed; this patch does not silently
  change that policy.
- No live Snowflake compilation/execution, full regression suite, GitHub CI run,
  full JSON-schema validation, or OSCAL constraint validation was performed.

## Next single validation run
In the existing notebook, replace/refresh only ARCHER_OSCAL_MAPPINGS.csv from this
branch. Keep the current runtime cells, SELECTED_MODELS=("SSP",), and shared
EXECUTE_WRITES=False. Run Cell 2, Cell 3, then Cell 7 with OSCAL_LOAD_MODE="PREVIEW".
No cleanup SQL, registry updates, old COMMIT_NOW.py, or profiler is needed.

Cell 2 refreshes the source/lookup snapshots as usual; required upstream loads must
be complete. If sources are unchanged, this patch adds no nodes/edges and changes
no keys. Do not hard-code an update count: it depends on the persisted payloads and
current source values. Review the resulting PREVIEW before COMMIT.

## Remaining gaps
The remarks correction is committed in GitHub, not yet previewed or committed in
Snowflake. Component-specific narrative/status, role/parameter/inheritance mappings,
source-to-catalog control-id compatibility, full-document conformance, and durable
reporting of skipped source rows remain separate work. No completion claim is made
for those items. OVERALL_IMPLEMENTATION_DETAILS remains separate and was not mapped
onto the same target member.
