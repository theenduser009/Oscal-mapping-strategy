# Source 2 Source RAW binding correction — 2026-09-17

## Repository checkpoint

- Repository: `theenduser009/Oscal-mapping-strategy`
- Branch: `simplify-metadata-boundary`
- SQL correction commit: `443f1f1dac5ee847d48919ae09e341270ee7837f`
- Corrected file: `sql/SOURCE2_SOURCE_READ_ONLY_DISCOVERY.sql`

## Owner clarification

The Source 2 Source mapping input is not the non-RAW/wide table. The physical source is the same Archer content name with `_RAW` appended, and mapped business fields are read from `CURATED_JSON`.

Expected Source-level RAW object:

`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_RAW`

The existing seven-cell design remains aligned with this contract: source identity is expected from a record key such as `CONTENT_ID`, while mapped fields are resolved from `CURATED_JSON`.

## Change made

The previously published discovery SQL was corrected so it no longer searches both wide/non-RAW and RAW candidates. It now:

1. checks the exact expected `_RAW` object in `INFORMATION_SCHEMA.COLUMNS`;
2. performs a small read-only sample of `CONTENT_ID`, `CURATED_JSON` type, `SOURCE_NAME`, and `SOURCE_VERSION` from `CURATED_JSON`;
3. performs no DDL or DML.

## Validation actually performed

- GitHub file update succeeded.
- Post-update GitHub readback verified the corrected SQL text at commit `443f1f1dac5ee847d48919ae09e341270ee7837f`.
- No Snowflake execution has been performed or claimed in this chat.

## Supersession

This checkpoint supersedes the earlier discovery wording that treated matching Authoritative Sources Source objects as candidates and could include the non-RAW/wide object. For Source 2 execution, the mapping source is the `_RAW` table and its `CURATED_JSON` payload unless newer owner evidence explicitly changes that contract.

## Remaining gap

The exact live Snowflake column readback and sample payload shape have not yet been executed here. The GitHub SQL is prepared, not proof that the object currently exists or that the current role can read it.

## Next action

Run `sql/SOURCE2_SOURCE_READ_ONLY_DISCOVERY.sql` in Snowflake and return the two read-only result sets. Then continue the Source -> Catalog Metadata pilot using the RAW `CURATED_JSON` contract.
