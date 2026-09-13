# POA&M Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 6 | `POAMS` | `plan-of-action-and-milestones.poam-items[]` | Reference | Link to POA&M item UUIDs in the POA&M model. |

## Validation gate

Resolve the referenced POA&M item by deterministic UUID and verify that every reference has a matching POA&M node before enabling writes.

## Current implementation - 2026-09-13

The owner reconfirmed Source One and this Reference row. Its CSV execution
metadata now builds UUID-only, package-scoped item nodes with root-to-item
links through the shared references operator. Every emitted UUID equals its
matching graph node UUID. Item details and external-document UUID resolution
are outside this increment. Live registry/destination verification and preview
remain pending; see [POA&M next run](../docs/POAM_NEXT_RUN.md).
