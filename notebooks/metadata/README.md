# Mapper settings and mapping input

Field rules now live once in [ARCHER_OSCAL_MAPPINGS.csv](../../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
The [column guide](../../Mapping/MAPPING_COLUMNS.md) explains the readable
execution columns and retained source Notes. No field-specific Python edit or
second catalog entry is needed for another approved mapping using supported
operators.

[mapper_contract.v1.json](mapper_contract.v1.json) remains a **structural settings
file**, not a second field-rule table. It contains source/lookup bindings,
element operators, model identities and verified destinations that are not
fully represented in the current live registry. It no longer contains
MAPPING_RULES, PATH_RULES or EXCLUDED_FIELDS.

This is a migration of duplicated field rules, not completion of the final
catalog-free design. Do not replace the structural settings with guessed
registry defaults or paste the old field rules into Python.

## Responsibilities

| Input | Owns |
| --- | --- |
| Mapping CSV | Source field, original model/path/type/Notes, execution status, runtime target and reusable conversion parameters. |
| Live registry | Active paths, hierarchy, collection flags, instance-key rules and processing order. |
| Structural settings | Source table bindings, lookups, element operations and verified target contracts not fully captured in the registry. |
| Shared seven cells | Input selection, compilation, transformations, graph construction, key checks and guarded persistence. |

Cell Three compiles one in-memory plan. It never executes prose Notes, evaluates
metadata as Python/SQL, or calls a separate SSP/AR mapper. Original paths remain
visible alongside runtime targets. Unknown transformations, incompatible
parameters, duplicate rule identities and contradictory model paths block.
Deferred and excluded rows do not execute.

## Scope and compatibility

The maintained CSV has the 147 reviewed occurrences plus one pre-existing
populated-value guard. Exactly 60 approved rules and that guard are executable.
All eleven CIA rules and seventeen AR mappings preserve accepted behavior.
Unresolved Notes, control paths, workflow fields and AR candidates remain
unapproved. The review workbook is the unchanged compilation snapshot, not
another executable input.

The prior catalog is frozen under tests/fixtures solely as a regression oracle.
Cell Three temporarily retains its older metadata input branch for compatibility
tests; the deployed settings contain no rules for that branch. Retiring this
branch and consolidating the remaining structural settings are unfinished
simplification work, not requests for more owner approval.

Normal writes remain disabled. SSP's earlier DEV reload is still accepted;
the old-row reduction remains unexplained. AR has no verified destination and
remains graph-preview-only. Local parity does not establish a new Snowflake
run, daily-load acceptance, or full OSCAL schema completeness.

See [current status](../../docs/CURRENT_STATUS.md) before running the notebook.
