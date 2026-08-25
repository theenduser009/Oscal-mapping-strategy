Yes — let’s move to **model #3**. We’ll use the **same Authorization Package source** and first let the mapping CSV tell us what model has usable mappings next.

In the **DEV/reference notebook**, add one new Python cell at the bottom. **Read-only — no registry or mapper changes yet.**

```python
# ============================================================
# NEXT OSCAL MODEL INVENTORY
# READ ONLY
# ============================================================

from collections import defaultdict

model_inventory = defaultdict(lambda: {
    "mapping_rows": 0,
    "roots": set()
})

for row in canonical_mapping_df.collect():

    model = row["OSCAL_MODEL"]
    path = row["OSCAL_ELEMENT_PATH"]

    if model is None or path is None:
        continue

    model = str(model).strip()
    path = str(path).strip()

    if not model or not path:
        continue

    root = path.split(".")[0]

    model_inventory[model]["mapping_rows"] += 1
    model_inventory[model]["roots"].add(root)


print("=== OSCAL MODEL / ROOT INVENTORY ===")

for model in sorted(model_inventory):

    print("\nMODEL       :", model)
    print("MAPPING ROWS:", model_inventory[model]["mapping_rows"])

    for root in sorted(model_inventory[model]["roots"]):
        print("ROOT        :", root)
```

We’re looking for output roughly like:

```text
MODEL       : Security Assessment Plan
MAPPING ROWS: ...
ROOT        : assessment-plan

MODEL       : Assessment Results
MAPPING ROWS: ...
ROOT        : assessment-results
```

Don’t add anything to the registry yet.

**Run this cell and send me the output.** Then we’ll choose the third model based on the actual mapping data, not the diagram.
