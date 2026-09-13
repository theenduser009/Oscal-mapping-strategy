# Seven-cell lean rebuild

The owner requested a substantial reduction across every cell, using the
shorter pasted notebook as the starting point. The maintained implementation
now contains **1,802 physical lines**, down from **3,700**: **1,898 lines removed
(51.3%)**. This count includes comments and blank lines. Nonblank, noncomment
lines total 1,591. Production code does not import a replacement framework or
any test fixture.

| Cell | Purpose | Physical lines |
| --- | --- | ---: |
| 1 | Visible configuration | 90 |
| 2 | Frozen source selection, CSV and lookups | 149 |
| 3 | Approved mapping and registry contracts | 439 |
| 4 | Shared transforms and element assembly | 572 |
| 5 | Nodes and parent-child edges | 81 |
| 6 | Validation, preview, transactional upsert and readback | 387 |
| 7 | Build, preview all routes, optionally commit | 84 |

## Why it is smaller

The runtime accepts the maintained CSV format and the three active registry
extensions. It no longer carries alternate JSON metadata formats, arbitrary
value-constraint objects, serialized plan caches, historical compatibility
globals or detailed per-field reporting machinery. Required values are checked
when mapped, linked collections are assembled together, and the graph is
validated at the load boundary. The loader supports the reviewed physical
schema directly rather than negotiating multiple unproved schemas.

The maintained CSV is unchanged: 151 rows, including the existing support
rules; 47 SSP and 17 AR executable rules. Deferred/excluded rows do not become
approved because the code is shorter. Registry ownership, deterministic keys
and UUIDs, calendar dates, Archer selections, decimal scores, atomic C-I-A
emission, responsible-party links and partial component hydration are retained.
Component lookup queries use batches of at most 1,000 requested identifiers.

`run_oscal_mapping` returns nodes, edges and load result. Cell 7 stores graphs
in `MODEL_GRAPHS` and prints aggregate `PIPELINE_REPORT`. The default selection
is SSP and the default mode is PREVIEW. AR is selectable for graph preview;
its destination contract is still absent.

## Validation

The initial rebuild was published as
[a28059de](https://github.com/theenduser009/Oscal-mapping-strategy/commit/a28059de728533f12faf6b553dd261b068ac0e98).
[GitHub checks #4](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34738888719)
passed all 105 tests, including all five installed Snowpark smoke cases, in
4.820 seconds. The published Git tree matched the local tested index.

The final compiler review added three regressions: collection metadata cannot
silently suppress document IDs through an unsupported atomic-assembly rule;
malformed repeated path separators reject; and an invalid SSP target does not
block an independently selected AR route. These fixes do not add runtime lines.
The final local suite passes 103 tests (5.383 seconds), with only the absent
Snowpark class skipped. CI adds those five package cases; current checks are
attached to [PR #1](https://github.com/theenduser009/Oscal-mapping-strategy/pull/1).

The new [release suite](../../tests/lean/README.md) exercises fresh cell
definitions. The older private-API suite belongs to the retired engine and is
retained as historical evidence; its former 769-test pass is not claimed for
this rebuild.

- The existing SSP fingerprint matches exactly: 20 nodes and 19 edges.
- AR17 nodes and edges match the independent existing standalone oracle,
  including high-precision decimals and zero.
- 1,403 transformation cases match SHA-256-pinned pre-rebuild code.
- A third model and new source field work through metadata alone.
- Input tests cover snapshotting, conflicting latest rows, quoted columns,
  strict CSV structure and source binding. Lookup tests cover requested-ID
  batching, partial hydration and missing/ambiguous selected references.
- Loader tests cover physical conversions, JSON semantics, record/parent
  scope, empty edges, unchanged-row audit preservation, obsolete-row blocking,
  DIM/FACT rollback, incorrect MERGE counts, lost commit responses and failed
  readback. Runner tests verify every preview precedes the first commit and
  preserve earlier commits if a later route fails.
- Locally, `python -m unittest discover -s tests/lean -q` passes. The installed
  Snowpark test class is skipped because the local package is absent.
- CI requires Snowpark 1.55.0 with local testing and pandas 2.3.3, so missing
  package dependencies fail rather than silently skipping the API smoke.
- Split and combined notebook files are generated from `notebooks/cells` and
  pass the synchronization check. Existing accepted fixture files are unchanged.

Snowpark's local emulator does not execute arbitrary SQL. The five package
smoke cases adapt its documented SQL boundaries and exercise actual DataFrame
APIs; SQLite-based loader tests are separate unit evidence. Neither is proof
of live Snowflake MERGE execution or OSCAL schema conformance.

## Deployment boundary

No Snowflake connection or live database action was available in this task.
Registry setup and daily persistence/readback acceptance remain pending. Use
the [registry setup instructions](../REGISTRY_METADATA_SETUP.md), then verify
PREVIEW in the intended environment. Before COMMIT, pause other target writers:
the baseline comparison detects drift but is not a concurrency lock. The
loader requires the reviewed BINARY(16), compact UUID, VARIANT and TIMESTAMP_TZ
schema. It never deletes obsolete rows; a changed scope blocks for review.
Unknown commit outcomes must be inspected before retrying.

The mapper builds the approved mapped scope. Full OSCAL completeness, the
historical unexplained SSP row difference, AR storage and unapproved fields
remain outside the acceptance claim.
