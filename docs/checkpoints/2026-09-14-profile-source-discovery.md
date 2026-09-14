# Profile source discovery checkpoint

Date: 2026-09-14
Branch: `simplify-metadata-boundary`

## Owner read-back verified in Snowflake

Source table: `RTX_RAW_DEV.ES_ESC_GRC.ARCHER_CONTENT_AUTHORIZATION_PACKAGE_RAW`

- RAW schema read back as exactly `CURATED_JSON VARIANT` and `CONTENT_ID TEXT` for the inspected table.
- Cardinality: 2,813 RAW rows, 2,813 distinct `CONTENT_ID`, 0 extra rows beyond one per `CONTENT_ID`, 0 null `CONTENT_ID`.
- `ADD_OVERLAY` is null across the current 2,813-record snapshot.
- `BASELINE_RECOMMENDATION` current distribution:
  - DFARS: 989
  - null: 855
  - LOE C: 625
  - GS Labs: 246
  - LOE D: 62
  - LOE A: 22
  - LOE B: 13
  - Basic: 1
- Counts total 2,813.

Observed `BASELINE_RECOMMENDATION` Archer select IDs:

- 162398 = LOE A
- 162399 = LOE B
- 162400 = LOE C
- 162401 = LOE D
- 162402 = DFARS
- 162403 = GS Labs
- 177494 = Basic

Additional discovery showed `ALLOCATE_BASELINE_CONTROLS` resolves to `Not Ready` (select value 80664), so it is workflow/status evidence rather than baseline identity. `CONTROL_SET_TO_ASSESS` was explicit JSON null in the inspected current source result.

Observed control-set/version labels include NIST 800-53 Rev 4, NIST 800-171 Rev 1/Rev 2/Rev 4X, NIST 800-171 (GS Labs) Rev 1, and CMMC Model Version 1.02. Current-source correlation is not one-to-one: a recommendation such as DFARS occurs with multiple control-set/version values. Therefore do not derive an OSCAL import URI from `BASELINE_RECOMMENDATION` alone.

## Decision

Keep both reviewed Profile mappings deferred for now.

- `ADD_OVERLAY`: no populated current source evidence; do not activate imports/merge/modify behavior.
- `BASELINE_RECOMMENDATION`: populated and semantically useful, but it does not identify an approved OSCAL catalog/profile resource URI by itself. No URI/default import may be invented.

No Profile model route, registry rows, mapping approval, DIM/FACT target DML, or notebook runtime change is established by this checkpoint.

## Precise remaining gap

Obtain an authoritative baseline/control-set-to-OSCAL catalog/profile resource mapping (approved `href`, plus include-all/include-controls policy where applicable). Until that evidence exists, Profile execution remains deferred.
