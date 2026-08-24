# Oscal-mapping-strategy
Oscal loading mechanics 


Yep. Create a file in your repo named:

`AI_WORKING_CONTEXT.md`

Then paste **everything below** into it.

````markdown
# AI Working Context — OSCAL Mapping Strategy

> **Purpose**
>
> This file is the working source of truth for any AI assistant or engineer helping with this project.
>
> **Read this entire file before proposing or modifying code.**
>
> This repository may be public. Do not paste credentials, production data, client-confidential information, private URLs, internal screenshots, secrets, or controlled/proprietary technical data here. Use sanitized examples and placeholders.

---

# 1. Project Goal

We are building a **production-grade, metadata-driven OSCAL transformation engine** using Snowflake and Snowpark/Python.

The source is Archer/GRC data already landed in Snowflake as JSON/VARIANT.

A mapping CSV tells the engine how source fields map into OSCAL paths.

The engine must eventually support multiple OSCAL models using the **same reusable framework**, including:

- System Security Plan (SSP)
- POA&M
- Assessment Plan
- Assessment Results
- Component Definition
- future OSCAL models

The implementation must NOT become:

```text
one notebook per OSCAL model
one Python function per OSCAL element
one hard-coded mapping block per child
````

The primary design principle is:

> **Mappings are metadata. Python/Snowpark provides reusable execution mechanics.**

---

# 2. Desired Architecture

The production flow should look like:

```text
                SOURCE DATA
                     +
                MAPPING CSV
                     |
                     v
          canonical_mapping_df
                     |
                     v
          element_registry_df
                     |
                     v
          GENERIC NODE BUILDER
                     |
                     v
          canonical_nodes_df
                     |
                     v
      GENERIC RELATIONSHIP BUILDER
                     |
                     v
          canonical_edges_df
                     |
             +-------+-------+
             |               |
             v               v
           DIM             FACT
          MERGE            MERGE
```

We want reusable mechanics, not element-specific code.

---

# 3. Source Contract

The source Snowpark dataframe is conceptually:

```text
SOURCE_RECORD_ID
CURATED_JSON
```

`CURATED_JSON` is a Snowflake `VARIANT`.

One source record corresponds to one Archer content/record ID.

Upstream processing already converts Archer-specific Field IDs into readable field names.

Therefore:

> OSCAL mapping should normally work from `CURATED_JSON`, not raw numeric Archer Field IDs.

The source may also contain raw JSON and audit fields, but they are not the normal mapping input.

---

# 4. Mapping CSV Is the Mapping Source of Truth

The mapping CSV already exists and contains the information required to map Archer fields into OSCAL.

Known columns from the current mapping work include fields such as:

```text
Archer_Field_Name
Sparx EA Mapping Completed
NULL%
Data_Type
Cardinality
OSCAL_Model
OSCAL_Element_Path
OSCAL_Data_Type
Mapping_Type
Transformation_Logic
Notes
```

Runtime/enrichment work has also used fields such as:

```text
SOURCE_JSON_PATH
OBSERVED_VALUE_TYPES
```

IMPORTANT:

> Always inspect the actual CSV/dataframe columns before coding.

Do not invent columns because this document mentions a conceptual field.

---

# 5. Mapping Row != DIM Row

This distinction is critical.

A mapping row represents a **field-level mapping instruction**.

Example:

```text
Archer field A
→ system-security-plan.metadata.title

Archer field B
→ system-security-plan.metadata.last-modified

