# Lean registry runtime checkpoint

Date: 2026-09-12

## Outcome

The maintained mapper no longer depends on the eighteen-column registry
extension. Cell One identifies the lean registry release and Cell Three compiles
the mapping CSV with the original nine registry columns plus only three sparse
execution rules:

- `OPERATOR`
- `UUID_POLICY`
- `REQUIRED_MEMBERS`

The other fifteen experimental columns are not read by the active notebook.
The revised registry setup does not drop them if an earlier DEV attempt created
them; it leaves them untouched and ignores them.

The mapping CSV remains the field-mapping authority. The original registry
columns remain the hierarchy and instance-identity authority. Cell Three derives
parent-instance behavior, property naming, reference-family links, report target
and enabled path closure rather than storing duplicate policy columns.

## Preserved behavior

- Exact accepted SSP graph digest is unchanged.
- All eleven accepted CIA transforms remain unchanged, including complete-only
  security-impact assembly.
- All seventeen accepted Assessment Results outputs remain unchanged.
- A third synthetic model and new field still execute through metadata only.
- The compiled-plan interface consumed by Cells Four through Seven is unchanged.
- Normal mapper writes remain disabled.

## Compactness result

The release also removes duplicate normalization and loader compatibility code
without changing the public seven-cell workflow:

- Cell Four: 1,527 to 1,468 executable lines; duplicate registry parsing moved
  behind Cell Three's single validated boundary.
- Cell Six: 864 to 804 executable lines and 40 to 35 functions; SSP-only loader
  constants and redundant projection helpers were removed.
- Total: 3,956 to 3,837 executable lines across Cells One through Seven.

The remaining Cell Four code is reachable from the active graph engine or its
callbacks. Its larger sections implement tested transformations, hydration,
identity and integrity behavior, so they were not deleted merely to reduce LOC.

## Verification

The synchronized maintained cells, V2 pages and combined notebook pass all 697
local tests. Focused metadata, routing, release, migration, binding, SSP digest,
CIA11, AR17, future-model, hydration, typed-graph and guarded-loader tests also
pass. Local tests do not prove Snowflake execution or authorize DIM/FACT writes.

## Database boundary

No Snowflake statement was run by this change. No registry, DIM or FACT data was
changed. The revised three-column SQL is prepared but not live-verified. If the
previous eighteen-column setup succeeded in DEV, those extra nullable columns
may remain; the lean runtime does not use them.

## Current action

Run the published lean three-rule registry setup once in a fresh DEV worksheet
and share its aggregate result. Keep the seven-cell notebook on PREVIEW and
normal writes disabled until that setup is verified.

