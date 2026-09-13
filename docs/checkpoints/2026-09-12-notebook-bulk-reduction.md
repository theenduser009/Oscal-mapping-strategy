# Notebook bulk reduction - 2026-09-12

Review candidate continuing the existing draft. Parent: `fa75b3ff19de981f91ffa657f3842a348b3c843d`.
The owner supplied the full original notebook and clarified that actual
readability and size reduction are the objective, without a fixed 500-line cap.

## Measured result

Original: **860 total lines / 669 nonblank, noncomment lines**.
Previous draft: **4,262 / 3,812**.
Updated notebook: **3,859 / 3,416**.
Reduction from previous draft: **403 / 396 lines**.
Against main before the draft: **4,245 / 3,803**.

| Cell | Original code | Previous draft code | Updated code |
| --- | ---: | ---: | ---: |
| 1 | 26 | 209 | 209 |
| 2 | 25 | 149 | 146 |
| 3 | 18 | 924 | 850 |
| 4 | 236 | 1,415 | 1,125 |
| 5 | 171 | 151 | 151 |
| 6 | 159 | 804 | 775 |
| 7 | 34 | 160 | 160 |
| **Total** | **669** | **3,812** | **3,416** |

Code-line counts exclude blank and comment-only lines, but include SQL strings,
data declarations and docstrings. This is a size measure, not a claim of an
equivalent percentage reduction in computational complexity. Sources are the
seven maintained cells; generated copies and test fixtures are excluded.

## What became simpler

- Cell Two reuses the distinct identity count from its frozen snapshot; ranked
  selection already guarantees one output row per identity.
- Cell Three shares CSV/registry scalar parsers, derives collection behavior
  from common operator rules, centralizes routing failure reporting, and groups
  mappings once. Unused declarations and unreachable checks are removed.
- Cell Four shares scalar conversion and aggregate lookup validation. Hydration
  receives approved reference mapping rows and lookup bindings directly; the
  intermediate private hydration-spec object and its repeated reconstruction
  are removed. Query formatting is also shorter and clearer.
- Cell Five calls the existing metadata operations directly, replacing fixed
  callback dispatch. It retains the same node, edge and parent identities.
- Cell Six validates its supported storage types once, shares target comparisons,
  and removes a redundant graph traversal. Strict descendant paths and exactly
  one parent for each non-root already establish rooted reachability.

One narrow correction accompanies the cleanup: unrelated or skipped mappings
sharing a reference source field no longer count as duplicate reference rules.
Duplicate active reference mappings still reject, with a dedicated regression.

## Verification and limits

All **736 local tests pass** in 17.768 seconds using
`python -m unittest discover -s tests -q`, with no failures, errors or skips.
The original draft had 720 passing tests. Active-backend tests exercise lookup
queries, SQL NULL versus JSON null, full lookup-source validation, routed-only
streaming and scalar parity. Loader tests cover storage types, duplicate target
multiplicity and all 220 three-edge graphs over four nodes. Existing accepted
SSP/CIA11/AR17 comparisons and metadata-only future models remain green.

Historical test harnesses now pair the frozen transformer with a byte-equivalent
copy of its previous graph builder. Existing frozen fixtures and expected
outputs were not changed. Current-engine comparisons continue to use the
maintained source. No deployed code imports historical fixtures or moves into
external helper modules. Generated synchronization and whitespace checks pass.
Independent reviews found no blocking issue.

Review before adoption. The mapping CSV, registry SQL, Cells One and Seven,
public runner and guarded loader APIs are unchanged. No Snowflake execution or
database writes occurred. Existing accepted DEV reload and AR17 in-memory
status remain historical evidence; this change has no new live acceptance.
Normal writes remain false. No preview or registry rerun is requested here.
