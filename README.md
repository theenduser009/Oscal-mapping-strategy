Perfect — this tells us something important:

**For the current mapping file, `system-characteristics` is now structurally complete.** ✅

The inventory found only these deeper structural parents:

```text
system-characteristics
├── authorization-boundary     REGISTERED
├── security-impact-level      REGISTERED
├── status                     REGISTERED
└── system-ids[]               REGISTERED
```

There are **no remaining `NOT REGISTERED` structural paths** under `system-characteristics`.

So we stop touching that branch.

### Next branch: `system-implementation`

Now do the exact same check against the real mapping, changing only the base path:

```python
# ============================================================
# Remaining System Implementation Structural Nodes
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

BASE = "system-security-plan.system-implementation"

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

registered_paths = {
    r["NODE_PATH"]
    for r in (
        element_registry_df
        .filter(col("OSCAL_MODEL_KEY") == "SSP")
        .select("NODE_PATH")
        .collect()
    )
}

candidates = set()

for full_path in mapped_paths:
    parts = full_path.split(".")

    # Proper structural prefixes only; exclude final payload field.
    for i in range(3, len(parts)):
        prefix = ".".join(parts[:i])

        if prefix.startswith(BASE + "."):
            candidates.add(prefix)

print("=== Remaining System Implementation Structural Nodes ===")

if not candidates:
    print("No deeper structural nodes found in current mapping.")
else:
    for path in sorted(candidates):
        status = (
            "REGISTERED"
            if path in registered_paths
            else "NOT REGISTERED"
        )

        print(status, " | ", path)
```

This is now our method branch by branch:

**mapping paths → discover structural parents → compare registry → inspect only missing ones → register → engine builds DIM/FACT.**

Run this next and send me the output.
