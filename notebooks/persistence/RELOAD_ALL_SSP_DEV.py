# Full SSP DEV truncate-and-reload; replaces ALL rows in the two fixed targets.
# Stages/checks the entire accepted graph, then truncates and loads in one transaction.
# No permanent backup. Pause other target writers; requires accepted Cells 1-7.
import json
import re
import uuid


SSP_RELOAD_RELEASE = "ssp-full-dev-truncate-reload-v1"
SSP_RELOAD_MODE = "PREVIEW"  # Set COMMIT for the authorized full DEV reload.
SSP_RELOAD_SOURCE_RECORDS = 2813
SSP_PILOT_DIM = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT"
SSP_PILOT_FACT = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY"
SSP_PILOT_DIM_PK = "PK_OSCAL_SSP_ELEMENT_HASH"
SSP_PILOT_FACT_PK = "PK_FACT_OSCAL_DEPENDENCY_HASH"
SSP_PILOT_SOURCE = "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
SSP_PILOT_ACCEPTED_COUNTS = (70102, 67289)


class PilotError(RuntimeError):
    def __init__(self, code, details=None):
        self.code = code
        self.details = details or {}
        super().__init__(code)


def _pilot_query(session, statement):
    return session.sql(statement).collect()


def _pilot_error_details(error):
    # Preserve actionable categories without echoing Snowflake/source messages.
    details = {"CAUSE": error.code if isinstance(error, PilotError) else
               ("CANCELLED" if isinstance(error, (KeyboardInterrupt, SystemExit)) else "SQL_OR_CLIENT_ERROR")}
    if isinstance(error, PilotError):
        details.update(error.details)
    for attr, label, pattern in (("sql_error_code", "SQL_ERROR_CODE", r"[0-9]{1,10}"),
                                 ("sqlstate", "SQLSTATE", r"[A-Z0-9]{5}"),
                                 ("sfqid", "QUERY_ID", r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")):
        value = str(getattr(error, attr, ""))
        if re.fullmatch(pattern, value):
            details[label] = value
    return details


def _pilot_no_transaction(session):
    try:
        transaction = _pilot_query(session, "SELECT CURRENT_TRANSACTION() AS TX")[0]["TX"]
    except BaseException:
        raise PilotError("TRANSACTION_STATE_UNAVAILABLE") from None
    if transaction is not None:
        raise PilotError("EXISTING_TRANSACTION_STOPPED_PILOT")


def _pilot_contract(config, run_result):
    expected = {
        "OSCAL_MODEL": "SSP", "TARGET_DIM": SSP_PILOT_DIM,
        "TARGET_FACT": SSP_PILOT_FACT, "DIM_PK_COLUMN": SSP_PILOT_DIM_PK,
        "FACT_PK_COLUMN": SSP_PILOT_FACT_PK, "SOURCE_SYSTEM_NAME": "ARCHER",
        "SOURCE_TABLE_NAME": SSP_PILOT_SOURCE,
        "IDENTITY_VERSION": "v1_registry_path_instance",
    }
    if config.get("EXECUTE_WRITES") is not False or any(config.get(k) != v for k, v in expected.items()):
        raise PilotError("PILOT_CONFIG_DOES_NOT_MATCH_APPROVED_SSP_DEV_SCOPE")
    if (run_result.get("writes_executed") is not False
            or run_result.get("validation_passed") is not True
            or run_result.get("pre_write_validation_passed") is not True
            or (run_result.get("nodes"), run_result.get("edges")) != SSP_PILOT_ACCEPTED_COUNTS):
        raise PilotError("ACCEPTED_SSP_DRY_RUN_OUTPUTS_REQUIRED")


def _pilot_ident(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
        raise PilotError("UNSUPPORTED_COLUMN_IDENTIFIER")
    return '"' + value + '"'


def _pilot_merge_sql(table, stage, pk, columns):
    if table not in (SSP_PILOT_DIM, SSP_PILOT_FACT):
        raise PilotError("TARGET_OUTSIDE_APPROVED_DEV_TABLES")
    names = [column["name"] for column in columns]
    if not names or len(names) != len(set(names)) or pk not in names:
        raise PilotError("INVALID_INSERT_PROJECTION")
    # Load from the frozen stage after truncation; repeat MERGE must insert zero rows.
    return (f"MERGE INTO {table} t USING {stage} s ON t.{_pilot_ident(pk)} = s.{_pilot_ident(pk)} "
            f"WHEN NOT MATCHED THEN INSERT ({', '.join(_pilot_ident(n) for n in names)}) "
            f"VALUES ({', '.join('s.' + _pilot_ident(n) for n in names)})")


_PILOT_DIM_SOURCES = {
    SSP_PILOT_DIM_PK: "NODE_KEY", "ELEMENT_TYPE": "ELEMENT_TYPE",
    "OSCAL_UUID": "OSCAL_UUID", "METADATA_JSON": "METADATA_JSON",
    "SOURCE_SYSTEM_NAME": "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME": "SOURCE_TABLE_NAME",
    "SOURCE_RECORD_ID": "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID": "DW_PIPELINE_RUN_ID",
    "DW_LOAD_TIMESTAMP": "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ": "DW_LOAD_TIMESTAMP_TZ",
}
_PILOT_FACT_SOURCES = {
    SSP_PILOT_FACT_PK: "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH": "FK_SOURCE_ELEMENT_HASH",
    "FK_TARGET_ELEMENT_HASH": "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE": "DEPENDENCY_TYPE",
    "SOURCE_OSCAL_UUID": "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID": "TARGET_OSCAL_UUID",
}
_PILOT_HASH_SOURCES = {"NODE_KEY", "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"}
_PILOT_UUID_SOURCES = {"OSCAL_UUID", "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID"}
_PILOT_HEX_PATTERN = r"[0-9a-fA-F]{32}"
_PILOT_UUID_PATTERN = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def _pilot_table(name):
    parts = name.split(".") if isinstance(name, str) else []
    if len(parts) not in (1, 3):
        raise PilotError("UNSUPPORTED_TABLE_IDENTIFIER")
    return ".".join(_pilot_ident(part.upper()) for part in parts)


def _pilot_safe_type(value):
    if not isinstance(value, str):
        raise PilotError("MISSING_LIVE_COLUMN_DATATYPE")
    value = value.strip().upper()
    match = re.fullmatch(r"(?:VARCHAR|STRING|TEXT)(?:\(\s*([1-9][0-9]*)\s*\))?", value)
    if match:
        return "VARCHAR" + ("(" + str(int(match[1])) + ")" if match[1] else "")
    if re.fullmatch(r"BINARY\(\s*16\s*\)", value):
        return "BINARY(16)"
    if value == "VARIANT" or re.fullmatch(r"TIMESTAMP_(?:NTZ|LTZ|TZ)(?:\([0-9]\))?", value):
        return value
    raise PilotError("UNSUPPORTED_LIVE_COLUMN_DATATYPE")


def _pilot_column_plan(description, kind):
    mappings = {"DIM": _PILOT_DIM_SOURCES, "FACT": _PILOT_FACT_SOURCES}
    if kind not in mappings:
        raise PilotError("INVALID_PROJECTION_KIND")
    sources = mappings[kind]
    seen, plan = set(), []
    for row in description:
        raw = row.as_dict() if hasattr(row, "as_dict") else dict(row)
        entry = {str(k).lower(): v for k, v in raw.items()}
        if not {"name", "type", "kind", "null?", "default"}.issubset(entry):
            raise PilotError("INCOMPLETE_DESC_TABLE_METADATA")
        name = entry["name"]
        _pilot_ident(name)  # Quoted lower-case/case-colliding targets are not guessed.
        if name in seen:
            raise PilotError("DUPLICATE_LIVE_COLUMN_NAMES")
        seen.add(name)
        nullable = str(entry["null?"]).strip().upper()
        column_kind = str(entry["kind"]).strip().upper()
        if nullable not in {"Y", "N"} or column_kind not in {"COLUMN", "VIRTUAL", "VIRTUAL_COLUMN"}:
            raise PilotError("UNSUPPORTED_LIVE_COLUMN_METADATA")
        if name not in sources:
            if column_kind == "COLUMN" and nullable == "N" and entry["default"] is None:
                raise PilotError("UNMAPPED_REQUIRED_INSERT_COLUMN_" + name)
            continue
        if column_kind != "COLUMN" or entry.get("expression") not in (None, ""):
            raise PilotError("MAPPED_COLUMN_NOT_WRITABLE_" + name)
        try:
            dtype = _pilot_safe_type(entry["type"])
        except PilotError as error:
            # Only column metadata, never source values or full SQL, is reported.
            raise PilotError(error.code, {"TABLE_KIND": kind, "COLUMN": name,
                             "LIVE_TYPE": str(entry["type"])[:128]}) from None
        source, encoding = sources[name], None
        expression = "s." + _pilot_ident(source)
        if source in _PILOT_HASH_SOURCES and dtype == "BINARY(16)":
            # Decode the existing MD5 hex identity; never hash again or truncate.
            expression = "TO_BINARY(" + expression + ", 'HEX')"
            encoding = "HEX_TO_BINARY16"
        elif source in _PILOT_UUID_SOURCES and dtype == "VARCHAR(32)":
            # Storage only. Canonical UUIDs inside the graph and JSON stay unchanged.
            expression = "REPLACE(" + expression + ", '-', '')"
            encoding = "UUID_TO_COMPACT32"
        elif name == "METADATA_JSON":
            if dtype == "VARIANT":
                expression = "PARSE_JSON(" + expression + ")"
            elif dtype.startswith("VARCHAR"):
                expression = "CAST(" + expression + " AS VARCHAR)"
            else:
                raise PilotError("UNSUPPORTED_PAYLOAD_DATATYPE")
        elif name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}:
            if not dtype.startswith("TIMESTAMP_"):
                raise PilotError("EXPLICIT_AUDIT_TIMESTAMP_TYPE_REQUIRED")
            expression = "CAST(" + expression + " AS " + dtype + ")"
        else:
            if not dtype.startswith("VARCHAR"):
                raise PilotError("IDENTIFIERS_AND_LABELS_REQUIRE_STRING_TYPE")
            expression = "CAST(" + expression + " AS VARCHAR)"
        plan.append({"name": name, "source": source, "expression": expression,
                     "type": dtype, "nullable": nullable == "Y", "encoding": encoding})
    required = set(sources)
    if kind == "DIM":
        # The existing loader projects these audit columns only when exposed.
        # Do not invent a requirement that an optional target column must exist.
        required -= {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}
    if required - seen:
        raise PilotError("MISSING_TARGET_COLUMNS_" + "_".join(sorted(required - seen)))
    return plan


def _pilot_difference_sql(target, stage, pk, columns):
    target_sql, stage_sql = _pilot_table(target), _pilot_table(stage)
    names = [column["name"] for column in columns]
    if not names or len(names) != len(set(names)) or pk not in names:
        raise PilotError("INVALID_COMPARISON_PROJECTION")
    qpk = _pilot_ident(pk)
    selected = ", ".join(_pilot_ident(name) for name in names)
    differences = []
    for column in columns:
        name, dtype = column["name"], _pilot_safe_type(column["type"])
        left, right = "t." + _pilot_ident(name), "s." + _pilot_ident(name)
        if name == "METADATA_JSON":
            if dtype.startswith("VARCHAR"):
                left, right = "PARSE_JSON(" + left + ")", "PARSE_JSON(" + right + ")"
            elif dtype != "VARIANT":
                raise PilotError("UNSUPPORTED_COMPARISON_PAYLOAD_DATATYPE")
            differences.extend(["NOT COALESCE(IS_OBJECT(" + left + "), FALSE)",
                                "NOT COALESCE(IS_OBJECT(" + right + "), FALSE)"])
        differences.append("(" + left + " IS DISTINCT FROM " + right + ")")
    mismatch = " OR ".join(differences)
    return f"""WITH staged AS (SELECT {selected} FROM {stage_sql}),
expected_keys AS (SELECT DISTINCT {qpk} FROM staged WHERE {qpk} IS NOT NULL),
actual AS (SELECT t.* FROM {target_sql} t WHERE EXISTS (
    SELECT 1 FROM expected_keys k WHERE k.{qpk}=t.{qpk}))
SELECT (SELECT COUNT(*) FROM staged) AS STAGED_ROWS,
    (SELECT COUNT(*) FROM actual) AS TARGET_ROWS_IN_KEY_SCOPE,
    (SELECT COUNT(*) FROM staged WHERE {qpk} IS NULL) AS STAGE_NULL_KEYS,
    (SELECT COUNT(*) FROM (SELECT {qpk} FROM staged GROUP BY {qpk} HAVING COUNT(*)>1) d) AS STAGE_DUPLICATE_KEYS,
    (SELECT COUNT(*) FROM (SELECT {qpk} FROM actual GROUP BY {qpk} HAVING COUNT(*)>1) d) AS TARGET_DUPLICATE_KEYS,
    (SELECT COUNT(*) FROM expected_keys s WHERE NOT EXISTS (
        SELECT 1 FROM actual t WHERE t.{qpk}=s.{qpk})) AS MISSING_KEYS,
    (SELECT COUNT(*) FROM (SELECT DISTINCT s.{qpk} FROM staged s
        JOIN actual t ON t.{qpk}=s.{qpk} WHERE {mismatch}) d) AS MISMATCHED_KEYS"""


def _pilot_count(session, sql):
    return int(_pilot_query(session, sql)[0]["N"])


def _pilot_zero(session, sql, code):
    if _pilot_count(session, sql):
        raise PilotError(code)


def _pilot_unique(session, table, key):
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM (SELECT {key} FROM {table} "
                f"GROUP BY {key} HAVING {key} IS NULL OR COUNT(*) > 1)",
                "NULL_OR_DUPLICATE_KEYS")


def _pilot_selection_schema(plans):
    """Selection compares identities using the posted physical BINARY(16) schema."""
    required = ((SSP_PILOT_DIM_PK,),
                (SSP_PILOT_FACT_PK, "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"))
    for plan, keys in zip(plans, required):
        types = {c["name"]: c["type"] for c in plan}
        if any(types.get(key) != "BINARY(16)" for key in keys):
            raise PilotError("NEW_RECORD_SELECTION_REQUIRES_CONFIRMED_BINARY16_KEYS")


def _pilot_stage(session, raw_stage, stage, plan):
    # Validate identity syntax before evaluating conversions; NULL is not an identity.
    for column in plan:
        encoding = column.get("encoding")
        if encoding:
            source = _pilot_ident(column["source"])
            pattern = _PILOT_HEX_PATTERN if encoding == "HEX_TO_BINARY16" else _PILOT_UUID_PATTERN
            _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {raw_stage} WHERE "
                        f"{source} IS NULL OR NOT REGEXP_LIKE({source}, '{pattern}')",
                        "INVALID_STORAGE_IDENTITY_" + column["name"])
    expressions = ", ".join(c["expression"] + " AS " + _pilot_ident(c["name"]) for c in plan)
    _pilot_query(session, f"CREATE TEMPORARY TABLE {stage} AS SELECT {expressions} FROM {raw_stage} s")
    for column in plan:
        name = _pilot_ident(column["name"])
        if column["type"] == "BINARY(16)":
            _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE "
                        f"{name} IS NULL OR OCTET_LENGTH({name}) <> 16", "BINARY_KEY_WIDTH_INVALID")
        if column["name"] in {SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK}:
            # Different text casing can collapse to the same physical binary key.
            _pilot_unique(session, stage, name)
        if not column["nullable"]:
            _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE {name} IS NULL",
                        "REQUIRED_TARGET_VALUE_IS_NULL")
        width = re.fullmatch(r"VARCHAR\((\d+)\)", column["type"])
        if width:
            _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {stage} WHERE LENGTH({name}) > {int(width[1])}",
                        "TARGET_STRING_CAPACITY_EXCEEDED")


