# SSP pilot: physical storage correction

Date: 2026-09-11. Model: SSP. Scope: one accepted `system-security-plan` tree
in the already approved development DIM/FACT tables.

## Evidence and cause

The owner reported `UNSUPPORTED_LIVE_COLUMN_DATATYPE` during the pilot's DESC
planning. That attempt stopped before staging, transaction start or target DML.
The [uploaded physical schema](../ssp_dim_fact_physical_schema_checkpoint_2026-09-11.md)
now supplies the exact types. The schema-capture request is fulfilled.

| Physical columns | Existing graph representation | Uploaded target type | Corrected projection |
|---|---|---|---|
| DIM primary key; FACT primary key and both foreign keys | 32-character MD5 hexadecimal string | `BINARY(16)` | Validate 32 hex characters and decode with `TO_BINARY(..., 'HEX')` |
| DIM OSCAL UUID; FACT source and target UUID | Canonical 36-character dashed UUID | `VARCHAR(32)` | Validate canonical syntax and remove hyphens only for these physical columns |
| DIM metadata JSON | Mapped JSON with canonical UUIDs | `VARIANT` | Existing `PARSE_JSON` projection; payload content unchanged |
| Both DIM load timestamps | Existing graph audit timestamps | `TIMESTAMP_TZ(9)` | Existing explicit target-type cast |

Cell 4 already generates MD5 hex keys and canonical UUID5 identifiers. The fix
does not regenerate identifiers, truncate data, modify table definitions,
rewrite accepted mappings or change the registry. Hex decoding is reversible;
compact UUID storage preserves the same 128-bit UUID. Serialized OSCAL payload
UUIDs retain their hyphens.

The conversions use Snowflake's explicit
[TO_BINARY hexadecimal input format](https://docs.snowflake.com/en/sql-reference/functions/to_binary)
and [OCTET_LENGTH](https://docs.snowflake.com/en/sql-reference/functions/octet_length)
to check byte width, avoiding dependence on the session's binary input format.

## Guards and verification

- Only the four known key columns permit exact `BINARY(16)`. Other unsupported
  types still stop rather than receiving guessed conversions.
- Invalid or missing source identities stop before projection and target DML.
- Projected DIM and FACT primary keys must be non-null and unique before DML,
  including hex case variants which could collapse to one binary key.
- Binary key width is checked after projection. Other string capacity checks
  remain in place and no narrowing casts silently truncate values.
- Graph hierarchy checks remain on the original graph. Physical scope,
  ownership, MERGE and readback use projected physical keys consistently.
- Schema failures now print column/type metadata and the no-DML status in the
  aggregate report. Source values are not printed.
- The existing rollback rehearsal, baseline restore proof, repeated MERGEs,
  final COMMIT, readback, and uncertain-outcome safeguards remain unchanged.

Local verification: **32 focused pilot tests pass; 295 repository tests pass**.
New tests reproduce the uploaded schema and exercise reversible key/UUID
projection, payload preservation, invalid identities, binary collisions and
physical readback using local SQLite emulation. These tests do **not** claim
live Snowflake execution or persistence success.

## One next run

Open the [complete corrected pilot](../../notebooks/persistence/PILOT_SSP_ONE_RECORD_WRITE.py),
release `ssp-one-record-write-v2-binary16`.

1. Replace only the separate pilot Python cell in the accepted SSP notebook session.
2. Set `SSP_PILOT_MODE = "COMMIT"` near the top. Keep
   `CONFIG["EXECUTE_WRITES"] = False` in the normal mapper.
3. Pause other writers to these two DEV tables and run no concurrent notebook
   SQL in the pilot session. Run the pilot once, then post its aggregate report.

Do not rerun schema capture, registry setup, AR, or the SSP mapper while the
accepted Cell 7 outputs remain loaded. If the session restarted, rebuild only
the required accepted SSP outputs with Cells 1-7 and normal writes disabled.

Acceptance requires `ONE_RECORD_COMMITTED_AND_VERIFIED` and `PERSISTED: true`.
No corrected live run is recorded yet. A failure or uncertain outcome requires
review before retrying. Bulk SSP loading and AR persistence remain separate,
unaccepted work; no new Excel mapping is counted by this storage correction.
