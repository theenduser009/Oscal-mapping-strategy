# %% Cell 5 - Build nodes, exact containment, and contribution-backed lineage


def _create_canonical_graph_frame(rows, kind):
    columns = (
        "NODE_KEY", "ELEMENT_PATH", "PARENT_NODE_PATH", "INSTANCE_KEY", "PARENT_INSTANCE_KEY", "OSCAL_UUID",
        "ELEMENT_TYPE", "METADATA_JSON", "SOURCE_SYSTEM_NAME", "SOURCE_TABLE_NAME",
        "SOURCE_RECORD_ID", "DW_PIPELINE_RUN_ID", "DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ",
    ) if kind == "nodes" else (
        "EDGE_KEY", "FK_SOURCE_ELEMENT_HASH", "FK_TARGET_ELEMENT_HASH", "DEPENDENCY_TYPE",
        "SOURCE_OSCAL_UUID", "TARGET_OSCAL_UUID",
    )
    schema = StructType([StructField(name, TimestampType(TimestampTimeZone.TZ)
                        if name in {"DW_LOAD_TIMESTAMP", "DW_LOAD_TIMESTAMP_TZ"} else StringType())
                         for name in columns])
    return session.create_dataframe([tuple(row.get(name) for name in columns) for row in rows], schema=schema)


def _lineage_pointer(tokens):
    # RFC 6901 JSON Pointer: no slug normalization and no guessed array indices.
    return "".join("/" + token.replace("~", "~0").replace("/", "~1") for token in tokens)


def _attach_record_lineage(pending, parents, registry, append_node, context):
    """Use only surviving instances. Parent lookup is by node identity, not name.

    A repeated target may be described from an ancestor only with its real
    payload UUID. Without an unambiguous portable target, report a coverage gap
    and prohibit COMMIT; never guess a parent, add a schema path, or invent a URL.
    """
    plan, config, report = context["compiled_plan"], context["config"], context["graph_report"]
    emitted = set()
    for target, contribution in sorted(pending, key=lambda item: (
            item[0]["NODE_KEY"], item[1]["rule_id"], item[1]["target"], _json_text(item[1]["origin"]))):
        host, segments, crossed_collection = target, [], False
        props_path, inline = None, False
        while host is not None:
            path = host["ELEMENT_PATH"]
            inline = plan["elements"][path]["operator"] == "observations"
            candidate = path + ".props[]"
            if inline or (candidate in registry and plan["elements"][candidate]["operator"] == "properties"):
                props_path = None if inline else candidate
                break
            parent = parents.get(host["NODE_KEY"])
            if parent is not None:
                member = path[len(parent["ELEMENT_PATH"]) + 1:]
                crossed_collection |= plan["elements"][path]["parameters"]["registry_contract"]["is_collection"]
                segments.insert(0, member.removesuffix("[]"))
            host = parent
        native_uuid = json.loads(target["METADATA_JSON"]).get("uuid")
        if native_uuid != target["OSCAL_UUID"]:
            native_uuid = None  # A source string is not proof of a valid object reference.
        reason = ("NO_REGISTERED_PROPS_OWNER" if host is None else
                  "REPEATED_TARGET_WITHOUT_NATIVE_UUID" if crossed_collection and not native_uuid else None)
        if reason:
            report["LINEAGE_GAPS"] += 1
            if len(report["LINEAGE_GAP_SAMPLES"]) < 25:
                report["LINEAGE_GAP_SAMPLES"].append({"reason": reason, "rule_id": contribution["rule_id"],
                                                       "target_path": target["ELEMENT_PATH"]})
            continue
        tokens = contribution["target"].split(".") if contribution["target"] else []
        pointer = _lineage_pointer(tokens if crossed_collection else segments + tokens)
        origin = contribution["origin"]
        identity = ["source-attribution-v1", target["NODE_KEY"], contribution["rule_id"],
                    contribution["target"], origin]
        group = "source-" + uuid.uuid5(uuid.NAMESPACE_URL, _json_text(identity)).hex
        if group in emitted:
            continue
        emitted.add(group)
        members = [("source-field", contribution["source_field"]), ("target-path", pointer)]
        if crossed_collection:
            members.append(("target-uuid", native_uuid))
        if origin is not None:
            members.extend((name, origin[key]) for name, key in (
                ("source-system", "source_system"), ("source-table", "source_table"),
                ("source-record-id", "source_record_id")))
        properties = [_oscal_prop(name, value, config.get("LINEAGE_PROPERTY_NS"), group)
                      for name, value in members]
        if not config.get("LINEAGE_PROPERTY_NS"):
            raise ValueError("LINEAGE_PROPERTY_NS must be an absolute URI")
        if inline:
            payload = json.loads(host["METADATA_JSON"])
            # Existing observations put their business property first. The
            # recorded /props/0/value pointer is relative to that exact instance.
            payload.setdefault("props", []).extend(properties)
            host["METADATA_JSON"] = _json_text(payload)
        else:
            for prop in properties:
                append_node(registry[props_path], {
                    "instance_key": "lineage:" + group + ":" + prop["name"], "payload": prop,
                    "parent_instance_key": host["INSTANCE_KEY"]})
        report["LINEAGE_GROUPS"] += 1
    config["LINEAGE_GAP_COUNT"] = report["LINEAGE_GAPS"]