def _pilot_check_existing_scope(session, names, queries):
    """Post-load check: every saved row must belong to the complete frozen graph."""
    for kind, pk, query in zip(("D", "F"), (SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK), queries):
        stage = names[kind]
        _pilot_unique(session, f"({query})", pk)
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) t LEFT JOIN {stage} s "
                    f"ON t.{pk}=s.{pk} WHERE s.{pk} IS NULL", "EXTRA_TARGET_ROWS_REQUIRE_REVIEW")
        ownership = ("SOURCE_RECORD_ID", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME") if kind == "D" else (
            "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE")
        conditions = " OR ".join(f"NOT EQUAL_NULL(t.{c}, s.{c})" for c in ownership)
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM ({query}) t JOIN {stage} s "
                    f"ON t.{pk}=s.{pk} WHERE {conditions}", "TARGET_KEY_OWNERSHIP_CONFLICT")


def _pilot_baseline_equal(session, names, queries):
    # Multiset comparison: keep duplicate multiplicities in the OLD full tables.
    # GROUP BY ALL includes every existing target column, including VARIANT payloads.
    for baseline, query in zip((names["DB"], names["FB"]), queries):
        current = f"SELECT *, COUNT(*) AS SSP_RELOAD_ROW_MULTIPLICITY FROM ({query}) GROUP BY ALL"
        frozen = f"SELECT *, COUNT(*) AS SSP_RELOAD_ROW_MULTIPLICITY FROM {baseline} GROUP BY ALL"
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM (({current}) MINUS ({frozen}))",
                    "TARGET_BASELINE_CHANGED")
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM (({frozen}) MINUS ({current}))",
                    "TARGET_BASELINE_CHANGED")
        if _pilot_count(session, f"SELECT COUNT(*) AS N FROM ({query})") != _pilot_count(
                session, f"SELECT COUNT(*) AS N FROM {baseline}"):
            raise PilotError("TARGET_BASELINE_CHANGED")


