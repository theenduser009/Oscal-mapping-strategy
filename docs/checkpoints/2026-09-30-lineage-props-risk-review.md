# Lineage props risk review before further expansion

Date: 2026-09-30
Branch reviewed: simplify-metadata-boundary
Code commit reviewed: 14340954c0328634cbd72360a5e2b3dada7645e7
Status: Static code/schema review, plus one isolated synthetic Python JSON-formatting probe. No full mapper run, Snowflake run, runtime-code change, registry change, or target DML in this review.

## Continuity and supersession

Read 00_START_HERE.txt first and consulted the dated coverage supplement. Those September 14 sources are historical and do not prove today's database or full registry state.

Preserve the owner decision: portable source-field attribution via props, one reusable mapper, no hand-maintained per-field lineage rows, no unnecessary duplication. Other business-prop and link/href use cases remain for later discussion.

The code reviewed still routes every approved FIELD mapping with a registered enclosing properties collection. The subsequently discussed narrower eligibility rule has not been implemented.

This checkpoint supersedes any interpretation that the earlier five focused tests establish universal correctness, that raw source presence proves actual output contribution, or that nearest path selection proves correct collection-instance ownership. It does not change accepted mapping dispositions or invalidate prior native source-to-target samples.

## Findings from actual source

1. **Broad emission:** Cell 3 `_lineage_property_routes` filters APPROVED/FIELD and chooses a textual ancestor, but has no redundant-lineage eligibility check.
2. **False attribution risk:** Cell 4 `_lineage_source_is_mapped` checks raw presence/null policy rather than the transformed result or surviving output. `_metadata_instances` can separately suppress an optional object when required members are missing. A nonempty source is not proof that the target member was emitted.
3. **Instance scope:** nearest textual path does not enforce staying inside the same repeated requirement, observation, or component. Current lineage keys use RULE_ID; target-instance identity is not recorded by the routing helper.
4. **Joined records:** native joined-record mappings read each child payload, but the lineage helper reads the outer source object. It does not generally prove the correct joined source/table/child supplied the target value.
5. **Silent gaps:** no candidate props path causes `continue`. A schema-disallowed destination must be distinguished from a supported destination missing in the registry.
6. **Target qualifier:** normalizing the canonical path into `class` replaces collection brackets and other characters. The result is not inherently a lossless or NIST-defined target reference.
7. **Lifecycle:** the loader MERGEs inserts/updates and blocks obsolete rows with `OBSOLETE_TARGET_ROWS_BLOCKED`; it does not automatically remove old lineage. Contributor removal and narrowing previously persisted lineage require controlled reconciliation, not a truncation or weakened guard.
8. **Namespace:** `urn:company:oscal:lineage:v1` is an implementation setting, not independently established organization governance or consumer acceptance. The current validation checks a scheme-like prefix, not full governance.
9. **Preview defect:** the preview helper searches compact JSON literals such as `"name":"source-field"`, but Cell 4's default `json.dumps` emits `"name": "source-field"`. An isolated synthetic probe returned false for both compact name/namespace searches and true for parsed-key comparisons. Zero rows from this helper cannot prove missing lineage. Use parsed JSON keys.

## Sources inspected at the pinned commit

- `notebooks/cells/01_initialization_and_configuration.py`, lines 18–35.
- `notebooks/cells/03_canonical_mapping_contract.py`, lines 70–122.
- `notebooks/cells/04_parsing_transform_payload_helpers.py`, lines 18–70, 254–310, 550–610, and 690–812.
- `notebooks/cells/05_registry_graph_builder.py`.
- `notebooks/cells/06_validation_and_guarded_loader.py`, lines 180–350.
- `tests/lean/test_universal_lineage_props.py`.
- `notebooks/validation/15_ssp_universal_lineage_prop_preview.py`.

## Recommended single shared rule

Keep native values native. Record a known source-field contribution when it actually supplies a surviving target member. Emit additional attribution only when exact source identity is not already unambiguously recoverable under the agreed consumer contract. Use the nearest schema-permitted, registered extension point without losing target-instance ownership. Preserve every agreeing contributor; do not invent precedence for conflicting values.

A direct mapping can rename a field. A hyphenated business-property name may not recover exact Archer spelling or prefixes. Do not use apparent naming similarity as proof. A versioned mapping lookup can establish one-to-one provenance for platform consumers, but is not automatically present in an exported OSCAL document. This distinction must remain explicit.

A source-field prop is attribution, not complete immutable ETL history, and it cannot repair an unresolved lookup or an incorrect Legacy-LOE-to-FIPS interpretation.

## NIST findings

OSCAL v1.2.3 permits props and links under system-characteristics. security-impact-level itself has no props collection. control-implementation itself also has no direct props collection; implemented-requirement children do.

Properties use namespaced names and string values. The containing object establishes context. Our source-field vocabulary and target qualifier are local semantics, not a NIST-standard ETL lineage convention.

Links reference local/remote resources; href carries the resource reference. An Archer numeric ID is not automatically a valid resolvable resource reference. Do not manufacture links, URLs, UUIDs, or target relationships merely to fill output. Later link work must establish target type/scope, relationship meaning, actual resolution, authorization, relative-base behavior, version stability, and missing-target handling.

Primary references:
- https://pages.nist.gov/OSCAL/learn/tutorials/general/extension/
- https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml
- https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.3/src/metaschema/oscal_metadata_metaschema.xml
- https://pages.nist.gov/OSCAL/learn/concepts/uri-use/

## Next checkpoint

Before target COMMIT or expansion, validate the shared implementation on: one contributor; several agreeing contributors; conflicting contributors; missing source; suppressed optional output; two repeated instances; joined-source values; identical reruns and contributor removal; parsed-JSON inspection; schema-valid export and documented consumer retrieval.

The five existing focused tests cover direct emission, missing input, nearest registered path, CONFIG exclusion, and missing namespace. They do not establish these additional cases. Do not describe this review as a new full test pass or live acceptance.

Next action: correct and test the shared lineage path and its preview filter for the already identified use case. Keep new business-prop uses and automatic link/href generation out of scope until concrete cases are supplied.
