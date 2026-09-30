# SSP party UUID — tester teaching guide

Date: September 30, 2026

Purpose: explain exactly how an Archer responsible-party user becomes an OSCAL party UUID and how that UUID resolves back to a person name in the current SSP graph.

Companion SQL:
sql/qa/SSP_PARTY_UUID_END_TO_END_TESTER_WALKTHROUGH.sql

## The whole flow in one picture

Archer Authorization Package
  -> INFORMATION_OWNER_IO
  -> UserList[]
  -> UserList[].Id                       [source identity]
  -> ARCHER_META_USER.ARCHER_USER_ID    [descriptive lookup]
  -> ResolvedUser                       [name/EEID/status enrichment]
  -> deterministic UUID5                [OSCAL party identity]
  -> metadata.parties[].uuid
  -> metadata.responsible-parties[].party-uuids[]
  -> party name

## Step 1 — the identity starts with Archer UserList[].Id

For responsible-party mappings, the mapper extracts a stable identifier from each member:
- Id, else
- UserId, else
- ContentId.

For current Archer UserList members, Id is used.

This Id is the identity input. FIRST_NAME, LAST_NAME, EEID and LookupStatus do not create the party identity.

## Step 2 — ResolvedUser is descriptive enrichment

The raw-to-curated Matillion step performs:

UserList[].Id = ARCHER_META_USER.ARCHER_USER_ID

When the lookup is valid, it adds ResolvedUser while preserving the original Id and permission flags.

ResolvedUser includes:
- ContractVersion = archer-meta-user-v1
- LookupStatus
- EEID
- FIRST_NAME
- MIDDLE_NAME
- LAST_NAME

MATCHED means the user Id resolved to one Meta User row and EEID was present.

## Step 3 — exact party UUID seed

Current mapper code creates the party UUID with Python UUID5:

uuid.uuid5(
    uuid.NAMESPACE_URL,
    "ARCHER|<SOURCE_RECORD_ID>|party|<ARCHER_USER_ID>"
)

uuid.NAMESPACE_URL is:
6ba7b811-9dad-11d1-80b4-00c04fd430c8

Snowflake UUID_STRING(namespace, name) can independently reproduce the same version-5 UUID.

Important consequence:
The same Archer user on two different Authorization Package Content IDs gets two different party UUIDs because SOURCE_RECORD_ID is part of the seed. Party identity is document/source-record scoped in this implementation.

## Step 4 — roles, parties and assignments are built together

The INFORMATION_OWNER_IO mapping row declares:
- role-id = information-owner
- role title = Information Owner

From the same source member set, the mapper creates:

metadata.roles[]
  {"id": "information-owner", "title": "Information Owner"}

metadata.parties[]
  {"uuid": "<party uuid>", "type": "person", "name": "<resolved name>"}

metadata.responsible-parties[]
  {"role-id": "information-owner", "party-uuids": ["<party uuid>"]}

## Step 5 — how the role resolves to the name

The semantic OSCAL join is:

responsible-parties[].party-uuids[]
    =
parties[].uuid

After that match, parties[].name gives the resolved name.

The name came from ResolvedUser, but the UUID came from the original Archer user Id.

## Step 6 — DIM key is not the same thing as party UUID

Each graph node also has a warehouse NODE_KEY / DIM primary key.

The node key is deterministic from:
- identity version
- source system
- source table
- source record ID
- OSCAL model
- element path
- instance key

FACT uses DIM node keys:
- FK_SOURCE_ELEMENT_HASH
- FK_TARGET_ELEMENT_HASH

OSCAL responsible-party references use OSCAL UUIDs:
- responsible-parties.party-uuids
- parties.uuid

Do not join party-uuids to DIM PK hashes.

## Step 7 — what FACT means here

FACT stores containment:
- metadata CONTAINS party
- metadata CONTAINS responsible-party
- metadata CONTAINS role

The semantic role-to-person relationship is not a FACT edge. It is inside the OSCAL payload:

responsible-parties.role-id
+
responsible-parties.party-uuids
    -> parties.uuid

## What the tester should prove

For one Content ID:
1. UserList[].Id exists.
2. It matches ARCHER_META_USER.ARCHER_USER_ID.
3. ResolvedUser lookup status is appropriate.
4. Recomputed UUID5 equals responsible-parties.party-uuids[].
5. The same UUID exists as parties[].uuid.
6. The party node contains the expected resolved name.
7. FACT connects metadata to the party node using DIM keys.

If all seven pass, the responsible-party identity and resolution chain is demonstrated end-to-end.
