# Props and downstream-consumption meeting note

Date: September 30, 2026
Status: Owner-provided meeting discussion captured. No mapper, registry, or Snowflake change implemented.

Confirmed discussion:
- Props are being considered for Archer fields that do not map cleanly to a named OSCAL member.
- Props were described as structured arrays/collections whose values can be selected by name, not as an opaque blob.
- A downstream-consumption question remains: whether consumers can use the hierarchical OSCAL structure directly or need a flattened published view.
- Current QA was described as field/path micro-testing with null/TBD cases tracked separately.
- The team wants clearer testing categories and acceptance criteria.
- Cleanup of inactive/null source fields is expected to reduce validation noise.

Implication:
This supports props as a project extension pattern for non-native source fields. It does not yet approve a specific source-field-lineage prop convention.

Before implementing lineage props, agree:
- parent OSCAL path;
- prop name;
- namespace;
- class/group convention;
- source-field provenance rule;
- direct hierarchical consumption versus published flattening.

For SSP security-impact lineage, keep the native security-impact members unchanged until the lineage convention is accepted.
