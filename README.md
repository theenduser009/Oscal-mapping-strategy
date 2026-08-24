Yes. **Next step is Cell 8 only**: build a read-only SSP hierarchy inventory from the CSV and compare it with the registry.

It uses only `OSCAL_ELEMENT_PATH` + registry — no cardinality logic, no writes.

```python
# ============================================================
# Cell 8 — SSP Hierarchy Inventory
# READ ONLY
# ============================================================

from collections import defaultdict
from snowflake.snowpark.functions import col

SSP_ROOT = "system-security-plan"


# ------------------------------------------------------------
# 1. Get every distinct SSP mapping path
# ------------------------------------------------------------

ssp_paths = [
    r["OSCAL_ELEMENT_PATH"]
    for r in (
        canonical_mapping_df
        .filter(
            col("OSCAL_ELEMENT_PATH").startswith(
                SSP_ROOT
            )
        )
        .select("OSCAL_ELEMENT_PATH")
        .distinct()
        .collect()
    )
    if r["OSCAL_ELEMENT_PATH"]
]


# ------------------------------------------------------------
# 2. Current SSP registry
# ------------------------------------------------------------

registry_rows = (
    element_registry_df
    .filter(
        col("OSCAL_MODEL_KEY") == "SSP"
    )
    .collect()
)

registry = {
    r["NODE_PATH"]: r
    for r in registry_rows
}


# ------------------------------------------------------------
# 3. Discover structural candidates
#
# Candidate rule:
#   - SSP root
#   - direct child of SSP root
#   - any repeated [] branch
#
# This does NOT automatically make them DIM nodes.
# ------------------------------------------------------------

candidate_counts = defaultdict(int)

for full_path in ssp_paths:

    parts = full_path.split(".")

    for depth in range(1, len(parts) + 1):

        prefix = ".".join(
            parts[:depth]
        )

        is_root = (
            prefix == SSP_ROOT
        )

        is_direct_child = (
            depth == 2
        )

        is_collection = (
            "[]" in parts[depth - 1]
        )

        if (
            is_root
            or is_direct_child
            or is_collection
        ):
            candidate_counts[prefix] += 1


# ------------------------------------------------------------
# 4. Build readable hierarchy report
# ------------------------------------------------------------

rows = []

for node_path in sorted(
    candidate_counts.keys()
):

    parts = node_path.split(".")

    parent_path = (
        ".".join(parts[:-1])
        if len(parts) > 1
        else None
    )

    registry_row = registry.get(
        node_path
    )

    rows.append({
        "NODE_PATH": node_path,
        "PARENT_PATH": parent_path,
        "IS_COLLECTION": "[]" in node_path,
        "REGISTERED": registry_row is not None,
        "ACTIVE": (
            registry_row["IS_ACTIVE"]
            if registry_row is not None
            else None
        ),
        "MAPPING_COUNT": candidate_counts[
            node_path
        ]
    })


# ------------------------------------------------------------
# 5. Output
# ------------------------------------------------------------

print("=== SSP Hierarchy Inventory ===")
print("Distinct SSP mapping paths:", len(ssp_paths))
print("Structural candidates:", len(rows))

for r in rows:

    status = (
        "ACTIVE"
        if r["ACTIVE"] is True
        else
        "INACTIVE"
        if r["ACTIVE"] is False
        else
        "NOT REGISTERED"
    )

    print(
        "\n",
        r["NODE_PATH"],
        "\n  Parent:",
        r["PARENT_PATH"],
        "\n  Collection:",
        r["IS_COLLECTION"],
        "\n  Registry:",
        status,
        "\n  Mapping paths:",
        r["MAPPING_COUNT"]
    )
```

Run Cell 8 and send me the output.

Then we’ll identify the **missing SSP nodes only** and add those to the registry. We will **not modify Cells 3–7**.
