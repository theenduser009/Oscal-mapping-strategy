# SSP Mapper Business Logic and Tester Guide

Status: tester handoff for the merged partial-component-hydration release  
Target model: NIST OSCAL System Security Plan (SSP) 1.2.3  
Safety state: read-only; `EXECUTE_WRITES = False`

## Start here: the mapper in plain language

The Excel mapping sheet is the team's approved instruction list. Each usable
row says, in effect: "take this Archer field, apply this rule, and place the
result at this OSCAL path." The tester does not need to memorize OSCAL or
decide new mappings. The tester compares what the approved spreadsheet says
with what the mapper actually builds.

The mapper builds a tree rather than one flat table:

- a **node** is one OSCAL location, such as metadata or system status;
- a **payload** is the business data written on that node;
- an **edge** is the parent-child link between two nodes;
- a **primary key** uniquely identifies one node or one edge; and
- a **foreign key** on an edge must point to a real parent and a real child.

Simple example:

| Approved Archer field | Approved OSCAL destination | Expected result |
| --- | --- | --- |
| `AUTHORIZATION_PACKAGE_NAME` | `system-security-plan.metadata.title` | The source package name appears as the metadata title on the correct SSP record. |
| `OPERATIONAL_STATUS` | `system-security-plan.system-characteristics.status.state` | The approved status crosswalk produces the correct OSCAL state. |
| `SOFTWARE` | `system-security-plan.system-implementation.components` | Each referenced software ID creates one component and is hydrated only from the approved software lookup. |

For every test, ask these four questions in order:

1. Did the approved Archer field reach the approved OSCAL path?
2. Is its payload correct after the documented transformation?
3. Is the node connected to the right parent, with unique and valid keys?
4. If the field or branch is not built yet, is it reported honestly as a known
   gap instead of being guessed or silently dropped?

Passing the first three questions proves the implemented mapper scope is built
correctly. It does **not** prove that every field required for a complete OSCAL
SSP exists yet; Section 9 lists those known gaps.

## 1. What the tester is validating

This mapper converts one Archer Authorization Package record into a hierarchy
of OSCAL SSP element nodes and parent-child dependency edges. It does not copy
an Archer JSON object into one OSCAL JSON document. Instead, it:

1. reads the approved Archer source record;
2. reads the Excel/CSV field-to-OSCAL mapping contract;
3. reads the OSCAL element registry for hierarchy and cardinality;
4. applies the approved business transformation for each mapping;
5. creates deterministic element nodes in the DIM-shaped output;
6. creates deterministic parent-child edges in the FACT-shaped output; and
7. validates keys and relationships before any write is possible.

The tester must answer four different questions separately:

1. **Mapping contract:** Does each approved Archer field target the documented
   OSCAL path and transformation?
2. **Payload correctness:** Does the target node contain the expected mapped or
   transformed value?
3. **Graph integrity:** Are node primary keys unique, and do every edge's two
   foreign keys resolve to real nodes in the same generated graph?
4. **OSCAL completeness:** Which required OSCAL branches or fields are still
   missing?

A healthy graph is not automatically a complete OSCAL SSP. This distinction is
important when recording the result.

## 2. Authoritative business inputs

| Input | Business purpose |
| --- | --- |
| `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW` | One source Authorization Package per canonical `CONTENT_ID`; mapped values come from `CURATED_JSON`. |
| `archer_to_oscal_mapping (4).csv` | Approved Archer field, OSCAL model/path, mapping type, transformation notes, and current status. This is the implementation work contract. |
| `OSCAL_ELEMENT_REGISTRY` | Approved SSP hierarchy, parent path, singleton/collection behavior, processing order, and collection instance-key rule. |
| `ARCHER_META_VALUE` | Resolves Archer select-value identifiers to approved labels. |
| `ARCHER_CONTENT_SOFTWARE_RAW` | Approved lookup for referenced software title and description. |
| `ARCHER_CONTENT_INTERCONNECTIONS_RAW` | Approved lookup for referenced interconnection title and populated description. |

Rules of authority:

- `CURATED_JSON` supplies business values; the RAW row supplies lineage.
- Archer `CONTENT_ID` identifies the source SSP record.
- The mapping spreadsheet supplies the approved source-to-target intent.
- The registry supplies the node hierarchy and collection identity rule.
- A model label without an OSCAL element path is not an executable mapping.
- Empty, `TBD`, helper, and unapproved values are not invented or promoted.

## 3. Seven-cell processing flow

