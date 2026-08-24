Yes — **this Cell 3 is finally good enough to freeze.** I read the screenshots carefully.

The important outputs are exactly what we needed:

```text
canonical_mapping_df: 608 rows
element_registry_df: 5 rows
usable mappings for SSP: 54
mappings without registered owner: 0
```

And the two critical fixes are now present:

* no hardcoded `system-security-plan%` filter in the generic ownership logic
* prefix matching is segment-safe:
  `path = NODE_PATH OR path LIKE NODE_PATH || '.%'`

Also, `DATA_TYPE` is preserved now. Good.

### Freeze Cell 3 now

Do **not** let the other AI touch Cells 1–3 anymore.

We now have the foundation:

```text
Cell 1
CONFIG

Cell 2
source_df + mapping_df

Cell 3
canonical_mapping_df + element_registry_df
        ↓
deepest registered owner-node matching works
```

That means this is working:

```text
system-security-plan.metadata.document-ids[].identifier
                       ↓
OWNER_NODE_PATH
system-security-plan.metadata
                       ↓
FIELD_RELATIVE_PATH
document-ids[].identifier
```

That is the abstraction we needed.

One thing to remember: those 5 registry rows are temporarily defined inside Python. That's acceptable for proving the engine. Later they should become actual metadata rows in a table/CSV. **We do not refactor that now.**

---

## Now Cell 4

Cell 4 should **not build nodes yet**.

It should contain the reusable functions that Cell 5 will call.

This is where we bring the good pieces from the old notebook back in, but cleanly.

Send the other AI exactly this:

> **Cells 1, 2 and 3 are now APPROVED AND FROZEN. Do not modify them.**
>
> Current approved runtime objects:
>
> `source_df`
>
> `mapping_df`
>
> `canonical_mapping_df`
>
> `element_registry_df`
>
> Cell 3 results:
>
> * canonical mapping rows = 608
> * registry rows = 5
> * usable mappings for `CONFIG["OSCAL_MODEL"] = "SSP"` = 54
> * mappings without registered owner = 0
>
> The generic deepest-owner-node matching is working.
>
> ---
>
> # TASK: CELL 4 ONLY — REUSABLE FUNCTIONS
>
> Cell 4 contains reusable functions only.
>
> Do NOT execute the SSP build yet.
>
> Do NOT create `canonical_nodes_df`.
>
> Do NOT create `canonical_edges_df`.
>
> Do NOT MERGE.
>
> Do NOT write DIM or FACT.
>
> Do NOT add more registry rows.
>
> Do NOT modify identity behavior yet.
>
> ---
>
> ## A. Reuse the existing approved identity helpers
>
> Bring over the existing prototype functions unchanged:
>
> `build_node_seed(...)`
>
> `compute_node_key(seed)`
>
> `compute_node_uuid(seed)`
>
> `build_edge_seed(...)`
>
> `compute_edge_key(...)`
>
> Important:
>
> The existing node seed is still the legacy singleton V1 contract.
>
> Do NOT redesign it in Cell 4.
>
> We will deal with repeated-node identity only when collection nodes are deliberately introduced into the registry.
>
> ---
>
> ## B. Reuse the source JSON resolver
>
> Bring over the approved reusable:
>
> `resolve_json_path(obj, path)`
>
> It must only retrieve a value from source JSON.
>
> It must not contain SSP-specific logic.
>
> Do not invent fallback field names.
>
> ---
>
> ## C. Reuse the nested OSCAL payload helper
>
> Bring over the approved generic:
>
> `set_nested_path(container, path_segments, value)`
>
> This function creates the nested payload structure from `FIELD_RELATIVE_PATH`.
>
> It must support nested dictionaries and existing `[]` array notation.
>
> No SSP-specific paths may be hardcoded.
>
> ---
>
> ## D. Transformation helper
>
> Do NOT bring back the previous behavior that returned literal `"TBD_TRANSFORM"`.
>
> We must never fabricate OSCAL values.
>
> Create a minimal helper contract:
>
> `apply_transform(value, mapping_type, transformation_logic)`
>
> For now:
>
> * `None` source value -> return `None`
> * direct/no-transform mapping -> return source value
> * unresolved/TBD transformation -> return source value unchanged AND allow it to be flagged later
>
> Do not invent transformation behavior.
>
> Do not parse dates, UUIDs, references, or special OSCAL types unless an existing approved transformation already exists.
>
> ---
>
> ## E. Add ONE generic helper for mapping ownership
>
> Create a reusable helper concept for:
>
> `get_mappings_for_node(...)`
>
> Inputs should be based on:
>
> `canonical_mapping_df`
>
> `element_registry_df`
>
> `OSCAL_MODEL_KEY`
>
> `NODE_PATH`
>
> It should return the field mappings owned by that registered node using the same deepest-node ownership rule already proven in Cell 3.
>
> Do not hardcode `metadata`, `system-security-plan`, or any other element.
>
> ---
>
> ## F. Add ONE generic payload-building helper
>
> Define:
>
> `build_element_payload(...)`
>
> Conceptually it receives:
>
> * one source record
> * mappings belonging to one registered node
>
> and:
>
> 1. resolves source values
> 2. applies approved transformation logic
> 3. writes values into the relative OSCAL payload path
> 4. returns one Python dict/object representing that node payload
>
> It must NOT generate node hashes.
>
> It must NOT create DIM rows.
>
> It must NOT know the target table name.
>
> It must NOT know about SSP specifically.
>
> ---
>
> ## IMPORTANT SOURCE-PATH RULE
>
> The existing CSV does not currently contain a `SOURCE_JSON_PATH` column.
>
> Do NOT invent one.
>
> Before implementing `build_element_payload()`, inspect how the already-approved prototype successfully resolved `SOURCE_FIELD_NAME` against `CURATED_JSON`.
>
> Reuse that exact source lookup behavior.
>
> If you cannot determine that behavior from the existing notebook/code, STOP and ask for the previous resolver logic instead of guessing.
>
> ---
>
> ## OUTPUT
>
> Show Cell 4 only.
>
> It should contain reusable function definitions and no execution of a model build.
>
> At the end print only:
>
> `Cell 4 loaded - reusable functions ready`
>
> Then STOP.
>
> Do not create Cell 5.

### Why I'm stopping Cell 4 before node building

This is intentional.

We now have two stable layers:

```text
METADATA
    ↓
generic reusable mechanics
```

Cell 5 will then be very small:

```text
for each registry node
    build payloads
    generate identity
    produce canonical node rows
```

That is where we finally create:

```text
system-security-plan
metadata
system-characteristics
system-implementation
control-implementation
```

for each source record **using the same builder**.

We're finally past the Cell 3 architecture loop. **Freeze it and move forward.**
