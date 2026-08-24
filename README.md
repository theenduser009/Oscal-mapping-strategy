Yes — there are several strong ways to test the FACT table beyond simply joining parent and child. Since we now have **92,880 DIM nodes and 90,715 FACT edges**, I’d run one independent integrity audit directly against the curated tables.

### Run this next — FACT integrity audit

```sql
WITH EDGE_AUDIT AS (

    SELECT
        f.PK_FACT_OSCAL_DEPENDENCY_HASH,
        f.FK_SOURCE_ELEMENT_HASH,
        f.FK_TARGET_ELEMENT_HASH,
        f.DEPENDENCY_TYPE,

        f.SOURCE_OSCAL_UUID,
        f.TARGET_OSCAL_UUID,

        p.OSCAL_UUID        AS PARENT_DIM_UUID,
        p.ELEMENT_TYPE      AS PARENT_TYPE,
        p.SOURCE_RECORD_ID  AS PARENT_RECORD_ID,

        c.OSCAL_UUID        AS CHILD_DIM_UUID,
        c.ELEMENT_TYPE      AS CHILD_TYPE,
        c.SOURCE_RECORD_ID  AS CHILD_RECORD_ID

    FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY f

    LEFT JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT p
        ON f.FK_SOURCE_ELEMENT_HASH =
           p.PK_OSCAL_SSP_ELEMENT_HASH

    LEFT JOIN RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT c
        ON f.FK_TARGET_ELEMENT_HASH =
           c.PK_OSCAL_SSP_ELEMENT_HASH
)

SELECT '1_ORPHAN_PARENT' AS TEST,
       COUNT(*) AS ISSUE_COUNT
FROM EDGE_AUDIT
WHERE PARENT_DIM_UUID IS NULL

UNION ALL

SELECT '2_ORPHAN_CHILD',
       COUNT(*)
FROM EDGE_AUDIT
WHERE CHILD_DIM_UUID IS NULL

UNION ALL

SELECT '3_PARENT_CHILD_DIFFERENT_SOURCE_RECORD',
       COUNT(*)
FROM EDGE_AUDIT
WHERE PARENT_RECORD_ID <> CHILD_RECORD_ID

UNION ALL

SELECT '4_SELF_REFERENCE',
       COUNT(*)
FROM EDGE_AUDIT
WHERE FK_SOURCE_ELEMENT_HASH = FK_TARGET_ELEMENT_HASH

UNION ALL

SELECT '5_PARENT_UUID_MISMATCH',
       COUNT(*)
FROM EDGE_AUDIT
WHERE SOURCE_OSCAL_UUID <> PARENT_DIM_UUID

UNION ALL

SELECT '6_CHILD_UUID_MISMATCH',
       COUNT(*)
FROM EDGE_AUDIT
WHERE TARGET_OSCAL_UUID <> CHILD_DIM_UUID

UNION ALL

SELECT '7_INVALID_DEPENDENCY_TYPE',
       COUNT(*)
FROM EDGE_AUDIT
WHERE DEPENDENCY_TYPE <> 'parent_of';
```

For our design, ideally everything should return:

```text
TEST                                      ISSUE_COUNT
----------------------------------------------------
1_ORPHAN_PARENT                           0
2_ORPHAN_CHILD                            0
3_PARENT_CHILD_DIFFERENT_SOURCE_RECORD    0
4_SELF_REFERENCE                          0
5_PARENT_UUID_MISMATCH                    0
6_CHILD_UUID_MISMATCH                     0
7_INVALID_DEPENDENCY_TYPE                 0
```

These tests prove different things. `ORPHAN_PARENT/CHILD` proves both FKs resolve to DIM. The source-record check proves we didn't accidentally connect children belonging to another Archer Authorization Package. The UUID checks are especially useful because FACT stores UUIDs as well as hashes — they prove that the hash FK and UUID describe the **same actual node**. Self-reference catches a node pointing to itself.

There is another very powerful test after this: **root reachability**. We can start from every `system-security-plan` root and recursively follow FACT to prove that every child/grandchild node is reachable through the graph:

```text
SSP
 → metadata
    → responsible-parties[]
 → system-characteristics
    → status
    → props[]
 → system-implementation
    → components[]
```

That would test the FACT table as an actual **graph**, not merely FK integrity.

Run the audit above first. If all seven are `0`, then I recommend we do the recursive root-to-leaf test next — that's probably the strongest proof that the FACT design is working correctly.
