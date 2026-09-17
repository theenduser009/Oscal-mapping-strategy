# Checkpoint — SME questions narrowed to technical mapping blockers

Date: 2026-09-17
Branch: `simplify-metadata-boundary`
Repository version reviewed before update: `001615b38642266d203e54bd7f0031cae7b77b80`
Question-file update commit: `3a7f5137e9b5c3d962bb45c182de5ee95bb71b77`

## Supersedes

This checkpoint supersedes the earlier broad/business-oriented wording in `questions/SME_DEVELOPER_BLOCKING_QUESTIONS_2026-09-17.md`.

## Change

The SME email list is now limited to technical blockers where the mapping document cannot be compiled or emitted deterministically by the Python mapper because of one of the following:

- missing/unspecified OSCAL target path,
- multiple alternative OSCAL targets with no routing rule,
- two source rows targeting one singleton OSCAL member,
- required mapping metadata such as property name or role-id is missing,
- the mapping as written cannot satisfy the NIST OSCAL structure without additional exact mapping data,
- screenshot-derived source text is clipped/incomplete.

The updated list keeps the validated Control Implementation and Profile blockers, converts the `AUTHORIZATION_DECISION` question from a business-semantics question into a direct target-path/singleton-collision question, and adds only unresolved technical mapping metadata from SSP Metadata, Assessment Results, and Source 2.

## NIST validation actually performed

Reviewed official NIST OSCAL references for:

- SSP `control-implementation` / `implemented-requirement` / `by-component`,
- Profile `import.href`, `include-all`, `include-controls`, `merge`, and `modify`,
- SSP System Characteristics `status.state`,
- Assessment Results `observation`,
- Catalog `remarks` guidance.

No claim is made that NIST decides RTX business semantics; NIST was used only to identify schema/structural constraints relevant to executable mapping.

## Files changed

- `questions/SME_DEVELOPER_BLOCKING_QUESTIONS_2026-09-17.md`

## Validation / read-back

- Current branch head was read before the question update.
- Current mapping documents were read from GitHub, including SSP Metadata, SSP System Characteristics, SSP Control Implementation, Assessment Results, Profile, and Source 2 Source.
- Official NIST reference pages were checked for the structural constraints cited above.
- No notebook code, runtime CSV, registry metadata, DIM/FACT data, or Snowflake objects were changed.

## Next action

Use the updated technical-only question file as the email/source-owner question list. Continue implementation only for mappings already deterministic from the existing mapping document and NIST schema; use SME responses only to resolve the listed blockers.
