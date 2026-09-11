# Reconcile only the reviewed lowest-root SSP DEV record. Normal writes stay False.
# PREVIEW creates temporary snapshots; COMMIT replaces only the reviewed DEV graph.
# Requires the accepted SSP Cell 7 outputs in the same session; AR is not used.
import json
import re
import uuid


SSP_RECONCILE_RELEASE = "ssp-one-record-reconcile-v2-dev-no-backup"
SSP_RECONCILE_MODE = "PREVIEW"  # Set to COMMIT only for the approved one-record replacement.
SSP_RECONCILE_BACKUP_POLICY = "TRANSACTION_ONLY_DEV"  # Owner approved: no permanent recovery copy.
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
    # New-record authorization only: no statement can update or delete an old row.
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


def _pilot_freeze_graph(session, nodes, edges, names):
    """All Snowpark materialization and temporary DDL precedes any transaction."""
    # A cross-schema view rebinds unqualified Snowpark backing-table references
    # in the view's schema. Materialize each frame in its existing session instead.
    # Random pilot names + errorifexists avoid replacing any existing object.
    for frame, suffix, step in ((nodes, "NV", "MATERIALIZE_GRAPH_NODES"),
                                 (edges, "EV", "MATERIALIZE_GRAPH_EDGES")):
        try:
            frame.write.save_as_table(names[suffix], mode="errorifexists", table_type="temporary")
        except BaseException as error:
            raise PilotError("GRAPH_TEMP_MATERIALIZATION_FAILED",
                             dict(_pilot_error_details(error), STEP=step)) from None
    nv, ev, nr, er = (names[k] for k in ("NV", "EV", "NR", "ER"))
    if (_pilot_count(session, f"SELECT COUNT(*) AS N FROM {nv}"),
            _pilot_count(session, f"SELECT COUNT(*) AS N FROM {ev}")) != SSP_PILOT_ACCEPTED_COUNTS:
        raise PilotError("GRAPH_COUNTS_CHANGED_SINCE_ACCEPTED_RUN")
    # Validate snapshot identities before selection evaluates binary conversions.
    for table, columns in ((nv, ("NODE_KEY",)),
                           (ev, ("EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH"))):
        invalid = " OR ".join(f"{c} IS NULL OR NOT REGEXP_LIKE({c}, '{_PILOT_HEX_PATTERN}')"
                              for c in columns)
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {table} WHERE {invalid}",
                    "INVALID_GRAPH_IDENTITY_BEFORE_SELECTION")
    _pilot_query(session, f"CREATE TEMPORARY TABLE {nr} AS SELECT * FROM {nv} "
                 f"WHERE SOURCE_RECORD_ID=(SELECT MIN(SOURCE_RECORD_ID) FROM {nv} "
                 "WHERE ELEMENT_PATH='system-security-plan')")
    n = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {nr}")
    if n == 0:
        raise PilotError("REVIEWED_LOWEST_ROOT_RECORD_NOT_AVAILABLE")
    _pilot_query(session, f"CREATE TEMPORARY TABLE {er} AS SELECT * FROM {ev} "
                 f"WHERE FK_SOURCE_ELEMENT_HASH IN (SELECT NODE_KEY FROM {nr}) "
                 f"OR FK_TARGET_ELEMENT_HASH IN (SELECT NODE_KEY FROM {nr})")
    e = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {er}")
    roots = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {nr} "
                         "WHERE ELEMENT_PATH = 'system-security-plan'")
    if (n, e, roots) != (19, 18, 1):
        raise PilotError("REVIEWED_CANDIDATE_SHAPE_CHANGED")
    _pilot_unique(session, nr, "NODE_KEY")
    _pilot_unique(session, er, "EDGE_KEY")
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {nr} WHERE "
                "SOURCE_RECORD_ID IS NULL OR OSCAL_UUID IS NULL OR ELEMENT_PATH IS NULL OR "
                "NOT EQUAL_NULL(SOURCE_SYSTEM_NAME, 'ARCHER') OR "
                f"NOT EQUAL_NULL(SOURCE_TABLE_NAME, '{SSP_PILOT_SOURCE}') OR "
                "(ELEMENT_PATH <> 'system-security-plan' AND "
                "ELEMENT_PATH NOT LIKE 'system-security-plan.%') OR "
                "COALESCE(TYPEOF(TRY_PARSE_JSON(METADATA_JSON)), '') <> 'OBJECT'",
                "SOURCE_SCOPE_OR_PAYLOAD_INVALID")
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {er} e LEFT JOIN {nr} s "
                "ON s.NODE_KEY=e.FK_SOURCE_ELEMENT_HASH "
                f"LEFT JOIN {nr} t ON t.NODE_KEY=e.FK_TARGET_ELEMENT_HASH WHERE "
                "s.NODE_KEY IS NULL OR t.NODE_KEY IS NULL OR "
                "NOT EQUAL_NULL(e.DEPENDENCY_TYPE, 'CONTAINS') OR "
                "NOT EQUAL_NULL(e.SOURCE_OSCAL_UUID, s.OSCAL_UUID) OR "
                "NOT EQUAL_NULL(e.TARGET_OSCAL_UUID, t.OSCAL_UUID)",
                "CROSS_BOUNDARY_OR_INVALID_SOURCE_EDGES")
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM (SELECT n.NODE_KEY,n.ELEMENT_PATH,"
                f"COUNT(e.EDGE_KEY) AS PARENTS FROM {nr} n LEFT JOIN {er} e "
                "ON n.NODE_KEY=e.FK_TARGET_ELEMENT_HASH GROUP BY n.NODE_KEY,n.ELEMENT_PATH "
                "HAVING PARENTS <> IFF(n.ELEMENT_PATH='system-security-plan',0,1))",
                "INVALID_PARENT_CARDINALITY")
    reachable = _pilot_count(session, f"WITH RECURSIVE tree (K,DEPTH) AS ("
                            f"SELECT NODE_KEY,0 FROM {nr} WHERE ELEMENT_PATH='system-security-plan' "
                            f"UNION ALL SELECT e.FK_TARGET_ELEMENT_HASH,t.DEPTH+1 FROM tree t "
                            f"JOIN {er} e ON e.FK_SOURCE_ELEMENT_HASH=t.K WHERE t.DEPTH < {n}) "
                            "SELECT COUNT(DISTINCT K) AS N FROM tree")
    if reachable != n:
        raise PilotError("DISCONNECTED_SOURCE_TREE")
    return {"SOURCE_RECORDS": 1, "NODES": n, "EDGES": e}


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


