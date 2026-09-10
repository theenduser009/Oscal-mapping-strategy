# Read-only SSP controlled-vocabulary crosswalk review
#
# Run after Mapper V1 Cell 7 in the same Snowflake Python notebook session.
# This cell prints only aggregate Archer select-value labels and occurrence
# counts for security impact and status. It never prints Archer IDs, source
# record IDs, or complete payloads, and it performs no database writes.

from collections import Counter
import json


if "CONFIG" not in globals():
    raise RuntimeError("Run Mapper V1 Cells 1 through 7 first.")
if CONFIG.get("EXECUTE_WRITES", False):
    raise RuntimeError(
        "Set EXECUTE_WRITES = False before running this review."
    )
if "final_nodes_df" not in globals() or final_nodes_df is None:
    raise RuntimeError("Cell 7 final_nodes_df is not available.")
if "run_result" not in globals() or not run_result.get(
    "validation_passed", False
):
    raise RuntimeError("Cell 7 validation must pass before this review.")
if "ARCHER_VALUE_LOOKUP" not in globals():
    raise RuntimeError("Cell 2 Archer select-value lookup is not available.")


CROSSWALK_SECURITY_PATH = (
    "system-security-plan.system-characteristics.security-impact-level"
)
CROSSWALK_STATUS_PATH = (
    "system-security-plan.system-characteristics.status"
)
CROSSWALK_OBJECTIVES = (
    "security-objective-confidentiality",
    "security-objective-integrity",
    "security-objective-availability",
)


def _crosswalk_payload(value):
    if value is None:
        return {}
    if hasattr(value, "as_dict"):
        return value.as_dict(recursive=True)
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _crosswalk_flatten(value):
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(_crosswalk_flatten(item))
        return result
    return [value]


def _crosswalk_labels(value):
    """Return lookup metadata labels, never raw or unresolved Archer IDs."""
    extracted = _extract_reference_ids(value)
    items = _crosswalk_flatten(extracted)
    labels = []
    for item in items:
        if item is None:
            labels.append("<empty>")
            continue
        if isinstance(item, (dict, list)):
            labels.append("<unresolved-structured-value>")
            continue

        key = str(item).strip()
        if key in ARCHER_VALUE_LOOKUP:
            label = ARCHER_VALUE_LOOKUP.get(key)
            label = str(label).strip() if label is not None else ""
            labels.append(label if label else "<blank-lookup-label>")
            continue

        # Permit an already normalized OSCAL token, but never echo arbitrary
        # source strings that were not proven to be controlled-vocabulary
        # metadata from ARCHER_VALUE_LOOKUP.
        normalized = "-".join(key.lower().replace("_", "-").split())
        if normalized in {
            "low",
            "moderate",
            "high",
            "fips-199-low",
            "fips-199-moderate",
            "fips-199-high",
            "operational",
            "under-development",
            "under-major-modification",
            "disposition",
            "other",
            "legacy-loe-a",
            "legacy-loe-a-+-dfars",
            "legacy-loe-b",
            "legacy-loe-b-+-dfars",
            "legacy-loe-c",
            "legacy-loe-c-+-dfars",
            "legacy-loe-d",
            "legacy-loe-d-+-dfars",
        }:
            labels.append(key)
        else:
            labels.append("<unresolved-value-not-displayed>")
    return labels or ["<empty>"]


security_by_objective = {
    objective: Counter() for objective in CROSSWALK_OBJECTIVES
}
status_labels = Counter()
node_counts = Counter()

for row in final_nodes_df.select(
    "ELEMENT_PATH",
    "METADATA_JSON",
).filter(
    col("ELEMENT_PATH").in_(
        [CROSSWALK_SECURITY_PATH, CROSSWALK_STATUS_PATH]
    )
).to_local_iterator():
    path = str(row["ELEMENT_PATH"])
    payload = _crosswalk_payload(row["METADATA_JSON"])

    if path == CROSSWALK_SECURITY_PATH:
        node_counts["security-impact nodes"] += 1
        for objective in CROSSWALK_OBJECTIVES:
            if objective not in payload:
                security_by_objective[objective]["<missing>"] += 1
                continue
            for label in _crosswalk_labels(payload.get(objective)):
                security_by_objective[objective][label] += 1

    elif path == CROSSWALK_STATUS_PATH:
        node_counts["status nodes"] += 1
        if "state" not in payload:
            status_labels["<missing>"] += 1
            continue
        for label in _crosswalk_labels(payload.get("state")):
            status_labels[label] += 1


def _crosswalk_print(title, counter):
    print("\n===", title, "===")
    for label, count in sorted(
        counter.items(), key=lambda item: (-item[1], item[0].lower())
    ):
        print(label, "=", count)


print("=" * 74)
print("SSP READ-ONLY CONTROLLED-VOCABULARY CROSSWALK REVIEW")
print("Only lookup metadata labels and aggregate counts are displayed.")
print("=" * 74)

for name, count in sorted(node_counts.items()):
    print(name, "=", count)

for objective in CROSSWALK_OBJECTIVES:
    _crosswalk_print(objective, security_by_objective[objective])

_crosswalk_print("status.state", status_labels)

print("\n=== SAFETY RESULT ===")
print("READ-ONLY CROSSWALK REVIEW COMPLETE")
print("EXECUTE_WRITES =", CONFIG.get("EXECUTE_WRITES", False))
print("No source/Archer IDs or complete payloads were displayed.")
print("No DIM/FACT writes or permanent objects were created.")

