# Cell Three scalar legacy identity fix

Date: 2026-09-12  
Scope: Cell Three only  
Database writes: none

## Owner evidence

The matching V2 notebook run passed Cell Two and stopped while Cell Three was
decoding registry contracts:

```text
ValueError: Scalar object operator cannot define collection identity metadata
```

The failure preceded graph construction and persistence. No DIM or FACT write
was reached.

## Correction

`INSTANCE_KEY_RULE` and `ITEM_PATH` describe collection instances. Cell Three
now omits those two fields from the compiled runtime contract when
`IS_COLLECTION = FALSE`, even when an established registry row retains legacy
values in the original columns. Collection rows still require their exact
operator-specific identity rule and item path.

This preserves the original registry data and keeps the mapper lean. It does
not add metadata columns, change the CSV, loosen collection checks, touch Cell
Four's transformations, or alter persistence.

## Verification

- Maintained Cell Three, V2 Cell Three and the combined notebook are synchronized.
- New regression proves a scalar legacy row crosses the Cell Three-to-Four
  boundary without carrying collection identity into the runtime contract.
- Existing tests continue to reject missing or conflicting collection identity.
- All 698 local tests pass.
- Accepted SSP digest, CIA11 and AR17 outputs remain unchanged.
- Metadata-only third-model, PK/FK, idempotency and preview-no-write gates pass.

Local regression is not live Snowflake acceptance.

## Next action

If the successful Cell Two session remains open, replace only V2 Cell Three and
run Cells Three through Seven with `EXECUTE_WRITES = False`. If the session was
restarted, run the matching V2 Cells One through Seven. Share the Cell Seven
aggregate report. Do not rerun registry SQL or enable writes.