Archer field C
→ system-security-plan.metadata.document-ids[].identifier
```

Those may all contribute to ONE OSCAL node:

```text
ELEMENT_TYPE = metadata
```

Therefore:

```text
3 mapping rows
DO NOT automatically mean
3 DIM rows
```

The generic engine must group mappings by the OSCAL node they belong to.

---

# 6. Canonical Mapping DataFrame

The new notebook should normalize the source CSV into a runtime contract such as:

```text
canonical_mapping_df
```

Conceptual fields may include:

```text
OSCAL_MODEL
SOURCE_FIELD_NAME
SOURCE_JSON_PATH
OSCAL_ELEMENT_PATH
NODE_PATH
FIELD_RELATIVE_PATH
CARDINALITY
OSCAL_DATA_TYPE
MAPPING_TYPE
TRANSFORMATION_LOGIC
IS_ACTIVE
```

Exact fields must be derived from the actual CSV.

Do not modify the CSV simply to satisfy Python code unless that change is explicitly approved.

The CSV remains the business mapping source of truth.

---

# 7. Element Registry

We need a second canonical metadata structure:

```text
element_registry_df
```

This describes the OSCAL hierarchy.

Conceptual fields:

```text
OSCAL_MODEL
NODE_PATH
ELEMENT_TYPE
PARENT_NODE_PATH
ROOT_NODE_PATH
IS_COLLECTION
INSTANCE_KEY_RULE
PROCESS_ORDER
IS_ACTIVE
```

Example for SSP:

| OSCAL_MODEL | NODE_PATH                             | ELEMENT_TYPE           | PARENT_NODE_PATH       | PROCESS_ORDER |
| ----------- | ------------------------------------- | ---------------------- | ---------------------- | ------------: |
| SSP         | `system-security-plan`                | `system-security-plan` | NULL                   |             1 |
| SSP         | `system-security-plan.metadata`       | `metadata`             | `system-security-plan` |             2 |
| SSP         | `system-security-plan.import-profile` | `import-profile`       | `system-security-plan` |             3 |

This hierarchy must drive processing.

---

# 8. Root Handling

The SSP root is:

```text
system-security-plan
```

The root must NOT be special hard-coded Python like:

```python
if model == "SSP":
    create_root()
```

The generic rule should be:

```text
PARENT_NODE_PATH IS NULL
= ROOT NODE
```

For one source record:

```text
SOURCE_RECORD_ID = 565187

system-security-plan
    |
    +-- metadata
    |
    +-- import-profile
```

Root and children should be created by the same metadata-driven engine.

---

# 9. What Went Wrong in the Prototype

The old notebook was useful as a prototype but became too procedural.

The prototype successfully built:

```text
metadata payload
metadata node identity
metadata DIM rows
metadata DIM MERGE
```

It created approximately:

```text
2165 metadata DIM rows
```

But it did NOT create:

```text
system-security-plan root rows
```

before attempting relationships.

So the DIM effectively looked like:

```text
metadata
metadata
metadata
...
2165 times
```

instead of:

```text
system-security-plan
    -> metadata

system-security-plan
    -> metadata

...
```

Then FACT processing failed because there was no SSP root to connect metadata to.

This was a design drift, not a reason to patch more SSP-specific code into the old notebook.

---

# 10. Current DIM State From Prototype

The prototype target DIM is:

```text
DIM_OSCAL_SSP_ELEMENT
```

Observed physical columns include approximately:

```text
PK_OSCAL_SSP_ELEMENT_HASH
ELEMENT_TYPE
OSCAL_UUID
METADATA_JSON
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
SOURCE_RECORD_ID
DW_PIPELINE_RUN_ID
DW_LOAD_TIMESTAMP
DW_LOAD_TIMESTAMP_TZ
```

There was a timestamp-column discrepancy during the prototype.

That issue is intentionally NOT the current priority.

The production refactor should not get distracted by timestamp naming until the core metadata-driven design is stable.

Also note:

`METADATA_JSON` is a misleading generic DIM column name because the DIM eventually contains:

```text
system-security-plan
metadata
import-profile
other OSCAL elements
```

Architecturally a future generic name such as:

```text
ELEMENT_JSON
```

or:

```text
PAYLOAD_JSON
```

would be clearer.

Do not alter the physical DDL without explicit approval.

---

# 11. FACT Model

The existing dependency FACT target contains fields such as:

```text
PK_FACT_OSCAL_DEPENDENCY_HASH
FK_SOURCE_ELEMENT_HASH
FK_TARGET_ELEMENT_HASH
DEPENDENCY_TYPE
SOURCE_OSCAL_UUID
TARGET_OSCAL_UUID
```

The FACT table exists.

However, the prototype did NOT successfully create the correct SSP parent/child FACT rows.

For:

```text
system-security-plan
    -> metadata
