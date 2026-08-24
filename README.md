Exactly. **Parameterization can wait. The mapper is proven; now we use it to onboard the other OSCAL models.**

And we should **not write another mapper**. From here the work is:

```text
Same generic mapper
        +
different mapping paths
        +
registry rows
        =
next OSCAL model
```

I recommend we do the models one at a time, starting from what is actually present in your 608-row mapping—not from assumptions.

### Next step only: inventory the remaining OSCAL roots

Run this read-only cell in the **old/reference notebook or a temporary cell in the mapper**:

```python
# ============================================================
# Remaining OSCAL Model / Root Inventory
# READ ONLY
# ============================================================

from collections import Counter

root_counts = Counter()

for row in canonical_mapping_df.select(
    "OSCAL_ELEMENT_PATH"
).collect():

    path = row["OSCAL_ELEMENT_PATH"]

    if not path:
        continue

    root = str(path).split(".")[0]

    root_counts[root] += 1


print("=== OSCAL ROOT INVENTORY ===")

for root, count in sorted(root_counts.items()):
    print(f"{root:45} {count}")
```

This should expose roots such as, depending on the actual CSV:

```text
system-security-plan
assessment-plan
assessment-results
plan-of-action-and-milestones
...
```

Then we choose the **next root from the real mapping** and do exactly what worked for SSP:

```text
1. inspect its mapped hierarchy
2. inspect actual Archer values where identity is unclear
3. populate registry
4. run the SAME mapper
5. validate DIM + FACT
```

No new 700-line notebook. No model-specific Python.

And yes, we already learned something about POA&M: `POAMS` in the Authorization Package is a list of `{ContentId, LevelId}` references. So when we get to POA&M, we must distinguish **the Auth Package → POA&M relationship** from the actual **POA&M document contents**. We won't pretend those references are the whole POA&M.

Run this root inventory next and send me the output. Then I’ll tell you which model I recommend we onboard first.
