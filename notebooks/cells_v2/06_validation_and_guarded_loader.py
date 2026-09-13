# %% Cell 6 - Validate once, preview, then atomically upsert the reviewed tables
# Pause other target writers during COMMIT; the snapshots detect changes but do not lock tables.
import json
import re
import uuid

OSCAL_LOAD_RELEASE = "oscal-lean-daily-v3"
_AUDIT = {"DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"}
_DIM_FIELDS = {
    "ELEMENT_TYPE": "VARCHAR(64)", "OSCAL_UUID": "VARCHAR(32)", "METADATA_JSON": "VARIANT",
    "SOURCE_SYSTEM_NAME": "VARCHAR(100)", "SOURCE_TABLE_NAME": "VARCHAR(128)",
    "SOURCE_RECORD_ID": "VARCHAR(128)", "DW_PIPELINE_RUN_ID": "VARCHAR(64)",
    "DW_LOAD_TIMESTAMP": "TIMESTAMP_TZ(9)", "DW_LOAD_TIMESTAMP_TZ": "TIMESTAMP_TZ(9)",
}
_FACT_FIELDS = {
    "FK_SOURCE_ELEMENT_HASH": "BINARY(16)", "FK_TARGET_ELEMENT_HASH": "BINARY(16)",
    "DEPENDENCY_TYPE": "VARCHAR(32)", "SOURCE_OSCAL_UUID": "VARCHAR(32)",
    "TARGET_OSCAL_UUID": "VARCHAR(32)",
}


class LoadError(RuntimeError):
    def __init__(self, code, details=None):
        self.code, self.details = code, details or {}
        super().__init__(code)


def _load_query(statement):
    return session.sql(statement).collect()


def _load_count(statement):
    return int(_load_query(statement)[0]["N"])


def _load_zero(statement, code):
    count = _load_count(statement)
    if count:
        raise LoadError(code, {"COUNT": count})


def _load_identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*){0,2}", value):
        raise LoadError("INVALID_STORAGE_IDENTIFIER")
    return value


def _load_literal(value):
    if not isinstance(value, str) or not value.strip():
        raise LoadError("MISSING_CONFIGURATION_VALUE")
    return "'" + value.replace("'", "''") + "'"


def _load_no_transaction():
    if _load_query("SELECT CURRENT_TRANSACTION() AS TX")[0]["TX"] is not None:
        raise LoadError("EXISTING_TRANSACTION")


def _load_storage(config):
    if type(config.get("EXECUTE_WRITES")) is not bool:
        raise LoadError("EXPLICIT_BOOLEAN_WRITE_MODE_REQUIRED")
    if config.get("OBSOLETE_ROW_POLICY", "BLOCK") != "BLOCK":
        raise LoadError("ONLY_BLOCK_OBSOLETE_POLICY_IS_APPROVED")
    storage = config.get("STORAGE_CONTRACT")
    if not storage or storage.get("VERIFIED") is not True:
        if config["EXECUTE_WRITES"]:
            raise LoadError("STORAGE_CONTRACT_NOT_VERIFIED")
        return None
    storage = dict(storage)
    if storage.get("PHYSICAL_PROFILE") != "BINARY16_UUID32":
        raise LoadError("UNSUPPORTED_STORAGE_PROFILE")
    for name in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"):
        _load_identifier(storage[name])
        if storage[name].count(".") != (2 if name.startswith("TARGET_") else 0):
            raise LoadError("INVALID_STORAGE_IDENTIFIER")
        if config.get(name, storage[name]) != storage[name]:
            raise LoadError("CONFIG_STORAGE_MISMATCH")
    if storage["TARGET_DIM"] == storage["TARGET_FACT"]:
        raise LoadError("DIM_AND_FACT_TARGETS_MUST_DIFFER")
    if storage["DIM_PK_COLUMN"] in _DIM_FIELDS or storage["FACT_PK_COLUMN"] in _FACT_FIELDS:
        raise LoadError("PRIMARY_KEY_COLUMN_CONFLICT")
    for name in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME", "RAW_TABLE", "IDENTITY_VERSION",
                 "ROOT_PATH", "ROOT_ELEMENT_TYPE", "MODEL_KEY"):
        value = config.get("OSCAL_MODEL" if name == "MODEL_KEY" else name)
        if value != storage.get(name) or not isinstance(value, str) or not value:
            raise LoadError("CONFIG_STORAGE_MISMATCH")
    return storage


