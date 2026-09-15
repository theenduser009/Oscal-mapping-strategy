# %% SSP Validation 05 - Remaining Metadata mappings (bulk)
# Date: 2026-09-15
# READ ONLY. Run after Cells 1-7 in SSP PREVIEW mode.
#
# Validation 03 handled published/last-modified timestamps (DEFERRED_SME).
# Validation 04 handled document-ids[].identifier (PASS on 2026-09-15).
# This validation handles the remaining executable Metadata targets together:
# direct metadata members, roles[], parties[], responsible-parties[].

if tuple(SELECTED_MODELS) != ("SSP",):
    raise ValueError("Validation 05 requires SELECTED_MODELS = ('SSP',)")
if CONFIG.get("EXECUTE_WRITES") is not False:
    raise ValueError("Validation 05 requires EXECUTE_WRITES = False")
if OSCAL_LOAD_MODE != "PREVIEW":
    raise ValueError("Validation 05 requires Cell 7 OSCAL_LOAD_MODE = 'PREVIEW'")

ssp_context = next((c for c in MAPPING_CONTEXTS if c["config"]["OSCAL_MODEL"] == "SSP"), None)
if ssp_context is None:
    raise ValueError("Compiled SSP context is missing")

graph_key = (ssp_context["source_key"], "SSP")
if not isinstance(MODEL_GRAPHS, dict) or graph_key not in MODEL_GRAPHS:
    raise ValueError("Cell 7 SSP PREVIEW graph is missing from MODEL_GRAPHS")
nodes_df = MODEL_GRAPHS[graph_key]["nodes"]
edges_df = MODEL_GRAPHS[graph_key]["edges"]

metadata_mappings = [r for r in ssp_context["mapping_rows"]
                     if str(r.get("CANONICAL_ELEMENT_PATH") or "").startswith("system-security-plan.metadata")]
already_tested = {
    "system-security-plan.metadata.published",
    "system-security-plan.metadata.last-modified",
    "system-security-plan.metadata.document-ids[].identifier",
}
remaining = [r for r in metadata_mappings if r.get("CANONICAL_ELEMENT_PATH") not in already_tested]

mapping_failures = []
for r in remaining:
    if not str(r.get("SOURCE_FIELD_NAME") or "").strip():
        mapping_failures.append(("MISSING_SOURCE_FIELD", r.get("RULE_ID")))
    if not str(r.get("CANONICAL_ELEMENT_PATH") or "").strip():
        mapping_failures.append(("MISSING_TARGET", r.get("RULE_ID")))
    if not str(r.get("TRANSFORM_ID") or "").strip():
        mapping_failures.append(("MISSING_TRANSFORM", r.get("RULE_ID")))

metadata_types = {"metadata", "roles", "parties", "responsible-parties"}
metadata_nodes = [r.as_dict(recursive=True)
                  for r in nodes_df.filter(col("ELEMENT_TYPE").isin(list(metadata_types))).collect()]

missing_node_keys, duplicate_node_keys, seen_node_keys = [], [], set()
for r in metadata_nodes:
    key = r.get("PK_ELEMENT_HASH")
    if not key:
        missing_node_keys.append((r.get("SOURCE_RECORD_ID"), r.get("ELEMENT_TYPE")))
    elif key in seen_node_keys:
        duplicate_node_keys.append(key)
    else:
        seen_node_keys.add(key)

# Cell 2's actual registry contract is REGISTRY_INPUT_ROWS (already read once).
registry_rows = REGISTRY_INPUT_ROWS
uuid_required_types = {
    str(r.get("ELEMENT_TYPE"))
    for r in registry_rows
    if str(r.get("OSCAL_MODEL_KEY") or "").upper() == "SSP"
    and str(r.get("UUID_POLICY") or "").lower() in {"instance", "node"}
    and str(r.get("ELEMENT_TYPE") or "") in metadata_types
}
missing_uuids = [(r.get("SOURCE_RECORD_ID"), r.get("ELEMENT_TYPE"), r.get("PK_ELEMENT_HASH"))
                 for r in metadata_nodes
                 if r.get("ELEMENT_TYPE") in uuid_required_types and not r.get("OSCAL_UUID")]

