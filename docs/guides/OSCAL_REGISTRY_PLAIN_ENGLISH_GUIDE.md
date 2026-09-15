# OSCAL Registry — Plain-English Guide

**Created:** 2026-09-15  
**Purpose:** Explain the live `OSCAL_ELEMENT_REGISTRY` in a way that is easy to remember and use during development/testing.

## The one idea to remember

Treat the registry as **instructions for building an OSCAL house**.

Each registry row answers:

> **What do I build, where do I put it, is there one or many, how do I identify it, where are the source items, how do I build it, does it need a UUID, and must anything be present first?**

Do not start by memorizing column names. Translate each row into that sentence.

---

## The mental checklist

For every registry row ask these questions in order:

1. **WHAT?** → `NODE_PATH` / `ELEMENT_TYPE`
2. **WHERE?** → `PARENT_NODE_PATH`
3. **ONE OR MANY?** → `IS_COLLECTION`
4. **WHICH ONE?** → `INSTANCE_KEY_RULE`
5. **WHEN?** → `PROCESS_ORDER`
6. **WHERE ARE THE SOURCE ITEMS?** → `ITEM_PATH`
7. **HOW DO I BUILD IT?** → `OPERATOR`
8. **DOES IT NEED A UUID?** → `UUID_POLICY`
9. **DO I HAVE EVERYTHING REQUIRED?** → `REQUIRED_MEMBERS`

The Python engine provides reusable building mechanics. The registry tells those mechanics how each OSCAL structural node behaves.

---

# Example 1 — SSP Metadata

Live registry concept:

```text
NODE_PATH          = system-security-plan.metadata
ELEMENT_TYPE       = metadata
PARENT_NODE_PATH   = system-security-plan
IS_COLLECTION      = FALSE
INSTANCE_KEY_RULE  = SINGLETON
PROCESS_ORDER      = 2
ITEM_PATH          = null
OPERATOR           = object
UUID_POLICY        = omit
REQUIRED_MEMBERS   = null
```

Translate the entire row into one sentence:

> **Build one Metadata box inside the SSP box.**

Now decode it:

### WHAT?

```text
NODE_PATH    = system-security-plan.metadata
ELEMENT_TYPE = metadata
```

We are building the Metadata structural node.

### WHERE?

```text
PARENT_NODE_PATH = system-security-plan
```

Metadata lives directly under the SSP root.

Picture:

```text
System Security Plan
└── Metadata
```

### ONE OR MANY?

```text
IS_COLLECTION = FALSE
```

Metadata is one object under one SSP, not an array of Metadata objects.

### WHICH ONE? — `SINGLETON`

```text
INSTANCE_KEY_RULE = SINGLETON
```

`SINGLETON` means there is only one instance under that parent, so no ContentId, user ID, source value, etc. is needed to distinguish Metadata A from Metadata B.

Conceptually:

```json
{
  "system-security-plan": {
    "metadata": {
      "title": "..."
    }
  }
}
```

Not:

```json
"metadata": [
  {...},
  {...}
]
```

Easy memory rule:

> **SINGLETON = one box; there is nothing to choose between.**

### WHEN?

```text
PROCESS_ORDER = 2
```

The parent/root must exist before its child. Process order gives the generic builder a deterministic construction sequence.

### WHERE ARE THE SOURCE ITEMS? — `ITEM_PATH`

```text
ITEM_PATH = null
```

Metadata itself is not being expanded from a source collection at this structural level, so there is no item extraction path required.

`ITEM_PATH` is **not the OSCAL path**. `NODE_PATH` is the OSCAL structural path. `ITEM_PATH` tells the execution engine where individual source items are found when a source value needs collection/item extraction.

Easy memory rule:

> **NODE_PATH = where it belongs in OSCAL. ITEM_PATH = where its individual items are found in the source value.**

### HOW DO I BUILD IT? — `OPERATOR`

```text
OPERATOR = object
```

The generic mapper uses a reusable object assembler for this node.

Think of `OPERATOR` as selecting the correct tool from a toolbox.

Examples in the lean execution contract include:

```text
object
record
observations
properties
values
references
roles
parties
assignments
```

Instead of hardcoding Python like:

```text
if metadata: special code
if parties: another special block
if components: another special block
```

the shared engine asks the registry:

> **Which reusable builder should handle this node?**

Examples:

```text
props[]      -> properties builder
system-ids[] -> values builder
parties[]    -> parties builder
components[] -> references behavior where configured
```

Easy memory rule:

> **OPERATOR = which tool do I use to build this box?**

### DOES IT NEED A UUID? — `UUID_POLICY`

```text
UUID_POLICY = omit
```

For this structural Metadata node, the framework does not add a payload UUID under this policy.

The lean contract supports policies such as:

```text
omit
node
instance
```

Plain English:

