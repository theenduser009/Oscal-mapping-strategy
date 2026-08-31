Yes — registry first. You’re right. Before touching timestamp logic, we should see whether those OSCAL nodes are already registered and what their parent/collection rules are.

Run this SQL:

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
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND (
       NODE_PATH = 'system-security-plan.metadata'
       OR NODE_PATH LIKE 'system-security-plan.metadata.%'
  )
ORDER BY PROCESS_ORDER, NODE_PATH;

What I want to check specifically is whether the registry contains separate nodes for:

system-security-plan.metadata
system-security-plan.metadata.published
system-security-plan.metadata.last-modified
system-security-plan.metadata.responsible-parties[]
system-security-plan.metadata.document-ids[]

Run this and show me the result. Then we decide whether published and last-modified are supposed to be standalone registry nodes or simply fields owned by the metadata node. No code changes until we know that.