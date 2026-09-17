# Source 2 Source tab mapping review — 2026-09-17

Branch reviewed before this checkpoint: `simplify-metadata-boundary` at `3e77b6d274cf743b2b55cd494e454c09525deb71`.

## Scope

The Source 2 master workbook is being maintained as `archer_authoritative_sources_oscal_mappings.xlsx`, with lowercase workbook and tab names. This checkpoint records the first end-to-end review of tab `sources_source`; the other three tabs remain source transcription/review material and have not yet received equivalent execution review.

The Source tab has 56 Archer-field rows. The review preserves the existing worksheet model/path/Notes evidence and adds mapping-review status, runtime transform, runtime target, decision/next action, source-shape evidence, and reference columns. This is mapping design evidence, not a Snowflake PREVIEW or COMMIT.

## Material findings

- `SOURCE_NAME -> catalog.metadata.title` and `SOURCE_VERSION -> catalog.metadata.version` remain clean direct candidates and are supported by live Source 2 CURATED_JSON read-back.
- `DISCLAIMER`, `SOURCE_TYPE`, `CRITICALITY`, and `CONTENT_SOURCE` are viable Catalog metadata properties using existing supported transforms; the latter three require Archer select-value lookup where source data is a ValuesListIds container.
- `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL`, `COUNT_OF_CONTROLS`, `SOURCE_CRITICALITY_VALUE`, and `AUTH_SOURCES_FILTER` need an explicit generic property-name override because the intended property names differ from the current source-field slug behavior.
- `TOPIC_REFERENCES` was observed as an array of `{ContentId, LevelId}` objects. The previous review path to Back Matter citation is therefore marked `REMAP REQUIRED`; it is relationship evidence, not citation text.
- `LINKED_TO_POLICY_SOURCE_LEVEL` was observed as an Archer value-list container, not a cross-reference; its current Component Definition link proposal is marked `REMAP REQUIRED`.
- `DEFAULT_RECORD_PERMISSIONS` was observed as a structured GroupList/UserList permissions object, not OSCAL role text; its current `catalog.metadata.role` proposal is marked `REMAP REQUIRED`.
- `DATE_CREATED` and `LAST_UPDATED` are retained as source provenance candidates but are not approved as native `catalog.metadata.published` / `last-modified`. NIST metadata semantics describe the OSCAL document instance, not the original source material. The existing timestamp/timezone SME question remains relevant.
- `EFFECTIVE_DATE` and `RTX_RETIREMENT_DATE` remain clean date-property candidates if populated. `OFFICIAL_RETIREMENT_DATE` also needs the generic property-name override (`retirement-date`).
- System metadata rows `INSERT_DATE`, `UPDATE_DATE`, and `CHECKSUM_VALUE` are explicitly marked excluded from OSCAL payload mapping.
- The long prefixed Archer publication/update/confirmation/content-id fields were not demonstrated as CURATED_JSON keys in the supplied sample. Their source location is deferred rather than invented. RAW `CONTENT_ID` is already read-back verified and carried by the warehouse as source record identity.

## NIST reference check

Official OSCAL v1.2.3 Catalog/Metadata references were consulted for the mapping review. In particular, metadata `published` and `last-modified` represent the OSCAL document instance, while properties are the supported extensibility mechanism for additional controlled values. This review does not silently replace owner/SME business decisions with standards interpretation; open business semantics remain deferred.

References:
- https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/catalog/json-reference/
- https://pages.nist.gov/OSCAL/learn/tutorials/general/metadata/

## Implementation status

- Master workbook: updated locally for `sources_source`; GitHub binary publication is a separate repository action.
- Source 2 review CSVs: unchanged.
- Runtime CSV: unchanged by this mapping review.
- Seven-cell mapper: unchanged.
- Catalog registry: owner reported expected pilot setup result (`CATALOG_METADATA_PILOT_REGISTRY_VERIFIED`, 2 active rows); this checkpoint does not independently query Snowflake.
- Snowflake PREVIEW: not performed by this review.
- Snowflake COMMIT/read-back: not performed.

## Next action

Use the reviewed `sources_source` statuses to promote a coherent first Source-level runtime batch rather than the earlier two-row-only pilot. Before execution, add only the registry branches and reusable runtime capabilities required by rows marked ready, keep every deferred/remap row non-executable, and preserve Source 1 regression behavior.