# Security Assessment Plan Mapping

Source: screenshot review of the `archer_to_oscal_mapping` worksheet.

| Row | Exact Archer field name | OSCAL element path | Mapping type | Notes |
|---:|---|---|---|---|
| 61 | `REQUEST_TO_BEGIN_ASSESSMENT` | `security-assessment-plan.tasks[]` | Extension Property | Define whether this creates a task or a namespaced task property. |
| 62 | `APPROVAL_TO_BEGIN_ASSESSMENT` | `security-assessment-plan.tasks[]` | Extension Property | Define whether this creates a task or a namespaced task property. |
| 63 | `PREASSESSMENT_REVIEW_COMMENTS` | `security-assessment-plan.tasks[].remarks` | Extension Property | Needs analysis. |

## Validation gate

Define task identity, timing, dependency, and status semantics before registering these rows as task nodes.

## Current execution decision

The owner requested these three fields be mapped. The original table above is
source transcription; the executable CSV now uses assessment-plan.tasks[].props[]
for the two single-value picklists and assessment-plan.tasks[].remarks for review
comments. One Preassessment review task per source record is the common parent.
Task identity is source-record based; property identity is source-field based.
Explicit nulls are preserved, while missing keys remain absent. No workflow
status, timing or dependency is inferred. See [SAP next run](../docs/SAP_NEXT_RUN.md).
