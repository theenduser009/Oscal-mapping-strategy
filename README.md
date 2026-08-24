Yes — **before we touch another OSCAL model, this is worth doing.** Let’s look at the actual curated graph we built: SSP UUID → parent UUID → child UUID → JSON.

Run this as a **read-only SQL query**:

```sql
SELECT
    p.SOURCE_RECORD_ID,

    /* Root SSP for this Archer record */
    root.OSCAL_UUID                         AS SSP_OSCAL_UUID,

    /* Parent node */
    p.ELEMENT_TYPE                         AS PARENT_ELEMENT_TYPE,
    p.OSCAL_UUID                           AS PARENT_OSCAL_UUID,

    /* Relationship from FACT */
    f.DEPENDENCY_TYPE,

    /* Child node */
    c.ELEMENT_TYPE                         AS CHILD_ELEMENT_TYPE,
    c.OSCAL_UUID                           AS CHILD_OSCAL_UUID,

    /* Actual node payloads */
    p.METADATA_JSON                        AS PARENT_JSON,
    c.METADATA_JSON                        AS CHILD_JSON

FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
    ON f.FK_SOURCE_ELEMENT_HASH
     = p.PK_OSCAL_SSP_ELEMENT_HASH

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
    ON f.FK_TARGET_ELEMENT_HASH
     = c.PK_OSCAL_SSP_ELEMENT_HASH

JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT root
    ON root.SOURCE_RECORD_ID = p.SOURCE_RECORD_ID
   AND root.ELEMENT_TYPE = 'system-security-plan'

ORDER BY
    p.SOURCE_RECORD_ID,
    PARENT_ELEMENT_TYPE,
    CHILD_ELEMENT_TYPE,
    CHILD_OSCAL_UUID;
```

This gives you **all 2,165 SSPs**, not just one sample.

For one `SOURCE_RECORD_ID`, you should see something conceptually like:

```text
SOURCE_RECORD_ID: 565187
SSP UUID: abc123...

system-security-plan   abc123...
    │
    ├─ parent_of → metadata
    │              UUID = def456...
    │
    │              ├─ parent_of → document-ids
    │              │              UUID = ...
    │              │
    │              └─ parent_of → responsible-parties
    │                             UUID = ...
    │
    ├─ parent_of → system-characteristics
    │              UUID = ...
    │
    │              ├─ authorization-boundary
    │              ├─ security-impact-level
    │              ├─ status
    │              ├─ props
    │              └─ system-ids
    │
    └─ parent_of → system-implementation
                   UUID = ...
                   │
                   └─ components
                      UUID = ...
```

And importantly, the query lets you see the **actual JSON beside each node**. So you can prove visually that:

```text
FACT FK_SOURCE_ELEMENT_HASH
        ↓
parent DIM row / UUID
        ↓ parent_of
child DIM row / UUID
        ↓
child JSON
```

For collections you will naturally see many rows. For example, one SSP may have:

```text
system-implementation UUID X
    → component UUID A
    → component UUID B
    → component UUID C
    → ...
```

while all those rows still carry the same `SSP_OSCAL_UUID` at the top.

**Run this query next and show me a screenshot of a few rows.** Then I can walk you through one real SSP from root → child → grandchild using the exact UUIDs and JSON from your tables.
