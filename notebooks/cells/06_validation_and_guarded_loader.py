# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification
# Daily SSP DEV upsert. Missing/obsolete in-scope rows block; no destructive policy.
# Keep other target writers paused for the complete preflight/transaction/readback.
import json
import re
import uuid

SSP_LOAD_RELEASE = "ssp-daily-upsert-v1"
SSP_LOAD_DIM = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT"
SSP_LOAD_FACT = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY"
SSP_LOAD_DIM_PK = "PK_OSCAL_SSP_ELEMENT_HASH"
SSP_LOAD_FACT_PK = "PK_FACT_OSCAL_DEPENDENCY_HASH"
SSP_LOAD_SOURCE = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
_LOAD_AUDIT_COLUMNS = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}


class LoadError(RuntimeError):
    def __init__(self, code, details=None):
        self.code = code
        self.details = details or {}
        super().__init__(code)

_LOAD_DIM_SOURCES = {
    SSP_LOAD_DIM_PK: "NODE_KEY", "ELEMENT_TYPE": "ELEMENT_TYPE",
    "OSCAL_UUID": "OSCAL_UUID", "METADATA_JSON": "METADATA_JSON",
    "SOURCE_SYSTEM_NAME": "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME": "SOURCE_TABLE_NAME",
    "SOURCE_RECORD_ID": "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID": "DW_PIPELINE_RUN_ID",
    "DW_LOAD_TIMESTAMP": "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ": "DW_LOAD_TIMESTAMP_TZ",
}
_LOAD_FACT_SOURCES = {
    SSP_LOAD_FACT_PK: "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH": "FK_SOURCE_ELEMENT_HASH",
    "FK_TARGET_ELEMENT_HASH": "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE": "DEPENDENCY_TYPE",
    "SOURCE_OSCAL_UUID": "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID": "TARGET_OSCAL_UUID",
}
_LOAD_HASH_SOURCES = {"NODE_KEY", "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"}
_LOAD_UUID_SOURCES = {"OSCAL_UUID", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID"}
_LOAD_HEX_PATTERN = r"[0-9a-fA-F]{32}"
_LOAD_UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _load_query(session, statement):
    return session.sql(statement).collect()


def _load_error_details(error):
    # Preserve actionable categories without echoing Snowflake/source messages.
    details = {"CAUSE": error.code if isinstance(error, LoadError) else
               ("CANCELLED" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "SQL_OR_CLIENT_ERROR")}
    if isinstance(error, LoadError):
        details.update(error.details)
    for attr, label, pattern in (("sql_error_code", "SQL_ERROR_CODE", r"[0-9]{1,10}"),
                                 ("sqlstate", "SQLSTATE", r"[A-Z0-9]{5}"),
                                 ("sfqid", "QUERY_ID", r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")):
        value = str(getattr(error, attr, ""))
        if re.fullmatch(pattern, value):
            details[label] = value
    return details


def _load_no_transaction(session):
    try:
        transaction = _load_query(session, "SELECT CURRENT_TRANSACTION() AS TX")[0]["TX"]
    except BaseException:
        raise LoadError("TRANSACTION_STATE_UNAVAILABLE") from None
    if transaction is not None:
        raise LoadError("EXISTING_TRANSACTION")


def _load_ident(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
        raise LoadError("UNSUPPORTED_COLUMN_IDENTIFIER")
    return '"' + value + '"'


def _load_table(name):
    parts = name.split(".") if isinstance(name, str) else []
    if len(parts) not in (1, 3):
        raise LoadError("UNSUPPORTED_TABLE_IDENTIFIER")
    return ".".join(_load_ident(part.upper()) for part in parts)


def _load_safe_type(value):
    if not isinstance(value, str):
        raise LoadError("MISSING_LIVE_COLUMN_DATATYPE")
    value = value.strip().upper()
    match = re.fullmatch(r"(?:VARCHAR|STRING|TEXT)(?:\(\s*([1-9][0-9]*)\s*\))?", value)
    if match:
        return "VARCHAR" + ("(" + str(int(match[1])) + ")" if match[1] else "")
    if re.fullmatch(r"BINARY\(\s*16\s*\)", value):
        return "BINARY(16)"
    if value == "VARIANT" or re.fullmatch(r"TIMESTAMP_(?:NTZ|LTZ|TZ)(?:\([0-9]\))?", value):
        return value
    raise LoadError("UNSUPPORTED_LIVE_COLUMN_DATATYPE")


def _load_column_plan(description, kind):
    mappings = {"DIM": _LOAD_DIM_SOURCES, "FACT": _LOAD_FACT_SOURCES}
    if kind not in mappings:
        raise LoadError("INVALID_PROJECTION_KIND")
    sources = mappings[kind]
    seen, plan = set(), []
    for row in description:
        raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
        entry = {str(k).lower(): v for k, v in raw.items()}
        if not {"name", "type", "kind", "null?", "default"}.issubset(entry):
            raise LoadError("INCOMPLETE_DESC_TABLE_METADATA")
        name = entry["name"]
        _load_ident(name)  # Quoted lower-case/case-colliding targets are not guessed.
        if name in seen:
            raise LoadError("DUPLICATE_LIVE_COLUMN_NAMES")
        seen.add(name)
        nullable = str(entry["null?"]).strip().upper()
        column_kind = str(entry["kind"]).strip().upper()
        if nullable not in {"Y", "N"} or column_kind not in {"COLUMN", "VIRTUAL", "VIRTUAL_COLUMN"}:
            raise LoadError("UNSUPPORTED_LIVE_COLUMN_METADATA")
        if name not in sources:
            if column_kind == "COLUMN" and nullable == "N" and entry["default"] is None:
                raise LoadError("UNMAPPED_REQUIRED_INSERT_COLUMN_" + name)
            continue
        if column_kind != "COLUMN" or entry.get("expression") not in (None, ""):
            raise LoadError("MAPPED_COLUMN_NOT_WRITABLE_" + name)
        try:
            dtype = _load_safe_type(entry["type"])
        except LoadError as error:
            # Only column metadata, never source values or full SQL, is reported.
            raise LoadError(error.code, {"TABLE_KIND": kind, "COLUMN": name,
                             "LIVE_TYPE": str(entry["type"])[:128]}) from None
        source, encoding = sources[name], None
        expression = "s." + _load_ident(source)
        if source in _LOAD_HASH_SOURCES and dtype == "BINARY(16)":
            # Decode the existing MD5 hex identity; never hash again or truncate.
            expression = "TO_BINARY(" + expression + ", 'HEX')"
            encoding = "HEX_TO_BINARY16"
        elif source in _LOAD_UUID_SOURCES and dtype == "VARCHAR(32)":
            # Storage only. Canonical UUIDs inside the graph and JSON stay unchanged.
            expression = "REPLACE(" + expression + ", '-', '')"
            encoding = "UUID_TO_COMPACT32"
        elif name == "METADATA_JSON":
            if dtype == "VARIANT":
                expression = "PARSE_JSON(" + expression + ")"
            elif dtype.startswith("VARCHAR"):
                expression = "CAST(" + expression + " AS VARCHAR)"
            else:
                raise LoadError("UNSUPPORTED_PAYLOAD_DATATYPE")
        elif name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}:
            if not dtype.startswith("TIMESTAMP_"):
                raise LoadError("EXPLICIT_AUDIT_TIMESTAMP_TYPE_REQUIRED")
            expression = "CAST(" + expression + " AS " + dtype + ")"
        else:
            if not dtype.startswith("VARCHAR"):
                raise LoadError("IDENTIFIERS_AND_LABELS_REQUIRE_STRING_TYPE")
            expression = "CAST(" + expression + " AS VARCHAR)"
        plan.append({"name": name, "source": source, "expression": expression,
                     "type": dtype, "nullable": nullable == "Y", "encoding": encoding})
    required = set(sources)
    if kind == "DIM":
        # The existing loader projects these audit columns only when exposed.
        # Do not invent a requirement that an optional target column must exist.
        required -= {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}
    if required - seen:
        raise LoadError("MISSING_TARGET_COLUMNS_" + "_".join(sorted(required - seen)))
    return plan


def _load_count(session, sql):
    return int(_load_query(session, sql)[0]["N"])


def _load_zero(session, sql, code):
    if _load_count(session, sql):
        raise LoadError(code)


def _load_unique(session, table, key):
    _load_zero(session, f"SELECT COUNT(*) AS N FROM (SELECT {key} FROM {table} "
                f"GROUP BY {key} HAVING {key} IS NULL OR COUNT(*) > 1)",
                "NULL_OR_DUPLICATE_KEYS")


def _load_selection_schema(plans):
    """Selection compares identities using the posted physical BINARY(16) schema."""
    required = ((SSP_LOAD_DIM_PK,),
                (SSP_LOAD_FACT_PK, "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"))
    for plan, keys in zip(plans, required):
        types = {c["name"]: c["type"] for c in plan}
        if any(types.get(key) != "BINARY(16)" for key in keys):
            raise LoadError("CONFIRMED_BINARY16_SCHEMA_REQUIRED")


def _load_stage(session, raw_stage, stage, plan):
    # Validate identity syntax before evaluating conversions; NULL is not an identity.
    for column in plan:
        encoding = column.get("encoding")
        if encoding:
            source = _load_ident(column["source"])
            pattern = _LOAD_HEX_PATTERN if encoding == "HEX_TO_BINARY16" else _LOAD_UUID_PATTERN
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {raw_stage} WHERE "
                        f"{source} IS NULL OR NOT REGEXP_LIKE({source}, '{pattern}')",
                        "INVALID_STORAGE_IDENTITY_" + column["name"])
    expressions = ", ".join(c["expression"] + " AS " + _load_ident(c["name"]) for c in plan)
    _load_query(session, f"CREATE TEMPORARY TABLE {stage} AS SELECT {expressions} FROM {raw_stage} s")
    for column in plan:
        name = _load_ident(column["name"])
        if column["type"] == "BINARY(16)":
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE "
                        f"{name} IS NULL OR OCTET_LENGTH({name}) <> 16", "BINARY_KEY_WIDTH_INVALID")
        if column["name"] in {SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK}:
            # Different text casing can collapse to the same physical binary key.
            _load_unique(session, stage, name)
        if not column["nullable"]:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE {name} IS NULL",
                        "REQUIRED_TARGET_VALUE_IS_NULL")
        width = re.fullmatch(r"VARCHAR\((\d+)\)", column["type"])
        if width:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE LENGTH({name}) > {int(width[1])}",
                        "TARGET_STRING_CAPACITY_EXCEEDED")


