Yeah — **do not approve Cell 4 yet.** I caught several important errors in what the other AI generated. This is exactly why we’re checking before Cell 5.

The biggest one is serious: **it rewrote our approved identity logic even though we explicitly said not to.**

Your screenshot now has something like:

```python
def build_node_seed(oscal_model_key, source_record_id, node_path, ...)
```

That is **not** the old approved function.

The frozen prototype contract was:

```python
build_node_seed(
    source_system,
    source_table,
    content_id,
    node_type
)
```

with seed:

```text
SOURCE_SYSTEM|SOURCE_TABLE|CONTENT_ID|NODE_TYPE
```

It also changed these:

```python
compute_node_key()
compute_node_uuid()
build_edge_seed()
compute_edge_key()
```

For example, I can see `compute_node_key()` returning a **32-character MD5 hex string**. Our target DIM PK is `BINARY(16)` and the old approved function returned the MD5 **digest bytes**, not hex text.

It also changed UUID generation to SHA-256 / UUID formatting. That is completely different from the frozen 32-character lowercase MD5 hex we already used for the 2,165 metadata records.

And this is wrong too:

```python
sorted([source_node_key, target_node_key])
```

for the edge seed.

Our edge is directional:

```text
PARENT → CHILD
```

Sorting destroys that direction.

So this part absolutely cannot move forward.

There is a second important bug: `get_mappings_for_node()` returns the original canonical mapping rows, but `canonical_mapping_df` does **not** contain:

```text
FIELD_RELATIVE_PATH
```

Then `build_element_payload()` does this:

```python
field_relative_path = m.get("FIELD_RELATIVE_PATH") or m["OSCAL_ELEMENT_PATH"]
```

That means if `FIELD_RELATIVE_PATH` is missing, it could feed the **full OSCAL path** into the payload builder.

For metadata, instead of building:

```json
{
  "last-modified": "..."
}
```

it could start building something conceptually like:

```json
{
  "system-security-plan": {
    "metadata": {
      "last-modified": "..."
    }
  }
}
```

inside the **metadata node payload itself**.

That is wrong. The node payload must only contain the path **relative to its owner node**.

There is also a resolver issue: its `[]` handling returns the list immediately, which means a path like:

```text
something[].identifier
```

doesn't actually continue through `identifier`. That may bite us later.

So we are **not rewriting Cell 4 from scratch**, but there are specific corrections.

Give the other AI exactly this:

> **STOP. Cell 4 is NOT approved. Do not create Cell 5.**
>
> You changed established contracts that were explicitly frozen.
>
> Make ONLY the corrections below.
>
> ---
>
> ## CORRECTION 1 — IDENTITY FUNCTIONS MUST BE COPIED EXACTLY FROM THE OLD NOTEBOOK
>
> You redesigned the identity helpers. Undo that.
>
> Do NOT create a new signature based on:
>
> `OSCAL_MODEL_KEY`
> `NODE_PATH`
> `FIELD_RELATIVE_PATH`
>
> The existing approved V1 node identity contract is exactly:
>
> `build_node_seed(source_system, source_table, content_id, node_type)`
>
> Seed format:
>
> `SOURCE_SYSTEM|SOURCE_TABLE|CONTENT_ID|NODE_TYPE`
>
> `compute_node_key(seed)` must preserve the existing behavior:
>
> MD5 digest bytes → `BINARY(16)`
>
> NOT MD5 hex text.
>
> `compute_node_uuid(seed)` must preserve the existing behavior:
>
> lowercase MD5 hex → 32-character text
>
> Do NOT use SHA256.
>
> Do NOT format it into UUID groups.
>
> Do NOT introduce UUID5.
>
> Do NOT redesign repeated-node identity in Cell 4.
>
> The exact approved behavior must be copied from the old notebook byte-for-byte if available.
>
> ---
>
> ## CORRECTION 2 — EDGE IDENTITY IS DIRECTIONAL
>
> Do NOT sort source and target node keys.
>
> Parent → child direction matters.
>
> Preserve the existing approved edge seed/helper from the old notebook, including its existing `edge_type` behavior.
>
> Do not invent a new edge algorithm.
>
> ---
>
> ## CORRECTION 3 — `get_mappings_for_node()` MUST RETURN RELATIVE PATH
>
> `canonical_mapping_df` does not contain `FIELD_RELATIVE_PATH`.
>
> Therefore `get_mappings_for_node()` must return mapping records enriched with:
>
> `OWNER_NODE_PATH`
>
> and
>
> `FIELD_RELATIVE_PATH`
>
> using the exact ownership rule already proven in Cell 3.
>
> For example:
>
> OSCAL_ELEMENT_PATH:
>
> `system-security-plan.metadata.document-ids[].identifier`
>
> OWNER_NODE_PATH:
>
> `system-security-plan.metadata`
>
> FIELD_RELATIVE_PATH:
>
> `document-ids[].identifier`
>
> Do NOT return the original mapping row without this information.
>
> ---
>
> ## CORRECTION 4 — REMOVE THE FULL-PATH FALLBACK
>
> Delete behavior equivalent to:
>
> `FIELD_RELATIVE_PATH or OSCAL_ELEMENT_PATH`
>
> `build_element_payload()` must consume `FIELD_RELATIVE_PATH`.
>
> If a mapping does not have a valid relative path for the requested node, skip/flag that mapping rather than inserting the full OSCAL path into the node payload.
>
> ---
>
> ## CORRECTION 5 — SOURCE LOOKUP
>
> For the current mappings, use the already-proven prototype behavior for resolving `SOURCE_FIELD_NAME` from `CURATED_JSON`.
>
> Do not invent `SOURCE_JSON_PATH`.
>
> Do not redesign source lookup.
>
> Keep `resolve_json_path()` only if it matches the existing approved prototype implementation.
>
> If your current version is not copied from the old notebook, replace it with the exact old implementation rather than rewriting it.
>
> ---
>
> ## CORRECTION 6 — KEEP THE TRANSFORMATION HELPER SIMPLE
>
> Current `apply_transform()` behavior is acceptable:
>
> * source `None` → `None`
> * unresolved/TBD → preserve source value
> * no fabricated `"TBD_TRANSFORM"` string
>
> Do not add new transformations yet.
>
> ---
>
> ## IMPORTANT
>
> Do not modify Cells 1–3.
>
> Do not build `canonical_nodes_df`.
>
> Do not build relationships.
>
> Do not write DIM.
>
> Do not write FACT.
>
> Do not redesign identity for collections.
>
> Show corrected Cell 4 only and STOP.

### The part I want you to remember

Our architecture is still:

```text
mapping CSV
      +
element registry
      ↓
generic reusable functions
      ↓
nodes
      ↓
relationships
```

But **reusable does not mean we are allowed to silently change keys that already exist in the database**.

That other AI crossed that line in Cell 4.

Good thing we caught it now. If we had built Cell 5 with this version, the new hashes would not line up with the 2,165 records already created by the prototype, and we'd have another major cleanup.

So: **Cells 1–3 stay frozen. Cell 4 needs correction only. No Cell 5 yet.**
