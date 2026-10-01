# Seven-cell contribution-aware props candidate

Date: 2026-10-01
Branch checked: simplify-metadata-boundary
Base commit checked before editing and before this documentation write: 852d276af5aa30fd8ddac9812e50f8ff992430bc
Status: IMPLEMENTED AND TESTED IN ATTACHED LOCAL CANDIDATE. THIS COMMIT ADDS DOCUMENTATION ONLY. The maintained repository runtime has NOT been replaced by the attached candidate. No Snowflake execution or native production acceptance is claimed.

## Decision retained

Native approved mappings remain native. Approved non-native business information remains in props at its approved owner. Unmapped, TBD, DEFERRED and EXCLUDED fields are not automatically approved or dumped into properties. Needed source attribution also uses props; there is no new lineage table, duplicate mapping CSV row, or per-field lineage switch.

The updated candidate replaces the broad source-presence approach with actual contribution capture. Unique one-to-one source names rely on the matching versioned mapping definitions. Multiple candidate sources and joined-source context receive actual per-record attribution. Consumer access to the mapping version and namespace governance remain explicit release prerequisites.

## What changed in the attached seven cells

1. Configuration: same sources, models, table bindings and safe defaults; matching release label.
2. Inputs: retain actual raw joined-child CONTENT_ID separately from its parent join ID.
3. Compiler: derive ambiguous target signatures and joined-source attribution from existing approved mapping metadata; compute a mapping fingerprint; reject stale release combinations.
4. Transform/assembly: capture only successful assigned contributions and retain them with surviving objects; one shared property constructor. Include previously tested strict mixed-impact cardinality and empty-user-wrapper fixes. No new FIPS/Legacy classification or group resolver.
5. Graph: attach grouped source-field and target-path properties to actual containing instances after native output survives. Joined contributions also identify actual source system/table/child record. An ancestor host for a repeated target requires its existing validated native payload UUID. Missing safe placement produces an explicit lineage gap rather than invented structure.
6. Loader: keep schema, identity, duplicate, obsolete-row, transaction, rollback and readback safeguards; block COMMIT with unresolved lineage gaps.
7. Orchestrator: PREVIEW default; report mapping fingerprint and lineage gaps; prevent every route COMMIT when any preview has a gap; avoid exposing unknown exception payload text.

Matching releases: lean-csv-registry-v5-lineage and oscal-lean-daily-v3.2-lineage.
CONFIG.EXECUTE_WRITES remains False. Cell 7 OSCAL_LOAD_MODE remains PREVIEW.

## Property contract

Related properties use the same namespace and stable group. source-field contains the exact mapped SOURCE_FIELD_NAME, not a guessed Archer display label. target-path uses JSON Pointer relative to the owner, or the separately qualified target-uuid when a repeated target requires an ancestor host. An empty pointer means the complete target object. Joined data adds source-system, source-table and source-record-id.

Groups and new property keys use stable target/rule/source identity, not changing values or timestamps. Current inline observations retain their business property before appended attribution; exporters reordering arrays must recompute pointers. The existing namespace urn:company:oscal:lineage:v1 is a development convention, not proven organizational approval or a NIST-standard ETL vocabulary.

No new production mapping approval, CSV change, registry mutation, automatic deletion, rekey, truncation or href generation is included. Old broad-lineage rows and contributor removal still require controlled reconciliation under the preserved obsolete-row guard.

## Executed local evidence

Reproduced the incoming candidate first: 68 PASS / 5 FAIL / 0 ERROR on its 73 cases and 23 focused tests passing. Verified baseline runtime against the live Git blob hashes before changes.

New candidate:
- 73 updated scenario checks: 73 PASS, 0 FAIL, 0 ERROR.
- 23 first-pass regression tests: PASS.
- 30 additional contribution, instance ownership, lifecycle and safety tests: PASS.
- 126 local checks total; no skipped or expected-failure substitutions.
- Extracted the delivered evidence archive to a separate directory and reran all 126 checks and native parity successfully.
- Native non-lineage payloads, keys and edges match the pinned baseline across five synthetic models and six routes: 384 native nodes and 312 native edges; 12 records per source. Only known lineage and audit fields excluded from this comparison.
- Demonstration database: 648 DIM nodes, 576 FACT edges including grouped lineage; PREVIEW target-empty, insert/readback and unchanged rerun passed locally. This is not a claim of reduced output volume.
- SQLite integrity_check returned ok; 73 result-ledger entries were read back after close/reopen.
- All delivered cell files match the tested copies and manifest hashes; seven cells and combined notebook compile.
- Repository-ready seven-cell patch passed git apply --check and reproduced all seven candidate files in a separate scratch baseline.

### Test contract changes disclosed

The updated ordinary fixture registers the schema-permitted implemented-requirement props path; production registry is unchanged. An independent missing-registration case proves a lineage gap and COMMIT block. Source/target assertions now use group and exact target-path instead of normalized class. The reader checks both property kinds. The removal test removes a genuine optional contributor while a remaining contributor preserves the native value. The misleading outer-field case requires correct child attribution and no outer-value leakage rather than demanding the former parent-ambiguity error. Original test files are retained in the evidence archive. This is not an unchanged run of the original 73-case file.

## Delivered artifacts and integrity

Attached to the OSCAL project conversation:
- OSCAL_Seven_Cells_2026-10-01.zip — seven cells, exact combined notebook, read-only reader, report, manifest and seven-cell patch.
  SHA256: 3ebbadc9bb5d2f9553bcb4fd37d16c71dbc4ccff7466bcbb54562edcb0a06232
- OSCAL_Seven_Cell_Test_Evidence_2026-10-01.zip — code under test, limited local adapter, synthetic fixtures, original evidence, tests, logs and database.
  SHA256: 67088e22d4dab4f80051287eb880fed667c6d4089ab0fcc24ff40b6157c7bb43
- OSCAL_Seven_Cell_Update_Report_2026-10-01.md.

These are attached recreatable artifacts, not a hosted database or a GitHub runtime deployment. No actual Archer record payloads or credentials were used.

## Supersession and remaining gates

This local candidate supersedes the prior broad-lineage/first-pass candidate only for its changed code and tested scenarios. It does not change the truth of historical results on earlier versions or establish any new live acceptance.

Local engine: custom limited Python/SQLite adapter, NOT the official Snowpark SDK or a Snowflake service. The entire maintained repository test suite, full production CSV/current registry, native SQL/grants/VARIANT/timestamps, concurrency/scale and complete OSCAL export conformance have not been validated in this pass.

Next action: review this exact matching seven-cell candidate and run the maintained/native compatibility gates before runtime promotion or a bounded native Dev integration. Preserve current native mapping semantics and load guards. Do not ask for another source-by-source debugging run merely to reproduce the defects now covered locally. Do not label this candidate production-ready from local results alone.
