# Props contract and seven-cell simplification roadmap

Date: 2026-09-30
Branch reviewed: simplify-metadata-boundary
Repository snapshot reviewed: 9b44685d81e533dd3b00b8c04ad0b67f3f3940ae
Status: STATIC REVIEW AND PROPOSAL. This checkpoint changes documentation only. No mapper, CSV, registry, database write, new test execution, or live acceptance is claimed.

## Continuity

Read 00_START_HERE.txt and the dated coverage-and-historical-support supplement. Their September 14 evidence is historical, not a current complete registry or database export. Reviewed all seven maintained cells at the snapshot above, the lineage tests, inspection helper, synchronization tool, and prior risk checkpoint.

Preserve the owner decisions: props for portable source attribution, no new lineage fact table, one universal engine, no per-field lineage flags or duplicate CSV rows, and no unnecessary attribution. Other prop and link use cases remain for later discussion.

This roadmap refines 2026-09-30-lineage-props-risk-review.md. It supersedes treating direct mappings as automatically traceable, every populated source as an actual contribution, or nearest-path routing as proof of instance ownership. It does not change accepted mapping dispositions, FIPS/Legacy values, null policies, or existing identity seeds.

## Recommendation

Keep seven cells and current DIM/FACT boundaries. Define one small extension contract, correct shared contribution capture and retrieval, prove the behavior, then remove verified duplication. Do not perform a broad rewrite or run the current broad-lineage candidate in COMMIT mode.

## Every prop must answer what and whose

- Containment identifies the exact owning object instance. Content ID alone identifies a package, not a control, observation, or property.
- name identifies the attribute.
- ns identifies the vocabulary that defines its meaning.
- value supplies that attribute's value.
- class is an optional qualifier, not an automatically lossless path.
- group associates related properties within their owner.
- remarks may explain context but must not hide essential structured identifiers.

Use two immediate purposes: business extensions and source attribution. One generic property constructor can support both. Business meaning remains defined by approved mappings; unapproved fields are not automatically dumped into props.

Keep reusable meaning, units, cardinality, and value interpretation in existing mapping documentation, and generate a readable inventory from metadata. Do not build a second hand-maintained catalog or repeat long descriptions for every source record.

## Proposed precise attribution shape

For the known security-impact case, use two grouped properties at system-characteristics: source-field contains the exact Archer field; target-path contains the exact relative member path. Example only:

```json
{
  "props": [
    {
      "name": "source-field",
      "ns": "urn:company:oscal:lineage:v1",
      "group": "lineage-1",
      "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
    },
    {
      "name": "target-path",
      "ns": "urn:company:oscal:lineage:v1",
      "group": "lineage-1",
      "value": "/security-impact-level/security-objective-integrity"
    }
  ]
}
```

This is a proposed local vocabulary, not a NIST-standard lineage schema or current output. The namespace is the existing development setting; organization approval is still needed. The example group is illustrative. Generate real groups from stable source/rule/owner/target identity, not a changing value, run timestamp, or array index. Do not repeat the native value merely to explain its origin.

Specify relative-path/escaping rules once. Prefer exact owner placement over paths involving unstable array positions. For joined data, carry actual child source/table identity when the document source context is insufficient. Preserve every agreeing contributor; do not invent precedence.

## Eligibility without per-field flags

Only consider contributions to surviving mapped output. Use the versioned mapping to determine whether the exact source is already uniquely recoverable. A direct transform can rename a field, and a hyphenated business-property name can lose exact spelling or prefixes; neither is proof by appearance.

For unambiguous one-to-one mappings, existing mapping definitions can provide source attribution without duplicating it per record. Multiple candidate sources feeding one member require actual per-record contributor evidence. Configuration constants must not be described as Archer fields.

Portability must remain explicit: a consumer holding only an OSCAL file does not automatically have our mapping CSV. To avoid redundant props and still recover exact source names, deliver the relevant versioned mapping definitions once with the export. A standalone-file requirement instead needs an approved embedded representation or the necessary attribution. Do not promise exact recovery while omitting both mapping definitions and source metadata.

## Placement and retrieval

Use the nearest schema-permitted and registered props location without losing the particular target instance. Do not silently attach Requirement A's attribution to a shared package parent. If no valid destination exists, report the distinction between schema prohibition and missing registry coverage.

Current storage includes both separate prop DIM nodes and inline observation props. Reuse the existing representation; do not emit both or create a table/node for every scalar. Build one read-only reader: source context, owner hash/type, namespace, name, group, value, and target where applicable. Join separate props through FACT containment and inspect inline props inside their owner.

