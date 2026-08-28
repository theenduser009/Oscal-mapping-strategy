Great. Run this read-only impact check next. It does not write anything.

from snowflake.snowpark.functions import col

print("=== TARGET IMPACT CHECK ===")

dim_table = CONFIG["TARGET_DIM"]
fact_table = CONFIG["TARGET_FACT"]

dim_pk = CONFIG.get(
    "DIM_PK_COLUMN",
    "PK_OSCAL_SSP_ELEMENT_HASH"
)

fact_pk = CONFIG.get(
    "FACT_PK_COLUMN",
    "PK_FACT_OSCAL_DEPENDENCY_HASH"
)

# Recreate the exact key sets that would be loaded
dim_keys_df = final_nodes_df.select(
    col("NODE_KEY").alias(dim_pk)
)

fact_keys_df = final_edges_df.select(
    col("EDGE_KEY").alias(fact_pk)
)

# DIM impact
dim_existing = (
    dim_keys_df
    .join(
        session.table(dim_table).select(col(dim_pk)),
        dim_pk,
        "inner"
    )
    .count()
)

dim_new = (
    dim_keys_df.count()
    - dim_existing
)

# FACT impact
fact_existing = (
    fact_keys_df
    .join(
        session.table(fact_table).select(col(fact_pk)),
        fact_pk,
        "inner"
    )
    .count()
)

fact_new = (
    fact_keys_df.count()
    - fact_existing
)

print("\nDIM")
print("Would process :", dim_keys_df.count())
print("Already exist :", dim_existing)
print("Would insert  :", dim_new)

print("\nFACT")
print("Would process :", fact_keys_df.count())
print("Already exist :", fact_existing)
print("Would insert  :", fact_new)

print("\nEXECUTE_WRITES =", CONFIG["EXECUTE_WRITES"])

This tells us, before DML:

DIM:  how many will MATCH vs INSERT
FACT: how many will MATCH vs INSERT

Keep EXECUTE_WRITES = False. Send me those four numbers, and then we can decide whether the first DEV write is safe.