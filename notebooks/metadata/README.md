# Reviewed mapper metadata

This artifact makes the active seven-cell mapper metadata-driven. It does not add an eighth execution cell. Upload `mapper_contract.v1.json` to Snowflake notebook Files alongside the approved mapping CSV, and deploy the matching seven cells. Cell One refuses a missing/invalid catalog and never fetches remote code or metadata automatically.

## Which input owns what?

| Input | Responsibility |
| --- | --- |
| Original Excel/CSV mapping rows | Archer source field, OSCAL model, target path, mapping type, Notes and original business intent. Preserved without mutation. |
| Live element registry | Active nodes, parent paths, collection flags, instance-key rules and processing order. |
| Reviewed JSON catalog | Executable choices previously recorded in Python: transform identifiers/parameters, element operators, property/reference names, controlled values, source bindings and verified storage contracts. Existing sheet rows must match their reviewed rules. |
| Shared Python | Generic parsing, transformations, registry traversal, keys, validation, guarded persistence and reporting. It does not select active mappings by hardcoded field/model names. |

The catalog is a reviewed deployment artifact, not a replacement for business approval. Existing SSP and accepted AR17 choices were migrated without expanding scope. Historical field-specific Python now lives only in a frozen test fixture; it is not imported or uploaded by the seven-cell workflow. Earlier standalone diagnostics that depend on that dispatcher are historical and refuse active metadata contexts.

### One generated executable specification

Cell Three generates `compiled_plan` from the approved mapping rows, registry and reviewed supplements. The daily engine interprets that plan; it does not choose a second SSP/AR implementation. The plan is generated in memory, not another file to maintain. Original Notes are never executed or interpreted as code.

The catalog is **not automatically synchronized from Excel**. It still contains approved executable choices for legacy rows whose sheet has only prose. For new rules, prefer explicit executable columns in the mapping artifact. Do not create conflicting copies of a rule: when migrating a reviewed legacy rule to the sheet, retire its supplementary rule in the same reviewed metadata release. Unknown meaning remains a clarification, not an inferred transformation.

## Adding an approved mapping

### Registry-first routing

Model ownership comes from active registry paths, including paths for models not enabled for execution. Recognized labels cross-check that ownership; a conflicting known label blocks, while an unfamiliar display label does not override a registered path. Original sheet labels and paths remain unchanged in the artifact and traceability fields.

The catalog's `ROUTING` section declares placeholder model labels and target paths. They are deferred, never treated as approved mappings. The currently evidenced labels are `TBD`, `N/A - Calculated`, and `Multiple - See Notes`; target placeholders also include `All Nulls`. A TBD row with a real SSP path remains deferred. Unreviewed rows follow the existing `UNREVIEWED_ROWS` policy, even if their model is not configured. Explicitly approved rows with unresolved ownership still block.

No special Profile or Assessment Plan executor or field-name rule was added. If the registry identifies another model's path, it is outside the selected route. If no registry ownership exists and the row is unapproved, it stays deferred rather than being mapped by inference. Required accepted mapping identities and genuine label/path conflicts still fail closed. Routing-only recognition does not populate `SELECTED_MODELS` or approve storage.

Reports identify `ROUTING_POLICY: registry-first-v1`, preserve exact disposition counts, and include original model labels/paths in bounded issue samples. This avoids requiring another label-extraction diagnostic for a future routing failure.

For an existing supported model/operator, add the approved Excel/CSV row with these executable columns, or add its exact reviewed rule to `MAPPING_RULES` in the catalog:

- `APPROVAL_STATUS`: `APPROVED`.
- `TRANSFORM_ID`: a supported reusable transformation below.
- `TRANSFORM_PARAMS`: JSON object; use `{}` when none.
- `REPRESENTATION_PARAMS`: JSON object, such as an explicitly approved property name or reference type.
- Optional `VALUE_CONSTRAINTS`: JSON object defining required values, null policy, cardinality and validation, as below.
- Optional `RULE_ID` for stable review traceability; optional `REPRESENTATION` must match the owning element's operator.

Source field, model, original target path and mapping type are still required. The compiler resolves the owner from the registry. Notes remain business evidence, never executable Python. Unreviewed rows are deferred under the current Source One policy; selected rows with invalid or conflicting executable metadata block the group. Existing reviewed rules cannot be overridden by changing a CSV transform or constraint alone; revise the governed release deliberately.