| Cell | Responsibility | Tester focus |
| --- | --- | --- |
| 1 | Initializes the Snowflake session, SSP 1.2.3 configuration, identity version, source/target objects, and the write gate. | Confirm model/version and `EXECUTE_WRITES = False`. |
| 2 | Selects one canonical source row per `CONTENT_ID`; loads mapping, registry, Archer labels, and the two approved component lookup sources. | Confirm source uniqueness and exact lookup schemas. |
| 3 | Canonicalizes mapping-column aliases, filters SSP scope, derives each owner path, and groups mappings by registry element. | Confirm mappings are attached to the correct registry owner path. |
| 4 | Parses source values, dispatches Direct/Transform/Reference/Extension behavior, constructs payloads, and builds component hydration lookups. | Confirm business transformations and omission/failure rules. |
| 5 | Traverses the registry root-to-leaf and creates deterministic nodes and containment edges. | Confirm cardinality, instance identity, UUIDs, and parent selection. |
| 6 | Validates graph and target-load keys, verifies all foreign-key references, and performs MERGE only when the write flag is true. | Confirm every validation passes and no DML occurs in this test. |
| 7 | Runs the mapper once and returns `final_nodes_df`, `final_edges_df`, coverage, and the run result. | Preserve the complete output as acceptance evidence. |

## 4. Mapping types and common business rules

| Mapping type | Expected behavior | Required tests |
| --- | --- | --- |
| Direct | Preserve the approved source value, subject to the OSCAL field's scalar/string contract. | Populated value, empty value, wrong type, and conflicting rows targeting one singleton field. |
| Transform | Run the shared approved transformation; never silently fall back to Direct. | Every approved input label, null input, unknown input, and multiple conflicting populated candidates. |
| Reference | Use the referenced member's governed identifier, type, and approved lookup contract. | Object and scalar reference shapes, duplicates, missing IDs, missing lookup rows, and cross-type collision. |
| Extension Property | Emit an OSCAL `prop` with a stable normalized `name` and string `value`. | Scalar, select value, duplicate value, blank/non-finite value, and structured unresolved value. |
| TBD / more information required | Do not emit a business payload. | Confirm the row is reported as backlog/skipped, not silently mapped. |

General rules:

- Empty source values are omitted; required-field absence remains a visible gap.
- Two populated mappings may converge on one singleton field only when their
  transformed values are equal. Different values fail closed.
- Structural singleton nodes may contain `{}`. This represents hierarchy, not
  proof that a complete OSCAL assembly is available.
- Collection identity never uses list position when a governed business key is
  available.

## 5. Implemented SSP business logic

### 5.1 Metadata

| Archer source / rule | OSCAL target | Business behavior |
| --- | --- | --- |
| `AUTHORIZATION_PACKAGE_NAME` | `system-security-plan.metadata.title` | Required nonblank string; no fallback title. |
| `FIRST_PUBLISHED` and package-prefixed published candidate | `metadata.published` | Preserve the selected source string exactly. Equal populated candidates are allowed; different populated values fail. |
| `LAST_UPDATED` and package-prefixed last-updated candidate | `metadata.last-modified` | Preserve the source string exactly. Timezone is not added. Equal populated candidates are allowed; different populated values fail. |
| Controlled configuration | `metadata.version` | Fixed SSP document version `1.0`. |
| Controlled configuration | `metadata.oscal-version` | Exact model version `1.2.3`. |
| `TRACKING_ID` | `metadata.document-ids[].identifier` | One trimmed, nonblank scalar string. Boolean, object, list, blank, and non-finite values fail. |

Five approved responsible-party fields create three linked OSCAL structures:

| Archer field | OSCAL role ID | OSCAL role title |
| --- | --- | --- |
| `INFORMATION_OWNER_IO` | `information-owner` | Information Owner |
| `INFORMATION_SYSTEM_OWNER_ISO` | `system-owner` | Information System Owner |
| `AUTHORIZING_OFFICIAL_AO` | `authorizing-official` | Authorizing Official |
| `INFORMATION_SYSTEM_SECURITY_OFFICER_ISSO` | `system-security-officer` | Information System Security Officer |
| `PRIVACY_OFFICER_PO` | `privacy-officer` | Privacy Officer |

For these fields:

- a stable Archer user identifier becomes a deterministic party UUID within
  the SSP;
- the party type is `person`;
- the same person used in two roles produces one party and two role links;
- duplicate references are removed;
- every role and party must be referenced exactly once or the run fails; and
- four workbook rows still marked `TBD`—ISSE, ISA, AODR, and SISSO—remain
  excluded.

