# ============================================================
# Cell 4 — Reusable Functions
# ============================================================
# Cells 1–3 are frozen.
#
# This cell defines reusable mechanics only.
#
# NO node construction
# NO canonical_nodes_df
# NO canonical_edges_df
# NO DIM / FACT writes
# NO MERGE
# NO identity redesign
# ============================================================

import hashlib
import json

from snowflake.snowpark.functions import col


# ============================================================
# A. IDENTITY HELPERS — FROZEN V1 CONTRACT
# ============================================================

def build_node_seed(source_system, source_table, content_id, node_type):
    """
    Frozen singleton V1 node identity.

    Format:
    SOURCE_SYSTEM|SOURCE_TABLE|CONTENT_ID|NODE_TYPE
    """
    cid = content_id.strip() if content_id is not None else ""

    return (
        f"{source_system}|"
        f"{source_table}|"
        f"{cid}|"
        f"{node_type}"
    )


def compute_node_key(seed):
    """
    MD5 digest bytes -> BINARY(16)
    """
    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


def compute_node_uuid(seed):
    """
    Deterministic 32-character lowercase MD5 hex.
    """
    return hashlib.md5(
        seed.encode("utf-8")
    ).hexdigest().lower()


def build_edge_seed(
    source_node_key_hex,
    target_node_key_hex,
    edge_type="parent_of"
):
    """
    Frozen directional edge identity.

    SOURCE = parent
    TARGET = child

    Format:
    SOURCE_KEY_HEX::TARGET_KEY_HEX::EDGE_TYPE
    """
    return (
        f"{source_node_key_hex}::"
        f"{target_node_key_hex}::"
        f"{edge_type}"
    )


def compute_edge_key(seed):
    """
    MD5 digest bytes -> BINARY(16)
    """
    return hashlib.md5(
        seed.encode("utf-8")
    ).digest()


# ============================================================
# B. SOURCE JSON RESOLVER
# ============================================================

def resolve_json_path(obj, path):
    """
    Resolve a source field/path from CURATED_JSON.

    Current mapping CSV does not contain SOURCE_JSON_PATH,
    therefore SOURCE_FIELD_NAME is used.

    Supports:
        FIELD
        OBJECT.FIELD
        ARRAY[]
        ARRAY.0.FIELD

    For [] arrays, returns the array to the caller.
    """

    if obj is None or not path:
        return None

    # Exact key first.
    # Important in case a source key itself contains dots.
    if isinstance(obj, dict) and path in obj:
        return obj.get(path)

    current = obj
    parts = str(path).split(".")

    for part in parts:

        if current is None:
            return None

        # Array notation: field[]
        if part.endswith("[]"):

            key = part[:-2]

            if isinstance(current, dict):
                current = current.get(key)

            else:
                return None

            if isinstance(current, list):
                # Caller handles the returned collection.
                return current

            return None

        # Standard dictionary key
        if isinstance(current, dict):
            current = current.get(part)

        # Numeric list index
        elif isinstance(current, list):

            try:
                idx = int(part)

                if 0 <= idx < len(current):
                    current = current[idx]
                else:
                    return None

            except (ValueError, TypeError):
                return None

        else:
            return None

    return current


# ============================================================
# C. MAPPING OWNERSHIP HELPER
# ============================================================

def _row_to_dict(row):
    """
    Convert Snowpark Row or dict into a normal Python dict.
    """

    if isinstance(row, dict):
        return dict(row)

    if hasattr(row, "as_dict"):
        return row.as_dict()

    if hasattr(row, "asDict"):
        return row.asDict()

    raise TypeError(
        f"Unsupported row type: {type(row)}"
    )


