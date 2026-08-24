Right now, for SSP, we are **2 structural levels below the SSP root**, and some mapped JSON fields go **one level deeper inside those nodes**.

```text
Level 0  system-security-plan
│
├── Level 1  metadata
│      ├── Level 2  document-ids[]
│      │      └── Level 3  identifier          ← JSON field
│      └── Level 2  responsible-parties[]
│
├── Level 1  system-characteristics
│      ├── Level 2  authorization-boundary
│      │      └── Level 3  description         ← JSON field
│      ├── Level 2  security-impact-level
│      │      ├── Level 3  confidentiality
│      │      ├── Level 3  integrity
│      │      └── Level 3  availability
│      ├── Level 2  status
│      │      ├── Level 3  state
│      │      └── Level 3  remarks
│      ├── Level 2  system-ids[]
│      │      └── Level 3  id
│      └── Level 2  props[]
│
└── Level 1  system-implementation
       └── Level 2  components[]
```

So there are **two different answers**:

**DIM/FACT graph depth:** currently through **Level 2**.
Example:

```text
SSP
→ system-characteristics
→ status
```

`status` is a DIM node and both arrows are FACT relationships.

**Mapping/payload depth:** currently reaches **Level 3** in places.
Example:

```text
SSP
→ system-characteristics
→ status
→ state
```

But `state` is not another DIM node; it lives inside the `status` JSON.

And here's the key: **we have not yet proven from the raw Archer data that Level 3 is the deepest SSP-related data available.** We only proved it is the deepest level represented by the SSP mappings we've processed so far.

So the next comprehensive audit should answer:

```text
Actual Archer data
     ↓
all SSP-related mapped fields
     ↓
Level 0
Level 1
Level 2
Level 3
Level 4?
Level 5?
...
```

That's the audit I would do next. If we discover something like:

```text
Level 2 implemented-requirements[]
    → Level 3 statements[]
        → Level 4 by-components[]
```

then we'll know we need to extend the registry and, importantly, handle **collection → collection lineage** generically.

**Current proven point: structural Level 2, mapped leaf Level 3.**
