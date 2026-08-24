Yes — the real problem is that the other AI keeps trying to **infer too much from the mapping CSV**, and every time it guesses, we end up redesigning Cell 3.

We should stop asking it to “discover” the whole OSCAL structure.

Here is the clean decision:

**Cell 3 has only two jobs:**

```text
1. Normalize the field-mapping CSV
2. Load/use a separate structural element registry
```

That’s it.

The existing CSV is for:

```text
ARCHER FIELD
    →
OSCAL FIELD PATH
```

It is **not reliable enough to decide every node boundary and parent relationship**.

So we should stop making AI invent things like:

```text
is this a node?
is document-ids[] a node?
is components[] a node?
what is the parent?
```

That structural information belongs in a **small second metadata object**: `element_registry_df`.

This actually makes the architecture MORE reusable, not less:

```text
FIELD MAPPING CSV
        +
ELEMENT REGISTRY
        ↓
GENERIC ENGINE
```

For SSP, the first registry rows can simply be:

```text
system-security-plan
system-security-plan.metadata
system-security-plan.system-characteristics
system-security-plan.system-implementation
system-security-plan.control-implementation
```

Later we add `components[]`, `props[]`, POA&M nodes, Assessment Results nodes, etc. as metadata rows — **no Python rewrite**.

---

## Send the other AI this exact prompt