def _load_baseline_equal(session, names, queries):
    # Multiset comparison: keep duplicate multiplicities in the OLD full tables.
    # GROUP BY ALL includes every existing target column, including VARIANT payloads.
    for baseline, query in zip((names["DB"], names["FB"]), queries):
        current = f"SELECT *, COUNT(*) AS SSP_LOAD_ROW_MULTIPLICITY FROM ({query}) GROUP BY ALL"
        frozen = f"SELECT *, COUNT(*) AS SSP_LOAD_ROW_MULTIPLICITY FROM {baseline} GROUP BY ALL"
        _load_zero(session, f"SELECT COUNT(*) AS N FROM (({current}) MINUS ({frozen}))",
                    "TARGET_BASELINE_CHANGED")
        _load_zero(session, f"SELECT COUNT(*) AS N FROM (({frozen}) MINUS ({current}))",
                    "TARGET_BASELINE_CHANGED")
        if _load_count(session, f"SELECT COUNT(*) AS N FROM ({query})") != _load_count(
                session, f"SELECT COUNT(*) AS N FROM {baseline}"):
            raise LoadError("TARGET_BASELINE_CHANGED")


def _load_integrity_sql(queries, ids, allow_absent=False):
    if type(allow_absent) is not bool:
        raise LoadError("INVALID_OLD_GRAPH_POLICY")
    dim, fact = queries
    dk, fk = SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK
    relationship = "('parent_of','CONTAINS')" if allow_absent else "('CONTAINS')"
    empty = "c.NODES=0 AND COALESCE(e.EDGES,0)=0" if allow_absent else "FALSE"
    return f"""WITH checked_nodes AS ({dim}), checked_edges AS ({fact}),
record_counts AS (
 SELECT i.SOURCE_RECORD_ID, COUNT(d.{dk}) AS NODES,
        SUM(CASE WHEN d.ELEMENT_TYPE='system-security-plan' THEN 1 ELSE 0 END) AS ROOTS
 FROM {ids} i LEFT JOIN checked_nodes d ON d.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
 GROUP BY i.SOURCE_RECORD_ID),
edge_counts AS (
 SELECT d.SOURCE_RECORD_ID, COUNT(f.{fk}) AS EDGES
 FROM checked_edges f JOIN checked_nodes d ON d.{dk}=f.FK_SOURCE_ELEMENT_HASH
 GROUP BY d.SOURCE_RECORD_ID)
SELECT
 (SELECT COUNT(*) FROM {ids}) AS SELECTED_RECORDS,
 (SELECT COUNT(*) FROM checked_nodes) AS NODES,
 (SELECT COUNT(*) FROM checked_edges) AS EDGES,
 (SELECT COUNT(*) FROM checked_nodes WHERE {dk} IS NULL) AS DIM_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {dk} FROM checked_nodes GROUP BY {dk} HAVING COUNT(*)>1)) AS DIM_DUPLICATE_KEYS,
 (SELECT COUNT(*) FROM checked_edges WHERE {fk} IS NULL) AS FACT_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {fk} FROM checked_edges GROUP BY {fk} HAVING COUNT(*)>1)) AS FACT_DUPLICATE_KEYS,
 (SELECT COUNT(*) FROM checked_nodes d LEFT JOIN {ids} i ON i.SOURCE_RECORD_ID=d.SOURCE_RECORD_ID
     WHERE d.OSCAL_UUID IS NULL OR
     NOT EQUAL_NULL(d.SOURCE_SYSTEM_NAME,'ARCHER') OR
     NOT EQUAL_NULL(d.SOURCE_TABLE_NAME,'{SSP_LOAD_SOURCE}') OR
     i.SOURCE_RECORD_ID IS NULL) AS INVALID_NODE_OWNERSHIP_OR_UUID,
 (SELECT COUNT(*) FROM checked_edges WHERE FK_SOURCE_ELEMENT_HASH IS NULL OR FK_TARGET_ELEMENT_HASH IS NULL) AS NULL_FOREIGN_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS
     (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_SOURCE_ELEMENT_HASH)) AS DANGLING_SOURCE_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS
     (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_TARGET_ELEMENT_HASH)) AS DANGLING_TARGET_KEYS,
 (SELECT COUNT(*) FROM checked_edges f JOIN checked_nodes s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
     JOIN checked_nodes t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
     WHERE NOT EQUAL_NULL(s.SOURCE_RECORD_ID,t.SOURCE_RECORD_ID)) AS CROSS_RECORD_EDGES,
 (SELECT COUNT(*) FROM checked_edges f JOIN checked_nodes s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
     JOIN checked_nodes t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
     WHERE NOT EQUAL_NULL(f.SOURCE_OSCAL_UUID,s.OSCAL_UUID)
        OR NOT EQUAL_NULL(f.TARGET_OSCAL_UUID,t.OSCAL_UUID)) AS UUID_LINK_MISMATCHES,
 (SELECT COUNT(*) FROM checked_edges WHERE DEPENDENCY_TYPE IS NULL
     OR DEPENDENCY_TYPE NOT IN {relationship}) AS WRONG_RELATIONSHIP_TYPE,
 (SELECT COUNT(*) FROM (SELECT d.{dk},d.ELEMENT_TYPE,COUNT(f.{fk}) AS PARENTS
     FROM checked_nodes d LEFT JOIN checked_edges f ON f.FK_TARGET_ELEMENT_HASH=d.{dk}
     GROUP BY d.{dk},d.ELEMENT_TYPE
     HAVING COUNT(f.{fk}) <> CASE WHEN d.ELEMENT_TYPE='system-security-plan' THEN 0 ELSE 1 END)) AS WRONG_PARENT_COUNTS,
 (SELECT COUNT(*) FROM record_counts c LEFT JOIN edge_counts e ON e.SOURCE_RECORD_ID=c.SOURCE_RECORD_ID
     WHERE NOT ({empty}) AND
     (c.NODES<1 OR c.ROOTS<>1 OR COALESCE(e.EDGES,0)<>c.NODES-1)) AS INVALID_RECORD_SHAPES"""


