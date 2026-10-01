# Current status

Updated: October 1, 2026. Branch: `simplify-metadata-boundary`.

## Current action — seven-cell GitHub publication completed by this revision

The owner explicitly requested that the delivered October 1 contribution-aware candidate replace the maintained repository runtime, together with generated copies and durable context. This publication contains the seven actual runtime files, not merely documentation or download links.

Read [the publication checkpoint](checkpoints/2026-10-01-seven-cells-published-to-github.md) and [exact file manifest](checkpoints/2026-10-01-seven-cell-publication-manifest.json). The publication revision is the commit introducing that checkpoint; its inspected parent is `94e41f8896d73cd6ed191c6030efb7f31c7d206b`.

| Evidence stage | Status |
|---|---|
| Seven-cell implementation | Published together under `notebooks/cells` in this revision |
| Generated mirrors and combined notebook | Synchronized using the existing repository generator |
| Read-only props reader | Published; parsed JSON with exact owner lookup, separate and inline props |
| Local test rerun before publication | 73 scenario checks plus 53 focused tests passed; 126 total |
| Native-output parity | Passed for 384 non-lineage nodes and 312 edges over five synthetic models/six routes |
| Entire maintained repository suite / official SDK compatibility | Not established by the local test rerun; inspect CI separately |
| Native Snowflake execution or new database COMMIT/readback | None performed by this publication |
| Full production CSV/current registry or complete OSCAL export validation | Not established |
| Production readiness | Pending remaining compatibility, integration, governance, and release checks |

## What is now implemented

Matching compiler/helpers: `lean-csv-registry-v5-lineage`. Loader: `oscal-lean-daily-v3.2-lineage`.

- Native mappings remain native; approved business extensions retain their approved props destinations.
- Needed attribution is captured when a mapping actually contributes to a surviving output, rather than by checking raw presence.
- Grouped `source-field` and `target-path` props describe that contribution. Joined data also carries actual child source context; repeated-target ancestor attribution requires an existing validated payload UUID.
- Unique one-to-one source names rely on matching versioned mapping definitions; ambiguous and joined-source cases have per-record attribution. No per-field toggle, duplicate mapping row, new lineage table, or blanket dump of unmapped fields.
- Strict impact-list cardinality prevents silently dropping mixed inputs. Empty user/group wrappers omit assignments, without inventing a group resolver or suppressing malformed populated references.
- Missing safe attribution placement produces a lineage gap; COMMIT is blocked before any route writes when a preview has such a gap.

Keep `CONFIG["EXECUTE_WRITES"] = False` and `OSCAL_LOAD_MODE = "PREVIEW"`. A Git commit is not authorization or proof of a Snowflake commit.

## Preserved scope and open requirements

No mapping CSV, registry, table DDL, native identity seed, null policy, FIPS/Legacy crosswalk, or href generation was changed by publication. Old broad-lineage rows, contributor removal, and value-keyed SSP property updates still require controlled reconciliation under the obsolete-row guard. Never bypass it or truncate targets.

The namespace `urn:company:oscal:lineage:v1` is an existing development convention, not proven organization approval. Exact recovery for one-to-one mappings requires the versioned definitions to be available to consumers. Grouping and target references are local semantics, not a NIST-standard ETL vocabulary. Current graph validation does not establish full model/schema conformance.

Prior SAP/POAM, AR30/AR32, SSP/daily-loss, Profile, and other mapping/run decisions remain in dated history. Do not infer their current live outcome from this publication or resurrect September 14 next-step instructions. Check the newest owner evidence before asking for a repeat run.

## Single next action

Validate this exact published set against the maintained repository tests and native compatibility gates, preserving the local regression evidence. Resolve or explicitly account for relevant CI failures before a bounded, authorized native Dev integration. No owner Snowflake debugging run is requested merely to repeat the locally reproduced cases.

## Supersession and history

This publication supersedes the statement in [the earlier October 1 candidate checkpoint](checkpoints/2026-10-01-seven-cell-contribution-candidate.md) that the new runtime exists only in attachments. That checkpoint remains true for its time. Earlier successful local tests and live batches remain version-specific evidence, not proof of later changes.

The full previous status document, including historical run links and counts, is preserved [at revision 94e41f8](https://github.com/theenduser009/Oscal-mapping-strategy/blob/94e41f8896d73cd6ed191c6030efb7f31c7d206b/docs/CURRENT_STATUS.md). The [checkpoint directory](checkpoints) contains the dated evidence trail. This shorter current page deliberately does not repeat outdated counts as current facts.
