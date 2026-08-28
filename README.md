Perfect. This is exactly the baseline result we wanted.

After replacing Cell 5:

Nodes = 59,232 — unchanged

Edges = 56,419 — unchanged

Null/duplicate keys = 0

Missing parents/children = 0

Validation = PASSED

Writes = False


So the Cell 5 replacement did not break the existing SSP graph. Great.

Next step — activate ONE deeper branch only

Do not activate all four children yet. Let's test only:

system-security-plan.system-implementation.components[].component.props[]

Run this SQL:

UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
SET IS_ACTIVE = TRUE
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH =
      'system-security-plan.system-implementation.components[].component.props[]';

Then verify:

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
  AND NODE_PATH LIKE '%components%';

Don't run Cell 7 yet.

Send me the result of that SELECT. I specifically want to verify props[]'s PARENT_NODE_PATH, INSTANCE_KEY_RULE, and ITEM_PATH before we let the mapper process it. We are finally isolating this one variable at a time.