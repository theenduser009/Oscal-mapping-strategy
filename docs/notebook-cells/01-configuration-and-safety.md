# Cell 1 - Shared configuration and safety guard

Run this cell first. It defines the candidate Archer fields and prevents the inspection cells from running when writes are enabled.

> Confirm `EXECUTE_WRITES = False` before running.

```python
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
```

[Back to the cell library](README.md) · [Next: Cell 2](02-sample-populated-props.md)