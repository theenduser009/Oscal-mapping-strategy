# Validation 09 live result — source difference triage

Date: **2026-09-16**

Evidence: owner-provided Snowflake notebook screenshots from the existing SSP PREVIEW session.

## Live result

Validator: `09_SSP_SOURCE_DIFFERENCE_TRIAGE`
Validator version: `2026-09-16-r1`
Status: **DIAGNOSTIC_COMPLETE**
Sample source record: `7344415`

Source tables:

- Wide source table: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE`
- Live RAW table: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`

Approved SSP fields: 47
Approved fields present in wide table: 45

Classification counts:

- `MATCH`: 26
- `EXPECTED_NORMALIZATION`: 1
- `COMPLEX_REPRESENTATION_REVIEW`: 9
- `WIDE_VS_RAW_SOURCE_DIFFERENCE`: 9

No `PREVIEW_STALE_OR_RAW_CHANGED` classification was reported in the screenshots. The displayed detail rows consistently showed `FROZEN_VS_LIVE_RAW = MATCH`, meaning the frozen PREVIEW CURATED_JSON and current live RAW CURATED_JSON agree for the inspected discrepancies.

## Consequential finding

The current evidence indicates the remaining direct discrepancies are between the **wide Authorization Package table** and the **RAW/CURATED_JSON representation**, not between frozen preview data and the current RAW row.

This matters because Validation 08 already showed `OSCAL_MAPPING_STATUS = PASS` with no OSCAL failures for record `7344415`. Therefore, this source-layer discrepancy should not be treated as an OSCAL mapper failure.

Examples visible in the screenshots:

- `ACRONYM`: wide `CCS Hardware` vs RAW/CURATED_JSON `CCS Tanium`
- `AUTHORIZATION_PACKAGE_NAME`: wide `RAY_CUI_NetSeg_NATO Seasparrow_PTS_LFA` vs RAW/CURATED_JSON `RAY-CUI-NetSeg-NATO Seasparrow-PTS`
- `FIRST_PUBLISHED`: wide `2024-03-11 14:36:09` vs RAW/CURATED_JSON `2024-03-11 14:36:09.390`
- `LAST_UPDATED`: wide `2026-06-19 13:51:23` vs RAW/CURATED_JSON `2026-06-08 12:50:31.320`
- `MISSION_PURPOSE`: wide `NULL` vs populated RAW/CURATED_JSON HTML/text payload
- `HARDWARE`: wide populated list vs RAW/CURATED_JSON `NULL`

Expected normalization example:

- `ATOIATO_DATE`: wide `2024-09-13 00:00:00` vs RAW/CURATED_JSON `2024-09-13`

Complex representations requiring lookup-aware comparison include fields such as:

- `AUTHORIZING_OFFICIAL_AO`
- `CRITICAL_INFRASTRUCTURE`
- `INFORMATION_CLASSIFICATION`
- `INFORMATION_SYSTEM_OWNER_ISO`
- `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO`
- `INFORMATION_SYSTEM_TYPE`
- `MISSION_CRITICAL`
- `OPERATIONAL_STATUS`

These wide-table values are display labels or text, while RAW/CURATED_JSON stores structures such as `UserList` identities or `ValuesListIds`.

## Interpretation

Confirmed by current evidence:

1. Frozen PREVIEW CURATED_JSON matches the live RAW CURATED_JSON for the inspected record.
2. The remaining direct differences therefore point to **wide-table vs RAW lineage / refresh / normalization semantics**.
3. Validation 08 already established the sampled `CURATED_JSON -> expected OSCAL -> actual OSCAL` mapping path passes.
4. No OSCAL mapper change is justified by this evidence alone.

Not yet confirmed:

- Which upstream representation is authoritative for the nine wide-vs-RAW differences.
- Whether the wide table intentionally applies later enrichment, normalization, display-label resolution, or a different refresh cadence.
- Whether any of the nine discrepancies are genuine upstream data defects.

## Next action

Do not modify OSCAL mappings based on these nine source differences yet.

The next evidence step is to review the wide-table build/lineage or source-owner contract for the nine `WIDE_VS_RAW_SOURCE_DIFFERENCE` fields, beginning with the most material values (`ACRONYM`, `AUTHORIZATION_PACKAGE_NAME`, `LAST_UPDATED`, `MISSION_PURPOSE`, `HARDWARE`).

For complex representation fields, add lookup-aware comparison only if needed; do not compare display labels directly to Archer ID structures.
