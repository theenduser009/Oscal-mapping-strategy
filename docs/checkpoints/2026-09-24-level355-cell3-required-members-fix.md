# Level-355 Cell 3 REQUIRED_MEMBERS fix — 2026-09-24

## Owner-provided live evidence
After the Level-355 registry setup and first CONTROL_NUMBER mapping were prepared,
Cell 3 stopped during registry compilation with:

`ValueError: REQUIRED_MEMBERS requires scalar object member paths`

The error occurred because the existing compiler allowed `REQUIRED_MEMBERS`
only on non-collection `object` operators. The new
`implemented-requirements[]` branch intentionally uses the generic
`joined-records` collection operator and requires `control-id`.

## Correction
Cell 3 now permits `REQUIRED_MEMBERS` for:
- scalar non-collection `object` operators, preserving existing behavior;
- collection `joined-records` operators, where the joined-record builder
  already validates required payload members per child instance.

The existing scalar-object optional-assembly behavior is unchanged.

Files updated:
- `notebooks/cells/03_canonical_mapping_contract.py`
- `notebooks/cells_v2/03_canonical_mapping_contract.py`

No mapping CSV, registry, source or target data was changed by this fix.

## Next action
In the same notebook session:
1. refresh/pull the latest Cell 3;
2. rerun Cell 3 only;
3. if the route compiles READY, run Cells 4, 5, 6 and 7 with Cell 7 in PREVIEW mode.

Cells 1 and 2 do not need to be rerun if their latest Level-355 source/lookup setup
already completed successfully in the current session.
