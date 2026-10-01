# READ ONLY: sample lineage properties from canonical PREVIEW graphs.
# Handles separate property nodes and inline props without JSON text matching.
# These are in-memory graph columns, not an assumed physical DIM table schema.
import json


def read_lineage_props(nodes, edges, namespace, limit=200):
    """Return a bounded sample with the exact owning node; never perform DML."""
    from snowflake.snowpark.functions import col

    if not isinstance(namespace, str) or not namespace.strip():
        raise ValueError("A lineage namespace is required")
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    result, separate_keys = [], set()
    for record in nodes.to_local_iterator():
        node = record.as_dict() if hasattr(record, "as_dict") else dict(record)
        payload = node["METADATA_JSON"]
        payload = json.loads(payload) if isinstance(payload, str) else payload
        if not isinstance(payload, dict):
            raise ValueError("Expected an object node payload")
        separate = payload.get("ns") == namespace and "name" in payload and "value" in payload
        props = [payload] if separate else payload.get("props", [])
        if not isinstance(props, list):
            raise ValueError("Expected an inline props array")
        for prop in props:
            if not isinstance(prop, dict):
                raise ValueError("Expected a property object")
            if prop.get("ns") != namespace:
                continue
            if "name" not in prop or "value" not in prop:
                raise ValueError("Property requires name and value")
            if separate:
                separate_keys.add(node["NODE_KEY"])
            result.append({
                "SOURCE_SYSTEM_NAME": node["SOURCE_SYSTEM_NAME"],
                "SOURCE_TABLE_NAME": node["SOURCE_TABLE_NAME"],
                "SOURCE_RECORD_ID": node["SOURCE_RECORD_ID"],
                "NODE_KEY": node["NODE_KEY"],
                "ELEMENT_PATH": node["ELEMENT_PATH"],
                "OWNER_NODE_KEY": None if separate else node["NODE_KEY"],
                "PROPERTY_LOCATION": "separate" if separate else "inline",
                "PROPERTY_NAMESPACE": prop["ns"],
                "PROPERTY_NAME": prop["name"],
                "PROPERTY_GROUP": prop.get("group"),
                "PROPERTY_CLASS": prop.get("class"),
                "PROPERTY_VALUE": prop["value"],
            })
            if len(result) == limit:
                break
        if len(result) == limit:
            break
    if separate_keys:
        selected = edges.filter(col("FK_TARGET_ELEMENT_HASH").isin(sorted(separate_keys)))
        parents = {}
        for edge in selected.select("FK_TARGET_ELEMENT_HASH", "FK_SOURCE_ELEMENT_HASH", "DEPENDENCY_TYPE").to_local_iterator():
            child = edge["FK_TARGET_ELEMENT_HASH"]
            if edge["DEPENDENCY_TYPE"] != "CONTAINS" or child in parents:
                raise ValueError("Lineage property requires exactly one containment parent")
            parents[child] = edge["FK_SOURCE_ELEMENT_HASH"]
        if set(parents) != separate_keys:
            raise ValueError("Lineage property is missing its containment parent")
        for item in result:
            if item["PROPERTY_LOCATION"] == "separate":
                item["OWNER_NODE_KEY"] = parents[item["NODE_KEY"]]
    return result


# When pasted after Cell 7, inspect the routes already built; no source reload.
if globals().get("MODEL_GRAPHS"):
    for route, graph in MODEL_GRAPHS.items():
        rows = read_lineage_props(
            graph["nodes"], graph["edges"], graph["context"]["config"]["LINEAGE_PROPERTY_NS"]
        )
        print("Lineage sample", route, "rows:", len(rows))
        for row in rows:
            print(row)
