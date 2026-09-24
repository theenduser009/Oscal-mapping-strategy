# Level-355 cleanup corrected to source-derived identity — 2026-09-24

## Owner-provided live evidence
The first one-time cleanup aborted with the guarded bad-shape exception. No delete
was performed.

## Root cause
The first cleanup tried to identify the previously committed bad child by inspecting
the stored `METADATA_JSON.control-id` text representation. That representation is
not a reliable identity selector after the projected-VARIANT serialization issue.

## Engineering correction
1. The joined-record builder now preserves ALLOCATED_CONTROL_ID exactly as the
   first accepted Level-355 batch saw it. Only mapped payload fields are JSON-decoded.
   This prevents an accidental re-key of all 127,496 previously persisted children.

2. The cleanup SQL now derives the one malformed source row directly from the
   current Level-355 source, then computes both possible historical deterministic
   node keys:
   - decoded ALLOCATED_CONTROL_ID
   - JSON-serialized ALLOCATED_CONTROL_ID

   It refuses to delete unless exactly one of those hashes identifies exactly one
   target implemented-requirement with exactly one incoming and zero outgoing edges.

This supersedes the payload-text cleanup logic.

## Next action
Run the updated cleanup SQL once:
`sql/validation/2026-09-24_cleanup_one_invalid_level355_implemented_requirement.sql`

If it returns `LEVEL355_SINGLE_BAD_IMPLEMENTED_REQUIREMENT_REMOVED`, refresh the
latest Cell 4, run Cell 4, then Cell 7 PREVIEW.
