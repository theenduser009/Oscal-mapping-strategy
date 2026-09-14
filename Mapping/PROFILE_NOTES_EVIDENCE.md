# OSCAL Profile Notes evidence

Date posted: **2026-09-14**

Transcribed from the supplied mapping-workbook screenshot. This file records
visible evidence only and does not approve a mapping or change the mapper,
mapping CSV, registry, or Snowflake data.

## Visible worksheet evidence

The screenshot shows `Mapping Type` as `Extension Property` and provides two
expanded Notes blocks.

### Conditional Profile routing

The first Notes block says that the target depends on the behavior specified by
the row's data and may map to one of three operations inside an OSCAL Profile:

- `profile/imports`: when `ADD_OVERLAY` introduces an entirely new external
  regulatory baseline or overlay file into the current catalog.
- `profile/merge`: when the value dictates how controls from different
  overlays combine, resolve overlaps, or establish control priority.
- `profile/modify/alters`: when the row contains tailored changes, including
  specialized organizational parameters, custom text additions, or removal of
  baseline control requirements.

### Profile import example

The second Notes block says that when a recommendation dictates the control set
imported into a full OSCAL ecosystem, it maps to the import array of an OSCAL
Profile model.

The visible example is:

```json
{
  "profile": {
    "id": "system-recommended-profile",
    "imports": [
      {
        "href": "https://nist.gov",
        "include-all": {}
      }
    ]
  }
}
```

## Evidence boundary

The screenshot does not display the Archer field-name or row-number columns, so
it does not independently prove which exact worksheet rows own these expanded
Notes cells. The example values are illustrative and are not approved runtime
identifiers, references, or persisted values.
