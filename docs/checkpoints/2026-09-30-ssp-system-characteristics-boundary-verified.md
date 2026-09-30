# SSP System Characteristics authorization-boundary verified

Date: September 30, 2026
Status: Owner-run Snowflake output reviewed. No mapper change made.

## Owner-run evidence

The direct System Characteristics field check showed all reviewed direct fields matched except authorization-boundary when it was incorrectly inspected inside the system-characteristics node.

A follow-up query inspected the dedicated authorization-boundary DIM node:
- ELEMENT_TYPE = authorization-boundary
- Archer AUTHORIZATION_BOUNDARY_DESCRIPTION matched the OSCAL authorization-boundary description for the reviewed rows.

## Interpretation

The boundary mapping is correct. The earlier null was caused by reading the wrong DIM node, not by a mapping defect.

Verified direct System Characteristics mappings now include:
- AUTHORIZATION_PACKAGE_NAME -> system-name
- ACRONYM -> system-name-short
- MISSION_PURPOSE -> description
- AUTHORIZATION_BOUNDARY_DESCRIPTION -> authorization-boundary.description
- ATOIATO_DATE -> date-authorized
- SECURITY_CATEGORY -> security-sensitivity-level

No code or mapping change is authorized by this checkpoint.