def _load_integrity(session, queries, ids, expected_records, allow_absent=False):
    row = _load_query(session, _load_integrity_sql(queries, ids, allow_absent))[0]
    report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
    metrics = ("SELECTED_RECORDS", "NODES", "EDGES")
    if report.get("SELECTED_RECORDS") != expected_records or any(v != 0 for k, v in report.items() if k not in metrics):
        raise LoadError("BATCH_PRIMARY_FOREIGN_KEY_OR_HIERARCHY_FAILED", {"KEY_CHECKS": report})
    # Cardinality is checked first; disconnected cycles must still fail reachability.
    dim, fact = queries
    dk = SSP_LOAD_DIM_PK
    bound = max(int(report["NODES"]), 1)
    sql = f"""WITH RECURSIVE checked_nodes AS ({dim}), checked_edges AS ({fact}),
tree(K,SOURCE_RECORD_ID,DEPTH) AS (
 SELECT {dk},SOURCE_RECORD_ID,0 FROM checked_nodes WHERE ELEMENT_TYPE='system-security-plan'
 UNION ALL
 SELECT f.FK_TARGET_ELEMENT_HASH,t.SOURCE_RECORD_ID,t.DEPTH+1
 FROM tree t JOIN checked_edges f ON f.FK_SOURCE_ELEMENT_HASH=t.K
 JOIN checked_nodes d ON d.{dk}=f.FK_TARGET_ELEMENT_HASH AND d.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
 WHERE t.DEPTH<{bound}),
node_counts AS (SELECT SOURCE_RECORD_ID,COUNT(*) AS N FROM checked_nodes GROUP BY SOURCE_RECORD_ID),
reachable AS (SELECT SOURCE_RECORD_ID,COUNT(DISTINCT K) AS N FROM tree GROUP BY SOURCE_RECORD_ID)
SELECT COUNT(*) AS N FROM {ids} i
LEFT JOIN node_counts d ON d.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
LEFT JOIN reachable r ON r.SOURCE_RECORD_ID=i.SOURCE_RECORD_ID
WHERE COALESCE(d.N,0)<>COALESCE(r.N,0)"""
    _load_zero(session, sql, "BATCH_DISCONNECTED_RECORD_TREE")
    report["DISCONNECTED_RECORDS"] = 0
    return report


