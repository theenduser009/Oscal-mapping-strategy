Yes — this is much closer, but I would **not freeze this registry yet**. I caught a few design issues that are worth fixing now so this really is our last architectural rewrite.

The biggest positive: the AI correctly recognized the unambiguous SSP structure:

```text
system-security-plan
├── metadata
├── system-characteristics
├── system-implementation
└── control-implementation
```

And it correctly did **not** automatically turn `document-ids[]` or `components[]` into nodes. Good.

But I want these corrections before we implement it.

### 1. Add a real canonical model key

The registry needs:

```text
OSCAL_MODEL_KEY
```

Example:

```text
SSP
POAM
ASSESSMENT_PLAN
ASSESSMENT_RESULTS
PROFILE
```

Because the CSV's current `OSCAL_MODEL` is really a raw mapping section:

```text
SSP - Metadata
SSP - System Characteristics
...
```

So production should work like:

```text
CONFIG["OSCAL_MODEL"] = "SSP"
        ↓
element_registry.OSCAL_MODEL_KEY = "SSP"
        ↓
ROOT_NODE_PATH = system-security-plan
```

That makes the engine truly reusable.

---

### 2. `INSTANCE_KEY_RULE = "content_id"` is not right

The standardized engine uses:

```text
SOURCE_RECORD_ID
```

and source record identity is already part of the node identity.

For singleton nodes, use something like:

```text
INSTANCE_KEY_RULE = "SINGLETON"
```

Then later:

```text
components[]
```

might have:

```text
INSTANCE_KEY_RULE = <stable component identifier>
```

We should decide that only when we inspect its actual source representation.

---

### 3. `PROCESS_ORDER` should represent hierarchy depth

The AI has:

```text
root                   1
metadata               2
system-characteristics 3
system-implementation  4
```

That incorrectly implies the siblings depend on one another.

They don't.

It should be:

```text
system-security-plan        1

metadata                    2
system-characteristics      2
system-implementation       2
control-implementation      2
```

Later:

```text
component                   3
prop                        4
```

etc.

That makes `PROCESS_ORDER` generic.

---

### 4. It forgot `control-implementation` in the candidate rows

The analysis itself found:

```text
SSP - Control Implementation
→ system-security-plan.control-implementation.*
```

and even says it is a child of root.

So if we're accepting those raw mapping groups as evidence of a node boundary, it should also be in the candidate registry.

---

### 5. Most important: add a node creation rule

This directly prevents **the exact root problem we suffered before**.

The registry needs one additional column:

```text
NODE_CREATION_RULE
```

Conceptually:

```text
system-security-plan
    ALWAYS_PER_SOURCE_RECORD

metadata
    WHEN_MAPPED_VALUE_EXISTS

system-characteristics
    WHEN_MAPPED_VALUE_EXISTS

system-implementation
    WHEN_MAPPED_VALUE_EXISTS

control-implementation
    WHEN_MAPPED_VALUE_EXISTS
```

Later a collection might have:

```text
components[]
    PER_COLLECTION_INSTANCE
```

Why this matters:

If the generic builder only creates nodes when it finds direct field mappings, the SSP root could disappear **again**, because most mappings belong to children.

With:

```text
NODE_CREATION_RULE = ALWAYS_PER_SOURCE_RECORD
```

the registry explicitly tells the engine:

> Create the root for every source record, even if its own payload has no direct field mapping.

That's the production-grade fix to the mistake we made earlier.

---

### 6. Relationship type belongs in metadata too

Add:

```text
DEPENDENCY_TYPE
```

Root:

```text
NULL
```

Children eventually get the approved relationship value.

We don't need to decide today whether the exact value is:

```text
parent_of
contains
```

or something else.

But the **column should exist**, because we specifically don't want relationship type hardcoded in Python later.

---

## Therefore I would freeze the registry contract as

```text
OSCAL_MODEL_KEY
ROOT_NODE_PATH
NODE_PATH
ELEMENT_TYPE
PARENT_NODE_PATH
DEPENDENCY_TYPE
IS_COLLECTION
INSTANCE_KEY_RULE
NODE_CREATION_RULE
PROCESS_ORDER
IS_ACTIVE
```

And SSP initially looks conceptually like:

| Model | Node                                          | Parent | Collection | Instance Rule | Creation Rule            | Order |
| ----- | --------------------------------------------- | ------ | ---------- | ------------- | ------------------------ | ----: |
| SSP   | `system-security-plan`                        | NULL   | False      | SINGLETON     | ALWAYS_PER_SOURCE_RECORD |     1 |
| SSP   | `system-security-plan.metadata`               | root   | False      | SINGLETON     | WHEN_MAPPED_VALUE_EXISTS |     2 |
| SSP   | `system-security-plan.system-characteristics` | root   | False      | SINGLETON     | WHEN_MAPPED_VALUE_EXISTS |     2 |
| SSP   | `system-security-plan.system-implementation`  | root   | False      | SINGLETON     | WHEN_MAPPED_VALUE_EXISTS |     2 |
| SSP   | `system-security-plan.control-implementation` | root   | False      | SINGLETON     | WHEN_MAPPED_VALUE_EXISTS |     2 |

We **do not add `components[]` yet**.

We **do not add `import-profile` yet** because the mapping inspection hasn't actually proven it in the current CSV.

---

## And here is the really nice part

Once this registry exists, we don't have to guess where every mapping belongs.

For:

```text
system-security-plan.metadata.document-ids[].identifier
```

we compare it to registered node prefixes.

It matches:

```text
system-security-plan
system-security-plan.metadata
```

The **deepest registered node prefix** is:

```text
system-security-plan.metadata
```

Therefore:

```text
OWNER_NODE_PATH =
system-security-plan.metadata

FIELD_RELATIVE_PATH =
document-ids[].identifier
```

Perfect.

Similarly:

```text
system-security-plan.system-characteristics.security-impact-level.security-objective-integrity
```

gets owned by:

```text
system-security-plan.system-characteristics
```

without making `security-impact-level` another DIM node.

And later, if we deliberately add:

```text
system-security-plan.system-implementation.components[]
```

to the registry, the exact same matching algorithm automatically starts treating components as separate nodes.

**That's the reusable design we've been trying to reach.**

### Tell the other AI this exact thing

> The candidate registry is close, but make these architecture corrections before generating any implementation:
>
> 1. Add `OSCAL_MODEL_KEY`. This is the canonical model selector such as `SSP`, `POAM`, etc. Do not use raw CSV `OSCAL_MODEL` values such as `SSP - Metadata` as the runtime model key.
>
> 2. For singleton nodes use `INSTANCE_KEY_RULE = "SINGLETON"`, not `"content_id"`. Source record identity is already represented separately by `SOURCE_RECORD_ID`.
>
> 3. `PROCESS_ORDER` represents hierarchy depth, not sibling sequence. Root = 1. All direct SSP children = 2.
>
> 4. Add the unambiguous `system-security-plan.control-implementation` child because the mapping inspection showed the `SSP - Control Implementation` path group.
>
> 5. Add `NODE_CREATION_RULE` to the registry. Supported conceptual policies for now:
>
>    * `ALWAYS_PER_SOURCE_RECORD`
>    * `WHEN_MAPPED_VALUE_EXISTS`
>    * later `PER_COLLECTION_INSTANCE`
>
>    SSP root must use `ALWAYS_PER_SOURCE_RECORD` so we never repeat the earlier missing-root failure.
>
> 6. Add nullable `DEPENDENCY_TYPE` so relationship semantics are metadata-driven rather than hardcoded in Python. Do not choose its final child value yet.
>
> Final proposed schema:
>
> `OSCAL_MODEL_KEY`
> `ROOT_NODE_PATH`
> `NODE_PATH`
> `ELEMENT_TYPE`
> `PARENT_NODE_PATH`
> `DEPENDENCY_TYPE`
> `IS_COLLECTION`
> `INSTANCE_KEY_RULE`
> `NODE_CREATION_RULE`
> `PROCESS_ORDER`
> `IS_ACTIVE`
>
> Show the corrected five SSP registry rows only.
>
> Do NOT create them as a hardcoded production Python list yet.
> Do NOT build nodes.
> Do NOT build FACT.
> Do NOT modify Cells 1 or 2.
> STOP after showing the corrected registry rows.

And one more important decision: **I don't want these registry rows permanently hardcoded in Python.** Once we approve these five rows, we should make them structural metadata — likely a small second CSV/table such as `oscal_element_registry` — so adding elements/models is a metadata change, exactly as we intended.
