# Raw-to-curated null field loss — production incident

Status: **null-loss mechanism identified in the supplied SQL; correction candidate
prepared; live verification and deployment pending**. No production data or
Matillion job was changed by Codex. SSP write pilot is paused and has not run.

## What is actually wrong

The [uploaded SQL transcription](raw_curated_json_update_sql_checkpoint.md) resolves
field IDs through `ARCHER_META_FIELD`, but its final
`OBJECT_AGG(SQL_KEY, TYPED_VALUE)` omits pairs whose value is SQL NULL.
The preceding `NULLIF` and unsuccessful `TRY_TO_*` casts can produce that SQL
NULL. A field can therefore resolve to the right name and still disappear from
the assembled JSON. This behavior is documented by Snowflake
[OBJECT_AGG](https://docs.snowflake.com/en/sql-reference/functions/object_agg).

This is one confirmed loss mechanism, not proof that every missing field ID has
the same cause. Source/data evidence for specific affected records is still needed.

## Start here — complete corrected curated JSON before writing

[Copy the complete conversion preview SQL](../sql/matillion/READ_ONLY_authorization_package_full_conversion_preview.sql).

**Copy the full file into one Snowflake SQL cell and run. No replacements.**
The source table is already set to
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW` from Cell 1.
No record-ID input, Matillion variable, previous query or notebook rerun is needed.

This is the requested preview of the **actual correction**, not a null-only list.
For each eligible raw record, open **PROPOSED_CURATED_JSON** to see both populated
values and named JSON-null values. Compare **RAW_FIELD_CONTENTS** (raw IDs and
values) with **CURRENT_CURATED_JSON** and **PROPOSED_CURATED_JSON** (mapped names
and converted values). Current/proposed content IDs and key counts are alongside.

The preview runs the same metadata lookup/type-conversion pipeline and
null-retaining aggregation as the candidate. It includes already-curated records
for inspection only. There are **no writes or Matillion changes**.

Only rows with `PREVIEW_READY_NOT_WRITTEN` have a proposed JSON document to inspect.
Duplicate raw IDs, duplicate output keys, missing names/IDs and unsupported root
shapes are blocked explicitly. The original converter processes only the first
root-array item; this preview conservatively blocks multi-item root arrays
instead of presenting their first item as full coverage. Missing/invalid raw IDs
are grouped into a diagnostic row, not emitted as fabricated record identities.
Existing strict casts/nested extraction can still raise an error. A ready preview
does not prove every raw field ID is covered; inspect the affected field.

**Published without running tests at the owner's request. Snowflake verification
and production deployment are still pending.** Full-table execution consumes
warehouse compute. Keep source values in Snowflake; share only redacted evidence.
The production UPDATE still skips populated curated JSON; viewing a proposed
repair here does not authorize or perform a historical backfill.

The older null-only reports below are optional and are **not the next step**.

## Copy, paste, run — all records, no inputs

[Open the all-record null-field-name SQL](../sql/matillion/READ_ONLY_authorization_package_all_null_field_names.sql).

Copy the entire file into **one Snowflake SQL cell** and run it. No placeholders,
record ID, previous result, Python cell or Matillion variable are required.
It reads the explicitly configured
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW` table.

The result lists each **FIELD_NAME** with a null **MAPPED_VALUE** and counts of
affected records/occurrences across the table. It includes already-curated rows
for inspection. Duplicate-key and missing/fallback-style-name signals are marked
for review, not silently treated as a valid JSON assembly.

**Published without a test run at the owner's request; not verified in Snowflake.**
This is SELECT only and does not update anything, but a full-table scan uses
warehouse compute. Existing type conversions, row-selection precedence, nested
extraction and first-array-item handling remain. A selected null can come from a
raw null, an empty string or a failed conversion. This inventory is not a complete
raw-field coverage proof, deployment approval or historical repair. Zero results
only means no null rows reached this query's final conversion stage.

The earlier one-record previews below remain available but are **not required**
for this no-input query.

## Just show the null-valued field names — one query

Use [the one-step authorization-package null-field list](../sql/matillion/READ_ONLY_authorization_package_null_field_names.sql).
It returns **FIELD_NAME** beside **MAPPED_VALUE**, filtered to proposed JSON-null
values. You do not need a previous query or RESULT_SCAN.

The raw table is already filled in as
`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`, exactly as
configured in repository Cell 1. That is the recorded DEV location; it is not a
claim that this is the live production table.

Replace only `REPLACE_WITH_REQUESTED_OBJECT_ID` with the affected record's raw
`RequestedObject.Id`, keep the quotes, and run the full file in one Snowflake SQL
cell. It is SELECT only. No Matillion table variable or follow-up query remains.

A status row distinguishes a blocked preview from a successful preview with no
null-valued keys. A row whose status is `NULL_VALUED_FIELD` contains a real field
name; a diagnostic row with an empty field-name column is not a mapped field.
These are nulls **after the existing conversion**, which can originate from raw
nulls, empty strings, or failed casts. Fields filtered out before assembly are
not included; this is not a complete unmapped-field audit. Local checks passed;
Snowflake runtime verification remains pending.

## See the actual values without writing

Open the [one-record SELECT-only values preview](../sql/matillion/READ_ONLY_raw_curated_values_preview.sql).

1. Copy it into a **Snowflake SQL worksheet/cell**, not a Python cell.
2. Replace `${jv_raw_table_name}` with the actual fully qualified raw table
   (or retain it when Matillion resolves that existing variable).
3. Replace `REPLACE_WITH_REQUESTED_OBJECT_ID` with one affected raw
   `RequestedObject.Id`, keeping the quotes. This is not necessarily the stored
   `CONTENT_ID`.
4. Run only this SELECT. It displays `RAW_FIELD_CONTENTS`,
   `CURRENT_CURATED_JSON`, `PROPOSED_CURATED_JSON`, current/proposed content IDs,
   key counts and status. Open the JSON cells to inspect field names and values.

This preview deliberately includes an already-curated record for **inspection**.
It does not remove the production UPDATE's pending-only filters or repair that
record. There is no UPDATE, MERGE, DDL or transaction in this preview.

Exactly one physical raw row must match. Duplicate rows or combined field names
block the proposed JSON instead of choosing a winner. No match, no extracted
fields, or an input placeholder is not a pass. Existing strict casts and recursive
extraction remain unchanged: if those fail, report the error rather than deploying
the candidate. Local checks verify the SELECT-only boundary and preserved
conversion text; **this SQL has not yet run in Snowflake**.

A content-ID mismatch needs review; a previously unprocessed row can legitimately
have no stored ID yet. More proposed keys alone is not proof every field mapped:
compare the particular missing field and any non-null values too. The preview
does not show every intermediate metadata-lookup decision.

The result contains real source values. Inspect them in Snowflake; share only
sanitized counts/errors or approved redacted evidence, not sensitive payloads
or unredacted identifiers in GitHub.

## Bounded candidate correction

[Full Matillion SQL candidate](../sql/matillion/CANDIDATE_raw_curated_preserve_null_keys.sql)
is derived from the supplied transcription. Compare it with the **actual** job
component before deployment; a transcription is not a verified export.

The final aggregate becomes:

```sql
OBJECT_AGG(SQL_KEY, COALESCE(TYPED_VALUE, PARSE_JSON('null'))) AS CURATED_JSON,
OBJECT_AGG(SQL_KEY, TYPED_VALUE) AS ID_SOURCE_JSON
```

`PARSE_JSON('null')` creates JSON null, distinct from SQL NULL; it retains the named
key without inventing a value. Existing non-null typed values—including type-4
objects and arrays—are passed through. [Snowflake null handling](https://docs.snowflake.com/en/sql-reference/functions/parse_json)

The internal `ID_SOURCE_JSON` uses the **old aggregate** solely for the five
existing content-ID fallback terms. Their order, casts and final requested-object
ID fallback are unchanged. It is passed through the inner SELECT but not stored
in the target. This isolates record identity from newly retained null keys.

All field-type conversions, metadata joins, precedence rules, nested extraction,
table variable and both `CURATED_JSON IS NULL` update predicates are preserved.
Invalid dates/numbers still require investigation: this candidate retains their
keys as null; it does not repair the invalid value.

## Before any production deployment

1. Save the actual Matillion component/version and compare it to the checkpoint.
2. Run the [read-only synthetic regression](../sql/matillion/READ_ONLY_null_key_regression.sql)
   in Snowflake. It has no table dependency: expected key counts are **7 before,
   12 after**, and every boolean check must be true. This proves the small
   expression behavior in Snowflake, not the complete production pipeline.
3. Run the [read-only pending-cohort preflight](../sql/matillion/READ_ONLY_raw_curated_null_preflight.sql)
   using the existing Matillion table variable; in a worksheet replace the variable
   with its actual fully qualified table. It uses the original pending-row scope,
   returns counts only, and changes nothing.
4. Any duplicate key groups, missing/empty names, numeric-ID errors or extraction
   errors require review. Retaining a previously omitted null can expose a
   duplicate key that the old aggregate ignored. Do not pick an arbitrary winner.
   `FALLBACK_STYLE_NAME_ROWS` is a name-prefix signal, not proof of failed lookup.
5. Compare one affected record's raw field IDs, resolved names, previous/candidate
   keys, non-null values and content ID under the normal production change process.
   Only then deploy the candidate to the existing pending-row workflow.

The preflight can legitimately report **no pending rows**; that is not a pass and
does not test already-curated affected records. Six local tests verify the exact
change boundary/read-only scripts, not live Snowflake execution.

## Already-processed records need a separate repair

The update skips rows with populated `CURATED_JSON`, including incomplete JSON.
The candidate intentionally preserves that boundary. It will **not** backfill them.
Do not clear `CURATED_JSON` across the table or remove the update predicates.

For a bounded repair we need the actual target table and one affected
`RequestedObject.Id`, followed by before/after evidence and an explicitly scoped
repair with a saved baseline. No bulk production backfill is prepared or authorized.

## Independent gaps that this patch does not hide

- Top-level missing metadata falls back to `FIELD_<id>`; null preservation does
  not supply a missing governed field name.
- Nested rows with no `SQL_FIELD_NAME` are explicitly filtered out.
- Recursive extraction can encounter nonnumeric keys while the join uses strict
  `TO_NUMBER`; this is a potential separate runtime failure.
- `ROW_NUMBER` intentionally selects one row per requested object and SQL key;
  multiple field IDs sharing a name do not become separate JSON properties.
- Array-root handling currently uses the first item; additional root entries are
  not handled by this correction.

None of those independent issues has been declared fixed or silently rewritten.