### 5.2 System characteristics

| Archer source / rule | OSCAL target | Business behavior |
| --- | --- | --- |
| `AUTHORIZATION_PACKAGE_NAME` | `system-characteristics.system-name` | Direct approved system name. |
| `ACRONYM` | `system-characteristics.system-name-short` | Direct short name when populated. |
| `MISSION_PURPOSE` | `system-characteristics.description` | Direct description; missing source remains a gap. |
| `SAP_ID` | `system-characteristics.system-ids[].id` | Canonical nonblank string; collection identity is derived from the value. |
| `OPERATIONAL_STATUS` | `system-characteristics.status.state` | Uses the approved status crosswalk below. |
| `AUTHORIZATION_COMMENTS` | status remarks/approved extension behavior | Preserved only through its approved mapping; not used to invent a state. |
| `AUTHORIZATION_BOUNDARY_DESCRIPTION` | `system-characteristics.authorization-boundary` | Direct approved description; missing source remains a gap. |

Approved system-status crosswalk:

| Archer label | OSCAL state |
| --- | --- |
| Operational | `operational` |
| Under Development | `under-development` |
| Decommissioned | `disposition` |
| Reauthorize | `other`, with an explanatory remark |

Unknown or multi-valued status labels fail closed.

Approved Archer-specific attributes mapped as OSCAL properties produce:

```json
{"name": "normalized-source-field", "value": "resolved-string-value"}
```

Archer select IDs are resolved through `ARCHER_META_VALUE`. Property identity
uses source field plus normalized value. Identical properties deduplicate;
conflicting payloads for one identity fail. `PACKAGE_TYPE_HELPER_CALC` is
intentionally excluded by its Notes. **Known discrepancy from clearer Excel
evidence:** the current code also skips `HELPER_PTA_CALC`, but row 35's Notes
require a custom property under system characteristics. That is a pending fix,
not correct exclusion behavior. `PACKAGE_TYPE` also needs its property name
reconciled with the Notes example. See [done and next](SSP_DONE_AND_NEXT.md).

Security impact is an optional assembly with three objectives:

- confidentiality;
- integrity; and
- availability.

Recognized FIPS values normalize to `low`, `moderate`, or `high`. Eight
reviewed legacy LOE labels may remain unchanged strings; no equivalence is
invented. The assembly is emitted only when all three objectives are present.
Zero, one, or two objectives result in omission of the whole optional assembly.

### 5.3 System implementation components

The six Excel reference fields declare these component types:

| Archer reference field | Declared component type | Hydration status |
| --- | --- | --- |
| `SUBSYSTEMS` | `system` | UUID/type only; hydration deferred. |
| `SOFTWARE` | `software` | Hydrated from the approved software lookup. |
| `HARDWARE` | `hardware` | UUID/type only; source not yet proved. |
| `INTERCONNECTIONS` | `interconnection` | Hydrated from the approved interconnection lookup. |
| `INTERCONNECTIONS_CONNECTING_INFORMATION_SYSTEM` | `interconnection` | Hydrated from the approved interconnection lookup. |
| `SAP_INTAKE_FORM_INTERCONNECTIONS` | `interconnection` | Inactive/deferred; it must not hydrate merely because its type matches. |

Reference members may be either an object containing `ContentId,LevelId` or a
scalar content ID. `ContentId` is the governed collection instance key. Source
field and list position are not identity. A repeated content ID with the same
type creates one component per SSP; the same ID assigned different types fails.

Approved partial hydration:

| Type | Lookup | Emitted fields |
| --- | --- | --- |
| Software | `ARCHER_CONTENT_SOFTWARE_RAW`, keyed by `CONTENT_ID` | `uuid`, `type=software`, `title=SOFTWARE_NAME`, `description=DESCRIPTION` |
| Interconnection | `ARCHER_CONTENT_INTERCONNECTIONS_RAW`, keyed by `CONTENT_ID` | `uuid`, `type=interconnection`, `title=INTERCONNECTION_NAME`, and `description=DESCRIPTION` only when populated |

Lookup keys must be nonblank and unique. Every referenced approved-route ID
must match exactly one lookup row. Software title/description and
interconnection title must be nonblank text. A missing interconnection
description is omitted rather than defaulted. Component status is not approved
and must not appear. The current hardware reference remains UUID/type only.

## 6. Node primary-key and edge foreign-key logic

### Node identity / DIM primary key

Every graph node has a deterministic `NODE_KEY`. Its identity includes:

- identity-contract version;
- source system;
- source table;
- source record `CONTENT_ID`;
- OSCAL model;
- full OSCAL element path; and
- singleton or governed collection instance key.

`NODE_KEY` maps to the configured DIM primary-key column. The same input must
produce the same key across reruns. A different SSP record, path, or collection
member must produce a different key.

### Edge identity / FACT primary key

Every parent-child relationship has a deterministic `EDGE_KEY`. It is derived
from the exact parent node, exact child node, and dependency type. `EDGE_KEY`
maps to the configured FACT primary-key column.

### Foreign-key closure

Each FACT-shaped edge contains:

- `FK_SOURCE_ELEMENT_HASH` — must equal one generated node `NODE_KEY`; and
- `FK_TARGET_ELEMENT_HASH` — must equal one generated node `NODE_KEY`.

An edge passes only when both keys resolve. A collection child must link to its
own source record's parent, never a parent from another SSP. If a collection
has multiple possible parents and no unique parent-instance key, the mapper
fails instead of choosing one globally.

## 7. Tester execution procedure

### Preconditions

1. Use the current `main` version of the authoritative notebook or all seven
   synchronized split cells. Do not mix cells from different commits.
2. Start a fresh Snowflake notebook session.
3. Confirm access is read-only for the test and Cell 1 contains
   `EXECUTE_WRITES = False`.
4. Record the Git commit, Snowflake environment, tester, and test date.

### Run

1. Run Cells 1 through 7 once, in numerical order.
2. Do not run the registry setup cell; the required registry paths already
   exist.
3. Do not rerun the old component discovery, source-contract, or routing audit.
4. Save the complete Cell 2 and Cell 7 console output.
5. Save aggregate screenshots/results from the coverage DataFrame and required
   validators. Do not publish business payload values or source identifiers.

### Current-snapshot acceptance values

| Check | Expected result |
| --- | --- |
| RAW source rows | 2,813 |
| RAW distinct source `CONTENT_ID` values | 2,813 |
| Selected source rows | 2,813 |
| Loaded mapping rows | 608 |
| Archer select values | 114,471 |
| Approved component hydration sources | 2 |
| Component hydration lookup rows | 1,435 |
| Software hydration rows | 7 |
| Software descriptions | 7 |
| Interconnection hydration rows | 1,428 |
| Interconnection descriptions | 968 |
| Graph nodes | 67,671 |
| Graph edges | 64,858 |
| Duplicate node keys | 0 |
| Duplicate edge keys | 0 |
| Dangling source edges | 0 |
| Dangling target edges | 0 |
| Pre-write validation | Passed |
| Writes executed | False |

The graph counts should not change because hydration changes payload content,
not node or edge identity. If live source data legitimately changes, the tester
must reconcile the new counts to source changes instead of forcing these old
numbers.

## 8. Required test cases

### A. Source and mapping contract

1. Prove the selected source has exactly one row per source `CONTENT_ID`.
2. Prove required mapping columns resolve unambiguously.
3. Prove all canonical SSP mappings either have an approved OSCAL path or are
   explicitly classified as backlog/skipped.
4. For each executable Excel row, verify its owner node is the nearest
   registered collection/singleton path—not merely the human model label.
5. Verify no blank-path Control Implementation row is assigned a guessed path.

### B. Field-to-node and payload tests

For every executable mapping row:

1. select at least one populated source case and one empty source case;
2. locate the output by the same source record plus expected OSCAL owner path;
3. verify the expected field exists only when the approved source is populated;
4. compare the output to the documented Direct/Transform/Reference/Extension
   business rule;
5. verify an empty source is omitted rather than replaced with a default; and
6. verify no unrelated Archer field appears in the payload.

For transforms, test every approved distinct input label plus one unknown
label. Unknown values must fail clearly and must not be silently preserved.

### C. Primary-key tests

1. `NODE_KEY` is non-null for every node.
2. `NODE_KEY` has zero duplicates.
3. `EDGE_KEY` is non-null for every edge.
4. `EDGE_KEY` has zero duplicates.
5. Rerun the same input and confirm all node and edge keys are identical.
6. Change only the collection member business key in a controlled fixture and
   confirm only that member's node/relationship identity changes.
7. Confirm the target DIM/FACT projections contain their configured PK columns
   and retain zero duplicates/nulls.

### D. Foreign-key and hierarchy tests

1. Left-anti join every `FK_SOURCE_ELEMENT_HASH` to `NODE_KEY`; result must be
   zero.
