# Source 2 Component Definition registry read-back verified — 2026-09-18

Repository branch: `simplify-metadata-boundary`
Repository head inspected before this checkpoint: `e525ab3dae78fa6eb91bf582a4475022f64c9aee`

## Owner-provided Snowflake evidence

Owner-provided screenshot on 2026-09-18 shows the Component Definition registry branch present and active.

Visible Component Definition rows:

1. `component-definition`
   - model: `COMPONENT_DEFINITION`
   - parent: NULL
   - collection: FALSE
   - identity: `SINGLETON`
   - process order: 1
   - active: TRUE
   - operator: `object`
   - UUID policy: `node`

2. `component-definition.components[]`
   - parent: `component-definition`
   - collection: TRUE
   - identity: `SOURCE_RECORD_ID`
   - process order: 2
   - active: TRUE
   - operator: `optional-record`
   - UUID policy: `node`

3. `component-definition.components[].props[]`
   - parent: `component-definition.components[]`
   - collection: TRUE
   - identity: `SOURCE_FIELD_NAME+VALUE`
   - process order: 3
   - active: TRUE
   - item path: `$`
   - operator: `properties`
   - UUID policy: `omit`

This is screenshot/read-back evidence; the project does not have direct Snowflake access.

## Important technical blocker before runtime PREVIEW

NIST OSCAL Component Definition v1.2.3 requires each `components[]` item to contain:
- `uuid`
- `type`
- `title`
- `description`

The mapper can generate the UUID, but the current Source 2 mapping sheet does not provide an approved mapping for the required component `type`, `title`, and `description` members for the Source-level Component Definition grain.

The current Component Definition worksheet rows only describe policy links/properties under a component. Creating a component containing only `props[]` would not be a schema-complete OSCAL component.

Therefore no Component Definition runtime rows or PREVIEW are promoted by this checkpoint.

## Next decision required

Obtain the exact source-field-to-OSCAL mapping for the required Component members:
- component `type`
- component `title`
- component `description`

A candidate such as `SOURCE_NAME -> title` or `SOURCE_DESCRIPTION -> description` must not be treated as approved unless the mapping owner confirms it. The component type must likewise not be invented.

Once these required members are resolved, add the Component Definition model/storage contract and executable Source 2 mappings, then PREVIEW before COMMIT.