def _assert_safe_identifier(identifier):
    _load_table(identifier)


def _duplicate_count(dataframe, key_column):
    return dataframe.group_by(col(key_column)).count().filter(col("COUNT") > lit(1)).count()


def _load_columns(columns):
    names = [c["name"] if isinstance(c, dict) else c for c in columns]
    for name in names:
        _load_ident(name)
    if not names or len(names) != len(set(names)):
        raise LoadError("INVALID_PROJECTION_COLUMNS")
    return names


def _load_business_columns(columns):
    return [name for name in _load_columns(columns) if name not in _LOAD_AUDIT_COLUMNS]


def _load_difference_predicate(columns, left="t", right="s"):
    if left not in ("t", "s", "b") or right not in ("t", "s", "b"):
        raise LoadError("INVALID_COMPARISON_ALIAS")
    terms = []
    for name in _load_business_columns(columns):
        if name in (SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK):
            continue
        lhs, rhs = left + "." + _load_ident(name), right + "." + _load_ident(name)
        if name == "METADATA_JSON":
            # Structural object comparison, not JSON key ordering.
            lhs = "TRY_PARSE_JSON(TO_VARCHAR(" + lhs + "))"
            rhs = "TRY_PARSE_JSON(TO_VARCHAR(" + rhs + "))"
        terms.append("(" + lhs + " IS DISTINCT FROM " + rhs + ")")
    if not terms:
        raise LoadError("BUSINESS_COLUMNS_REQUIRED")
    return " OR ".join(terms)


def _build_merge_sql(target_table, source_view, pk_column, columns):
    expected_pk = {SSP_LOAD_DIM: SSP_LOAD_DIM_PK, SSP_LOAD_FACT: SSP_LOAD_FACT_PK}
    if expected_pk.get(target_table) != pk_column:
        raise LoadError("TARGET_OUTSIDE_APPROVED_SSP_DEV")
    names = _load_columns(columns)
    if pk_column not in names:
        raise LoadError("MISSING_PROJECTED_PRIMARY_KEY")
    _load_table(source_view)
    changed = _load_difference_predicate(columns)
    updates = ", ".join("t." + _load_ident(n) + " = s." + _load_ident(n)
                        for n in names if n != pk_column)
    return (
        f"MERGE INTO {target_table} t USING {source_view} s "
        f"ON t.{_load_ident(pk_column)} = s.{_load_ident(pk_column)} "
        f"WHEN MATCHED AND ({changed}) THEN UPDATE SET {updates} "
        f"WHEN NOT MATCHED THEN INSERT ({', '.join(_load_ident(n) for n in names)}) "
        f"VALUES ({', '.join('s.' + _load_ident(n) for n in names)})"
    )


def _load_expected_changes_sql(target, stage, pk, columns):
    target_sql, stage_sql, key = _load_table(target), _load_table(stage), _load_ident(pk)
    changed = _load_difference_predicate(columns)
    return f"""SELECT
 (SELECT COUNT(*) FROM {stage_sql} s WHERE NOT EXISTS
     (SELECT 1 FROM {target_sql} t WHERE t.{key}=s.{key})) AS INSERTS,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE {changed}) AS UPDATES,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE NOT ({changed})) AS UNCHANGED"""


