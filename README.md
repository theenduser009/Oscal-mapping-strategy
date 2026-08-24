Great — now we know the **entire POA&M scope currently present in the CSV**:

```text
SOURCE_FIELD_NAME : POAMS
OSCAL_MODEL       : POA&M
MAPPING_TYPE      : Reference

OSCAL path:
plan-of-action-and-milestones.poam-items[]
```

So, based on the current mapping, the hierarchy is only:

```text
Level 0
plan-of-action-and-milestones

└── Level 1
    poam-items[]
```

There are **no deeper POA&M paths in the CSV right now**. And because `MAPPING_TYPE = Reference`, those `poam-items[]` values are references rather than full POA&M item attributes. From our earlier source inspection, `POAMS` contained lists of `{ContentId, LevelId}` references, and `ContentId` was safe as the instance identity.

### Next step only: check the POA&M registry

We previously experimented with POA&M registry rows, so **do not insert anything yet**. First see what is already registered:

```sql
SELECT
    OSCAL_MODEL_KEY,
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    ITEM_PATH,
    PROCESS_ORDER,
    IS_ACTIVE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY IN ('POAM', 'POA&M')
ORDER BY PROCESS_ORDER, NODE_PATH;
```

Ideally we should already have exactly this:

```text
POAM
plan-of-action-and-milestones
parent = NULL
collection = FALSE
key = SINGLETON

POAM
plan-of-action-and-milestones.poam-items[]
parent = plan-of-action-and-milestones
collection = TRUE
key = CONTENT_ID
item_path = $
```

Show me that result.

Then we can configure the **same production mapper** for POA&M. We will not create another mapping engine. Also, before we actually write to the POA&M tables, we’ll account for the fact that their PK column names are `PK_DIM_OSCAL_POAM_ELEMENT_HASH` and `PK_FACT_OSCAL_POAM_DEPENDENCY_HASH`, rather than the SSP names.
