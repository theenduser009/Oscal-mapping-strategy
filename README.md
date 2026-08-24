Good — but one important correction before we move on.

This output shows only:

```text
REGISTERED | system-security-plan.metadata.document-ids[]
```

It does **not** show `responsible-parties[]` because the little structural-prefix check excludes the final path itself. In your mapping, `responsible-parties[]` is itself the final mapped path, so the check misses it.

We already know it is registered and working:

```text
metadata
├── document-ids[]          ✅
└── responsible-parties[]   ✅
```

So instead of continuing branch-by-branch with more cells, I want to do **one final SSP-wide structural audit** that catches both intermediate objects **and terminal `[]` collections**.

Run this next:

```python
# ============================================================
# Final SSP Structural Registry Audit
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col

ROOT = "system-security-plan"

mapped_paths = [
    r["OSCAL_ELEMENT_PATH"]
    for r in (
        canonical_mapping_df
        .filter(col("OSCAL_ELEMENT_PATH").startswith(ROOT))
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

candidates = {ROOT}

for full_path in mapped_paths:
    parts = full_path.split(".")

    # All intermediate structural parents
    for i in range(2, len(parts)):
        candidates.add(".".join(parts[:i]))

    # Terminal collection paths are structural nodes too
    if full_path.endswith("[]"):
        candidates.add(full_path)


print("=== FINAL SSP STRUCTURAL AUDIT ===")

missing = []

for path in sorted(candidates):
    status = "REGISTERED" if path in registered_paths else "NOT REGISTERED"

    print(status, "|", path)

    if status == "NOT REGISTERED":
        missing.append(path)

print("\nMissing structural nodes:", len(missing))
```

This is better than doing metadata, system-implementation, system-characteristics one at a time.

The key output is simply:

```text
Missing structural nodes: ?
```

If it says `0`, then **every structural node represented by the current SSP mapping is registered**. At that point we can confidently stop hierarchy discovery and move to the production wrapper.
