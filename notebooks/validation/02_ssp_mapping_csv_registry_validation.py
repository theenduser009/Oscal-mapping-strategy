# %% SSP VALIDATION 02 — mapping CSV + live registry compatibility
# Date: 2026-09-15
# READ ONLY. NO TARGET DML / DDL.
#
# HOW TO RUN
# 1) Use the same Snowflake notebook/session as the seven-cell mapper.
# 2) Run Cells 01, 02 and 03 first with SELECTED_MODELS = ("SSP",)
#    and CONFIG["EXECUTE_WRITES"] = False.
# 3) Paste/run this as the next temporary validation cell.
#
# WHY THIS USES CELL 3
# Cell 2 reads the actual ARCHER_OSCAL_MAPPINGS.csv uploaded to the notebook
# and the live OSCAL_ELEMENT_REGISTRY. Cell 3 already contains the authoritative
# routing/contract compiler. This validation reports that compiler's evidence
# instead of re-implementing different validation rules.

from collections import Counter, defaultdict

# ------------------------------------------------------------
# 02A. Locate the compiled SSP context
# ------------------------------------------------------------
ssp_contexts = [
    c for c in MAPPING_CONTEXTS
    if c["config"]["OSCAL_MODEL"] == "SSP"
]

if len(ssp_contexts) != 1:
    raise ValueError(f"Expected exactly one SSP mapping context; found {len(ssp_contexts)}")

ctx = ssp_contexts[0]
route = ctx["routing_report"]
compiled = ctx["mapping_rows"]
registry = ctx["registry_rows"]

# ------------------------------------------------------------
# 02B. Independent read-only inventory from actual CSV rows
# ------------------------------------------------------------
raw_rows = MAPPING_INPUTS[ctx["source_key"]]
ssp_alias_tokens = {
    _model_token("SSP"),
    *(_model_token(v) for v in MODEL_CONTRACTS["SSP"].get("MODEL_ALIASES", ())),
}

ssp_csv_rows = [
    _meta_row(r) for r in raw_rows
    if _model_token((_meta_row(r)).get("OSCAL_MODEL")) in ssp_alias_tokens
]

status_counts = Counter((r.get("EXECUTION_STATUS") or "BLANK") for r in ssp_csv_rows)

approved_rows = [r for r in ssp_csv_rows if r.get("EXECUTION_STATUS") == "APPROVED"]
deferred_rows = [r for r in ssp_csv_rows if r.get("EXECUTION_STATUS") == "DEFERRED"]
excluded_rows = [r for r in ssp_csv_rows if r.get("EXECUTION_STATUS") == "EXCLUDED"]
blocked_guard_rows = [r for r in ssp_csv_rows if r.get("EXECUTION_STATUS") == "BLOCKED_IF_POPULATED"]

# ------------------------------------------------------------
# 02C. Checks that should be zero for executable SSP rows
# ------------------------------------------------------------
missing_source_field = [
    r for r in approved_rows + blocked_guard_rows
    if not str(r.get("SOURCE_FIELD_NAME") or "").strip()
]

missing_runtime_path = [
    r for r in approved_rows + blocked_guard_rows
    if not str(r.get("RUNTIME_TARGET_PATH") or "").strip()
]

missing_transform = [
    r for r in approved_rows + blocked_guard_rows
    if not str(r.get("TRANSFORM_ID") or "").strip()
]

missing_rule_id = [
    r for r in approved_rows + blocked_guard_rows
    if not str(r.get("RULE_ID") or "").strip()
]

unsupported_transform = [
    r for r in approved_rows + blocked_guard_rows
    if str(r.get("TRANSFORM_ID") or "").strip() not in METADATA_TRANSFORM_IDS
]

rule_counts = Counter(
    str(r.get("RULE_ID") or "").strip()
    for r in approved_rows + blocked_guard_rows
    if str(r.get("RULE_ID") or "").strip()
)
duplicate_rule_ids = sorted(rule for rule, count in rule_counts.items() if count > 1)

# Every compiled executable mapping must be owned by a live registered SSP node.
registered_paths = {_registry_path(r) for r in registry}
unregistered_compiled_owner = [
    r for r in compiled
    if r.get("OWNER_ELEMENT_PATH") not in registered_paths
]

# Explicitly deferred/excluded rows must not have entered the compiled executable plan.
compiled_rule_ids = {r["RULE_ID"] for r in compiled}
nonexec_with_rule = [
    r for r in deferred_rows + excluded_rows
    if r.get("RULE_ID") and r.get("RULE_ID") in compiled_rule_ids
]