def _load_contract(config):
    expected = {"OSCAL_MODEL": "SSP", "TARGET_DIM": SSP_LOAD_DIM,
                "TARGET_FACT": SSP_LOAD_FACT, "DIM_PK_COLUMN": SSP_LOAD_DIM_PK,
                "FACT_PK_COLUMN": SSP_LOAD_FACT_PK, "SOURCE_SYSTEM_NAME": "ARCHER",
                "SOURCE_TABLE_NAME": SSP_LOAD_SOURCE,
                "RAW_TABLE": "RTX_RAW_DEV.ES_ESC_GRC." + SSP_LOAD_SOURCE,
                "IDENTITY_VERSION": "v1_registry_path_instance"}
    if any(config.get(k) != v for k, v in expected.items()):
        raise LoadError("UNSUPPORTED_MODEL_OR_SSP_DEV_CONTRACT")
    if type(config.get("EXECUTE_WRITES")) is not bool:
        raise LoadError("EXPLICIT_BOOLEAN_WRITE_MODE_REQUIRED")
    if config.get("OBSOLETE_ROW_POLICY", "BLOCK") != "BLOCK":
        raise LoadError("ONLY_BLOCK_OBSOLETE_POLICY_IS_APPROVED")


def _load_row(row):
    raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
    return {str(k).upper(): v for k, v in raw.items()}


def _load_scope_queries(names):
    # Include ownership AND key matches: foreign-owned identities cannot hide.
    dim = f"""SELECT t.* FROM {SSP_LOAD_DIM} t
 LEFT JOIN {names['D']} s ON s.{SSP_LOAD_DIM_PK}=t.{SSP_LOAD_DIM_PK}
 LEFT JOIN {names['IDS']} i ON i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
     AND t.SOURCE_SYSTEM_NAME='ARCHER' AND t.SOURCE_TABLE_NAME='{SSP_LOAD_SOURCE}'
 WHERE s.{SSP_LOAD_DIM_PK} IS NOT NULL OR i.SOURCE_RECORD_ID IS NOT NULL"""
    keys = f"SELECT {SSP_LOAD_DIM_PK} FROM ({dim}) UNION SELECT {SSP_LOAD_DIM_PK} FROM {names['D']}"
    fact = f"""SELECT t.* FROM {SSP_LOAD_FACT} t
 LEFT JOIN {names['F']} f ON f.{SSP_LOAD_FACT_PK}=t.{SSP_LOAD_FACT_PK}
 LEFT JOIN ({keys}) s ON s.{SSP_LOAD_DIM_PK}=t.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({keys}) d ON d.{SSP_LOAD_DIM_PK}=t.FK_TARGET_ELEMENT_HASH
 WHERE f.{SSP_LOAD_FACT_PK} IS NOT NULL OR s.{SSP_LOAD_DIM_PK} IS NOT NULL
     OR d.{SSP_LOAD_DIM_PK} IS NOT NULL"""
    return dim, fact


def _load_storage_values(session, query, plan):
    for column in plan:
        name, dtype = _load_ident(column["name"]), column["type"]
        where = []
        if not column["nullable"]:
            where.append(name + " IS NULL")
        if dtype == "BINARY(16)":
            where.append(name + " IS NULL OR OCTET_LENGTH(" + name + ")<>16")
        if column["source"] in _LOAD_UUID_SOURCES:
            pattern = r"[0-9a-f]{32}" if dtype == "VARCHAR(32)" else _LOAD_UUID_PATTERN
            where.append(name + " IS NULL OR NOT REGEXP_LIKE(" + name + ", '" + pattern + "')")
        width = re.fullmatch(r"VARCHAR\((\d+)\)", dtype)
        if width:
            where.append("LENGTH(" + name + ")>" + width[1])
        if column["name"] == "METADATA_JSON":
            where.append("NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(TO_VARCHAR(" + name + "))),FALSE)")
        if where:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) WHERE " + " OR ".join(where),
                       "INVALID_STORED_OR_STAGED_COLUMN_" + column["name"])


