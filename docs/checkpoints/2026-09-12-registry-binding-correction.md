# Registry dynamic-binding correction - 2026-09-12

## Owner-reported failure and exact scope

The owner ran the published one-time registry setup and reported:
`Uncaught exception of type STATEMENT_ERROR on line 270 at position 18:
SQL compilation error: invalid type VARCHAR(17076) for parameter INPUT.`

In the failing [published SQL](https://github.com/theenduser009/Oscal-mapping-strategy/blob/0c53081f53ed2168e1ccd77107d7a337cba8e1c4/sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql#L292),
anonymous-block line 270/position 18 is the first dynamic conflict query.
The first ALTER execution follows at file line 311 and the UPDATE is later.
Therefore this invocation stopped before registry DDL or UPDATE. This does
not establish whether earlier attempts had already added metadata columns.
The migration never reads or writes application DIM/FACT targets.

## Root cause and bounded correction

Native ARRAY values were passed directly through dynamic SQL binds to
`FLATTEN(INPUT=>?)`. The reported runtime supplied VARCHAR instead.
[Snowflake's binding guidance](https://docs.snowflake.com/en/sql-reference/bind-variables#use-bind-variables-with-semi-structured-data)
specifies string bindings plus explicit parsing for semi-structured data.

- Keep seed, desired metadata, original-row snapshot and column specs as
  native ARRAYs for static queries and row-count checks.
- Serialize desired metadata and the original-row snapshot once with
  `TO_JSON(TO_VARIANT(...))` into separate VARCHAR variables.
- Decode the placeholder with `PARSE_JSON(?)` in each of the four dynamic
  templates: conflict, baseline, update and verification.
- Bind those serialized variables in all six executions.

No seed, registry-row scope, original column, transaction boundary, metadata
conflict rule, notebook cell, mapping CSV or write switch changed. No source
values or identifiers were published.

## Verification

The existing 685-test suite and eight new binding regressions pass locally.
The added tests cover all templates/calls, serialization order, static ARRAY
preservation, pre-DDL failure ordering, and synthetic JSON null/type/multiplicity
preservation. Two existing assertions now expect serialized variable names;
their transaction/count/readback assertions remain intact.

These are static/source-contract checks and Python simulations, not execution
by Snowflake's SQL compiler. The earlier tests missed this transport boundary.
A successful corrected live migration is still pending; do not describe this
as production or daily-loader acceptance.

## Single next action

Run the complete corrected
[EXTEND_OSCAL_MAPPER_METADATA.sql](../../sql/registry/EXTEND_OSCAL_MAPPER_METADATA.sql)
in a fresh Snowflake SQL worksheet using the approved DEV role, with no active
transaction or competing registry writer. No replacements or mode changes.
Share the aggregate result: `STATUS=REGISTRY_METADATA_VERIFIED`,
`ORIGINAL_COLUMNS_UNCHANGED=true`, and numeric `UPDATED_ROWS`.

Keep the seven notebook cells on hold until registry verification. Normal
mapper writes remain disabled. DDL additions auto-commit; a later DDL failure
can leave added nullable columns, and an uncertain commit outcome must be
inspected rather than blindly retried.