# ------------------------------------------------------------
# 02D. Branch inventory for executable SSP mappings
# ------------------------------------------------------------
def _branch(path):
    path = str(path or "")
    if path.startswith("system-security-plan.metadata"):
        return "METADATA"
    if path.startswith("system-security-plan.system-characteristics"):
        return "SYSTEM_CHARACTERISTICS"
    if path.startswith("system-security-plan.system-implementation"):
        return "SYSTEM_IMPLEMENTATION"
    if path.startswith("system-security-plan.import-profile"):
        return "IMPORT_PROFILE"
    if path.startswith("system-security-plan.control-implementation"):
        return "CONTROL_IMPLEMENTATION"
    if path.startswith("system-security-plan.back-matter"):
        return "BACK_MATTER"
    if path == "system-security-plan":
        return "ROOT"
    return "OTHER"

branch_counts = Counter(_branch(r.get("CANONICAL_ELEMENT_PATH")) for r in compiled)
transform_counts = Counter(r.get("TRANSFORM_ID") for r in compiled)
owner_counts = Counter(r.get("OWNER_ELEMENT_PATH") for r in compiled)

# ------------------------------------------------------------
# 02E. Compact PASS/FAIL
# ------------------------------------------------------------
mechanical_failures = {
    "MISSING_SOURCE_FIELD": len(missing_source_field),
    "MISSING_RUNTIME_TARGET_PATH": len(missing_runtime_path),
    "MISSING_TRANSFORM_ID": len(missing_transform),
    "MISSING_RULE_ID": len(missing_rule_id),
    "UNSUPPORTED_TRANSFORM_ID": len(unsupported_transform),
    "DUPLICATE_RULE_ID": len(duplicate_rule_ids),
    "UNREGISTERED_COMPILED_OWNER": len(unregistered_compiled_owner),
    "DEFERRED_OR_EXCLUDED_COMPILED": len(nonexec_with_rule),
    "CELL3_BLOCKED_ROWS": int(route.get("BLOCKED_ROWS", 0)),
}

status = "PASS" if all(v == 0 for v in mechanical_failures.values()) and route.get("STATUS") == "READY" else "FAIL"

VALIDATION_02_REPORT = {
    "VALIDATION": "02_SSP_MAPPING_CSV_REGISTRY",
    "STATUS": status,
    "CELL3_ROUTE_STATUS": route.get("STATUS"),
    "CSV_SSP_ROWS": len(ssp_csv_rows),
    "CSV_STATUS_COUNTS": dict(status_counts),
    "COMPILED_EXECUTABLE_ROWS": len(compiled),
    "REGISTERED_SSP_ROWS_USED_BY_CONTEXT": len(registry),
    "BRANCH_COUNTS": dict(sorted(branch_counts.items())),
    "TRANSFORM_COUNTS": dict(sorted(transform_counts.items(), key=lambda x: str(x[0]))),
    "MECHANICAL_FAILURES": mechanical_failures,
    "ROUTING_REASON_COUNTS": route.get("REASON_COUNTS", {}),
    "ROUTING_SEVERITY_COUNTS": route.get("SEVERITY_COUNTS", {}),
}

print("\n=== SSP VALIDATION 02 ===")
for key, value in VALIDATION_02_REPORT.items():
    print(f"{key}: {value}")

print("\n=== EXECUTABLE MAPPINGS BY OWNER NODE ===")
for path, count in sorted(owner_counts.items()):
    print(f"{count:>3}  {path}")

# ------------------------------------------------------------
# 02F. Failure samples only when needed
# ------------------------------------------------------------
if status != "PASS":
    failure_samples = {
        "missing_source_field": [r.get("SOURCE_FIELD_NAME") for r in missing_source_field[:10]],
        "missing_runtime_path": [r.get("SOURCE_FIELD_NAME") for r in missing_runtime_path[:10]],
        "missing_transform": [r.get("SOURCE_FIELD_NAME") for r in missing_transform[:10]],
        "missing_rule_id": [r.get("SOURCE_FIELD_NAME") for r in missing_rule_id[:10]],
        "unsupported_transform": [
            (r.get("SOURCE_FIELD_NAME"), r.get("TRANSFORM_ID"))
            for r in unsupported_transform[:10]
        ],
        "duplicate_rule_ids": duplicate_rule_ids[:10],
        "unregistered_owner": [
            (r.get("SOURCE_FIELD_NAME"), r.get("OWNER_ELEMENT_PATH"))
            for r in unregistered_compiled_owner[:10]
        ],
        "nonexec_compiled": [
            (r.get("SOURCE_FIELD_NAME"), r.get("EXECUTION_STATUS"), r.get("RULE_ID"))
            for r in nonexec_with_rule[:10]
        ],
        "cell3_issues": route.get("ISSUES", [])[:10],
    }
    print("\n=== FAILURE SAMPLES ===")
    for key, value in failure_samples.items():
        if value:
            print(f"{key}: {value}")
else:
    print("\nVALIDATION 02 PASSED: current executable SSP CSV mappings compile cleanly against the live registry.")

# Important boundary:
# PASS here means mapping metadata/registry mechanics are internally consistent.
# It does NOT yet prove that each mapping is semantically correct according to
# OSCAL. That is Validation 03+ (field semantics and generated payload tests).
