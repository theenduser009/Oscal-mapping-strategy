# Assessment Results - corrected threshold source names

> Current package: matching v4 compiler/helpers, 1,903 runtime lines.
> Use [the project walkthrough](PROJECT_WALKTHROUGH.md) and [current status](CURRENT_STATUS.md)
> for the latest acceptance and next action. Older release sizes, replacement lists
> and first-preview steps below are historical where superseded. This guide alone
> is not a request to repeat a completed run.

Upload the updated [ARCHER_OSCAL_MAPPINGS.csv](../Mapping/ARCHER_OSCAL_MAPPINGS.csv).
Only two existing source names and their provenance notes changed:

| Correct source key | OSCAL element path | Transform |
| --- | --- | --- |
| `_CURRENT_AVERAGE_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` | `scalar-score` |
| `_CURRENT_HIGHEST_DEVICE_RISK_THRESHOLD` | `assessment-results.results[].observations[]` | `scalar-score` |

Both leading underscores are confirmed by the owner and the private source
screenshot. The CSV still has 32 approved AR mappings; PCT mappings and the 13
deferred AR mappings are unchanged. No percentages are calculated or substituted.

## Next run

1. Upload this corrected CSV before running Cell Two.
2. Keep the current seven cells. The earlier null-preserving release required
   Cells One, Three and Four; if those replacements are already installed, no
   further cell replacement is needed for this correction.
3. Select `SELECTED_MODELS = ("ASSESSMENT_RESULTS",)` in Cell One. Retain
   `CONFIG["EXECUTE_WRITES"] = False` and AR `preserve_null_observations: True`.
4. Set Cell Seven `OSCAL_LOAD_MODE = "PREVIEW"` and run Cells One through Seven
   in order, so the CSV is reloaded and the mapping plan is rebuilt.
5. Confirm Cell Three selects 32 AR rows, and Cell Seven reports
   `PREVIEW_COMPLETE` / `PREVIEW_PASSED_NO_TARGET_DML`, with validation/storage
   checks passed and writes/commit false. Review the proposed threshold
   observations and parent links before the planned COMMIT.

No registry setup, DDL, table reset or loader change is required.

## Expected field behavior

| Source state | Result |
| --- | --- |
| Exact underscored key present, JSON null | Observation with actual `props[].value: null` |
| Supported populated value, including zero/false | Existing string-valued property |
| Exact key absent | No observation; no fallback to another spelling |
| Empty string/list/object | Existing omission behavior |
| Unsupported populated value | Run blocks before writing |

Output property names remain `current-average-device-risk-threshold` and
`current-highest-device-risk-threshold`. The two collection instance keys now
use the corrected source names. Thus their hashes/UUIDs differ from rows that
would have been generated using the old unprefixed names; other mappings retain
their identities. The owner reports these properties missing in the target.
No historical rows are deleted or re-keyed by this release. Actual changes depend
on the retained source snapshot and existing tables, so no fixed count is assumed.

PCT fields are separate. If absent from the source, they remain absent in output.

## Validation and acceptance

Local validation ran 204 tests without failures, with three unavailable-Snowpark
class skips. All seven focused AR extension tests pass, including nulls, exact
keys, unchanged AR30 identities and PCT separation. Generated notebook checks
pass. [CI passed all 218 tests with zero skips](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34798321269)
on corrected CSV commit 2a567ec6eef54e668122aa385a243a2d0e044f95.
The directly readable private two-key fragment produced
two observations, four nodes and three valid edges with stable repeat identities,
using a synthetic record ID.
It is a partial excerpt, not the complete live dataset. Private source data
stays outside this repository.

The previous null-preserving runtime passed all 217 tests with zero skips in
[CI](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/34793258107).
The seven runtime cells remain at 1,875 lines. Full Snowpark tests use the local
relational SQL adapter, not a live Snowflake account. No live preview or commit
for this corrected CSV has been accepted yet.

Literal null remains the owner's warehouse representation. The
[NIST property definition](https://pages.nist.gov/OSCAL-Reference/models/v1.2.2/assessment-results/json-reference/)
requires a string; graph/storage checks do not establish a schema-valid complete
OSCAL export. FULL_MODEL_COMPLETE and SCHEMA_VALIDATED remain false.
