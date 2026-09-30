# NIST OSCAL provenance / field-lineage research

Date: September 30, 2026
Repository branch: simplify-metadata-boundary
Repository head before this checkpoint: 6c86bcf0756e19ea4be389bd736e1f00cae93e9d
Status: Research checkpoint only. No mapper/table change implemented.

## Question

How does NIST OSCAL officially represent the provenance of a final SSP value back to a source-system field such as an Archer column?

## Confirmed NIST findings

1. OSCAL v1.2.3 is the latest patch release as of September 2026. NIST states that v1.2.3 is a patch release and does not introduce model changes or new model features.
   - https://pages.nist.gov/OSCAL/about/blog/
   - https://github.com/usnistgov/OSCAL/releases

2. In the SSP model, `security-impact-level` contains the three semantic values:
   - `security-objective-confidentiality`
   - `security-objective-integrity`
   - `security-objective-availability`

   The object itself does not provide a generic source-column/source-field lineage child.
   - https://pages.nist.gov/OSCAL-Reference/models/v1.2.1/system-security-plan/json-reference/

3. The parent `system-characteristics` object supports OSCAL `props` and `links`.

4. NIST's official extension tutorial identifies namespaced `prop` and `link` as the standard extension mechanisms for data that is not formally represented by a core OSCAL model. A property namespace must be an absolute URI. `class` and `group` can qualify/associate locally defined properties.
   - https://pages.nist.gov/OSCAL/learn/tutorials/general/extension/

5. NIST model references explicitly caution against using `remarks` for arbitrary data and direct implementers to use `prop` or `link` instead.

6. OSCAL does contain dedicated provenance constructs where provenance is part of the domain semantics. For example, Assessment Results uses `origin` / `actor` to identify a person, tool, or assessment platform that produced/gathered assessment evidence.
   - https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/assessment-results/xml-definitions/

7. NIST's profile-resolution process uses source-profile provenance at the document level (for example source-profile metadata/link concepts). The processing specification explicitly focuses on deterministic inputs/outputs rather than prescribing implementation-level storage details.
   - https://pages.nist.gov/OSCAL/learn/concepts/processing/profile-resolution/

8. NIST's own SSP examples encode FIPS 199-style objective values as `fips-199-low`, `fips-199-moderate`, and `fips-199-high`.
   - https://github.com/usnistgov/oscal-content/blob/main/examples/ssp/xml/ssp-example.xml
   - https://github.com/usnistgov/oscal-content/blob/main/examples/ssp/xml/oscal_leveraging-example_ssp.xml

## Interpretation for this project

There is no NIST-defined generic SSP field such as `source-field-name` or `source-column` that directly attaches an Archer column name to `security-objective-integrity`.

A NIST-compatible design has two layers:

### Core OSCAL semantic value
Keep the native SSP member focused on the final OSCAL value.

### Provenance/lineage
Use one or both of:
- implementation-side lineage storage (for example a Snowflake lineage fact table); and/or
- OSCAL extension data using organization-namespaced `prop` / `link` on an enclosing object that supports extensions.

Because `security-impact-level` itself does not carry `props` or `links`, member-level lineage placed inside the OSCAL document would need to be represented on an enclosing extensible object such as `system-characteristics`, with local `class`/`group` semantics, or via a link to an external/back-matter lineage resource.

Those local lineage semantics would be organization-defined, not NIST-standard field names.

## NIST-aligned candidate pattern

Example only; not implemented:

```json
{
  "security-impact-level": {
    "security-objective-integrity": "fips-199-low"
  },
  "props": [
    {
      "name": "source-field",
      "ns": "https://example.org/ns/oscal/lineage",
      "class": "security-objective-integrity",
      "group": "lineage-1",
      "value": "INTEGRITY_CONTROL_CATEGORY_OVERRIDE"
    },
    {
      "name": "mapping-rule",
      "ns": "https://example.org/ns/oscal/lineage",
      "class": "security-objective-integrity",
      "group": "lineage-1",
      "value": "ssp:INTEGRITY_CONTROL_CATEGORY_OVERRIDE:7"
    }
  ]
}
```

This follows the OSCAL extension mechanism, but the exact namespace/property names/classes/groups are local governance decisions.

## Current project implication

The previously proposed `FACT_OSCAL_SSP_FIELD_LINEAGE` remains compatible with OSCAL because NIST does not prescribe how a warehouse must persist transformation lineage. If portability of lineage with exported OSCAL documents is required, a namespaced `prop`/`link` layer can be added separately without changing the core semantic members.

## Important follow-up

Separate from lineage, the project should review whether the current values `low` and legacy LOE labels should remain as-is or whether FIPS-199 semantics require the NIST example convention `fips-199-low|moderate|high`. This is a semantic mapping decision and must not be silently changed without owner/domain approval.

## Next action

Decide the lineage portability requirement:
- warehouse-only lineage, or
- warehouse lineage plus OSCAL-carried namespaced provenance.

No implementation change should be made until that decision is accepted.
