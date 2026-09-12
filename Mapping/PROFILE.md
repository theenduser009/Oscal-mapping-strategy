# OSCAL Profile Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 10 | `ADD_OVERLAY` | Multiple — see notes | Extension Property | The visible note describes conditional routing among profile imports, merge behavior, and modify/alters depending on the field's behavior and whether tailored control changes are present. |
| 33 | `BASELINE_RECOMMENDATION` | `profile.imports[]` | Extension Property | Use as a profile import only after resolving it to an approved catalog/profile reference. |

## Validation gate

Define the exact semantics of `ADD_OVERLAY` first. Do not generate profile structure until the source values unambiguously distinguish import, merge, and modify/alter behavior.
