# %% Cell 6 - Validation, guarded idempotent DIM/FACT MERGE, verification
# Shared reviewed-contract upsert. Missing/obsolete in-scope rows block; no destructive policy.
# Keep other target writers paused for the complete preflight/transaction/readback.
import json
import re
import uuid
from types import MappingProxyType

OSCAL_LOAD_RELEASE = "oscal-shared-daily-upsert-v2"
_LOAD_AUDIT_COLUMNS = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}


class LoadError(RuntimeError):
    def __init__(self, code, details=None):
        self.code = code
        self.details = details or {}
        super().__init__(code)

_LOAD_DIM_COLUMNS = (
    "ELEMENT_TYPE", "OSCAL_UUID", "METADATA_JSON", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
    "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ",
)
_LOAD_FACT_COLUMNS = (
    "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE",
    "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID",
)
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


def _load_column_plan(description, kind, contract=None):
    c = _load_runtime_contract(contract)
    mappings = _load_sources(c)
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
        raw_type = entry["type"]
        dtype = raw_type.strip().upper() if isinstance(raw_type, str) else None
        text = re.fullmatch(r"(?:VARCHAR|STRING|TEXT)(?:\(\s*([1-9][0-9]*)\s*\))?", dtype or "")
        if text:
            dtype = "VARCHAR" + ("(" + str(int(text[1])) + ")" if text[1] else "")
        elif re.fullmatch(r"BINARY\(\s*16\s*\)", dtype or ""):
            dtype = "BINARY(16)"
        elif dtype != "VARIANT" and not re.fullmatch(
                r"TIMESTAMP_(?:NTZ|LTZ|TZ)(?:\([0-9]\))?", dtype or ""):
            code = "MISSING_LIVE_COLUMN_DATATYPE" if dtype is None else "UNSUPPORTED_LIVE_COLUMN_DATATYPE"
            # Only column metadata, never source values or full SQL, is reported.
            raise LoadError(code, {"TABLE_KIND": kind, "COLUMN": name,
                                   "LIVE_TYPE": str(raw_type)[:128]})
        source, encoding = sources[name], None
        expression = "s." + _load_ident(source)
        if source in _LOAD_HASH_SOURCES:
            if dtype != "BINARY(16)":
                raise LoadError("CONFIRMED_BINARY16_SCHEMA_REQUIRED")
            # Decode the existing identity; never hash again or truncate.
            expression = "TO_BINARY(" + expression + ", 'HEX')"
            encoding = "HEX_TO_BINARY16"
        elif source in _LOAD_UUID_SOURCES:
            if dtype != "VARCHAR(32)":
                raise LoadError("VERIFIED_UUID32_PROFILE_REQUIRED")
            expression = "REPLACE(" + expression + ", '-', '')"
            encoding = "UUID_TO_COMPACT32"
        elif name == "METADATA_JSON" and dtype == "VARIANT":
            expression = "PARSE_JSON(" + expression + ")"
        elif name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}:
            if not dtype.startswith("TIMESTAMP_"):
                raise LoadError("EXPLICIT_AUDIT_TIMESTAMP_TYPE_REQUIRED")
            expression = "CAST(" + expression + " AS " + dtype + ")"
        else:
            if not dtype.startswith("VARCHAR"):
                raise LoadError("UNSUPPORTED_PAYLOAD_DATATYPE" if name == "METADATA_JSON"
                                else "IDENTIFIERS_AND_LABELS_REQUIRE_STRING_TYPE")
            expression = "CAST(" + expression + " AS VARCHAR)"
        plan.append({"name": name, "source": source, "expression": expression,
                     "type": dtype, "nullable": nullable == "Y", "encoding": encoding})
    optional = _LOAD_AUDIT_COLUMNS if kind == "DIM" else set()
    missing = set(sources) - optional - seen
    if missing:
        raise LoadError("MISSING_TARGET_COLUMNS_" + "_".join(sorted(missing)))
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


def _load_projection_values(session, query, plan, stage_codes=False):
    for column in plan:
        name, dtype = _load_ident(column["name"]), column["type"]
        generic = "INVALID_STORED_OR_STAGED_COLUMN_" + column["name"]
        checks = []
        if not column["nullable"]:
            checks.append((name + " IS NULL", "REQUIRED_TARGET_VALUE_IS_NULL"))
        if dtype == "BINARY(16)":
            checks.append((name + " IS NULL OR OCTET_LENGTH(" + name + ")<>16",
                           "BINARY_KEY_WIDTH_INVALID"))
        if column["source"] in _LOAD_UUID_SOURCES:
            checks.append((name + " IS NULL OR NOT REGEXP_LIKE(" + name + ", '[0-9a-f]{32}')", None))
        width = re.fullmatch(r"VARCHAR\((\d+)\)", dtype)
        if width:
            checks.append(("LENGTH(" + name + ")>" + width[1], "TARGET_STRING_CAPACITY_EXCEEDED"))
        if column["name"] == "METADATA_JSON":
            checks.append(("NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(TO_VARCHAR(" + name +
                           "))),FALSE)", None))
        for condition, specific in checks:
            _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) WHERE {condition}",
                       specific if stage_codes and specific else generic)


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
    _load_projection_values(session, "SELECT * FROM " + stage, plan, stage_codes=True)
    for column in plan:
        name = _load_ident(column["name"])
        if column["source"] in {"NODE_KEY", "EDGE_KEY"}:
            # Different text casing can collapse to the same physical binary key.
            _load_unique(session, stage, name)


