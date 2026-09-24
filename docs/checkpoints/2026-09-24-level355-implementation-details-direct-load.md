# Level-355 implementation details direct-load decision — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head after mapping update: `2a13cd397b12231a955634c5602a16faa7c7acac`

## Decision
Stop the second-batch profiling loop for `IMPLEMENTATION_DETAILS`.

The field is now APPROVED as:
`system-security-plan.control-implementation.implemented-requirements[].description`

Runtime contract:
- source = Level-355 joined record from `ARCHER_CONTENT_ALLOCATED_CONTROLS_CONTROL_RAW`
- join = top-level CONTENT_ID to Authorization Package CONTENT_ID
- child identity = ALLOCATED_CONTROL_ID
- transform = text
- null/blank = omitted
- lookup binding = allocated-controls

`OVERALL_IMPLEMENTATION_DETAILS` remains separate/deferred so two different source
fields do not silently compete for the same OSCAL description member.

## Evidence basis
- Source-owner guidance identified implementation detail as substantive Allocated Control content.
- Owner-provided Snowflake samples showed populated implementation text on some Level-355 control rows and nulls on others.
- First Level-355 control-id batch is COMMIT/read-back verified.

## Next action
Refresh the mapping CSV in the current notebook session, then run:
- Cell 2
- Cell 3
- Cell 7 in PREVIEW mode

Cells 4-6 do not need to be rerun if the same session still has the current joined-record code loaded.

Use the PREVIEW update count as the validation for this field. No separate RUN_NOW profile is required.
