# SSP Component Lookup Discovery — 2026-09-10

Source: read-only Snowflake diagnostic screenshots from `NB_ARCHER_OSCAL_MAPPER_V2`.

## Safety / execution

- Aggregate-only diagnostic; no component IDs, source-record IDs, payloads, or source values printed.
- Writes executed: `False`.
- No database objects or rows were changed.

## Component lookup summary

- Component-node occurrences: **4,792**
- Distinct governed component IDs: **1,436**
- ContentId metadata objects profiled: **52**
- Metadata objects that failed safety: **0**
- Objects with governed-ID matches: **5**
- Objects with zero governed-ID matches: **47**
- Distinct IDs matched by any object: **1,436**
- Distinct IDs unmatched by all objects: **0**
- IDs matching more than one object: **1,436**

This proves full governed-ID coverage exists somewhere in the candidate lookup objects, but every governed ID is found in more than one object, so the lookup source is ambiguous without an explicit precedence or union contract.

## Candidate objects observed

### `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_CONTENT`
- Object type: BASE TABLE
- Key column: `CONTENT_ID`
- Total rows: **788,617**
- Nonblank key rows: **788,617**
- Distinct keys: **788,617**
- Duplicate key rows: **0**
- Matched key rows: **1,436**
- Matched distinct component IDs: **1,436**
- Duplicate matched key rows: **0**
- Governed-ID coverage: **100.0%**
- Available source-order columns: NONE
- Likely relational fields: NONE
- Likely top-level `CURATED_JSON` keys: NONE

### `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_CONTENT_STG`
- Object type: BASE TABLE
- Key column: `CONTENT_ID`
- Total rows: **782,255**
- Nonblank key rows: **782,255**
- Distinct keys: **782,255**
- Duplicate key rows: **0**
- Matched key rows: **1,436**
- Matched distinct component IDs: **1,436**
- Duplicate matched key rows: **0**
- Governed-ID coverage: **100.0%**
- Available source-order columns: NONE
- Likely relational fields: NONE
- Likely top-level `CURATED_JSON` keys: NONE

### `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_CONTENT_TMP`
- Object type: BASE TABLE
- Key column: `CONTENT_ID`
- Total rows: **772,684**
- Nonblank key rows: **772,684**
- Distinct keys: **772,684**
- Duplicate key rows: **0**
- Matched key rows: **1,436**
- Matched distinct component IDs: **1,436**
- Duplicate matched key rows: **0**
- Governed-ID coverage: **100.0%**
- Available source-order columns: NONE
- Likely relational fields: NONE
- Likely top-level `CURATED_JSON` keys: NONE

### `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_INTERCONNECTIONS_RAW`
- Object type: BASE TABLE
- Key column: `CONTENT_ID`
- Total rows: **2,140**
- Nonblank key rows: **2,140**
- Distinct keys: **2,140**
- Duplicate key rows: **0**
- Matched key rows: **1,428**
- Matched distinct component IDs: **1,428**
- Duplicate matched key rows: **0**
- Governed-ID coverage: **99.44%**
- Available source-order columns: NONE
- Likely relational fields: NONE
- Likely top-level `CURATED_JSON` keys observed:
  - `DESCRIPTION` as description: key-present IDs **968**, nonblank matched IDs **968**, coverage **67.79%**
  - `THIRD_PARTY_DESCRIPTION` as description: key-present IDs **16**, nonblank matched IDs **16**, coverage **1.12%**
  - `INTERCONNECTION_NAME` as title: key-present IDs **1,428**, nonblank matched IDs **1,428**, coverage **100.0%**
  - `THIRD_PARTY_NAME` as title: key-present IDs **31**, nonblank matched IDs **31**, coverage **2.17%**

### `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_SOFTWARE_RAW`
- Object type: BASE TABLE
- Key column: `CONTENT_ID`
- Total rows: **15,619**
- Nonblank key rows: **15,619**
- Distinct keys: **15,619**
- Duplicate key rows: **0**
- Matched key rows: **7**
- Matched distinct component IDs: **7**
- Duplicate matched key rows: **0**
- Governed-ID coverage: **0.49%**
- Available source-order columns: NONE
- Likely relational fields: NONE
- For the 7 matched IDs, observed top-level keys were fully populated:
  - `DESCRIPTION`
  - `INSTALL_STATUS`
  - `OPERATIONAL_STATUS`
  - `RECORD_STATUS`
  - `SERVICENOW_LIFE_CYCLE_STAGE_STATUS`
  - `BUSINESS_NAME`
  - `SOFTWARE_NAME`

## Discovery conclusion

`RESULT: CROSS-OBJECT LOOKUP AMBIGUITY; EXPLICIT SOURCE PRECEDENCE OR UNION CONTRACT REQUIRED`

No lookup table or lookup field was approved, configured, or written by this discovery cell. The next design decision must therefore be explicit and governed: choose source precedence, or define a deterministic union/deduplication contract. Do **not** infer precedence from table naming, row count, or discovery order.
