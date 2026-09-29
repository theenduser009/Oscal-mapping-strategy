# STG fallback retired; unmatched-user classification is next

Date: September 29, 2026
Status: Owner clarification incorporated. Read-only classification SQL published and repository read-back verified. No database write or mapper change.

## Owner clarification

The owner clarified that only a small part of the reference payload was shown in earlier screenshots; the screenshots were examples, not an exhaustive source inventory.

The owner also clarified that ARCHER_META_USER_STG is the same user source for this purpose and should not be treated as an independent fallback that can explain the 546 unresolved UserList member occurrences.

This supersedes the prior proposed STG diagnostic as the next action. It does not change the accepted full-source counts or the Meta User lookup contract.

## Current confirmed issue

The whole-source read-only coverage reported 55,782 UserList member occurrences, 55,236 matched user-member occurrences, zero visible missing-EEID members, zero blocking members, and 546 unmatched occurrences. Those 546 occur in CURRENT_ACTOR, RCD_CREATOR, RESPONSIBLE_PARTY and RESPONSIBLE_PARTY_DELEGATE.

The supplied evidence does not establish why those IDs are absent from ARCHER_META_USER. Do not label them deleted users, service/workflow identities, stale references, or another namespace without evidence.

Meta Group remains pending. Group IDs should be preserved unchanged until an authoritative group-ID-to-name table/column contract is supplied or verified.

## New SQL

Published and read-back verified:
- Branch baseline before publication: simplify-metadata-boundary at 2ceef28a7e4cc99779a9bbedb13970d28487a579.
- Path: sql/READ_ONLY_ARCHER_UNMATCHED_USER_CLASSIFICATION.sql
- Publication commit: d46b63939b25a1f711b78d91b956167ac7820e22
- Blob after read-back: 1cb3bbf3fbcaab0faa22364fe846ce6d4cfa31b3

The file contains three read-only result sets:
1. Per-field unresolved occurrence count, distinct unmatched IDs, distinct source records, ID range and permission-pattern count.
2. Per-unmatched-ID repetition count, distinct source records, contributing fields and permission-flag counts. No EEID or names are returned.
3. ARCHER_META_FIELD metadata for the unresolved source fields, including FIELD_ID, FIELD_TYPE_ID, LEVEL_ID, MODULE_ID, FIELD_NAME, SQL_FIELD_NAME and KEY_FIELD. Multiple metadata rows are retained rather than silently selecting one.

## Next action

Run the three SELECT statements in Dev. The key question is whether 546 occurrences represent a very small set of repeated special IDs or a broader population of missing users, and what Archer field types own them.

After that classification, choose one evidence-backed policy:
- resolve through another authoritative Archer identity source if one exists;
- preserve as unresolved source identities with explicit status if they are valid but non-user/system identities;
- or request a source/Archer correction if the references are invalid.

Do not block the already-proved matched-user logic from being designed, but do not silently mark these 546 as matched or substitute their IDs for EEID.

No GitHub result data, private IDs, source records, screenshots or personal names are stored in this checkpoint.
