# NIST OSCAL Control Mapping Model review and project alignment

Date: September 30, 2026
Status: Official NIST sources reviewed and compared against the current OSCAL repository. No runtime mapper behavior changed by this checkpoint.

## Official NIST sources

Control Mapping conceptual overview:
https://pages.nist.gov/OSCAL/learn/concepts/layer/control/mapping/

OSCAL v1.2.3 Control Mapping Model reference:
https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/mapping/

OSCAL v1.2.3 full release reference:
https://pages.nist.gov/OSCAL-Reference/models/v1.2.3/

Model documentation landing:
https://pages.nist.gov/OSCAL-Reference/models/

## What NIST says this model is for

The Control Mapping Model represents machine-readable relationships between controls or control statements from different authoritative resources such as standards, regulations, frameworks, catalogs, and profiles.

It is not a replacement for an SSP, Assessment Results, POAM, Assessment Plan, Catalog, Profile, or Component Definition model.

Core Control Mapping structure includes:
- mapping-collection
- metadata
- provenance
- mapping
- source-resource
- target-resource
- map entries
- source / target members
- explicit relationship semantics such as equivalent-to, equal-to, subset-of, superset-of, intersects-with, and no-relationship

The model is intended to reference source and target controls rather than restating/duplicating the source control content.

## Current project alignment

### Aligned

The current project already follows several OSCAL design principles that are compatible with NIST guidance:
- distinct OSCAL model boundaries are maintained for SSP, Assessment Results, POAM, Assessment Plan, Catalog, and Profile;
- deterministic UUID / node / relationship identity is used;
- metadata, roles, parties, responsible-party references, props, and remarks are represented through OSCAL model structures rather than flattened into one generic document;
- control implementation in SSP is represented as implemented-requirements, not as catalog-to-catalog mapping;
- source lineage and business identifiers are kept distinct from OSCAL identity;
- current runtime mapping preserves source data without inventing unsupported semantics;
- OSCAL version is pinned to v1.2.3.

### Not yet implemented

The repository does not currently contain a native Control Mapping Model implementation. A repository search found no runtime use of:
- mapping-collection
- source-resource
- target-resource
- equivalent-to
- subset-of
- superset-of
- intersects-with

Therefore the internal ARCHER_OSCAL_MAPPINGS.csv should not be described as an OSCAL Control Mapping artifact. It is an ETL / transformation contract from Archer source fields into OSCAL models.

### Where Control Mapping should matter

The strongest fit is future Source Two / authoritative-source control harmonization and control crosswalk work, where one control or statement in one source is related to a control or statement in another source.

Before finalizing that architecture, review whether current planned Source Two crosswalk outputs should produce a proper OSCAL mapping-collection with explicit source-resource, target-resource, map entries, relationship, method/rationale, provenance, status, and confidence where approved.

Do not retrofit Source One SSP field mappings into Control Mapping Model merely because NIST recommended reviewing it.

## Current conclusion

Source One architecture is broadly aligned with OSCAL model separation and should continue.

The main gap relative to the newly requested NIST review is that the project has not yet implemented the Control Mapping Model for cross-source control relationships. That is an architectural item for Source Two/control crosswalk scope, not a defect in the current Source One SSP pipeline.

## Next action

Before starting or finalizing Source Two control crosswalk implementation:
1. document the current source/target control-resource concepts;
2. compare them to OSCAL v1.2.3 mapping-collection semantics;
3. decide whether Source Two should emit a native Control Mapping artifact;
4. only then update metadata/registry/code.
