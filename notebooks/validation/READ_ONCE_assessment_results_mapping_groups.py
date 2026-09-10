# Copy into one new Python cell in the session where Cell 2 already ran.
# Reads mapping metadata and the registry only. Does not change CONFIG,
# source data, the accepted SSP graph, registry, DIM, or FACT.
import json
import re


AR_REGISTRY_READ_SQL = """
SELECT OSCAL_MODEL_KEY, NODE_PATH, ELEMENT_TYPE, PARENT_NODE_PATH,
       IS_COLLECTION, INSTANCE_KEY_RULE, PROCESS_ORDER, IS_ACTIVE, ITEM_PATH
FROM RTX_RAW_DEV.ES_ESC_GRC.OSCAL_ELEMENT_REGISTRY
WHERE UPPER(TRIM(OSCAL_MODEL_KEY::STRING)) = 'ASSESSMENT_RESULTS'
ORDER BY PROCESS_ORDER NULLS FIRST, NODE_PATH
"""


def group_assessment_mapping_metadata(artifact):
    aliases = {
        "ARCHER_FIELD_NAME": "SOURCE_FIELD_NAME", "SOURCE_FIELD": "SOURCE_FIELD_NAME",
        "MODEL": "OSCAL_MODEL", "OSCAL_PATH": "OSCAL_ELEMENT_PATH",
        "ELEMENT_PATH": "OSCAL_ELEMENT_PATH", "TARGET_FIELD_NAME": "OSCAL_FIELD_NAME",
        "OSCAL_TARGET_FIELD": "OSCAL_FIELD_NAME", "TRANSFORM_LOGIC": "TRANSFORMATION_LOGIC",
        "MAPPING_STATUS": "STATUS",
    }
    columns = [aliases.get(str(c).strip().upper(), str(c).strip().upper())
               for c in artifact.columns]
    if len(columns) != len(set(columns)):
        raise ValueError("Mapping metadata has ambiguous column aliases")
    required = {"SOURCE_FIELD_NAME", "OSCAL_MODEL", "OSCAL_ELEMENT_PATH", "MAPPING_TYPE"}
    if not required.issubset(columns):
        raise ValueError("Mapping metadata is missing: " + ", ".join(sorted(required - set(columns))))
    metadata_keys = (
        "OSCAL_MODEL", "OSCAL_ELEMENT_PATH", "OSCAL_FIELD_NAME", "MAPPING_TYPE",
        "NOTES", "MAPPING_NOTES", "TRANSFORMATION_LOGIC", "STATUS",
    )
    groups = {}
    selected_count = 0
    for original in artifact.to_dict(orient="records"):
        row = dict(zip(columns, [original[c] for c in artifact.columns]))
        # Cell 2 loads CSV metadata as strings/None. Do not stringify source data.
        def text_value(key):
            value = row.get(key)
            if value is None or (isinstance(value, float) and value != value):
                return ""
            if not isinstance(value, str):
                raise ValueError("Expected string mapping metadata in " + key)
            # Keep the artifact's target text literal, including alternatives.
            return value if key == "OSCAL_ELEMENT_PATH" else value.strip()
        model = re.sub(r"[^A-Z0-9]", "", text_value("OSCAL_MODEL").upper())
        path = text_value("OSCAL_ELEMENT_PATH").strip()
        path_matches = path == "assessment-results" or path.startswith("assessment-results.")
        if model != "ASSESSMENTRESULTS" and not path_matches:
            continue
        selected_count += 1
        signature = tuple(text_value(key) for key in metadata_keys)
        if signature not in groups:
            groups[signature] = {
                **dict(zip(metadata_keys, signature)),
                "SOURCE_FIELDS": [], "MAPPING_ROW_COUNT": 0,
                "MODEL_LABEL_MATCHES": model == "ASSESSMENTRESULTS",
                "TARGET_PATH_MATCHES": path_matches,
                # Syntax only: this does not establish registry ownership,
                # approved identity, payload semantics, or handler support.
                "SYNTACTICALLY_SINGLE_TARGET_PATH": re.fullmatch(
                    r"assessment-results(?:\.[a-z][a-z0-9-]*(?:\[\])?)*", path
                ) is not None,
            }
        group = groups[signature]
        group["SOURCE_FIELDS"].append(text_value("SOURCE_FIELD_NAME"))
        group["MAPPING_ROW_COUNT"] += 1
    ordered = sorted(groups.values(), key=lambda g: tuple(g[k] for k in metadata_keys))
    for group in ordered:
        group["SOURCE_FIELDS"].sort()  # Retain duplicate occurrences for review.
    return {
        "MAPPING_ROWS": selected_count, "GROUP_COUNT": len(ordered),
        "OPTIONAL_COLUMNS_ABSENT": [k for k in metadata_keys if k not in columns],
        "GROUPS": ordered,
    }


def read_assessment_mapping_contract(artifact, snowflake_session):
    report = group_assessment_mapping_metadata(artifact)
    registry_rows = snowflake_session.sql(AR_REGISTRY_READ_SQL).collect()
    report["REGISTRY_ROWS"] = [r.as_dict(recursive=True) for r in registry_rows]
    report["REGISTRY_ROW_COUNT"] = len(registry_rows)
    report["WRITES_EXECUTED"] = False
    report["MAPPING_COMPLETION_CLAIM"] = False
    return report


if __name__ == "__main__":
    if "mapping_artifact_pdf" not in globals() or "session" not in globals():
        raise RuntimeError("Use the notebook session where Cell 2 loaded the full mapping CSV; do not change the OSCAL model.")
    print(json.dumps(read_assessment_mapping_contract(mapping_artifact_pdf, session), indent=2, default=str))