def build_oscal_graph(source_df, canonical_mapping_df, element_registry_df,
                      model_key, source_system, source_table, context=None):
    context = _prepare_model_context(context, model_key, source_system, source_table)
    if getattr(_metadata_instances, "_oscal_mapper_release", None) != "lean-csv-registry-v5-lineage":
        raise ValueError("Run the matching Cell 4 before Cell 5")
    config, report = context["config"], context["graph_report"]
    registry = _canonical_registry_rows(element_registry_df, model_key, context)
    registry_by_path = {row["element_path"]: row for row in registry}
    root = context["model_contract"]["ROOT_PATH"]
    context["root_element_type"] = registry_by_path[root]["element_type"]
    _metadata_prepare(source_df, context)
    nodes, edges, records = [], [], set()
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    for record in source_df.to_local_iterator():
        record_id = record["SOURCE_RECORD_ID"]
        if not isinstance(record_id, str) or not record_id.strip() or record_id != record_id.strip():
            raise ValueError("Source record identity must be a nonblank canonical string")
        if record_id in records:
            raise ValueError("Duplicate source record identity")
        records.add(record_id)
        report["SOURCE_RECORDS"] += 1
        source = _metadata_parse(record, context)
        by_path, parents, pending = {}, {}, []

        def append_node(row, item):
            path, parent_path, key = row["element_path"], row["parent_path"], item["instance_key"]
            instances = by_path.setdefault(path, {})
            if not isinstance(key, str) or not key.strip() or key in instances:
                raise ValueError("Element instances require unique nonblank identities")
            parent = None
            if parent_path:
                candidates = by_path.get(parent_path, {})
                parent_key = item.get("parent_instance_key")
                parent = candidates.get(parent_key) if parent_key is not None else (
                    next(iter(candidates.values())) if len(candidates) == 1 else None)
                if parent is None:
                    raise ValueError("Missing or ambiguous parent instance for " + path)
            node_key = _deterministic_hash(config["IDENTITY_VERSION"], source_system,
                                           source_table, record_id, model_key, path, key)
            node_uuid = _metadata_uuid(path, item, source_system, source_table, record_id, model_key, context)
            payload = _metadata_payload(path, item["payload"], node_uuid, context)
            if not isinstance(payload, dict):
                raise ValueError("An element payload must be an object")
            node = {
                "NODE_KEY": node_key, "ELEMENT_PATH": path, "PARENT_NODE_PATH": parent_path, "INSTANCE_KEY": key,
                "PARENT_INSTANCE_KEY": item.get("parent_instance_key"), "OSCAL_UUID": node_uuid,
                "ELEMENT_TYPE": row["element_type"], "METADATA_JSON": _json_text(payload),
                "SOURCE_SYSTEM_NAME": source_system, "SOURCE_TABLE_NAME": source_table,
                "SOURCE_RECORD_ID": record_id, "DW_PIPELINE_RUN_ID": config["RUN_ID"],
                "DW_LOAD_TIMESTAMP": timestamp, "DW_LOAD_TIMESTAMP_TZ": timestamp,
            }
            instances[key] = node
            nodes.append(node)
            parents[node_key] = parent
            if parent is not None:
                edges.append({
                    "EDGE_KEY": _deterministic_hash("edge-v1", parent["NODE_KEY"], node_key, "CONTAINS"),
                    "FK_SOURCE_ELEMENT_HASH": parent["NODE_KEY"], "FK_TARGET_ELEMENT_HASH": node_key,
                    "DEPENDENCY_TYPE": "CONTAINS", "SOURCE_OSCAL_UUID": parent["OSCAL_UUID"],
                    "TARGET_OSCAL_UUID": node_uuid,
                })
            pending.extend((node, contribution) for contribution in item.get("contributions", ()))

        for row in registry:
            by_path.setdefault(row["element_path"], {})
            for item in _metadata_instances(source, record_id, row, context):
                append_node(row, item)
        _attach_record_lineage(pending, parents, registry_by_path, append_node, context)
        _metadata_record_complete({path: list(values.values()) for path, values in by_path.items()}, context)
    if not nodes:
        raise ValueError("Graph builder produced no nodes")
    node_frame = _create_canonical_graph_frame(nodes, "nodes")
    edge_frame = _create_canonical_graph_frame(edges, "edges")
    _metadata_finish(nodes, edges, context)
    return node_frame, edge_frame


build_oscal_graph._oscal_mapper_release = "lean-csv-registry-v5-lineage"
