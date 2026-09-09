# Current Status

Last reconciled: 2026-09-09

## Verified notebook

- Current live Snowflake notebook: `NB_ARCHER_OSCAL_MAPPER_V2`.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Verified mapper checkpoint

```text
Graph nodes: 67683
Graph edges: 64870
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False
```

The metadata completion run is accepted. The governed roles and parties were
materialized, the prior responsible-party identifier error was cleared, every
structural key check passed, and no DIM/FACT write occurred. The durable
[checkpoint](checkpoints/2026-09-09-ssp-graph-67683-64870.md) records the
complete Cell 7 result.

The active production increment is now the existing-registry
`system-characteristics` collection contract. All 101 repository tests pass.

## Minimum-required-scope checkpoint

The previous minimum-contract audit established:

```text
Required paths in minimum contract: 13
Required paths present in registry: 8
Required paths missing from registry: 5
Required paths with mapping owner: 6
Required paths without mapping owner: 7
Records meeting current minimum contract: 0
Result: NOT READY
```

Missing registry branches identified were `import-profile`, `system-information`, `information-types[]`, `control-implementation`, and `implemented-requirements[]`.

## Latest required-source readiness audit — EXECUTED 2026-09-09

The read-only OSCAL SSP 1.2.3 required-source readiness audit was executed successfully in the live Snowflake notebook.

### Safety / identity gates

```text
Session CONFIG OSCAL version: 1.2.3
Cell 7 graph validation passed: True
Cell 7 pre-write validation passed: True
Writes executed: False
Source rows: 2813
Unique source records: 2813
Unique graph records: 2813
Source/graph identity reconciled: True
Source parse errors: 0
Source path resolution errors: 0
```

### Required path action classification

The audit reviewed 13 required paths and classified them as:

```text
ADD_STRUCTURAL_REGISTRY_PATH: 3
DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING: 2
SOURCE_CANDIDATE_COLLISION_REVIEW: 1
STRUCTURE_CARDINALITY_COVERED: 7
```

Key findings:

- `system-security-plan`: registry present, 2813 generated nodes, cardinality valid for all 2813; no artifact rows required for the structural root.
- `metadata`: registry present, artifact rows=5, executable rows=4, skipped rows=1; generated coverage=2813.
- `import-profile`: registry missing, artifact rows=0, executable rows=0, generated nodes=0. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `system-characteristics`: registry present, artifact rows=6, executable rows=6, generated coverage=2813.
- `system-information`: registry missing, no mapping candidates. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `status`: registry present, artifact rows=3, executable rows=2, skipped=1; generated coverage=2813.
- `authorization-boundary`: registry present and generated coverage=2813.
- `system-implementation`: structural cardinality covered for 2813.
- `control-implementation`: registry missing. Action: `ADD_STRUCTURAL_REGISTRY_PATH`.
- `system-ids[]`: registry present; one executable candidate; generated coverage/cardinality valid for all 2813.
- `information-types[]`: registry missing. Action: `DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING`.
- `components[]`: registry present, artifact/executable rows=6, six unique source candidates; generated nodes=4804 but generated record coverage only 944. Candidate records zero=1869. Action: `SOURCE_CANDIDATE_COLLISION_REVIEW`.
- `implemented-requirements[]`: registry missing. Action: `DESIGN_COLLECTION_REGISTRY_AND_INSTANCE_MAPPING`.

Important: collection multiplicity/extra nodes are not being treated as duplicate graph-key defects. Graph duplicate keys remain zero.

### Required payload field action classification

The audit reviewed 18 required payload fields:

```text
ADD_REGISTRY_AND_MAPPING_SOURCE: 4
ADD_REGISTRY_CONFIG_VALUE_REQUIRED: 1
CONFIG_INJECTION_OR_SHAPING_REQUIRED: 1
GENERATED_VALID_FULL_COVERAGE: 3
MAPPING_SOURCE_AND_SHAPING_REQUIRED: 1
MAPPING_SOURCE_REQUIRED: 5
SOURCE_COMPLETENESS_REQUIRED: 3
```

Confirmed full generated coverage:

```text
system-characteristics.system-name: 2813
system-ids[].id: 2813
metadata.last-modified: 2813
```

