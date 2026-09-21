# Source One SSP responsible-party compile verification — 2026-09-21

## Owner-provided live Snowflake evidence

After replacing the notebook-visible `ARCHER_OSCAL_MAPPINGS.csv` with the
current GitHub version and rerunning Cells 1-3 with SSP selected, the owner ran
the root `RUN_NOW.py` compile check.

Observed:
- `ROUTE_STATUS: READY`
- `SELECTED_ROWS_TOTAL: 53`
- `SENIOR_INFORMATION_SYSTEMS_SECURITY_OFFICER_SISSO`
  -> direct -> `system-security-plan.metadata.responsible-parties[]`
  -> role-id `senior-information-systems-security-officer`
- `INFORMATION_SYSTEM_SECURITY_ENGINEER_ISSE`
  -> direct -> responsible-parties[]
  -> role-id `information-system-security-engineer`
- `INFORMATION_SYSTEM_ADMINISTRATOR_ISA`
  -> direct -> responsible-parties[]
  -> role-id `information-system-administrator`
- `AUTHORIZING_OFFICIAL_DESIGNATED_REPRESENTATIVE_AODR`
  -> direct -> responsible-parties[]
  -> role-id `authorizing-official-designated-representative`
- `ARCHER_CONTENT_AUTHORIZATION_PACKAGE_CONFIRMED_IN_ARCHER`
  remains `DEFERRED | NOT_COMPILED`
- final result:
  `SSP_RESPONSIBLE_PARTY_MAPPINGS_READY_FOR_PREVIEW`

## Status distinction
- GitHub mapping metadata: committed.
- Cell 3 compilation: owner-reported live verification passed.
- SSP PREVIEW after these four role additions: not yet run.
- DIM/FACT DML: not authorized by this checkpoint.

## Next action
Run Cells 4-7 with SSP selected, `EXECUTE_WRITES=False`, and Cell 7 in
`PREVIEW`. Then run the root `RUN_NOW.py` reconciliation to verify the four
new role/assignment counts against the live source population before any COMMIT.
