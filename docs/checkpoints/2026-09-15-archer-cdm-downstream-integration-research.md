# Archer CDM downstream integration research

Date: 2026-09-15
Repository branch: `simplify-metadata-boundary`
Branch head inspected before this update: `2a0e018c6222b39d8f0d28800ba58373684aed64`

## Purpose

Preserve the Archer CDM research discussed in the OSCAL project so later modeling work does not depend on chat memory alone. This document is architectural/research evidence only. It does not approve new OSCAL mappings, change runtime code, change registry rows, or prove any Snowflake execution.

## Core Archer CDM context

The current Archer conceptual model under discussion contains a core Assessment & Testing area around Business/SBU/Entity/Facility context, Compliance Engagement, Control Procedure, Control Testing Result, Control Standard, Evidence, and policy/authoritative-source context.

RTX-specific policy relationships currently under review are:

- Control Procedure -> Policy Level 3
- Policy Level 3 -> Control Standard
- Direct Control Procedure <-> Control Standard only if RTX Archer stores that relationship independently
- Control Testing Result -> Control Standard for the specific standard evaluated/failed, if the RTX source stores that relationship

These relationships must remain semantically distinct. A Procedure -> Standard path derivable through Policy Level 3 should not automatically be duplicated as a physical relationship unless Archer stores it independently.

## Important version distinction

The RTX implementation appears to use a Policy Level 1 -> Policy Level 2 -> Policy Level 3 hierarchy. That hierarchy should be modeled as an RTX/current-client implementation detail, not as a claim about the newest generic Archer Core Compliance architecture.

Current public Archer material has evolved toward flatter policy structures and regulatory constructs such as authoritative sources/citations/obligations/sub-obligations around Control Standards. Public Archer documentation is useful for conceptual architecture, but RTX Archer metadata is authoritative for actual physical relationships, field direction, and cardinality.

## Issues Management branch

Treat Issues Management as a downstream domain attached to the core rather than redesigning the core around it.

Primary concepts:

- Finding
- Remediation Plan
- Remediation Plan Status Update
- Exception Request

Conceptual workflow:

- A Finding can originate from a control test, assessment, audit, risk activity, monitoring activity, or another supported source.
- Remediate path: Finding -> one or more Remediation Plans -> Remediation Plan Status Updates.
- Accept-risk path: Finding -> Exception Request.

Do not force Control Testing Result to be the mandatory sole parent of Finding.

Do not collapse Finding and Risk into one entity.

### Deviation

`Deviation` remains RTX-specific/unverified in this draft. Do not place it as a parent or child of Finding until actual RTX Archer metadata confirms the relationship.

## Evidence Repository

Evidence should be treated as a cross-cutting documentation/evidence concept. It may support control implementation, testing, compliance engagement evidence requests, remediation, or exception decisions depending on the RTX implementation.

Do not assume Evidence Repository belongs only under Control Testing Result.

## A&A / Public Sector branch

Primary concepts under review:

- Authorization Package
- Allocated Control
- Finding
- POA&M
- Milestone

Keep `Allocated Control` distinct from `Control Procedure` unless RTX metadata proves they are the same business object. Their business grains are different: Control Procedure is a reusable/master testing or control-procedure concept, while Allocated Control is closer to an instantiated/assigned control in an authorization context.

Conceptual direction only:

`Authorization Package -> Allocated Control -> assessment/authorization context -> Finding -> POA&M -> Milestone`

Do not lock the arrows or cardinalities from public documentation alone. RTX relationship metadata must establish actual cross-reference direction and whether links are single-value or multi-value.

## Risk Register

Keep Risk Register as a separate risk domain. Conceptually risks may relate to controls and business/system context, while findings are the issue/remediation mechanism.

Do not add a direct `Finding <-> Risk Register` relationship unless RTX Archer metadata confirms it.

## Legacy DPF crosswalk

Treat legacy DPF Control Standards as a migration/crosswalk concern rather than as another current-state hierarchy level.

Recommended conceptual pattern:

`LEGACY_DPF_CONTROL_STANDARD -> CONTROL_STANDARD_CROSSWALK -> CURRENT_CONTROL_STANDARD`

Do not contaminate the current Control Standard entity with many legacy identifiers unless a specific source requirement demands it. Crosswalk cardinality and attributes remain proposed until actual DPF/FCP evidence is reviewed.

## OSCAL intersection

Keep Archer CDM and OSCAL warehouse models distinct:

`ARCHER CDM -> mapping/transformation -> OSCAL representation`

Do not merge the source CDM and OSCAL model simply because concepts overlap.

Relevant current OSCAL evidence:

- `FINDINGS` exists in the Assessment Results mapping source with proposed target `assessment-results.results[].findings[]`, but remains DEFERRED pending finding identity/reference semantics.
- SSP Control Implementation includes fields such as `ALLOCATED_CONTROLS`, `CONTROL_STANDARDS`, `MASTER_CONTROLS`, `ALLOCATED_CONTROLS_AUTHORIZATION_PACKAGE`, inheritance fields, control-assessor fields, and POA&M-related counts, but all 42 Control Implementation mapping rows remain DEFERRED.
- POA&M is conceptually downstream and currently has an approved source reference mapping, but accepted project evidence is still PREVIEW only, not verified COMMIT/readback.

## Evidence and modeling rules

1. Public Archer documentation establishes useful conceptual architecture, not RTX physical truth.
2. RTX Archer metadata must determine actual field relationships, direction, cardinality, FK versus XREF, and single-value versus multi-value behavior.
3. Explicit Archer relationships may be modeled independently even if another path can derive the same business association.
4. Derived relationships should not be materialized automatically if doing so creates conflicting truths.
5. Keep current-state entities clean; isolate legacy crosswalk concerns.
6. Preserve domain grain: Finding != Risk, Allocated Control != Control Procedure unless proven, Exception Request != Remediation Plan.

## Current OSCAL evidence boundaries that still apply

- Historical SSP committed/read-back acceptance does not prove the later `DAILY_LOSS_AMOUNT_FROM_OUTAGE` mapping.
- Historical AR30 committed/read-back acceptance does not prove later AR32/null-preservation/leading-underscore changes.
- POA&M has accepted PREVIEW evidence, not verified COMMIT/readback.
- Assessment Plan setup code and corrected registry SQL do not prove successful live setup or a completed preview/commit.
- The 42 SSP Control Implementation mapping rows remain deferred until reviewed and explicitly approved.

## Immediate next checkpoint

Before changing Erwin cardinalities or enabling new OSCAL mappings, inspect RTX Archer metadata for the downstream applications and relationships. Capture, at minimum:

- application/table
- primary identifier
- related-record field
- target application
- single-value versus multi-value
- relationship direction
- whether the relationship is directly stored or only derivable

Priority objects:

- Control Procedure
- Policy Level 3
- Control Standard
- Control Testing Result
- Finding
- Remediation Plan
- Remediation Plan Status Update
- Exception Request
- Deviation
- Authorization Package
- Allocated Control
- Risk Register
- POA&M
- Milestone
- Legacy DPF Control Standard

This checkpoint should be treated as read-only evidence collection. Do not infer missing values or approve mappings from conceptual similarity alone.