def _pilot_scope_queries(names):
    d, f, nr = names["D"], names["F"], names["NR"]
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
    dim = (f"SELECT t.* FROM {SSP_PILOT_DIM} t WHERE t.{dk} IN (SELECT {dk} FROM {d}) OR "
           f"(t.SOURCE_SYSTEM_NAME='ARCHER' AND t.SOURCE_TABLE_NAME='{SSP_PILOT_SOURCE}' "
           f"AND t.SOURCE_RECORD_ID=(SELECT MIN(SOURCE_RECORD_ID) FROM {nr}))")
    fact = (f"SELECT t.* FROM {SSP_PILOT_FACT} t WHERE t.{fk} IN (SELECT {fk} FROM {f}) OR "
            f"t.FK_SOURCE_ELEMENT_HASH IN (SELECT {dk} FROM ({dim})) OR "
            f"t.FK_TARGET_ELEMENT_HASH IN (SELECT {dk} FROM ({dim})) OR "
            f"t.FK_SOURCE_ELEMENT_HASH IN (SELECT {dk} FROM {d}) OR "
            f"t.FK_TARGET_ELEMENT_HASH IN (SELECT {dk} FROM {d})")
    return dim, fact


def _pilot_check_existing_scope(session, names, queries):
    """No deletion or reassignment of another record's keys is authorized."""
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
    for baseline, query in zip((names["DB"], names["FB"]), queries):
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM (({query}) MINUS (SELECT * FROM {baseline}))",
                    "TARGET_BASELINE_CHANGED")
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM ((SELECT * FROM {baseline}) MINUS ({query}))",
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