```

the relationship should conceptually be:

```text
FK_SOURCE_ELEMENT_HASH = system-security-plan node hash
FK_TARGET_ELEMENT_HASH = metadata node hash
```

The parent and child must belong to the SAME source record.

Never use:

```python
.limit(1)
```

to get one SSP root and relate every metadata row to it.

That would be incorrect.

---

# 12. Generic Relationship Construction

The preferred production design is to first build canonical nodes.

Example:

```text
SOURCE_RECORD_ID
NODE_PATH
PARENT_NODE_PATH
INSTANCE_KEY
ELEMENT_TYPE
NODE_HASH
OSCAL_UUID
ELEMENT_JSON
```

Example data:

```text
565187 | system-security-plan
565187 | system-security-plan.metadata
565187 | system-security-plan.import-profile

565188 | system-security-plan
565188 | system-security-plan.metadata
565188 | system-security-plan.import-profile
```

Then relationships can be generated from the same canonical node set.

Conceptually:

```text
child.SOURCE_RECORD_ID = parent.SOURCE_RECORD_ID

AND

child.PARENT_NODE_PATH = parent.NODE_PATH
```

Then:

```text
parent.NODE_HASH -> child.NODE_HASH
```

becomes the FACT relationship.

For repeated nodes, parent instance context must also be included.

---

# 13. Identity Functions From Prototype

The previous notebook already established reusable deterministic identity helpers.

Known helpers include:

```python
build_node_seed(...)
compute_node_key(...)
compute_node_uuid(...)
compute_edge_key(...)
```

The approved hashing approach uses MD5 deterministically.

Prototype behavior included:

```text
compute_node_key(seed)
    -> MD5 digest
    -> BINARY(16)

compute_node_uuid(seed)
    -> deterministic MD5-derived text
```

DO NOT introduce:

```text
UUID4
random IDs
new hashing algorithms
```

without explicit architecture approval.

---

# 14. Existing Prototype Seed

The prototype node seed used:

```text
SOURCE_SYSTEM
|
SOURCE_TABLE
|
SOURCE_RECORD_ID
|
ELEMENT_TYPE
```

Example:

```text
ARCHER
|
ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW
|
565187
|
metadata
```

That was acceptable for singleton nodes such as:

```text
system-security-plan
metadata
import-profile
```

when only one of each exists per source record.

---

# 15. Important Production Identity Issue

OSCAL contains repeated structures such as:

```text
props[]
links[]
roles[]
parties[]
components[]
resources[]
inventory-items[]
implemented-requirements[]
by-components[]
```

Example:

```text
system-security-plan
    |
    +-- component
    |
    +-- component
    |
    +-- component
```

All three components cannot receive the same identity.

Therefore a production-safe identity needs more context than only:

```text
SOURCE_RECORD_ID + ELEMENT_TYPE
```

Conceptually, the future seed should include:

```text
SOURCE_SYSTEM
|
SOURCE_TABLE
|
SOURCE_RECORD_ID
|
NODE_PATH
|
INSTANCE_KEY
```

IMPORTANT:

> Keep the approved hash algorithm.

But before changing the prototype seed format, the new production identity contract must be explicitly reviewed and approved.

Do not silently change identity behavior.

---

# 16. Instance Key

For singleton nodes:

```text
INSTANCE_KEY
```

may use a deterministic singleton convention.

For repeated nodes, it should use a stable source identifier when possible.

Good example:

```text
component source ContentId
```

Potentially bad example:

```text
array index 0
array index 1
array index 2
```

Array position should not be permanent identity unless source ordering is guaranteed stable.

---

# 17. Canonical Node Contract

Before anything is written to Snowflake, the engine should ideally produce:

```text
canonical_nodes_df
```

Conceptual columns:

```text
SOURCE_RECORD_ID
OSCAL_MODEL
NODE_PATH
PARENT_NODE_PATH
INSTANCE_KEY
PARENT_INSTANCE_KEY
ELEMENT_TYPE
NODE_HASH
OSCAL_UUID
ELEMENT_JSON
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
DW_PIPELINE_RUN_ID
DW_LOAD_TIMESTAMP
```

Exact final fields should align with approved target schemas.

---

# 18. Reusable Functions We Want

The production engine should converge toward a small reusable function set.

Conceptually:

```python
load_source()

load_mapping()

normalize_mapping()

build_element_registry()

resolve_json_path()

build_nested_payload()

build_node_seed()

compute_node_key()

compute_node_uuid()

build_nodes()