def get_mappings_for_node(
    canonical_mapping_df,
    element_registry_df,
    node_path,
    oscal_model_key=None
):
    """
    Return field mappings owned by one registered OSCAL node.

    Ownership rule:
        mapping belongs to the deepest registered NODE_PATH
        that is a segment-safe prefix of OSCAL_ELEMENT_PATH.

    Returned mappings are enriched with:

        OWNER_NODE_PATH
        FIELD_RELATIVE_PATH

    Example:

        OSCAL_ELEMENT_PATH:
        system-security-plan.metadata.document-ids[].identifier

        OWNER_NODE_PATH:
        system-security-plan.metadata

        FIELD_RELATIVE_PATH:
        document-ids[].identifier
    """

    if oscal_model_key is None:
        oscal_model_key = CONFIG["OSCAL_MODEL"]

    # Get active nodes for selected OSCAL model.
    active_node_rows = (
        element_registry_df
        .filter(
            (col("OSCAL_MODEL_KEY") == oscal_model_key)
            & (col("IS_ACTIVE") == True)
        )
        .select("NODE_PATH")
        .collect()
    )

    active_node_paths = [
        row["NODE_PATH"]
        for row in active_node_rows
        if row["NODE_PATH"]
    ]

    # Deepest paths first.
    active_node_paths = sorted(
        active_node_paths,
        key=len,
        reverse=True
    )

    if not active_node_paths:
        return []

    # Mapping CSV is small metadata (currently 608 rows).
    mapping_rows = canonical_mapping_df.collect()

    owned_mappings = []

    for mapping_row in mapping_rows:

        mapping = _row_to_dict(mapping_row)

        element_path = mapping.get(
            "OSCAL_ELEMENT_PATH"
        )

        if not element_path:
            continue

        owner_node_path = None

        # Find deepest registered node.
        for candidate_node_path in active_node_paths:

            if (
                element_path == candidate_node_path
                or element_path.startswith(
                    candidate_node_path + "."
                )
            ):
                owner_node_path = candidate_node_path
                break

        if owner_node_path is None:
            continue

        # Only return mappings for requested node.
        if owner_node_path != node_path:
            continue

        # Derive path relative to owner node.
        if element_path == owner_node_path:

            field_relative_path = None

        else:

            field_relative_path = element_path[
                len(owner_node_path) + 1:
            ]

        enriched = dict(mapping)

        enriched["OWNER_NODE_PATH"] = (
            owner_node_path
        )

        enriched["FIELD_RELATIVE_PATH"] = (
            field_relative_path
        )

        owned_mappings.append(enriched)

    return owned_mappings


# ============================================================
# D. TRANSFORMATION HELPER
# ============================================================

def apply_transform(
    value,
    mapping_type,
    transformation_logic
):
    """
    Minimal safe transformation contract.

    Current behavior:

      None value
          -> None

      Direct / no transform
          -> original source value

      TBD / unresolved transformation
          -> original source value

    Never fabricates placeholder target values.

    Approved transformations can be added here later.
    """

    if value is None:
        return None

    return value


# ============================================================
# E. NESTED PAYLOAD HELPER
# ============================================================

def set_nested_path(
    container,
    path_segments,
    value
):
    """
    Write a value into a nested OSCAL payload.

    Supports dictionary paths and basic [] array notation.

    Example:

        document-ids[].identifier

    becomes conceptually:

        {
            "document-ids": [
                {
                    "identifier": value
                }
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

        # ----------------------------
        # Array segment: something[]
        # ----------------------------
        if segment.endswith("[]"):

            key = segment[:-2]

            if key not in current:
                current[key] = []

            if not isinstance(current[key], list):
                current[key] = []

            # Array is final destination.
            if is_last:

                if isinstance(value, list):
                    current[key].extend(value)
                else:
                    current[key].append(value)

                return

            # Nested object inside array.
            if len(current[key]) == 0:
                current[key].append({})

            if not isinstance(
                current[key][0],
                dict
            ):
                current[key][0] = {}

            current = current[key][0]

        # ----------------------------
        # Normal object segment
        # ----------------------------
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
# F. PAYLOAD BUILDING HELPER
# ============================================================

def build_element_payload(
    source_record,
    mappings,
    source_json_field="CURATED_JSON"
):
    """
    Build one OSCAL node payload for one source record.

    Inputs:
        source_record
            Snowpark Row or dict containing CURATED_JSON

        mappings
            mappings returned by get_mappings_for_node()

    Uses:
        SOURCE_FIELD_NAME
            -> source lookup

        FIELD_RELATIVE_PATH
            -> target payload location

    Does NOT:
        generate hashes
        generate UUIDs
        create DIM rows
        create FACT rows
        know target table names
        know SSP-specific element names
    """

    payload = {}

    source_record_dict = _row_to_dict(
        source_record
    )

    json_data = source_record_dict.get(
        source_json_field
    )

    # Snowflake VARIANT can arrive as JSON text.
    if isinstance(json_data, str):

        try:
            source_obj = json.loads(
                json_data
            )

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

        source_field_name = mapping.get(
            "SOURCE_FIELD_NAME"
        )

        field_relative_path = mapping.get(
            "FIELD_RELATIVE_PATH"
        )

        mapping_type = mapping.get(
            "MAPPING_TYPE"
        )

        transformation_logic = mapping.get(
            "TRANSFORMATION_LOGIC"
        )

        # A node-level mapping without a relative
        # payload field is not written into payload.
        if not field_relative_path:
            continue

        if not source_field_name:
            continue

        # Resolve source value.
        source_value = resolve_json_path(
            source_obj,
            source_field_name
        )

        # Apply approved transformation behavior.
        resolved_value = apply_transform(
            source_value,
            mapping_type,
            transformation_logic
        )

        if resolved_value is None:
            continue

        path_segments = [
            segment
            for segment
            in field_relative_path.split(".")
            if segment
        ]

        if not path_segments:
            continue

        set_nested_path(
            payload,
            path_segments,
            resolved_value
        )

    return payload


# ============================================================
# CELL 4 COMPLETE
# ============================================================

print(
    "Cell 4 loaded - reusable functions ready"
)