def _reconcile_live_scope_queries(names):
    """Retain old-key incident scope even after old DIM rows have been deleted."""
    dim, fact = _pilot_scope_queries(names)
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
    db, fb = names["DB"], names["FB"]
    return (
        f"SELECT t.* FROM {SSP_PILOT_DIM} t WHERE t.{dk} IN (SELECT {dk} FROM ({dim})) "
        f"OR t.{dk} IN (SELECT {dk} FROM {db})",
        f"SELECT t.* FROM {SSP_PILOT_FACT} t WHERE t.{fk} IN (SELECT {fk} FROM ({fact})) "
        f"OR t.{fk} IN (SELECT {fk} FROM {fb}) "
        f"OR t.FK_SOURCE_ELEMENT_HASH IN (SELECT {dk} FROM {db}) "
        f"OR t.FK_TARGET_ELEMENT_HASH IN (SELECT {dk} FROM {db})")


def _reconcile_integrity_sql(dim, fact, relationship):
    if relationship not in ("parent_of", "CONTAINS"):
        raise PilotError("UNAPPROVED_RELATIONSHIP_CHECK")
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
    return f"""WITH checked_nodes AS ({dim}), checked_edges AS ({fact})
SELECT
 (SELECT COUNT(*) FROM checked_nodes d WHERE {dk} IS NULL) AS DIM_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {dk} FROM checked_nodes d GROUP BY {dk} HAVING COUNT(*)>1)) AS DIM_DUPLICATE_KEY_GROUPS,
 (SELECT COUNT(*) FROM checked_edges f WHERE {fk} IS NULL) AS FACT_NULL_KEYS,
 (SELECT COUNT(*) FROM (SELECT {fk} FROM checked_edges f GROUP BY {fk} HAVING COUNT(*)>1)) AS FACT_DUPLICATE_KEY_GROUPS,
 (SELECT COUNT(*) FROM checked_edges f WHERE FK_SOURCE_ELEMENT_HASH IS NULL OR FK_TARGET_ELEMENT_HASH IS NULL) AS NULL_FOREIGN_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_SOURCE_ELEMENT_HASH)) AS DANGLING_SOURCE_KEYS,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EXISTS (SELECT 1 FROM checked_nodes d WHERE d.{dk}=f.FK_TARGET_ELEMENT_HASH)) AS DANGLING_TARGET_KEYS,
 (SELECT COUNT(*) FROM checked_edges f JOIN checked_nodes s ON s.{dk}=f.FK_SOURCE_ELEMENT_HASH
    JOIN checked_nodes t ON t.{dk}=f.FK_TARGET_ELEMENT_HASH
    WHERE NOT EQUAL_NULL(f.SOURCE_OSCAL_UUID,s.OSCAL_UUID)
       OR NOT EQUAL_NULL(f.TARGET_OSCAL_UUID,t.OSCAL_UUID)) AS UUID_LINK_MISMATCHES,
 (SELECT COUNT(*) FROM checked_edges f WHERE NOT EQUAL_NULL(DEPENDENCY_TYPE,'{relationship}')) AS WRONG_RELATIONSHIP_TYPE,
 (SELECT COUNT(*) FROM (SELECT d.{dk}, d.ELEMENT_TYPE, COUNT(f.{fk}) AS PARENTS
    FROM checked_nodes d LEFT JOIN checked_edges f ON d.{dk}=f.FK_TARGET_ELEMENT_HASH
    GROUP BY d.{dk},d.ELEMENT_TYPE
    HAVING COUNT(f.{fk}) <> CASE WHEN d.ELEMENT_TYPE='system-security-plan' THEN 0 ELSE 1 END)) AS WRONG_PARENT_COUNTS,
 (SELECT COUNT(*) FROM checked_nodes d WHERE ELEMENT_TYPE='system-security-plan') AS ROOTS"""


def _reconcile_integrity(session, queries, relationship):
    row = _pilot_query(session, _reconcile_integrity_sql(*queries, relationship))[0]
    report = dict(row.as_dict()) if hasattr(row, "as_dict") else dict(row)
    if report.get("ROOTS") != 1 or any(v != 0 for k, v in report.items() if k != "ROOTS"):
        raise PilotError("PRIMARY_FOREIGN_KEY_OR_HIERARCHY_CHECK_FAILED", {"KEY_CHECKS": report})
    return report


