# Copy the complete file into ONE NEW PYTHON cell in the same accepted SSP session.
# No edits. Do not rerun the write pilot. No target writes or role changes.
# Reads the current accepted graph, not the failed pilot's original frozen snapshot.
# Only aggregate counts and element/dependency type labels are printed.
import json
import re


class ExtraTargetComparisonError(ValueError):
    pass


def _extra_hex_keys(values):
    if not values or any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-fA-F]{32}", v) for v in values):
        raise ExtraTargetComparisonError("INVALID_CANDIDATE_KEYS")
    normalized = [v.lower() for v in values]
    if len(normalized) != len(set(normalized)):
        raise ExtraTargetComparisonError("DUPLICATE_PHYSICAL_CANDIDATE_KEYS")
    return normalized


def _extra_comparison_sql(node_keys, edge_keys):
    # Keys cannot inject SQL: only exact 32-hex strings are accepted.
    ns, es = _extra_hex_keys(node_keys), _extra_hex_keys(edge_keys)
    nv = ",".join("('" + k + "')" for k in ns)
    ev = ",".join("('" + k + "')" for k in es)
    return f"""WITH wanted_nodes AS (
 SELECT TO_BINARY(column1, 'HEX') AS K FROM VALUES {nv}
), wanted_edges AS (
 SELECT TO_BINARY(column1, 'HEX') AS K FROM VALUES {ev}
), scoped_dim AS (
 SELECT t.PK_OSCAL_SSP_ELEMENT_HASH AS K, t.ELEMENT_TYPE
 FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.DIM_OSCAL_SSP_ELEMENT t
 WHERE t.PK_OSCAL_SSP_ELEMENT_HASH IN (SELECT K FROM wanted_nodes)
 OR (t.SOURCE_SYSTEM_NAME='ARCHER'
     AND t.SOURCE_TABLE_NAME='ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW'
     AND t.SOURCE_RECORD_ID=?)
), scoped_fact AS (
 SELECT t.PK_FACT_OSCAL_DEPENDENCY_HASH AS K, t.FK_SOURCE_ELEMENT_HASH AS S,
        t.FK_TARGET_ELEMENT_HASH AS T, t.DEPENDENCY_TYPE
 FROM RTX_ENTERPRISESERVICES_DEV.ES_ESC_GRC_CURATED.FACT_OSCAL_SSP_DEPENDENCY t
 WHERE t.PK_FACT_OSCAL_DEPENDENCY_HASH IN (SELECT K FROM wanted_edges)
 OR t.FK_SOURCE_ELEMENT_HASH IN (SELECT K FROM wanted_nodes)
 OR t.FK_TARGET_ELEMENT_HASH IN (SELECT K FROM wanted_nodes)
 OR t.FK_SOURCE_ELEMENT_HASH IN (SELECT K FROM scoped_dim)
 OR t.FK_TARGET_ELEMENT_HASH IN (SELECT K FROM scoped_dim)
), extra_dim AS (
 SELECT t.* FROM scoped_dim t WHERE NOT EXISTS (SELECT 1 FROM wanted_nodes w WHERE w.K=t.K)
), extra_fact AS (
 SELECT t.* FROM scoped_fact t WHERE NOT EXISTS (SELECT 1 FROM wanted_edges w WHERE w.K=t.K)
), facts_classified AS (
 SELECT f.*, IFF(s.K IS NULL, FALSE, TRUE) AS SOURCE_IN_BATCH,
             IFF(t.K IS NULL, FALSE, TRUE) AS TARGET_IN_BATCH
 FROM extra_fact f LEFT JOIN wanted_nodes s ON s.K=f.S
 LEFT JOIN wanted_nodes t ON t.K=f.T
)
SELECT 'SUMMARY' AS SECTION, 'CANDIDATE_NODES' AS DETAIL, NULL AS SOURCE_IN_BATCH,
       NULL AS TARGET_IN_BATCH, COUNT(*) AS ROW_COUNT FROM wanted_nodes
UNION ALL SELECT 'SUMMARY','CANDIDATE_EDGES',NULL,NULL,COUNT(*) FROM wanted_edges
UNION ALL SELECT 'SUMMARY','TARGET_DIM_ROWS',NULL,NULL,COUNT(*) FROM scoped_dim
UNION ALL SELECT 'SUMMARY','TARGET_FACT_ROWS',NULL,NULL,COUNT(*) FROM scoped_fact
UNION ALL SELECT 'SUMMARY','EXTRA_DIM_ROWS',NULL,NULL,COUNT(*) FROM extra_dim
UNION ALL SELECT 'SUMMARY','EXTRA_FACT_ROWS',NULL,NULL,COUNT(*) FROM extra_fact
UNION ALL SELECT 'SUMMARY','EXTRA_DIM_DISTINCT_KEYS',NULL,NULL,COUNT(DISTINCT K) FROM extra_dim
UNION ALL SELECT 'SUMMARY','EXTRA_FACT_DISTINCT_KEYS',NULL,NULL,COUNT(DISTINCT K) FROM extra_fact
UNION ALL SELECT 'SUMMARY','DIM_DUPLICATE_KEY_GROUPS',NULL,NULL,COUNT(*) FROM
 (SELECT K FROM scoped_dim GROUP BY K HAVING COUNT(*)>1)
UNION ALL SELECT 'SUMMARY','FACT_DUPLICATE_KEY_GROUPS',NULL,NULL,COUNT(*) FROM
 (SELECT K FROM scoped_fact GROUP BY K HAVING COUNT(*)>1)
UNION ALL SELECT 'EXTRA_DIM_BY_TYPE',ELEMENT_TYPE,NULL,NULL,COUNT(*) FROM extra_dim GROUP BY ELEMENT_TYPE
UNION ALL SELECT 'EXTRA_FACT_BY_TYPE',DEPENDENCY_TYPE,SOURCE_IN_BATCH,TARGET_IN_BATCH,COUNT(*)
 FROM facts_classified GROUP BY DEPENDENCY_TYPE,SOURCE_IN_BATCH,TARGET_IN_BATCH
ORDER BY SECTION,DETAIL,SOURCE_IN_BATCH,TARGET_IN_BATCH"""