2. Left-anti join every `FK_TARGET_ELEMENT_HASH` to `NODE_KEY`; result must be
   zero.
3. For sample SSPs, traverse root to metadata, system characteristics, and
   system implementation; every child must have the registry-defined parent.
4. Confirm no edge crosses source-record IDs.
5. Confirm each component belongs to that SSP's single system-implementation
   parent.
6. Confirm role, party, and responsible-party references all close exactly.

### E. Collection identity and deduplication

1. Duplicate system property with the same source/value produces one prop.
2. Duplicate system ID with the same normalized value produces one system ID.
3. Duplicate component `ContentId` with the same type produces one component
   within an SSP.
4. Duplicate component `ContentId` with different types fails closed without
   exposing the identifier.
5. The same person used in multiple roles produces one party UUID and all
   required role assignments.
6. Reversing mapping-row order does not change keys or payloads.

### F. Component hydration

1. Every `SOFTWARE` reference matches exactly one software lookup row.
2. Every active interconnection reference matches exactly one interconnection
   lookup row.
3. Software payload uses only `SOFTWARE_NAME` and `DESCRIPTION`; alternate
   names/status fields do not appear.
4. Interconnection payload uses only `INTERCONNECTION_NAME` and populated
   `DESCRIPTION`; absent description stays absent.
5. Hardware, subsystem, and SAP-only references remain UUID/type only.
6. Lookup duplicate key, missing approved lookup, blank required title, blank
   software description, malformed JSON, and cross-type identity each fail
   before graph construction.
7. Confirm no component payload contains `status` in this release.

### G. Negative and safety tests

1. Set up controlled fixtures for malformed reference, unknown status,
   conflicting singleton values, unresolved select ID, invalid UUID, missing
   parent, duplicate PK, and dangling FK; each must fail closed.
2. Confirm failure messages do not print source payloads or identifiers.
3. Confirm the test run ends with `Writes: False` and reports no DIM/FACT
   changes.
4. Do not enable writes to test a negative case.

### H. Existing automated checks

Run the repository suite in a local clone:

```powershell
python -m unittest discover -s tests
```

Current release expectation: all 156 tests pass. The suite covers metadata,
timestamps, OSCAL version, document ID, responsible-party identity, security
impact, properties/system IDs, component identity, source routing, partial
hydration, graph safety, and notebook/split-cell synchronization.

After Cell 7, run these current read-only validation cells when executing a
formal end-to-end tester cycle:

1. `RUN_AFTER_07_ssp_scope_validation.py`
2. `RUN_AFTER_07_ssp_payload_semantics_validation.py`
3. `RUN_AFTER_07_ssp_v123_minimum_required_scope_audit.py`
4. `RUN_AFTER_07_ssp_v123_required_source_readiness_audit.py`

The first two assess the currently mapped graph and payload semantics. The last
two deliberately report remaining OSCAL-required gaps; they are not expected
to declare the SSP complete yet.

## 9. Known expected gaps—not defects in this release

The tester must record these as backlog unless behavior differs from the rule:

- `import-profile.href` still needs an approved profile URI.
- system information and information-type required branches are incomplete.
- some SSPs have no source system-characteristics description, status state,
  or authorization-boundary description.
- 460 currently referenced interconnections have no populated approved
  description; the field is correctly omitted.
- component status is deferred; hardware and subsystem hydration are deferred.
- many Control Implementation workbook rows have blank OSCAL paths and cannot
  be placed by inference.
- required control-implementation and implemented-requirement structures remain
  incomplete.
- the loaded mapping artifact count/provenance discrepancy remains unresolved.
- one complete SSP JSON document is not yet assembled.
- official OSCAL 1.2.3 JSON schema and constraint validation have not yet been
  run against an assembled document.

Therefore the correct current conclusion is:

> The merged mapper release can pass its approved mapped-scope, transformation,
> identity, graph-integrity, hydration, and no-write tests while the full OSCAL
> SSP remains incomplete.

## 10. Evidence the tester must return

Return one package containing:

1. tested Git commit and environment;
2. Cell 2 source/mapping aggregate output;
3. component hydration aggregate output;
4. complete Cell 7 result;
5. mapping coverage summary by Archer field and OSCAL path;
6. results of the four read-only validators;
7. PK/FK and deterministic-rerun results;
8. negative-test results;
9. known-gap list, separated from actual defects; and
10. final disposition: Pass, Pass with known gaps, or Fail, with each failure
    tied to one business rule or acceptance check in this guide.
