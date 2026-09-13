# Eight-hour delivery candidate — September 13, 2026

The owner authorized continued changes while away and requested tested code on
GitHub within eight hours. The maintained seven-cell candidate has passed all
769 local tests. The normal mode remains PREVIEW, with writes disabled. This is
a tested deployment candidate; live Snowflake acceptance is still unavailable.

## Changes after the 749-test checkpoint

- CSV parsing now rejects malformed quotes instead of swallowing later mapping
  rows. Valid multiline notes and literal strings remain supported.
- Source bindings resolve real Snowpark quoted identifiers, including exact case
  and escaped quotes. The obsolete mapping DataFrame upload is removed; mapping
  inspection remains local, and execution continues to use MAPPING_INPUTS.
- Source selection ranks by the configured technical ordering, collapses equal
  latest identity/payload pairs, and rejects conflicting latest payloads. It no
  longer relies on a hash of JSON serialization. Duplicate identities without
  an approved ordering still fail before mapping. This is a deliberate behavior
  correction: conflicting latest ties now require a source ordering correction.
- Cell Three uses the registry decoder's validated paths and identities once,
  removing duplicate checks and unreachable routing branches.
- Linked roles, parties and assignments use ordered identity dictionaries, which
  preserve reviewed output order and avoid repeated list scans. A failed graph
  build no longer leaves stale party values available to a retry.
- Loader comparison logic is shared. The transaction function expresses its
  single DIM/FACT pass directly, retaining rollback and unknown-outcome handling.
- Pipeline failures now report the actual failed source/model group, retain
  confirmed writes after a post-commit readback failure, and record cancellation.

The earlier cached-plan upgrade fix, retired metadata rejection, accepted field
mappings, registry identity recipes and frozen parity fixtures remain intact.

## Verification

- **769 tests passed**, no errors, failures or skips, in **20.032 seconds** on
  Python 3.12.14 / pandas 3.0.1.
- **2,209 supported-metadata differential cases** match prior output types,
  errors, routing reports and input immutability.
- **729 linked-identity differential cases** match prior outputs and diagnostics.
  A separate regression reproduces and fixes stale data after a failed build.
- Twenty additional regression tests cover input ambiguity, malformed CSV,
  quoted columns, linked identities, failed retries and persistence reporting.
- Accepted SSP, CIA11, AR17 and metadata-only future-model checks remain passing.
  Historical expected outputs and frozen engines were not rewritten.
- Independent review found no blocking issue in the compiler, transformer,
  loader and orchestration changes. Source transport behavior was checked against
  official documentation; local tests still substitute the Snowpark transport.
- Generated split/combined notebook synchronization and whitespace checks pass.
- The preceding checkpoint, af639853f8c9543f025d89b547321c6b02993a29, passed the
  new pinned GitHub workflow. Publication and CI for this final candidate must
  be verified against its own commit before claiming the remote result.

The input correction follows Snowflake's documented unpredictable object-key
ordering in [TO_JSON](https://docs.snowflake.com/en/sql-reference/functions/to_json),
using [DENSE_RANK](https://docs.snowflake.com/en/sql-reference/functions/dense_rank)
and native [DISTINCT](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.DataFrame.distinct).
Identifier handling follows [DataFrame.columns](https://docs.snowflake.com/en/developer-guide/snowpark/reference/python/latest/snowpark/api/snowflake.snowpark.DataFrame.columns).

## Size and remaining work

| Cell | Before this task | Delivery candidate |
| --- | ---: | ---: |
| Configuration | 231 | 220 |
| Inputs | 176 | 182 |
| Mapping | 951 | 886 |
| Transformations | 1,275 | 1,197 |
| Graph | 164 | 165 |
| Loader | 879 | 869 |
| Orchestration | 183 | 181 |
| **Physical lines** | **3,859** | **3,700** |
| **Nonblank/noncomment lines** | **3,416** | **3,263** |

This removes 159 physical lines in this task and 562 from the earlier 4,262-line
draft. The notebook remains far larger than the original 860-line version. The
owner's substantial simplification target has not been achieved; do not describe
this as a lean rewrite or use local tests as production certification.

No source query, database write, registry modification or live notebook run was
performed. Live registry setup and the daily preview/commit/persistence/readback
path remain pending, and Assessment Results has no verified destination. The
historical SSP row-count discrepancy is unchanged. A successful local or GitHub
test run does not resolve those deployment requirements.

Next action: verify publication and CI for this candidate, continue any meaningful
remaining simplification from this tested checkpoint, and obtain live acceptance
in the intended Snowflake environment before enabling writes. The one-time
delivery check is scheduled for September 13 at 08:04 America/New_York.
