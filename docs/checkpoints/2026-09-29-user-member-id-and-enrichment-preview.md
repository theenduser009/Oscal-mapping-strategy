# User member Id confirmed; CURATED_JSON enrichment preview published

Date: September 29, 2026
Status: Enrichment SELECT implemented as a reviewable preview artifact, committed to GitHub, and read back. Not integrated into the Matillion UPDATE, not executed in Snowflake, and not accepted as a database change.

## Repository and actual source reviewed

- Branch: `simplify-metadata-boundary`.
- Pre-change head read: `ca77c8648c74fbc87806c34ecd671797d1755119`.
- Existing precheck read at that SHA: `sql/READ_ONLY_ARCHER_USER_ENRICHMENT_PRECHECK.sql`; blob `a5490298ac4f3cfa4c96630e2cea74c026a5db63`.
- Current downstream helper excerpt read at that SHA: `notebooks/cells/04_parsing_transform_payload_helpers.py`, lines 560-625; blob `57d5aba68504a9bc94230687d20d69b67ed7c75b`. Party payloads still contain uuid/type; assignment payloads contain role-id/party-uuids.
- New SQL: `sql/PREVIEW_ARCHER_CURATED_JSON_USER_ENRICHMENT.sql`.
- Initial publication: `692a041999427ea0d0c2572484012297a2ccd401`.
- Final SQL revision, adding non-array UserList blocking: `53c3cb8cf3252cf4d93804207f80d895bbb5993c`.
- Final SQL blob from complete read-back: `968395ee2f67c4391a510cd58b038a5787502274`, identical to the locally computed Git blob hash of the intended 10,016-byte, 188-line file.

## New owner evidence and supersession

Two new photographs show the requested row-4 user payload and excerpts of the row-5 group payload. The user payload is complete for that one displayed field: GroupList is empty, UserList has an object containing exactly spelled `Id`, `HasDelete`, `HasRead`, and `HasUpdate`. Displayed group members also use `Id` and the same permission-key spellings; the later photo shows the end of GroupList and an empty UserList. The middle of the group payload is not fully supplied, so no complete group-array transcription is inferred.

This resolves the previously missing source member-key question for the displayed examples. The implemented extraction uses `UserList[].Id`, not a guessed UserId or group ID alias. It supersedes the prior request to open these two cells merely to identify the member key. Do not ask for those same examples again as a prerequisite to this preview.

No private screenshots, user IDs, group IDs, Content IDs, EEIDs or person names are committed with this release. Previous owner-posted lookup counts remain dated evidence; they were not rerun here. The earlier global missing-EEID count was off-screen and is still unknown. The new preview measures missing EEIDs for the actual selected source references, without needing an invented global count.

## Proposed JSON contract implemented in the preview

Preserve the original named source field and its GroupList/UserList arrays. Within each valid user member, preserve Id, permission flags, and all other original keys. Add one explicit new child object named `ResolvedUser` containing:

- `ContractVersion`: `archer-meta-user-v1`.
- `LookupStatus`: MATCHED, MATCHED_MISSING_EEID or USER_NOT_FOUND for nonblocking members.
- `EEID`, `FIRST_NAME`, `MIDDLE_NAME`, `LAST_NAME`: values from the singleton matching ARCHER_META_USER row. Preserve missing values as JSON null; do not fabricate identities or substitute the Archer ID for EEID.

These are proposed warehouse-enrichment keys, not existing Archer keys or native OSCAL fields. They remain subject to output review before persistence. The original user Id stays intact. No UUID, DIM key or Content ID is changed.

The physical lookup is `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_USER.ARCHER_USER_ID`, with the EEID and name columns already confirmed in the owner's schema result. Only the exact source `Id` is used; digit-only integer/string forms can be joined numerically while preserving the original JSON representation. Fractional and malformed identities are not rounded into another user's ID.

## Preview behavior and safeguards

One read-only SELECT selects one eligible source record automatically, then builds BEFORE_CURATED_JSON, AFTER_CURATED_JSON, per-field before/after detail, and member-resolution counters. It handles every user array member in source order, including repeated references; there is no DISTINCT collapse and no user-by-group cross product.

