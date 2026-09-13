# Seven-cell cleanup and verification

The owner requested simpler code across all seven cells, authorized continued
implementation while away, and required full testing. This remains a draft.

## Result and size

This pass removes duplicate runtime state, repeated file reads and repeated
setup. It is a modest cleanup, not the substantial rewrite originally sought.
No transformation rule or identity recipe was removed to reach a line target.

| Cell | Before total | After total | After nonblank/noncomment |
| --- | ---: | ---: | ---: |
| Configuration | 231 | 220 | 198 |
| Inputs | 176 | 171 | 146 |
| Mapping | 951 | 939 | 842 |
| Transformations | 1,275 | 1,270 | 1,120 |
| Graph | 164 | 165 | 152 |
| Loader | 879 | 874 | 770 |
| Orchestration | 183 | 178 | 155 |
| Total | 3,859 | 3,817 | 3,383 |

The total decreases by 42 physical and 33 nonblank/noncomment lines.
Eleven removed lines are ordinary configuration formatting. The mapping,
transform and loader cells remain large; do not call the broader size target met.

## Changes

- Configuration projects verified default targets in one loop.
- Mapping CSV intake opens each file once and uses the standard CSV parser.
  It preserves literal N/A, null, NaN, zero, Unicode and multiline text;
  empty cells stay absent, short rows keep their column alignment, and extra
  columns or duplicate headers reject instead of shifting values silently.
- Registry reference families are built directly, without an intermediate
  family dictionary. Parent parsing and ancestor visits are reused.
- Transform and graph execution share the existing mapping index and read
  options from the compiled plan. Parallel index, options and policy copies
  are removed. Edited plans still validate and rebuild the shared index.
- Preview and commit reporting share their count/validation setup.
- The runner calls the graph builder directly and prints the final report
  in one place on success or failure.

The seven cells remain the maintained runtime; no external implementation
module, new runtime dependency, or field-specific dispatch was added.
Mapping CSV, registry SQL, frozen historical fixtures and accepted values are
unchanged. Normal writes remain disabled.

## Verification

- All **739 local tests pass** in 21.943 seconds, with no failures or skips.
  Environment: Python 3.12.14, pandas 3.0.1.
- The complete suite includes accepted SSP/CIA11/AR17 comparisons,
  metadata-only future models, duplicate/parent identity checks, source
  selection, lookup hydration, required values, transaction failures,
  rollback, unknown commit outcomes, unchanged rows and readback behavior.
- A scratch differential harness compares the prior and current mapping
  compiler across **2,209 cases**, with zero differences in typed outputs,
  reports, exceptions or input mutation. It exercises overlapping routing
  conditions, source/model ownership, inactive registry paths and future models.
- New regressions cover CSV column alignment and blank values, aggregate
  versus immediate error handling, and nonfinite JSON serialization options.
- Generated split and combined notebook synchronization passes.
- GitHub checks run the suite and synchronization check on pull requests and
  main updates. Workflow and dependency versions are pinned; the workflow
  uses no Snowflake credentials or target DML. Remote execution is reported
  separately after publication, never inferred from the local pass.

The workflow follows GitHub's [Python testing documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

## Production limits and next action

No Snowflake connector or open Snowflake browser session is available in this
environment. No source query, registry change, DIM/FACT write or live notebook
run occurred. Local tests use synthetic frames/sessions for database behavior.
This is not live acceptance or full OSCAL conformance certification.

The daily writer still needs live preview and persistence/readback acceptance;
the Assessment Results destination remains unverified. The accepted historical
SSP DEV reload and AR17 in-memory results are unchanged.

Next action: continue the larger simplification from this tested draft, then
verify the resulting candidate in the intended Snowflake environment before
enabling its writes. Do not rerun historical registry cleanup or DEV reload.
