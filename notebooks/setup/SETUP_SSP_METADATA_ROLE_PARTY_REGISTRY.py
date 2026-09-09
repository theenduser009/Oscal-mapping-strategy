# %% Standalone Snowflake Python cell - governed SSP metadata registry setup

# With the flag below left False, this performs read-only preflight only. For
# the approved metadata release, set it to True before one controlled run: the
# same run preflights first, derives deterministic orders, inserts only missing
# target paths, and verifies the final state. It never updates a governed row.

import re

from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col, lit, trim, upper


EXECUTE_REGISTRY_WRITES = False

REGISTRY_TABLE = "RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY"
MODEL_KEY = "SSP"
SSP_ROOT_PATH = "system-security-plan"
METADATA_PATH = "system-security-plan.metadata"
ROLES_PATH = "system-security-plan.metadata.roles[]"
PARTIES_PATH = "system-security-plan.metadata.parties[]"
RESPONSIBLE_PARTIES_PATH = (
    "system-security-plan.metadata.responsible-parties[]"
)
TARGET_PATHS = (ROLES_PATH, PARTIES_PATH)
# These values use only conventions present in the live collection snapshot.
# Roles are one generated instance per approved source field. Parties are one
# reusable instance per UserList member value, independent of source field.
TARGET_INSTANCE_CONTRACTS = {
    ROLES_PATH: {
        "INSTANCE_KEY_RULE": "SOURCE_FIELD_NAME",
        "ITEM_PATH": "$",
    },
    PARTIES_PATH: {
        "INSTANCE_KEY_RULE": "ID",
        "ITEM_PATH": "UserList[]",
    },
}

REQUIRED_REGISTRY_COLUMNS = {
    "OSCAL_MODEL_KEY",
    "NODE_PATH",
    "PARENT_NODE_PATH",
    "ELEMENT_TYPE",
    "IS_COLLECTION",
    "INSTANCE_KEY_RULE",
    "PROCESS_ORDER",
    "IS_ACTIVE",
    "ITEM_PATH",
}

SUPPORTED_INSERT_COLUMNS = REQUIRED_REGISTRY_COLUMNS


session = get_active_session()


def _assert_safe_identifier(identifier):
    if not re.fullmatch(r"[A-Za-z0-9_.$]+", identifier):
        raise ValueError("Unsafe registry table identifier")


def _clean(value):
    return "" if value is None else str(value).strip()


def _is_active(value):
    return _clean(value).upper() not in {"FALSE", "F", "NO", "N", "0"}


def _is_true(value):
    return _clean(value).upper() in {"TRUE", "T", "YES", "Y", "1"}


def _element_type(node_path):
    return node_path.rsplit(".", 1)[-1].removesuffix("[]")


def _stored_process_order(value, node_path, required=False):
    text = _clean(value)
    if not text:
        if required:
            raise ValueError(
                f"Registry PROCESS_ORDER is missing for {node_path}"
            )
        return None
    if not re.fullmatch(r"-?[0-9]+", text):
        raise ValueError(
            f"Registry PROCESS_ORDER is not an integer for {node_path}"
        )
    return int(text)


def _assert_supported_not_null_columns():
    database_name, schema_name, table_name = REGISTRY_TABLE.split(".")
    column_rows = session.sql(
        f"""
SELECT COLUMN_NAME, IS_NULLABLE, COLUMN_DEFAULT, IS_IDENTITY
FROM {database_name}.INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '{schema_name}'
  AND TABLE_NAME = '{table_name}'
ORDER BY ORDINAL_POSITION
"""
    ).collect()
    if not column_rows:
        raise ValueError("Registry schema metadata could not be read")

    unsupported = []
    for row in column_rows:
        values = {
            str(key).upper(): value
            for key, value in row.as_dict(recursive=True).items()
        }
        column_name = _clean(values.get("COLUMN_NAME")).upper()
        is_required = _clean(values.get("IS_NULLABLE")).upper() == "NO"
        has_default = values.get("COLUMN_DEFAULT") is not None
        is_identity = _clean(values.get("IS_IDENTITY")).upper() == "YES"
        if (
            is_required
            and not has_default
            and not is_identity
            and column_name not in SUPPORTED_INSERT_COLUMNS
        ):
            unsupported.append(column_name)

    if unsupported:
        raise ValueError(
            "Registry has unsupported required insert columns: "
            + ", ".join(unsupported)
        )


