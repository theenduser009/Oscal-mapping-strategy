# Mapper simplification: verified cleanup and compiled mapping review

## Completed field-rule migration and compatibility retirement

No owner approval is pending. All 61 prior execution contracts now compile from
the readable mapping CSV: 60 approved rules and one existing populated-value
guard. The 147 reviewed source occurrences retain exact paths, labels, types,
Notes and provenance. Other entries remain 85 deferred and two excluded.

The deployed settings shrink from 1,705 lines to 364 lines by removing
MAPPING_RULES, PATH_RULES and EXCLUDED_FIELDS. Source bindings, element behavior,
identity and destination settings remain explicit; the JSON dependency is not
yet removed. Cell Three's catalog field matching, Notes matching and source-field
path rewriting are now removed from active execution. Historical input behavior
is frozen in tests/fixtures/legacy_cell3_catalog_input.py, not production.
Active model settings reject retired field-rule keys, even when empty.
Do not describe this staged migration as the final simplified architecture.

All 599 local tests pass; generated notebook pages are synchronized.
Regression coverage pins the original 61 rule contracts independently of the
new artifact, the accepted SSP graph fingerprint and AR17 business output.
All eleven CIA routes, reference parameters and the populated-value guard are
unchanged. Flat metadata also works for a synthetic third model, without the
catalog matching functions. UTF-8 Notes and literal N/A labels survive input.
Unsupported member paths fail rather than being silently ignored.

Active SSP and AR parity checks consume the current flat mapping file directly;
they do not use the frozen compiler. Missing approval on partially specified
executable metadata blocks explicitly, and no fallback is available.

Remaining simplification: consolidate structural settings without guessing
registry capabilities. The current registry does not provide all operator,
parent-instance, UUID and optional-assembly rules. Required metadata.title
sourcing and the AR17 completeness gate also remain in the settings file and
need a governed home; removing them or hiding them in Python is not cleanup.
No additional owner approval is pending for the authorized refactor. The existing SSP
guard-presence gap is recorded: the guard currently executes, but removing its
CSV row is not detected by an SSP required-rule list. AR's exact required IDs
remain enforced. No new live acceptance or database write is claimed.

The owner requires a simple seven-cell interface, one human-maintained Excel/CSV
mapping source, registry-owned structure/identity, reusable transformations and
the existing guarded writer. A second hand-maintained JSON catalog duplicating
the sheet is not the desired final design. The current code still requires that
catalog; this cleanup does not claim to remove it or finish the redesign.

## Earlier cleanup (completed)

- The posted Cell Three failure occurred while uploading empty nested metadata
  to Snowpark. Its resulting dataframe has no active consumer: the graph builder
  discards it and the runner passes explicit compiled contexts. Removed that
  upload; the Python dictionaries and local pandas inspection view are unchanged.
- Removed three unused private helpers: Cell Two's `_required_lookup_column`,
  Cell Six's `_assert_safe_identifier` and `_duplicate_count`.
- Removed the ignored legacy-name argument from Cell Four's lookup accessor and
  its four calls. Explicit source/model lookup isolation remains.
- No new transformation, model branch, mapping approval, target change or write.
- **567 tests pass**. Three new tests execute the entire Cell Three with a
  session that forbids any database call, covering empty/nested dictionaries,
  false/zero constraints, multiple models, no selected rows and stale aliases.
  They fail on the old upload and pass after its removal. Generated V2 and
  combined files match the maintained seven cells. No live acceptance yet.

## CIA was preserved

The current metadata retains all eleven accepted mappings under
`system-security-plan.system-characteristics.security-impact-level`:
three confidentiality, four integrity and four availability routes.
Their transforms, lookup resolution and reviewed legacy labels match the old
implementation. Missing one objective still omits the optional assembly;
conflicting values still block. The separate Recommended Security Category
All Nulls row remains unresolved and is not one of these eleven mappings.
The independent review ran 65 focused tests and 32 old-versus-current graph
comparisons without finding an output difference. These are local fixtures,
not counts from a new Snowflake run.

## Original design and missing input

Earlier README revisions preserve the original generic design (`69e1933`),
simple Cell One (`8d0e4f3`), source/CSV/registry input Cell Two (`cc1f1b4`), and
an early reusable graph builder (`749a563`). These are design/code fragments,
not a recovered, independently verified complete original notebook.

The earlier input code names `archer_to_oscal_mapping (4).csv` and records
608 mapping rows. The saved earlier checkout/history and the current GitHub
tree do not contain that file or a full workbook; only transcribed subsets
are available. Retrieved recent original-chat pages have not supplied it.

## Updated input and owner review

The owner uploaded eight Mapping documents and requested a consolidated workbook.
[Review workbook and source inventory](../../Mapping/REVIEW.md) contains 147 source
occurrences, 146 distinct fields. The owner checked the blank-path control rows
and confirmed continuing. That confirms the compilation, not new mapping rules.
Do not request the original 608-row file again as a blanket prerequisite.
The compiled workbook is not yet a replacement notebook input.

All 43 accepted SSP source fields (including the eleven CIA fields) and all
17 accepted AR fields appear in the draft. The missing RECOMMENDED_SECURITY_CATEGORY
row is an existing reject-populated guard; retain it without inventing a new
populated mapping. The shared low/moderate/high note conflicts with accepted
legacy CIA labels, and FULL_CONTROL_ASSESSMENT_HELPER is an additional unapproved
candidate. Neither changes accepted behavior automatically.

**Earlier plan (now completed above):** migrate known accepted executable rules into readable mapping metadata,
carrying forward acceptance/deferment, identity, null/assembly and reference rules
from existing evidence. Reconcile specific conflicting Notes separately; the
unresolved control candidates need not block work on accepted rows. Remove
duplicated catalog mapping rules only after output parity is proved. Keep source
and storage settings distinct from field mappings; no guessed model/path rules,
field-name dispatch, extra runtime cells, new write approval or daily truncation.

The interim cleanup is 567-test verified, not the final catalog-free release.
No notebook rerun is requested while the requested simplification continues.

The accepted full SSP DEV reload, AR17 in-memory acceptance, deferred work,
unexplained old-row reduction and writes-disabled boundary remain unchanged.