def _reconcile_validate_baseline(session, names, queries):
    db, fb, d, f = (names[k] for k in ("DB", "FB", "D", "F"))
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
    counts = tuple(_pilot_count(session, f"SELECT COUNT(*) AS N FROM {t}") for t in (db, fb, d, f))
    if counts != (21, 20, 19, 18):
        raise PilotError("REVIEWED_OLD_OR_NEW_GRAPH_COUNTS_CHANGED")
    _pilot_unique(session, db, dk)
    _pilot_unique(session, fb, fk)
    _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {db} WHERE "
                "NOT EQUAL_NULL(SOURCE_SYSTEM_NAME,'ARCHER') OR "
                f"NOT EQUAL_NULL(SOURCE_TABLE_NAME,'{SSP_PILOT_SOURCE}') OR "
                f"NOT EQUAL_NULL(SOURCE_RECORD_ID,(SELECT MIN(SOURCE_RECORD_ID) FROM {names['NR']}))",
                "OLD_SCOPE_CONTAINS_ANOTHER_RECORD")
    for baseline, stage, pk in ((db, d, dk), (fb, f, fk)):
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM {baseline} b JOIN {stage} s ON b.{pk}=s.{pk}",
                    "REVIEWED_ZERO_KEY_OVERLAP_CHANGED")
    old_queries = (f"SELECT * FROM {db}", f"SELECT * FROM {fb}")
    integrity = _reconcile_integrity(session, old_queries, "parent_of")
    # Closed old graph: joins above reject either endpoint outside this owned set.
    reachable = _pilot_count(session, f"WITH RECURSIVE tree(K,DEPTH) AS ("
                f"SELECT {dk},0 FROM {db} WHERE ELEMENT_TYPE='system-security-plan' "
                f"UNION ALL SELECT f.FK_TARGET_ELEMENT_HASH,t.DEPTH+1 FROM tree t "
                f"JOIN {fb} f ON f.FK_SOURCE_ELEMENT_HASH=t.K WHERE t.DEPTH<21) "
                "SELECT COUNT(DISTINCT K) AS N FROM tree")
    if reachable != 21:
        raise PilotError("OLD_GRAPH_IS_NOT_ONE_CONNECTED_TREE")
    _pilot_baseline_equal(session, names, queries)
    return {"OLD_DIM_ROWS": 21, "OLD_FACT_ROWS": 20, "NEW_DIM_ROWS": 19,
            "NEW_FACT_ROWS": 18, "OLD_KEY_INTEGRITY": integrity}


def _reconcile_delete_sql(names):
    # No broad source filter: deletion is constrained to the exact frozen keys.
    return [
        f"DELETE FROM {SSP_PILOT_FACT} WHERE {SSP_PILOT_FACT_PK} IN "
        f"(SELECT {_pilot_ident(SSP_PILOT_FACT_PK)} FROM {_pilot_table(names['FB'])})",
        f"DELETE FROM {SSP_PILOT_DIM} WHERE {SSP_PILOT_DIM_PK} IN "
        f"(SELECT {_pilot_ident(SSP_PILOT_DIM_PK)} FROM {_pilot_table(names['DB'])})"]


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