def _load_equal(session, current, frozen, code):
    for left, right in ((current, frozen), (frozen, current)):
        _load_zero(session, f"SELECT COUNT(*) AS N FROM (({left}) MINUS ({right}))", code)


def _load_baseline_equal(session, names, queries):
    # Multiset comparison: keep duplicate multiplicities in the OLD full tables.
    # GROUP BY ALL includes every existing target column, including VARIANT payloads.
    for baseline, query in zip((names["DB"], names["FB"]), queries):
        current = f"SELECT *, COUNT(*) AS OSCAL_LOAD_ROW_MULTIPLICITY FROM ({query}) GROUP BY ALL"
        frozen = f"SELECT *, COUNT(*) AS OSCAL_LOAD_ROW_MULTIPLICITY FROM {baseline} GROUP BY ALL"
        _load_equal(session, current, frozen, "TARGET_BASELINE_CHANGED")


def _load_integrity_sql(queries, ids, allow_absent=False, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    if type(allow_absent) is not bool:
        raise LoadError("INVALID_OLD_GRAPH_POLICY")
    dim, fact = queries
    relationship = "('parent_of','CONTAINS')" if allow_absent else "('CONTAINS')"
    empty = "c.NODES=0 AND COALESCE(e.EDGES,0)=0" if allow_absent else "FALSE"
    return f"""WITH checked_nodes AS ({dim}), checked_edges AS ({fact}),
record_counts AS (
 SELECT i.SOURCE_RECORD_ID, COUNT(d.{dk}) AS NODES,
        SUM(CASE WHEN d.ELEMENT_TYPE={root_type} THEN 1 ELSE 0 END) AS ROOTS
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
     NOT EQUAL_NULL(d.SOURCE_SYSTEM_NAME,{source_system}) OR
     NOT EQUAL_NULL(d.SOURCE_TABLE_NAME,{source_table}) OR
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
     HAVING COUNT(f.{fk}) <> CASE WHEN d.ELEMENT_TYPE={root_type} THEN 0 ELSE 1 END)) AS WRONG_PARENT_COUNTS,
 (SELECT COUNT(*) FROM record_counts c LEFT JOIN edge_counts e ON e.SOURCE_RECORD_ID=c.SOURCE_RECORD_ID
     WHERE NOT ({empty}) AND
     (c.NODES<1 OR c.ROOTS<>1 OR COALESCE(e.EDGES,0)<>c.NODES-1)) AS INVALID_RECORD_SHAPES"""


def _load_integrity(session, queries, ids, expected_records, allow_absent=False, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    row = _load_query(session, _load_integrity_sql(queries, ids, allow_absent, c))[0]
    report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
    metrics = ("SELECTED_RECORDS", "NODES", "EDGES")
    if report.get("SELECTED_RECORDS") != expected_records or any(v != 0 for k, v in report.items() if k not in metrics):
        raise LoadError("BATCH_PRIMARY_FOREIGN_KEY_OR_HIERARCHY_FAILED", {"KEY_CHECKS": report})
    # Cardinality is checked first; disconnected cycles must still fail reachability.
    dim, fact = queries
    bound = max(int(report["NODES"]), 1)
    sql = f"""WITH RECURSIVE checked_nodes AS ({dim}), checked_edges AS ({fact}),
tree(K,SOURCE_RECORD_ID,DEPTH) AS (
 SELECT {dk},SOURCE_RECORD_ID,0 FROM checked_nodes WHERE ELEMENT_TYPE={root_type}
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


def _load_comparison(columns, left="t", right="s", include_audit=False, parse_json=True):
    names = [c["name"] if isinstance(c, dict) else c for c in columns]
    for name in names:
        _load_ident(name)
    if not names or len(names) != len(set(names)):
        raise LoadError("INVALID_PROJECTION_COLUMNS")
    if left not in ("t", "s", "b") or right not in ("t", "s", "b"):
        raise LoadError("INVALID_COMPARISON_ALIAS")
    terms = []
    for name in (name for name in names if include_audit or name not in _LOAD_AUDIT_COLUMNS):
        lhs, rhs = left + "." + _load_ident(name), right + "." + _load_ident(name)
        if parse_json and name == "METADATA_JSON":
            # Structural object comparison, not JSON key ordering.
            lhs = "TRY_PARSE_JSON(TO_VARCHAR(" + lhs + "))"
            rhs = "TRY_PARSE_JSON(TO_VARCHAR(" + rhs + "))"
        terms.append("(" + lhs + " IS DISTINCT FROM " + rhs + ")")
    if not terms:
        raise LoadError("BUSINESS_COLUMNS_REQUIRED")
    return names, " OR ".join(terms)


def _build_merge_sql(target_table, source_view, pk_column, columns, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    expected_pk = {dim_table: dk, fact_table: fk}
    if expected_pk.get(target_table) != pk_column:
        raise LoadError("TARGET_OUTSIDE_APPROVED_STORAGE_CONTRACT")
    names, changed = _load_comparison(columns)
    if pk_column not in names:
        raise LoadError("MISSING_PROJECTED_PRIMARY_KEY")
    _load_table(source_view)
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
    _, changed = _load_comparison(columns)
    return f"""SELECT
 (SELECT COUNT(*) FROM {stage_sql} s WHERE NOT EXISTS
     (SELECT 1 FROM {target_sql} t WHERE t.{key}=s.{key})) AS INSERTS,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE {changed}) AS UPDATES,
 (SELECT COUNT(*) FROM {stage_sql} s JOIN {target_sql} t ON t.{key}=s.{key}
     WHERE NOT ({changed})) AS UNCHANGED"""



def _load_row(row):
    raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
    return {str(k).upper(): v for k, v in raw.items()}


def _load_scope_queries(names, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    # Include ownership AND key matches: foreign-owned identities cannot hide.
    dim = f"""SELECT t.* FROM {dim_table} t
 LEFT JOIN {names['D']} s ON s.{dk}=t.{dk}
 LEFT JOIN {names['IDS']} i ON i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID
     AND t.SOURCE_SYSTEM_NAME={source_system} AND t.SOURCE_TABLE_NAME={source_table}
 WHERE s.{dk} IS NOT NULL OR i.SOURCE_RECORD_ID IS NOT NULL"""
    keys = f"SELECT {dk} FROM ({dim}) UNION SELECT {dk} FROM {names['D']}"
    fact = f"""SELECT t.* FROM {fact_table} t
 LEFT JOIN {names['F']} f ON f.{fk}=t.{fk}
 LEFT JOIN ({keys}) s ON s.{dk}=t.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({keys}) d ON d.{dk}=t.FK_TARGET_ELEMENT_HASH
 WHERE f.{fk} IS NOT NULL OR s.{dk} IS NOT NULL
     OR d.{dk} IS NOT NULL"""
    return dim, fact


def _load_scope_check(session, names, plans, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    source_system = _load_literal(c["SOURCE_SYSTEM_NAME"])
    source_table = _load_literal(c["SOURCE_TABLE_NAME"])
    queries = _load_scope_queries(names, c)
    for target, pk in ((dim_table, dk), (fact_table, fk)):
        _load_unique(session, target, pk)
    extra = {}
    for kind, pk, query, plan in zip(("D", "F"), (dk, fk), queries, plans):
        extra[kind] = _load_count(session, f"SELECT COUNT(*) AS N FROM ({query}) t "
                                  f"WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})")
        ownership = ("SOURCE_RECORD_ID", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "ELEMENT_TYPE", "OSCAL_UUID") if kind == "D" else (
            "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID")
        conflict = " OR ".join(f"t.{_load_ident(c)} IS DISTINCT FROM s.{_load_ident(c)}" for c in ownership)
        _load_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) t JOIN {names[kind]} s "
                           f"ON t.{pk}=s.{pk} WHERE {conflict}", "TARGET_IDENTITY_PROVENANCE_CONFLICT")
        _load_projection_values(session, query, plan)
    report = {"OBSOLETE_DIM_ROWS": extra["D"], "OBSOLETE_FACT_ROWS": extra["F"]}
    if any(extra.values()):
        raise LoadError("OBSOLETE_TARGET_ROWS_BLOCKED", report)
    dim, fact = queries
    _load_zero(session, f"""SELECT COUNT(*) AS N FROM ({fact}) f
 LEFT JOIN ({dim}) s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
 LEFT JOIN ({dim}) t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
 WHERE s.{dk} IS NULL OR t.{dk} IS NULL""",
               "CROSS_SCOPE_LINKS_BLOCKED")
    report["ABSENT_INPUT_SOURCE_RECORDS_PRESERVED"] = _load_count(session, f"""
 SELECT COUNT(*) AS N FROM (SELECT DISTINCT t.SOURCE_RECORD_ID FROM {dim_table} t
 WHERE t.SOURCE_SYSTEM_NAME={source_system} AND t.SOURCE_TABLE_NAME={source_table}
 AND NOT EXISTS (SELECT 1 FROM {names['IDS']} i WHERE i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID))""")
    return report


def _load_freeze(session, nodes, edges, names, contract=None):
    c = _load_runtime_contract(contract)
    root = _load_literal(c["ROOT_PATH"])
    root_type = _load_literal(c["ROOT_ELEMENT_TYPE"])
    required_nodes = set(_load_sources(c)["DIM"].values()) - _LOAD_AUDIT_COLUMNS
    required_nodes |= {"ELEMENT_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY"}
    required_edges = set(_load_sources(c)["FACT"].values())
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
 OR ELEMENT_PATH IS NULL OR (ELEMENT_PATH<>{root}
     AND NOT STARTSWITH(ELEMENT_PATH, {root}||'.'))
 OR ELEMENT_TYPE IS DISTINCT FROM CASE WHEN ELEMENT_PATH={root} THEN {root_type} ELSE REPLACE(SPLIT_PART(ELEMENT_PATH,'.',-1),'[]','') END
 OR NOT COALESCE(IS_OBJECT(TRY_PARSE_JSON(METADATA_JSON)),FALSE)""", "INVALID_MODEL_PATH_IDENTITY_OR_PAYLOAD")
    roots = f"SELECT SOURCE_RECORD_ID FROM {nv} WHERE ELEMENT_PATH={root}"
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
    c = _load_contract(config)
    if c is None:
        if config["EXECUTE_WRITES"]:
            raise LoadError("STORAGE_CONTRACT_NOT_VERIFIED")
        graph = _load_logical_graph(nodes, edges, _load_graph_contract(config), config.get("EXPECTED_SOURCE_RECORDS"))
        return {"storage_verified": False, "candidate": graph, "records": graph["SELECTED_RECORDS"]}
    dim_table, fact_table, dk, fk = _load_targets(c)
    _load_no_transaction(session)
    prefix = c["TARGET_DIM"].rsplit(".", 1)[0] + ".TMP_OSCAL_DAILY_" + uuid.uuid4().hex.upper()
    names = {k: prefix + "_" + k for k in ("NV", "EV", "IDS", "D", "F", "DB", "FB")}
    plans = [_load_column_plan(_load_query(session, "DESC TABLE " + target), kind, c)
             for target, kind in ((dim_table, "DIM"), (fact_table, "FACT"))]
    records = _load_freeze(session, nodes, edges, names, c)
    expected_records = config.get("EXPECTED_SOURCE_RECORDS")
    if expected_records is not None and (
            type(expected_records) is not int or expected_records <= 0 or records != expected_records):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH",
                        {"EXPECTED_SOURCE_RECORDS": expected_records, "GRAPH_SOURCE_RECORDS": records})
    for raw, physical, plan in zip(("NV", "EV"), ("D", "F"), plans):
        _load_stage(session, names[raw], names[physical], plan)
    candidates = (f"SELECT * FROM {names['D']}", f"SELECT * FROM {names['F']}")
    candidate = _load_integrity(session, candidates, names["IDS"], records, contract=c)
    for target, key in ((dim_table, "DB"), (fact_table, "FB")):
        _load_query(session, f"CREATE TEMPORARY TABLE {names[key]} AS SELECT * FROM {target}")
    context = {"names": names, "plans": plans, "records": records, "candidate": candidate, "contract": c, "storage_verified": True}
    context["scope"] = _load_scope_check(session, names, plans, c)
    _load_integrity(session, _load_scope_queries(names, c), names["IDS"], records, allow_absent=True, contract=c)
    context["changes"] = [
        _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        for target, kind, pk, plan in zip((dim_table, fact_table), ("D", "F"),
                                         (dk, fk), plans)]
    return context

