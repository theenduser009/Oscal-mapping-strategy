# Decision Log

## 2026-09-08 — Repository reconciliation

- `NB_ARCHER_OSCAL_MAPPER_V1` is the only current mapper notebook.
- The older SSP-specific notebook remains a conceptual reference only and is not copied into this repository.
- Temporary three-cell props diagnostics are retired to avoid conflicting sources.
- GitHub becomes the durable checkpoint for code, current status, architectural context, and future substantive project responses.
- Writes remain disabled until a read-only Snowflake run passes every validation gate.

## Current technical decision

The observed 5,626 rows versus 2,813 distinct source IDs is treated as an upstream source-selection problem until the physical RAW-table count proves otherwise. Cell 2 now permits deterministic deduplication only when an approved technical recency column is present; otherwise it raises an error.

## Next decision required

Review the RAW row count and distinct `CONTENT_ID` count. Then confirm which available technical timestamp or version column is the authoritative tie-breaker for duplicate Archer records.



## 2026-09-08 — Cleanup completed

The main branch now contains one 1,083-line, seven-cell Mapper V1 source plus the authoritative current-status and architecture documents. The notebook passes Python syntax compilation. Snowflake runtime validation remains pending, and `EXECUTE_WRITES` remains `False`.

Removed from the current branch as superseded:

- the three-cell props inspection script;
- the four copy-page files generated from that partial script;
- the older SSP progress file;
- the older response log.

All removed material remains recoverable through Git history. Future substantive project checkpoints are recorded in this decision log.


## 2026-09-08 — Path and payload demonstration query

Added a read-only SQL query that starts from the SSP DIM root, follows parent-child links in the FACT table, reconstructs each structural path, resolves registered array paths, and displays the payload written to each DIM element. It defaults to test content ID `565189` and performs no writes.

Query: [`sql/show_oscal_path_and_payload.sql`](../sql/show_oscal_path_and_payload.sql)


## 2026-09-08 — Demo query registry-column correction

The first path/payload demo query assumed the registry column `OSCAL_ELEMENT_PATH`, which is not present in the connected Snowflake registry schema. The query was corrected to reconstruct `OSCAL_PATH` entirely from DIM nodes and FACT parent-child edges. The registry dependency and invalid identifier were removed; the query remains read-only.


## 2026-09-08 — Empty root payload interpretation

A `system-security-plan` DIM row with `METADATA_JSON = {}` is currently valid. The row is a structural root node, its OSCAL UUID is stored in the separate `OSCAL_UUID` column, and mapped content is stored in descendant nodes such as `metadata`, `system-characteristics`, `system-implementation`, and `control-implementation`.

The root is not required to remain empty forever. It should receive payload only when an approved mapping explicitly targets a root-level OSCAL field; data must not be copied upward merely to make the root JSON non-empty.


## 2026-09-08 — System-characteristics descendant status

The standalone system-characteristics drill-down returns the parent node plus available descendants: `props`, `security-impact-level`, `status`, `system-ids`, and `authorization-boundary`.

Confirmed mapping state:

- FIPS 199 security-impact transformations were implemented and previously validated for confidentiality, integrity, and availability.
- For test SSP `565189`, the security-impact structure existed but its three objective values were null.
- Existing loaded `props` rows contained raw values and were not OSCAL-ready.
- The consolidated Mapper V1 now contains generic extension-property and Archer select-value transformation logic, but its `props` runtime result still requires a read-only Snowflake validation.
- `status.state` semantic lookup and some optional branches remain incomplete.

## 2026-09-08 — Cells 1–3 Snowflake checkpoint

Cells 1 and 2 completed successfully. The RAW source contains 2,813 rows and 2,813 distinct selected records, so the current physical source is already one row per `CONTENT_ID`; Cell 2 did not need to deduplicate it. The mapping artifact contains 608 rows, and 114,471 Archer select values were loaded.

