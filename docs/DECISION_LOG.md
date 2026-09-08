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