def _pilot_verify(session, names, queries, plans, require_match=True):
    _pilot_check_existing_scope(session, names, queries)
    reports = {}
    for kind, target, pk, plan in zip(("D", "F"), (SSP_PILOT_DIM, SSP_PILOT_FACT),
                                    (SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK), plans):
        row = _pilot_query(session, _pilot_difference_sql(target, names[kind], pk, plan))[0]
        report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
        if require_match and (report["STAGED_ROWS"] != report["TARGET_ROWS_IN_KEY_SCOPE"]
                or any(value for key, value in report.items()
                       if key not in ("STAGED_ROWS", "TARGET_ROWS_IN_KEY_SCOPE"))):
            raise PilotError("SAVED_VALUES_OR_KEYS_DIFFER_FROM_FROZEN_BATCH")
        reports["DIM" if kind == "D" else "FACT"] = report
    return reports


def _reconcile_dml_count(rows, label, expected, code):
    if len(rows) != 1:
        raise PilotError("DML_ROW_COUNT_UNAVAILABLE")
    row = rows[0].as_dict() if hasattr(rows[0], "as_dict") else dict(rows[0])
    value = {str(k).lower(): v for k, v in row.items()}.get(label)
    if not re.fullmatch(r"[0-9]+", str(value)):
        raise PilotError("DML_ROW_COUNT_UNAVAILABLE")
    actual = int(value)
    if actual != expected:
        raise PilotError(code, {"EXPECTED_ROWS": expected, "ACTUAL_ROWS": actual})
    return actual

