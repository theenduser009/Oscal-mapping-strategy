# Source 2 Source CURATED_JSON sample evidence — 2026-09-17

Branch reviewed before this update: `simplify-metadata-boundary` at `f2cf9c174d4c3a6a7f8e38d2f146745e349c25db`.

## Evidence supplied

Owner-provided screenshots on 2026-09-17 show a complete-looking sample of the `CURATED_JSON` payload for the Authoritative Sources **Source** level. This evidence is treated as source-shape evidence only; business values and record identifiers are intentionally not copied into this public repository checkpoint.

The owner previously clarified that the runtime source is the RAW table with `_RAW` appended and that mapped business fields come from `CURATED_JSON`. This checkpoint is consistent with that contract.

## Confirmed JSON shapes from the sample

### Plain scalar/text/numeric fields

The sample shows scalar values for fields including:

- `SOURCE_NAME` — string
- `SOURCE_VERSION` — string
- `SOURCE_DESCRIPTION` — string
- `SOURCE_TRACKING_ID` — numeric scalar
- `DATE_CREATED` — timestamp-like string without an explicit timezone suffix in the shown value
- `LAST_UPDATED` — timestamp-like string without an explicit timezone suffix in the shown value
- `NUMBER_OF_CONTROL_STANDARDS_SOURCE_LEVEL` — numeric scalar
- `NUMBER_OF_POLICIES_SOURCE_LEVEL` — numeric scalar
- `COUNT_OF_CONTROLS` — numeric scalar
- `COUNT_OF_NONCOMPLIANT_CONTROLS` — numeric scalar
- `SOURCE_CRITICALITY_VALUE` — numeric scalar
- `RECORD_STATUS` — numeric scalar/code in this sample
- several other fields are explicitly JSON `null` in the sample.

### Archer value-list container fields

The sample shows the Archer object shape

```json
{
  "OtherText": null,
  "ValuesListIds": [ ... ]
}
```

for fields including:

- `AUTH_SOURCES_FILTER`
- `COMPLIANCE_RATING`
- `CONTENT_SOURCE`
- `CRITICALITY`
- `ENGAGEMENT_SCOPE_IN_CONTROL_SOURCE`
- `LINKED_TO_POLICY_SOURCE_LEVEL`
- `SOURCE_TYPE`

This confirms these fields must not be treated as already-resolved text labels in the RAW payload. Any executable mapping that needs business labels must use the existing Archer select-value lookup behavior or another explicitly approved resolution rule.

### Cross-reference array

`TOPIC_REFERENCES` is shown as an array of objects with the shape:

```json
{
  "ContentId": <id>,
  "LevelId": <id>
}
```

This is direct evidence that the Source record carries cross-references to Topic records in the generic Archer `{ContentId, LevelId}` form. It supports later relationship discovery, but does not by itself establish the final Catalog ownership/edge implementation across separate RAW tables.

### Record permissions

`DEFAULT_RECORD_PERMISSIONS` is a structured object containing at least a `GroupList` array with permission flags and identifiers, and a `UserList` collection. This is not plain OSCAL role text. The review-sheet suggestion to map it to `catalog.metadata.role` remains unresolved and should not be promoted to executable metadata from this sample alone.

## Mapping implications

1. `SOURCE_NAME -> catalog.metadata.title` remains a straightforward scalar/text candidate for the first Catalog Metadata pilot.
2. `SOURCE_VERSION -> catalog.metadata.version` remains a straightforward scalar/text candidate for the first pilot.
3. Select-list-backed fields require Archer value-list resolution before deciding their final OSCAL value representation.
4. `TOPIC_REFERENCES` should be treated as cross-reference objects, not scalar text. Its sample shape materially informs Source -> Topic relationship analysis.
5. The sample contains `SOURCE_DESCRIPTION` as narrative text while `INFORMATION` is null in this one record. This does **not** resolve the general `SOURCE_DESCRIPTION` / `INFORMATION` destination question because other records may populate both.
6. `DATE_CREATED` and `LAST_UPDATED` are visible, but the screenshot sample does not establish the semantics or precedence of the review-sheet prefixed publication/update fields, nor does it establish timezone provenance. Existing SME questions remain open.
7. The review-sheet prefixed fields such as `ARCHER_CONTENT_AUTHORITATIVE_SOURCES_SOURCE_FIRST_PUBLISHED`, `...LAST_UPDATED`, `...CONFIRMED_IN_ARCHER`, and `...CONTENT_ID` are not demonstrated as `CURATED_JSON` keys by this sample. Before making them executable, verify whether they are RAW-row columns, wide-table aliases, derived fields, or absent from the JSON contract.

## Superseded / narrowed next step

The previous need to run a query merely to prove that `SOURCE_NAME` and `SOURCE_VERSION` exist in `CURATED_JSON` is superseded by the owner-provided sample. A new Snowflake run should only be requested when it answers a remaining decision, such as broader field coverage, select-value resolution, key provenance, or cross-record relationship validation.

## Implementation status

- Seven-cell code: unchanged.
- Source 1 mappings: unchanged.
- Source 2 review CSVs: unchanged.
- Runtime mapping CSV: unchanged.
- Registry: unchanged/unverified for Catalog in this chat.
- Catalog DDL: unchanged; live execution/read-back still not established here.
- Snowflake writes: none performed by this update.

## Next action

Continue reviewing Source-level mappings that are supported by the confirmed JSON shapes. Promote nothing to runtime until the relevant destination, transform, null policy and identity/registry contract are approved. For the first pilot, `SOURCE_NAME` and `SOURCE_VERSION` remain the cleanest candidates; value-list and cross-reference fields can be reviewed next using this sample evidence without rerunning the seven cells.