The chosen record must have a raw RequestedObject.Id matching stored CONTENT_ID, one physical eligible source row, object CURATED_JSON, and at least one nonempty top-level UserList. Raw objects or single-object arrays are supported for this sample. Multi-object raw arrays, duplicate records, mismatched Content IDs, missing/invalid source roots, and deeper nested access-control paths are not certified by the sample. If no sample qualifies, the result says NO_ELIGIBLE_SOURCE_RECORD; it is not a passed validation.

Duplicate lookup matches, invalid member objects/IDs, a foreign ResolvedUser key, non-array/non-null UserList values, and member-count mismatches block the proposed full document. No arbitrary duplicate winner is selected. Existing ResolvedUser content is refreshed only when it carries this contract's version marker. Blocked field content stays unchanged in FIELD_PREVIEW and AFTER_CURATED_JSON is withheld.

Unmatched users remain present with USER_NOT_FOUND and null lookup attributes. Matched users with blank/null EEID remain present with MATCHED_MISSING_EEID; the record's preview status explicitly reports unresolved users. MATCHED_USERS includes matched rows missing EEID; MISSING_EEID_USERS distinguishes those occurrences. Counts are member occurrences, not necessarily unique people.

GroupList, all its members and flags, and all non-user field values are left structurally unchanged. GROUP_FIELDS_CHANGED should be zero. HasDelete is retained, not interpreted as a deletion instruction. Object key display order may change during reconstruction; byte-for-byte JSON text equality is not claimed.

This SQL does not add Meta Value labels, change the existing field-ID/name converter, approve new OSCAL mappings, expand group membership, or resolve Meta Group. The authoritative Meta Group table and column contract remain unavailable in the supplied evidence. No group name is invented.

## Validation actually performed

- Read both new owner photos through Files and inspected the visible JSON.
- Re-read current GitHub branch and relevant actual code before publication.
- Reviewed official Snowflake OBJECT_INSERT, OBJECT_CONSTRUCT_KEEP_NULL, OBJECT_AGG, AS_OBJECT, ARRAY_AGG and FLATTEN semantics.
- Ran 19 local synthetic Python contract tests covering singleton matches, unchanged IDs/flags, groups, same numeric user/group IDs, mixed arrays, repeated/order preservation, unmatched users, missing EEIDs, duplicate blocking, exact Id/no alias, fractional-ID rejection, null members, key collisions, idempotent same-snapshot output, own-contract refresh, null/empty/missing/unrelated values, invalid array shapes, input immutability, and basic read-only/exact-key SQL text checks.
- These tests exercise a Python model of the proposed output contract, NOT the Snowflake SELECT or the production mapper. They do not prove SQL compilation, query plans or live lookup coverage.
- A SQL parser and Snowflake runtime were unavailable locally. An optional parser-install attempt failed due to network/name-resolution restrictions; no parser pass is claimed.
- Published the SQL, then used SHA-guarded update for the non-array guard; fetched the complete final file and matched its Git blob hash with the intended local bytes.

No Snowflake execution, database PREVIEW result, UPDATE, Matillion run, mapper run, database COMMIT, or database read-back was performed. Repository commits and repository read-back are not database execution evidence.

## Next action

Run only `sql/PREVIEW_ARCHER_CURATED_JSON_USER_ENRICHMENT.sql` in Dev and review the result. Inspect PREVIEW_STATUS and the unresolved/blocking counters, then open FIELD_PREVIEW or AFTER_CURATED_JSON to check ResolvedUser values beside the original Id and flags. Share only the needed result privately.

After that review, integrate the same approved enrichment expressions into the existing Matillion conversion/update with an explicitly scoped plan for already-populated JSON and source-ID exceptions. Do not remove the existing null-only filter or clear CURATED_JSON globally as an unreviewed workaround. The downstream OSCAL party builder and source-field lineage will still need their separately reviewed changes to expose these attributes in DIM/Power BI. Group and select-value enrichment remain coordinated later work, not silently completed by this release.

## Public syntax references

- https://docs.snowflake.com/en/sql-reference/functions/object_insert
- https://docs.snowflake.com/en/sql-reference/functions/object_construct_keep_null
- https://docs.snowflake.com/en/sql-reference/functions/object_agg
- https://docs.snowflake.com/en/sql-reference/functions/as_object
- https://docs.snowflake.com/en/sql-reference/functions/array_agg
- https://docs.snowflake.com/en/sql-reference/functions/flatten