def _batch_integrity_sql(queries, ids, allow_absent=False):
    if type(allow_absent) is not bool:
        raise PilotError("INVALID_OLD_GRAPH_POLICY")
    dim, fact = queries
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
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
 (SELECT COUNT(*) FROM checked_nodes d WHERE d.OSCAL_UUID IS NULL OR
     NOT EQUAL_NULL(d.SOURCE_SYSTEM_NAME,'ARCHER') OR
     NOT EQUAL_NULL(d.SOURCE_TABLE_NAME,'{SSP_PILOT_SOURCE}') OR
     NOT EXISTS (SELECT 1 FROM {ids} i WHERE i.SOURCE_RECORD_ID=d.SOURCE_RECORD_ID)) AS INVALID_NODE_OWNERSHIP_OR_UUID,
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


def _batch_integrity(session, queries, ids, expected_records, allow_absent=False):
    row = _pilot_query(session, _batch_integrity_sql(queries, ids, allow_absent))[0]
    report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
    metrics = ("SELECTED_RECORDS", "NODES", "EDGES")
    if report.get("SELECTED_RECORDS") != expected_records or any(v != 0 for k, v in report.items() if k not in metrics):
        raise PilotError("BATCH_PRIMARY_FOREIGN_KEY_OR_HIERARCHY_FAILED", {"KEY_CHECKS": report})
    # Cardinality is checked first; disconnected cycles must still fail reachability.
    dim, fact = queries
    dk = SSP_PILOT_DIM_PK
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
    _pilot_zero(session, sql, "BATCH_DISCONNECTED_RECORD_TREE")
    report["DISCONNECTED_RECORDS"] = 0
    return report


