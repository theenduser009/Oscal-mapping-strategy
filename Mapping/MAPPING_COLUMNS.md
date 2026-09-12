# Mapping input

[ARCHER_OSCAL_MAPPINGS.csv](ARCHER_OSCAL_MAPPINGS.csv) is the single maintained
field-mapping input for this migration. Open it in Excel or a text editor.
It preserves the 147 reviewed source occurrences, one explicitly labelled
existing populated-value guard, and three existing required support values.
Those support rows replace structural settings, not newly completed Excel rows.
This is not the missing full 608-row file.

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
| VALUE_SOURCE | FIELD (default) reads the named source path; CONFIG reads the explicitly named Cell One setting. There is no fallback between them. |
| VALUE_REQUIRED | true requires a nonempty value before and after conversion. Blank/false preserves optional behavior; 0 and false are values, not missing data. |

Blank optional operation columns mean no extra option. They are not JSON.
Notes remain evidence, not executable code. Changing prose alone does not
silently change a transformation.

## Preserved scope

There are 60 original approved mappings (43 SSP and 17 AR), three existing
support rules, one populated-value guard, 85 deferred rows and two excluded
helpers: 151 rows total. The three support rules source metadata title from
AUTHORIZATION_PACKAGE_NAME and the two versions from Cell One settings.
These counts are not a claim that a complete OSCAL model is accepted.

Accepted CIA legacy values, status remarks, component hydration, property naming,
and AR observation behavior are preserved. Recorded Notes conflicts remain
unresolved, including the shared CIA note, PTA helper and package-type naming.
The guard for RECOMMENDED_SECURITY_CATEGORY comes from accepted implementation
evidence, not a fabricated source-sheet row.

## What remains separate

The [extended registry](../docs/REGISTRY_METADATA_SETUP.md) defines element
operators, parent identity, UUID/empty/assembly policies and required-mapping
gates. Cell One holds visible source/lookup locations and verified destinations.
No JSON catalog is maintained or read. The one-time DEV registry migration is
prepared, not live-verified; normal DIM/FACT writes remain disabled.

See [current status](../docs/CURRENT_STATUS.md) before any notebook run.
