# Level-355 current join-key evidence after generic CONTENT_ID correction

Date: September 29, 2026
Status: Owner-posted Snowflake results reviewed. No target DML performed.

## New current-table evidence

From sql/validation/2026-09-29_level355_post_refresh_join_key_diagnostic.sql:

Visible first-result values:
- CONTROL_ROWS = 160,000
- DISTINCT_CONTROL_STORED_CONTENT_IDS = 160,000
- DISTINCT_CONTROL_REQUESTED_OBJECT_IDS = 160,000
- CONTROL_ROWS_CONTENT_ID_EQUALS_REQUESTED_OBJECT_ID = 160,000

Owner reports the remaining package-match measures in that first result are zero except for the base/current-row counts.

Second result:
- AUTHORIZATION_PACKAGE_TYPE = ARRAY for 127,496 rows
- AUTHORIZATION_PACKAGE_TYPE = NULL_VALUE for 32,504 rows

## Interpretation

The current allocated-controls table now uses top-level CONTENT_ID as each allocated-control row's own RequestedObject.Id. Therefore the old package-grain join:
Authorization Package CONTENT_ID = Allocated Controls Control CONTENT_ID
is no longer valid.

This is consistent with the SME-confirmed identity rule that RequestedObject.Id is the record Content ID. The fix should not revert CONTENT_ID to the old overloaded package lineage.

Instead, the SSP joined-record lookup must derive its parent/package join key from the AUTHORIZATION_PACKAGE reference stored inside allocated-controls CURATED_JSON.

The 127,496 populated AUTHORIZATION_PACKAGE arrays are highly significant because:
- prior Level-355 accepted source population was 127,496 rows;
- the failed PREVIEW shows 127,495 obsolete implemented-requirement rows;
- historical validation identified one Level-355 row with no usable CONTROL_NUMBER that is intentionally skipped;
- affected parent/source-record count is 1,895, matching the prior distinct package join population.

This is strong root-cause evidence, but the exact array member shape/package-ID extraction still needs one read-only proof before changing Cell 2/Cell 4.

## Next read-only diagnostic

Published:
- sql/validation/2026-09-29_level355_authorization_package_array_join_diagnostic.sql
- commit: 02daf2111d8cba6dde09e3cffff07d00b2ed085c

It checks:
- AUTHORIZATION_PACKAGE array member count and datatype;
- extractable package IDs;
- exact match coverage to current Authorization Package CONTENT_ID;
- ambiguity/no-match counts;
- distinct matched packages;
- matched rows with/without usable CONTROL_NUMBER.

No raw IDs or payload values are returned.

## Design direction if confirmed

Keep:
- allocated-controls CONTENT_ID = RequestedObject.Id (row identity)

Change:
- joined-record parent linkage to use the package reference from CURATED_JSON:AUTHORIZATION_PACKAGE

Do not overload CONTENT_ID again with package lineage.
