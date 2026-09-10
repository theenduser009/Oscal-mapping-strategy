# SSP control count — proposed Excel correction, not implemented

Status: mapping-owner approval required. No mapper, registry, DIM or FACT changes.

## Evidence from the newly supplied Excel Notes

The three screenshots posted on 2026-09-10 show the filter
`SSP - Control Implementation`, with 50 of 609 rows displayed. The large Notes
example aligned with row 66 concerns
`COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS`; the full field name is
established by the existing artifact transcription because the screenshot's
source label is clipped. `CONTROL_SET_VERSION_NUMBER` is row 38 above it.

The visible heading recommends Option 1: nest inside
`control-implementation/props`. The example proposes the property name
`controls-missing-implementation-details-count`. The company namespace,
UUID, description and value `"14"` are sample scaffolding, not production data
or approved constants. The remarks describe a calculated count of gaps in
control narrative documentation; their final text is clipped. The path and
datatype columns are blank. Other visible Notes repeatedly suggest properties
or a calculation based on implemented-requirement counts.

The [live evidence summary](../live-snowflake-results.md) records these images,
but omits the detailed Option 1 example; this checkpoint captures that detail.

## Why the original example is not an executable standard mapping

The pinned [OSCAL SSP 1.2.3 definition](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_ssp_metaschema.xml)
allows description, set-parameters and implemented-requirements directly inside
control-implementation. It does not allow the example's props or UUID there.
The user did not approve a custom schema/extension. Do not implement that path
silently or claim it is standard-conformant.

## Recommended correction for the mapping owner

| Contract item | Proposal, not approved |
| --- | --- |
| OSCAL model | SSP |
| Excel business grouping | Retain SSP - Control Implementation |
| Archer field | COUNT_OF_CONTROLS_WITHOUT_IMPLEMENTATION_DETAILS |
| Proposed target path | system-security-plan.metadata.props[] |
| Mapping type | Extension Property |
| Property name | controls-missing-implementation-details-count |
| Proposed value policy | Use the existing Archer count; serialize the validated count as a string; do not recalculate or hard-code 14 |
| Namespace | Mapping owner must supply/approve the organizational namespace; do not copy the example company URL |

The pinned [metadata definition](https://github.com/usnistgov/OSCAL/blob/v1.2.3/src/metaschema/oscal_metadata_metaschema.xml)
supports metadata props. Using it for this document-wide summary is an
engineering recommendation, not a schema-mandated business placement.
The Notes do not settle whether Archer already calculated the count or the
mapper is expected to calculate it; the proposed direct-source policy needs
approval along with the destination and namespace.

## One action needed

Ask the mapping owner to approve or correct the proposed destination, value
policy and namespace in the Excel row. This is not a request to rerun Snowflake.
Do not alter the original Excel evidence, invent missing control records or
broaden this proposal to all 50 rows. Current accepted mappings and the 2,813
assembled mapped-scope documents remain unchanged. This proposal adds zero
completed mappings until approved, implemented and accepted.
