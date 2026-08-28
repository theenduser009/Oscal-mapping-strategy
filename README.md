Excellent — this is exactly what we wanted to see. 🎯

Your result is:

props[] nodes = 15,120
system-characteristics → props[] edges = 15,120

So props[] is not being collapsed to one prop per Authorization Package. The mapper is correctly generating multiple property instances.

That means we can mark this branch structurally validated:

system-characteristics
        │
        ├── system-ids[]       2,813 nodes / 2,813 edges ✅
        │
        └── props[]           15,120 nodes / 15,120 edges ✅

One important validation before we leave props[]

We need to ensure those 15,120 nodes are unique, not duplicate graph nodes.

Run this next:

print("=== PROPS UNIQUENESS CHECK ===")

props_df = final_nodes_df.filter(
    col("NODE_PATH") == props_path
)

print("Total props:")
print(props_df.count())

print("Distinct PKs:")
print(
    props_df
    .select("PK_ELEMENT_HASH")
    .distinct()
    .count()
)

print("Null PKs:")
print(
    props_df
    .filter(col("PK_ELEMENT_HASH").is_null())
    .count()
)

Expected:

Total props:      15120
Distinct PKs:     15120
Null PKs:             0

If we get that, props[] is done and we move to the next SSP child branch.