def _reconcile_transaction(session, deletes, merges, before_replace, verify,
                           expected_inserts, commit=False):
    if type(commit) is not bool or len(deletes) != 2 or len(merges) != 2:
        raise PilotError("INVALID_TRANSACTION_ARGUMENTS")
    if tuple(expected_inserts) != (19, 18) or not callable(before_replace) or not callable(verify):
        raise PilotError("INVALID_TRANSACTION_ARGUMENTS")
    if any(";" in s or not s.lstrip().upper().startswith("DELETE FROM ") or " WHERE " not in s.upper()
           for s in deletes) or any(";" in s or not s.lstrip().upper().startswith("MERGE INTO ") for s in merges):
        raise PilotError("INVALID_TRANSACTION_STATEMENT")
    _pilot_no_transaction(session)
    try:
        _pilot_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise PilotError("BEGIN_OUTCOME_UNKNOWN") from None
    step, pass_number = "BASELINE_BEFORE_REPLACE", 0
    deleted, inserts, checks = [], [], []
    try:
        before_replace()
        for step, statement, expected in zip(("DELETE_OLD_FACT", "DELETE_OLD_DIM"), deletes, (20, 21)):
            deleted.append(_reconcile_dml_count(_pilot_query(session, statement),
                           "number of rows deleted", expected, "UNEXPECTED_DELETE_COUNT"))
        for pass_number in (1, 2):
            inserted = []
            for index, (step, statement) in enumerate(zip(("DIM_MERGE", "FACT_MERGE"), merges)):
                expected = expected_inserts[index] if pass_number == 1 else 0
                inserted.append(_reconcile_dml_count(_pilot_query(session, statement),
                                "number of rows inserted", expected, "UNEXPECTED_MERGE_INSERT_COUNT"))
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
        _pilot_query(session, "COMMIT" if commit else "ROLLBACK")
    except BaseException:
        raise PilotError("COMMIT_OUTCOME_UNKNOWN" if commit else "ROLLBACK_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED" if commit else "ROLLED_BACK",
            "DELETED_FACT_ROWS": deleted[0], "DELETED_DIM_ROWS": deleted[1],
            "INSERT_COUNTS": inserts, "VERIFIED_PASSES": len(checks), "CHECKS": checks}


def _reconcile_create_backups(session, names, backup_names):
    # Durable tables, not temporary/transient, so closing the notebook retains recovery data.
    # No OR REPLACE. Any backup/verification failure occurs before target DML.
    for kind, old in (("DIM", "DB"), ("FACT", "FB")):
        _pilot_query(session, f"CREATE TABLE {_pilot_table(backup_names[kind])} AS SELECT * FROM {names[old]}")
    backup_queries = tuple("SELECT * FROM " + _pilot_table(backup_names[k]) for k in ("DIM", "FACT"))
    _pilot_baseline_equal(session, names, backup_queries)
    return backup_queries


