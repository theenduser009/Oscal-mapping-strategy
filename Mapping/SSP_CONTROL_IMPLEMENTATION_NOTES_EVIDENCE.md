# SSP Control Implementation Notes evidence

Date posted: **2026-09-14**

Transcribed from the supplied mapping-workbook screenshot. This file records
visible evidence only and does not approve a mapping or change the mapper,
mapping CSV, registry, or Snowflake data.

## Visible worksheet evidence

- The formula bar displays `BASELINE_CONTROLS_ALLOCATED_DATE`.
- Repeated Notes text reads: `May map to props[] or calculated from implemented-requirements count`.
- The expanded Notes cell begins: `Option 1: Nest inside control-implementation/props (Recommended for SSPs)`.
- The visible explanation says that placing the summary metric inside the
  system's control-implementation block provides immediate insight into SSP
  completeness. The remainder of that sentence is cut off in the screenshot.

The screenshot does not display the left-side row number or field-name column
beside the expanded Notes cell, so it does not independently prove which exact
row owns the expanded example.

## Visible example payload

```json
{
  "system-security-plan": {
    "control-implementation": {
      "uuid": "7a8b9c0d-1e2f-3a4b-5c6d-8c53a6dbcf5e",
      "description": "System-wide security control mappings and operational parameters.",
      "props": [
        {
          "name": "controls-missing-implementation-details-count",
          "ns": "https://yourcompany.com",
          "value": "14",
          "remarks": "Calculated value representing active gaps in control narrative documentation."
        }
      ],
      "implemented-requirements": [
        "..."
      ]
    }
  }
}
```

This is a Notes-column example, not proof of an approved runtime target,
calculation rule, property namespace, or persisted value.
