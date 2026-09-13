# POA&M reference mapping

The owner confirmed the existing Source One worksheet row:

| Archer field | Source | OSCAL path | Mapping type |
| --- | --- | --- | --- |
| POAMS | ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW.CURATED_JSON | plan-of-action-and-milestones.poam-items[] | Reference |

The official path uses **milestones**, plural. The maintained CSV preserves
the reviewed row and Notes; only its execution metadata is enabled.
No second Archer source table or item-detail lookup is required for this scope.

## What this increment builds

The existing references operator extracts scalar ContentIds or ContentId
members from reference objects, deduplicates within one authorization package,
and builds UUID-only item nodes with root-to-item CONTAINS edges. Null, missing
and empty references emit no item. Source IDs, model, registry path and item
identity feed the existing deterministic hashes; run IDs and list order do not.
The same ContentId in two packages remains two package-scoped graph identities,
consistent with the existing SSP/AR identity standard. This does not resolve
UUIDs belonging to a separate external POA&M document.

No component type, title, description, status, date or alternate source field
is invented. This is the approved reference graph, not a complete POA&M
document: populated poam-items require additional members in the
[NIST OSCAL 1.2.3 definition](https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/plan-of-action-and-milestones/json-definitions/).
Graph validation does not establish complete document conformance.

The same seven cells are maintained. Cells Three and Four use compiled-plan
release lean-csv-registry-v2; replace them together and rebuild contexts.
Typed/hydrated SSP references preserve their existing behavior. Hydration still
requires REFERENCE_TYPE. A known unselected model cannot block SSP/AR merely
because its registry rows are absent; conflicting known path ownership still
blocks. The loader and key/UUID algorithms are unchanged.

## Current next action

Run [READ_ONLY_POAM_INPUTS.sql](../notebooks/validation/READ_ONLY_POAM_INPUTS.sql)
as **SQL in a Snowflake worksheet** and post its three result grids. It requires
no notebook globals. It returns candidate POA&M destination columns, existing
POA&M registry rows, and aggregate POAMS container/reference shapes. It changes
nothing. Empty metadata results are limited by the role and configured schema;
they do not prove absence elsewhere. Counts are physical source reference slots,
not deduplicated package/item counts.

The [POA&M registry update](../sql/registry/ENABLE_POAM_REFERENCE_METADATA.sql)
is prepared for the existing root and item rows. Inspect the registry result
first. It sets only their execution metadata and the collection ITEM_PATH
needed by the existing references operator; it creates or resets no registry.
It stops on missing, duplicate, inactive or conflicting rows.

After registry preparation, upload the updated
[CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv), copy the updated
[seven cells](../notebooks/cells/README.md), set Cell One
SELECTED_MODELS = ("POAM",), and run Cells One through Seven with shared
EXECUTE_WRITES false and Cell Seven OSCAL_LOAD_MODE = "PREVIEW".
Cell Three must report READY with one selected POAMS row. Until the actual
POA&M target names and physical definitions are bound, Cell Seven can only
report MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING. This is not a write.

Bind the confirmed POA&M DIM/FACT and PK names using the owner's shared SSP
physical standard before a target-aware preview or COMMIT. No table names,
table recreation or production write are inferred. SSP and AR accepted
commits remain accepted and need no repeated run.

## Validation scope

Focused tests cover reference payloads, deterministic identity, deduplication,
null/malformed inputs, links and rejection of stale plans/unverified writes.
SSP/AR regression and generated-cell checks accompany this change. The private
screenshot check covers the readable empty-reference example only; no populated
POAMS screenshot example or complete source dataset has been executed.
SQL preparation and local tests are not evidence of live POA&M acceptance.