invalid_payloads = []
for r in metadata_nodes:
    payload = r.get("METADATA_JSON")
    if isinstance(payload, str):
        try: payload = json.loads(payload)
        except Exception: payload = None
    if not isinstance(payload, dict):
        invalid_payloads.append((r.get("SOURCE_RECORD_ID"), r.get("ELEMENT_TYPE"), r.get("PK_ELEMENT_HASH")))

node_keys = {r.get("PK_ELEMENT_HASH") for r in metadata_nodes if r.get("PK_ELEMENT_HASH")}
all_node_keys = {r["PK_ELEMENT_HASH"] for r in nodes_df.select("PK_ELEMENT_HASH").collect() if r["PK_ELEMENT_HASH"]}
edge_rows = [r.as_dict(recursive=True) for r in edges_df.collect()]
metadata_edge_rows = [r for r in edge_rows
                      if r.get("FK_SOURCE_ELEMENT_HASH") in node_keys or r.get("FK_TARGET_ELEMENT_HASH") in node_keys]
missing_edge_sources = [r for r in metadata_edge_rows if r.get("FK_SOURCE_ELEMENT_HASH") not in all_node_keys]
missing_edge_targets = [r for r in metadata_edge_rows if r.get("FK_TARGET_ELEMENT_HASH") not in all_node_keys]

metadata_uuids = {str(r.get("OSCAL_UUID")) for r in metadata_nodes if r.get("OSCAL_UUID")}
unresolved_uuid_refs = []
uuid_re = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
for r in metadata_nodes:
    payload = r.get("METADATA_JSON")
    if isinstance(payload, str):
        try: payload = json.loads(payload)
        except Exception: payload = None
    if not isinstance(payload, dict):
        continue
    text = json.dumps(payload, default=str)
    refs = set(re.findall(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}", text))
    for ref in refs:
        if uuid_re.fullmatch(ref) and ref != str(r.get("OSCAL_UUID")) and ref not in metadata_uuids:
            unresolved_uuid_refs.append((r.get("SOURCE_RECORD_ID"), r.get("ELEMENT_TYPE"), ref))

from collections import Counter
mapping_targets = Counter(r.get("CANONICAL_ELEMENT_PATH") for r in remaining)
node_types = Counter(r.get("ELEMENT_TYPE") for r in metadata_nodes)

print("=== SSP VALIDATION 05 ===")
print("VALIDATION: SSP_METADATA_REMAINING_BULK")
print("REMAINING_MAPPING_ROWS_CHECKED:", len(remaining))
print("MAPPING_TARGET_COUNTS:", dict(mapping_targets))
print("MAPPING_FAILURES:", len(mapping_failures))
print("METADATA_BRANCH_NODE_COUNTS:", dict(node_types))
print("MISSING_NODE_KEYS:", len(missing_node_keys))
print("DUPLICATE_NODE_KEYS:", len(duplicate_node_keys))
print("UUID_REQUIRED_TYPES:", sorted(uuid_required_types))
print("MISSING_REQUIRED_UUIDS:", len(missing_uuids))
print("INVALID_PAYLOAD_OBJECTS:", len(invalid_payloads))
print("METADATA_RELATED_EDGES:", len(metadata_edge_rows))
print("MISSING_EDGE_SOURCES:", len(missing_edge_sources))
print("MISSING_EDGE_TARGETS:", len(missing_edge_targets))
print("UNRESOLVED_UUID_REFS:", len(unresolved_uuid_refs))
print("MAPPING_FAILURE_SAMPLES:", mapping_failures[:10])
print("MISSING_UUID_SAMPLES:", missing_uuids[:10])
print("INVALID_PAYLOAD_SAMPLES:", invalid_payloads[:10])
print("UNRESOLVED_UUID_REF_SAMPLES:", unresolved_uuid_refs[:10])
print("NODE_SAMPLES:", [(r.get("SOURCE_RECORD_ID"), r.get("ELEMENT_TYPE"), r.get("OSCAL_UUID")) for r in metadata_nodes[:12]])

failures = (mapping_failures or missing_node_keys or duplicate_node_keys or missing_uuids
            or invalid_payloads or missing_edge_sources or missing_edge_targets or unresolved_uuid_refs)
status = "PASS" if remaining and not failures else "FAIL"
print("STATUS:", status)
if status == "PASS":
    print("VALIDATION 05 PASSED: remaining executable SSP Metadata structures are mechanically coherent in the current preview graph.")
elif not remaining:
    print("FAILURE: no remaining executable Metadata mappings were found after excluding Validations 03/04.")