def _reload_freeze(session, nodes, edges, names):
    # Do not filter the graph: all nodes/edges, including previously accepted eleven.
    for frame, key in ((nodes, "NV"), (edges, "EV")):
        frame.write.save_as_table(names[key], mode="errorifexists", table_type="temporary")
    counts = tuple(_pilot_count(session, f"SELECT COUNT(*) AS N FROM {names[k]}") for k in ("NV", "EV"))
    if counts != SSP_PILOT_ACCEPTED_COUNTS:
        raise PilotError("ACCEPTED_GRAPH_COUNTS_CHANGED")
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {names['NV']} WHERE "
                "ELEMENT_PATH IS NULL OR (ELEMENT_PATH <> 'system-security-plan' AND "
                "ELEMENT_PATH NOT LIKE 'system-security-plan.%') OR "
                "COALESCE(TYPEOF(TRY_PARSE_JSON(METADATA_JSON)), '') <> 'OBJECT'",
                "INVALID_SSP_CANDIDATE_PATH_OR_PAYLOAD")
    roots = f"SELECT SOURCE_RECORD_ID FROM {names['NV']} WHERE ELEMENT_PATH='system-security-plan'"
    _pilot_unique(session, f"({roots})", "SOURCE_RECORD_ID")
    _pilot_query(session, f"CREATE TEMPORARY TABLE {names['IDS']} AS {roots}")
    selected = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {names['IDS']}")
    if selected != SSP_RELOAD_SOURCE_RECORDS:
        raise PilotError("FULL_RELOAD_SOURCE_RECORD_COUNT_CHANGED",
                         {"EXPECTED": SSP_RELOAD_SOURCE_RECORDS, "ACTUAL": selected})
    return selected


