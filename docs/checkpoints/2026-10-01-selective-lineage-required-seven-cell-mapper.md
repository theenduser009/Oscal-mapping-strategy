# Selective LINEAGE_REQUIRED seven-cell mapper checkpoint

Date: 2026-10-01
Branch: simplify-metadata-boundary
Repository head before checkpoint: 6594812ed9dfd195c369cc3943c1c68f9efeb65e
Status: IMPLEMENTED IN REPOSITORY; FOCUSED CI TESTS PASSED; NOT YET OWNER-RUN IN SNOWFLAKE.

## Owner decision implemented

Use one simple mapping-sheet flag:

LINEAGE_REQUIRED = Y | N

Default/missing behavior is N.

The mapping sheet, not Python field-name branches, decides whether a successful
native mapping also needs source-field lineage.

## Current SSP System Characteristics scope

12 rows are Y:
- OPERATIONAL_STATUS
- RECOMMENDED_CONFIDENTIALITY_CONTROL_CATEGORY
- CONFIDENTIALITY_CONTROL_CATEGORY_OVERRIDE
- RECOMMENDED_INTEGRITY_CONTROL_CATEGORY
- INTEGRITY_CONTROL_CATEGORY_OVERRIDE
- PROGRAMSITE_INTEGRITY_CONTROL_CATEGORY
- AVAILABILITY_CONTROL_CATEGORY_OVERRIDE
- RECOMMENDED_AVAILABILITY_CONTROL_CATEGORY
- PROGRAMSITE_AVAILABILITY_CONTROL_CATEGORY
- CNSS_AVAILABILITY_RATING
- CNSS_CONFIDENTIALITY_RATING
- CNSS_INTEGRITY_RATING

Every other current row is N in this first pass.

## Business props remain business props

Approved rows whose actual target is props[] continue to emit the business
property itself. They do not receive duplicate lineage merely because a lookup
or transformation occurred.

Examples:
- FISMA_REPORTABLE -> fisma-reportable
- FINANCIAL_SYSTEM -> financial-system
- MISSION_CRITICAL -> mission-critical
- CRITICAL_INFRASTRUCTURE -> critical-infrastructure
- PIA_REQUIRED -> pia-required

Missing/null source values remain omitted under the existing null policy, so an
empty source does not create an empty property just to advertise the mapping.

## Runtime changes

Cell 1:
- release marker updated only.

Cell 2:
- unchanged intentionally. The generic CSV loader already carries the new column.

Cell 3:
- removed automatic ambiguity/joined-record lineage selection;
- compiles lineage only from LINEAGE_REQUIRED=Y;
- validates Y/N;
- rejects Y on CONFIG, skip/guard, or business-prop/observation destinations.

Cell 4:
- keeps contribution capture tied to successful mapped assignments;
- one shared property constructor now supports optional class;
- report key is LINEAGE_PROPS rather than LINEAGE_GROUPS.

Cell 5:
- emits exactly one namespaced source-field prop per selected surviving
  contribution;
- class is the native member name;
- no target-path prop, grouping prop pair, target UUID, joined-source expansion,
  or automatic joined-field lineage;
- nearest valid props owner is used without crossing a repeated collection;
  unsafe placement is reported as a lineage gap.

Cell 6:
- unchanged intentionally. Existing loader/transaction/obsolete-row/readback
  protections remain intact.

Cell 7:
- release compatibility marker updated;
- existing COMMIT block on lineage gaps remains.

Generated cells_v2 files and the combined notebook were synchronized from the
maintained seven-cell source.

## Focused validation actually performed

GitHub Actions run 36888977082:
- generated-notebook synchronization check: PASS
- 9 selective-lineage tests: PASS
  - Y emits one source-field prop
  - N emits no extra prop
  - business prop is not duplicated as lineage
  - missing source emits no lineage
  - Y rejects business-prop and CONFIG rows
  - invalid flag rejects
  - missing namespace fails closed when lineage is emitted
  - two selected sources feeding one native member preserve both source names
  - current mapping CSV has exactly the intended 12 Y rows

The overall maintained repository suite is still red: 40 failures and 76 errors.
This checkpoint does not claim a clean release gate. Those broader failures
include historical fixture/compatibility debt and must be reconciled separately;
the focused selective-lineage tests above are green.

## Expected effect on the owner's prior SSP PREVIEW

The prior broad-lineage PREVIEW reported 202,593 NO_REGISTERED_PROPS_OWNER gaps
from joined Control Implementation fields. Those rows are now LINEAGE_REQUIRED=N
and the runtime no longer auto-selects joined fields for lineage.

Therefore the next SSP PREVIEW should no longer create those Control
Implementation lineage gaps. This is an expected result from the new metadata
and code, not yet owner-run evidence.

## No live-write claim

No Snowflake DML or new owner PREVIEW was performed from this chat after this
change. Do not treat GitHub commits or focused CI as database acceptance.

## Next action

Run one SSP PREVIEW only with the current seven cells and current mapping CSV.
Check:
- PREVIEW_COMPLETE
- writes_executed=false
- LINEAGE_GAPS=0
- LINEAGE_COMPLETE=true
- lineage sample contains only fields marked LINEAGE_REQUIRED=Y
- existing business props remain unchanged and no empty props are manufactured.

Do not COMMIT until that bounded PREVIEW is reviewed.
