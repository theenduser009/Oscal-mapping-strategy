# Level-355 package reference proved; joined lookup corrected

Date: September 29, 2026
Status: Owner-posted Snowflake diagnostics accepted; current joined-record source contract corrected in GitHub and read back. No downstream Snowflake target write or COMMIT was performed.

## Owner-posted proof

The AUTHORIZATION_PACKAGE array diagnostic returned:

Result set 1:
- ARRAY_MEMBER_OCCURRENCES = 127,496
- CONTROL_ROWS_WITH_ARRAY_MEMBERS = 127,496
- NULL_MEMBER_OCCURRENCES = 0
- MEMBERS_WITHOUT_EXTRACTABLE_PACKAGE_ID = 0
- DISTINCT_EXTRACTED_PACKAGE_IDS = 1,895
- MIN_MEMBER_INDEX = 0

Result set 2, visible values:
- CONTROL_ROWS_WITH_AUTH_PACKAGE_ARRAY = 127,496
- CONTROL_ROWS_WITH_ONE_ARRAY_MEMBER = 127,496
- CONTROL_ROWS_WITH_MULTIPLE_ARRAY_MEMBERS = 0
- CONTROL_ROWS_WITH_ONE_EXTRACTABLE_PACKAGE_ID = 127,496
- CONTROL_ROWS_WITH_EXACTLY_ONE_PACKAGE_MATCH = 127,496

Result set 3:
- MEMBER_TYPE = INTEGER
- MEMBER_OCCURRENCES = 127,496

This proves the current allocated-controls parent/package reference is the singleton integer member in CURATED_JSON.AUTHORIZATION_PACKAGE[].

Combined with the prior failed-PREVIEW evidence:
- 127,495 obsolete implemented-requirement DIM rows
- 127,495 obsolete FACT rows
- 1,895 affected Authorization Package source records

and the previously verified single Level-355 row without a usable CONTROL_NUMBER, the source shape reconciles:
127,496 package-linked control rows - 1 unusable control row = 127,495 implemented requirements.

## Identity decision retained

Do NOT revert allocated-controls CONTENT_ID.

Current source identity remains:
- Allocated Controls Control CONTENT_ID = its own RequestedObject.Id.

Parent/package lineage is now explicit and separate:
- Allocated Controls Control CURATED_JSON.AUTHORIZATION_PACKAGE[0] -> Authorization Package CONTENT_ID.

This removes the earlier overloaded meaning of CONTENT_ID.

## Code changes

Repository branch baseline before implementation:
- simplify-metadata-boundary at c4269276250399bf1f37aca2f05be8ed95861b56

Updated maintained Cell 1:
- notebooks/cells/01_initialization_and_configuration.py
- commit 9686aaf1018afa218cde1696bd49c31ccfa1b575
- blob 01b10f9ab20a88c227696992f7403aef1770af77
- added join_json_array_field = AUTHORIZATION_PACKAGE to allocated-controls joined lookup contract.

Updated maintained Cell 2:
- notebooks/cells/02_source_mapping_registry_inputs.py
- commit 2dc45c7e7ee0b8f27d44500b0a1c3a5cdd954a49
- blob 7783b5fbcf9038073cc04fb496d2583a63623e64
- joined lookup now derives the parent join identifier from the first member of the configured singleton JSON array, aliases it as CONTENT_ID for the existing Cell 4 interface, filters null parent IDs, and preserves CURATED_JSON.

Cell 4 was intentionally not changed. Its joined-record code still consumes the lookup's CONTENT_ID alias as _JOIN_ID and still uses ALLOCATED_CONTROL_ID for child identity.

Test source updated:
- tests/test_multi_model_inputs.py
- commit 8dbfcfcab9876c133966306b057bfd41d6b4fa63
- blob e02a16f01a03d7f622a920762c124ecfd529632d
- added coverage for a singleton JSON-array parent reference and a null unlinked row.

Generated mirrors synchronized:
- cells_v2 Cell 1 commit 18169b3a893c0cf0e6bebe37b3226dc967f14ae2
- cells_v2 Cell 2 commit 67bebedebc5fee787c141e78da0365f01fb9d49e
- monolithic notebook commit ba870e69e3b39cc9343ebc0bc1f4f57291c9ffe1
- monolithic blob 60f47cf8da51ba4f74718efdcaa8107f5d848ac9

Repository read-back verified the new contract and extraction expression in the maintained cells, generated v2 cells and monolithic notebook.

## Validation boundary

Performed:
- owner-run Snowflake source-shape and package-match diagnostics;
- repository source inspection;
- repository write/read-back and static contract checks.

Not performed:
- local Python unit-test execution;
- fresh Snowflake Cell 2 execution with the corrected code;
- fresh SSP PREVIEW;
- target DML / COMMIT.

## Immediate next action

In the same Snowflake notebook session:
1. replace Cell 1 and Cell 2 with the current GitHub versions;
2. run Cell 1, Cell 2, and Cell 3;
3. keep the existing loaded Cell 4/5/6 functions;
4. run Cell 7 with PREVIEW.

Expected Level-355 behavior is 127,495 implemented-requirement children across 1,895 package records, with the one previously identified unusable-control row skipped. Treat actual PREVIEW output as authoritative.
