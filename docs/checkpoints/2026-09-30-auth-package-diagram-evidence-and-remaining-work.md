# Auth Package diagram evidence and remaining-work checkpoint

Date: September 30, 2026
Status: Documentation/evidence preservation only. No mapper, mapping CSV, registry, table, or Snowflake data change.

## Repository basis

Branch: simplify-metadata-boundary
Inspected commit: 53f2b11abf841b0e5971630a65e0999270501678
Inspected tree: 309deb200965cde75d7c2fc253b4f2a757af2421

Project 00_START_HERE.txt was read first. Its September 14 runtime facts are historical, not proof of later changes. The handoff coverage/gaps evidence boundary remains: the screenshot-derived workbook is partial and the historical collection-only registry rows are not a full/current registry export.

## New owner evidence preserved

Seven photographs of the organizational diagram titled "10.1 OSCAL Mappings - Auth Package" were supplied September 30. They were visually reviewed and preserved byte-for-byte in the attached project-conversation evidence archive:

OSCAL_Auth_Package_Diagram_Evidence_2026-09-30.zip

The archive includes originals/, manifest.json with SHA-256 hashes and conversation file IDs, SHA256SUMS.txt and README.md. The standalone report is OSCAL_Diagram_Checkpoint_2026-09-30.md. These artifacts are attached to the current project conversation; no automatic Project Sources insertion is claimed. Original images retain internal screen context and have not been copied into this repository by this update.

Image inventory:
1. image-1790794105582.jpg: SSP root, Import Profile, Document Metadata, System Characteristics, System Implementation, Control Implementation and adjacent cross-model boxes.
2. image-1790794127326.jpg: System Characteristics descendants/types, Security Impact Level, Status, Authorization Boundary, Network Architecture, Data Flow, reusable Property/Link region.
3. image-1790794142730.jpg: Profile, Assessment Assets, Observation, Security Assessment Results, Local Definitions and reviewed-controls region.
4. image-1790794152230.jpg: System User, Inventory Item, Component, Responsible Party, Back matter, Link and adjacent assemblies.
5. image-1790794190567.jpg: Subject of Assessment, Identified Risk, POA&M Item and partial response/observation region.
6. image-1790794202721.jpg: Task, Finding, Responsible Role, Assessment Result, Risk Response, Related Observation and POA&M/risk region.
7. image-1790794222324.jpg: Parameter Setting and another box labelled Control Implementation; incoming endpoints are partly outside the view.

These are partial overlapping photographs, not a complete model export. The diagram version, formal relationship legend and exact OSCAL schema version are not established here.

## Interpretation rules for future use

- Preserve the diagram's terminology; verify the full path before translating a display label into an executable JSON key or table name.
- Distinguish containment, UUID/role/href references and reusable types. Property and Link may be referenced by many parents; this does not make those parents related to each other or make their individual property instances identical.
- Follow both endpoints and the arrowhead. A crossing line is not a junction. Clipped or overlapping endpoints stay unresolved.
- This is a cross-model diagram. Profile, assessment/result and POA&M boxes are not automatically children of SSP.
- Repeated labels such as Control Implementation require full-path/context disambiguation. Do not derive a unique node/table from the box title alone.
- A diagram box is neither proof of current registry configuration nor proof of a populated source/target. No new table, node or mapping is authorized just because the box appears.
- Some visible labels, including system-id, document-id and Link's resource-fragment, are diagram labels to verify, not asserted current executable schema names.

## Existing evidence: what remains accepted

The September 29 owner-posted SSP COMMIT/readback checkpoint records 2,813 sources, 546,799 DIM nodes, 543,986 FACT edges, 22,976 party payload updates, no DIM inserts or FACT changes, and zero outstanding post-commit differences. Source: docs/checkpoints/2026-09-29-ssp-party-name-enrichment-committed-and-verified.md, read at the inspected commit. This is that load's graph/storage consistency evidence, not complete document conformance.

September 30 owner-reviewed examples also matched metadata title/timestamps/document identifier, dedicated status and authorization-boundary nodes, direct System Characteristics values, SAP_ID and sampled confidentiality/integrity lookup values. Displayed party UUIDs resolved to named party nodes. These checks retain their actual sample/aggregate scope.

Caveats: inner-join LIMIT samples can omit missing targets; equal role-link/name totals alone do not prove full source-user attribution, unique matches or empty-array coverage. CURATED_JSON all-null checks for FISMA_REPORTABLE, FINANCIAL_SYSTEM and PIA_REQUIRED explain current omission but do not test their populated-value mapping or independently prove upstream RAW extraction.

## Remaining work and decisions

1. Finish System Characteristics security-impact reconciliation across the 11 active source candidates, keeping missing targets and null/no-data cases visible. Source-label equality is different from a domain-approved FIPS impact interpretation. Legacy LOE labels have no demonstrated Low/Moderate/High crosswalk. Preserve current mapping until an explicit semantic decision; do not silently impose candidate precedence.
2. Decide actual field-level contributor lineage. FACT_OSCAL_SSP_FIELD_LINEAGE and portable namespaced prop/link/back-matter representations remain proposals, not implemented features. Capture actual contributors during the load; a trace rebuilt from today's source is not historical load-event lineage. Multiple agreeing source fields can contribute to one target member.
3. Reconcile diagram to runtime by full path and relation kind before declaring missing implementations. System Information, Network Architecture, Data Flow and Back matter appearing in a picture proves neither their implementation nor their absence. Use mapping/registry/current output evidence separately.
4. GroupList lookup remains pending in the reviewed SSP checkpoint. An authoritative Meta Group source and approved EEID external-ID scheme are separate unresolved items; do not infer group membership or a scheme URI.
5. Source One Assessment Results had a clean owner-posted preview before a separate Source Two ValueError. The exact current Source Two cause remains the issue to diagnose. Keep the accepted universal model-driven routing; do not hide it behind another source-selection workaround.
6. Reconcile latest owner SAP/POAM reports before recommending another run. docs/SAP_NEXT_RUN.md at this commit describes three source mappings plus support rows, with full export metadata/import-ssp/reviewed-controls incomplete and live acceptance not established there. docs/POAM_NEXT_RUN.md describes the September 13 reference-only PREVIEW and pending committed-readback evidence. These are dated guide statements, not proof that newer owner results cannot exist. Neither guide alone authorizes repeating a completed run.

## Immediate next checkpoint

Create one path-by-path coverage register for the already reviewed System Characteristics branch: diagram label, full OSCAL path, containment/reference/type relation, source field or explicit disposition, registry-configured status, runtime/persisted status, evidence date/version and remaining question. Separate implemented, configured-but-unverified, no-populated-source, excluded/deferred and genuine gaps. Do not count diagram boxes as percent complete or introduce a table-per-box design.

## Validation actually performed

Read project continuity/coverage evidence, the live branch/tree, AGENTS.md, docs/CURRENT_STATUS.md, SAP/POAM next-run guides and the September 29 SSP party-name COMMIT checkpoint. Visually reviewed the seven originals. Verified their existence, exact copied bytes using SHA-256 and archive integrity. No Snowflake execution, live registry export, new mapper tests or complete schema/conformance validation was performed. A subsequent fetch of this document is needed to establish repository read-back after creation.

## Supersession boundary

This qualifies earlier broad conversation descriptions such as "all metadata fully verified" and any inference that a diagram implies a completed mapping. It preserves successful samples and the actual committed-load evidence, accepted field names/statuses and unresolved questions. It changes no mapping decisions or runtime behavior.
