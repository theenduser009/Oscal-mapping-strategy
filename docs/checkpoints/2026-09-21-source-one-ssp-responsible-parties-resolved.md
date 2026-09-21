# Source One SSP responsible-party deferred rows resolved — 2026-09-21

## Live evidence used
Owner-provided Snowflake read-only output compared the four historically deferred
SSP Metadata responsible-party fields with already-approved responsible-party fields.

All nine responsible-party fields share:
- Archer FIELD_TYPE_ID = 8
- LEVEL_ID = 353
- MODULE_ID = 547
- SELECT_ID = NULL
- top-level OBJECT payloads when populated
- object key signature: GroupList,UserList
- UserList member key signature: HasDelete,HasRead,HasUpdate,Id

Historically deferred fields observed:
- SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO:
  2,104 populated objects / 709 null
- INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE:
  257 populated objects / 2,556 null
- INFORMATION_SYSTEM_ADMINISTRATOR_ISA:
  257 populated objects / 2,556 null
- AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR:
  65 populated objects / 2,748 null

The shapes match the already-approved responsible-party implementation contract.
No new party/role graph operator or identity logic is required.

## Runtime mapping changes
The four rows were promoted in Mapping/ARCHER_OSCAL_MAPPINGS.csv from DEFERRED
to APPROVED and reuse the existing responsible-party path and direct transform:

- SISSO -> role-id senior-information-systems-security-officer
- ISSE -> role-id information-system-security-engineer
- ISA -> role-id information-system-administrator
- AODR -> role-id authorizing-official-designated-representative

Titles preserve the source role terminology. These are custom OSCAL role IDs;
this checkpoint does not claim they are predefined NIST role identifiers.

## Remaining SSP Metadata exception
ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER produced no observed
shape in the current Source One CURATED_JSON population check. It remains
DEFERRED. No value or property is invented.

## Repository version
- CSV update commit: bee267888577b4fd0a3fa363e4e2b9e93052bb38

## Status distinction
- Mapping metadata updated in GitHub.
- No Snowflake PREVIEW has yet been rerun for these four added SSP roles.
- No DIM/FACT DML was performed by this metadata change.

## Next action
Replace the notebook-visible ARCHER_OSCAL_MAPPINGS.csv with the current GitHub
version, select SSP, rerun Cells 1-3, and run the root RUN_NOW.py verification.
If that passes, run Cells 4-7 in PREVIEW only.
