# AR30 metadata extension - September 13, 2026

The owner selected AR next after the accepted SSP no-change COMMIT/readback.
This release enables 13 conflict-free, previously approved alternative-path
score mappings through the existing scalar-score transform and observations
operator. The maintained CSV now selects 30 AR fields and 48 SSP rows.
No runtime cell or registry rule changes; all seven cells remain 1,838 lines.

## Evidence and scope

- [Existing business approval](../ASSESSMENT_RESULTS_START_HERE.md#approved-alternative-path-batch---seventeen-more-fields-pending-live):
  one observation per source field with a named inline scalar property.
- [Exact next-run scope and deferred decisions](../AR_NEXT_RUN.md).
- Exactly 13 CSV rows change execution metadata. Original source names, paths,
  Notes and provenance remain unchanged; all other CSV lines are preserved.
- Two threshold-source names differ from the historical approval and stay
  deferred, together with the two parked shape rejections, seven workflow
  rows, two average-score rows, inherent risk and findings.
- AR17 stays live accepted in memory. The 13 additions are pending live
  acceptance; three had no populated historical candidate evidence.
- AR persistence and full model conformance are not accepted by this release.

## Verification

- 51 focused tests passed with no skips: exact scope/provenance, independent
  earlier-mapper output, original SSP/AR17 parity, old key/edge preservation,
  scalar precision/zero/false, null omission and invalid-value rejection.
- Full local suite: 182 reported, OK with three class-level skips because the
  installed Snowpark localtest dependency is absent from the local runtime.
  GitHub CI requires that dependency and rejects missing-package skips.
- Frozen transform comparison retains all original 1,403 cases and adds 299
  cases for the 13 new fields; immutable fixture hashes remain enforced.
- The notebook integration assertion is updated to require 48 SSP/30 AR rows.
- Notebook synchronization check and whitespace check pass.
- No live Snowflake run, target DML or registry change was performed here.

Read the published commit's GitHub checks for the installed-Snowpark result.
The next user run is the AR30 PREVIEW in [AR next run](../AR_NEXT_RUN.md).
