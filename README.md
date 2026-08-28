Yes — this aligns with what I’d expect for the write phase, and the overall pattern is sound.

The important pieces are right: DIM merges on the deterministic node key, FACT merges on the deterministic edge key, matched rows update non-PK columns, and unmatched rows insert. That gives you the idempotent behavior we want.

Before turning EXECUTE_WRITES = True, I would verify only three things in Cell 6:

dim_pk really resolves to the physical DIM PK column that receives NODE_KEY.

fact_pk really resolves to the physical FACT PK column that receives EDGE_KEY.

dim_load_df and fact_load_df have no duplicate PK values before the MERGE. Snowflake MERGE can become problematic if the source temp view has duplicate keys.


So the immediate next step is not to change the merge SQL. Run one read-only pre-write validation against the actual load DataFrames:

from snowflake.snowpark.functions import col

print("=== PRE-WRITE LOAD VALIDATION ===")

print("DIM rows:", dim_load_df.count())
print(
    "DIM distinct PKs:",
    dim_load_df.select(dim_pk).distinct().count()
)
print(
    "DIM null PKs:",
    dim_load_df.filter(col(dim_pk).is_null()).count()
)

print()

print("FACT rows:", fact_load_df.count())
print(
    "FACT distinct PKs:",
    fact_load_df.select(fact_pk).distinct().count()
)
print(
    "FACT null PKs:",
    fact_load_df.filter(col(fact_pk).is_null()).count()
)

What we want is:

DIM rows = DIM distinct PKs
DIM null PKs = 0

FACT rows = FACT distinct PKs
FACT null PKs = 0

If that passes, then I’d be comfortable with the next step being the first DEV write with EXECUTE_WRITES = True.

One thing I would not do yet is truncate either target table. With deterministic MERGE keys, the whole point is to prove the load is idempotent without destructive resets.