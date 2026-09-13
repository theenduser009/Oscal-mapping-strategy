# FIPS value reconciliation after the live SSP review

**Follow-up:** the owner posted the
[completed live value report](2026-09-13-ssp-read-only-value-reconciliation.md).
The case-only impact changes and populated sensitivity source values are now
confirmed. The [direct-restoration checkpoint](2026-09-13-ssp-direct-sensitivity-restoration.md)
supersedes the next-action instructions below.

The owner confirmed that the existing FIPS conversion to `low`, `moderate`
and `high` should be retained, and requested work on the remaining ingestion
differences. The [posted live review](2026-09-13-ssp-read-only-dim-review.md)
identifies 36 changed security-impact nodes and 1,958 removed sensitivity
members. It does not contain their before/after values.

## Confirmed correction

Cell Two previously filtered FIPS lookup labels case-insensitively but stored
their original capitalization. A picklist ID resolving to `Low` therefore
produced `Low`, while direct text `Low` produced `low`. The lookup now stores
the lowercase label. This is a one-line correction with no runtime line growth.
The same inconsistency exists in the frozen earlier code; it is not evidence
that the simplification introduced the 36 live differences.

Four focused tests cover actual lookup loading, IDs, casing, whitespace, all
eleven executable objective mappings and all eight explicitly retained legacy
labels. General Archer lookup labels retain their original capitalization.
No ID ordering, severity inference, new label equivalence or mapping approval
is introduced. Frozen parity evidence remains unchanged.

## Next live evidence

Use the extended [read-only review cell](../../notebooks/validation/READ_ONLY_SSP_PREVIEW_UPDATE_REVIEW.py)
in the existing session before replacing or rerunning mapper cells. It compares
the accepted candidate with the current target and the retained source snapshot,
and groups controlled old/new impact labels. It separately reports sensitivity
source presence and comparisons with the removed stored member.

The extension also compares accepted impact values with the proposed lowercase
lookup behavior on a copied context. It does not modify the retained candidate,
source, lookups, mapping status or target. Unknown/multiple source selections
are reported even when the earlier transform kept one recognized value.

The previous structural review is live-accepted. The extended value report and
corrected mapper still need live execution. The existing candidate has not
been rebuilt with the correction. A later preview of the corrected mapper is
distinct from repeating the already accepted run unchanged.

`SECURITY_CATEGORY` remains deferred pending reconciliation; current evidence
does not establish whether existing sensitivity members should be removed or
mapped from that source. Keep writes disabled. Do not reset the registry or
repeat the accepted full reload.