Cell 3 also completed successfully. Snowflake emitted a benign warning because Pandas filtering and sorting retained a non-standard index before `session.create_dataframe`. Cell 3 now calls `reset_index(drop=True)` before that conversion. This changes no mapping data and prevents the warning. Writes remain disabled.

## 2026-09-08 — Cell 7 registry-schema correction

The first read-only Mapper V1 run reached Cell 7 but stopped before graph construction with no registry paths found. The registry itself was not empty; its authoritative schema uses `OSCAL_MODEL_KEY`, `NODE_PATH`, `PARENT_NODE_PATH`, `PROCESS_ORDER`, and `IS_ACTIVE`. Cell 5 had only recognized generic alternative names.

Cell 5 now recognizes the actual Snowflake registry columns, excludes explicitly inactive rows, and sorts by `PROCESS_ORDER`. The correction passes Python syntax validation. No DIM or FACT writes occurred, and `EXECUTE_WRITES` remains `False`.

## 2026-09-08 — Canonical mapping ownership correction

After the registry-schema fix, Cell 7 built and validated a read-only structural graph, reported zero duplicate or dangling keys, passed pre-write validation, and correctly made no DIM/FACT changes. It then failed in the optional coverage helper because Cell 3 had produced an empty mapping list.

The mapping CSV uses inconsistent model labels, while the registry uses the stable model key `SSP`. Cell 3 no longer filters mappings by the CSV display label. It now uses the active registry paths as the authoritative model boundary, assigns every mapping to its deepest active registry owner, derives a target field from the relative OSCAL path when necessary, and fails early if no mapping is owned. A focused local test and Python syntax validation passed. Writes remain disabled.

## 2026-09-08 — Reviewed SSP semantic transformation revision

The controlled-vocabulary review produced the exact runtime labels. The
authoritative notebook and split Cell 4 now implement the following
deterministic rules:

- Normalize recognized FIPS Low values to `low`.
- Preserve reviewed `Legacy LOE A/B/C/D` labels, including `+ DFARS`
  variants, as strings. OSCAL defines each security-objective field as a
  required string when the security-impact object is emitted; no unsupported
  LOE-to-FIPS equivalence is inferred.
- Map `Operational -> operational`, `Under Development ->
  under-development`, and `Decommissioned -> disposition`.
- Map `Reauthorize -> other` and add the OSCAL-required explanatory remark.
- Convert scalar document identifiers to strings.
- Treat `HELPER_PTA_CALC` as transient and do not emit it as an OSCAL prop.
- Fail closed on unknown or multi-valued security/status labels.
- Leave component hydration in Phase 2.

The payload-semantics validator was aligned with these reviewed rules and now
distinguishes invalid shapes from required-field source gaps. Repository
`EXECUTE_WRITES` remains `False`; Snowflake runtime revalidation is pending.

## 2026-09-08 — Provisional OSCAL 1.2.3 cardinality correction

The earlier aggregate of 2,585 empty/incomplete observations is no longer
classified as 2,585 required-field gaps. Under provisional OSCAL SSP 1.2.3,
`security-impact-level` is optional, but all three C/I/A objectives are
required when that assembly is emitted. `status.state` remains required.

The verified counts now mean:

- 2,453 no-objective security nodes represent optional absence for final OSCAL
  emission and are not required-field gaps.
- 90 partial security-impact assemblies contain 91 values and are missing 179
  required objective occurrences.
- 42 records are missing required `status.state`.
- The narrow security/status missing-required-field total is 221 occurrences.
- The exact unique affected-record and source-versus-transform split will be
  measured by the new aggregate-only read-only diagnostic.

This is a validation/interpretation correction, not a production graph change.
The current 17-path mapped subset also does not constitute a complete SSP:
required areas such as `import-profile`, `control-implementation`,
`system-information`, full required metadata/system-characteristics fields,
component hydration, and assembled-document validation remain.

