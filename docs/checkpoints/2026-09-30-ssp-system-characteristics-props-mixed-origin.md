# SSP system-characteristics props contain mixed business-origin fields

Date: September 30, 2026
Status: Owner-run target query reviewed. No mapper change made.

## Observed target behavior

A direct system-characteristics -> props query returned a very large result set and included prop names such as:
- add-additional-controls
- allocated-controls
- mission-critical
- critical-infrastructure
- information-system-type
- package-type

The current runtime mapping CSV explains this: some rows whose business section is "SSP - Control Implementation" are intentionally targeted to system-security-plan.system-characteristics.props[] for source-preservation purposes.

Examples:
- ADD_ADDITIONAL_CONTROLS -> system-security-plan.system-characteristics.props[]
- ALLOCATED_CONTROLS -> system-security-plan.system-characteristics.props[]

Therefore querying all props beneath system-characteristics does not return only the core System Characteristics business fields.

## Interpretation

This is not evidence that the DIM/FACT joins are wrong. It is a consequence of the current accepted source-preservation mappings.

It does mean that "all props under system-characteristics" should not be interpreted as "all Archer System Characteristics fields." The target branch contains mixed-origin extension properties.

## Current core System Characteristics prop set

For focused inspection use only:
- information-system-type
- fisma-reportable
- financial-system
- mission-critical
- critical-infrastructure
- package-type
- authorization-decision
- pia-required

Read-only helper:
sql/qa/SSP_SYSTEM_CHARACTERISTICS_CORE_PROPS_ONLY.sql

No runtime mapping change is authorized by this checkpoint.