def _load_unchanged_scope(session, names, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    for target, baseline, kind, pk in (
        (dim_table, names["DB"], "D", dk),
        (fact_table, names["FB"], "F", fk)):
        current = f"SELECT t.* FROM {target} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        frozen = f"SELECT t.* FROM {baseline} t WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        _load_equal(session, current, frozen, "UNTOUCHED_TARGET_ROWS_CHANGED")


def _load_verify_context(session, context):
    c = _load_runtime_contract(context.get("contract"))
    dim_table, fact_table, dk, fk = _load_targets(c)
    names, plans = context["names"], context["plans"]
    scope = _load_scope_check(session, names, plans, c)
    saved = _load_integrity(session, _load_scope_queries(names, c), names["IDS"], context["records"], contract=c)
    reports = {}
    for target, kind, pk, plan, baseline in zip(
            (dim_table, fact_table), ("D", "F"), (dk, fk),
            plans, (names["DB"], names["FB"])):
        changes = _load_row(_load_query(session, _load_expected_changes_sql(target, names[kind], pk, plan))[0])
        if changes["INSERTS"] or changes["UPDATES"]:
            raise LoadError("SAVED_BUSINESS_PAYLOAD_OR_KEYS_DIFFER", {"TABLE_KIND": kind, "COUNTS": changes})
        # Business-unchanged rows retain prior fields, including audit. Updated/new
        # rows must match every projected stage field, including current audit.
        _, business_changed = _load_comparison(plan, "b", "s")
        business_same = "NOT (" + business_changed + ")"
        _, all_old = _load_comparison(plan, "t", "b", include_audit=True, parse_json=False)
        _, all_new = _load_comparison(plan, include_audit=True)
        _load_zero(session, f"""SELECT COUNT(*) AS N FROM {names[kind]} s
 JOIN {target} t ON t.{pk}=s.{pk} LEFT JOIN {baseline} b ON b.{pk}=s.{pk}
 WHERE (b.{pk} IS NOT NULL AND ({business_same}) AND ({all_old}))
 OR ((b.{pk} IS NULL OR NOT ({business_same})) AND ({all_new}))""",
                   "SAVED_PROJECTION_OR_UNCHANGED_AUDIT_DIFFER")
        reports["DIM" if kind == "D" else "FACT"] = changes
    _load_unchanged_scope(session, names, c)
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


def _load_transaction(session, merges, before_write, verify, expected_changes, contract=None):
    c = _load_runtime_contract(contract)
    dim_table, fact_table, dk, fk = _load_targets(c)
    if (not isinstance(merges, (list, tuple)) or len(merges) != 2
            or not isinstance(expected_changes, (list, tuple)) or len(expected_changes) != 2
            or any(not isinstance(pair, (list, tuple)) or len(pair) != 2
                   or any(type(v) is not int or v < 0 for v in pair) for pair in expected_changes)
            or not callable(before_write) or not callable(verify)):
        raise LoadError("INVALID_TRANSACTION_ARGUMENTS")
    for statement, target in zip(merges, (dim_table, fact_table)):
        if (not isinstance(statement, str) or ";" in statement
                or not statement.startswith("MERGE INTO " + target + " t USING ")
                or "WHEN MATCHED AND (" not in statement or "WHEN NOT MATCHED THEN INSERT" not in statement
                or re.search(r"\b(?:DELETE|TRUNCATE|DROP|CREATE|ALTER)\b", statement, re.IGNORECASE)):
            raise LoadError("MERGE_OUTSIDE_APPROVED_UPSERT_POLICY")
    _load_no_transaction(session)
    try:
        _load_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise LoadError("BEGIN_OUTCOME_UNKNOWN") from None
    step, result = "PREWRITE_BASELINE", []
    try:
        before_write()
        for step, statement, expected in zip(("DIM_MERGE", "FACT_MERGE"), merges, expected_changes):
            actual = _load_dml_counts(_load_query(session, statement))
            if actual != tuple(expected):
                raise LoadError("UNEXPECTED_MERGE_CHANGE_COUNT",
                                {"EXPECTED_INSERTS": expected[0], "EXPECTED_UPDATES": expected[1],
                                 "ACTUAL_INSERTS": actual[0], "ACTUAL_UPDATES": actual[1]})
            result.append({"INSERTS": actual[0], "UPDATES": actual[1]})
        step = "READBACK_AND_INTEGRITY"
        verify(1)
    except BaseException as error:
        details = dict(_load_error_details(error), STEP=step, PASS=int(step != "PREWRITE_BASELINE"))
        try:
            _load_query(session, "ROLLBACK")
        except BaseException:
            raise LoadError("ROLLBACK_OUTCOME_UNKNOWN", details) from None
        raise LoadError("TRANSACTION_ROLLED_BACK", details) from None
    try:
        _load_query(session, "COMMIT")
    except BaseException:
        raise LoadError("COMMIT_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED", "VERIFIED_PASSES": 1,
            "CHANGE_COUNTS": [{"PASS": 1, "DIM": result[0], "FACT": result[1]}]}


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    config = dict(config)
    result = {"release": OSCAL_LOAD_RELEASE, "model": config.get("OSCAL_MODEL"),
              "mode": "COMMIT" if config.get("EXECUTE_WRITES") is True else "PREVIEW",
              "writes_executed": False, "persisted": False, "target_dml_attempted": False,
              "obsolete_policy": "BLOCK"}
    phase, context = "SCHEMA_STAGING_AND_PREFLIGHT", None
    try:
        context = _load_prepare(session, canonical_nodes_df, canonical_edges_df, config)
        candidate = context["candidate"]
        nodes, edges = int(candidate["NODES"]), int(candidate["EDGES"])
        verified = context.get("storage_verified") is not False
        result.update(nodes=nodes, edges=edges, source_records=context["records"],
                      validation_passed=True, storage_verified=verified,
                      pre_write_validation_passed=verified,
                      dim_load_rows=nodes if verified else 0, fact_load_rows=edges if verified else 0)
        if not verified:
            result.update(status="MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING",
                          graph_integrity=candidate)
            return result
        c = _load_runtime_contract(context.get("contract"))
        dim_table, fact_table, dk, fk = _load_targets(c)
        result.update(scope=context["scope"],
                      expected_changes={"DIM": context["changes"][0], "FACT": context["changes"][1]})
        print("Validated graph:", nodes, "nodes,", edges, "edges")
        print("PRE-WRITE VALIDATION PASSED")
        if not config["EXECUTE_WRITES"]:
            result["status"] = "DAILY_" + c["MODEL_KEY"] + "_PREVIEW_PASSED_NO_TARGET_DML"
            print("EXECUTE_WRITES = False; no DIM/FACT changes were made")
            return result
        names, plans = context["names"], context["plans"]
        queries = (f"SELECT * FROM {dim_table}", f"SELECT * FROM {fact_table}")
        merges = [_build_merge_sql(target, names[kind], pk, plan, c) for target, kind, pk, plan in
                  zip((dim_table, fact_table), ("D", "F"), (dk, fk), plans)]
        expected = tuple((int(c["INSERTS"]), int(c["UPDATES"])) for c in context["changes"])

        def before_write():
            _load_baseline_equal(session, names, queries)
            _load_scope_check(session, names, plans, c)
            result["target_dml_attempted"] = True

        phase = "TRANSACTION"
        transaction = _load_transaction(session, merges, before_write,
                                        lambda number: _load_verify_context(session, context), expected, c)
        result.update(writes_executed=True, persisted=True, transaction=transaction,
                      dim_merge_result=transaction["CHANGE_COUNTS"][0]["DIM"],
                      fact_merge_result=transaction["CHANGE_COUNTS"][0]["FACT"])
        phase = "POST_COMMIT_READBACK"
        verification = _load_verify_context(session, context)
        verification.update(dim_expected=result["nodes"], dim_matched=result["nodes"],
                            fact_expected=result["edges"], fact_matched=result["edges"])
        result.update(status="DAILY_" + c["MODEL_KEY"] + "_COMMITTED_AND_VERIFIED", verification=verification)
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
                                     (f"SELECT * FROM {dim_table}", f"SELECT * FROM {fact_table}"))
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
        if context.get("storage_verified") is False:
            return {"status": "MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING",
                    "validation_passed": True, "storage_verified": False, "writes_executed": False,
                    "dim_expected": context["candidate"]["NODES"], "fact_expected": context["candidate"]["EDGES"],
                    "dim_matched": None, "fact_matched": None}
        report = _load_verify_context(session, context)
        n, e = int(context["candidate"]["NODES"]), int(context["candidate"]["EDGES"])
        report.update(dim_expected=n, dim_matched=n, fact_expected=e, fact_matched=e)
        return report
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "READ_ONLY_VERIFICATION_FAILED"
        raise LoadError(code, _load_error_details(error)) from None



