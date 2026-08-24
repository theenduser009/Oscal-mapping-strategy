Yes. We should simplify **without touching the working load**.

Replace **Cell 3 and Cell 4 only** with these versions. **Do not change Cells 5, 6, or 7 yet.** This removes the unnecessary dependence on `CARDINALITY`, `MAPPING_TYPE`, etc. The runtime logic is driven by `OSCAL_ELEMENT_PATH` + the registry node boundaries.

### Cell 3 — Mapping + Registry

```python
# ============================================================
# Cell 3 — Canonical Mapping + Element Registry
# READ ONLY
# ============================================================

from snowflake.snowpark.functions import col


# ------------------------------------------------------------
# A. Canonical field mapping
#
# SOURCE_FIELD_NAME -> OSCAL_ELEMENT_PATH
#
# Other CSV columns may remain for traceability,
# but the hierarchy engine does NOT depend on them.
# ------------------------------------------------------------

canonical_mapping_df = (
    mapping_df
    .with_column_renamed(
        "ARCHER_FIELD_NAME",
        "SOURCE_FIELD_NAME"
    )
    .select(
        col("SOURCE_FIELD_NAME"),
        col("OSCAL_ELEMENT_PATH"),

        # retained only for traceability
        col("OSCAL_MODEL"),
        col("MAPPING_TYPE"),
        col("TRANSFORMATION_LOGIC")
    )
)


# ------------------------------------------------------------
# B. Element registry
#
# Registry defines ONLY which OSCAL paths become DIM nodes.
# ------------------------------------------------------------

element_registry_df = (
    session.table(
        CONFIG["ELEMENT_REGISTRY_TABLE"]
    )
    .filter(
        col("OSCAL_MODEL_KEY")
        == CONFIG["OSCAL_MODEL"]
    )
)


# ------------------------------------------------------------
# Compact validation
# ------------------------------------------------------------

print("=== Cell 3 ===")
print(
    "Canonical mapping rows:",
    canonical_mapping_df.count()
)

print(
    "Registry rows:",
    element_registry_df.count()
)

element_registry_df.select(
    "NODE_PATH",
    "ELEMENT_TYPE",
    "PARENT_NODE_PATH",
    "IS_ACTIVE"
).sort(
    "PROCESS_ORDER",
    "NODE_PATH"
).show()

print(
    "Cell 3 complete - mapping and registry ready"
)
```

### Cell 4 — Generic reusable engine functions

