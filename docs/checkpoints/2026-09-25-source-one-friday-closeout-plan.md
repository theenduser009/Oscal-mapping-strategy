# Source One Friday closeout plan — 2026-09-25

## Repository basis
Branch: simplify-metadata-boundary
Starting head checked: a311dc41005eba5499b53dce787eec2120c1999c
Current mapping CSV blob checked: 766f56d90b1f21c1f59e532fa3dc6225f3e91079

## Current Source One mapping state
Current runtime CSV shows:
- SSP Metadata: 17 APPROVED / 1 DEFERRED
- SSP System Characteristics: 28 APPROVED / 3 EXCLUDED
- SSP System Implementation: 6 APPROVED
- SSP Control Implementation: 20 APPROVED / 10 EXCLUDED / 14 DEFERRED
- System Security Plan: 2 APPROVED
- Assessment Results: 43 APPROVED / 2 DEFERRED
- POA&M: 1 APPROVED
- Security Assessment Plan: 5 APPROVED
- SSP populated-value guard: 1 BLOCKED_IF_POPULATED

Profile evidence from 2026-09-24 showed only two of the 14 remaining Control Implementation deferred fields populated in the current source snapshot:
- INHERITABLE_CONTROLS
- ALLOCATED_CONTROLS_PARTIAL_CONTROL_PROVIDERS

Twelve other Control Implementation deferred fields had no populated values in either profiled Source One dataset.

## Friday closeout sequence
1. Run the new read-only two-array shape query.
2. If either field fits an existing transform/operator, map it with metadata only. Do not add a custom parser merely to force completion.
3. Refresh the daily Source One snapshot once and run all four Source One runtime models together in PREVIEW:
   SSP, ASSESSMENT_RESULTS, POAM, SECURITY_ASSESSMENT_PLAN.
4. If PREVIEW passes and the reported changes are understood, run guarded COMMIT.
5. Capture read-back verification and publish one Source One closeout checkpoint.

## Explicit exceptions that do not justify invented mappings
- Control Implementation fields with no current populated value stay documented as no-current-value deferred.
- Assessment Results FINDINGS remains deferred while Source One contains only empty sentinel values.
- Assessment Results RISK_ASSESSMENT_REPORT remains blocked by the missing approved current-runtime document/resource resolution contract.
- The remaining SSP Metadata Archer-confirmation field has no current-value evidence.
- Profile rows are not part of the Source One runtime model binding.

Completion for Friday means current populated Source One data is mapped or explicitly dispositioned, and the four executable Source One routes have a current PREVIEW/COMMIT/read-back checkpoint. It does not mean every optional OSCAL assembly or future-null source field has been fabricated.