Added
`notebooks/validation/RUN_AFTER_07_ssp_required_field_gap_review.py` and
corrected the payload-semantics validator. The repository still does not pin an
OSCAL version; confirming the target version is required before production
conformance decisions. `EXECUTE_WRITES` remains `False`.
Final validator QA added fail-closed handling for a conflicting pinned OSCAL
version, malformed/non-object payloads, noncanonical status tokens,
missing/duplicate/orphan singleton nodes, source parse/resolution errors, and
source/output coverage mismatches. Optional-omission projections now subtract
only actual empty-node keys and their counted incoming edges. Raw component
references remain an explicit mapped-scope blocker. The cells remain
aggregate-only and read-only.

## 2026-09-08 — OSCAL SSP 1.2.3 target pin and minimum-contract gate

The user confirmed NIST OSCAL SSP 1.2.3 as the repository's conformance
target. Authoritative Mapper V1 Cell 1 and its copy-ready split file now set
`OSCAL_VERSION = "1.2.3"` and display the version at initialization. This pin
does not change the existing deterministic identity policy, registry ownership,
or DIM/FACT graph representation.

The existing security/status cardinality and payload-semantics validators now
identify 1.2.3 as the pinned contract. They tolerate an absent version only in
an already-running notebook session that predates this repository pin, and
they fail closed if a different version is configured.

Added the aggregate-only, read-only
`RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py`. It measures the
minimum required SSP paths, cardinalities, and payload fields derived from the
official OSCAL 1.2.3 SSP, metadata, and implementation-common metaschemas. It
does not expose source identifiers or payloads, does not assemble a final OSCAL
document, and does not replace official JSON schema and constraint validation.

The immediate next step is to run that audit against the existing read-only
Snowflake graph and use the aggregate gaps as the mapping backlog. The 90
partial security-impact assemblies and 42 missing statuses remain
source/business disposition items, while 4,452 raw component references still
require hydration. `EXECUTE_WRITES` remains `False`.

## 2026-09-08 — SSP required-source readiness checkpoint

The minimum-required-scope audit established that all 2,813 source SSPs remain
blocked by required structure or payload gaps. The next action is evidence
collection, not speculative mapper or registry mutation.

Added the read-only
`RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py`. It inspects the
original mapping artifact so target candidates beneath currently missing
registry paths are not hidden by current ancestor ownership. For every
hard-coded minimum-contract path and payload field, it reports separate
aggregate evidence for registry presence, executable candidate rows, populated
source coverage, current canonical ownership, generated validity, and
collection all-member validity.

The diagnostic fails closed on graph/pre-write/write-state failures,
source/graph identity differences, source parsing/resolution errors, and a
conflicting OSCAL version. It distinguishes structural singleton registry work
from source mappings, detects mapping-candidate collisions and exact duplicate
artifact rows, and identifies nested targets such as component `status.state`
that require mapper shaping rather than simple mapping activation. It does not
print record IDs, Archer field names, source values, payloads, hashes, or lookup
labels.

No registry path, mapping, source value, profile URI, graph policy, DIM row, or
FACT row was changed. `EXECUTE_WRITES` remains `False`. The audit result will
determine whether `import-profile.href` has a usable candidate or requires an
approved `SSP_IMPORT_PROFILE_HREF` configuration value.

## 2026-09-09 — Excel-first SSP progress sequencing

The user confirmed that the complete Archer-to-OSCAL Excel crosswalk is the
implementation work queue for finishing SSP root-to-leaf. The pinned NIST OSCAL
1.2.3 contract remains the final conformance and ambiguity-resolution gate; it
does not replace the mappings approved in the workbook or force work to pause
at an external governance dependency when other earlier mappings are ready.

The repository currently contains filtered screenshot evidence, not the Excel
workbook itself. The screenshot UI reports 103 of 609 records, while the live
notebook previously loaded 608 mapping rows. Because this baseline and the
per-row completion statuses are not visible in full, the estimate that roughly
20 mappings are complete is not yet recorded as a verified count.

