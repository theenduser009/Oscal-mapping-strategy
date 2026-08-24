Yes — **this inspection finally gave us the key answer.** And it changes one important assumption in a good way.

Your CSV’s `OSCAL_MODEL` column is **not actually a clean model identifier**. It is mixing model names and mapping sections:

```text
SSP - Metadata
SSP - System Characteristics
SSP - System Implementation
SSP - Control Implementation
System Security Plan
Assessment Results
Security Assessment Plan
POA&M
Profile
TBD
...
```

So we should **never again do**:

```python
col("OSCAL_MODEL") == "SSP"
```

That was the reason for the zero rows.

### What IS reliable

The strongest metadata we have is `OSCAL_ELEMENT_PATH`.

For example:

```text
system-security-plan.metadata.last-modified
system-security-plan.metadata.props
system-security-plan.system-characteristics.description
system-security-plan.system-implementation.components[]
plan-of-action-and-milestones.poam-items[]
assessment-results.results[].findings[]
profile.imports[]
```

From this, the **first path segment gives us the OSCAL root/model family**:

```text
system-security-plan.*              → root = system-security-plan
plan-of-action-and-milestones.*     → root = plan-of-action-and-milestones
assessment-results.*                → root = assessment-results
security-assessment-plan.*          → root = security-assessment-plan
profile.*                           → root = profile
```

That part can be generic.

---

## But here is the production-grade distinction we need

The existing CSV is excellent for:

> **FIELD MAPPING**

It tells us:

```text
Archer field
      ↓
OSCAL element path
```

But it is **not enough by itself to safely define every node boundary**.

For example:

```text
system-security-plan.metadata.document-ids[].identifier
```

Should NOT necessarily produce:

```text
metadata
document-ids
identifier
```

as three DIM nodes.

It likely belongs inside the `metadata` payload.

But:

```text
system-security-plan.system-implementation.components[]
```

may legitimately represent repeated `component` DIM nodes.

That distinction cannot safely be guessed just because a path contains `.` or `[]`.

### So our final metadata architecture should have TWO metadata datasets

```text
                 Existing Mapping CSV
                    FIELD MAPPING
                         │
                         │
                         ▼
                 canonical_mapping_df


               OSCAL Element Registry
                 STRUCTURE/HIERARCHY
                         │
                         ▼
                 element_registry_df
```

Then both feed the engine:

```text
canonical_mapping_df
        +
element_registry_df
        ↓
    build_nodes()
        ↓
canonical_nodes_df
        ↓
build_dependencies()
        ↓
canonical_edges_df
```

This is the piece that prevents us from ever having the SSP-root problem again.

---

## The element registry is small

It would contain rows such as:

| MODEL_ROOT           | NODE_PATH                                   | ELEMENT_TYPE           | PARENT_NODE_PATH     | COLLECTION | ORDER |
| -------------------- | ------------------------------------------- | ---------------------- | -------------------- | ---------- | ----: |
| system-security-plan | system-security-plan                        | system-security-plan   | NULL                 | No         |     1 |
| system-security-plan | system-security-plan.metadata               | metadata               | system-security-plan | No         |     2 |
| system-security-plan | system-security-plan.system-characteristics | system-characteristics | system-security-plan | No         |     2 |
| system-security-plan | system-security-plan.system-implementation  | system-implementation  | system-security-plan | No         |     2 |

And later, when confirmed:

```text
system-security-plan.system-implementation.components[]
```

could be:

```text
PARENT_NODE_PATH =
system-security-plan.system-implementation
```

Now the relationship is automatic.

There is no:

```python
if SSP:
    connect metadata to root
```

Instead:

```text
metadata.PARENT_NODE_PATH
        =
system-security-plan
```

and the generic edge builder does the rest.

---

## This also answers your original root question

For every model:

```text
PARENT_NODE_PATH = NULL
```

means:

**ROOT**

So:

```text
system-security-plan
```

becomes the SSP root.

And:

```text
system-security-plan.metadata
```

knows its parent is:

```text
system-security-plan
```

That's all FACT needs.

---

### One other important thing from your output

You have:

```text
608 total mappings
416 = TBD
```

That's okay.

We **keep all 608 mappings** in the raw mapping layer.

We do not throw TBD away.

But the production engine should process only mappings that have a usable, approved OSCAL path. TBD/unresolved mappings remain visible for governance and future completion.

So we are not allowing unfinished mappings to block the engine.

---

# What I want the other AI to do next

Don't let it build nodes yet.

Give it this exact prompt:

> The inspection is complete and it revealed the correct architecture.
>
> Important findings:
>
> * `OSCAL_MODEL` is NOT a canonical model identifier. It contains section/category values such as `SSP - Metadata`, `SSP - System Characteristics`, `SSP - System Implementation`, `SSP - Control Implementation`, `System Security Plan`, `Assessment Results`, `POA&M`, etc.
> * Therefore NEVER filter with `OSCAL_MODEL == "SSP"`.
> * Preserve the original `OSCAL_MODEL` value as mapping metadata, conceptually `OSCAL_MODEL_RAW` or `MAPPING_SECTION`.
> * `OSCAL_ELEMENT_PATH` is the authoritative OSCAL target path.
> * The first path segment can deterministically identify `ROOT_NODE_PATH`.
>
> Examples:
>
> `system-security-plan.metadata.last-modified`
> → ROOT_NODE_PATH = `system-security-plan`
>
> `assessment-results.results[].findings[]`
> → ROOT_NODE_PATH = `assessment-results`
>
> `plan-of-action-and-milestones.poam-items[]`
> → ROOT_NODE_PATH = `plan-of-action-and-milestones`
>
> Do NOT infer every dot-separated segment or every `[]` segment as a DIM node.
>
> The existing CSV is FIELD-MAPPING metadata.
>
> We will use a separate `element_registry_df` as STRUCTURAL metadata that explicitly defines node boundaries and parent-child relationships.
>
> For the next step only:
>
> 1. Create a proposed schema for `element_registry_df` with:
>
> `ROOT_NODE_PATH`
> `NODE_PATH`
> `ELEMENT_TYPE`
> `PARENT_NODE_PATH`
> `IS_COLLECTION`
> `INSTANCE_KEY_RULE`
> `PROCESS_ORDER`
> `IS_ACTIVE`
>
> 2. Using the current mapping dataframe, inspect ONLY rows whose valid `OSCAL_ELEMENT_PATH` starts with:
>
> `system-security-plan`
>
> 3. Group/show those paths by their existing raw `OSCAL_MODEL` value:
>
> `System Security Plan`
> `SSP - Metadata`
> `SSP - System Characteristics`
> `SSP - System Implementation`
> `SSP - Control Implementation`
>
> 4. For each group, show the distinct OSCAL paths and their longest common path prefix.
>
> 5. Propose candidate registry nodes only where the node boundary is unambiguous.
>
> At minimum we already expect to validate candidates such as:
>
> `system-security-plan`
> `system-security-plan.metadata`
> `system-security-plan.system-characteristics`
> `system-security-plan.system-implementation`
>
> Do NOT assume `import-profile`, `components[]`, `props[]`, or control-implementation node boundaries until the actual paths prove them.
>
> Do NOT create `canonical_nodes_df`.
> Do NOT build FACT.
> Do NOT MERGE.
> Do NOT modify Cells 1 or 2.
>
> Show the candidate `element_registry_df` proposal and STOP.

This is the right turn. **We're no longer trying to make Python discover OSCAL structure magically. Mapping metadata handles fields; structural metadata handles nodes/relationships. The generic engine consumes both.**

That design will carry us beyond SSP without rewriting the engine.
