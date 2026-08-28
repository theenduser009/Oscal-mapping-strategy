Great — this is very clean. We now know exactly what your active metadata graph contains:

system-security-plan
└── metadata                         SINGLETON
    ├── document-ids[]               COLLECTION / VALUE
    └── responsible-parties[]        COLLECTION / SOURCE_FIELD_NAME+ID

Notice something important: there are no deeper active children below those two in your registry. So this branch is much smaller than system-characteristics.

Let's validate metadata itself first, exactly like we did before. Run:

from snowflake.snowpark.functions import col

metadata_path = "system-security-plan.metadata"

print("=== METADATA GRAPH CHECK ===")

metadata_df = final_nodes_df.filter(
    col("NODE_PATH") == metadata_path
)

print("Total metadata nodes:")
print(metadata_df.count())

print("Distinct NODE_KEYs:")
print(
    metadata_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    metadata_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into metadata:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == metadata_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

Because metadata is SINGLETON under each SSP, I expect roughly 2,813 metadata nodes and 2,813 SSP → metadata edges.

Run only this first. Then we'll inspect document-ids[] and responsible-parties[] individually, because their instance-key rules are different and we should validate them differently.