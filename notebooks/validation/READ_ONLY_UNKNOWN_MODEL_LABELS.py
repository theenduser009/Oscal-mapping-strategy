# Read-only mapping-label report: copy this ENTIRE file into one temporary
# Snowflake PYTHON cell in the SAME session as the failed Cell Seven run.
# Run only this cell; post its complete printed output to GitHub status.
# No edits, IDs, table names, SQL, database writes, or mapper reruns are needed.
# Reads existing mapping/registry metadata only, never Archer source payloads.
# Requires the current Cells One-Three and PIPELINE_REPORT from Cell Seven.
# Verified with synthetic metadata; the live label report remains pending.

def show_unknown_model_labels():
    from collections import Counter
    import json

    source = PIPELINE_REPORT["active_group"]["source"]
    aliases = _model_aliases(MODEL_CONTRACTS)

    for original in REGISTRY_INPUT_ROWS:
        row = _meta_row(original)
        path, model = _registry_path(row), _registry_model(row)
        parent = (row.get("PARENT_NODE_PATH") or
                  row.get("PARENT_ELEMENT_PATH") or row.get("PARENT_PATH"))
        if _metadata_active(row) and path and "." not in path and not parent and model:
            aliases.setdefault(_model_token(model), model)

    counts = Counter()
    for original in MAPPING_INPUTS[source]:
        row = _meta_row(original)
        label = row.get("OSCAL_MODEL") or ""
        token = _model_token(label)
        if token and token not in aliases and token not in {"extensionproperty", "extensionproperties"}:
            counts[(str(label), str(row.get("OSCAL_ELEMENT_PATH") or ""))] += 1

    print(json.dumps({
        "unknown_model_rows": sum(counts.values()),
        "model_path_pairs": [
            {"model_label": label, "target_path": path, "row_count": count}
            for (label, path), count in sorted(counts.items())
        ]
    }, indent=2, ensure_ascii=True))

show_unknown_model_labels()
