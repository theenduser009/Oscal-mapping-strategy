# Current Status

Last reconciled: 2026-09-09

## Verified notebook

- Current live Snowflake notebook: `NB_ARCHER_OSCAL_MAPPER_V2`.
- Keep `EXECUTE_WRITES = False` while validating.
- Repository conformance target: NIST OSCAL SSP `1.2.3`, pinned in authoritative Cell 1.

## Verified mapper checkpoint

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

Source/graph identity remains exact for 2813 source records.

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
| `metadata.last-modified` | 2 | Source-preserving collision-safe resolver added; live rerun pending; timezone gap retained |
| `metadata.published` | 2 | Same collision-safe resolver added; live source collision outcome pending |
| literal `metadata.props` | 1 | `TBD`, source-empty, and not an active collection registry path |
| `metadata.document-ids[].identifier` | 1 | Exact source/output equality passed for 2,813/2,813 records |
| `metadata.responsible-parties[]` | 9 | Five shape/presence-reconciled, four `TBD`; party/role targets are absent |

The pinned contract additionally requires `metadata.title`,
`metadata.version`, and `metadata.oscal-version`. The first two have no
approved Excel source or controlled value. OSCAL version is the only one that
can be safely closed now. Responsible-party nodes are not semantically
complete merely because their payload shape is valid: neither
`metadata.parties[]` nor `metadata.roles[]` exists to resolve their references.

## Current engineering interpretation

The graph engine is no longer the primary problem. Its structural integrity remains clean. The backlog is now separated into four concrete categories:

1. **Structural registry additions** — `import-profile`, `system-information`, `control-implementation`.
2. **Collection design + instance mapping** — `information-types[]` and `implemented-requirements[]`.
3. **Component collection/source collision + hydration design** — current `components[]` coverage is 944/2813 records and six candidate source mappings need deliberate reconciliation.
4. **Required field sourcing/configuration** — metadata title/version, import-profile href, component fields, plus known source-completeness gaps of 33/42/294 records.

The Excel mapping artifact is now the primary sequencing source for that
backlog. The minimum-contract findings remain valid final-completeness gates,
but they do not determine which spreadsheet-defined mapping should be worked
next when an earlier root-to-leaf row is still unresolved.

Do not patch individual records. Do not invent required controlled values. Do not enable writes.

## Immediate next action

Replace the live notebook's Cell 4 with
[the updated copy-ready cell](../notebooks/cells/04_parsing_transform_payload_helpers.py),
then run Cells 4, 5, 6, and 7 in order. Do not run another standalone
validator for this step. The expected `last-modified` behavior is unchanged;
if populated `published` sources disagree, the production mapper will stop
with a sanitized conflict instead of silently choosing one. Keep
`EXECUTE_WRITES = False` and do not attach a timezone.