The physical DIM contract does not persist all canonical in-memory path and instance columns. Do not select an invented physical ELEMENT_PATH. Derive paths from verified structure or show the unresolved context explicitly.

## Actual code findings and focused changes

1. Cell 1: retain model/source/destination contracts and safe configuration. One global namespace is sufficient. Keep an explicit release boundary; do not quietly mix old compiled state with new helpers.
2. Cell 2: retain frozen source inputs, lookup validation, approved source ordering, and conflict rejection. No source query per generated prop.
3. Cell 3: replace broad _lineage_property_routes selection with one deterministic eligibility/routing plan from existing metadata. Current code uses textual ancestors and silently skips paths without a registered properties operator.
4. Cell 4: replace _lineage_source_is_mapped raw-presence checking with actual successful contribution capture. Keep attribution only for emitted objects/members, including joined-child and inline-property context. One property constructor, not FIPS-specific branches.
5. Cell 5: keep deterministic native node/edge identity and exact parent checks. Attach attribution only after target instance survival is known. Audit unused canonical_mapping_df and legacy registry arguments before removal; current orchestrator passes None for these slots.
6. Cell 6: keep schema, duplicates, source scope, transaction, obsolete-row, rollback, and readback checks. They are not redundant merely because they occur at multiple transaction boundaries. Contributor removal needs scoped reconciliation; current MERGE does not automatically delete old lineage.
7. Cell 7: retain thin orchestration and per-route commit semantics. Keep operator-facing PREVIEW/COMMIT clear and shared EXECUTE_WRITES false. Report concise actionable errors without unrestricted source payloads.

Maintain notebooks/cells as the single source. cells_v2 and the monolithic notebook are generated packaging outputs. Do not hand-edit them independently.

The current lineage preview uses compact JSON substring searches while the serializer emits spaced JSON. Replace them with parsed-key predicates and include inline props. Zero rows from the current text search are not reliable absence evidence.

Current graph validation explicitly reports FULL_MODEL_COMPLETE=false and SCHEMA_VALIDATED=false. Graph consistency is not complete OSCAL document validation or business-semantic acceptance.

## Roadmap and completion gates

1. **Contract:** settle namespace ownership, two property purposes, source/target grouping, exact owner context, and consumer mapping availability. Produce expected examples for direct mapping, business prop, ambiguous native value, and two different collection items.
2. **Shared correction:** implement contribution-aware attribution and parsed-JSON retrieval without per-field toggles, new tables, or native mapping changes. Report unsupported contexts instead of fabricating placement.
3. **Proof:** test one/multiple agreeing contributors, conflicts, missing/null/empty source, skipped transforms, suppressed optional output, repeated instances, joined children, same names in different contexts, inline/separate props, identical reruns, value changes, and removed contributors. No-data is not a mapping pass.
4. **Simplify:** remove verified dead parameters and duplicate work after native-key/payload regression proof. Synchronize generated artifacts. Address relevant red tests; a red baseline is not release approval.
5. **Dev acceptance:** after code gates, inspect the current registry and latest owner evidence, preview representative data, compare native output and additional attribution, then explicitly approve a scoped write and verify readback plus unchanged rerun. Do not repeat already completed SAP/POAM work without checking newer reports. No truncation or bypass of safety guards.

Measure output volume and runtime rather than inventing improvement percentages. Validate relevant fragments and export representation against the pinned model, and complete documents separately when required content exists.

## Deferred decisions

Keep FIPS/Legacy business classification separate from lineage. Preserve explicit null policies; a warehouse null is not automatically a schema-valid OSCAL string. New links need a concrete relationship and resolvable target, not an invented URL from an Archer ID. Do not strip business-unit prefixes or merge fields by naming similarity. Minimize private payloads in logs and exports.

## Evidence

All seven maintained cells, tests/lean/test_universal_lineage_props.py, notebooks/validation/15_ssp_universal_lineage_prop_preview.py, tools/sync_notebook_cells.py, and docs/checkpoints/2026-09-30-lineage-props-risk-review.md were read at the pinned snapshot above. This is a static review, not a fresh test or Snowflake run.

NIST references checked:
- https://pages.nist.gov/OSCAL/learn/tutorials/general/extension/
- https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.3/src/metaschema/oscal_metadata_metaschema.xml
- https://raw.githubusercontent.com/usnistgov/OSCAL/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml
- https://pages.nist.gov/OSCAL/learn/concepts/validation/

Immediate next action: use this proposal to finalize the small expected-output contract, then correct the shared contribution path and reader. No runtime change is authorized or performed by this documentation checkpoint.
