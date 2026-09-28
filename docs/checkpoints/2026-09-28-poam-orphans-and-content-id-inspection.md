# Source One QA: POAM orphan finding and single-Content-ID inspection

Date: 2026-09-28

## Repository basis
- Branch: simplify-metadata-boundary.
- Head inspected before this work: 0e9ccad4793eff0f598f6f969a005f160f17e539.
- New SELECT-only inspection SQL commit: a3887441f7f96c7037c850493d6c2575fd43f447.
- SQL: sql/qa/SOURCE_ONE_CONTENT_ID_ALL_ATTRIBUTES_2026-09-28.sql.
- SQL blob read back through GitHub: c33cc56feefc13fe4d7715dd3d652d13f55b6556.
- That blob matches the locally generated file's Git blob hash.

## Newly supplied owner evidence
The owner supplied a partial screenshot of the 32-row relationship-integrity result from section 04 of sql/qa/SOURCE_ONE_PRODUCTION_QA_2026-09-25.sql.

Visible POAM results:
- ORPHAN_SOURCE_FK: 2,575 / FAIL.
- ORPHAN_TARGET_FK: 2,575 / FAIL.
- The visible POAM duplicate-FACT-key, null-FK, self-edge, UUID-mismatch, cross-record and cross-namespace rows show zero / PASS.

The owner says the rest looks good. The screenshot does not show all 32 rows, so this checkpoint does not independently certify every other row.

The two orphan counts may overlap. They are not proof of 5,150 distinct bad FACT rows. The original checks compare each endpoint against the full POAM DIM, not a Content-ID-filtered DIM. Their counts are table-wide. A fact with both endpoints absent cannot be assigned a current Content ID or source namespace from those DIM joins alone.

Root cause remains unverified: no deletion, truncation, cleanup, rekeying or reload is authorized by this finding. Do not label these rows historical leftovers without evidence. A UUID-mismatch count of zero does not exonerate orphan facts: that older check uses inner joins and only tests resolved endpoints.

## Status precedence
This current QA finding supersedes any implication that the entire current downstream POAM relationship table is clean or ready for final sign-off. It does not erase the dated September 25 committed/read-back-verified batch checkpoints. Batch-scoped readback and table-wide orphan QA have different coverage.

The earlier September 28 upstream result remains MATCHED_SAVED_REFERENCE for its inspected snapshot: 2,813 rows compared, 1,628,727 matching key/value/type pairs, and no reported discrepancies. That upstream comparison is not downstream orphan validation or full production sign-off.

## Requested inspection now prepared
The owner requested all stored models, components, implementation details, responsible parties, metadata and properties for one Authorization Package Content ID.

The new query returns one result grid with:
- MODEL_SUMMARY: all four Source One models, with explicit missing-model indication.
- ELEMENT: complete stored DIM payload and audit/provenance context for every matching node, including disconnected nodes.
- ATTRIBUTE: recursive JSON paths, values and types for nested properties, containers and array members. Nulls are not replaced with text. Empty payloads remain visible in ELEMENT rows.
- RELATIONSHIP: all FACT rows touching a selected node; left-joined endpoint inspection distinguishes missing, ambiguous, self, cross-record, cross-namespace and UUID/type problems.
- POAM_TABLE_SCOPE: mutually exclusive endpoint-presence buckets across the entire POAM FACT table. These rows have no attributed Content ID.

The query uses source namespace plus Content ID and model-specific keys. Shared Assessment Results rows from another source are not blended into Source One. Duplicate DIM keys are counted rather than arbitrarily deduplicated; they do not multiply the endpoint diagnostic through joins. All actual DIM payloads and FACT rows remain represented in their relevant scope.

No graph reachability/cycle validation, every-reference resolution, raw-to-target field parity or full OSCAL document conformance is claimed. Inline party/component UUID references stay visible in payloads; they are not relabelled as FACT containment edges. Existing POAM scope remains reference-only, and missing business details are not fabricated. Source-preservation FINDINGS properties do not become native findings objects.

## Validation actually performed
- Current branch read and pinned.
- Existing production QA, integrated QA, SSP root-to-leaf SQL and current field-scope checkpoint inspected.
- Static checks: one SELECT statement, no database writes, balanced literals/parentheses, all four actual DIM/FACT table/key bindings, and no private record IDs in the new SQL.
- Local SQLite relational adapter exercised the actual nodes/key-index/edge-context/selected-edge CTE logic with 11 synthetic edges. Checked valid edges, each missing endpoint, both missing, cross-record, cross-namespace with equal textual IDs, self-edge, null UUID, null FK, duplicate DIM keys and exclusion of unrelated-source-only edges. Passed.
- The SQLite adapter is not a Snowflake compile or live execution. Snowflake-specific JSON flattening was source-reviewed, not executed locally.
- SQL published and blob read-back verified. No mapper, mapping CSV, registry, table or loader change.
- No live Snowflake run of the new inspection query occurred in this chat. Existing accepted load evidence is not reused as proof of this new query.

## Immediate next action
In a private Snowflake worksheet, replace the single REPLACE_WITH_CONTENT_ID placeholder in the SQL params CTE with the owner's chosen Authorization Package Content ID. Run the complete SELECT and inspect the four MODEL_SUMMARY rows and POAM_TABLE_SCOPE bucket rows alongside the detailed attributes. Do not publish private result data to GitHub.

Next diagnosis depends on those live results. No destructive repair is proposed.
