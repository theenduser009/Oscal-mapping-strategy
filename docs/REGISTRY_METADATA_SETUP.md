# One-time DEV registry setup, then the same seven cells

The code no longer needs the JSON catalog. The lean runtime contract uses the
existing nine registry columns plus only three sparse execution columns:
`OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`. **This revised migration has
not been run or verified in Snowflake.**

The reported block-line-270 attempt failed on a JSON binding type mismatch
before ALTER or UPDATE. A later 18-column run was reported as finishing, but its
aggregate result was not captured here; therefore some or all legacy columns
may already exist in DEV. This migration safely ignores them. It continues to
bind explicit JSON strings and decode them with `PARSE_JSON` in all four dynamic
templates. The lean revision reduces only the registry execution contract; it
does not broaden the SSP/Assessment Results scope or approve new mappings.
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

- Adds only three nullable metadata columns when they do not already exist:
  `OPERATOR`, `UUID_POLICY` and `REQUIRED_MEMBERS`.
- Populates only existing active SSP and Assessment Results rows.
- Preserves the original nine columns and every existing row.
- Retains explicit operators for the accepted SSP/Assessment Results paths and
  the prior SSP singleton defaults. A null `OPERATOR` is not approval: the
  shared engine may infer a supported shape from the original identity columns,
  but a path is included only through approved CSV routing or explicit retained
  metadata.
- Updates blank values only, or leaves exact matches unchanged. Conflicting
  non-null metadata stops the run rather than being overwritten.
- Does not drop, clear, validate or rely on any legacy columns left by an
  earlier 18-column setup. Those columns are intentionally untouched.
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

## Registry columns: lean execution contract

The original columns remain authoritative for model structure and identity:
`OSCAL_MODEL_KEY`, `NODE_PATH`, `ELEMENT_TYPE`, `PARENT_NODE_PATH`,
`IS_COLLECTION`, `INSTANCE_KEY_RULE`, `PROCESS_ORDER`, `IS_ACTIVE` and
`ITEM_PATH`. Only behavior that cannot be determined safely from those columns
or the approved mapping CSV is retained separately.

| Added column | Meaning |
| --- | --- |
| OPERATOR | Selects one shared assembler (`object`, `record`, `observations`, `properties`, `values`, `references`, `roles`, `parties` or `assignments`). Null means no explicit override; an approved CSV route may use a shape that is unambiguously derivable from the original registry identity columns. |
| UUID_POLICY | Preserves the accepted payload UUID behavior: `omit`, deterministic node UUID, or deterministic instance UUID. |
| REQUIRED_MEMBERS | Optional vertical-bar list for atomic assembly. The CIA security-impact object is emitted only when all three required objectives are available. |

The executable set is approved CSV owners plus paths with retained non-null
`OPERATOR`, closed over their registry ancestors and governed role/party
siblings. Parent linkage, collection shape and instance identity come from the
original registry columns. Field selection, target paths, transformations and
provenance come from `Mapping/ARCHER_OSCAL_MAPPINGS.csv`. Empty handling,
property naming, list positioning, role/party companion discovery and report
annotations are shared engine conventions for the proven operators, not
duplicated registry columns.
The seed checks the recorded document-ID, component-reference, role, party and
assignment identity contracts before DDL and does not rewrite them.

## Scope and maintenance

The CSV retains the 147 reviewed occurrences plus the prior guard and three
explicitly labelled existing metadata support rules. Field names, original
paths, Notes, provenance and accepted SSP/CIA/AR behavior are preserved.
The review workbook remains a compilation snapshot, not another runtime input.

A new approved field using a supported transform requires a CSV row.
A new model requires its original registry hierarchy/identity rows, mappings in
the approved CSV, and visible source/destination configuration. Only paths that
need a supported shared assembler receive an `OPERATOR`; `UUID_POLICY` or
`REQUIRED_MEMBERS` are populated only when that behavior is actually required.
Genuinely unsupported operations need one reusable code enhancement, not a new
model-specific mapper or another policy-column expansion.

The current compact release passes 691 local tests, including static and
synthetic bind-transport regressions. None is live Snowflake proof. Successful
registry setup, DIM/FACT writes, Matillion runs, daily-loader acceptance and
full-model conformance remain unverified for this release.

