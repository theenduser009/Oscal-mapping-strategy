✅ **Cell 7 passed. New verified baseline:**

```text
DIM  92,880 / 92,880
FACT 90,715 / 90,715
LOAD VERIFIED
```

Now we should **not manually guess `network-architecture`, `data-flow`, `system-information`, etc.** We can make the mapping file tell us every remaining nested object under `system-characteristics`.

Our earlier inventory missed deeper singleton objects. This next check fixes that properly and should replace the need to visually hunt through all 32 mappings.

### Next cell — remaining structural nodes under System Characteristics

```python
# ============================================================
# Find remaining System Characteristics structural nodes
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

BASE = "system-security-plan.system-characteristics"

# Actual mapped paths
mapped_paths = [
    r["OSCAL_ELEMENT_PATH"]
    for r in (
        canonical_mapping_df
        .filter(col("OSCAL_ELEMENT_PATH").startswith(BASE + "."))
        .select("OSCAL_ELEMENT_PATH")
        .distinct()
        .collect()
    )
    if r["OSCAL_ELEMENT_PATH"]
]

# Existing registry paths
registered_paths = {
    r["NODE_PATH"]
    for r in (
        element_registry_df
        .filter(col("OSCAL_MODEL_KEY") == "SSP")
        .select("NODE_PATH")
        .collect()
    )
}

# A structural node is a proper prefix of an actual mapped path.
# The final path segment is treated as the payload field.
candidates = set()

for full_path in mapped_paths:
    parts = full_path.split(".")

    # Do not include the final leaf field
    for i in range(3, len(parts)):
        prefix = ".".join(parts[:i])

        if prefix.startswith(BASE + "."):
            candidates.add(prefix)

print("=== Remaining System Characteristics Structural Nodes ===")

for path in sorted(candidates):
    status = (
        "REGISTERED"
        if path in registered_paths
        else "NOT REGISTERED"
    )

    print(status, " | ", path)
```

What I expect this to do is show something like:

```text
REGISTERED     | ...authorization-boundary
REGISTERED     | ...security-impact-level
REGISTERED     | ...status

NOT REGISTERED | ...network-architecture
NOT REGISTERED | ...data-flow
...
```

**But we will use the actual output, not that expectation.**

This is the better method going forward: every time we go deeper, the **real OSCAL paths in your mapping identify the structural parents automatically**. Then we check their source data and add confirmed ones to the registry.

Run only this next and show me the output.
