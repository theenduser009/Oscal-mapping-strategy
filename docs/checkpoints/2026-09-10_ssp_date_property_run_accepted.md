# SSP date/property release — live graph run accepted

Source: the user's [latest Snowflake result](../live-snowflake-results.md),
captured on 2026-09-10 after the property-routing and authorization-date fixes.

| Check | Observed result |
| --- | --- |
| OSCAL model | SSP |
| Graph nodes | 70,102 |
| Graph edges | 67,289 |
| Duplicate node / edge keys | 0 / 0 |
| Dangling source / target edges | 0 / 0 |
| Pre-write validation | Passed |
| Writes enabled / DIM-FACT changes | False / none |
| Hydration lookup rows | 1,435 |
| Interconnection rows / descriptions | 1,428 / 968 |
| Software rows / descriptions | 7 / 7 |

This accepts the latest code release at graph-runtime level, including the
authorization-date handler and eight approved extension-property routes.
It does not assert exact payload equality for every field, universal source
coverage, complete SSP JSON, schema conformance, or production write readiness.

Compared with the earlier 67,671-node / 64,858-edge accepted baseline, nodes
and edges both increased by 2,431. Authorization date is a scalar on an existing
parent and does not itself add nodes. The equal delta is consistent with added
child nodes, but the aggregate output alone does not prove exact per-path
attribution or exclude source changes. No per-field population is invented.

## Next step — assemble the accepted SSP graph

- OSCAL model: **SSP**.
- Active branch: `system-security-plan.system-implementation.components[]`.
- Assembly root: `system-security-plan` (all currently mapped branches).
- Source: accepted Cell 7 in-memory graph, not another Archer field mapping.

Copy the complete [mapped-scope assembler](../../notebooks/validation/RUN_AFTER_07_ssp_mapped_scope_assembly.py)
into one new Python cell and run only it in the same active session. Do not
rerun Cells 1–7, registry setup or diagnostic reports. Keep writes disabled.
Post the complete aggregate output, not source payloads or assembled documents.
If the session restarted, run Cells 1–7 once to recreate the graph first.

No live assembler result is recorded yet. Assembly creates transient JSON from
existing nodes; it does not implement additional mappings or prove whole-SSP
completeness/schema conformance. Every new mapping handoff will identify its
OSCAL model, exact path, Archer field and rule.

## Next ten additional mappings requested

The requested target is ten genuinely additional SSP rows, not recounting
completed code, skipped fields or tests. Current checked-in evidence does not
establish ten more executable contracts:

- The concrete text, metadata, role, impact, component, property and date
  contracts in the register already have handlers.
- Fifty screenshot/audit control rows have blank OSCAL target paths.
- Four additional responsible-party candidates remain TBD.
- Metadata confirmed-in-Archer and recommended-security-category remain
  unresolved; the latter's All Nulls note is not a transform.
- Existing component/source-value gaps are not ten new mapping definitions.

The full mapping CSV is external to the repo. The minimum next input is the
current workbook or SSP-only export retaining Archer field, model, target
path, mapping type, Notes and optional Status. Ten new implementations require
ten additional approved nonblank targets with defined rules. A copy retaining
the same blank/TBD rows will not unlock them. Source payloads are not required
to provide this mapping-contract input.
