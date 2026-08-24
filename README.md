Yes — this is the important discovery. We **definitely have deeper mapped SSP structure**, and now we can add it to the registry based on the actual mapping/data rather than guessing.

From what you showed, I can confirm these three deeper singleton nodes:

```text
system-security-plan.system-characteristics
│
├── authorization-boundary
│   └── description
│
├── security-impact-level
│   ├── security-objective-availability
│   ├── security-objective-confidentiality
│   └── security-objective-integrity
│
└── status
    ├── state
    └── remarks
```

Fields such as these remain payload fields of `system-characteristics`, not separate DIM nodes:

```text
date-authorized
description
security-sensitivity-level
system-name
system-name-short
```

And we already have:

```text
props[]
system-ids[]
```

So **next step is registry only**. Add the three confirmed singleton objects:

```sql
MERGE INTO RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY t
USING (

    SELECT
        'SSP' AS OSCAL_MODEL_KEY,
        'system-security-plan.system-characteristics.authorization-boundary' AS NODE_PATH,
        'authorization-boundary' AS ELEMENT_TYPE,
        'system-security-plan.system-characteristics' AS PARENT_NODE_PATH,
        FALSE AS IS_COLLECTION,
        'SINGLETON' AS INSTANCE_KEY_RULE,
        3 AS PROCESS_ORDER,
        TRUE AS IS_ACTIVE,
        NULL AS ITEM_PATH

    UNION ALL

    SELECT
        'SSP',
        'system-security-plan.system-characteristics.security-impact-level',
        'security-impact-level',
        'system-security-plan.system-characteristics',
        FALSE,
        'SINGLETON',
        3,
        TRUE,
        NULL

    UNION ALL

    SELECT
        'SSP',
        'system-security-plan.system-characteristics.status',
        'status',
        'system-security-plan.system-characteristics',
        FALSE,
        'SINGLETON',
        3,
        TRUE,
        NULL

) s

ON  t.OSCAL_MODEL_KEY = s.OSCAL_MODEL_KEY
AND t.NODE_PATH = s.NODE_PATH

WHEN MATCHED THEN UPDATE SET
    t.ELEMENT_TYPE      = s.ELEMENT_TYPE,
    t.PARENT_NODE_PATH  = s.PARENT_NODE_PATH,
    t.IS_COLLECTION     = s.IS_COLLECTION,
    t.INSTANCE_KEY_RULE = s.INSTANCE_KEY_RULE,
    t.PROCESS_ORDER     = s.PROCESS_ORDER,
    t.IS_ACTIVE         = s.IS_ACTIVE,
    t.ITEM_PATH         = s.ITEM_PATH

WHEN NOT MATCHED THEN INSERT (
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH
)
VALUES (
    s.OSCAL_MODEL_KEY,
    s.NODE_PATH,
    s.ELEMENT_TYPE,
    s.PARENT_NODE_PATH,
    s.IS_COLLECTION,
    s.INSTANCE_KEY_RULE,
    s.PROCESS_ORDER,
    s.IS_ACTIVE,
    s.ITEM_PATH
);
```

Notice I am **not** registering:

```text
security-objective-availability
security-objective-confidentiality
security-objective-integrity
```

as separate nodes. They are mapped properties **inside `security-impact-level`**, so they'll live in that node's JSON.

Same reasoning:

```text
authorization-boundary.description
```

belongs inside the `authorization-boundary` node.

And:

```text
status.state
status.remarks
```

belong inside the `status` node.

This is exactly the parent/child normalization we wanted:

```text
DIM:
system-characteristics
authorization-boundary
security-impact-level
status

FACT:
system-characteristics → authorization-boundary
system-characteristics → security-impact-level
system-characteristics → status
```

Run this registry MERGE only. Then refresh Cell 3 and run Cell 5 unchanged. **Do not run Cell 6 yet** — first we inspect the new node counts and make sure the hierarchy was generated correctly.