build_dependencies()

compute_edge_key()

validate_nodes()

validate_edges()

merge_dim()

merge_fact()
```

We do NOT want a growing collection like:

```python
build_ssp_root()

build_ssp_metadata()

build_ssp_import_profile()

build_poam_root()

build_component()

build_prop()
```

unless a transformation truly requires exceptional handling.

---

# 19. What From the Old Notebook Is Worth Reusing

The prototype had useful work.

## Keep / reuse

### CONFIG

Keep the configuration concept containing explicit values such as:

```text
SOURCE_SYSTEM_NAME
SOURCE_TABLE_NAME
RAW_TABLE
TARGET_DIM
TARGET_FACT
RUN_ID
```

Do not derive target names through string replacement.

---

### Identity helpers

Keep:

```python
build_node_seed()
compute_node_key()
compute_node_uuid()
compute_edge_key()
```

subject to the production instance-identity review described above.

---

### Source loading

Keep the generic creation of:

```text
source_df
```

with:

```text
SOURCE_RECORD_ID
CURATED_JSON
```

---

### JSON discovery utilities

The recursive JSON discovery code was useful.

However, it should become:

```text
debug / profiling utility
```

not something production must execute on every run.

---

### JSON path resolver

Keep the reusable logic that resolves nested source JSON paths.

---

### Nested JSON payload builder

Keep the reusable mechanics that assemble nested OSCAL payloads from mapped paths.

Do NOT keep it metadata-specific.

---

### DIM merge idea

The prototype proved that deterministic keys can support an idempotent DIM merge.

Keep the concept and make it generic.

---

# 20. What Should NOT Be Copied From the Old Notebook

Do not copy these patterns into the new notebook:

```text
metadata-specific DIM builder

hard-coded system-security-plan patch

special Cell 27 root lookup

global root selection

dozens of validation cells

one cell per OSCAL child

one builder per OSCAL node

manual table-name derivation

FACT construction that queries one arbitrary parent
```

---

# 21. Production Notebook Shape

The goal is approximately 6 logical cells.

The exact count can change slightly, but it should stay compact.

---

## Cell 1 — Initialization

Contains:

```text
imports
Snowpark session
CONFIG
stable constants
```

No SSP-specific transformations.

---

## Cell 2 — Inputs

Contains:

```text
load source dataframe
load mapping CSV/dataframe
minimal input validation
```

Expected main objects:

```text
source_df
mapping_df
```

---

## Cell 3 — Canonical Metadata

Contains:

```text
canonical_mapping_df
element_registry_df
```

This is where mapping paths become explicit node hierarchy.

---

## Cell 4 — Reusable Functions

Contains generic reusable functions:

```text
JSON path resolver
nested OSCAL payload assembler
identity functions
node builder
relationship builder
validation functions
merge functions
```

No SSP-only builders.

---

## Cell 5 — Build

Contains a small runner.

Conceptually:

```python
nodes_df = build_nodes(
    source_df,
    canonical_mapping_df,
    element_registry_df,
    config
)

edges_df = build_dependencies(
    nodes_df,
    element_registry_df,
    config
)
```

SSP should be the first validation model.

The engine itself should NOT be SSP-specific.

---

## Cell 6 — Validate and Load

Contains:

```text
compact validation summary

DIM MERGE

FACT MERGE

run summary
```

Construction and validation should occur before writes.

---

# 22. Validation Philosophy

We DO want careful checking.

We DO NOT want 10 separate notebook cells just to validate one dataframe.

Use reusable compact validation.

Example validation output:

```text
SOURCE RECORDS          2165
MAPPING ROWS              42
NODE ROWS               6495
NULL NODE KEYS             0
DUPLICATE NODE KEYS        0
MISSING PARENTS             0
EDGE ROWS                4330
DUPLICATE EDGE KEYS         0
```

Potential checks:

```text
source count

mapping count

unresolved source paths

node count

null node keys

duplicate node keys

null source record IDs

unknown element types

missing parent nodes

duplicate edges

orphan edges
```

Keep the checking discipline.

Centralize the implementation.

---

# 23. Idempotency

Production writes must be idempotent.

Rerunning the same source input with the same deterministic identities should NOT create duplicate rows.

DIM should MERGE based on deterministic node identity.

FACT should MERGE based on deterministic edge identity.

---

# 24. Root + Relationship Example

For:

```text
SOURCE_RECORD_ID = 565187
```

the engine may construct:

```text
NODE 1

