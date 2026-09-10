# SSP — done and next

Updated: 2026-09-10. Our scope follows the Excel Archer field, OSCAL path,
mapping type and Notes. This is the short summary; the
[mapping register](MAPPING_PROGRESS.md) retains the detail.

## Done within the agreed mapping scope

- **Metadata:** implemented mapping work is included in accepted read-only runs.
- **System Implementation:** all six Excel-defined component-reference mappings
  are implemented; the approved partial title/description hydration is accepted.
- **Mapped-scope assembly:** 2,813 SSP documents assembled successfully, with no writes.

## Parked — System Characteristics corrections

Most of the recorded mappings are implemented. The clearer Excel screenshots
identify these two corrections, **not yet coded**:

| Archer field | Exact OSCAL path | Remaining correction |
| --- | --- | --- |
| `HELPER_PTA_CALC` | `system-security-plan.system-characteristics.props[]` | Row 35 is `Calculated`; its Notes say to map it as a custom property. Cell 4 currently skips it. The visible Notes do not define the calculation formula. |
| `PACKAGE_TYPE` | `system-security-plan.system-characteristics.props[]` | The Notes example names the property `authorization-package-type`; the current code emits `package-type`. |

The separate row 36, `PACKAGE_TYPE_HELPER_CALC`, remains excluded: its Notes
explicitly say **Transient calculation field - do not map**. The PTA field is
spelled `HELPER_PTA_CALC`, not `HELPER_PIA_CALC`.

## Parked — Control Implementation

**Control Implementation is not complete.** Its unresolved path/value decisions
remain parked; the proposed control-count mapping is not an approved implementation.

No notebook rerun is needed for this documentation update. Keep writes disabled.
Accepted graph/assembly runs do not prove full SSP completeness or exact agreement
with every Excel row. The owner has now chosen to park SSP and review other
Excel-defined models. The [model/path clarification queue](MAPPING_PROGRESS.md#modelpath-status-and-clarification-queue)
records status, why each item is pending, and additional information needed.

Evidence: the owner's clearer Excel screenshots, rows 27, 35 and 36, reviewed
against [Cell 4](../notebooks/cells/04_parsing_transform_payload_helpers.py).
This supersedes the earlier classification of both helpers as transient.