def _read_model_rows():
    registry_df = session.table(REGISTRY_TABLE)
    columns = {str(name).strip().upper() for name in registry_df.columns}
    missing_columns = sorted(REQUIRED_REGISTRY_COLUMNS - columns)
    if missing_columns:
        raise ValueError(
            "Registry is missing required governed columns: "
            + ", ".join(missing_columns)
        )

    selected_df = (
        registry_df.select(
            col("OSCAL_MODEL_KEY"),
            col("NODE_PATH"),
            col("PARENT_NODE_PATH"),
            col("ELEMENT_TYPE"),
            col("IS_COLLECTION"),
            col("INSTANCE_KEY_RULE"),
            col("PROCESS_ORDER"),
            col("IS_ACTIVE"),
            col("ITEM_PATH"),
        )
        .filter(
            upper(trim(col("OSCAL_MODEL_KEY").cast("string")))
            == lit(MODEL_KEY)
        )
    )
    return [row.as_dict(recursive=True) for row in selected_df.collect()]


def _rows_by_path(model_rows):
    indexed = {}
    for row in model_rows:
        path = _clean(row.get("NODE_PATH"))
        if path:
            indexed.setdefault(path, []).append(row)
    return indexed


def _one_row(indexed_rows, path, required):
    rows = indexed_rows.get(path, [])
    if len(rows) > 1:
        raise ValueError(f"Registry has duplicate SSP rows for {path}")
    if not rows:
        if required:
            raise ValueError(f"Registry is missing required SSP path {path}")
        return None
    return rows[0]


def _assert_existing_row(row, path, expected_parent):
    if row is None:
        return
    if _clean(row.get("PARENT_NODE_PATH")) != expected_parent:
        raise ValueError(f"Existing SSP registry parent is invalid for {path}")
    expected_element_type = _element_type(path)
    if _clean(row.get("ELEMENT_TYPE")) != expected_element_type:
        raise ValueError(
            f"Existing SSP registry ELEMENT_TYPE is invalid for {path}"
        )
    if path.endswith("[]") and not _is_true(row.get("IS_COLLECTION")):
        raise ValueError(
            f"Existing SSP registry collection flag is invalid for {path}"
        )
    if not _is_active(row.get("IS_ACTIVE")):
        raise ValueError(f"Existing SSP registry row is inactive for {path}")
    _stored_process_order(row.get("PROCESS_ORDER"), path, required=True)


def _print_metadata_siblings(model_rows):
    siblings = [
        row
        for row in model_rows
        if _clean(row.get("NODE_PATH")) == METADATA_PATH
        or _clean(row.get("PARENT_NODE_PATH")) == METADATA_PATH
    ]

    def _sort_key(row):
        path = _clean(row.get("NODE_PATH"))
        process_order = _stored_process_order(
            row.get("PROCESS_ORDER"),
            path,
        )
        return (
            process_order if process_order is not None else 2**63 - 1,
            path,
        )

    siblings.sort(key=_sort_key)
    print("=== READ-ONLY SSP METADATA REGISTRY PREFLIGHT ===")
    for row in siblings:
        print(
            "path=",
            _clean(row.get("NODE_PATH")),
            " | parent=",
            _clean(row.get("PARENT_NODE_PATH")) or "<root>",
            " | element_type=",
            _clean(row.get("ELEMENT_TYPE")) or "<null>",
            " | collection=",
            _is_true(row.get("IS_COLLECTION")),
            " | instance_key_rule=",
            _clean(row.get("INSTANCE_KEY_RULE")) or "<null>",
            " | process_order=",
            _clean(row.get("PROCESS_ORDER")) or "<null>",
            " | active=",
            _is_active(row.get("IS_ACTIVE")),
            " | item_path=",
            _clean(row.get("ITEM_PATH")) or "<null>",
            sep="",
        )


def _build_preflight(model_rows):
    if not model_rows:
        raise ValueError("No SSP registry rows were found")

    indexed_rows = _rows_by_path(model_rows)
    root_row = _one_row(indexed_rows, SSP_ROOT_PATH, True)
    metadata_row = _one_row(indexed_rows, METADATA_PATH, True)
    responsible_row = _one_row(
        indexed_rows,
        RESPONSIBLE_PARTIES_PATH,
        True,
    )
    roles_row = _one_row(indexed_rows, ROLES_PATH, False)
    parties_row = _one_row(indexed_rows, PARTIES_PATH, False)

    _assert_existing_row(root_row, SSP_ROOT_PATH, "")
    _assert_existing_row(metadata_row, METADATA_PATH, SSP_ROOT_PATH)
    _assert_existing_row(
        responsible_row,
        RESPONSIBLE_PARTIES_PATH,
        METADATA_PATH,
    )
    _assert_existing_row(roles_row, ROLES_PATH, METADATA_PATH)
    _assert_existing_row(parties_row, PARTIES_PATH, METADATA_PATH)

    metadata_collection_order = _stored_process_order(
        responsible_row.get("PROCESS_ORDER"),
        RESPONSIBLE_PARTIES_PATH,
        required=True,
    )
    planned_rows = []
    expected_rows = {}
    for path, existing_row in (
        (ROLES_PATH, roles_row),
        (PARTIES_PATH, parties_row),
    ):
        instance_contract = TARGET_INSTANCE_CONTRACTS[path]
        expected_row = {
            "OSCAL_MODEL_KEY": MODEL_KEY,
            "NODE_PATH": path,
            "PARENT_NODE_PATH": METADATA_PATH,
            "ELEMENT_TYPE": _element_type(path),
            "IS_COLLECTION": True,
            "INSTANCE_KEY_RULE": instance_contract["INSTANCE_KEY_RULE"],
            "PROCESS_ORDER": metadata_collection_order,
            "IS_ACTIVE": True,
            "ITEM_PATH": instance_contract["ITEM_PATH"],
        }
        expected_rows[path] = expected_row
        if existing_row is not None:
            _assert_target_row(existing_row, expected_row)
            continue
        planned_rows.append(expected_row)

    return {
        "planned_rows": planned_rows,
        "expected_rows": expected_rows,
    }


