# Universal registry-driven source-field lineage props

Date: September 30, 2026
Branch: simplify-metadata-boundary
Status: IMPLEMENTED IN REPOSITORY; NOT YET OWNER-RUN IN SNOWFLAKE.

## Decision

Source-field lineage is a universal mapper behavior.

There are no per-field lineage mapping rows, no security-impact-only branch, and
no manual EMIT_SOURCE_LINEAGE flag.

For every approved source FIELD mapping, the compiler asks one generic question:

What is the nearest registered OSCAL props[] extension point that encloses this
target element?

If such a props[] collection exists, and the source field actually maps a value,
the mapper emits one lineage prop there.

## Universal property shape

{
  "name": "source-field",
  "ns": "urn:company:oscal:lineage:v1",
  "class": "<normalized canonical OSCAL target path>",
  "value": "<exact SOURCE_FIELD_NAME>"
}

Example:

{
  "name": "source-field",
  "ns": "urn:company:oscal:lineage:v1",
  "class": "system-security-plan.system-characteristics.security-impact-level.security-objective-integrity",
  "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
}

## Rules

- Same behavior for every approved FIELD mapping.
- CONFIG support values do not claim Archer source-field lineage.
- Missing/omitted source values do not generate lineage.
- Explicit source nulls generate lineage only when the mapped field's existing
  null policy actually preserves that null.
- Multiple agreeing source fields produce multiple lineage props.
- Existing target-conflict validation remains unchanged and fails closed.
- Native OSCAL payloads remain unchanged.
- If no registered enclosing props[] extension point exists, the mapper does
  not invent an OSCAL structure.

## Clean mapper implementation

Cell 1:
- one global lineage namespace only.

Cell 3:
- computes generic source-field -> nearest props[] lineage routes from the
  already-compiled mapping rows and registry.

Cell 4:
- emits the generic lineage prop when the source field is actually mapped.

ARCHER_OSCAL_MAPPINGS.csv:
- restored to the normal mapping rows;
- no duplicate lineage rows;
- no lineage-specific per-field columns.

## Repository validation

- Maintained Cells 1, 3 and 4 updated.
- cells_v2 regenerated from maintained cells.
- monolithic NB_ARCHER_OSCAL_MAPPER_V1.py regenerated.
- focused universal-lineage unit tests added.
- GitHub Actions run 36771095246 confirmed all five universal-lineage tests pass.
- The generated-notebook synchronization check also passed.
- Compared with the pre-lineage baseline workflow, this change introduced no
  additional failing tests; the branch still has unrelated pre-existing failures.
- universal read-only SSP preview helper:
  notebooks/validation/15_ssp_universal_lineage_prop_preview.py

## Snowflake status

No live Snowflake execution was performed from this chat.
No target DML is claimed.

## Next action

Run SSP PREVIEW only (EXECUTE_WRITES=False), then run the universal lineage
preview helper and review the generated props before any COMMIT.
