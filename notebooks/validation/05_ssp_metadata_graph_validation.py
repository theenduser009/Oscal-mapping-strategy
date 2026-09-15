# SSP Validation 05 - Metadata graph
# Read only. Run after current Cells 1-7 in SSP PREVIEW.

from collections import Counter

if tuple(SELECTED_MODELS) != ("SSP",):
    raise ValueError("SSP only")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Writes must remain false")
if OSCAL_LOAD_MODE != "PREVIEW":
    raise ValueError("PREVIEW required")
if PIPELINE_REPORT.get("status") != "PREVIEW_COMPLETE":
    raise ValueError("Cell 7 preview is not complete")

ctx = next(c for c in MAPPING_CONTEXTS if c["config"]["OSCAL_MODEL"] == "SSP")
graph = MODEL_GRAPHS[(ctx["source_key"], "SSP")]
nodes = [r.as_dict(recursive=True) for r in graph["nodes"].collect()]
edges = [r.as_dict(recursive=True) for r in graph["edges"].collect()]

# Cell 5 contract uses NODE_KEY and ELEMENT_PATH.
meta_nodes = [r for r in nodes if r["ELEMENT_PATH"] == "system-security-plan.metadata" or r["ELEMENT_PATH"].startswith("system-security-plan.metadata.")]
meta_keys = {r["NODE_KEY"] for r in meta_nodes}
all_keys = {r["NODE_KEY"] for r in nodes}
all_uuids = {r["OSCAL_UUID"] for r in nodes}
meta_edges = [r for r in edges if r["FK_SOURCE_ELEMENT_HASH"] in meta_keys or r["FK_TARGET_ELEMENT_HASH"] in meta_keys]

missing_node_key = [r for r in meta_nodes if not r.get("NODE_KEY")]
duplicate_node_key = [k for k,n in Counter(r["NODE_KEY"] for r in meta_nodes).items() if n > 1]
missing_instance_key = [r for r in meta_nodes if not str(r.get("INSTANCE_KEY") or "").strip()]
missing_uuid = [r for r in meta_nodes if not str(r.get("OSCAL_UUID") or "").strip()]
duplicate_uuid = [u for u,n in Counter(r["OSCAL_UUID"] for r in meta_nodes).items() if n > 1]

bad_payload = []
for r in meta_nodes:
    try:
        p = json.loads(r["METADATA_JSON"]) if isinstance(r["METADATA_JSON"], str) else r["METADATA_JSON"]
        if not isinstance(p, dict):
            bad_payload.append(r["NODE_KEY"])
    except Exception:
        bad_payload.append(r["NODE_KEY"])

bad_edge_source = [r["EDGE_KEY"] for r in meta_edges if r["FK_SOURCE_ELEMENT_HASH"] not in all_keys]
bad_edge_target = [r["EDGE_KEY"] for r in meta_edges if r["FK_TARGET_ELEMENT_HASH"] not in all_keys]
bad_edge_type = [r["EDGE_KEY"] for r in meta_edges if r["DEPENDENCY_TYPE"] != "CONTAINS"]
bad_edge_uuid = [r["EDGE_KEY"] for r in meta_edges if r["SOURCE_OSCAL_UUID"] not in all_uuids or r["TARGET_OSCAL_UUID"] not in all_uuids]

# Parent path must match the exact registry contract compiled by Cell 3.
parent_by_path = {r["NODE_PATH"]: r.get("PARENT_NODE_PATH") for r in ctx["ELEMENT_REGISTRY"]}
bad_parent_path = [(r["ELEMENT_PATH"], r["PARENT_NODE_PATH"], parent_by_path.get(r["ELEMENT_PATH"])) for r in meta_nodes if r["PARENT_NODE_PATH"] != parent_by_path.get(r["ELEMENT_PATH"])]

print("=== SSP VALIDATION 05 ===")
print("VALIDATION: SSP_METADATA_GRAPH")
print("METADATA_NODE_ROWS:", len(meta_nodes))
print("NODE_COUNTS_BY_PATH:", dict(Counter(r["ELEMENT_PATH"] for r in meta_nodes)))
print("MISSING_NODE_KEY:", len(missing_node_key))
print("DUPLICATE_NODE_KEY:", len(duplicate_node_key))
print("MISSING_INSTANCE_KEY:", len(missing_instance_key))
print("MISSING_UUID:", len(missing_uuid))
print("DUPLICATE_UUID:", len(duplicate_uuid))
print("INVALID_PAYLOAD:", len(bad_payload))
print("METADATA_RELATED_EDGES:", len(meta_edges))
print("MISSING_EDGE_SOURCE:", len(bad_edge_source))
print("MISSING_EDGE_TARGET:", len(bad_edge_target))
print("NON_CONTAINS_EDGE:", len(bad_edge_type))
print("MISSING_EDGE_UUID_REFERENCE:", len(bad_edge_uuid))
print("PARENT_PATH_MISMATCH:", len(bad_parent_path))
print("SAMPLES:", [(r["SOURCE_RECORD_ID"], r["ELEMENT_PATH"], r["INSTANCE_KEY"], r["OSCAL_UUID"]) for r in meta_nodes[:10]])

failures = missing_node_key or duplicate_node_key or missing_instance_key or missing_uuid or duplicate_uuid or bad_payload or bad_edge_source or bad_edge_target or bad_edge_type or bad_edge_uuid or bad_parent_path
status = "PASS" if meta_nodes and not failures else "FAIL"
print("STATUS:", status)
