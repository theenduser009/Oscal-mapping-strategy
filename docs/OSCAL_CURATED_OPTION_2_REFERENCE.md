# OSCAL CURATED - Option 2 — Reference

## Source artifact

This page records the architecture/reference material shown in the **OSCAL CURATED - Option 2** design artifact (Version 1.0, created July 7, 2026).

## What is OSCAL?

OSCAL provides machine-readable data models for standardizing, structuring, and expressing security and compliance information. The design artifact describes the move from static/manual documents toward Compliance-as-Code.

Reference: NIST OSCAL overview — https://pages.nist.gov/OSCAL/learn/concepts/layer/overview/

## Design patterns captured in the artifact

### 1. Factless Fact Table

The proposed curated design uses a graph-oriented dimensional pattern:

- Dimension rows represent OSCAL nodes/elements.
- Fact rows represent edges/relationships between those nodes.
- The fact table does not require numeric measures.
- This supports coverage, membership, dependency, and many-to-many relationships.
- Keeping OSCAL elements at their appropriate grain preserves the semantic grain of the source model.

This is consistent with the DIM-node / FACT-edge architecture implemented by the OSCAL mapper.

### 2. Binary Hash Key

The design proposes deterministic hash-based surrogate keys derived from stable natural/business identity rather than database sequences.

Benefits called out by the artifact include:

- deterministic identity;
- decentralized/idempotent processing;
- parallel ingestion support;
- no dependence on locking database sequences; and
- no centralized key lookup registry solely for surrogate-key generation.

### 3. Semantic Knowledge Graph

The combination of factless relationship facts and deterministic node keys provides the foundation for a semantic knowledge graph. The artifact anticipates integration with semantic/ontology tooling and future indexing for RAG-style GRC applications.

## OSCAL structures visible in the reference diagrams

The accompanying design diagrams show mappings/relationships across structures including:

- System Security Plan (SSP)
- System Implementation
- Control Implementation
- System Characteristics
- Document Metadata
- POA&M
- Assessment Result
- Findings
- Observations
- Implemented Requirements
- Parameter Settings
- Components and related component structures

## Relationship to the current mapper

This page is **reference documentation**, not evidence that every OSCAL branch is currently production-complete. Current implementation state, validation results, mapping gaps, and write readiness remain governed by the repository's status/checkpoint documentation and executable validation results.

The current mapper architecture follows the same central pattern: **nodes in DIM, relationships in FACT, deterministic identity, registry-driven hierarchy, and validation before writes**.

## Screenshot provenance

This page was created from screenshots supplied on September 10, 2026 of the existing architecture/modeling artifacts, including the page labeled **OSCAL CURATED - Option 2** and the broader **10.1 OSCAL Mappings** diagrams.