NODE_PATH:
system-security-plan

ELEMENT_TYPE:
system-security-plan

PARENT_NODE_PATH:
NULL
```

Then:

```text
NODE 2

NODE_PATH:
system-security-plan.metadata

ELEMENT_TYPE:
metadata

PARENT_NODE_PATH:
system-security-plan
```

Then relationship:

```text
SOURCE:
system-security-plan

TARGET:
metadata
```

FACT:

```text
FK_SOURCE_ELEMENT_HASH
    = root hash

FK_TARGET_ELEMENT_HASH
    = metadata hash
```

For another source record:

```text
565188
```

it gets its own root and metadata pair.

There is never one root shared by every source record.

---

# 25. How Mapping Paths Establish Hierarchy

Example mapping:

```text
system-security-plan.metadata.title
```

We need to determine:

```text
ROOT_NODE_PATH:
system-security-plan

NODE_PATH:
system-security-plan.metadata

ELEMENT_TYPE:
metadata

PARENT_NODE_PATH:
system-security-plan

FIELD_RELATIVE_PATH:
title
```

Another:

```text
system-security-plan.metadata.document-ids[].identifier
```

may produce:

```text
NODE_PATH:
system-security-plan.metadata

FIELD_RELATIVE_PATH:
document-ids[].identifier
```

The `document-ids[]` array is part of the metadata payload unless we intentionally model it as a separate DIM node.

This is an important modeling decision:

> Not every nested OSCAL JSON object must automatically become a DIM node.

The element registry determines which paths become DIM nodes.

---

# 26. Arrays and Nested Structures

The engine must distinguish:

```text
ARRAY AS PART OF PAYLOAD
```

versus:

```text
ARRAY THAT PRODUCES REPEATED DIM NODES
```

Example:

```text
metadata.document-ids[]
```

may remain inside the metadata payload.

Example:

```text
system-implementation.components[]
```

may become repeated element nodes.

This must be controlled by metadata / registry configuration, not guessed from the existence of `[]`.

---

# 27. Mapping Type Caveat

The existing mapping CSV contains fields such as:

```text
Mapping_Type
```

Some of those values may still be incomplete, stale, or TBD.

Do not block the entire framework simply because a non-essential mapping annotation is incomplete.

Use confirmed mapping information that actually exists.

Do not invent missing mapping behavior.

---

# 28. Current Refactor Decision

The old SSP notebook is now:

```text
PROTOTYPE / REFERENCE
```

We are starting a NEW notebook for the production refactor.

Suggested name:

```text
NB_ARCHER_OSCAL_METADATA_ENGINE
```

The name intentionally does NOT contain only SSP because this engine must support multiple OSCAL models.

---

# 29. Immediate Development Order

Follow this sequence.

Do not skip ahead.

```text
1. Create new notebook

2. Reuse stable CONFIG/source-loading pieces

3. Load actual mapping CSV

4. Inspect exact source_df schema

5. Inspect exact mapping_df schema

6. Define canonical_mapping_df

7. Define element_registry_df

8. Validate SSP root → metadata → import-profile hierarchy

9. Confirm production node identity contract

10. Implement reusable node builder

11. Build SSP canonical nodes

12. Validate nodes

13. Implement generic relationship builder

14. Build SSP relationships

15. Validate edges

16. Implement generic DIM MERGE

17. Implement generic FACT MERGE