def _load_graph(nodes, edges, config):
    """One graph boundary for both stored and targetless models; reports contain counts only."""
    def rows(frame):
        values = frame.to_local_iterator() if hasattr(frame, "to_local_iterator") else iter(frame)
        return (value.as_dict() if hasattr(value, "as_dict") else dict(value) for value in values)
    def key(value):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", value):
            raise LoadError("INVALID_GRAPH_HASH")
        return value.lower()
    root = config["ROOT_PATH"]
    by_key, roots, parents, uuids = {}, {}, {}, set()
    for node in rows(nodes):
        k, sid, path = key(node.get("NODE_KEY")), node.get("SOURCE_RECORD_ID"), node.get("ELEMENT_PATH")
        if k in by_key:
            raise LoadError("DUPLICATE_NODE_KEY")
        if not isinstance(sid, str) or not sid.strip() or not isinstance(path, str):
            raise LoadError("MISSING_GRAPH_RECORD_OR_PATH")
        if not (path == root or path.startswith(root + ".")):
            raise LoadError("WRONG_MODEL_PATH")
        parent_path = node.get("PARENT_NODE_PATH")
        if "PARENT_NODE_PATH" not in node or (path == root and parent_path is not None) or (
                path != root and (not isinstance(parent_path, str) or not path.startswith(parent_path + "."))):
            raise LoadError("MISSING_OR_INVALID_PARENT_PATH")
        element_type = node.get("ELEMENT_TYPE")
        if (not isinstance(element_type, str) or not element_type.strip()
                or (path == root and element_type != config["ROOT_ELEMENT_TYPE"])):
            raise LoadError("WRONG_NODE_TYPE_OR_SOURCE")
        if node.get("MODEL_KEY", config["OSCAL_MODEL"]) != config["OSCAL_MODEL"] or any(
                node.get(name) != config[name] for name in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME")):
            raise LoadError("WRONG_NODE_TYPE_OR_SOURCE")
        identity, instance = node.get("OSCAL_UUID"), node.get("INSTANCE_KEY")
        if not isinstance(identity, str) or not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", identity):
            raise LoadError("INVALID_NODE_UUID")
        if identity in uuids:
            raise LoadError("DUPLICATE_NODE_UUID")
        uuids.add(identity)
        if not isinstance(instance, str) or not instance.strip():
            raise LoadError("MISSING_INSTANCE_KEY")
        try:
            payload = node.get("METADATA_JSON")
            payload = json.loads(payload) if isinstance(payload, str) else payload
            if not isinstance(payload, dict):
                raise ValueError()
            json.dumps(payload, allow_nan=False)
        except (ValueError, TypeError):
            raise LoadError("INVALID_NODE_PAYLOAD") from None
        by_key[k] = (sid, path, identity, instance, node.get("PARENT_INSTANCE_KEY"), parent_path)
        parents[k] = 0
        if path == root:
            if sid in roots:
                raise LoadError("DUPLICATE_RECORD_ROOT")
            roots[sid] = k
    if not roots or config.get("EXPECTED_SOURCE_RECORDS", len(roots)) != len(roots):
        raise LoadError("SOURCE_RECORD_GRAPH_COVERAGE_MISMATCH")
    edge_keys = set()
    for edge in rows(edges):
        ek = key(edge.get("EDGE_KEY"))
        if ek in edge_keys:
            raise LoadError("DUPLICATE_EDGE_KEY")
        edge_keys.add(ek)
        source, target = key(edge.get("FK_SOURCE_ELEMENT_HASH")), key(edge.get("FK_TARGET_ELEMENT_HASH"))
        if source not in by_key or target not in by_key:
            raise LoadError("ORPHAN_EDGE")
        parent, child = by_key[source], by_key[target]
        if parent[0] != child[0] or parent[0] not in roots:
            raise LoadError("CROSS_RECORD_EDGE")
        if (edge.get("DEPENDENCY_TYPE") != "CONTAINS" or edge.get("SOURCE_OSCAL_UUID") != parent[2]
                or edge.get("TARGET_OSCAL_UUID") != child[2]):
            raise LoadError("EDGE_RELATIONSHIP_OR_UUID_MISMATCH")
        if (not child[1].startswith(parent[1] + ".") or (child[4] is not None and child[4] != parent[3])
                or child[5] != parent[1]):
            raise LoadError("WRONG_PARENT_CONTEXT")
        parents[target] += 1
    root_keys = set(roots.values())
    if any(count != (0 if k in root_keys else 1) for k, count in parents.items()):
        raise LoadError("WRONG_PARENT_COUNT")
    # Paths strictly descend and each non-root has one parent: cycles and disconnected nodes are impossible.
    return {"nodes": len(by_key), "edges": len(edge_keys), "source_records": len(roots)}


def _load_schema(table, pk, fields, kind):
    expected = {pk: "BINARY(16)", **fields}
    actual = {}
    for row in _load_query("DESC TABLE " + table):
        row = row.as_dict() if hasattr(row, "as_dict") else dict(row)
        row = {str(k).lower(): value for k, value in row.items()}
        name = row["name"]
        nullable = "N" if kind == "FACT" or name == pk else "Y"
        if (name in actual or row.get("kind") != "COLUMN" or row.get("null?") != nullable
                or row.get("expression") not in (None, "")):
            raise LoadError("TARGET_SCHEMA_MISMATCH", {"TABLE_KIND": kind})
        actual[name] = row["type"].upper().replace(" ", "")
    if actual != expected:
        raise LoadError("TARGET_SCHEMA_MISMATCH", {"TABLE_KIND": kind})
    return tuple(expected)


def _load_changed(columns, left="t", right="s", audit=False):
    return " OR ".join(f"{left}.{name} IS DISTINCT FROM {right}.{name}"
                       for name in columns if audit or name not in _AUDIT)


def _load_changes(target, stage, pk, columns):
    changed = _load_changed(columns)
    row = _load_query(f"""SELECT
      COUNT_IF(t.{pk} IS NULL) AS INSERTS,
      COUNT_IF(t.{pk} IS NOT NULL AND ({changed})) AS UPDATES,
      COUNT_IF(t.{pk} IS NOT NULL AND NOT ({changed})) AS UNCHANGED
      FROM {stage} s LEFT JOIN {target} t ON t.{pk}=s.{pk}""")[0]
    return {name: int(row[name] or 0) for name in ("INSERTS", "UPDATES", "UNCHANGED")}


def _load_merge(target, stage, pk, columns):
    assignments = ", ".join(f"t.{name}=s.{name}" for name in columns if name != pk)
    return (f"MERGE INTO {target} t USING {stage} s ON t.{pk}=s.{pk} "
            f"WHEN MATCHED AND ({_load_changed(columns)}) THEN UPDATE SET {assignments} "
            f"WHEN NOT MATCHED THEN INSERT ({', '.join(columns)}) "
            f"VALUES ({', '.join('s.' + name for name in columns)})")


def _load_equal(left, right, code):
    for first, second in ((left, right), (right, left)):
        _load_zero(f"SELECT COUNT(*) AS N FROM (({first}) MINUS ({second}))", code)


def _load_scope(context):
    c, names = context["storage"], context["names"]
    dim, fact, dk, fk = (c[name] for name in ("TARGET_DIM", "TARGET_FACT", "DIM_PK_COLUMN", "FACT_PK_COLUMN"))
    source = " AND ".join(f"t.{name}={_load_literal(c[name])}" for name in ("SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME"))
    dim_query = f"""SELECT t.* FROM {dim} t LEFT JOIN {names['D']} s ON s.{dk}=t.{dk}
      LEFT JOIN (SELECT DISTINCT SOURCE_RECORD_ID FROM {names['D']}) i
      ON i.SOURCE_RECORD_ID=t.SOURCE_RECORD_ID AND {source}
      WHERE s.{dk} IS NOT NULL OR i.SOURCE_RECORD_ID IS NOT NULL"""
    keys = f"SELECT {dk} FROM ({dim_query}) UNION SELECT {dk} FROM {names['D']}"
    fact_query = f"""SELECT t.* FROM {fact} t LEFT JOIN {names['F']} s ON s.{fk}=t.{fk}
      LEFT JOIN ({keys}) p ON p.{dk}=t.FK_SOURCE_ELEMENT_HASH
      LEFT JOIN ({keys}) c ON c.{dk}=t.FK_TARGET_ELEMENT_HASH
      WHERE s.{fk} IS NOT NULL OR p.{dk} IS NOT NULL OR c.{dk} IS NOT NULL"""
    return dim_query, fact_query


def _load_preflight(context):
    c, names = context["storage"], context["names"]
    queries = _load_scope(context)
    for kind, query, fields in zip(("D", "F"), queries, (_DIM_FIELDS, _FACT_FIELDS)):
        table, pk, columns = context[kind]
        _load_zero(f"SELECT COUNT(*) AS N FROM (SELECT {pk} FROM {table} GROUP BY {pk} "
                   f"HAVING {pk} IS NULL OR COUNT(*)>1)", "TARGET_NULL_OR_DUPLICATE_KEYS")
        _load_zero(f"SELECT COUNT(*) AS N FROM ({query}) t WHERE NOT EXISTS "
                   f"(SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})", "OBSOLETE_TARGET_ROWS_BLOCKED")
        identity = [name for name in fields if name not in _AUDIT | {"METADATA_JSON"}]
        _load_zero(f"SELECT COUNT(*) AS N FROM ({query}) t JOIN {names[kind]} s ON s.{pk}=t.{pk} "
                   f"WHERE {_load_changed(identity)}", "TARGET_IDENTITY_PROVENANCE_CONFLICT")
    dim, fact = queries
    dk, fk = c["DIM_PK_COLUMN"], c["FACT_PK_COLUMN"]
    _load_zero(f"SELECT COUNT(*) AS N FROM ({dim}) WHERE NOT COALESCE(IS_OBJECT(METADATA_JSON), FALSE)",
               "INVALID_STORED_PAYLOAD")
    _load_zero(f"""SELECT COUNT(*) AS N FROM ({fact}) f
      LEFT JOIN ({dim}) p ON p.{dk}=f.FK_SOURCE_ELEMENT_HASH
      LEFT JOIN ({dim}) c ON c.{dk}=f.FK_TARGET_ELEMENT_HASH
      WHERE p.{dk} IS NULL OR c.{dk} IS NULL""", "TARGET_ORPHAN_OR_CROSS_SCOPE_EDGE")
    _load_zero(f"""SELECT COUNT(*) AS N FROM (SELECT d.{dk}, d.ELEMENT_TYPE, COUNT(f.{fk}) AS PARENTS
      FROM ({dim}) d LEFT JOIN ({fact}) f ON f.FK_TARGET_ELEMENT_HASH=d.{dk}
      GROUP BY d.{dk}, d.ELEMENT_TYPE HAVING PARENTS <>
      CASE WHEN d.ELEMENT_TYPE={_load_literal(c['ROOT_ELEMENT_TYPE'])} THEN 0 ELSE 1 END)""", "TARGET_WRONG_PARENT_COUNT")
    return queries


def _load_prepare(nodes, edges, config):
    storage = _load_storage(config)
    if storage is None:
        return {"graph": _load_graph(nodes, edges, config), "storage": None}
    _load_no_transaction()  # All materialization DDL must finish before BEGIN.
    context = {"storage": storage}
    for kind, table_key, pk_key, fields in (("D", "TARGET_DIM", "DIM_PK_COLUMN", _DIM_FIELDS),
                                           ("F", "TARGET_FACT", "FACT_PK_COLUMN", _FACT_FIELDS)):
        table, pk = storage[table_key], storage[pk_key]
        context[kind] = (table, pk, _load_schema(table, pk, fields, "DIM" if kind == "D" else "FACT"))
    prefix = storage["TARGET_DIM"].rsplit(".", 1)[0] + ".TMP_OSCAL_" + uuid.uuid4().hex.upper()
    names = {name: prefix + "_" + name for name in ("N", "E", "D", "F", "BD", "BF")}
    context["names"] = names
    for frame, name in ((nodes, names["N"]), (edges, names["E"])):
        frame.write.save_as_table(name, mode="errorifexists", table_type="temporary")
    context["graph"] = _load_graph(session.table(names["N"]), session.table(names["E"]), config)
    for kind, raw, source_pk, fields in (("D", "N", "NODE_KEY", _DIM_FIELDS), ("F", "E", "EDGE_KEY", _FACT_FIELDS)):
        _, pk, columns = context[kind]
        expressions = [f"TO_BINARY({source_pk}, 'HEX') AS {pk}"]
        for name, dtype in fields.items():
            value = (f"TO_BINARY({name}, 'HEX')" if dtype == "BINARY(16)" else
                     f"REPLACE({name}, '-', '')" if name.endswith("OSCAL_UUID") else
                     f"PARSE_JSON({name})" if dtype == "VARIANT" else
                     f"CAST({name} AS {dtype})" if dtype.startswith("TIMESTAMP_") else name)
            expressions.append(f"{value} AS {name}")
        _load_query(f"CREATE TEMPORARY TABLE {names[kind]} AS SELECT {', '.join(expressions)} FROM {names[raw]}")
        for name, dtype in fields.items():
            if dtype.startswith("VARCHAR"):
                width = int(dtype[8:-1])
                _load_zero(f"SELECT COUNT(*) AS N FROM {names[kind]} WHERE LENGTH({name})>{width}", "TARGET_STRING_CAPACITY_EXCEEDED")
        _load_query(f"CREATE TEMPORARY TABLE {names['B' + kind]} AS SELECT * FROM {context[kind][0]}")
    context["scope"] = _load_preflight(context)
    context["changes"] = {kind: _load_changes(context[kind][0], names[kind], context[kind][1], context[kind][2]) for kind in ("D", "F")}
    return context


def _load_baseline(context):
    for kind in ("D", "F"):
        table, _, columns = context[kind]
        grouped = ", ".join(columns)
        query = f"SELECT {grouped}, COUNT(*) AS ROW_MULTIPLICITY FROM {{}} GROUP BY {grouped}"
        _load_equal(query.format(table), query.format(context["names"]["B" + kind]), "TARGET_BASELINE_CHANGED")


def _load_verify(context):
    _load_preflight(context)
    names, report = context["names"], {}
    for kind in ("D", "F"):
        table, pk, columns = context[kind]
        changes = _load_changes(table, names[kind], pk, columns)
        if changes["INSERTS"] or changes["UPDATES"]:
            raise LoadError("SAVED_VALUES_OR_KEYS_DIFFER")
        same = "NOT (" + _load_changed(columns, "b", "s") + ")"
        _load_zero(f"""SELECT COUNT(*) AS N FROM {names[kind]} s JOIN {table} t ON t.{pk}=s.{pk}
          LEFT JOIN {names['B' + kind]} b ON b.{pk}=s.{pk}
          WHERE (b.{pk} IS NOT NULL AND ({same}) AND ({_load_changed(columns, 't', 'b', True)}))
          OR ((b.{pk} IS NULL OR NOT ({same})) AND ({_load_changed(columns, audit=True)}))""", "SAVED_AUDIT_VALUES_DIFFER")
        untouched = f"WHERE NOT EXISTS (SELECT 1 FROM {names[kind]} s WHERE s.{pk}=t.{pk})"
        _load_equal(f"SELECT t.* FROM {table} t {untouched}",
                    f"SELECT t.* FROM {names['B' + kind]} t {untouched}", "UNTOUCHED_ROWS_CHANGED")
        report["DIM" if kind == "D" else "FACT"] = changes
    return report


def validate_and_load_oscal(canonical_nodes_df, canonical_edges_df, config):
    config = dict(config)
    result = {"release": OSCAL_LOAD_RELEASE, "model": config.get("OSCAL_MODEL"),
              "mode": "COMMIT" if config.get("EXECUTE_WRITES") is True else "PREVIEW",
              "writes_executed": False, "persisted": False, "committed": False,
              "target_dml_attempted": False, "pre_write_validation_passed": False}
    phase, context = "PREPARATION", None
    try:
        context = _load_prepare(canonical_nodes_df, canonical_edges_df, config)
        result.update(context["graph"], validation_passed=True, storage_verified=context["storage"] is not None)
        if context["storage"] is None:
            result["status"] = "MAPPED_GRAPH_VALIDATED_TARGET_CONTRACT_PENDING"
            return result
        result.update(pre_write_validation_passed=True, expected_changes=context["changes"])
        if not config["EXECUTE_WRITES"]:
            result["status"] = "PREVIEW_PASSED_NO_TARGET_DML"
            return result
        _load_no_transaction()
        phase = "BEGIN"
        _load_query("BEGIN TRANSACTION")
        phase = "TRANSACTION"
        try:
            _load_baseline(context)
            _load_preflight(context)
            for kind in ("D", "F"):
                target, pk, columns = context[kind]
                result["target_dml_attempted"] = True
                counts = _load_query(_load_merge(target, context["names"][kind], pk, columns))[0]
                expected = context["changes"][kind]
                if (int(counts["number of rows inserted"]), int(counts["number of rows updated"])) != (expected["INSERTS"], expected["UPDATES"]):
                    raise LoadError("UNEXPECTED_MERGE_CHANGE_COUNT")
            _load_verify(context)  # Zero remaining inserts/updates proves a rerun will be unchanged.
        except BaseException as error:
            result["cause"] = error.code if isinstance(error, LoadError) else type(error).__name__
            phase = "ROLLBACK"
            _load_query("ROLLBACK")
            phase = "ROLLBACK_READBACK"
            _load_baseline(context)
            result["rollback_readback_verified"] = True
            phase = "ROLLED_BACK"
            raise LoadError("TRANSACTION_ROLLED_BACK") from None
        phase = "COMMIT"
        _load_query("COMMIT")
        result.update(writes_executed=True, persisted=True, committed=True)
        phase = "POST_COMMIT_READBACK"
        result["verification"] = _load_verify(context)
        result["status"] = "COMMITTED_AND_VERIFIED"
        return result
    except BaseException as error:
        code = error.code if isinstance(error, LoadError) else "LOAD_OPERATION_FAILED"
        if phase in {"BEGIN", "COMMIT", "ROLLBACK", "ROLLBACK_READBACK"}:
            code, result["persisted"] = phase + "_OUTCOME_UNKNOWN_DO_NOT_RETRY", "UNKNOWN"
        elif phase == "POST_COMMIT_READBACK":
            code = "POST_COMMIT_READBACK_FAILED_DO_NOT_RETRY"
        result.update(status=code, phase=phase)
        raise LoadError(code, result) from None


def verify_oscal_load(canonical_nodes_df, canonical_edges_df, config):
    context = _load_prepare(canonical_nodes_df, canonical_edges_df, dict(config, EXECUTE_WRITES=False))
    if context["storage"] is None:
        return {"status": "TARGET_CONTRACT_PENDING", "storage_verified": False, **context["graph"]}
    return {"status": "LOAD_VERIFIED", "storage_verified": True, **_load_verify(context)}


validate_and_load_oscal._oscal_loader_release = OSCAL_LOAD_RELEASE
