# Tested seven-cell candidate — September 13, 2026

The owner requested simpler code across all seven cells and full testing.
The candidate is locally verified and remains a draft, with normal writes disabled.

## What changed

The notebook reads mapping CSVs once, shares one mapping index and one set of
runtime options, derives reference groups directly, and calls the graph builder
without an intermediate argument object. Preview and commit reports share setup.

The second pass removes obsolete configuration execution: model settings can no
longer substitute their own element catalog or default elements; the runtime no
longer interprets controlled-field definitions, customizable UUID token recipes,
or hidden property/crosswalk/merge settings. Those options cannot be produced by
the maintained CSV and twelve-column registry. Attempts to supply them now reject
explicitly. Required FIELD/CONFIG values remain normal approved mapping rows.
Supported registry operators, identity recipes and remarks precedence remain.

An independent review reproduced a cached-plan upgrade bug: an old cached plan
could skip the new boundary and silently lose retired fields. Versioned snapshots
now force revalidation; Cell Four rejects a mismatched older Cell Three.

## Size

| Cell | Before this task | Tested candidate |
| --- | ---: | ---: |
| Configuration | 231 | 220 |
| Inputs | 176 | 171 |
| Mapping | 951 | 905 |
| Transformations | 1,275 | 1,207 |
| Graph | 164 | 165 |
| Loader | 879 | 874 |
| Orchestration | 183 | 178 |
| **Total physical lines** | **3,859** | **3,720** |
| **Nonblank/noncomment lines** | **3,416** | **3,290** |

This task removes 139 physical / 126 nonblank/noncomment lines. Against the earlier
4,262-line draft, the cumulative reduction is 542 lines. Configuration formatting
accounts for eleven removed lines. The notebook remains substantially larger than
the original 860-line version; this is not the requested major lean rewrite.

## Verification

- **749 local tests pass**, with no failures or skips, in 19.065 seconds.
- **2,209 differential cases** produce zero differences for the supported
  CSV/registry inputs, comparing outputs, errors, routing reports and mutation.
  Internal cache bytes are checked against each version's own snapshot format.
- Accepted SSP fingerprints, CIA11, AR17 and metadata-only future-model behavior
  pass. Frozen historical engines and expected business outputs are unchanged.
- Test setup previously using the retired catalog dialect now supplies the same
  CSV and registry format as deployment. Business assertions remain in place;
  obsolete-format assertions now verify explicit rejection.
- New tests cover retired settings, old cached plans, mismatched cells, CSV
  column alignment and literal values, error aggregation and JSON number options.
- Independent read-only review found no blocking issue; 21 focused retirement
  and compiled-boundary tests passed separately.
- Generated split/combined notebook synchronization and whitespace checks pass.
- Local environment: Python 3.12.14 and pandas 3.0.1. The added GitHub workflow
  pins Python 3.12, pandas 3.0.1 and the action commits; remote results must be
  checked separately after publication. No Snowflake credentials are used by CI.

## Release boundary

Use the matching seven cells together. Live Snowflake execution was unavailable:
no connector or open Snowflake session was present. No source query, database
write, registry alteration or reload occurred. The daily writer still needs live
preview and persistence/readback acceptance, and AR has no verified destination.
This candidate is not production acceptance or full OSCAL conformance certification.

Next action: review the tested candidate and decide the remaining simplification
scope; perform live acceptance in the intended Snowflake environment before writes.