For `metadata.last-modified`, **2813 means nonblank string/output presence
only**. It does not prove RFC 3339-with-timezone normalization, transformed
value equality, source precedence, or semantic completion. Two artifact rows
converge on that singleton field:
`ARCHER_CONTENT_AUTHORIZATION_PACKAGE_LAST_UPDATED` and `LAST_UPDATED`.
Cell 4 now has a source-preserving timestamp resolver. It keeps one populated
source string unchanged, accepts identical populated candidates, and fails
closed when populated candidates differ instead of allowing mapping order to
overwrite a value. It does not infer a timezone. A live rerun is pending.

Confirmed source-completeness gaps:

```text
system-characteristics.description: candidate zero=33; generated valid=2780
status.state: candidate zero=42; generated valid=2771
authorization-boundary.description: candidate zero=294; generated valid=2519
```

These are source completeness issues, not observed mapper-loss discrepancies.

Metadata/config findings:

- `metadata.title`: no executable mapping source; action `MAPPING_SOURCE_REQUIRED`.
- `metadata.version`: no executable mapping source; action `MAPPING_SOURCE_REQUIRED`.
- `metadata.oscal-version`: controlled config `OSCAL_VERSION` is injected by
  Cell 5; the updated graph ran successfully and the exact aggregate payload
  validation passed for all 2,813 metadata nodes. The durable checkpoint
  records every failure count at zero and no writes.
- `import-profile.href`: registry absent, no mapping source, and no configured profile href; action `ADD_REGISTRY_CONFIG_VALUE_REQUIRED`.

Missing branch/field design findings include:

- `control-implementation.description`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `information-types[].title`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `information-types[].description`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.
- `implemented-requirements[].control-id`: `ADD_REGISTRY_AND_MAPPING_SOURCE`.

Component hydration findings:

```text
components[].type: MAPPING_SOURCE_REQUIRED
components[].title: MAPPING_SOURCE_REQUIRED
components[].description: MAPPING_SOURCE_REQUIRED
components[].status.state: MAPPING_SOURCE_AND_SHAPING_REQUIRED
```

The current component collection remains reference-oriented and needs source/instance design before production OSCAL assembly.

### Composite record-level readiness

The audit reports:

```text
system-security-plan: generated nodes satisfy cardinality/all required fields = 2813
metadata: candidate sources cover all required fields = 0; generated nodes satisfy all required fields = 0
import-profile: 0 / 0
system-characteristics: candidate source completeness=2780; generated valid=2780
system-information: 0 / 0
status: candidate/generated valid=2771
 authorization-boundary: candidate/generated valid=2519
system-implementation: generated structural coverage=2813
control-implementation: 0 / 0
system-ids[]: candidate/generated valid=2813
information-types[]: 0 / 0
components[]: candidate/generated all-required-field coverage=0
implemented-requirements[]: 0 / 0
```

Candidate-source coverage for collections is explicitly record-level evidence only and does not prove that values correlate to the same collection member instance.

### Import-profile decision gate

```text
Registry path present: False
Artifact rows for href: 0
Executable rows for href: 0
Currently owner-aligned rows for href: 0
Candidate records with one populated value: 0
Candidate records with multiple populated values: 0
SSP_IMPORT_PROFILE_HREF configured: False
```

Decision from the audit:

> Provide the approved profile URI for `CONFIG['SSP_IMPORT_PROFILE_HREF']`; no default was invented.

This is a controlled configuration/business-governance input, not something the mapper should fabricate.

### Audit result

```text
RESULT: MAPPING-BACKLOG EVIDENCE ONLY
```

The audit never authorizes writes. Assembled OSCAL JSON schema and constraint validation remain mandatory after the minimum-contract gaps are resolved.

## Latest mapping-artifact progress audit — EXECUTED 2026-09-09

The repository now records the filtered screenshot evidence from
`archer_to_oscal_mapping.xlsx`. The visible filter reports 103 of 609 records
and confirms SSP mappings across metadata, system characteristics, extension
properties, security-impact candidates, responsible parties, components, and
control implementation.

The complete loaded-artifact
[progress audit](checkpoints/2026-09-09_SSP_MAPPING_ARTIFACT_PROGRESS_AUDIT.md)
has now been executed. Its aggregate result is:

```text
Loaded artifact rows: 608
Screenshot-reported rows: 609
Artifact identity/version/provenance reconciled: False
Explicit STATUS column: False
SSP rows retained: 104
Unique SSP row fingerprints: 104
Exact duplicate SSP rows: 0
MORE_INFORMATION_REQUIRED: 80
PRESENCE_RECONCILED: 17
NO_SOURCE_DATA: 5
NOT_APPLICABLE: 2
Artifact rows explicitly marked complete: 0
Global completion claim allowed: False
```

The 608-versus-609 baseline difference remains unresolved. The estimate that
roughly 20 items are complete cannot be treated as a governed project count:
17 rows have output-presence reconciliation, but the artifact declares none
complete and presence is not transformed-value equality.

The user's implementation priority is now explicit:

1. Use the complete Excel Archer-to-OSCAL crosswalk as the daily SSP work
   queue.
2. Preserve each concrete `OSCAL_Element_Path`, mapping type, transformation
   rule, and declared status.
3. Process unresolved mappings root-to-leaf without reworking rows already
   proven complete.
4. Use the pinned OSCAL contract for final conformance and for resolving
   ambiguity, not as a substitute for the mapping artifact.

The audit selected the first implementation-ready root-to-leaf target as:

```text
NEXT ROOT-TO-LEAF TARGET: system-security-plan.metadata.last-modified
NEXT TARGET SELECTION BASIS: IMPLEMENTATION_READY
NEXT TARGET CLASS: MORE_INFORMATION_REQUIRED
NEXT TARGET REASON: TRANSFORM_HANDLER_MISSING
```

The read-only
[metadata last-modified audit](checkpoints/2026-09-09_SSP_METADATA_LAST_MODIFIED_READINESS_AUDIT.md)
was executed. The package-prefixed candidate is empty for all 2,813 records;
`LAST_UPDATED` is populated and is the current generated value for all 2,813.
Every populated value is parseable but timezone-naive. The user chose to keep
that source value unchanged. Cell 4 therefore resolves the source cluster
without normalizing the timestamp or inferring a timezone. This remains a
final OSCAL-conformance gap, but it no longer permits silent mapping-order
overwrite.

The next safe branch change is implemented in the repository: Cell 5 injects
the controlled `CONFIG["OSCAL_VERSION"]` value into the one
`system-security-plan.metadata` payload for each source record. It copies the
payload rather than mutating mapping output, rejects missing configuration,
and fails closed if an existing mapped value conflicts with the configured
version. The authoritative notebook and split Cell 5 are synchronized. This
change has now run successfully in Snowflake.

## Latest mapper rerun — EXECUTED 2026-09-09

The user-provided
[Cell 7 + Cell 8 checkpoint](checkpoints/2026-09-09_CELL7_CELL8_OUTPUT_CHECKPOINT.md)
records the full rerun after replacing Cell 5:

```text
Graph nodes: 51500
Graph edges: 48687
Duplicate node keys: 0
Duplicate edge keys: 0
Dangling source edges: 0
Dangling target edges: 0
PRE-WRITE VALIDATION PASSED
EXECUTE_WRITES = False
```

The unchanged graph cardinality is expected because this patch changes the
metadata payload, not graph topology. Successful Cell 5 execution proves that
the configured-version, conflict, and singleton guards did not fail. The
checkpoint does not print a field-level version count, so exact 2,813-record
payload verification required a separate small check. That check is now
recorded `PASSED`: all 2,813 metadata nodes contain the configured value, every
failure count is zero, and no writes occurred. The repeated Cell 8 timestamp
conclusion is historical audit output; it does not supersede the later user
decision to preserve those timestamps unchanged.

## Locked metadata branch boundary

The Excel artifact defines 15 metadata rows. This is the fixed work slice; do
not restart discovery for each field:

| Target | Rows | Current disposition |
| --- | ---: | --- |
| `metadata.last-modified` | 2 | Source-preserving collision-safe resolver ran successfully; timezone gap retained |
| `metadata.published` | 2 | Same collision-safe resolver ran successfully; no populated-source conflict raised |
| literal `metadata.props` | 1 | `TBD`, source-empty, and not an active collection registry path |
| `metadata.document-ids[].identifier` | 1 | Exact source/output equality passed for 2,813/2,813 records |
| `metadata.responsible-parties[]` | 9 | Five executable assignments now close to generated role and `person` party objects; four `TBD` rows remain excluded |