18. Expand through metadata to other OSCAL models
```

SSP is the first test case.

SSP is NOT a separate engine.

---

# 30. Rules For Any AI Working On This Project

Every AI assistant must follow these rules.

## Rule 1

Read this file before proposing code.

---

## Rule 2

Do not invent:

```text
source columns
mapping columns
target columns
table names
OSCAL mappings
```

Inspect unknowns first.

---

## Rule 3

Do not redesign established architecture casually.

If you think something needs to change, explain:

```text
what
why
impact
migration consequence
```

before changing code.

---

## Rule 4

Mapping CSV is the mapping source of truth.

Python should implement reusable mechanics.

---

## Rule 5

Keep these concepts distinct:

```text
SOURCE_JSON_PATH
OSCAL_ELEMENT_PATH
NODE_PATH
FIELD_RELATIVE_PATH
```

Never accidentally use the source path as the target path or vice versa.

---

## Rule 6

A mapping row is not automatically a DIM row.

Multiple field mappings may contribute to one node payload.

---

## Rule 7

Root and parent/child hierarchy must be metadata-driven.

Do not manually search for the SSP root later.

---

## Rule 8

Never use one global root for all source records.

---

## Rule 9

Repeated nodes require deterministic instance identity.

---

## Rule 10

Do not introduce a new hash/UUID algorithm without approval.

---

## Rule 11

Prefer reusable functions over element-specific code.

---

## Rule 12

Separate:

```text
BUILD
VALIDATE
WRITE
```

Do not combine all three into one giant function.

---

## Rule 13

Keep validation strong but compact.

---

## Rule 14

Do not immediately write to DIM/FACT when testing new generic logic.

Build the dataframe first.

Inspect it.

Then approve the write.

---

## Rule 15

Avoid unnecessary notebook-cell growth.

---

## Rule 16

If a choice may cause substantial rework later, raise it before coding.

---

## Rule 17

Do not create speculative code just to appear complete.

If information is missing, inspect or ask.

---

# 31. COPY THIS SECTION INTO ANOTHER AI

Below is the prompt to use when starting a fresh AI conversation.

---

## BEGIN AI PROMPT

I am building a production-grade metadata-driven OSCAL transformation engine using Snowflake and Snowpark/Python.

Before proposing code, follow these architecture rules.

### Goal

One reusable engine must support:

* SSP
* POA&M
* Assessment Plan
* Assessment Results
* Component Definition
* future OSCAL models

Do not build a separate engine per model.

### Source

The main source dataframe is conceptually:

```text
SOURCE_RECORD_ID
CURATED_JSON
```

`CURATED_JSON` is Snowflake VARIANT containing readable source field names.

### Mapping

A mapping CSV is the mapping source of truth.

It contains information such as:

```text
Archer_Field_Name
SOURCE_JSON_PATH
OSCAL_Model
OSCAL_Element_Path
Cardinality
OSCAL_Data_Type
Mapping_Type
Transformation_Logic
Notes
```

Use the actual dataframe columns I show you.

Do not invent columns.

A mapping row is a field-level instruction, NOT automatically a DIM row.

### Required architecture

```text
source_df
+
mapping_df
    ↓
canonical_mapping_df
    ↓
element_registry_df
    ↓
generic build_nodes()
    ↓
canonical_nodes_df
    ↓
generic build_dependencies()
    ↓
canonical_edges_df
    ↓
DIM MERGE
+
FACT MERGE
```

### SSP hierarchy example

```text
system-security-plan
    parent = NULL

system-security-plan.metadata
    parent = system-security-plan

system-security-plan.import-profile
    parent = system-security-plan
```

Root must be metadata-driven.

Do not build metadata first and later search the database for a root.

### Prototype lesson

The old prototype successfully built approximately 2165 metadata DIM rows but failed to create the corresponding SSP root rows before attempting FACT relationships.

Do not repeat that architecture.

### Identity

Existing approved helpers include:

```python
build_node_seed()
compute_node_key()
compute_node_uuid()
compute_edge_key()
```

The existing deterministic algorithm is MD5-based.

Do not introduce UUID4, random IDs, or a new hashing algorithm without approval.

Repeated OSCAL nodes require stable instance identity, so the production design must eventually support node-path + instance context.

Do not silently change identity behavior.

### FACT

A relationship such as:

```text
system-security-plan
    ->
metadata
```

must use the hashes/UUIDs belonging to the correct parent and child for the SAME source record.

Never use one global root.

### Notebook goal

Keep the production notebook compact.

Approximately:

```text
Cell 1
imports + CONFIG

Cell 2
source + mapping inputs

Cell 3
canonical mapping + element registry

Cell 4
reusable generic functions

Cell 5
build nodes + edges

