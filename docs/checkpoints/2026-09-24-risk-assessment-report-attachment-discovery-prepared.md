# Source One RISK_ASSESSMENT_REPORT attachment-resolution discovery prepared — 2026-09-24

## Repository basis
- Branch: `simplify-metadata-boundary`
- Head before helper update: `eaae71de62acb7fd8228953287d3d513f2583272`

## Current accepted evidence
`RISK_ASSESSMENT_REPORT` remains DEFERRED in the runtime CSV.

Current mapping metadata records:
- model = Assessment Results
- mapping type = Attachment Reference
- Archer field type = attachment (FIELD_TYPE_ID 11)
- prior live review = 316 populated Source One rows / 742 attachment IDs
- multi-valued rows exist
- no approved current-runtime href/identifier contract is established

Historical notes that treated the field as a scalar or ordinary result property are superseded by the attachment review.

## Diagnostic prepared
Root `RUN_NOW.py` now performs a read-only current-runtime discovery:

1. reconfirms current attachment counts/shapes and Source One field metadata;
2. discovers current Archer *_RAW tables whose names suggest document, attachment,
   file, repository, evidence or report storage;
3. prints candidate table schemas;
4. recursively scans candidate CURATED_JSON payloads for the Source One attachment
   IDs without printing the IDs;
5. for matching records, inventories populated JSON paths/keys that look like
   identifiers, file names, URLs, URIs, hrefs or links.

Only aggregate counts, table names and JSON paths are printed.

## Status
- mapping CSV unchanged
- mapper code unchanged
- no target/source DML
- live Snowflake result pending

## Next action
Run only the current root `RUN_NOW.py` in Snowflake and return the output.

A mapping change is justified only if a current RAW source resolves the attachment
IDs and exposes a stable identifier/resource path suitable for the intended OSCAL
representation. Otherwise keep the field explicitly deferred rather than inventing
an href.
