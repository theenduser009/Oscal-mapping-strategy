# Authorization-date mapping — implementation ready, live run pending

## Approved Excel contract

The user's [in-memory contract report](../live-snowflake-results.md) inspected
54 canonical SSP mappings and identified two unsupported contracts. For this
implementation, the relevant row is:

| Contract field | Recorded value |
| --- | --- |
| Archer source | `ATOIATO_DATE` |
| OSCAL model | `SSP` |
| OSCAL path | `system-security-plan.system-characteristics.date-authorized` |
| Registry owner | `system-security-plan.system-characteristics` |
| Mapping type | `Transform` |
| Notes | `Convert timestamp to DateDatatype` |
| Artifact status | `In Progress` |

This source-to-target contract comes from the user's Excel evidence, not from
an inferred NIST source mapping. The report contains mapping metadata only;
it does not prove the source timestamp format or population coverage.

## Implemented behavior

Cell 4 adds one exact source/owner/target/type handler. A valid ISO calendar date
or ISO timestamp becomes a JSON string in `YYYY-MM-DD` form on the existing
system-characteristics singleton. The source calendar date is retained: no UTC
conversion, invented timezone, or change to `published` / `last-modified`.

Supported strings have a full `YYYY-MM-DD` date; timestamps also have
`HH:MM:SS`, separated by `T`, `t`, or a space. Optional fractional seconds
(up to nine digits), `Z`/`z`, or a numeric `+/-HH:MM` offset are accepted.
Calendar dates, clock values and offset components are validated. Native Python
dates/datetimes are supported too. These are conservative parser capabilities,
not a claim that every form occurs in Archer.

The existing empty-value policy remains: `None`, empty string/list/object emits
nothing. Invalid calendar values, ambiguous locale dates, numeric epochs,
nonempty arrays and object wrappers fail with a sanitized actionable message.
The parser does not silently guess locale order, epoch units, wrapper fields,
or a source timezone. No source value or source-record identifier is printed.

The only other rejected contract, `RECOMMENDED_SECURITY_CATEGORY`, targets
security-impact-level with type `Extension Property` and Notes `All Nulls`.
It is unchanged: absent source values skip; populated values still require an
approved contract and fail. The note alone does not prove current population.

## Local verification

203 tests pass. New cases cover exact dispatch, ISO strings, native date types,
leap dates, invalid values and offsets, timezone-boundary dates without shifts,
nulls, sanitized failures, duplicate singleton rows, unchanged metadata
timestamps and the null-only security-category behavior. Canonicalization
retains the reported Notes. The graph regression verifies the date lands on
the existing parent, without additional nodes or changed containment keys.
The copy-ready cell and authoritative notebook are synchronized.

Local graph tests fake Snowflake transport and unrelated lookup I/O. No actual
Archer timestamp values were supplied to this implementation session.
**Local tests are not live acceptance or full-workbook completion.**

## Run now

Replace only [Cell 4](../../notebooks/cells/04_parsing_transform_payload_helpers.py)
with the complete current file. In the existing session run **4, 5, 6, 7**,
keeping `EXECUTE_WRITES = False`. If the session restarted, run all seven in
order. Do not rerun registry setup or either contract report.

Post the full Cell 7 result. If it succeeds, run the mapped-scope assembler;
if it fails, stop there and post the exact error. A non-ISO source format is
an evidence gap to resolve, not permission to silently reinterpret it.

## Progress reporting

[The field-to-model/path register](../MAPPING_PROGRESS.md) and
[today's manager report](../daily/2026-09-10.md) separate implemented changes,
live acceptance, payload proof and pending gaps. Daily reporting is scheduled
for 5 PM Eastern in this task. The OpenAI Docs skill guided that schedule
setup; it did not supply mapping rules. For a report using local files, keep
the computer on and the app running, per the
[official scheduled-task guidance](https://learn.chatgpt.com/docs/automations?surface=app).
