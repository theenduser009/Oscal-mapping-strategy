Yes — this output already tells us something important. 👍

The node test worked. Right now Cell 5 generated only:

components   → 14792
props        → 15120

But it generated zero nodes for:

component
links
responsible-roles
protocols

So we have found the real issue: the SSP component branch is not being traversed all the way down yet. This is not just a FACT problem.

The second error is only from my diagnostic filter. Snowpark is treating the path string incorrectly in .contains(). Don't change Cells 1–7.

Replace only the edges diagnostic with this:

print("=== COMPONENT BRANCH EDGES ===")

final_edges_df.filter(
    col("SOURCE_NODE_PATH").like(
        "%system-security-plan.system-implementation.components%"
    )
    |
    col("TARGET_NODE_PATH").like(
        "%system-security-plan.system-implementation.components%"
    )
).group_by(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).count().sort(
    "SOURCE_NODE_PATH",
    "TARGET_NODE_PATH"
).show()

Run just that.

But we already have our first major finding:

Registry expects:
components[]
   ↓
component
   ├── props[]
   ├── links[]
   ├── responsible-roles[]
   └── protocols[]

Actual generated nodes:
components ✅
props      ✅
component  ❌
links      ❌
responsible-roles ❌
protocols  ❌

That is exactly where we need to focus next. Do not modify Cell 5 yet. Send me the edge output from this corrected query first, and then we'll trace why Cell 4/5 skips component.