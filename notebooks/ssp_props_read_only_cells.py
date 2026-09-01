"""Read-only notebook cells for OSCAL SSP system-characteristics.props[].

Prerequisites supplied by the existing SSP notebook:

- ``source_df``
- ``_parse_source_json(record)``
- ``resolve_json_path(source_obj, field)``

These cells inspect Archer source values only. They do not write to the SSP
DIM or FACT tables.
"""

# %% Cell 1 - shared configuration and safety guard

from collections import Counter


PROP_FIELDS = [
    "FISMA_REPORTABLE",
    "FINANCIAL_SYSTEM",
    "MISSION_CRITICAL",
    "CRITICAL_INFRASTRUCTURE",
    "PACKAGE_TYPE",
    "HELPER_PTA_CALC",
    "PACKAGE_TYPE_HELPER_CALC",
    "PIA_REQUIRED",
    "INFORMATION_CLASSIFICATION",
    "DAILY_LOSS_AMOUNT_FROM_OUTAGE",
]


def _assert_read_only() -> None:
    """Stop inspection if the notebook write flag is enabled."""

    if globals().get("EXECUTE_WRITES", False):
        raise RuntimeError(
            "Read-only props inspection requires EXECUTE_WRITES = False."
        )


def _has_source_value(value) -> bool:
    """Return True for source values that should be inspected."""

    return value not in (None, "", [], {})


# %% Cell 2 - show up to 10 SSPs with populated candidate prop fields

_assert_read_only()

shown = 0

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)
    populated = {}

    for field in PROP_FIELDS:
        value = resolve_json_path(source_obj, field)

        if _has_source_value(value):
            populated[field] = value

    if populated:
        print("\nSOURCE_RECORD_ID:", record["SOURCE_RECORD_ID"])

        for field, value in populated.items():
            print(field, "=", value)

        shown += 1

    if shown >= 10:
        break


# %% Cell 3 - count populated candidate prop fields across all SSPs

_assert_read_only()

counts = Counter()

for record in source_df.to_local_iterator():
    source_obj = _parse_source_json(record)

    for field in PROP_FIELDS:
        value = resolve_json_path(source_obj, field)

        if _has_source_value(value):
            counts[field] += 1

print("=== POPULATED PROP FIELD COUNTS ===")

for field in PROP_FIELDS:
    print(field, "=", counts[field])
