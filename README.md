Yes. I read both screenshots carefully. **We are very close, but I want three small corrections before we freeze Cell 1.** These are exactly the kinds of things that would otherwise force another refactor later.

The overall Cell 1 structure is now correct: imports, session, CONFIG, no functions, no DIM/FACT writes. Keep that.

### 1. Remove `ROOT_NODE_PATH_PREFIX`

This line should **not** exist in Cell 1:

```python
ROOT_NODE_PATH_PREFIX = "system-security-plan"
```

That makes the supposedly generic engine SSP-specific again.

The root must come later from `element_registry_df`:

```text
system-security-plan
PARENT_NODE_PATH = NULL
```

For POA&M the root will be different. We should never hardcode the root into the engine.

### 2. Remove `edge_type_default = "parent_of"`

I see:

```python
"edge_type_default": "parent_of"
```

Don't freeze that yet.

`DEPENDENCY_TYPE` should eventually be determined by relationship metadata/registry. We haven't approved that contract yet. Otherwise we may later discover that some relationships are `contains`, `references`, etc., and have to undo this.

### 3. Add the model explicitly

Add:

```python
"OSCAL_MODEL": "SSP",
```

This is the clean generic way to say:

> This run is processing SSP.

Then later exactly the same engine can run:

```python
"OSCAL_MODEL": "POAM"
```

without changing Python logic.

---

### One more cleanup I recommend

I would also remove these from Cell 1 for now:

```python
SEED_SEPARATOR = "|"
EDGE_SEED_SEPARATOR = "::"
LEGACY_SEED_FORMAT = ...
```

Why? Your **existing approved identity functions already define those exact formats themselves**. Having them both in constants **and** hardcoded inside the functions gives us two sources of truth.

We are preserving the old functions unchanged for compatibility, so let the functions own their V1 format for now.

`identity_version = "v1_legacy_singleton"` is good. **Keep that.**

`node_uuid_policy = "md5_32char_lowercase_hex"` is also okay to keep because it documents the current identity contract.

---

## Final Cell 1 contract

I want Cell 1 to be this simple conceptually:

```python
# imports

session = get_active_session()

CONFIG = {
    "RUN_ID": "<bind-run-id>",
    "OSCAL_MODEL": "SSP",

    "SOURCE_SYSTEM_NAME": "ARCHER",
    "SOURCE_TABLE_NAME": "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW",
    "RAW_TABLE": "...",

    "TARGET_DIM": "...DIM_OSCAL_SSP_ELEMENT",
    "TARGET_FACT": "...FACT_OSCAL_SSP_DEPENDENCY",

    "identity_version": "v1_legacy_singleton",
    "node_uuid_policy": "md5_32char_lowercase_hex"
}
```

That's enough.

Notice what is deliberately **NOT** there:

```text
system-security-plan root path
metadata path
import-profile path
parent relationship
edge/dependency type
mapping rules
node builders
hash functions
JSON functions
```

Those belong to metadata/functions later.

### Send this to the other AI

> Cell 1 is almost approved. Make ONLY these final corrections:
>
> 1. Add `"OSCAL_MODEL": "SSP"` to CONFIG.
> 2. Remove `ROOT_NODE_PATH_PREFIX = "system-security-plan"`. Root must come from `element_registry_df`, not hardcoded configuration.
> 3. Remove `"edge_type_default": "parent_of"`. Dependency type will be metadata-driven and has not been approved yet.
> 4. Remove `SEED_SEPARATOR`, `EDGE_SEED_SEPARATOR`, and `LEGACY_SEED_FORMAT` from Cell 1 because the existing approved V1 identity functions already own those formats. Do not create two sources of truth.
> 5. Keep `identity_version = "v1_legacy_singleton"` and `node_uuid_policy = "md5_32char_lowercase_hex"` for compatibility.
> 6. Do not add any functions or SSP paths.
>
> Show the corrected Cell 1 only and STOP.

After those changes, **I will consider Cell 1 frozen**. We don't come back and remodel it unless an actual technical requirement forces us to.

Then Cell 2 has exactly one job: **load `source_df` and the actual mapping CSV as `mapping_df` — no transformations yet.**
