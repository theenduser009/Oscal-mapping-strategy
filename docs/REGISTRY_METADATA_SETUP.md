# One-time DEV registry setup, then the same seven cells

The code no longer needs the JSON catalog. The registry must receive its
approved structural metadata before this release can run. **The previous SQL
failed in Snowflake before making registry changes. The corrected SQL still
needs live verification.**

The reported block-line-270 error was a JSON binding type mismatch in the first
dynamic conflict check, before ALTER or UPDATE. The correction binds explicit
JSON strings and decodes them with PARSE_JSON in all four dynamic templates.
It does not change the seven cells, metadata seeds or registry update scope.
See the [binding correction checkpoint](checkpoints/2026-09-12-registry-binding-correction.md).
Local tests are not permission to enable the daily database writer.

## Your next step: registry SQL only

Open [EXTEND_OSCAL_MAPPER_METADATA.sql](../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql),
copy the whole file into a **fresh Snowflake SQL worksheet**, and run it with
your approved DEV role. No table names, IDs or mode switches need replacing.
Use a session with no active transaction and pause other registry writers.

It targets only `RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY`.
The role needs SELECT, ALTER and UPDATE access plus database/schema usage.
This does not create permanent backup tables or need access to DIM/FACT.

Share the aggregate result showing `STATUS = REGISTRY_METADATA_VERIFIED`
and `ORIGINAL_COLUMNS_UNCHANGED = true`, including numeric `UPDATED_ROWS`.
Stop on any error and share the
actual Snowflake message; do not bypass it or change privileges automatically.

## What the migration changes

- Adds 18 nullable metadata columns to the existing registry.
- Populates only existing active SSP and Assessment Results rows.
- Preserves the original nine columns and every existing row.
- Keeps unimplemented collections disabled; does not approve mappings.
- Updates blank values only, or leaves exact matches unchanged. Conflicting
  non-null metadata stops the run rather than being overwritten.
- Does not read, delete, truncate, insert into or update OSCAL DIM/FACT.

Schema additions are DDL: **they auto-commit and cannot be rolled back by the
metadata transaction**. A failed DDL phase can leave some nullable columns.
The metadata UPDATE has its own transaction, conflict checks and readback.
An uncertain commit/rollback outcome requires inspection, not an automatic
retry. A successful setup can be rerun without changing matching metadata,
but is a one-time deployment action, not a daily Matillion step.

## After setup is verified: preview

1. Replace the notebook Files copy of
   [ARCHER_OSCAL_MAPPINGS.csv](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
   Keep that exact filename. No JSON catalog or test fixtures are needed.
2. Replace the existing seven Python cells with the matching
   [V2 pages](../notebooks/cells_v2/README.md). Do not mix releases.
3. Keep `CONFIG["EXECUTE_WRITES"] = False` in Cell One and
   `OSCAL_LOAD_MODE = "PREVIEW"` in Cell Seven.
4. Run Cells One through Seven in order in the same session. Share only the
   aggregate `OSCAL_PIPELINE_REPORT`; keep source IDs and payloads private.

The shipped selection previews SSP and the seventeen accepted AR fields.
AR's target contract is still absent: a graph-validated/target-pending AR
outcome is expected, **not an AR database write**. Live preview acceptance
remains pending. No SSP reload, old pilot or standalone AR rerun is requested.

## Registry columns: maintain structure once

Only relevant columns need values on each row. Root-only settings live once
on the model root; reference-family settings live on the assignment collection.

| Columns | Meaning |
| --- | --- |
| MAPPER_METADATA_VERSION | Root marker for the supported metadata format; this release uses 1. |
| MAPPER_ENABLED | Explicit true/false on every active row of a configured model. |
| OPERATOR | Shared object, record, observations, properties, values, references, roles, parties or assignments behavior. |
| PARENT_INSTANCE_RULE | none, singleton or source-record; never a guessed parent. |
| UUID_POLICY | omit, node or instance. |
| EMPTY_POLICY | omit or emit, within operator capabilities. |
| LIST_INSTANCE_RULE | none or source-field-index for supported object lists. |
| PROPERTY_NAME_RULE | source-field-slug where properties/observations require it. |
| ASSEMBLY_POLICY / REQUIRED_MEMBERS | normal or complete-only; required scalar members separated by a vertical bar. |
| DEFAULT_SINGLETON_POLICY | Root-level none or emit-outside-collections; preserves accepted SSP defaults. |
| REQUIRED_RULE_IDS | Root-level required mapping-row identities separated by a vertical bar. |
| ROLES_PATH / PARTIES_PATH | Governed companion paths for an assignment collection. |
| PARTY_TYPE | Approved party type. |
| PARTY_UUID_PARTS / PARTY_UUID_SOURCE_KEY | Deterministic reference identity and the existing scoped namespace. |
| REPORT_TARGET_PATH | Optional root-level report annotation; not another mapping target. |

Existing NODE_PATH, PARENT_NODE_PATH, IS_COLLECTION, INSTANCE_KEY_RULE, ITEM_PATH
and processing order stay authoritative. The seed retains the recorded
document-ID and role/party identity contracts; it does not rewrite them.

## Scope and maintenance

The CSV retains the 147 reviewed occurrences plus the prior guard and three
explicitly labelled existing metadata support rules. Field names, original
paths, Notes, provenance and accepted SSP/CIA/AR behavior are preserved.
The review workbook remains a compilation snapshot, not another runtime input.

A new approved field using a supported transform requires a CSV row.
A new model requires its registry metadata and visible source/destination
configuration, then reuses these seven cells. Genuinely unsupported operations
need one reusable code enhancement, not a new model-specific mapper.

The earlier 685 local tests did not exercise actual Snowflake bind transport;
static and synthetic binding regressions are now included. None is live
Snowflake proof. Successful registry setup, DIM/FACT writes, Matillion runs,
daily-loader acceptance and full-model conformance remain unverified for this
release.
