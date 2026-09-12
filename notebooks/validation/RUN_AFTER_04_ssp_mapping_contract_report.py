# HISTORICAL — legacy field-dispatch workflow only; not for metadata-v1.
# Current workflow: Cell 3 routing reports and Cell 7 mapping coverage.
# Run once in the existing session after Cell 4 (also works after failed Cell 7).
# Reads only in-memory Excel mapping metadata. No Snowflake query or source data.
# This is contract evidence, NOT a populated-record count or mapper validation.
import json



def _require_legacy_dispatch_context():
    """Do not classify executable metadata with the retired field dispatcher."""
    state = globals()
    contexts = state.get("MAPPING_CONTEXTS", [])
    if not isinstance(contexts, (list, tuple)):
        contexts = []
    contexts = list(contexts) + [state.get("_default_context")]
    contracts = state.get("MODEL_CONTRACTS", {})
    if not isinstance(contracts, dict):
        contracts = {}
    metadata_context = any(
        isinstance(context, dict) and (
            context.get("model_contract", {}).get("POLICY") == "metadata-v1"
            or isinstance(context.get("compiled_plan"), dict)
        )
        for context in contexts
    )
    metadata_contract = any(
        isinstance(contract, dict) and contract.get("POLICY") == "metadata-v1"
        for contract in contracts.values()
    )
    rows = state.get("CANONICAL_MAPPING_ROWS", [])
    metadata_rows = isinstance(rows, (list, tuple)) and any(
        isinstance(row, dict) and bool(row.get("TRANSFORM_ID")) for row in rows
    )
    if metadata_context or metadata_contract or metadata_rows:
        raise RuntimeError(
            "Historical legacy-only diagnostic cannot run on metadata-v1. "
            "Use Cell 3 routing_report and Cell 7 mapping coverage instead."
        )

def build_mapping_contract_report(mapping_rows, classifier):
    report = []
    fields = (
        "SOURCE_FIELD_NAME", "OSCAL_MODEL", "OSCAL_ELEMENT_PATH",
        "CANONICAL_ELEMENT_PATH", "OWNER_ELEMENT_PATH", "OSCAL_FIELD_NAME",
        "FIELD_RELATIVE_PATH", "MAPPING_TYPE", "STATUS",
        "NOTES", "MAPPING_NOTES", "TRANSFORMATION_LOGIC",
    )
    for row_number, mapping_row in enumerate(mapping_rows, start=1):
        try:
            classifier(mapping_row)
        except (KeyError, TypeError, ValueError) as error:
            output = {"CANONICAL_ROW_NUMBER": row_number}
            output.update({field: mapping_row.get(field) for field in fields})
            output["REJECTION_REASON"] = str(error)
            report.append(output)
    return report


def run_mapping_contract_report():
    _require_legacy_dispatch_context()
    rows = globals().get("CANONICAL_MAPPING_ROWS")
    classifier = globals().get("_mapping_handler_for_row")
    if not isinstance(rows, list) or not rows or not callable(classifier):
        raise RuntimeError("This report needs the state from Cells 3 and 4.")
    if globals().get("CONFIG", {}).get("EXECUTE_WRITES", False):
        raise RuntimeError("Keep EXECUTE_WRITES = False.")
    report = build_mapping_contract_report(rows, classifier)
    print("Canonical mapping rows inspected:", len(rows))
    print("Rows rejected by handler contract (regardless of source data):", len(report))
    print("Includes original Excel paths, mapping types, Notes and transformation logic.")
    print("No source values read. No database queries or writes. Not a graph acceptance.")
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return report


mapping_contract_report_result = run_mapping_contract_report()