Added the read-only
`RUN_AFTER_07_ssp_mapping_artifact_progress_audit.py`. It evaluates the entire
Cell 2 mapping artifact, preserves blank-path SSP rows as unresolved conceptual
backlog, separates declared artifact status from derived technical progress,
groups by normalized SSP path, and recommends the first implementation-ready
path in root-to-leaf order, with an unresolved-review fallback. Non-empty
attributable output is classified only as presence reconciliation, not proof
of transformed-value equality or a completed mapping. It prints aggregate
progress by default and never authorizes writes or whole-document conformance.
`EXECUTE_WRITES` remains `False`.

## 2026-09-09 — Build referenced metadata roles; preserve registry authority

The five approved responsible-party mappings already establish controlled role
semantics. Cell 4 now defines an explicit nonblank OSCAL role ID and title for
each one and emits only the distinct roles actually referenced by a source SSP.
TBD mappings and empty source references remain excluded.

The element registry remains authoritative for hierarchy. Cell 5 does not
silently add `metadata.roles[]`; when approved responsible-party mappings are
active and that registry path is missing, it fails with a sanitized registry
error. A present roles path must be parented to metadata. This prevents a
notebook-only hierarchy from drifting away from the governed registry.

The live registry addition and explicit party-type rule remain prerequisites
for full role/party closure. No notebook rerun is requested yet, and
`EXECUTE_WRITES` remains `False`.

## 2026-09-09 — Metadata last-modified evidence gate

The executed Excel-first progress audit selected
`system-security-plan.metadata.last-modified` as the next implementation-ready
path with reason `TRANSFORM_HANDLER_MISSING`. The earlier 2,813 generated count
is output-presence evidence only; it is not timestamp normalization or
transformed-value equality.

Two artifact mappings converge on the singleton field:
`ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` and `LAST_UPDATED`. Cell 4
has no timestamp-specific handler, so both Transform mappings currently reach
the raw-value fallback and mapping order can silently overwrite one candidate.

Added the aggregate-only, read-only
`RUN_AFTER_07_ssp_metadata_last_modified_audit.py`. It fails closed on mapping
baseline or candidate-contract drift, graph/write-state failures, source or
metadata identity problems, malformed payloads, non-singleton metadata nodes,
invalid timestamp shapes, unsafe precision, and invalid policy settings. It
reports candidate coverage, overlap, timezone/format readiness, normalized
equality/conflicts, and current output attribution without printing record IDs,
timestamps, payloads, or other source values.

Do not choose precedence from mapping order, assume a timezone, or select the
maximum timestamp. Run and record the diagnostic before changing Cell 4. The
production mapper remains unchanged and `EXECUTE_WRITES` remains `False`.

## 2026-09-09 — Preserve source timestamps; inject controlled OSCAL version

The metadata last-modified audit was executed and recorded in
`docs/checkpoints/2026-09-09_SSP_METADATA_LAST_MODIFIED_READINESS_AUDIT.md`.
The package-prefixed candidate is empty for all 2,813 records;
`LAST_UPDATED` alone supplies every current generated value. All populated
values are parseable but timezone-naive.

The user chose to retain those timestamp values as they are. Therefore Cell 4
is unchanged: no source precedence, timezone, or normalization rule is
invented. The missing timezone remains a final OSCAL-conformance gap and does
not block the remaining metadata implementation work.

The next safe metadata requirement uses an existing controlled value. Cell 5
now injects `CONFIG["OSCAL_VERSION"]` into every singleton
`system-security-plan.metadata` payload. It requires exactly one singleton,
requires a nonblank configured version, copies the payload, and rejects an
existing conflicting value. Both the authoritative notebook and copy-ready
Cell 5 carry the same change. `EXECUTE_WRITES` remains `False`; Snowflake
runtime validation is still required.

## 2026-09-09 — Controlled OSCAL-version mapper rerun passed

The user replaced Cell 5, reopened the Snowflake session, and ran all seven
mapper cells. The recorded checkpoint reports 51,500 nodes, 48,687 edges,
zero duplicate keys, zero dangling edges, passed pre-write validation, and no
writes. Graph cardinality correctly stayed unchanged because the version is a
payload field.

