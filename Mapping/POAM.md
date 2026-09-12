# POA&M Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 6 | `POAMS` | `plan-of-action-and-milestones.poam-items[]` | Reference | Link to POA&M item UUIDs in the POA&M model. |

## Validation gate

Resolve the referenced POA&M item by deterministic UUID and verify that every reference has a matching POA&M node before enabling writes.
