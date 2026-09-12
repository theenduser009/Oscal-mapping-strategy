# Security Assessment Plan Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 61 | `REQUEST_TO_BEGIN_ASSESSMENT` | `security-assessment-plan.tasks[]` | Extension Property | Define whether this creates a task or a namespaced task property. |
| 62 | `APPROVAL_TO_BEGIN_ASSESSMENT` | `security-assessment-plan.tasks[]` | Extension Property | Define whether this creates a task or a namespaced task property. |
| 63 | `PREASSESSMENT_REVIEW_COMMENTS` | `security-assessment-plan.tasks[].remarks` | Extension Property | Needs analysis. |

## Validation gate

Define task identity, timing, dependency, and status semantics before registering these rows as task nodes.
