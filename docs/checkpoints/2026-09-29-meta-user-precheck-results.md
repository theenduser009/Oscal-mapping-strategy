# Meta User precheck results received

Date: September 29, 2026
Status: Owner-posted read-only result evidence reviewed. No enrichment UPDATE implemented or executed.

## Repository and evidence

Pre-publication branch head verified: `simplify-metadata-boundary` at `0e262a5ed5d0a9a4b19f5606e03ee211d8ddc5c9`.

Read the complete `sql/READ_ONLY_ARCHER_USER_ENRICHMENT_PRECHECK.sql` at that SHA, blob `a5490298ac4f3cfa4c96630e2cea74c026a5db63`. Also read the select-value/reference extraction helpers in `notebooks/cells/04_parsing_transform_payload_helpers.py`, lines 70-125, blob `57d5aba68504a9bc94230687d20d69b67ed7c75b`.

The owner supplied two new result screenshots corresponding to the published precheck. The earlier 35-row lookup-schema result was re-inspected. Screenshots, source Content IDs, member IDs, personal values, and private payloads are not published here. The figures below are aggregate evidence only.

## Accepted visible results

| Check | Visible result |
| --- | ---: |
| LOOKUP_ROWS | 219716 |
| DISTINCT_NON_NULL_ARCHER_IDS | 219716 |
| NULL_ID_ROWS | 0 |
| DUPLICATE_ARCHER_ID_GROUPS | 0 |
| ARCHER_IDS_WITH_CONFLICTING_EEIDS | 0 |

The MISSING_EEID_ROWS result is outside the visible right-hand area of the first screenshot. Its value remains unknown; no zero is inferred. These results establish the posted lookup-key checks, not that every source user matches the lookup, every EEID is populated, or enterprise identities are globally unique.

The second result contains 13 eligible top-level reference fields for one selected source record. SOURCE_CONTENT_ID equals STORED_CONTENT_ID for that record, with CONTENT_ID_CHECK = MATCH and SOURCE_ROWS_FOR_CONTENT_ID = 1. The visible sample includes user-only fields, multiple-user arrays, and group-only fields. One user array contains seven members and another two; two group-only arrays contain twenty and twelve members. This confirms that the enrichment cannot assume one member per field. It does not establish complete source coverage, a mixed user/group field example, or an OSCAL approval for all 13 fields.

The ORIGINAL_FIELD_PAYLOAD cells are truncated in the screenshot. They show UserList/GroupList containers and permission flags, but not the complete user/group member objects or the exact identifier key. Id versus UserId or other spelling must not be chosen from this cropped evidence.

## Lookup scope

- Field ID to SQL field name: present in the owner's existing converter through ARCHER_META_FIELD.SQL_FIELD_NAME. Preserve that behavior while separately reviewing ambiguous field matches.
- User member ID to enterprise identity: ARCHER_META_USER has verified ARCHER_USER_ID, EEID, FIRST_NAME, MIDDLE_NAME and LAST_NAME columns. The posted key checks now support a unique internal-user-key lookup for that run. Exact source member-key extraction and source-to-lookup match coverage still need validation.
- Select-value ID to label: ARCHER_META_VALUE columns SELECT_ID, SELECT_VALUE_ID and SELECT_VALUE_NAME were visible in the earlier schema result. The current OSCAL helper already resolves select values. Adding labels upstream is a coordinated change; do not discard original select IDs or silently double-transform the field.
- Group member ID to group name: source GroupList values are now visible in the bounded sample, but no group lookup definition was returned in the earlier schema result. Source groups existing does not establish a Meta Group table or its join columns. Preserve groups unchanged until the authoritative lookup is supplied or located.
- Content references and attachments remain separate field-specific mappings. User/group enrichment does not approve or resolve them automatically.

## Supersession

This supersedes the prior pending status for the posted Meta User row/key counts and for obtaining a source reference-container sample. Do not rerun those unchanged checks merely to recover their accepted values.

It does not resolve the cropped missing-EEID result, exact member ID keys, lookup match coverage, group lookup, final enriched JSON contract, historical/as-of lookup policy, existing non-null JSON update scope, downstream party enrichment, or field lineage. The one matching source Content ID does not resolve the shared converter's alternative-ID precedence for all records.

## Immediate next action

Use the already-open second result grid. Open ORIGINAL_FIELD_PAYLOAD for the authorizing-official row (row 4) and the group-only row directly below it (row 5), and provide both complete JSON values privately. This needs no new SQL or rerun. Preserve actual property spelling, value types and permission flags; values may be redacted when necessary without changing structure.

Then author a user-enrichment preview using the verified source member key and ARCHER_META_USER. Retain original IDs, arrays, flags and unmatched users. Group-name enrichment remains pending its lookup contract. Do not change UUIDs or existing Content IDs as an incidental effect of this work.

## Changes and validation

Only this documentation checkpoint is added. No SQL, mapping CSV, registry, notebook, Matillion component, CURATED_JSON, DIM or FACT was changed. No new SQL compilation, enrichment preview, UPDATE, database COMMIT or database read-back was performed here. Repository publication/read-back is separate from database execution. Any later runnable SQL must be published and read back in GitHub before asking the owner to run it.
