# Mapping input

[ARCHER_OSCAL_MAPPINGS.csv](ARCHER_OSCAL_MAPPINGS.csv) is the single maintained
field-mapping input for this migration. Open it in Excel or a text editor.
It preserves the 147 reviewed source occurrences and adds one explicitly
labelled existing populated-value guard. It is not the missing full 608-row file.

The first five columns retain the source field, original model label, original
OSCAL path, mapping type and Notes. Source document, line and original Excel row
are retained at the right. The [review workbook](REVIEW.md) remains the unchanged
compilation snapshot; it is not a second executable mapping input.

## Executable columns

| Column | Meaning |
| --- | --- |
| EXECUTION_STATUS | APPROVED executes. BLOCKED_IF_POPULATED rejects a populated value. DEFERRED and EXCLUDED do not execute. |
| TRANSFORM_ID | Reusable conversion, such as text, date, archer-select, security-objective or scalar-score. |
| RUNTIME_TARGET_PATH | Exact accepted target used by the registry-based compiler, without overwriting the original path. |
| RULE_ID | Stable review identity, not a generated database key. |
| SOURCE_KEY | Source binding. Rows from different sources cannot be mixed. |
| ALLOWED_VALUES | Additional accepted legacy labels, separated by a vertical bar. Used by security-objective. |
| VALUE_MAP | Status crosswalk: source=target pairs separated by a vertical bar. |
| OTHER_REMARKS_TEMPLATE | Status remarks with one literal {label} placeholder. |
| ROLE_ID / ROLE_TITLE | Accepted role reference details. |
| REFERENCE_TYPE / LOOKUP_KEY / DESCRIPTION_REQUIRED | Reference kind, approved lookup binding and required-description flag. |

Blank optional operation columns mean no extra option. They are not JSON.
Notes remain evidence, not executable code. Changing prose alone does not
silently change a transformation.

## Preserved scope

There are 60 approved mappings (43 SSP and 17 AR), one existing populated-value
guard, 85 deferred rows and two excluded helpers. The count is executable rules,
not a claim that every populated field or complete OSCAL model is accepted.

Accepted CIA legacy values, status remarks, component hydration, property naming,
and AR observation behavior are preserved. Recorded Notes conflicts remain
unresolved, including the shared CIA note, PTA helper and package-type naming.
The guard for RECOMMENDED_SECURITY_CATEGORY comes from accepted implementation
evidence, not a fabricated source-sheet row.

## What remains separate

The reduced [structural settings](../notebooks/metadata/mapper_contract.v1.json)
still define source tables, lookup bindings, element operators, identity rules
and verified destinations that the current registry does not fully contain.
It no longer contains field rules, field-specific path rewrites or exclusions.
This removes duplicated field-rule maintenance, but does not yet remove every
JSON dependency. No registry schema change or database write is part of this work.

See [current status](../docs/CURRENT_STATUS.md) before any notebook run.
