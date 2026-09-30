# OSCAL resolution mechanics — plain-English hands-on guide

Date: September 30, 2026
Repository branch: simplify-metadata-boundary

This guide explains two different kinds of "resolution" used by the current mapper. They must not be confused.

## 1. Archer select/value-list resolution

Example source field:

- INTEGRITY_CONTROL_CATEGORY_OVERRIDE

The Archer CURATED_JSON value contains a select identifier such as:

- ValuesListIds[0] = <select id>

The mapper does not store that numeric select ID as the OSCAL business value.

Cell 2 reads:
- RTX_RAW_DEV.ES_ESC_GRC.ARCHER_META_VALUE
- SELECT_VALUE_ID
- SELECT_VALUE_NAME

and builds an in-memory lookup:

SELECT_VALUE_ID -> SELECT_VALUE_NAME

Cell 4 then:
1. extracts the ID from ValuesListIds;
2. resolves it through the lookup;
3. applies the field transform;
4. writes the resolved label/value into the OSCAL payload.

For security objectives:
- low / moderate / high are normalized to lowercase;
- specifically approved legacy labels are preserved as their reviewed labels.

Conceptually:

Archer source
  ValuesListIds = [123]
        |
        v
ARCHER_META_VALUE
  123 -> "some label"
        |
        v
OSCAL field
  resolved business value

## 2. Responsible-party/user resolution

Example source field:

- INFORMATION_OWNER_IO

The Archer source field contains UserList members. A member has an original Archer user identity:

- UserList[].Id

During raw -> CURATED_JSON processing, Matillion resolves:

UserList[].Id
    ->
ARCHER_META_USER.ARCHER_USER_ID

and adds a ResolvedUser object while preserving the original member and Id.

ResolvedUser currently contains:
- ContractVersion
- LookupStatus
- EEID
- FIRST_NAME
- MIDDLE_NAME
- LAST_NAME

Important: ResolvedUser supplies descriptive information. It does NOT replace the original Archer Id as identity.

## 3. How the OSCAL party UUID is created

For a responsible-party user, Cell 4 first extracts a stable identifier:

- Id
- otherwise UserId
- otherwise ContentId

For current UserList members this is the original Archer UserList[].Id.

Party UUID seed:

SOURCE_SYSTEM_NAME
+ SOURCE_RECORD_ID
+ literal "party"
+ Archer user identifier

The code uses deterministic UUID5.

Conceptually:

ARCHER
+ Authorization Package Content ID
+ "party"
+ Archer User Id
        |
        v
deterministic OSCAL party UUID

This means rerunning the same source record/user combination creates the same OSCAL party UUID.

The name does not participate in party identity. A name change does not re-key the party.

## 4. How the party name is created

If ResolvedUser.LookupStatus is MATCHED or MATCHED_MISSING_EEID, the mapper builds:

name = FIRST_NAME + optional MIDDLE_NAME + LAST_NAME

If LookupStatus is USER_NOT_FOUND, the mapper keeps the party identity but does not invent a name.

EEID is currently not emitted as an OSCAL external-id unless an approved ARCHER_EEID_SCHEME URI is configured.

## 5. How role, party, and responsible-party fit together

For INFORMATION_OWNER_IO, the mapping CSV supplies:

- role-id = information-owner
- role title = Information Owner

The mapper creates three related OSCAL collections under metadata:

metadata.roles[]
  id = information-owner

metadata.parties[]
  uuid = deterministic party UUID
  type = person
  name = resolved name

metadata.responsible-parties[]
  role-id = information-owner
  party-uuids = [deterministic party UUID]

The key cross-reference is:

responsible-parties[].party-uuids[]
        ->
parties[].uuid

That is how an Information Owner role resolves to a person name.

## 6. DIM/FACT versus OSCAL cross-reference

The warehouse graph and the OSCAL reference are different relationships.

DIM/FACT containment:
- metadata -> roles
- metadata -> parties
- metadata -> responsible-parties

FACT stores those parent/child containment edges using DIM node keys.

The semantic OSCAL relationship:
- responsible-parties.party-uuids -> parties.uuid

Therefore do not expect a FACT edge directly from a responsible-party row to its party row. The OSCAL UUID reference inside METADATA_JSON is what connects them semantically.

## 7. Warehouse node key versus OSCAL UUID

Every DIM node receives a warehouse node key derived from:

IDENTITY_VERSION
+ SOURCE_SYSTEM_NAME
+ SOURCE_TABLE_NAME
+ SOURCE_RECORD_ID
+ OSCAL_MODEL
+ ELEMENT_PATH
+ INSTANCE_KEY

FACT foreign keys point to these node keys.

For party nodes, the instance key is already the deterministic party UUID, so the party OSCAL_UUID equals that instance key. The DIM node key is still a separate warehouse key.

In short:

Archer user Id
   -> deterministic party UUID      (OSCAL identity)
   -> DIM node key                  (warehouse identity)

responsible-party.party-uuids uses the OSCAL UUID, not the DIM node key.

## 8. Two lookup tables, two different jobs

ARCHER_META_VALUE
- used for select/value-list IDs
- turns numeric select IDs into labels

ARCHER_META_USER
- used for UserList[].Id
- turns Archer user identity into user attributes/name data

These are separate resolution mechanisms.

## 9. Current limitation

UserList is enriched through ARCHER_META_USER.

GroupList is intentionally left unchanged until an authoritative Meta Group source is available. Do not infer group membership or group names from the user lookup.