def _load_scope_check(session, names, plans):
    queries = _load_scope_queries(names)
    for target, pk in ((SSP_LOAD_DIM, SSP_LOAD_DIM_PK), (SSP_LOAD_FACT, SSP_LOAD_FACT_PK)):
        _load_unique(session, target, pk)
    extra = {}
    for kind, pk, query, plan in zip(("D", "F"), (SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK), queries, plans):
        extra[kind] = _load_count(session, f"SELECT COUNT(*) AS N FROM ({query}) t "
                                  f"WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})")
        ownership = ("SOURCE_RECORD_ID", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "ELEMENT_TYPE", "OSCAL_UUID") if kind == "D" else (
            "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID")
        conflict = " OR ".join(f"t.{_load_ident(c)} IS DISTINCT FROM s.{_load_ident(c)}" for c in ownership)
        _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) t JOIN {names[kind]} s "
                           f"ON t.{pk}=s.{pk} WHERE {conflict}", "TARGET_IDENTITY_PROVENANCE_CONFLICT")
        _load_storage_values(session, query, plan)
    report = {"OBSOLETE_DIM_ROWS": extra["D"], "OBSOLETE_FACT_ROWS": extra["F"]}
    if any(extra.values()):
        raise LoadError("OBSOLETE_TARGET_ROWS_BLOCKED", report)
    dim, fact = queries
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM ({fact}) f
 LEFT JOIN ({dim}) s ON s.{SSP_LOAD_DIM_PK}=f.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({dim}) t ON t.{SSP_LOAD_DIM_PK}=f.FK_TARGET_ELEMENT_HASH
 WHERE s.{SSP_LOAD_DIM_PK} IS NULL OR t.{SSP_LOAD_DIM_PK} IS NULL""",
               "CROSS_SCOPE_LINKS_BLOCKED")
    report["ABSENT_INPUT_SOURCE_RECORDS_PRESERVED"] = _load_count(session, f"""
 SELECT COUNT(*) AS N FROM (SELECT DISTINCT t.SOURCE_RECORD_ID FROM {SSP_LOAD_DIM} t
 WHERE t.SOURCE_SYSTEM_NAME='ARCHER' AND t.SOURCE_TABLE_NAME='{SSP_LOAD_SOURCE}'
 AND NOT EXISTS (SELECT 1 FROM {names['IDS']} i WHERE i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID))""")
    return report


def _load_freeze(session, nodes, edges, names):
    required_nodes = set(_LOAD_DIM_SOURCES.values()) - _LOAD_AUDIT_COLUMNS
    required_nodes |= {"ELEMENT_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY"}
    required_edges = set(_LOAD_FACT_SOURCES.values())
    if required_nodes - set(nodes.columns) or required_edges - set(edges.columns):
        raise LoadError("MISSING_CANONICAL_GRAPH_COLUMNS")
    for frame, key in ((nodes, "NV"), (edges, "EV")):
        frame.write.save_as_table(names[key], mode="errorifexists", table_type="temporary")
    nv, ev = names["NV"], names["EV"]
    _load_unique(session, nv, "NODE_KEY")
    _load_unique(session, ev, "EDGE_KEY")
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM {nv} WHERE
 SOURCE_RECORD_ID IS NULL OR LENGTH(TRIM(SOURCE_RECORD_ID))=0
 OR INSTANCE_KEY IS NULL OR LENGTH(TRIM(INSTANCE_KEY))=0
 OR ELEMENT_PATH IS NULL OR (ELEMENT_PATH<>'system-security-plan'
     AND ELEMENT_PATH NOT LIKE 'system-security-plan.%')
 OR ELEMENT_TYPE IS DISTINCT FROM REPLACE(SPLIT_PART(ELEMENT_PATH,'.',-1),'[]','')
 OR NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(METADATA_JSON)),FALSE)""", "INVALID_SSP_PATH_IDENTITY_OR_PAYLOAD")
    roots = f"SELECT SOURCE_RECORD_ID FROM {nv} WHERE ELEMENT_PATH='system-security-plan'"
    _load_unique(session, f"({roots})", "SOURCE_RECORD_ID")
    _load_query(session, f"CREATE TEMPORARY TABLE {names['IDS']} AS {roots}")
    selected = _load_count(session, f"SELECT COUNT(*) AS N FROM {names['IDS']}")
    if selected == 0:
        raise LoadError("EMPTY_INPUT_NOT_AUTHORIZED")
    # Explicit collection context is preserved; singleton parent may leave it NULL.
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM {ev} e
 JOIN {nv} p ON LOWER(p.NODE_KEY)=LOWER(e.FK_SOURCE_ELEMENT_HASH)
 JOIN {nv} c ON LOWER(c.NODE_KEY)=LOWER(e.FK_TARGET_ELEMENT_HASH)
 WHERE NOT STARTSWITH(c.ELEMENT_PATH, p.ELEMENT_PATH||'.')
 OR (c.PARENT_INSTANCE_KEY IS NOT NULL AND
     c.PARENT_INSTANCE_KEY IS DISTINCT FROM p.INSTANCE_KEY)""", "CANONICAL_PARENT_CONTEXT_MISMATCH")
    return selected


def _load_prepare(session, nodes, edges, config):
    _load_contract(config)
    _load_no_transaction(session)
    prefix = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.TMP_SSP_DAILY_" + uuid.uuid4().hex.upper()
    names = {k: prefix + "_" + k for k in ("NV", "EV", "IDS", "D", "F", "DB", "FB")}
    plans = [_load_column_plan(_load_query(session, "DESC TABLE " + target), kind)
             for target, kind in ((SSP_LOAD_DIM, "DIM"), (SSP_LOAD_FACT, "FACT"))]
    _load_selection_schema(plans)
    records = _load_freeze(session, nodes, edges, names)
    expected_records = config.get("EXPECTED_SOURCE_RECORDS")
    if expected_records is not None and (
            type(expected_records) is not int or expected_records <= 0 or records != expected_records):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH",
                        {"EXPECTED_SOURCE_RECORDS": expected_records, "GRAPH_SOURCE_RECORDS": records})
    for raw, physical, plan in zip(("NV", "EV"), ("D", "F"), plans):
        _load_stage(session, names[raw], names[physical], plan)
    candidates = (f"SELECT * FROM {names['D']}", f"SELECT * FROM {names['F']}")
    candidate = _load_integrity(session, candidates, names["IDS"], records)
    for query, plan in zip(candidates, plans):
        _load_storage_values(session, query, plan)
    for target, key in ((SSP_LOAD_DIM, "DB"), (SSP_LOAD_FACT, "FB")):
        _load_query(session, f"CREATE TEMPORARY TABLE {names[key]} AS SELECT * FROM {target}")
    context = {"names": names, "plans": plans, "records": records, "candidate": candidate}
    context["scope"] = _load_scope_check(session, names, plans)
    _load_integrity(session, _load_scope_queries(names), names["IDS"], records, allow_absent=True)
    context["changes"] = [
        _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        for target, kind, pk, plan in zip((SSP_LOAD_DIM, SSP_LOAD_FACT), ("D", "F"),
                                         (SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK), plans)]
    return context

def _load_unchanged_scope(session, names):
    for target, baseline, kind, pk in (
        (SSP_LOAD_DIM, names["DB"], "D", SSP_LOAD_DIM_PK),
        (SSP_LOAD_FACT, names["FB"], "F", SSP_LOAD_FACT_PK)):
        current = f"SELECT t.* FROM {target} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        frozen = f"SELECT t.* FROM {baseline} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        for lhs, rhs in ((current, frozen), (frozen, current)):
            _load_zero(session, f"SELECT COUNT(*) AS N FROM (({lhs}) MINUS ({rhs}))",
                       "UNTOUCHED_TARGET_ROWS_CHANGED")


def _load_verify_context(session, context):
    names, plans = context["names"], context["plans"]
    scope = _load_scope_check(session, names, plans)
    saved = _load_integrity(session, _load_scope_queries(names), names["IDS"], context["records"])
    reports = {}
    for target, kind, pk, plan, baseline in zip(
            (SSP_LOAD_DIM, SSP_LOAD_FACT), ("D", "F"), (SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK),
            plans, (names["DB"], names["FB"])):
        changes = _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        if changes["INSERTS"] or changes["UPDATES"]:
            raise LoadError("SAVED_BUSINESS_PAYLOAD_OR_KEYS_DIFFER", {"TABLE_KIND": kind, "COUNTS": changes})
        # Business-unchanged rows retain prior fields, including audit. Updated/new
        # rows must match every projected stage field, including current audit.
        cols = _load_columns(plan)
        business_same = "NOT (" + _load_difference_predicate(plan, "b", "s") + ")"
        all_old = " OR ".join("t." + _load_ident(c) + " IS DISTINCT FROM b." + _load_ident(c) for c in cols)
        all_new = " OR ".join(
            ("TRY_PARSE_JSON(TO_VARCHAR(t." + _load_ident(c) + ")) IS DISTINCT FROM "
             "TRY_PARSE_JSON(TO_VARCHAR(s." + _load_ident(c) + "))") if c == "METADATA_JSON"
            else "t." + _load_ident(c) + " IS DISTINCT FROM s." + _load_ident(c) for c in cols)
        _load_zero(session, f"""SELECT COUNT(*) AS N FROM {names[kind]} s
 JOIN {target} t ON t.{pk}=s.{pk} LEFT JOIN {baseline} b ON b.{pk}=s.{pk}
 WHERE (b.{pk} IS NOT NULL AND ({business_same}) AND ({all_old}))
 OR ((b.{pk} IS NULL OR NOT ({business_same})) AND ({all_new}))""",
                   "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER")
        reports["DIM" if kind == "D" else "FACT"] = changes
    _load_unchanged_scope(session, names)
    reports.update({"KEY_INTEGRITY": saved, "SCOPE": scope})
    return reports


def _load_dml_counts(rows):
    if len(rows) != 1:
        raise LoadError("DML_ROW_COUNT_UNAVAILABLE")
    row = {str(k).lower(): v for k, v in _load_row(rows[0]).items()}
    counts = []
    for label in ("number of rows inserted", "number of rows updated"):
        value = row.get(label)
        if type(value) not in (int, str) or not re.fullmatch(r"[0-9]+", str(value)):
            raise LoadError("DML_ROW_COUNT_UNAVAILABLE")
        counts.append(int(value))
    return tuple(counts)


def _load_transaction(session, merges, before_write, verify, expected_changes):
    if (not isinstance(merges, (list, tuple)) or len(merges) != 2
            or not isinstance(expected_changes, (list, tuple)) or len(expected_changes) != 2
            or any(not isinstance(pair, (list, tuple)) or len(pair) != 2
                   or any(type(v) is not int or v < 0 for v in pair) for pair in expected_changes)
            or not callable(before_write) or not callable(verify)):
        raise LoadError("INVALID_TRANSACTION_ARGUMENTS")
    for statement, target in zip(merges, (SSP_LOAD_DIM, SSP_LOAD_FACT)):
        if (not isinstance(statement, str) or ";" in statement
                or not statement.startswith("MERGE INTO " + target + " t USING ")
                or "WHEN MATCHED AND (" not in statement or "WHEN NOT MATCHED THEN INSERT" not in statement
                or re.search(r"\b(?:DELETE|TRUNCATE|DROP|CREATE|ALTER)\b", statement, re.IGNORECASE)):
            raise LoadError("MERGE_OUTSIDE_APPROVED_SSP_UPSERT_POLICY")
    _load_no_transaction(session)
    try:
        _load_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise LoadError("BEGIN_OUTCOME_UNKNOWN") from None
    step, pass_number, changes, checks = "PREWRITE_BASELINE", 0, [], []
    try:
        before_write()
        for pass_number in (1, 2):
            result = []
            for index, (step, statement) in enumerate(zip(("DIM_MERGE", "FACT_MERGE"), merges)):
                actual = _load_dml_counts(_load_query(session, statement))
                expected = tuple(expected_changes[index]) if pass_number == 1 else (0, 0)
                if actual != expected:
                    raise LoadError("UNEXPECTED_MERGE_CHANGE_COUNT",
                                    {"EXPECTED_INSERTS": expected[0], "EXPECTED_UPDATES": expected[1],
                                     "ACTUAL_INSERTS": actual[0], "ACTUAL_UPDATES": actual[1]})
                result.append({"INSERTS": actual[0], "UPDATES": actual[1]})
            changes.append({"PASS": pass_number, "DIM": result[0], "FACT": result[1]})
            step = "READBACK_AND_INTEGRITY"
            checks.append(verify(pass_number))
    except BaseException as error:
        details = dict(_load_error_details(error), STEP=step, PASS=pass_number)
        try:
            _load_query(session, "ROLLBACK")
        except BaseException:
            raise LoadError("ROLLBACK_OUTCOME_UNKNOWN", details) from None
        raise LoadError("TRANSACTION_ROLLED_BACK", details) from None
    try:
        _load_query(session, "COMMIT")
    except BaseException:
        raise LoadError("COMMIT_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED", "CHANGE_COUNTS": changes, "VERIFIED_PASSES": len(checks)}


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    result = {"release": SSP_LOAD_RELEASE, "model": config.get("OSCAL_MODEL"),
              "mode": "COMMIT" if config.get("EXECUTE_WRITES") is True else "PREVIEW",
              "writes_executed": False, "persisted": False, "target_dml_attempted": False,
              "obsolete_policy": "BLOCK"}
    phase, context = "SCHEMA_STAGING_AND_PREFLIGHT", None
    try:
        context = _load_prepare(session, canonical_nodes_df, canonical_edges_df, config)
        candidate = context["candidate"]
        result.update(nodes=int(candidate["NODES"]), edges=int(candidate["EDGES"]),
                      source_records=context["records"], validation_passed=True,
                      pre_write_validation_passed=True, dim_load_rows=int(candidate["NODES"]),
                      fact_load_rows=int(candidate["EDGES"]), scope=context["scope"],
                      expected_changes={"DIM": context["changes"][0], "FACT": context["changes"][1]})
        print("Graph nodes:", result["nodes"])
        print("Graph edges:", result["edges"])
        print("Duplicate node keys:", candidate["DIM_DUPLICATE_KEYS"])
        print("Duplicate edge keys:", candidate["FACT_DUPLICATE_KEYS"])
        print("Dangling source edges:", candidate["DANGLING_SOURCE_KEYS"])
        print("Dangling target edges:", candidate["DANGLING_TARGET_KEYS"])
        print("PRE-WRITE VALIDATION PASSED")
        if not config["EXECUTE_WRITES"]:
            result["status"] = "DAILY_SSP_PREVIEW_PASSED_NO_TARGET_DML"
            print("EXECUTE_WRITES = False; no DIM/FACT changes were made")
            return result
        names, plans = context["names"], context["plans"]
        queries = (f"SELECT * FROM {SSP_LOAD_DIM}", f"SELECT * FROM {SSP_LOAD_FACT}")
        merges = [_build_merge_sql(target, names[kind], pk, plan) for target, kind, pk, plan in
                  zip((SSP_LOAD_DIM, SSP_LOAD_FACT), ("D", "F"), (SSP_LOAD_DIM_PK, SSP_LOAD_FACT_PK), plans)]
        expected = tuple((int(c["INSERTS"]), int(c["UPDATES"])) for c in context["changes"])

        def before_write():
            _load_baseline_equal(session, names, queries)
            _load_scope_check(session, names, plans)
            result["target_dml_attempted"] = True

        phase = "TRANSACTION"
        transaction = _load_transaction(session, merges, before_write,
                                        lambda number: _load_verify_context(session, context), expected)
        result.update(writes_executed=True, persisted=True, transaction=transaction,
                      dim_merge_result=transaction["CHANGE_COUNTS"][0]["DIM"],
                      fact_merge_result=transaction["CHANGE_COUNTS"][0]["FACT"])
        phase = "POST_COMMIT_READBACK"
        verification = _load_verify_context(session, context)
        verification.update(dim_expected=result["nodes"], dim_matched=result["nodes"],
                            fact_expected=result["edges"], fact_matched=result["edges"])
        result.update(status="DAILY_SSP_COMMITTED_AND_VERIFIED", verification=verification)
        print("LOAD VERIFIED")
        return result
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "DAILY_LOAD_OPERATION_FAILED"
        result.update(status=code, phase=phase, error_details=_load_error_details(error))
        if code in ("BEGIN_OUTCOME_UNKNOWN", "COMMIT_OUTCOME_UNKNOWN", "ROLLBACK_OUTCOME_UNKNOWN"):
            result["persisted"] = "UNKNOWN_DO_NOT_RETRY"
        elif code == "TRANSACTION_ROLLED_BACK" and context:
            try:
                _load_baseline_equal(session, context["names"],
                                     (f"SELECT * FROM {SSP_LOAD_DIM}", f"SELECT * FROM {SSP_LOAD_FACT}"))
                result["rollback_readback_verified"] = True
            except BaseException:
                result.update(status="ROLLBACK_READBACK_FAILED_DO_NOT_RETRY", persisted="UNKNOWN_DO_NOT_RETRY")
        if phase == "POST_COMMIT_READBACK":
            result["status"] = "POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY"
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
        raise LoadError(result["status"], result) from None


def verify_oscal_load(canonical_nodes_df, canonical_edges_df, config):
    # Public API freezes fresh logical inputs; no target DML is performed.
    read_config = dict(config)
    read_config["EXECUTE_WRITES"] = False
    try:
        context = _load_prepare(session, canonical_nodes_df, canonical_edges_df, read_config)
        report = _load_verify_context(session, context)
        n, e = int(context["candidate"]["NODES"]), int(context["candidate"]["EDGES"])
        report.update(dim_expected=n, dim_matched=n, fact_expected=e, fact_matched=e)
        return report
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "READ_ONLY_VERIFICATION_FAILED"
        raise LoadError(code, _load_error_details(error)) from None


validate_and_load_oscal._oscal_loader_release = "ssp-daily-upsert-v1"
print("Cell 6 validation and loader initialized; execution remains in Cell 7")
