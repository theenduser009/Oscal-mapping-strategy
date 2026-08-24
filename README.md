# ============================================================
# Cell 7 — Post-Load Verification
# ============================================================

dim_table = CONFIG["TARGET_DIM"]
fact_table = CONFIG["TARGET_FACT"]

dim_pk = [
    f.name.upper()
    for f in session.table(dim_table).schema.fields
    if f.name.upper().startswith("PK_")
    and f.name.upper().endswith("_HASH")
][0]

fact_pk = [
    f.name.upper()
    for f in session.table(fact_table).schema.fields
    if f.name.upper().startswith("PK_")
    and f.name.upper().endswith("_HASH")
][0]


dim_matches = session.sql(f"""
    SELECT COUNT(*) AS CNT
    FROM TMP_OSCAL_DIM_LOAD s
    JOIN {dim_table} t
      ON s.{dim_pk} = t.{dim_pk}
""").collect()[0]["CNT"]


fact_matches = session.sql(f"""
    SELECT COUNT(*) AS CNT
    FROM TMP_OSCAL_FACT_LOAD s
    JOIN {fact_table} t
      ON s.{fact_pk} = t.{fact_pk}
""").collect()[0]["CNT"]


expected_dim = canonical_nodes_df.count()
expected_fact = canonical_edges_df.count()


print("=== Post-Load Verification ===")
print(f"DIM expected : {expected_dim}")
print(f"DIM matched  : {dim_matches}")

print(f"FACT expected: {expected_fact}")
print(f"FACT matched : {fact_matches}")


if (
    dim_matches == expected_dim
    and fact_matches == expected_fact
):
    print("✅ LOAD VERIFIED")
else:
    print("❌ LOAD VERIFICATION FAILED")