def _insert_missing_rows(planned_rows):
    if not planned_rows:
        return []

    source_view = "TMP_SSP_METADATA_REGISTRY_SETUP"
    session.create_dataframe(planned_rows).create_or_replace_temp_view(
        source_view
    )
    merge_sql = f"""
MERGE INTO {REGISTRY_TABLE} AS target
USING {source_view} AS source
    ON UPPER(TRIM(target.OSCAL_MODEL_KEY::STRING)) = source.OSCAL_MODEL_KEY
   AND TRIM(target.NODE_PATH::STRING) = source.NODE_PATH
WHEN NOT MATCHED THEN INSERT (
    OSCAL_MODEL_KEY,
    NODE_PATH,
    PARENT_NODE_PATH,
    ELEMENT_TYPE,
    IS_COLLECTION,
    INSTANCE_KEY_RULE,
    PROCESS_ORDER,
    IS_ACTIVE,
    ITEM_PATH
) VALUES (
    source.OSCAL_MODEL_KEY,
    source.NODE_PATH,
    source.PARENT_NODE_PATH,
    source.ELEMENT_TYPE,
    source.IS_COLLECTION,
    source.INSTANCE_KEY_RULE,
    source.PROCESS_ORDER,
    source.IS_ACTIVE,
    source.ITEM_PATH
)
"""
    return session.sql(merge_sql).collect()


def _assert_target_row(row, expected_row):
    path = expected_row["NODE_PATH"]
    _assert_existing_row(row, path, expected_row["PARENT_NODE_PATH"])
    for column_name in ("INSTANCE_KEY_RULE", "ITEM_PATH"):
        if _clean(row.get(column_name)) != expected_row[column_name]:
            raise ValueError(
                f"Registry verification failed for {path} {column_name}"
            )
    actual_order = _stored_process_order(
        row.get("PROCESS_ORDER"),
        path,
        required=True,
    )
    if actual_order != expected_row["PROCESS_ORDER"]:
        raise ValueError(f"Registry verification failed for {path} order")


def _verify_targets(expected_rows):
    model_rows = _read_model_rows()
    indexed_rows = _rows_by_path(model_rows)
    for path in TARGET_PATHS:
        row = _one_row(indexed_rows, path, True)
        _assert_target_row(row, expected_rows[path])
    print("REGISTRY VERIFICATION PASSED")


_assert_safe_identifier(REGISTRY_TABLE)
_assert_supported_not_null_columns()
current_model_rows = _read_model_rows()
_print_metadata_siblings(current_model_rows)
preflight = _build_preflight(current_model_rows)

if preflight["planned_rows"]:
    print("=== DETERMINISTIC INSERT PLAN ===")
    for planned_row in preflight["planned_rows"]:
        print(
            "insert_path=",
            planned_row["NODE_PATH"],
            " | parent=",
            planned_row["PARENT_NODE_PATH"],
            " | element_type=",
            planned_row["ELEMENT_TYPE"],
            " | collection=True",
            " | instance_key_rule=",
            planned_row["INSTANCE_KEY_RULE"],
            " | process_order=",
            planned_row["PROCESS_ORDER"],
            " | active=True",
            " | item_path=",
            planned_row["ITEM_PATH"],
            sep="",
        )
else:
    print("Both governed target paths already exist; no insert is needed")

if not EXECUTE_REGISTRY_WRITES:
    print("EXECUTE_REGISTRY_WRITES = False; no registry changes were made")
    print("READ-ONLY REGISTRY PREFLIGHT PASSED")
else:
    merge_result = _insert_missing_rows(preflight["planned_rows"])
    print("Registry insert-only MERGE completed:", merge_result)
    _verify_targets(preflight["expected_rows"])