The run establishes that Cell 5's configured-version, singleton, and conflict
guards completed without error. The checkpoint does not include the exact
count of metadata payloads whose `oscal-version` equals the configured value,
so one aggregate-only validation cell is required before marking this field
runtime-verified. Do not rerun the mapper for that check.

The aggregate OSCAL-version validation is durably recorded `PASSED`: 2,813
metadata nodes exactly match the configured version, every failure count is
zero, and no writes occurred. Work may therefore advance to the next
executable metadata mapping.

## 2026-09-09 — Metadata document-ID exact-value gate

The next executable Excel row is the direct mapping from `TRACKING_ID` to
`system-security-plan.metadata.document-ids[].identifier`. Cell 4 already
implements the required deterministic scalar-to-trimmed-string conversion,
and the existing payload-shape audit reports 2,813 valid nodes. No production
mapper change is justified before checking equality.

Added `RUN_AFTER_07_ssp_metadata_document_id_validation.py`. It is
aggregate-only and read-only. It verifies the exact one-row mapping contract,
source/graph identity, populated-versus-absent source behavior, one attributable
collection node per populated source, singleton instance identity used by the
current builder, exact payload shape, and exact transformed identifier
equality. It prints no identifiers, payloads, or source record IDs and fails
closed on drift or mismatch.

The user then ran the validator. The durable checkpoint records 2,813
populated source identifiers, 2,813 generated document-ID nodes, 2,813 exact
matches, every failure count at zero, and no writes. The document-ID mapping is
closed and does not require another audit.

## 2026-09-09 — Build timestamp collision handling in production Cell 4

Repeated validation is no longer the work queue. The next production change
implements the four Excel-defined metadata timestamp mappings directly.

Cell 4 now routes `published` and `last-modified` through named,
source-preserving transforms and resolves each converging source cluster once.
One populated source is retained exactly. Multiple identical populated values
are accepted. Distinct populated values fail closed with a sanitized conflict
instead of being overwritten by canonical mapping row order. Non-string or
blank populated candidates fail closed. No timezone, normalization, or
precedence rule is invented.

The split Cell 4 and authoritative notebook remain synchronized. The next
runtime step is a normal read-only mapper execution from Cell 4 through Cell 7,
not another standalone diagnostic.

## 2026-09-09 — Make security-impact emission atomic

Existing aggregate evidence found 2,453 SSP records with no populated security
objective, 90 with only part of the confidentiality/integrity/availability
set, and 270 with the complete set. `security-impact-level` is optional as an
assembly, but the three objective fields are required whenever that assembly
is emitted.

Cell 4 now emits the singleton only when all three objectives are populated
nonblank strings. It omits empty and partial assemblies without inventing a
source value or default. Cell 5 excludes this optional path from the generic
empty structural-singleton fallback, so an omission is not recreated as an
empty node. Other structural singleton and collection behavior is unchanged.

The split Cells 4 and 5 and the authoritative notebook are synchronized.
Focused regression coverage verifies complete, empty, one-objective, and
two-objective inputs, reviewed legacy labels, optional-node omission, and
unchanged behavior for other structural paths. The next step is one normal
read-only mapper run from Cell 4 through Cell 7; no standalone validator is
required and `EXECUTE_WRITES` remains `False`.

The live rerun subsequently passed with 48,957 nodes and 46,144 edges, zero
duplicate or dangling keys, passed pre-write validation, and no writes. The
2,543-node and 2,543-edge reduction exactly matches the 2,453 empty plus 90
partial assemblies intentionally omitted. The production decision is accepted;
no additional security-impact validator is required.

## 2026-09-09 — Stabilize responsible-party identity across roles

The five approved responsible-party mappings previously included the source
role field in party UUID identity. That could assign different UUIDs to the
same Archer party when the party held multiple roles, making future
`metadata.parties[]` referential closure impossible.

