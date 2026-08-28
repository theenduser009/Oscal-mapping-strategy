Perfect — document-ids[] is behaving cleanly too. ✅

For the test record, you have:

NODE: system-security-plan.metadata.document-ids[]
OWNED MAPPINGS: 1

TRACKING_ID
→ system-security-plan.metadata.document-ids[].identifier

and the payload:

{
  "identifier": 565189
}

That matches the registry setup pretty well: document-ids[] is a collection and its INSTANCE_KEY_RULE = VALUE, so the collection instance can be keyed by the actual identifier value.

Next I want to validate the graph structure for this collection — node count, uniqueness, null keys, and incoming edges.

Run this:

from snowflake.snowpark.functions import col

doc_ids_path = "system-security-plan.metadata.document-ids[]"

print("=== DOCUMENT IDS GRAPH CHECK ===")

doc_ids_df = final_nodes_df.filter(
    col("NODE_PATH") == doc_ids_path
)

print("Total document-id nodes:")
print(doc_ids_df.count())

print("Distinct NODE_KEYs:")
print(
    doc_ids_df
    .select("NODE_KEY")
    .distinct()
    .count()
)

print("Null NODE_KEYs:")
print(
    doc_ids_df
    .filter(col("NODE_KEY").is_null())
    .count()
)

print("\nEdges into document-ids[]:")
(
    final_edges_df
    .filter(col("TARGET_NODE_PATH") == doc_ids_path)
    .group_by("SOURCE_NODE_PATH", "TARGET_NODE_PATH")
    .count()
    .show()
)

I expect the counts to be very close to the number of Authorization Package records with a usable TRACKING_ID. If total nodes = distinct keys, null keys = 0, and edge count matches the node count, then document-ids[] is validated and we move to the more interesting responsible-parties[] collection.