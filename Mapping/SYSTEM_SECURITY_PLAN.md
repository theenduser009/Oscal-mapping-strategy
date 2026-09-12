# System Security Plan Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 64 | `INFORMATION_CLASSIFICATION` | `system-security-plan.system-characteristics.props[]` | Extension Property | Visible note recommends mapping to system-characteristics properties; define the property name and namespace. |
| 65 | `DAILY_LOSS_AMOUNT_FROM_OUTAGE` | `system-security-plan.system-characteristics.props[]` | TBD | The screenshot note says `All Nulls`; do not map until populated source data and business meaning are confirmed. |

## Validation gate

Keep row 65 excluded while it remains entirely null. Approve the row 64 property name, namespace, datatype, and allowed values before enabling writes.
