Yes — here’s a clean architect-level question you can send:

> For mappings marked as Reference, such as system-security-plan.system-implementation.components[], the Archer source field does not contain the actual component payload. It only contains a LevelId and ContentId. LevelId identifies the referenced Archer content/table, and ContentId identifies the specific record in that table.

Should our OSCAL mapper resolve that reference at runtime by first using LevelId to determine the source table, then using ContentId to retrieve the referenced record and build the OSCAL component node? Or do you prefer that reference resolution happen upstream so the mapper receives an already-expanded record?

Also, should the initial components[] node represent just the Archer reference, or should it only be created after the referenced record has been resolved?



That question gets directly to the architectural decision: resolve inside the mapper vs resolve upstream, and reference node vs fully materialized OSCAL node.