The pinned contract additionally requires `metadata.title`,
`metadata.version`, and `metadata.oscal-version`. The approved completion rule
now reuses `AUTHORIZATION_PACKAGE_NAME` for the metadata title, sets the SSP
document version to controlled value `1.0`, and retains OSCAL version `1.2.3`.
The source field already generated `system-name` for all 2,813 records in the
accepted baseline, so no fallback title is invented.

## Security-impact production assembly — LIVE RERUN PASSED

The recorded source/runtime evidence separates the optional assembly states:

```text
No populated objective values: 2453
Partial confidentiality/integrity/availability assemblies: 90
Complete confidentiality/integrity/availability assemblies: 270
```

Cell 4 now treats
`system-security-plan.system-characteristics.security-impact-level` as one
atomic optional assembly. It emits the singleton only when all three required
security-objective strings are populated. Empty and partial assemblies are
omitted; the mapper does not invent or default a missing objective.

Cell 5 now recognizes that same path as an optional singleton and does not
recreate an omitted assembly as an empty structural node. Other structural
singleton and collection behavior is unchanged. The split cells and
authoritative notebook are synchronized, and focused tests cover complete,
empty, and partial inputs plus the structural fallback.

The read-only Snowflake rerun passed. Graph nodes and edges each fell by exactly
2,543, which equals the 2,453 empty plus 90 partial assemblies identified by
the earlier aggregate evidence. Duplicate and dangling key counts remained
zero, pre-write validation passed, and no DIM/FACT write occurred. The 270
complete security-impact assemblies remain the expected emitted population.

## Metadata completion release — IMPLEMENTED; REGISTRY RETRY PENDING

The five approved responsible-party source fields already emit role
assignments, but the prior party UUID included the source role field. That
could give one Archer party a different UUID for every role and would prevent
later creation of one reusable OSCAL party object.

Cell 4 now derives party UUIDs from the source system, SSP record, and stable
Archer party identifier without including the role field. The same party in
multiple roles therefore reuses one UUID. Duplicate source references are
removed in source order. Reference objects must expose `Id`, `UserId`, or
`ContentId`; arbitrary dictionaries no longer become identities through JSON
serialization. Missing stable identifiers fail closed with no source values in
the error.

The user approved the five executable source fields as person references.
Cell 4 now emits only referenced role definitions, one reusable `person` party
object per stable party UUID, and one deduplicated assignment per role. Cell 5
uses the party payload UUID as that node's OSCAL UUID and validates, per source
record, that every role ID and every party UUID resolves exactly once. It also
rejects unreferenced role or party objects. The four `TBD` mappings remain
excluded.

The registry remains authoritative. Cell 5 requires active
`system-security-plan.metadata.roles[]`,
`system-security-plan.metadata.parties[]`, and the existing
`system-security-plan.metadata.responsible-parties[]` rows, all parented to
metadata. The guarded setup cell derives unused process orders from the live
SSP registry, inserts only missing role/party paths, and verifies them. It is
read-only by default and never updates an existing governed row.

The first controlled registry setup attempt was blocked by Snowflake before
the new rows were inserted because the original merge omitted non-null
`ELEMENT_TYPE`. The next guarded revision also stopped before DML when its
schema preflight proved that `INSTANCE_KEY_RULE` is mandatory. Neither failed
attempt changed the registry.

The live schema and collection snapshot are now recorded. The registry has
nine columns, and the observed collection vocabulary includes
`SOURCE_FIELD_NAME`, `VALUE`, `SOURCE_FIELD_NAME+ID`, `SOURCE_FIELD_NAME+VALUE`,
and `CONTENT_ID`. Metadata collection rows use process order 3; process order
is hierarchy depth, not a globally unique sequence.

The setup now supplies and verifies the complete nine-column contract. Its
new rows reflect the mapper's actual instance identities:

```text
metadata.roles[]:
  ELEMENT_TYPE=roles
  IS_COLLECTION=TRUE
  INSTANCE_KEY_RULE=SOURCE_FIELD_NAME
  PROCESS_ORDER=3 (derived from existing metadata.responsible-parties[])
  ITEM_PATH=$

metadata.parties[]:
  ELEMENT_TYPE=parties
  IS_COLLECTION=TRUE
  INSTANCE_KEY_RULE=ID
  PROCESS_ORDER=3 (derived from existing metadata.responsible-parties[])
  ITEM_PATH=UserList[]
```

