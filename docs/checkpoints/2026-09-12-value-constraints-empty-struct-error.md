# Canonical mapping VALUE_CONSTRAINTS empty-struct failure — 2026-09-12

Status: **Cell 3 stopped before canonical Snowpark DataFrame creation**.

## Observed failure

```text
ArrowNotImplementedError: Cannot write struct type 'VALUE_CONSTRAINTS'
with no child field to Parquet. Consider adding a dummy child field.
```

Failing notebook location and statement:

```text
Cell [cell3], line 565
canonical_mapping_df = session.create_dataframe(canonical_mapping_pdf)
```

The traceback proceeds through Snowpark `session.create_dataframe`,
`session.write_pandas`, the Snowflake connector's `write_pandas`, pandas
`to_parquet`, and PyArrow's Parquet writer.

## Interpretation

At least one inferred `VALUE_CONSTRAINTS` value is an empty Python mapping or
otherwise produces a struct with zero child fields. Snowpark's pandas upload
path attempts to serialize the pandas DataFrame through Parquet, and PyArrow
cannot represent that empty struct.

This is a local canonical-mapping materialization/serialization failure. The
screenshot does not show target table DML, and it should not be classified as a
Snowflake DIM/FACT persistence failure.
