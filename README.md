Yes — we found the break. 🎯

Look at row 2:

components[]                         IS_ACTIVE = TRUE
components[].component               IS_ACTIVE = FALSE   ← BREAK
component.props[]                    IS_ACTIVE = TRUE
component.links[]                    IS_ACTIVE = TRUE
component.responsible-roles[]        IS_ACTIVE = TRUE
component.protocols[]                IS_ACTIVE = TRUE

That explains your results perfectly.

Cell 2 loads only registry rows where IS_ACTIVE = TRUE. So component disappears from element_registry_df. Cell 5 can therefore create components and some deeper collection nodes such as props, but it cannot build the continuous parent chain:

components
   ↓
component     ← missing from active registry
   ↓
props / links / responsible-roles / protocols

Next action

Activate only the component registry row:

UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
SET IS_ACTIVE = TRUE
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH =
      'system-security-plan.system-implementation.components[].component';

Then verify:

SELECT
    NODE_PATH,
    ELEMENT_TYPE,
    PARENT_NODE_PATH,
    IS_ACTIVE
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH ILIKE '%system-implementation%components%'
ORDER BY PROCESS_ORDER, NODE_PATH;

You should now see all six = TRUE.

After that, do not modify Cells 4, 5, or 6.

Rerun:

Cell 2  ← reloads active registry
Cell 7  ← rebuilds/validates graph

Keep:

EXECUTE_WRITES = False

Then show me Cell 7's node/edge counts or any error.

This was a registry configuration problem, not yet a graph-builder-code problem — which is exactly why checking before changing Cell 5 was important.