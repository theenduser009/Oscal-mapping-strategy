# Separate one-record SSP DEV pilot. Never change CONFIG['EXECUTE_WRITES'].
# PREVIEW touches only session-temporary objects; COMMIT performs the approved pilot.
# Requires the accepted SSP Cell 7 outputs in the same session; AR is not used.
import json
import re
import uuid


SSP_PILOT_RELEASE = "ssp-one-record-write-v4-new-record-insert-only"
SSP_PILOT_MODE = "PREVIEW"  # Set to COMMIT only for the approved one-record DEV pilot.
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


def _pilot_transaction(session, merge_statements, verify_callback, commit=False,
                       before_write=None, expected_inserts=None):
    """DML/SELECT only. Staging and verification SQL must be prepared beforehand."""
    if type(commit) is not bool or len(merge_statements) != 2:
        raise PilotError("INVALID_TRANSACTION_ARGUMENTS")
    if any(not statement.lstrip().upper().startswith("MERGE INTO ")
           or ";" in statement for statement in merge_statements):
        raise PilotError("INVALID_TRANSACTION_STATEMENT")
    if before_write is not None and not callable(before_write):
        raise PilotError("INVALID_TRANSACTION_ARGUMENTS")
    if expected_inserts is not None and (len(expected_inserts) != 2 or
            any(type(n) is not int or n < 1 for n in expected_inserts)):
        raise PilotError("INVALID_TRANSACTION_ARGUMENTS")
    _pilot_no_transaction(session)
    try:
        _pilot_query(session, "BEGIN TRANSACTION")
    except BaseException:
        raise PilotError("BEGIN_OUTCOME_UNKNOWN") from None
    verified, inserted = [], []
    step, pass_number = "BEFORE_MERGE", 0
    try:
        if before_write is not None:
            before_write()
        for pass_number in (1, 2):
            pass_inserts = []
            for index, (step, statement) in enumerate(zip(("DIM_MERGE", "FACT_MERGE"), merge_statements)):
                result = _pilot_query(session, statement)
                if expected_inserts is not None:
                    if len(result) != 1:
                        raise PilotError("MERGE_INSERT_COUNT_UNAVAILABLE")
                    row = result[0].as_dict() if hasattr(result[0], "as_dict") else dict(result[0])
                    counts = {str(k).lower(): v for k, v in row.items()}
                    value = counts.get("number of rows inserted")
                    if not re.fullmatch(r"[0-9]+", str(value)):
                        raise PilotError("MERGE_INSERT_COUNT_UNAVAILABLE")
                    actual = int(value)
                    expected = expected_inserts[index] if pass_number == 1 else 0
                    if actual != expected:
                        raise PilotError("UNEXPECTED_MERGE_INSERT_COUNT",
                                         {"EXPECTED_INSERTS": expected, "ACTUAL_INSERTS": actual})
                    pass_inserts.append(actual)
            if expected_inserts is not None:
                inserted.append({"PASS": pass_number, "DIM": pass_inserts[0], "FACT": pass_inserts[1]})
            step = "READBACK"
            verified.append(verify_callback(pass_number))
    except BaseException as error:
        details = dict(_pilot_error_details(error), STEP=step, PASS=pass_number)
        try:
            _pilot_query(session, "ROLLBACK")
        except BaseException:
            raise PilotError("ROLLBACK_OUTCOME_UNKNOWN", details) from None
        raise PilotError("TRANSACTION_ROLLED_BACK", details) from None
    if commit:
        try:
            _pilot_query(session, "COMMIT")
        except BaseException:
            # The server may have committed despite a lost response. Never retry blindly.
            raise PilotError("COMMIT_OUTCOME_UNKNOWN") from None
    else:
        try:
            _pilot_query(session, "ROLLBACK")
        except BaseException:
            raise PilotError("ROLLBACK_OUTCOME_UNKNOWN") from None
    return {"STATUS": "COMMITTED" if commit else "ROLLED_BACK",
            "VERIFIED_PASSES": len(verified), "CHECKS": verified, "INSERT_COUNTS": inserted}


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