> STOP trying to infer the complete OSCAL hierarchy from the existing mapping CSV.
>
> We are stuck because the mapping CSV is FIELD-MAPPING metadata, not a complete structural/node-registry definition.
>
> We are freezing the architecture now.
>
> ## FINAL ARCHITECTURE
>
> There are TWO metadata inputs:
>
> ### 1. `mapping_df`
>
> Existing CSV.
>
> Purpose:
>
> `SOURCE FIELD -> OSCAL_ELEMENT_PATH`
>
> It contains the existing 608 mapping rows and columns:
>
> `ARCHER_FIELD_NAME`
> `Sparx EA Mapping Completed`
> `NULL%`
> `DATA_TYPE`
> `CARDINALITY`
> `OSCAL_MODEL`
> `OSCAL_ELEMENT_PATH`
> `OSCAL_DATA_TYPE`
> `MAPPING_TYPE`
> `TRANSFORMATION_LOGIC`
> `NOTES`
>
> This CSV does NOT define all node boundaries.
>
> ### 2. `element_registry_df`
>
> Separate structural metadata.
>
> Purpose:
>
> define which OSCAL paths become DIM nodes and how those nodes relate to each other.
>
> It must contain:
>
> `OSCAL_MODEL_KEY`
> `NODE_PATH`
> `ELEMENT_TYPE`
> `PARENT_NODE_PATH`
> `IS_COLLECTION`
> `INSTANCE_KEY_RULE`
> `PROCESS_ORDER`
> `IS_ACTIVE`
>
> Do NOT add more columns right now.
>
> Do NOT invent dependency types, creation rules, or new identity policies in this step.
>
> ---
>
> ## CELL 3 RESPONSIBILITY
>
> Cell 3 must create only:
>
> `canonical_mapping_df`
>
> and
>
> `element_registry_df`
>
> Nothing else.
>
> No DIM.
> No FACT.
> No node hashes.
> No UUIDs.
> No MERGE.
> No payload construction.
>
> ---
>
> ## PART A — canonical_mapping_df
>
> Keep all original mapping rows.
>
> Normalize only these runtime column names:
>
> `ARCHER_FIELD_NAME -> SOURCE_FIELD_NAME`
>
> keep:
>
> `OSCAL_MODEL`
> `OSCAL_ELEMENT_PATH`
> `CARDINALITY`
> `OSCAL_DATA_TYPE`
> `MAPPING_TYPE`
> `TRANSFORMATION_LOGIC`
>
> Preserve the original `OSCAL_MODEL` value as raw mapping metadata.
>
> Do NOT filter `OSCAL_MODEL == "SSP"`.
>
> For the SSP test case, identify usable mappings by:
>
> `OSCAL_ELEMENT_PATH starts with "system-security-plan"`
>
> because the raw `OSCAL_MODEL` column contains section labels such as:
>
> `SSP - Metadata`
> `SSP - System Characteristics`
> `SSP - System Implementation`
> `SSP - Control Implementation`
>
> and is not a canonical model key.
>
> Do NOT derive node boundaries from every dot in `OSCAL_ELEMENT_PATH`.
>
> ---
>
> ## PART B — element_registry_df
>
> Do NOT derive this automatically from every mapping path.
>
> Build/load it as explicit structural metadata.
>
> For the FIRST SSP test, use exactly these five approved registry rows:
>
> | OSCAL_MODEL_KEY | NODE_PATH | ELEMENT_TYPE | PARENT_NODE_PATH | IS_COLLECTION | INSTANCE_KEY_RULE | PROCESS_ORDER | IS_ACTIVE |
> | SSP | system-security-plan | system-security-plan | NULL | False | SINGLETON | 1 | True |
> | SSP | system-security-plan.metadata | metadata | system-security-plan | False | SINGLETON | 2 | True |
> | SSP | system-security-plan.system-characteristics | system-characteristics | system-security-plan | False | SINGLETON | 2 | True |
> | SSP | system-security-plan.system-implementation | system-implementation | system-security-plan | False | SINGLETON | 2 | True |
> | SSP | system-security-plan.control-implementation | control-implementation | system-security-plan | False | SINGLETON | 2 | True |
>
> These rows are STRUCTURAL metadata.
>
> Do not infer `document-ids[]`, `props[]`, `components[]`, or other nested paths as separate nodes yet.
>
> Those remain payload paths until deliberately added to `element_registry_df`.
>
> ---
>
> ## IMPORTANT GENERIC RULE
>
> A mapping belongs to the deepest registered `NODE_PATH` that is a prefix of its `OSCAL_ELEMENT_PATH`.
>
> Example:
>
> `system-security-plan.metadata.document-ids[].identifier`
>
> matches:
>
> `system-security-plan`
>
> and
>
> `system-security-plan.metadata`
>
> The deepest registered match is:
>
> `system-security-plan.metadata`
>
> Therefore:
>
> `OWNER_NODE_PATH = system-security-plan.metadata`
>
> and:
>
> `FIELD_RELATIVE_PATH = document-ids[].identifier`
>
> Another example:
>
> `system-security-plan.system-characteristics.security-impact-level.security-objective-integrity`
>
> belongs to:
>
> `system-security-plan.system-characteristics`
>
> Do NOT turn `security-impact-level` into a DIM node unless it is explicitly added to the registry.
>
> ---
>
> ## CELL 3 OUTPUT
>
> Cell 3 should output only:
>
> 1. `canonical_mapping_df`
> 2. `element_registry_df`
> 3. count of usable SSP mapping rows
> 4. the five registry rows
> 5. 10 example mappings showing:
>
>    * `SOURCE_FIELD_NAME`
>    * `OSCAL_ELEMENT_PATH`
>    * matched `OWNER_NODE_PATH`
>    * derived `FIELD_RELATIVE_PATH`
>
> If a mapping cannot match any registered node, mark:
>
> `OWNER_NODE_PATH = NULL`
>
> Do NOT invent one.
>
> ---
>
> ## ABSOLUTE RULES
>
> Do not change Cell 1.
> Do not change Cell 2.
> Do not create Cell 4.
> Do not redesign the registry.
> Do not add more structural columns.
> Do not create nodes.
> Do not create relationships.
> Do not write to Snowflake.
>
> Build this exact Cell 3 and STOP.

This is the important reset: **we are no longer asking AI to be an OSCAL architect inside Cell 3.** We are giving it a precise metadata contract.

And this remains fully dynamic:

```text
new field mapping
→ change mapping CSV

new OSCAL node
→ add registry row

new parent/child structure
→ change registry metadata

Python engine
→ unchanged
```

That is the architecture we wanted from the beginning.
