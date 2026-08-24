Good — that means **`system-implementation` is complete for the current mapping too.** ✅

So far:

```text
system-security-plan
├── metadata                  ← still need final structural check
├── system-characteristics    ✅ complete
└── system-implementation     ✅ complete
    └── components[]
```

### Next step: check `metadata`

Run the same structural-prefix check with:

```python
# ============================================================
# Remaining Metadata Structural Nodes
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

BASE = "system-security-plan.metadata"

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

    for i in range(2, len(parts)):
        prefix = ".".join(parts[:i])

        if prefix.startswith(BASE + "."):
            candidates.add(prefix)

print("=== Remaining Metadata Structural Nodes ===")

if not candidates:
    print("No deeper structural nodes found in current mapping.")
else:
    for path in sorted(candidates):
        status = (
            "REGISTERED"
            if path in registered_paths
            else "NOT REGISTERED"
        )

        print(status, "|", path)
```

We already expect at least:

```text
metadata.document-ids[]          REGISTERED
metadata.responsible-parties[]   REGISTERED
```

But we’ll trust the output, not assumptions.

If there are no `NOT REGISTERED` rows, then **metadata is complete too**, and we’ll be very close to saying the entire mapped SSP hierarchy has been exhausted.