For legacy rows without executable columns, a single matching approved catalog rule supplies those choices. Matching checks the original field/path/type and any specific Notes constraints. Required AR17 rule identities must occur exactly once. Unreviewed Source One rows are reported deferred, not silently mapped. The all-null unresolved rule remains `BLOCKED_IF_POPULATED` and rejects populated values.

## Adding another model or source

### Declarative value constraints

Example for an approved direct numeric value (not a new business mapping):

```json
{
  "required": true,
  "null_policy": "reject",
  "cardinality": {"min": 1, "max": 1},
  "validation": {"type": "number", "minimum": 0, "maximum": 100}
}
```

Constraints run after transformation and before payload construction. A scalar or object counts as one; an array counts its members; an omitted value counts as zero. Cardinality describes this row's converted value, not all graph descendants. `max: null` means unbounded. `required: true` requires at least one value. `null_policy` is `omit` (default) or `reject`, covering absent/null/empty values omitted by the selected transform; it does not invent an OSCAL null property or change upstream CURATED_JSON null preservation.

Validation supports whole-value `type` (`string`, `integer`, `number`, `boolean`, `object`, `array`), `enum`, and finite numeric `minimum`/`maximum`. Bounds do not coerce text to numbers; zero and false are present values. Numeric constraints require JSON-native finite integers/floats, not Decimal objects that the existing graph serializer would stringify. A model requiring native JSON numbers can explicitly configure `RUNTIME_OPTIONS.parse_decimal: false`; do not change accepted score parsing automatically. Enum compares JSON representations, distinguishing nested booleans and numbers. Enum values and unknown constraints are checked during compilation. No executable expressions are allowed. Existing rows without these optional constraints retain accepted behavior. Failed validation prevents publishing a partial graph or committing it; an untracked failure is raised, never silently skipped.

### Model/source onboarding

1. Supply approved source-to-model bindings and an unambiguous mapping artifact/source-column binding in `SOURCES`.
2. Add the model key, root/aliases, `POLICY: metadata-v1`, element operators and reviewed mapping rules in `MODELS`.
3. Confirm the live registry has the correct parents, collections and instance identities.
4. Select that model through Cell One's single `SELECTED_MODELS` setting.
5. Keep its storage contract empty until actual target tables, physical types and provenance are verified. Graph preview is allowed; COMMIT is not.

No source-field or model-name branch is needed for supported behavior. The local tests include a third synthetic model and a never-seen source field through the actual common builder. Unsupported shapes/transforms require a reusable capability plus tests; the engine does not guess them.

## Supported execution vocabulary

Transforms: `direct`, `text`, `canonical-text`, `timestamp`, `date`, `identifier`, `archer-select`, `scalar-score`, `security-objective`, `status-crosswalk`, `reject-populated`, `skip`.

Element operators: `object`, `record`, `properties`, `values`, `observations`, `references`, `roles`, `parties`, `assignments`.

Operators define reusable semantics; metadata selects them. Named properties require a literal `property_name` or an explicit element-level `source-field-slug` naming rule. Crosswalks are data. Required values, optional assembly behavior and controlled configuration/source values are data. Unknown identifiers, incompatible registry identities and ambiguous paths block execution.

Collection parent keys support declared singleton/source-record/no-parent policies. The existing SSP default materializes only singletons without collection ancestors; nested singleton materialization requires explicit metadata. Hydrated reference routes preserve their reviewed array-root shape and require declared lookup bindings; software descriptions remain mandatory. Null handling preserves accepted model behavior without inventing values.

## Preserved boundaries

- One generic graph builder and guarded writer; deterministic source/model-scoped identities, PK/FK checks and repeat-write safeguards remain.
- No metadata SQL/Python evaluation, automatic model approval, schema writes, daily truncation or guessed deletion policy.
- Source One SSP plus AR17 only are configured. Candidate/deferred/rejected AR rows remain outside accepted scope.
- SSP's earlier full DEV reload remains accepted. The old-row reduction is still unexplained.
- AR storage remains unverified. Local parity is not live persistence or complete OSCAL conformance.

See [shared workflow and next preview](../../docs/SHARED_SEVEN_CELL_MAPPER.md) and [current status](../../docs/CURRENT_STATUS.md).
