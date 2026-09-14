# Profile: source and import decision

September 14, 2026. The owner selected Profile as the next model, superseding
the previous suggested order. This is input discovery, not a runnable Profile
package. Both reviewed CSV mappings remain deferred; no Profile model route,
registry execution rules, target schema or runtime changes were activated.

The owner's expanded notes are now posted in
[Profile notes evidence](https://github.com/theenduser009/Oscal-mapping-strategy/blob/847cfa09f406a850cb1c857f611a093a26219431/Mapping/PROFILE_NOTES_EVIDENCE.md).
They confirm the conditional import/merge/modify meanings and an illustrative
baseline import. They do not contain actual Source One field values or a
baseline-to-resource lookup. Do not ask the owner to repost these notes.

| Source field | Existing mapping | Needed to implement |
| --- | --- | --- |
| ADD_OVERLAY | Multiple destinations described in original notes | Actual values and meaning: flag, named overlay, or tailored control changes; any intended control selection |
| BASELINE_RECOMMENDATION | profile.imports[] | Baseline value to approved catalog/profile URI, and whether to include all controls or a selected subset |

The [NIST Profile definition](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_profile_metaschema.xml)
requires imports to reference a catalog/profile through href and select controls
through include-all or include-controls. Merge and modify are separate optional
operations. A baseline label or yes/no flag alone does not identify that resource
or those operations. The example URI in old transcribed notes is not an approved
catalog reference. The example's root id also is not a substitute for the
required Profile uuid; preserve the note as provenance, not executable JSON.

Run [READ_ONLY_PROFILE_INPUTS.sql](../notebooks/validation/READ_ONLY_PROFILE_INPUTS.sql)
in a Snowflake SQL worksheet to inspect distinct source-value combinations and
their datatypes. The query reads stored RAW versions, so its counts are not the
retained, deduplicated mapper population. NULL type can indicate an absent field;
NULL_VALUE means explicit JSON null. Check IS_OBJECT_DOCUMENT before interpreting
field absence. The top 30 combinations are a sample, not exhaustive coverage.
Keep the result values private. No source-value result has been received yet.

The source fields were not found in the saved private text excerpts searched for
this review. This does not mean the original screenshot collection lacks them;
no complete screenshot re-review or Profile example test has been performed.

Existing object/record/values operators may support approved structured imports;
the ContentId references operator is not a URI lookup. The current VALUE_MAP
belongs to status-crosswalk and is not a generic baseline resolver. Any needed
extension should be one reusable operation after the source contract is known,
while retaining the same seven cells. No catalog URI, control selection, overlay
meaning, or default import is inferred from the two field names.

Prior SSP/AR acceptance and pending SAP/POAM verification remain as documented
in PROJECT_WALKTHROUGH. This discovery query has not been run against Snowflake.
