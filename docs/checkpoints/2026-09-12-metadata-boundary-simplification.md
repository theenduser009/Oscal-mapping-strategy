# Cells Three and Four metadata simplification - 2026-09-12

Status: locally verified review candidate on `simplify-metadata-boundary`,
based on main commit `fc1c782d5f18b9cd37302a6ec7f88c26c110f017`.
This checkpoint does not establish merge, deployment or live acceptance.

## Result

CSV and registry rows were normalized again during model discovery and routing,
reference-family siblings were searched twice, and runtime preparation repeated
metadata validation and value-constraint compilation already done by the compiler.
Operator identity requirements were also declared separately in Cells Three and Four.

- Normalize inputs once before model discovery and reuse them for routing. The
  public raw-input decoder retains its existing normalization behavior.
- Resolve each reference family once and reuse the result for assembly, retaining
  distinct-path, active-sibling and source-namespace checks.
- Keep one compiled-plan validator and one operator-to-identity rule table in
  Cell Three. Cell Four consumes them and still validates the runtime registry.
- Reuse validation for unchanged compiler output. A serialization-only snapshot
  distinguishes Python types; it is an optimization for trusted in-memory
  metadata, not an authorization boundary. No snapshot is deserialized. Values
  that cannot be serialized fall back to full validation on every use.
- Revalidate edited and independently constructed plans before reading source
  rows. Source-value required/enum checks remain active on every build.

The seven public cells and public compiled-plan keys remain unchanged. This
consolidates responsibility and removes repeated preparation, without a material
reduction in total notebook length. Fixed callback indirection and repeated
loader-candidate preparation are outside this change.

## Verification

Baseline: 700 tests passed. Candidate: **720 tests passed** in 37.952 seconds
using `python -m unittest discover -s tests -q`, with zero failures, errors or
skips. Twenty new regressions cover normalization counts, reference-family
behavior, changed approvals/transforms/owners/parameters, required/enum checks,
deep-copy reuse, list/tuple and bool/integer distinctions, date and uncacheable
provenance, and metadata-only field edits. One existing error-message assertion
now uses the shared identity-rule wording; its rejection behavior is unchanged.

The full suite includes existing SSP, CIA11 and AR17 output parity, metadata-only
future models, routing, identity, PK/FK, idempotency and preview/write safeguards.
Frozen historical fixtures were not changed. Generated notebook synchronization
and whitespace checks pass. Independent review found no remaining blocking issue.

## Scope and next action

Review the candidate diff before adopting it. Cells One, Two, Five, Six and Seven,
mapping CSV, registry SQL, source bindings and write settings are unchanged.
No Snowflake execution or database writes occurred. The accepted SSP DEV reload,
unexplained historical row reduction and AR17 in-memory-only status are unchanged;
the daily writer and prior release preview still need live acceptance.

If this candidate is adopted, replace matching Cells Three and Four together.
No live rerun is requested during this review.