Roles are emitted once per approved source field. Party identity is derived
from each user-list member's stable identifier and is deliberately independent
of source field so the same person can be reused across roles. The schema
preflight remains fail-closed for any unrecognized mandatory column.

The live snapshot contained no ID-only party rule. The user explicitly
approved adding `ID` for this collection rather than reusing
`SOURCE_FIELD_NAME+ID`, which would contradict cross-role party reuse.

Do not rerun Cell 7 against either failed setup attempt. Run the latest setup
cell first and require its final verification message.

The subsequent Cell 7 attempt no longer stopped on missing role/party registry
paths; it reached responsible-party parsing and failed with the sanitized
"reference has no stable identifier" guard. The live registry evidence explains
the source shape: responsible-party values use `ITEM_PATH=UserList[]`, while
Cell 4 previously unwrapped other Archer containers but not `UserList`.

Cell 4 and the authoritative notebook now unwrap that exact governed container
before applying the existing stable `Id`, `UserId`, or `ContentId` checks. It
does not accept arbitrary dictionaries, invent an identity, print a source
value, or alter registry/DIM/FACT data. Focused wrapper and full metadata tests
pass, and the complete suite is green.

## Current engineering interpretation

The graph engine is no longer the primary problem. Its structural integrity remains clean. The backlog is now separated into four concrete categories:

1. **Structural registry additions** — `import-profile`, `system-information`, `control-implementation`.
2. **Collection design + instance mapping** — `information-types[]` and `implemented-requirements[]`.
3. **Component collection/source collision + hydration design** — current `components[]` coverage is 944/2813 records and six candidate source mappings need deliberate reconciliation.
4. **Required field sourcing/configuration** — import-profile href, component fields, plus known source-completeness gaps of 33/42/294 records.

The Excel mapping artifact is now the primary sequencing source for that
backlog. The minimum-contract findings remain valid final-completeness gates,
but they do not determine which spreadsheet-defined mapping should be worked
next when an earlier root-to-leaf row is still unresolved.

Do not patch individual records. Do not invent required controlled values. Do not enable writes.

## System-characteristics collection integrity release — IMPLEMENTED

The accepted live registry snapshot already defines the two collection
contracts needed for this increment:

```text
system-characteristics.props[]:
  INSTANCE_KEY_RULE=SOURCE_FIELD_NAME+VALUE
  ITEM_PATH=$

system-characteristics.system-ids[]:
  INSTANCE_KEY_RULE=VALUE
  ITEM_PATH=$
```

Cell 4 now converts every emitted property value to a canonical nonblank
string. Boolean values become lowercase JSON-style strings, finite scalar
values become trimmed strings, and unresolved objects, nested lists, blanks,
or non-finite values fail closed without exposing source values.

Property instance identity now derives from source field plus normalized
value, rather than list position. System-ID identity now derives from its
normalized value, rather than the generic `singleton` key. Identical governed
identities are deduplicated; a conflicting payload for one identity fails
closed. Reordering a multi-value property no longer changes its node identity.

Cell 5 now retains and verifies the live registry collection flag,
`INSTANCE_KEY_RULE`, and `ITEM_PATH` for these two paths before graph
construction. No registry DML is required.

The singleton aggregator no longer lets canonical mapping row order choose a
winner when two populated mappings target the same field. Identical
transformed values are accepted; distinct values fail closed with a sanitized
error. This applies the policy-free collision rule to the multiple
security-impact candidates without inventing recommended-versus-override
precedence. Security objective text is limited to normalized FIPS values and
the eight reviewed legacy LOE labels.

The known source-owned gaps remain unchanged: 33 records lack a system
description, 42 lack a status state, and 294 lack an authorization-boundary
description. `system-information` and `information-types[]` are not part of
this release because the checked-in evidence has neither governed registry
paths nor source mappings for them.

## Immediate next action

If the current notebook session is still open, replace Cells 4 and 5 from the
repository, run Cell 4, then Cell 5, then Cell 7. Keep mapper
`EXECUTE_WRITES = False`; do not rerun the metadata registry setup. If the
session was closed, run Cells 1 through 7 in order.

Post the complete Cell 7 output. Accept the run only with zero duplicate and
dangling keys, passed pre-write validation, and no writes. Do not assume graph
counts will remain unchanged: repeated identical property values may now
collapse to one governed identity, and any count delta must be explained from
that rule. No standalone validator is required.
