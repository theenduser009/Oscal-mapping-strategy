Perfect. This registry piece looks structurally right:

system-implementation → IS_COLLECTION = FALSE, SINGLETON

components[] → child of system-implementation

IS_COLLECTION = TRUE

INSTANCE_KEY_RULE = CONTENT_ID

ITEM_PATH = $


Now only validate system-implementation first before touching components[].

Run this Python cell:

from snowflake.snowpark.functions import col

print("=== SYSTEM IMPLEMENTATION GRAPH CHECK ===")

si_path = "system-security-plan.system-implementation"

si_df = final_nodes_df.filter(
    col("NODE_PATH") == si_path
)

print("Total system-implementation nodes:")
print(si_df.count())

print("Distinct NODE_KEYs:")
print(
    si_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    si_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into system-implementation:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == si_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

Based on everything we've seen so far, I would expect something around:

Total system-implementation nodes: 2813
Distinct NODE_KEYs:                2813
Null NODE_KEYs:                    0

system-security-plan
    → system-implementation

But don't assume 2813—let the mapper prove it.

Send me that output. Then components[] is the interesting one, because CONTENT_ID collection identity needs a different validation than the singleton nodes we've been checking.