def _reload_transaction(session, merges, before_replace, verify, new_counts):
    if (not isinstance(merges, (list, tuple)) or len(merges) != 2
            or not isinstance(new_counts, (list, tuple))
            or tuple(new_counts) != SSP_PILOT_ACCEPTED_COUNTS
            or any(type(v) is not int for v in new_counts)
            or not callable(before_replace) or not callable(verify)):
        raise PilotError("INVALID_FULL_RELOAD_TRANSACTION_ARGUMENTS")
    for statement, target in zip(merges, (SSP_PILOT_DIM, SSP_PILOT_FACT)):
        if (not isinstance(statement, str) or ";" in statement
                or not statement.startswith("MERGE INTO " + target + " t USING ")
                or "WHEN MATCHED" in statement.upper()):
            raise PilotError("RELOAD_MERGE_OUTSIDE_APPROVED_TARGET_OR_INSERT_POLICY")
    _pilot_no_transaction(session)
    try:
        _pilot_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise PilotError("BEGIN_OUTCOME_UNKNOWN") from None
    step, pass_number, inserts, checks = "BASELINE_BEFORE_TRUNCATE", 0, [], []
    try:
        before_replace()
        for kind, target in (("FACT", SSP_PILOT_FACT), ("DIM", SSP_PILOT_DIM)):
            step = "TRUNCATE_" + kind
            # Fixed exact DEV targets only. TRUNCATE is transactional DML in Snowflake.
            # Its result is a status, not the DELETE/MERGE affected-row result shape.
            _pilot_query(session, "TRUNCATE TABLE " + target)
            _pilot_zero(session, "SELECT COUNT(*) AS N FROM " + target,
                        "TRUNCATE_DID_NOT_EMPTY_" + kind)
        for pass_number in (1, 2):
            inserted = []
            for index, (step, statement) in enumerate(zip(("DIM_MERGE", "FACT_MERGE"), merges)):
                inserted.append(_reconcile_dml_count(_pilot_query(session, statement),
                                "number of rows inserted", new_counts[index] if pass_number == 1 else 0,
                                "UNEXPECTED_MERGE_INSERT_COUNT"))
            inserts.append({"PASS": pass_number, "DIM": inserted[0], "FACT": inserted[1]})
            step = "READBACK_AND_KEY_INTEGRITY"
            checks.append(verify(pass_number))
    except BaseException as error:
        details = dict(_pilot_error_details(error), STEP=step, PASS=pass_number)
        try:
            _pilot_query(session, "ROLLBACK")
        except BaseException:
            raise PilotError("ROLLBACK_OUTCOME_UNKNOWN", details) from None
        raise PilotError("TRANSACTION_ROLLED_BACK", details) from None
    try:
        _pilot_query(session, "COMMIT")
    except BaseException:
        raise PilotError("COMMIT_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED", "TRUNCATED_TARGETS": ["FACT", "DIM"],
            "INSERT_COUNTS": inserts, "VERIFIED_PASSES": len(checks), "CHECKS": checks}


