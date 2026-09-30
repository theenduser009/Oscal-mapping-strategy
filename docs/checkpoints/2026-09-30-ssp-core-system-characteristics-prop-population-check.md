# SSP core system-characteristics prop population check

Date: September 30, 2026
Status: Owner-run Snowflake inspection reviewed. No mapper change made.

## Verified observation

For the focused core SSP System Characteristics prop set, the target contains populated prop rows for all reviewed properties except:
- fisma-reportable
- financial-system
- pia-required

The three absent target props align with the owner-run source null check:
- FISMA_REPORTABLE: 2,813 JSON nulls / 0 real values
- FINANCIAL_SYSTEM: 2,813 JSON nulls / 0 real values
- PIA_REQUIRED: 2,813 JSON nulls / 0 real values

Current mapper behavior for these rows is omit-null, so no target prop is emitted when the source value is JSON null.

## Interpretation

The observed target behavior is internally consistent:
- populated source-backed System Characteristics properties are emitted with values;
- the three all-null source fields are omitted;
- no mapping defect is proven by the absence of those three props.

This checkpoint does not authorize changing null policy.
