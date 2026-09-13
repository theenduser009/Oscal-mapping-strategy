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

## Targets and preparation

The owner confirmed the SSP/AR physical definition and the same POAM naming
pattern. Cell One now binds these tables in
RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED:

| Table | Primary-key column |
| --- | --- |
| DIM_OSCAL_POAM_ELEMENT | PK_DIM_OSCAL_POAM_ELEMENT_HASH |
| FACT_OSCAL_POAM_DEPENDENCY | PK_FACT_OSCAL_POAM_DEPENDENCY_HASH |

DIM retains all ten columns, including both TIMESTAMP_TZ(9) audit columns.
FACT retains its six columns and source/target foreign-key hashes. The
BINARY(16) hashes, stored UUID32 format and package-scoped identity are the
same as SSP/AR. VERIFIED in config identifies the selected contract; the
existing loader still validates the actual live schema before any target DML.

Run these two SQL files in a Snowflake worksheet outside an active transaction:

1. [CREATE_POAM_TABLES.sql](../sql/CREATE_POAM_TABLES.sql) creates missing POAM
   tables and displays both definitions. Existing tables and rows are preserved.
   It does not repair an existing mismatched definition.
2. [ENABLE_POAM_REFERENCE_METADATA.sql](../sql/registry/ENABLE_POAM_REFERENCE_METADATA.sql)
   checks the existing two POAM registry rows and updates their execution
   metadata and collection ITEM_PATH. Success is POAM_REFERENCE_METADATA_VERIFIED.
   It creates or resets no registry and stops on missing/conflicting rows.

Then upload the updated [CSV](../Mapping/ARCHER_OSCAL_MAPPINGS.csv), copy the
matching [seven cells](../notebooks/cells/README.md), and use:

~~~python
# Cell One
SELECTED_MODELS = ("POAM",)

# Cell Seven
OSCAL_LOAD_MODE = "PREVIEW"
~~~

Keep shared EXECUTE_WRITES false. Run Cells One through Seven to rebuild the
POAM contexts. Cell Three must report READY with one selected POAMS row;
Cell Seven must report PREVIEW_COMPLETE with the POAM group status
PREVIEW_PASSED_NO_TARGET_DML, storage/pre-write validation true, and no writes.
Post that report for the first live POAM acceptance. COMMIT/readback remain
pending this live check. No SSP/AR rerun or table replacement is requested.

The earlier [read-only input SQL](../notebooks/validation/READ_ONLY_POAM_INPUTS.sql)
is available if diagnosis is needed; it is not a request to reconfirm the names
the owner has now specified. No live DDL, registry update or POAM load has been
executed by this code change.

## Validation scope

[CI passed all 205 tests with no skips](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34773274346)
on the prior reference-only code commit ad41b4fabe569ddc4d1d32c9e2192f572f4f7cad. This included eleven
focused POA&M cases and a real Snowpark VARIANT graph test; generated pages match.
Focused tests cover reference payloads, deterministic identity, deduplication,
null/malformed inputs, links and rejection of stale plans/unverified writes.
SSP/AR regression and generated-cell checks accompany this change. The private
screenshot check covers the readable empty-reference example only; no populated
POAMS screenshot example or complete source dataset has been executed.
SQL preparation and local tests are not evidence of live POA&M acceptance.

The storage binding adds an all-seven-cell POAM preview/insert/unchanged/new-reference
readback test that also preserves populated SSP/AR destinations. Current local
checks pass; the installed-Snowpark CI run for this binding is pending.
