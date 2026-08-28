Yep — this confirms it. The mapper currently sees only 2 active registry nodes in the component branch:

components[]              True   CONTENT_ID   $   order 3
components[].component    False  CONTENT_ID   $   order 4

So props[], links[], responsible-roles[], and protocols[] are not entering element_registry_df at all. That is why the fresh run still gives only the existing component branch.

Next step — don't change mapper code

We need to activate those four registry rows first.

Run this SQL SELECT only so we verify their current status before changing anything:

SELECT
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
  AND NODE_PATH IN (
    'system-security-plan.system-implementation.components[].component.props[]',
    'system-security-plan.system-implementation.components[].component.links[]',
    'system-security-plan.system-implementation.components[].component.responsible-roles[]',
    'system-security-plan.system-implementation.components[].component.protocols[]'
  )
ORDER BY PROCESS_ORDER, NODE_PATH;

Send me that output.

Don't UPDATE anything yet. I want to verify IS_ACTIVE, ITEM_PATH, parent, and process order before we activate them. This is the exact next step.