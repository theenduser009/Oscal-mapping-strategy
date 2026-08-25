Great — **45 Assessment Results mappings**. And this is the first model where we need to be extra careful before registering anything.

From your output I can already see this shape:

```text
assessment-results
    └── results[]
          ├── findings[]
          └── observations[]
```

That means we have a **collection inside a collection**. SSP and POA&M did not require that pattern.

Our current generic mapper safely handles:

```text
singleton → collection
```

but we deliberately did **not** implement:

```text
collection → collection
```

until we had real data proving how the child instance belongs to the correct parent instance.

So **do not add Assessment Results to the registry yet.**

### Next step only

Your `.show()` displayed only part of the 45 rows. Run this read-only summary:

```python
# ============================================================
# Assessment Results — Structural Path Inventory
# READ ONLY
# ============================================================

print("=== ASSESSMENT RESULTS DISTINCT PATHS ===")

(
    assessment_results_paths
    .group_by("OSCAL_ELEMENT_PATH")
    .count()
    .sort("OSCAL_ELEMENT_PATH")
    .show()
)
```

I want to see every distinct structure under:

```text
assessment-results
```

especially whether we have paths such as:

```text
assessment-results.results[]
assessment-results.results[].findings[]
assessment-results.results[].observations[]
assessment-results.results[].risks[]
assessment-results.results[].reviewed-controls
```

Send me that output.

Then we inspect the actual Archer fields behind `results[]` and determine **what identifies one result instance** before touching the registry or mapper.
