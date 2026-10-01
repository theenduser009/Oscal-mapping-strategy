# Current status

Updated: October 1, 2026. Branch: `simplify-metadata-boundary`.

## Current action — seven-cell GitHub publication and readback complete

Runtime publication commit: **de5b2ed2d98bbc4819e0c932bc26a45e3a85ffdc**.
Initial code inspected: 94e41f8896d73cd6ed191c6030efb7f31c7d206b.
Actual publication parent: 847c9544de9f3efc273d194da5d4037d33bea286; its connection-test.txt addition was preserved.

The owner explicitly requested that the delivered October 1 contribution-aware candidate replace the maintained repository runtime, together with generated copies and durable context. This is now done: the seven actual files are in GitHub, not only attachments.

Read [the publication checkpoint](checkpoints/2026-10-01-seven-cells-published-to-github.md) and [exact file manifest](checkpoints/2026-10-01-seven-cell-publication-manifest.json). This status-only follow-up does not change any runtime file.

| Evidence stage | Verified status |
|---|---|
| Seven maintained runtime files | Published together at de5b2ed2; remote Git blob SHA and size for all seven match the tested delivery |
| Seven generated mirrors | Remote blob hashes match their maintained counterparts |
| Combined notebook | Remote blob b0eff842e104f8157951bdc06004f6626d542904 matches the local output of the unchanged repository generator |
| Read-only property reader | Remote blob 0960d56f4654b12499dcc1dd3b718e25159a9cdb matches the delivered parsed-JSON reader |
| Local test rerun before publication | 73 scenarios plus 53 focused tests passed; 126 total, limited Python/SQLite adapter |
| Native-output parity in local fixtures | Passed: 384 non-lineage nodes and 312 edges, five synthetic models/six routes |
| GitHub Actions for publication | Run 36873093527 completed with FAILURE; generated-notebook check passed, lean-release/installed-Snowpark test step failed, whitespace step skipped |
| Native Snowflake execution or new database COMMIT/readback | None performed by this publication |
| Full production CSV/current registry or complete OSCAL export validation | Not established |
| Production readiness | BLOCKED pending investigation of actual CI failures and remaining integration/governance/release gates |

[Publication CI run](https://github.com/theenduser009/Oscal-mapping-strategy/actions/runs/36873093527), job 110405546471, completed October 1 at 14:02 UTC. This records observed run/step status only, not a root-cause diagnosis. Do not assume every failure is pre-existing or merely stale expectations. Do not substitute the local 126 passes for this failed compatibility gate.

## What is now implemented

Compiler/helpers: `lean-csv-registry-v5-lineage`. Loader: `oscal-lean-daily-v3.2-lineage`.

- Native mappings remain native; approved business extensions retain their approved props destinations.
- Needed attribution is captured when a mapping actually contributes to surviving output, not by checking raw presence.
- Grouped `source-field` and `target-path` props describe the contribution. Joined data includes actual child source context; repeated-target ancestor attribution requires an existing validated payload UUID.
- Unique one-to-one source names rely on matching versioned mapping definitions; ambiguous and joined-source cases receive per-record attribution. No per-field toggle, duplicate mapping row, lineage table, or blanket dump of unmapped fields.
- Strict impact-list cardinality prevents silently dropping mixed input. Empty user/group wrappers omit assignments without inventing group resolution or suppressing malformed populated references.
- Missing safe placement produces a lineage gap; COMMIT is blocked before any route writes when a preview has such a gap.

Keep `CONFIG["EXECUTE_WRITES"] = False` and `OSCAL_LOAD_MODE = "PREVIEW"`. GitHub publication/readback is not authorization or proof of a Snowflake commit.

## Preserved scope and open requirements

No mapping CSV, registry, table DDL, native identity seed, null policy, FIPS/Legacy crosswalk, href generation, CI workflow, or test fixture was changed in this publication. No unrelated empty files were deleted. Old broad-lineage rows, contributor removal, and value-keyed SSP property updates still require controlled reconciliation under the obsolete-row guard. Never bypass it or truncate targets.

The namespace `urn:company:oscal:lineage:v1` remains a development convention, not proven organization approval. Exact recovery for one-to-one mappings requires versioned definitions to be available to consumers. Grouping/target references are local semantics, not a NIST-standard ETL vocabulary. Current graph checks do not establish complete model/schema conformance.

Prior SAP/POAM, AR30/AR32, SSP/daily-loss, Profile, and other run decisions remain in dated history. Do not infer current live outcomes from this publication or resurrect September 14 next-step instructions. Check newest owner evidence before asking for a repeat run.

## Single next action

Read the failed publication CI logs and reconcile the maintained repository compatibility tests with this exact runtime, separating real defects from outdated fixture/contracts. Preserve independent assertions and local regressions. No production release or owner Snowflake debugging run is requested now; bounded native Dev integration follows a passed compatibility gate and explicit authorization.

## Supersession and history

This publication supersedes only the statement in [the earlier October 1 candidate checkpoint](checkpoints/2026-10-01-seven-cell-contribution-candidate.md) that the new runtime exists only in attachments. That checkpoint remains true for its time. Earlier test/load evidence remains version-specific.

The full previous status document, including historical run links/counts, is preserved [at revision 94e41f8](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/docs/CURRENT_STATUS.md). The [checkpoint directory](checkpoints) retains the evidence trail. This page does not repeat outdated counts as current facts.