```python
# ============================================================
# Cell 4 — Generic OSCAL Mapping Functions
# ============================================================
#
# Main rule:
#
# SOURCE_FIELD_NAME
#       ->
# OSCAL_ELEMENT_PATH
#       ->
# deepest registered NODE_PATH owns the field
#
# No CARDINALITY decisions.
# No OSCAL_MODEL label parsing.
# No SSP-specific element names.
# No writes.
# ============================================================

import hashlib
import json

from snowflake.snowpark.functions import col


# ============================================================
# A. FROZEN IDENTITY
# ============================================================

def build_node_seed(
    source_system,
    source_table,
    content_id,
    node_type
):
    cid = (
        content_id.strip()
        if content_id is not None
        else ""
    )

    return (
        f"{source_system}|"
        f"{source_table}|"
        f"{cid}|"
        f"{node_type}"
    )


def compute_node_key(seed):
    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


def compute_node_uuid(seed):
    return hashlib.md5(
        seed.encode("utf-8")
    ).hexdigest().lower()


def build_edge_seed(
    source_node_key_hex,
    target_node_key_hex,
    edge_type="parent_of"
):
    return (
        f"{source_node_key_hex}::"
        f"{target_node_key_hex}::"
        f"{edge_type}"
    )


def compute_edge_key(seed):
    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


# ============================================================
# B. BASIC HELPERS
# ============================================================

def _row_to_dict(row):

    if isinstance(row, dict):
        return dict(row)

    if hasattr(row, "as_dict"):
        return row.as_dict()

    if hasattr(row, "asDict"):
        return row.asDict()

    raise TypeError(
        f"Unsupported row type: {type(row)}"
    )


def is_collection_node(node_path):
    """
    Collection structure comes directly from OSCAL path.
    """
    return "[]" in str(node_path)


# ============================================================
# C. SOURCE VALUE RESOLVER
# ============================================================

def resolve_json_path(obj, path):
    """
    Resolve SOURCE_FIELD_NAME against CURATED_JSON.

    Exact field name is attempted first.
    Dot notation is supported if needed.
    """

    if obj is None or not path:
        return None

    # Archer fields are normally direct JSON keys.
    if isinstance(obj, dict) and path in obj:
        return obj.get(path)

    current = obj

    for part in str(path).split("."):

        if current is None:
            return None

        if isinstance(current, dict):
            current = current.get(part)

        elif isinstance(current, list):

            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError):
                return None

        else:
            return None

    return current


# ============================================================
# D. PATH OWNERSHIP
# ============================================================

def get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    oscal_model_key=None
):
    """
    Determine ownership ONLY from OSCAL_ELEMENT_PATH.

    The deepest ACTIVE registered NODE_PATH that prefixes
    OSCAL_ELEMENT_PATH owns that mapping.

    Example:

    OSCAL_ELEMENT_PATH
      system-security-plan.metadata.last-modified

    NODE_PATH
      system-security-plan.metadata

    FIELD_RELATIVE_PATH
      last-modified
    """

    if oscal_model_key is None:
        oscal_model_key = CONFIG["OSCAL_MODEL"]

    registered_paths = [
        r["NODE_PATH"]
        for r in (
            element_registry_df
            .filter(
                (col("OSCAL_MODEL_KEY") == oscal_model_key)
                & (col("IS_ACTIVE") == True)
            )
            .select("NODE_PATH")
            .collect()
        )
        if r["NODE_PATH"]
    ]

    # Deepest node first.
    registered_paths = sorted(
        registered_paths,
        key=len,
        reverse=True
    )

    mappings = []

    rows = (
        canonical_mapping_df
        .filter(
            col("OSCAL_ELEMENT_PATH").is_not_null()
        )
        .collect()
    )

    for row in rows:

        mapping = _row_to_dict(row)

        element_path = mapping.get(
            "OSCAL_ELEMENT_PATH"
        )

        if not element_path:
            continue

        owner = None

        for candidate in registered_paths:

            if (
                element_path == candidate
                or element_path.startswith(
                    candidate + "."
                )
            ):
                owner = candidate
                break

        if owner != node_path:
            continue

        if element_path == owner:
            relative_path = None
        else:
            relative_path = element_path[
                len(owner) + 1:
            ]

        mapping["OWNER_NODE_PATH"] = owner
        mapping["FIELD_RELATIVE_PATH"] = relative_path

        mappings.append(mapping)

    return mappings


# ============================================================
# E. NESTED OSCAL PAYLOAD
# ============================================================

def set_nested_path(
    container,
    path_segments,
    value
):
    """
    Build nested JSON directly from the relative OSCAL path.

    Example:

    document-ids[].identifier

    ->
    {
        "document-ids": [
            {"identifier": value}
        ]
    }
    """

    if not path_segments:
        return

    current = container

    for i, segment in enumerate(path_segments):

        is_last = (
            i == len(path_segments) - 1
        )

        # -----------------------------------------
        # Array path
        # -----------------------------------------
        if segment.endswith("[]"):

            key = segment[:-2]

            if key not in current:
                current[key] = []

            if not isinstance(current[key], list):
                current[key] = []

            if is_last:

                if isinstance(value, list):
                    current[key].extend(value)
                else:
                    current[key].append(value)

                return

            if not current[key]:
                current[key].append({})

            if not isinstance(
                current[key][0],
                dict
            ):
                current[key][0] = {}

            current = current[key][0]

        # -----------------------------------------
        # Normal object path
        # -----------------------------------------
        else:

            if is_last:
                current[segment] = value
                return

            if (
                segment not in current
                or not isinstance(
                    current[segment],
                    dict
                )
            ):
                current[segment] = {}

            current = current[segment]


# ============================================================
# F. BUILD ONE NODE PAYLOAD
# ============================================================

def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):
    """
    Generic mapping:

        SOURCE_FIELD_NAME
             ->
        FIELD_RELATIVE_PATH

    No CARDINALITY logic.
    No MAPPING_TYPE logic.
    No SSP-specific logic.
    """

    payload = {}

    record = _row_to_dict(
        source_record
    )

    json_data = record.get(
        source_json_field
    )

    if isinstance(json_data, str):

        try:
            source_obj = json.loads(json_data)

        except json.JSONDecodeError:
            source_obj = {}

    elif isinstance(
        json_data,
        (dict, list)
    ):
        source_obj = json_data

    else:
        source_obj = {}

    for mapping in mappings:

        source_field = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        target_path = mapping.get(
            "FIELD_RELATIVE_PATH"
        )

        if not source_field:
            continue

        # Exact node path itself is not a nested payload field.
        if not target_path:
            continue

        value = resolve_json_path(
            source_obj,
            source_field
        )

        if value in (
            None,
            "",
            [],
            {}
        ):
            continue

        segments = [
            p
            for p in target_path.split(".")
            if p
        ]

        set_nested_path(
            payload,
            segments,
            value
        )

    return payload


print(
    "Cell 4 loaded - path-driven reusable engine ready"
)
```

### Then stop

Do **not modify Cell 5 yet**.

Run:

```text
Cell 3
Cell 4
Cell 5
```

We want the exact same proven result:

```text
Source records: 2165
Canonical nodes: 8304
Canonical edges: 6139
```

If we get that, we freeze this simpler architecture.

Then we replace **Cell 5 once**, cleanly, to support `[]` collection nodes from the OSCAL path. No more little patches.
