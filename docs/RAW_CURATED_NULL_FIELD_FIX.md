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
