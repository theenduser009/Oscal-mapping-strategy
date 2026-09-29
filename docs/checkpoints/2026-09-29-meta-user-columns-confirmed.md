# Meta User columns confirmed; enrichment precheck published

Date: September 29, 2026
Status: Owner-posted schema result reviewed. New diagnostic SQL committed and repository read-back verified. Enrichment UPDATE not implemented or executed.

## Repository and source evidence

- Branch head inspected before this publication: `simplify-metadata-boundary` at `c3563a82b6ef6d095b0ec1f1b75c250f3c8478f2`.
- Read the actual prior diagnostic: `sql/READ_ONLY_ARCHER_META_LOOKUP_COLUMNS.sql`, blob `9a88a1dafdd30d474946638d095ec636d9795641`.
- New owner evidence: a screenshot of the 35-row Snowflake column-definition result, received September 29. This is result evidence, not merely a screenshot of a query. No private source-record/user values or screenshot are published here.
- New SQL: `sql/READ_ONLY_ARCHER_USER_ENRICHMENT_PRECHECK.sql`.
- SQL publication commit: `af5efc291528900c3cba0f96c17a166aa02ac9d8`.
- Branch read-back blob: `a5490298ac4f3cfa4c96630e2cea74c026a5db63`, matching the locally computed Git blob hash of the intended text.

## Confirmed schema

`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER` is visible in the owner's result with:

| Column | Displayed type | Nullable |
| --- | --- | --- |
| ARCHER_USER_ID | NUMBER | NO |
| EEID | TEXT | YES |
| FIRST_NAME | TEXT | YES |
| LAST_NAME | TEXT | YES |
| MIDDLE_NAME | TEXT | YES |
| INSERT_DATE | TIMESTAMP_NTZ | YES |
| UPDATE_DATE | TIMESTAMP_NTZ | YES |
| CHECKSUM_VALUE | TEXT | YES |

The intended user enrichment now has a verified physical key column and candidate enterprise-ID/name columns. This does not establish that IDs are unique, EEIDs are populated, or source users match lookup rows.

The result also shows ARCHER_META_FIELD, ARCHER_META_VALUE, ARCHER_META_USER_STG, and a separately named mixed-case Archer_Meta_Users object. Continue with ARCHER_META_USER as the intended lookup consistent with the meeting direction; do not silently substitute STG or the mixed-case object. Their presence is not evidence that they are authoritative or current alternatives.

ARCHER_META_FIELD includes FIELD_ID, FIELD_TYPE_ID, LEVEL_ID, MODULE_ID, SQL_FIELD_NAME and SELECT_ID. ARCHER_META_VALUE includes SELECT_ID, SELECT_VALUE_ID and SELECT_VALUE_NAME. Existing select-value handling is not changed by this checkpoint.

No group-metadata object appears in the 35 returned rows. The query covers matching names in ES_ESC_GRC and the current role's visibility only. This does not prove Meta Group is absent elsewhere. Its authoritative table/columns and group semantics remain unverified.

## Supersession and scope

This supersedes the previous statement that the Meta User physical column contract was unavailable. It does not supersede the separate source UserList member-key, lookup-quality, group mapping, party identity, or source-field lineage gaps. No mapping CSV statuses changed.

Owner direction remains: enrich CURATED_JSON in the Matillion/Snowflake workflow, retaining source IDs and arrays, before the downstream OSCAL mapper consumes resolved attributes. No group-to-person conversion, membership expansion, flag interpretation, or UUID rekeying is approved here.

## Immediate precheck

The new file has two read-only SELECT statements:

1. Report Meta User row count, null user IDs, duplicate ARCHER_USER_ID groups, conflicting nonblank EEIDs per ID and missing EEID rows. Do not resolve duplicate matches by arbitrary ROW_NUMBER selection.
2. Show every eligible top-level UserList/GroupList field for one automatically selected source record with a populated user array. ORIGINAL_FIELD_PAYLOAD is the current pre-enrichment CURATED_JSON field object, not a claim of byte-identical RAW_DATA. This reveals the actual member key and permission flags before writing joins. No assumed Id/UserId alias is applied.

The sample identifies the Archer record from RAW_DATA RequestedObject.Id and compares it with the stored CONTENT_ID. It does not substitute Tracking ID or an application field inside FieldContents. Raw arrays containing more than one object are deliberately ineligible for this sample because the existing converter selects only [0]; their ownership needs a separate review. Duplicate eligible source rows are reported, not silently deduplicated. Zero sample rows do not prove a mapping is correct or broken. This is not an exhaustive profile of all fields, nested structures or record shapes.

## Validation actually performed

Visual review of the owner result; current GitHub head and prior SQL read; manual review of the two SELECT statements against the supplied source column/path evidence and official Snowflake FLATTEN/COUNT_IF documentation; local file creation and hash calculation; SQL repository write and complete branch read-back with matching blob hash.

An optional local SQL parser was unavailable. No automated SQL parse, Snowflake compilation/execution, new lookup result, enriched JSON PREVIEW, UPDATE, Matillion run, notebook run, database COMMIT, or database read-back is claimed. Only the preceding schema-discovery result was supplied by the owner.

## Next action and remaining gates

Run both SELECT statements from the published SQL in Dev and return the two grids privately. Inspect the actual populated user member object and resolve lookup quality before authoring the user enrichment UPDATE. Group enrichment stays pending its own contract; preserve group IDs/flags without pretending they are resolved.

Existing non-null CURATED_JSON needs an explicit scoped enrichment plan; do not clear or truncate it. Source Content ID differences require separate impact review before writes. Downstream code must explicitly consume the added attributes; upstream enrichment alone does not make the current party payload display EEID/name or preserve field-level lineage.

Public syntax references: https://docs.snowflake.com/en/sql-reference/functions/flatten and https://docs.snowflake.com/en/sql-reference/functions/count_if.