Cell 4 now bases the UUID on source system, SSP record, and stable party
identifier, independent of role. Repeated references are deduplicated in
source order. Only scalar identifiers or explicit `Id`, `UserId`, and
`ContentId` object identifiers are accepted; arbitrary dictionaries fail
closed instead of being serialized into an identity. No source identifier is
printed in an error.

This release intentionally does not create role or party definition nodes and
does not infer whether a source reference is a person or organization. The
next production increment requires explicit party-type evidence or an approved
rule. No notebook rerun is required for this intermediate identity change, and
`EXECUTE_WRITES` remains `False`.

## 2026-09-09 — Complete the approved SSP metadata mapper branch

The user approved one metadata completion contract: reuse
`AUTHORIZATION_PACKAGE_NAME` as `metadata.title`, set the SSP document version
to controlled value `1.0`, treat the five executable responsible-party fields
as person references, and keep the four workbook rows marked `TBD` excluded.
This does not change the existing system-name mapping or the decision to
preserve source timestamps unchanged.

Cell 4 now builds the required title, deduplicated role definitions, reusable
`person` party objects, and one responsible-party assignment per role. Cell 5
injects both controlled version fields and fails closed unless role IDs and
party UUIDs resolve exactly once within the same source SSP. A party node's
graph OSCAL UUID is exactly the UUID carried in its party payload and referenced
by responsible-party assignments.

The registry remains authoritative. The mapper requires `metadata.roles[]`,
`metadata.parties[]`, and the existing `metadata.responsible-parties[]` under
metadata. A separate setup cell performs read-only preflight by default and,
only when its own registry-write flag is enabled, inserts missing role/party
paths using unused process orders derived from the live SSP registry. It never
updates an existing governed row and verifies the result after the merge.

The split Cells 1, 4, and 5 and the authoritative notebook are synchronized.
All 81 repository tests pass. The release is not yet runtime-accepted: first
run the guarded registry setup, then run Cells 1 through 7 once with mapper
`EXECUTE_WRITES = False`. No separate post-run validator is required.

## 2026-09-09 — Complete the governed registry insert contract from live evidence

The first controlled metadata registry setup attempt was rejected atomically
because the live table requires non-null `ELEMENT_TYPE`, which the original
five-column insert omitted. The next revision's schema guard then stopped
before DML because `INSTANCE_KEY_RULE` is also mandatory. Neither attempt
inserted a row, and mapper writes remained disabled.

The user supplied the complete nine-column schema and all 13 existing
collection rows. That evidence corrected two earlier assumptions: semantic
collection columns must be explicit, and `PROCESS_ORDER` represents hierarchy
depth rather than a globally unique order. Existing metadata collection rows
use order 3.

The final setup contract uses observed registry structure and actual mapper
identities. `metadata.roles[]` uses the existing `SOURCE_FIELD_NAME` rule with
item path `$` because one controlled role is emitted per approved source
field. No existing collection rule represented a party identifier independent
of source field, so the user explicitly approved the new `ID` rule for
`metadata.parties[]` with item path `UserList[]`. That exactly matches reusable
party identity and avoids the existing `SOURCE_FIELD_NAME+ID` behavior, which
would split the same person across roles. Both rows use their leaf element
type, collection true, metadata as parent, the existing metadata collection
order, and active true.

The insert remains merge-only-when-missing, verifies every semantic field, and
never updates existing rows. A Snowflake schema preflight rejects any unknown
non-null/no-default/non-identity column before DML.

## 2026-09-09 — Unwrap the governed responsible-party UserList container

After the registry path issue was cleared, Cell 7 reached Cell 4's party
identity helper and stopped because the responsible-party reference appeared
as a wrapper dictionary rather than a directly identifiable member. The live
registry snapshot already defines the source item path as `UserList[]`; this
was source-shape evidence, not a reason to loosen identity validation.

Cell 4 and the authoritative notebook now unwrap only the exact `UserList`
container before applying the existing `Id`, `UserId`, or `ContentId` member
checks. Arbitrary dictionaries still fail closed. Regression coverage confirms
deduplication inside the wrapper and full role/party closure, and mapper writes
remain disabled.