def _load_literal(value):
    if not isinstance(value, str) or not value.strip():
        raise LoadError("EMPTY_CONTRACT_VALUE")
    return "'" + value.replace("'", "''") + "'"


def _load_runtime_contract(contract):
    if not isinstance(contract, (dict, MappingProxyType)):
        raise LoadError("INVALID_STORAGE_CONTRACT")
    copied = dict(contract)
    required = ("MODEL_KEY", "ROOT_PATH", "ROOT_ELEMENT_TYPE", "SOURCE_SYSTEM_NAME",
                "SOURCE_TABLE_NAME", "RAW_TABLE", "TARGET_DIM", "TARGET_FACT",
                "DIM_PK_COLUMN", "FACT_PK_COLUMN", "IDENTITY_VERSION", "PHYSICAL_PROFILE")
    if copied.get("VERIFIED") is not True or any(
            not isinstance(copied.get(k), str) or not copied[k].strip() for k in required):
        raise LoadError("STORAGE_CONTRACT_NOT_VERIFIED")
    if copied["PHYSICAL_PROFILE"] != "BINARY16_UUID32":
        raise LoadError("UNSUPPORTED_REVIEWED_PHYSICAL_PROFILE")
    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", copied["MODEL_KEY"]):
        raise LoadError("INVALID_MODEL_KEY")
    if not re.fullmatch(r"[a-z][a-z0-9-]*", copied["ROOT_PATH"]):
        raise LoadError("INVALID_MODEL_ROOT_PATH")
    for key in ("RAW_TABLE", "TARGET_DIM", "TARGET_FACT"):
        parts = copied[key].split(".")
        if len(parts) != 3:
            raise LoadError("FULLY_QUALIFIED_CONTRACT_TABLE_REQUIRED")
        for part in parts:
            _load_ident(part)
    for key in ("DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        _load_ident(copied[key])
    if copied["TARGET_DIM"] == copied["TARGET_FACT"]:
        raise LoadError("DIM_AND_FACT_TARGETS_MUST_DIFFER")
    return MappingProxyType({k: copied[k] for k in (*required, 'VERIFIED')})


def _load_targets(contract):
    return (contract["TARGET_DIM"], contract["TARGET_FACT"],
            contract["DIM_PK_COLUMN"], contract["FACT_PK_COLUMN"])


def _load_sources(contract):
    dim = {name: name for name in _LOAD_DIM_COLUMNS}
    fact = {name: name for name in _LOAD_FACT_COLUMNS}
    dim[contract["DIM_PK_COLUMN"]] = "NODE_KEY"
    fact[contract["FACT_PK_COLUMN"]] = "EDGE_KEY"
    return {"DIM": dim, "FACT": fact}


def _load_graph_contract(config):
    root = config.get("ROOT_PATH", config.get("MODEL_ROOT_PATH"))
    fields = {"MODEL_KEY": config.get("OSCAL_MODEL"), "ROOT_PATH": root,
              "ROOT_ELEMENT_TYPE": config.get("ROOT_ELEMENT_TYPE"),
              "SOURCE_SYSTEM_NAME": config.get("SOURCE_SYSTEM_NAME"),
              "SOURCE_TABLE_NAME": config.get("SOURCE_TABLE_NAME"),
              "RAW_TABLE": config.get("RAW_TABLE"),
              "IDENTITY_VERSION": config.get("IDENTITY_VERSION")}
    for key in ("MODEL_KEY", "ROOT_PATH", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
                "RAW_TABLE", "IDENTITY_VERSION"):
        if not isinstance(fields[key], str) or not fields[key].strip():
            raise LoadError("MISSING_GRAPH_CONTRACT_" + key)
    if not re.fullmatch(r"[a-z][a-z0-9-]*", root):
        raise LoadError("INVALID_MODEL_ROOT_PATH")
    return MappingProxyType(fields)


def _load_contract(config):
    if type(config.get("EXECUTE_WRITES")) is not bool:
        raise LoadError("EXPLICIT_BOOLEAN_WRITE_MODE_REQUIRED")
    if config.get("OBSOLETE_ROW_POLICY", "BLOCK") != "BLOCK":
        raise LoadError("ONLY_BLOCK_OBSOLETE_POLICY_IS_APPROVED")
    supplied = config.get("STORAGE_CONTRACT")
    if supplied is None or (isinstance(supplied, (dict, MappingProxyType))
                            and supplied.get("VERIFIED") is not True):
        return None
    contract = _load_runtime_contract(supplied)
    matches = {"OSCAL_MODEL": "MODEL_KEY", "SOURCE_SYSTEM_NAME": "SOURCE_SYSTEM_NAME",
               "SOURCE_TABLE_NAME": "SOURCE_TABLE_NAME", "RAW_TABLE": "RAW_TABLE",
               "IDENTITY_VERSION": "IDENTITY_VERSION"}
    for cfg, key in matches.items():
        if config.get(cfg) != contract[key]:
            raise LoadError("CONFIG_STORAGE_CONTRACT_MISMATCH")
    for key in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        if config.get(key) is not None and config[key] != contract[key]:
            raise LoadError("CONFIG_STORAGE_CONTRACT_MISMATCH")
    root = config.get("ROOT_PATH", config.get("MODEL_ROOT_PATH"))
    if root is not None and root != contract["ROOT_PATH"]:
        raise LoadError("CONFIG_STORAGE_ROOT_MISMATCH")
    if config.get("ROOT_ELEMENT_TYPE") not in (None, contract["ROOT_ELEMENT_TYPE"]):
        raise LoadError("CONFIG_STORAGE_ROOT_TYPE_MISMATCH")
    return contract


def _load_logical_graph(nodes, edges, contract, expected_records=None):
    # A targetless preview reads only the canonical graph, never target metadata.
    # Payloads are checked then discarded; reports contain aggregate counts only.
    def rows(frame):
        return frame.to_local_iterator() if hasattr(frame, "to_local_iterator") else iter(frame)
    def row(value):
        return value.as_dict() if hasattr(value, "as_dict") else dict(value)
    def key(value):
        if not isinstance(value, str) or not re.fullmatch(_LOAD_HEX_PATTERN, value):
            raise LoadError("INVALID_LOGICAL_HASH_IDENTITY")
        return value.lower()
    def canonical_uuid(value):
        if not isinstance(value, str) or not re.fullmatch(_LOAD_UUID_PATTERN, value):
            raise LoadError("INVALID_LOGICAL_UUID")
        return value

    root = contract["ROOT_PATH"]
    by_key, roots, parents, root_types = {}, {}, {}, set()
    for raw in rows(nodes):
        n = row(raw)
        k = key(n.get("NODE_KEY"))
        if k in by_key:
            raise LoadError("DUPLICATE_LOGICAL_NODE_KEY")
        sid, path, typ = n.get("SOURCE_RECORD_ID"), n.get("ELEMENT_PATH"), n.get("ELEMENT_TYPE")
        if not isinstance(sid, str) or not sid.strip():
            raise LoadError("MISSING_LOGICAL_SOURCE_RECORD_ID")
        if (not isinstance(path, str) or not (path == root or path.startswith(root + "."))
                or not isinstance(typ, str) or not typ.strip()):
            raise LoadError("LOGICAL_MODEL_PATH_OR_TYPE_MISMATCH")
        if (n.get("SOURCE_SYSTEM_NAME") != contract["SOURCE_SYSTEM_NAME"]
                or n.get("SOURCE_TABLE_NAME") != contract["SOURCE_TABLE_NAME"]
                or ("MODEL_KEY" in n and n["MODEL_KEY"] != contract["MODEL_KEY"])):
            raise LoadError("LOGICAL_MODEL_OR_SOURCE_OWNERSHIP_MISMATCH")
        instance = n.get("INSTANCE_KEY")
        if not isinstance(instance, str) or not instance.strip():
            raise LoadError("MISSING_LOGICAL_INSTANCE_KEY")
        payload = n.get("METADATA_JSON")
        try:
            payload = json.loads(payload) if isinstance(payload, str) else payload
        except (ValueError, TypeError):
            raise LoadError("INVALID_LOGICAL_PAYLOAD") from None
        if not isinstance(payload, dict):
            raise LoadError("INVALID_LOGICAL_PAYLOAD")
        by_key[k] = (sid, path, canonical_uuid(n.get("OSCAL_UUID")), instance, n.get("PARENT_INSTANCE_KEY"))
        parents[k] = 0
        if path == root:
            if sid in roots:
                raise LoadError("MULTIPLE_MODEL_ROOTS_FOR_RECORD")
            roots[sid] = k
            root_types.add(typ)
            if contract.get("ROOT_ELEMENT_TYPE") not in (None, typ):
                raise LoadError("LOGICAL_ROOT_REGISTRY_TYPE_MISMATCH")
    if not roots or len(root_types) != 1:
        raise LoadError("EMPTY_OR_INCONSISTENT_MODEL_ROOTS")
    if expected_records is not None and (type(expected_records) is not int
                                         or expected_records != len(roots)):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH")
    edge_keys = set()
    for raw in rows(edges):
        e = row(raw)
        ek = key(e.get("EDGE_KEY"))
        if ek in edge_keys:
            raise LoadError("DUPLICATE_LOGICAL_EDGE_KEY")
        edge_keys.add(ek)
        source, target = key(e.get("FK_SOURCE_ELEMENT_HASH")), key(e.get("FK_TARGET_ELEMENT_HASH"))
        if source not in by_key or target not in by_key:
            raise LoadError("DANGLING_LOGICAL_FOREIGN_KEY")
        s, t = by_key[source], by_key[target]
        if s[0] != t[0] or s[0] not in roots:
            raise LoadError("CROSS_RECORD_LOGICAL_EDGE")
        if (e.get("DEPENDENCY_TYPE") != "CONTAINS"
                or e.get("SOURCE_OSCAL_UUID") != s[2]
                or e.get("TARGET_OSCAL_UUID") != t[2]):
            raise LoadError("LOGICAL_RELATIONSHIP_OR_UUID_MISMATCH")
        if not t[1].startswith(s[1] + ".") or (t[4] is not None and t[4] != s[3]):
            raise LoadError("LOGICAL_PARENT_CONTEXT_MISMATCH")
        parents[target] += 1
    root_keys = set(roots.values())
    if any(parents[k] != (0 if k in root_keys else 1) for k in by_key):
        raise LoadError("INVALID_LOGICAL_PARENT_CARDINALITY")
    # Strictly descending paths exclude cycles. One parent per non-root then
    # proves every node is reachable from its record root; no second walk is needed.
    return {"SELECTED_RECORDS": len(roots), "NODES": len(by_key), "EDGES": len(edge_keys),
            "DIM_DUPLICATE_KEYS": 0, "FACT_DUPLICATE_KEYS": 0,
            "DANGLING_SOURCE_KEYS": 0, "DANGLING_TARGET_KEYS": 0,
            "ROOTS": len(roots), "DISCONNECTED_RECORDS": 0}


validate_and_load_oscal._oscal_loader_release = "oscal-shared-daily-upsert-v2"
print("Cell 6 validation and loader initialized; execution remains in Cell 7")