def _pilot_new_record_sql(nv, ev):
    """Select once by source ownership AND physical-key absence, without returning IDs."""
    nv, ev = _pilot_table(nv), _pilot_table(ev)
    dim, fact = _pilot_table(SSP_PILOT_DIM), _pilot_table(SSP_PILOT_FACT)
    dk, fk = SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK
    # Flat CTEs avoid multi-level correlated subqueries in Snowflake. Any existing
    # row for this source record excludes it, even when all legacy keys differ.
    return f"""WITH candidates AS (
    SELECT DISTINCT SOURCE_RECORD_ID FROM {nv}
    WHERE ELEMENT_PATH='system-security-plan' AND SOURCE_RECORD_ID IS NOT NULL
      AND SOURCE_SYSTEM_NAME='ARCHER' AND SOURCE_TABLE_NAME='{SSP_PILOT_SOURCE}'
), occupied AS (
    SELECT r.SOURCE_RECORD_ID FROM candidates r JOIN {dim} t
      ON t.SOURCE_RECORD_ID=r.SOURCE_RECORD_ID
      AND t.SOURCE_SYSTEM_NAME='ARCHER' AND t.SOURCE_TABLE_NAME='{SSP_PILOT_SOURCE}'
    UNION
    SELECT n.SOURCE_RECORD_ID FROM {nv} n JOIN {dim} t
      ON t.{dk}=TO_BINARY(n.NODE_KEY, 'HEX')
    UNION
    SELECT n.SOURCE_RECORD_ID FROM {nv} n JOIN {fact} t
      ON t.FK_SOURCE_ELEMENT_HASH=TO_BINARY(n.NODE_KEY, 'HEX')
      OR t.FK_TARGET_ELEMENT_HASH=TO_BINARY(n.NODE_KEY, 'HEX')
    UNION
    SELECT n.SOURCE_RECORD_ID FROM {nv} n JOIN {ev} e
      ON e.FK_SOURCE_ELEMENT_HASH=n.NODE_KEY OR e.FK_TARGET_ELEMENT_HASH=n.NODE_KEY
      JOIN {fact} t ON t.{fk}=TO_BINARY(e.EDGE_KEY, 'HEX')
), chosen AS (
    SELECT MIN(r.SOURCE_RECORD_ID) AS SOURCE_RECORD_ID FROM candidates r
    WHERE NOT EXISTS (SELECT 1 FROM occupied o WHERE o.SOURCE_RECORD_ID=r.SOURCE_RECORD_ID)
)
SELECT n.* FROM {nv} n JOIN chosen c ON n.SOURCE_RECORD_ID=c.SOURCE_RECORD_ID"""


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
    _pilot_query(session, f"CREATE TEMPORARY TABLE {nr} AS " + _pilot_new_record_sql(nv, ev))
    n = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {nr}")
    if n == 0:
        raise PilotError("NO_UNSTORED_SSP_RECORD_AVAILABLE")
    _pilot_query(session, f"CREATE TEMPORARY TABLE {er} AS SELECT * FROM {ev} "
                 f"WHERE FK_SOURCE_ELEMENT_HASH IN (SELECT NODE_KEY FROM {nr}) "
                 f"OR FK_TARGET_ELEMENT_HASH IN (SELECT NODE_KEY FROM {nr})")
    e = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {er}")
    roots = _pilot_count(session, f"SELECT COUNT(*) AS N FROM {nr} "
                         "WHERE ELEMENT_PATH = 'system-security-plan'")
    if n < 2 or e != n - 1 or roots != 1:
        raise PilotError("ONE_COMPLETE_SSP_TREE_REQUIRED")
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


def _pilot_require_empty_scope(session, queries):
    # Called during preflight and again inside EACH transaction before pass 1.
    # Never on pass 2: that pass must see this transaction's own inserts.
    for query in queries:
        _pilot_zero(session, f"SELECT COUNT(*) AS N FROM ({query})",
                    "NEW_RECORD_TARGET_SCOPE_NOT_EMPTY")


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


