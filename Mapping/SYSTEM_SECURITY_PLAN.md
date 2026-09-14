# System Security Plan Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 64 | `INFORMATION_CLASSIFICATION` | `system-security-plan.system-characteristics.props[]` | Extension Property | Visible note recommends mapping to system-characteristics properties; define the property name and namespace. |
| 65 | `DAILY_LOSS_AMOUNT_FROM_OUTAGE` | `system-security-plan.system-characteristics.props[]` | TBD | The screenshot note says `All Nulls`; do not map until populated source data and business meaning are confirmed. |

## Historical validation note (superseded below)

Keep row 65 excluded while it remains entirely null. Approve the row 64 property name, namespace, datatype, and allowed values before enabling writes.


## Owner decision - September 14, 2026

INFORMATION_CLASSIFICATION is already approved. DAILY_LOSS_AMOUNT_FROM_OUTAGE
is now approved at the same system-characteristics properties path using the
existing direct transform and CSV NULL_POLICY=preserve. Explicit source nulls
are retained; a missing key is omitted. The original screenshot notes above
are preserved as provenance and no longer defer this field.

Only the existing CSV execution row changes; the seven runtime cells, registry
and table definitions remain unchanged. See [the daily-loss run guide](../docs/SSP_DAILY_LOSS_NEXT_RUN.md)
for validation and the existing SSP changed-value identity restriction.