- `omit` → do not emit a payload UUID for this structural element.
- `node` → use deterministic identity associated with the structural node policy.
- `instance` → generate/use deterministic UUID identity for each keyed collection instance.

Why deterministic? If the same source entity is processed again, references should continue to point to the same logical OSCAL entity instead of receiving a random identity on every run.

Easy memory rule:

> **UUID_POLICY = does this box/person/item need an OSCAL identity, and at what identity level?**

### DO I HAVE EVERYTHING REQUIRED? — `REQUIRED_MEMBERS`

```text
REQUIRED_MEMBERS = null
```

There is no special atomic completeness rule configured for the Metadata structural node.

Easy memory rule:

> **REQUIRED_MEMBERS = don't build the package until these pieces are present.**

---

# Example 2 — Parties

Picture:

```text
SSP
└── Metadata
    └── Parties[]
        ├── Party A
        ├── Party B
        └── Party C
```

Now the answers are different:

```text
WHAT?       Parties
WHERE?      Under Metadata
ONE/MANY?   Many
WHICH ONE?  Identify each party using the configured instance key
ITEM PATH?  Source collection/item location such as UserList[] where configured
HOW?        parties assembler
UUID?       deterministic instance UUID where configured
```

Why isn't this `SINGLETON`?

Because one Metadata object can contain multiple parties. The builder must distinguish one party from another.

That is the purpose of `INSTANCE_KEY_RULE` on a collection.

---

# Example 3 — `props[]`

Suppose the registry contains:

```text
system-security-plan.system-characteristics.props[]
```

and:

```text
OPERATOR = properties
```

Plain English:

> **There may be multiple OSCAL properties here. Use the shared property assembler rather than writing System-Characteristics-specific Python.**

The mapping CSV determines which approved source fields target those properties; the registry determines how that structural collection is assembled.

Important: a field should not be mapped to `props[]` merely because the generic mapper supports properties. Semantic approval still comes from mapping review/SME evidence.

---

# Example 4 — Security Impact Level and `REQUIRED_MEMBERS`

The registry has a `security-impact-level` structural object with a required-members rule for the CIA security objectives.

Conceptually:

```json
{
  "security-impact-level": {
    "security-objective-confidentiality": "...",
    "security-objective-integrity": "...",
    "security-objective-availability": "..."
  }
}
```

The required-members rule tells the assembler that this object is treated atomically under the current mapping contract.

Plain English:

> **Before I build the CIA box, make sure the required CIA pieces are available.**

This prevents the generic engine from blindly emitting a structurally incomplete atomic object under the configured contract.

---

# What `INSTANCE_KEY_RULE` is really solving

For every node, the engine needs to answer:

> **If I see this again, is it the same thing or another thing?**

Examples:

### Singleton

```text
Metadata
System Characteristics
System Implementation
```

There is one structural instance under the SSP root.

### ID / ContentId / source-field identity

Collections need identity. A rule such as ID, CONTENT_ID, VALUE, or a configured source-field combination tells the engine how to distinguish instances.

Conceptually:

```text
Party ID 100 -> Party A
Party ID 200 -> Party B
```

or:

```text
ContentId 573482 -> referenced component/control/etc.
```

The exact configured rule must be read from the live registry; do not assume all collections use the same key.

---

# Registry vs Mapping CSV — do not confuse them

This is critical.

## Mapping CSV answers:

> **Which Archer field goes to which OSCAL target, and what transformation does it use?**

Example concept:

```text
Archer SECURITY_CATEGORY
    -> SSP security-impact target
    -> approved transform
```

## Registry answers:

> **How is that OSCAL structural node built and identified?**

So:

```text
CSV      = WHAT SOURCE DATA GOES WHERE
Registry = HOW THE TARGET STRUCTURE BEHAVES
Python   = REUSABLE MECHANICS THAT EXECUTE BOTH
```

This is why adding a normal approved mapping should usually be metadata/configuration work rather than writing another model-specific Python block.

---

# The shortest memory version

When looking at a registry row, say this aloud:

> **What am I building? Where does it go? One or many? How do I tell instances apart? Where are the source items? Which builder do I use? Does it need a UUID? Do I have all required pieces?**

Or even shorter:

```text
WHAT
WHERE
ONE/MANY
WHICH ONE
SOURCE ITEMS
HOW
UUID
REQUIRED
```

If those eight questions make sense, the registry row makes sense.

---

# Current evidence boundary

This guide explains the current lean registry contract documented in the repository and the live SSP registry screenshot/read-back supplied on 2026-09-15.

It does **not** claim that every registered SSP branch is semantically OSCAL-complete. Profile/import-profile and Control Implementation remain separately deferred/under review based on newer source-owner evidence. Registry presence is structural/runtime configuration, not proof that a mapping is semantically approved or currently populated.