Cell 6
validate + MERGE
```

### Development style

I want careful validation.

But I do not want dozens of validation cells.

Use reusable compact validation.

### Current task

We are refactoring from the beginning.

Do NOT write the entire engine immediately.

First:

1. inspect the actual source dataframe schema I give you
2. inspect the actual mapping CSV/dataframe columns
3. propose the exact `canonical_mapping_df` contract
4. propose the exact `element_registry_df` contract
5. show how SSP root, metadata, and import-profile would be represented
6. show how repeated nodes can later be represented safely
7. identify which existing reusable functions can be retained

Do NOT:

```text
MERGE
INSERT
UPDATE
DELETE
DROP
create FACT rows
write element-specific builders
invent mappings
invent schemas
```

Stop after the metadata contracts and wait for my approval.

## END AI PROMPT

---

# 32. WORKING CODE AREA

This section can be updated as the project progresses.

## Current CONFIG

```python
# Paste sanitized CONFIG here.
```

---

## Current source loading

```python
# Paste the approved source_df loading logic here.
```

---

## Current mapping loading

```python
# Paste the approved mapping CSV loading logic here.
```

---

## Current identity helpers

```python
# Paste:
# build_node_seed
# compute_node_key
# compute_node_uuid
# compute_edge_key
```

---

## Current JSON resolver

```python
# Paste approved resolve_json_path helper here.
```

---

## Current nested payload builder

```python
# Paste reusable OSCAL payload construction helpers here.
```

---

## Current canonical mapping code

```python
# Add after approved.
```

---

## Current element registry code

```python
# Add after approved.
```

---

## Current node-builder code

```python
# Add after approved.
```

---

## Current relationship-builder code

```python
# Add after approved.
```

---

## Current DIM merge

```python
# Add generic approved DIM MERGE here.
```

---

## Current FACT merge

```python
# Add generic approved FACT MERGE here.
```

---

# 33. Current Next Task

Current project phase:

```text
PRODUCTION REFACTOR
```

Immediate target:

```text
Create the new metadata-driven notebook.

First establish:

canonical_mapping_df

and

element_registry_df
```

Before writing generic DIM/FACT processing.

---

# 34. Decision Log

| Date       | Decision                                      | Reason                                                 |
| ---------- | --------------------------------------------- | ------------------------------------------------------ |
| 2026-08-24 | Stop extending old SSP prototype              | Too many procedural cells and repeated validation      |
| 2026-08-24 | Start a new production notebook               | Clean architecture without carrying prototype drift    |
| 2026-08-24 | Mapping CSV remains mapping source of truth   | Avoid hard-coded mappings                              |
| 2026-08-24 | Use metadata-driven element registry          | Root and parent relationships should not be hard-coded |
| 2026-08-24 | Reuse approved identity/hash helpers          | Preserve deterministic behavior                        |
| 2026-08-24 | Review identity seed before repeated elements | Prototype seed is insufficient for repeated instances  |
| 2026-08-24 | Keep strong checking but centralize it        | Reduce code/cell count and mental overhead             |
| 2026-08-24 | SSP becomes first test model                  | Engine must remain reusable for other OSCAL models     |

---

# 35. Definition of Done

The new engine is successful when:

* SSP root is created correctly
* metadata is created correctly
* import-profile is created correctly
* hierarchy is driven from metadata
* repeated OSCAL nodes have stable unique identity
* parent/child relationships are generated automatically
* DIM loads are idempotent
* FACT loads are idempotent
* mappings remain metadata-driven
* adding an OSCAL element mostly requires metadata changes
* adding POA&M or another OSCAL model does not require cloning the whole notebook
* validation remains strong
* production notebook remains small
* another engineer or AI can continue the project by reading this file

---

# 36. Guiding Principle

When there is a choice between:

```text
MORE HARDCODED PYTHON
```

and:

```text
BETTER METADATA + GENERIC FUNCTIONS
```

prefer:

```text
BETTER METADATA + GENERIC FUNCTIONS
```

unless there is a concrete technical reason not to.

The objective is not merely to make SSP work.

The objective is to build a reusable OSCAL mapping engine.

```

After you paste that into GitHub, **don’t start pasting random cells into the bottom yet**.

Our next move should be to take the **good reusable code from the old notebook one piece at a time** and put it under the appropriate section:

`CONFIG → source loader → identity helpers → JSON helpers`.

Then we start the new notebook from those approved pieces instead of rewriting them again. That is how we reduce the mental load from here. 
```