def run_ssp_one_record_write_pilot(session, config, run_result, nodes, edges, mode="PREVIEW"):
    """Separate accepted-SSP-only persistence exercise. Run with other writers paused."""
    _pilot_contract(config, run_result)
    if mode not in ("PREVIEW", "COMMIT"):
        raise PilotError("PILOT_MODE_MUST_BE_PREVIEW_OR_COMMIT")
    _pilot_no_transaction(session)
    prefix = "RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.TMP_SSP_PILOT_" + uuid.uuid4().hex.upper()
    names = {suffix: prefix + "_" + suffix for suffix in ("NV", "EV", "NR", "ER", "D", "F", "DB", "FB")}
    report = {"RELEASE": SSP_PILOT_RELEASE, "MODEL": "SSP", "MODE": mode,
              "SELECTION": "LOWEST_UNSTORED_SOURCE_RECORD", "WRITE_POLICY": "INSERT_ONLY",
              "STATUS": "PREPARING", "TARGET_DML_ATTEMPTED": False, "PERSISTED": False}
    phase = "SCHEMA_AND_STAGING"
    try:
        # Include schema stops in the printed aggregate report, before any target DML.
        plans = [_pilot_column_plan(_pilot_query(session, "DESC TABLE " + target), kind)
                 for target, kind in ((SSP_PILOT_DIM, "DIM"), (SSP_PILOT_FACT, "FACT"))]
        _pilot_selection_schema(plans)
        report.update(_pilot_freeze_graph(session, nodes, edges, names))
        for raw, stage, plan in zip(("NR", "ER"), ("D", "F"), plans):
            _pilot_stage(session, names[raw], names[stage], plan)
        queries = _pilot_scope_queries(names)
        _pilot_require_empty_scope(session, queries)
        _pilot_check_existing_scope(session, names, queries)
        for baseline, query in zip((names["DB"], names["FB"]), queries):
            _pilot_query(session, f"CREATE TEMPORARY TABLE {baseline} AS {query}")
        _pilot_baseline_equal(session, names, queries)
        report["BEFORE_WRITE"] = _pilot_verify(session, names, queries, plans, require_match=False)
        if mode == "PREVIEW":
            report["STATUS"] = "PREVIEW_PASSED_NO_TARGET_DML"
            return report
        merges = [_pilot_merge_sql(target, names[kind], pk, plan)
                  for target, kind, pk, plan in zip((SSP_PILOT_DIM, SSP_PILOT_FACT), ("D", "F"),
                                                  (SSP_PILOT_DIM_PK, SSP_PILOT_FACT_PK), plans)]
        verify = lambda pass_number: _pilot_verify(session, names, queries, plans)
        def empty_scope():
            _pilot_require_empty_scope(session, queries)
            report["TARGET_DML_ATTEMPTED"] = True
        expected_inserts = (report["NODES"], report["EDGES"])
        phase = "ROLLBACK_REHEARSAL"
        _pilot_baseline_equal(session, names, queries)
        report["REHEARSAL"] = _pilot_transaction(session, merges, verify, commit=False,
                                               before_write=empty_scope, expected_inserts=expected_inserts)
        _pilot_baseline_equal(session, names, queries)
        report["ROLLBACK_RESTORED_BASELINE"] = True
        phase = "COMMIT"
        report["COMMIT"] = _pilot_transaction(session, merges, verify, commit=True,
                                            before_write=empty_scope, expected_inserts=expected_inserts)
        report["PERSISTED"] = True
        phase = "POST_COMMIT_READBACK"
        report["READBACK"] = _pilot_verify(session, names, queries, plans)
        report["STATUS"] = "ONE_RECORD_COMMITTED_AND_VERIFIED"
        return report
    except BaseException as error:
        code = error.code if isinstance(error, PilotError) else "PILOT_OPERATION_FAILED"
        report.update(STATUS=code, PHASE=phase)
        report["ERROR_DETAILS"] = _pilot_error_details(error)
        if code in ("COMMIT_OUTCOME_UNKNOWN", "ROLLBACK_OUTCOME_UNKNOWN", "BEGIN_OUTCOME_UNKNOWN"):
            report["PERSISTED"] = "UNKNOWN_DO_NOT_RETRY"
        # No automatic DDL cleanup: it could commit an uncertain active transaction.
        print(json.dumps(report, sort_keys=True, default=str))
        raise PilotError(code) from None


if __name__ == "__main__":
    # Assignment would otherwise leave an earlier success visible after a failed rerun.
    ssp_pilot_report = None
    required = ("session", "CONFIG", "run_result", "final_nodes_df", "final_edges_df")
    if any(name not in globals() for name in required):
        raise PilotError("ACCEPTED_SSP_SESSION_OUTPUTS_REQUIRED")
    ssp_pilot_report = run_ssp_one_record_write_pilot(
        session, CONFIG, run_result, final_nodes_df, final_edges_df, SSP_PILOT_MODE)
    print(json.dumps(ssp_pilot_report, indent=2, sort_keys=True, default=str))
