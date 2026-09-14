# OSCAL Profile source-discovery evidence

Date posted: **2026-09-14**

Transcribed from the supplied Snowflake screenshot. This is a sanitized,
read-only discovery checkpoint. It does not approve a mapping and does not
change the mapper, mapping CSV, registry, or Snowflake data.

## Visible query intent

The query comments explicitly state:

- Profile discovery only: inspect distinct values across the RAW table's stored
  versions.
- These counts are not the mapper's deduplicated current source snapshot.
- No record IDs or target writes.
- Keep source-value results private.

The visible query parses `CURATED_JSON` from:

`RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`

It inspects:

- whether the parsed payload is an object;
- `TYPEOF(payload:ADD_OVERLAY)`;
- `payload:ADD_OVERLAY`;
- `TYPEOF(payload:BASELINE_RECOMMENDATION)`;
- `payload:BASELINE_RECOMMENDATION`; and
- a stored-version count.

The query groups by all selected discovery attributes, orders by stored-version
count descending, and limits the output to 30 rows.

## Visible result pattern

Eight distinct result rows are visible.

| Field | Visible result |
|---|---|
| Parsed document | `IS_OBJECT_DOCUMENT = TRUE` in every visible row |
| `ADD_OVERLAY` | Type and value are `NULL` in every visible row |
| `BASELINE_RECOMMENDATION` | One visible pattern is `NULL_VALUE`; the remaining visible patterns are `OBJECT` |
| Object shape | The visible objects contain `OtherText` and `ValuesListIds` members |

The raw `ValuesListIds` shown in the screenshot are intentionally omitted from
this public evidence file.

## Interpretation boundary

This screenshot confirms source shape only. It does not resolve the value-list
IDs to business labels, prove an approved OSCAL `profile.imports[]` target, or
authorize runtime mapping or writes. The screenshot also does not expose the
stored-version counts clearly enough to transcribe them.
