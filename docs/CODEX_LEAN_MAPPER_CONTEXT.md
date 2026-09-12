# Codex context: lean seven-cell mapper review

## Why this file exists

The owner supplied the original shared Gemini conversation containing the earlier compact Snowflake/Snowpark OSCAL mapper:

- Shared reference: https://share.gemini.google/5Vql3Vy49tht
- Earlier implementation: seven notebook cells with substantially fewer lines than the current maintained mapper.
- Owner concern: the current implementation appears more than 70% larger, and added complexity must be justified rather than assumed necessary.

This document gives Codex the correct context for discussing that comparison. It does not authorize a rewrite or database execution.

## Earlier compact mapper

The shared implementation used these responsibilities:

| Cell | Earlier responsibility |
|---|---|
| 1 | Runtime configuration, one OSCAL model, source/registry/target tables, and `EXECUTE_WRITES=False`. |
| 2 | Load `CONTENT_ID` as `SOURCE_RECORD_ID`, `CURATED_JSON`, mapping CSV, and active registry rows. |
| 3 | Create canonical mapping columns: source field, OSCAL path, model, mapping type, and transformation logic. |
| 4 | Generic helpers for row/key normalization, deterministic hashes, JSON-path resolution, mapping ownership, nested payload assembly, parsing, and collection instances. |
| 5 | Build canonical OSCAL DIM nodes and FACT edges from registry hierarchy. |
| 6 | Validate graph/load frames and guard persistence behind `EXECUTE_WRITES`. |
| 7 | Orchestrate the run and print aggregate results. |

The design was easy to follow and is the owner's preferred simplicity baseline.

## Proven limitation of the earlier version

In the original compact implementation, Cell 3 loaded `MAPPING_TYPE` and
`TRANSFORMATION_LOGIC`, but payload construction initially copied values
directly without executing those fields. Therefore short code alone did not
prove that Direct, Transform, Reference, Calculated, and Extension Property
semantics were implemented.

Do not restore that gap merely to reduce line count.

## Current maintained implementation

The repository now contains:

- the root `AGENTS.md` continuity rules;
- `docs/PROJECT_HANDOFF.md` and `docs/CURRENT_STATUS.md` for the dated next action;
- `docs/SHARED_SEVEN_CELL_MAPPER.md` for the current seven-cell design;
- mapping CSV metadata plus registry-driven execution;
- the synchronized cell sources and combined notebook;
- regression tests covering accepted SSP/CIA and Assessment Results behavior.

The current release reports 685 local tests passing. Live one-time DEV registry setup and the matching PREVIEW remain pending. Normal target writes remain disabled.

## What Codex must preserve

Any simplification must preserve these contracts:

1. The approved CSV is the source of field mappings and Notes.
2. The registry governs hierarchy, node ownership, instance identity, operators, and assembly policy.
3. One mapping row is not automatically one DIM node.
4. Collection identity includes the correct record and parent-instance context.
5. Node/edge identities remain deterministic and compatible with accepted output.
6. Mapping types and transformation logic are actually dispatched and validated.
7. Unsupported, blank, conflicting, inactive, or deferred metadata blocks or stays excluded; there is no silent fallback.
8. Graph validation checks null/duplicate keys, missing endpoints, UUID links, and parent relationships.
9. Persistence stays isolated in Cell 6, remains idempotent, and is guarded.
10. `EXECUTE_WRITES=False` remains the normal mode until explicitly authorized.
11. SSP and Assessment Results use the same reusable engine; do not create model-specific mappers.
12. Matillion owns upstream FieldID-to-`CURATED_JSON` conversion.

## How to handle an owner question about code size

Start read-only. Do not immediately refactor.

First compare the compact reference with current `notebooks/cells_v2/` and
`notebooks/NB_ARCHER_OSCAL_MAPPER_V1.py`. Report:

- executable line count per cell, excluding comments and blank lines;
- which added lines implement required behavior, validation, compatibility, or Snowflake constraints;
- duplicated/dead/scaffolding code that can safely be removed;
- helpers that can be consolidated without changing accepted output;
- the smallest safe target size;
- tests proving each proposed deletion is behavior-neutral.

Distinguish essential complexity from accidental complexity. A lower line count is desirable only when the same contracts and accepted outputs remain intact.

## Ready-to-use Codex prompt

> Read `AGENTS.md`, `docs/PROJECT_HANDOFF.md`,
> `docs/CURRENT_STATUS.md`, `docs/SHARED_SEVEN_CELL_MAPPER.md`, and
> `docs/CODEX_LEAN_MAPPER_CONTEXT.md`. Compare the current seven-cell mapper
> with the earlier compact baseline. Work read-only first. Give me a per-cell
> executable line-count comparison and identify only duplicated, dead, or
> unnecessarily expanded code. Do not change code, weaken validation, restore
> ignored transformation logic, or enable writes. Finish with the single safest
> simplification candidate and the exact tests that would prove it safe.