def run_ssp_full_dev_reload(session, config, run_result, nodes, edges, mode="PREVIEW"):
    report = {"RELEASE": SSP_RELOAD_RELEASE, "MODEL": "SSP", "MODE": mode,
              "WRITE_POLICY": "FULL_TABLE_TRUNCATE_AND_RELOAD",
              "BACKUP_POLICY": "TRANSACTION_ONLY_DEV",
              "RECOVERY_LIMITATION": "NO_DURABLE_COPY_AFTER_COMMIT",
              "LOAD_METADATA_POLICY": "TRUNCATE_CLEARS_LOAD_METADATA",
              "PERSISTED": False, "TARGET_DML_ATTEMPTED": False}
    phase, snapshots_ready = "CONFIG", False
    try:
        _pilot_contract(config, run_result)
        if mode not in ("PREVIEW", "COMMIT"):
            raise PilotError("FULL_RELOAD_MODE_INVALID")
        _pilot_no_transaction(session)
        prefix = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.TMP_SSP_RELOAD_" + uuid.uuid4().hex.upper()
        names = {k: prefix + "_" + k for k in ("NV", "EV", "IDS", "D", "F", "DB", "FB")}
        phase = "SCHEMA_AND_STAGING"
        plans = [_pilot_column_plan(_pilot_query(session, "DESC TABLE " + target), kind)
                 for target, kind in ((SSP_PILOT_DIM, "DIM"), (SSP_PILOT_FACT, "FACT"))]
        _pilot_selection_schema(plans)
        selected = _reload_freeze(session, nodes, edges, names)
        report["SOURCE_RECORDS"] = selected
        for raw, physical, plan in zip(("NV", "EV"), ("D", "F"), plans):
            _pilot_stage(session, names[raw], names[physical], plan)
        candidate_queries = (f"SELECT * FROM {names['D']}", f"SELECT * FROM {names['F']}")
        candidate = _batch_integrity(session, candidate_queries, names["IDS"], selected)
        new_counts = (int(candidate["NODES"]), int(candidate["EDGES"]))
        if new_counts != SSP_PILOT_ACCEPTED_COUNTS:
            raise PilotError("STAGED_PHYSICAL_GRAPH_COUNTS_CHANGED")
        report["CANDIDATE_KEY_INTEGRITY"] = candidate
        report["NEW_DIM_ROWS"], report["NEW_FACT_ROWS"] = new_counts

        # Snapshots and other DDL occur BEFORE the explicit transaction.
        # Session-only snapshots support exact rollback verification, not durable backup.
        phase = "TEMPORARY_BASELINE"
        queries = (f"SELECT * FROM {SSP_PILOT_DIM}", f"SELECT * FROM {SSP_PILOT_FACT}")
        for key, query in zip(("DB", "FB"), queries):
            _pilot_query(session, f"CREATE TEMPORARY TABLE {names[key]} AS {query}")
        old_counts = tuple(_pilot_count(session, f"SELECT COUNT(*) AS N FROM {names[k]}") for k in ("DB", "FB"))
        report["OLD_DIM_ROWS"], report["OLD_FACT_ROWS"] = old_counts

        def baseline():
            _pilot_baseline_equal(session, names, queries)

        baseline()
        snapshots_ready = True
        if mode == "PREVIEW":
            report["STATUS"] = "FULL_RELOAD_PREVIEW_PASSED_NO_TARGET_DML"
            return report
        merges = [_pilot_merge_sql(t, names[k], pk, plan) for t, k, pk, plan in
                  zip((SSP_PILOT_DIM, SSP_PILOT_FACT), ("D", "F"),
                      (SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK), plans)]

        def before_replace():
            baseline()
            report["TARGET_DML_ATTEMPTED"] = True

        def verify(pass_number):
            return {"SAVED_VALUES": _pilot_verify(session, names, queries, plans),
                    "KEY_INTEGRITY": _batch_integrity(session, queries, names["IDS"], selected)}

        # One full reload transaction, not a hundred-record loop or another pilot.
        phase = "TRUNCATE_LOAD_AND_COMMIT"
        report["COMMIT"] = _reload_transaction(session, merges, before_replace, verify, new_counts)
        report["PERSISTED"] = True
        phase = "POST_COMMIT_READBACK"
        report["READBACK"] = verify(3)
        report["STATUS"] = "FULL_SSP_RELOAD_COMMITTED_AND_VERIFIED"
        return report
    except BaseException as error:
        code = error.code if isinstance(error, PilotError) else "FULL_RELOAD_OPERATION_FAILED"
        report.update(STATUS=code, PHASE=phase, ERROR_DETAILS=_pilot_error_details(error))
        if code in ("BEGIN_OUTCOME_UNKNOWN", "COMMIT_OUTCOME_UNKNOWN", "ROLLBACK_OUTCOME_UNKNOWN"):
            report["PERSISTED"] = "UNKNOWN_DO_NOT_RETRY"
        elif code == "TRANSACTION_ROLLED_BACK" and snapshots_ready:
            try:
                baseline()
                report["FAILURE_ROLLBACK_RESTORED_BASELINE"] = True
            except BaseException as check_error:
                report["STATUS"] = "ROLLBACK_READBACK_FAILED_DO_NOT_RETRY"
                report["ROLLBACK_CHECK_ERROR"] = _pilot_error_details(check_error)
                report["PERSISTED"] = "UNKNOWN_DO_NOT_RETRY"
        # Never retry an uncertain COMMIT or restore old data automatically afterward.
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        raise PilotError(report["STATUS"]) from None


if __name__ == "__main__":
    ssp_reload_report = None
    required = ("session", "CONFIG", "run_result", "final_nodes_df", "final_edges_df")
    if any(k not in globals() for k in required):
        raise PilotError("ACCEPTED_SSP_SESSION_OUTPUTS_REQUIRED")
    ssp_reload_report = run_ssp_full_dev_reload(
        session, CONFIG, run_result, final_nodes_df, final_edges_df, SSP_RELOAD_MODE)
    print(json.dumps(ssp_reload_report, indent=2, sort_keys=True, default=str))