def run_ssp_one_record_reconciliation(session, config, run_result, nodes, edges, mode="PREVIEW",
                                      backup_policy="DURABLE"):
    _pilot_contract(config, run_result)
    if mode not in ("PREVIEW", "COMMIT"):
        raise PilotError("PILOT_MODE_MUST_BE_PREVIEW_OR_COMMIT")
    if backup_policy not in ("DURABLE", "TRANSACTION_ONLY_DEV"):
        raise PilotError("UNAPPROVED_BACKUP_POLICY")
    _pilot_no_transaction(session)
    token = uuid.uuid4().hex.upper()
    schema = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED."
    prefix = schema + "TMP_SSP_RECONCILE_" + token
    names = {s: prefix + "_" + s for s in ("NV", "EV", "NR", "ER", "D", "F", "DB", "FB")}
    report = {"RELEASE": SSP_RECONCILE_RELEASE, "MODEL": "SSP", "MODE": mode,
              "SELECTION": "PREVIOUSLY_REVIEWED_LOWEST_ROOT",
              "WRITE_POLICY": "BACKUP_AND_REPLACE_ONE_REVIEWED_RECORD",
              "BACKUP_POLICY": backup_policy, "BACKUP_TABLES": {}, "BACKUPS_VERIFIED": False,
              "STATUS": "PREPARING", "TARGET_DML_ATTEMPTED": False, "PERSISTED": False}
    if backup_policy == "TRANSACTION_ONLY_DEV":
        report["WRITE_POLICY"] = "REPLACE_ONE_REVIEWED_DEV_RECORD_WITHOUT_DURABLE_BACKUP"
        report["RECOVERY_LIMITATION"] = "NO_DURABLE_COPY_AFTER_COMMIT"
    phase = "SCHEMA_AND_STAGING"
    try:
        plans = [_pilot_column_plan(_pilot_query(session, "DESC TABLE " + target), kind)
                 for target, kind in ((SSP_PILOT_DIM, "DIM"), (SSP_PILOT_FACT, "FACT"))]
        _pilot_selection_schema(plans)
        report.update(_pilot_freeze_graph(session, nodes, edges, names))
        for raw, stage, plan in zip(("NR", "ER"), ("D", "F"), plans):
            _pilot_stage(session, names[raw], names[stage], plan)
        initial_queries = _pilot_scope_queries(names)
        for baseline, query in zip((names["DB"], names["FB"]), initial_queries):
            _pilot_query(session, f"CREATE TEMPORARY TABLE {baseline} AS {query}")
        queries = _reconcile_live_scope_queries(names)
        report["REVIEWED_SCOPE"] = _reconcile_validate_baseline(session, names, queries)
        if mode == "PREVIEW":
            report["STATUS"] = "RECONCILIATION_PREVIEW_PASSED_NO_TARGET_DML"
            return report
        backup_queries = None
        if backup_policy == "DURABLE":
            phase = "DURABLE_BACKUP"
            backups = {k: schema + "BACKUP_SSP_RECONCILE_" + token + "_" + k for k in ("DIM", "FACT")}
            report["BACKUP_TABLES"] = backups
            backup_queries = _reconcile_create_backups(session, names, backups)
            report["BACKUPS_VERIFIED"] = True
        # The owner waived permanent backups only for this fixed, reviewed DEV scope.
        # Temporary DB/FB snapshots, transaction rollback and baseline checks still apply.
        deletes = _reconcile_delete_sql(names)
        merges = [_pilot_merge_sql(target, names[kind], pk, plan)
                  for target, kind, pk, plan in zip((SSP_PILOT_DIM, SSP_PILOT_FACT), ("D", "F"),
                                                  (SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK), plans)]

        def before_replace():
            if backup_queries is not None:
                _pilot_baseline_equal(session, names, backup_queries)
            _pilot_baseline_equal(session, names, queries)
            report["TARGET_DML_ATTEMPTED"] = True

        def verify(pass_number):
            return {"SAVED_VALUES": _pilot_verify(session, names, queries, plans),
                    "KEY_INTEGRITY": _reconcile_integrity(session, queries, "CONTAINS")}

        phase = "ROLLBACK_REHEARSAL"
        report["REHEARSAL"] = _reconcile_transaction(session, deletes, merges, before_replace,
                                                     verify, (19, 18), commit=False)
        _pilot_baseline_equal(session, names, queries)
        report["ROLLBACK_RESTORED_BASELINE"] = True
        phase = "COMMIT"
        report["COMMIT"] = _reconcile_transaction(session, deletes, merges, before_replace,
                                                  verify, (19, 18), commit=True)
        report["PERSISTED"] = True
        phase = "POST_COMMIT_READBACK"
        report["READBACK"] = verify(3)
        report["STATUS"] = "ONE_RECORD_RECONCILED_AND_VERIFIED"
        return report
    except BaseException as error:
        code = error.code if isinstance(error, PilotError) else "RECONCILIATION_OPERATION_FAILED"
        report.update(STATUS=code, PHASE=phase, ERROR_DETAILS=_pilot_error_details(error))
        if code in ("COMMIT_OUTCOME_UNKNOWN", "ROLLBACK_OUTCOME_UNKNOWN", "BEGIN_OUTCOME_UNKNOWN"):
            report["PERSISTED"] = "UNKNOWN_DO_NOT_RETRY"
        # Keep any snapshots/backups. No DDL or auto-restore after uncertain outcomes.
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        raise PilotError(code) from None


if __name__ == "__main__":
    ssp_reconciliation_report = None
    required = ("session", "CONFIG", "run_result", "final_nodes_df", "final_edges_df")
    if any(name not in globals() for name in required):
        raise PilotError("ACCEPTED_SSP_SESSION_OUTPUTS_REQUIRED")
    ssp_reconciliation_report = run_ssp_one_record_reconciliation(
        session, CONFIG, run_result, final_nodes_df, final_edges_df, SSP_RECONCILE_MODE,
        backup_policy=SSP_RECONCILE_BACKUP_POLICY)
    print(json.dumps(ssp_reconciliation_report, indent=2, sort_keys=True, default=str))
