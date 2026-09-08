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
