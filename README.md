Exactly — that explains the behavior.

Because Cell 2 loads registry rows with:

(col("OSCAL_MODEL_KEY") == CONFIG["OSCAL_MODEL"])
& (col("IS_ACTIVE") == True)

those four child nodes are being excluded from element_registry_df. That is why the mapper only built components and not props, links, responsible-roles, or protocols.

The next move is to activate those four registry rows, then rerun from Cell 2 onward.

UPDATE RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
SET IS_ACTIVE = TRUE
WHERE OSCAL_MODEL_KEY = 'SSP'
  AND NODE_PATH IN (
    'system-security-plan.system-implementation.components[].component.props[]',
    'system-security-plan.system-implementation.components[].component.links[]',
    'system-security-plan.system-implementation.components[].component.responsible-roles[]',
    'system-security-plan.system-implementation.components[].component.protocols[]'
  );

Then rerun Cell 2 → Cell 3 → Cell 7. Keep EXECUTE_WRITES = False.

What I expect next is that Cell 7 will either successfully create those child nodes, or it will expose the next real limitation: the collection-parent relationship logic in Cell 5. That is the part we were approaching before.