def run_ssp_extra_target_comparison(session, config, run_result, nodes, edges):
    from snowflake.snowpark.functions import col, min as sf_min
    # Reuse the already loaded pilot's exact accepted-model/target contract.
    _pilot_contract(config, run_result)
    _pilot_no_transaction(session)
    roots = nodes.filter(col("ELEMENT_PATH") == "system-security-plan")
    selected = roots.select(sf_min(col("SOURCE_RECORD_ID")).alias("SOURCE_RECORD_ID")).collect()
    record_id = selected[0]["SOURCE_RECORD_ID"] if selected else None
    if record_id is None:
        raise ExtraTargetComparisonError("NO_ACCEPTED_SSP_ROOT")
    batch = nodes.filter(col("SOURCE_RECORD_ID") == record_id)
    node_rows = batch.select("NODE_KEY", "ELEMENT_PATH", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME").limit(20).collect()
    if len(node_rows) != 19 or sum(r["ELEMENT_PATH"] == "system-security-plan" for r in node_rows) != 1:
        raise ExtraTargetComparisonError("CANDIDATE_DIFFERS_FROM_POSTED_19_NODE_BATCH")
    if any(r["SOURCE_SYSTEM_NAME"] != "ARCHER" or r["SOURCE_TABLE_NAME"] != "ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW"
           for r in node_rows):
        raise ExtraTargetComparisonError("CANDIDATE_SOURCE_SCOPE_CHANGED")
    raw_keys = [r["NODE_KEY"] for r in node_rows]
    node_keys = _extra_hex_keys(raw_keys)
    incident = edges.filter(col("FK_SOURCE_ELEMENT_HASH").isin(raw_keys) | col("FK_TARGET_ELEMENT_HASH").isin(raw_keys))
    edge_rows = incident.select("EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE").limit(19).collect()
    if len(edge_rows) != 18:
        raise ExtraTargetComparisonError("CANDIDATE_DIFFERS_FROM_POSTED_18_EDGE_BATCH")
    known = set(raw_keys)
    if any(r["FK_SOURCE_ELEMENT_HASH"] not in known or r["FK_TARGET_ELEMENT_HASH"] not in known
           or r["DEPENDENCY_TYPE"] != "CONTAINS" for r in edge_rows):
        raise ExtraTargetComparisonError("CANDIDATE_EDGE_SCOPE_CHANGED")
    edge_keys = _extra_hex_keys([r["EDGE_KEY"] for r in edge_rows])
    # One SELECT statement gives all target classifications in the same snapshot.
    rows = session.sql(_extra_comparison_sql(node_keys, edge_keys), params=[record_id]).collect()
    return {"STATUS": "READ_ONLY_COMPARISON_COMPLETE", "MODEL": "SSP",
            "BASELINE": "CURRENT_ACCEPTED_GRAPH_NOT_ORIGINAL_FROZEN_SNAPSHOT",
            "SOURCE_RECORDS": 1, "CANDIDATE_NODES": 19, "CANDIDATE_EDGES": 18,
            "TARGET_DML_ATTEMPTED": False,
            "COUNTS": [dict(r.as_dict()) if hasattr(r, "as_dict") else dict(r) for r in rows]}


if __name__ == "__main__":
    ssp_extra_target_report = None
    needed = ("session", "CONFIG", "run_result", "final_nodes_df", "final_edges_df",
              "_pilot_contract", "_pilot_no_transaction", "_pilot_error_details")
    if any(n not in globals() for n in needed):
        raise RuntimeError("KEEP_THE_ACCEPTED_SSP_AND_PILOT_SESSION_OPEN")
    try:
        ssp_extra_target_report = run_ssp_extra_target_comparison(
            session, CONFIG, run_result, final_nodes_df, final_edges_df)
        print(json.dumps(ssp_extra_target_report, indent=2, sort_keys=True, default=str))
    except Exception as error:
        details = _pilot_error_details(error)
        if isinstance(error, ExtraTargetComparisonError):
            details["CAUSE"] = str(error)
        print(json.dumps({"STATUS": "READ_ONLY_COMPARISON_STOPPED", "TARGET_DML_ATTEMPTED": False,
                          "ERROR_DETAILS": details}, sort_keys=True))
        raise RuntimeError("READ_ONLY_COMPARISON_STOPPED") from None
