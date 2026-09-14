# Short SME question — Profile import href

In Archer, `BASELINE_RECOMMENDATION` maps to OSCAL `profile.imports[]`.

We verified that `BASELINE_RECOMMENDATION` is a Values List field, with values such as LOE A/B/C/D, DFARS, GS Labs, and Basic. It is not a URL or direct cross-reference.

OSCAL `profile.imports[]` requires an `href` that identifies the Catalog/Profile being imported.

**Question:** Where should we get the `href` for each Baseline Recommendation value? Is there another Archer field/application or an existing lookup that provides the actual Catalog/Profile reference?
