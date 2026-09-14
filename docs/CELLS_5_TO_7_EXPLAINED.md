# Cells Five through Seven: graph, storage and execution

Code snapshot: `08ab607cc288d868549c6fb62aa945d51c55f017`.
See [the project walkthrough](PROJECT_WALKTHROUGH.md) for model history and
[Cells One through Four](CELLS_1_TO_4_EXPLAINED.md) for inputs and transformations.
Line ranges below cover the current function/configuration blocks. Pinned links
open the exact code being explained, even if the working branch later changes.

## Cell Five - create elements and relationships (83 lines)

Input: a retained source DataFrame and a compiled model context containing the
mapping plan, registry, lookups and configuration. Output: canonical node and
edge DataFrames. This cell does not write target tables.

| Lines / code | Explanation |
| --- | --- |
| [3-15: _create_canonical_graph_frame](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L3) | Converts node/edge dictionaries into explicitly typed Snowpark DataFrames. Node graph columns include path and instance context needed for validation; they are not all separate DIM columns. Audit timestamps use timezone-aware types; other graph fields initially use strings. Explicit schemas also handle an empty edge list. |
| [18-26: build_oscal_graph preparation](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L18) | Checks/prepares the model context, reads its canonical registry order, prepares reference lookups and fixes one audit timestamp for the build. |
| [27-36: source records](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L27) | Iterates retained source rows, rejects blank/noncanonical/duplicate record IDs, counts records and parses the curated JSON. Each record starts its own parent-instance index. Source iteration is streamed, but the accumulated graph is held in Python memory. |
| [37-59: node construction](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L37) | Calls Cell Four for instances of each registry element. Each instance must have a unique nonblank key. The node hash includes identity version, source, record, model, path and instance; UUID/payload rules come from the helpers. Provenance and audit values accompany the serialized object. |
| [60-75: parent links](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L60) | A root has no incoming edge. A child resolves either an explicit parent-instance key or the only available parent instance. Missing/ambiguous parents fail. Each CONTAINS edge stores parent/child hashes and UUIDs. |
| [76-83: completion](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/05_registry_graph_builder.py#L76) | Finishes per-record bookkeeping, rejects an entirely empty graph, creates the two DataFrames and records final graph diagnostics. |

## Cell Six - validate, compare and optionally load (414 lines)

Input: graph frames and one route's configuration. Output: counts, phase/status,
expected changes and readback information, or a structured LoadError. The two
tables in a route share a transaction. Separate routes do not share one global
transaction. The target snapshots detect changes; they do not lock out other writers.

| Lines / code | Explanation |
| --- | --- |
| [1-20: imports, release and field definitions](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L1) | Declares the common loader release, three audit fields, nine non-PK DIM fields and five non-PK FACT fields. The configured PK supplies the tenth/sixth column. |
| [23-26: LoadError](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L23) | Carries a machine-readable failure code and structured details without requiring callers to parse a sentence. |
| [29-40: _load_query / _load_count / _load_zero](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L29) | Executes SQL, reads a count, or raises when a query finds any prohibited rows. Shared wrappers keep repeated checks short. |
| [43-52: _load_identifier / _load_literal](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L43) | Validates configured table/column names and quotes nonblank configured SQL string values. Identifiers and values follow different rules. |
| [55-57: _load_no_transaction](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L55) | Stops if another transaction is open before setup/cleanup DDL or a new load transaction. |
| [60-88: _load_storage](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L60) | Requires explicit boolean write mode and the approved physical profile. Checks source/model/target configuration consistency. An unverified destination can return graph-only preview; it cannot commit. Obsolete-row policy must remain BLOCK. |
| [91-177: _load_graph](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L91) | Checks unique hashes/UUIDs, correct source/model/path, object JSON, audit values and one root per expected record. Edges must join existing endpoints in the same record and match both UUIDs and parent context. Roots have zero parents; every other node has exactly one. Strictly descending paths rule out cycles. This is graph validation, not complete OSCAL schema validation. |
| [180-194: _load_schema](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L180) | Reads DESC TABLE and compares exact column names/types/nullability and computed-column status with the shared layout. A table merely existing does not prove compatibility. |
| [197-199: _load_changed](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L197) | Builds null-safe comparisons. Ordinary change detection excludes the run/timestamp audit fields; verification can explicitly include them. |
| [202-209: _load_changes](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L202) | Joins staged and stored keys to count inserts, business-value updates and unchanged candidates. These are candidate counts, not a claim that writes occurred. |
| [212-217: _load_merge](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L212) | Builds a MERGE that updates changed matching keys and inserts new keys. It does not delete obsolete rows. |
| [220-222: _load_equal](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L220) | Compares SQL result sets in both directions to find omitted or extra rows. |
| [225-238: _load_scope](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L225) | Identifies target elements for the candidate keys and source records, then includes their touching relationships. This bounds the current graph checks to the affected data. |
| [241-265: _load_preflight](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L241) | Rejects null/duplicate target keys, obsolete scoped rows, incompatible identity/provenance, non-object stored payloads and invalid stored parent links. A value-driven SSP key change can stop here even when the new graph itself is valid. |
| [268-301: _load_prepare](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L268) | Verifies schema, materializes graph frames and converts hashes, UUIDs, JSON and timestamps to physical target representations. Checks text widths, saves target baselines, runs preflight and counts changes. Temporary DDL finishes before BEGIN. |
| [304-309: _load_baseline](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L304) | Compares target tables with saved baselines, including row multiplicity, to detect intervening writes or verify rollback. |
| [312-329: _load_verify](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L312) | Requires no remaining staged inserts/updates, correct audit values for changed versus unchanged rows, valid relationships and preservation of rows outside the candidate set. |
| [332-340: _load_cleanup](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L332) | Drops only this attempt's named temporary tables when no transaction is active. Reports cleanup failure separately rather than rewriting the recorded load outcome. |
| [343-362: validate_and_load_oscal preview](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L343) | Creates result flags, prepares the graph/storage checks, and returns either graph-only pending-storage status or a target-aware preview without target DML. |
| [363-389: commit and readback](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L363) | Begins a transaction, rechecks baseline/preflight, merges DIM then FACT, compares actual and expected change counts, verifies before committing, and verifies again after COMMIT. A transaction-phase error triggers rollback and baseline readback. |
| [390-402: failure and cleanup reporting](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L390) | Records failure phase. Ambiguous BEGIN/COMMIT/ROLLBACK results and failed post-commit readback are distinct from a confirmed rollback, so the report cannot promise a safe blind retry. Cleanup runs for confirmed preview, commit or rollback outcomes. |
| [405-411: verify_oscal_load](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L405) | Reuses preparation/readback checks to compare a supplied graph with storage, then cleans up. It is an available helper; the current normal commit already verifies internally. |
| [414: loader release marker](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/06_validation_and_guarded_loader.py#L414) | Marks the callable so Cell Seven can reject an incompatible loader left in notebook memory. |

## Cell Seven - run and report (84 lines)

Input: Cell Two's retained source inputs and Cell Three's mapping contexts.
Output: MODEL_GRAPHS and PIPELINE_REPORT. On failure, the structured report is
still printed so the user can see the failed model and whether a commit was attempted.

| Lines / code | Explanation |
| --- | --- |
| [1-2: OSCAL_LOAD_MODE](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L1) | Selects PREVIEW or COMMIT. Keep the shared configuration's EXECUTE_WRITES false; the orchestrator enables it only for the commit pass. |
| [5-8: PipelineError](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L5) | Attaches the complete pipeline report to a raised error. |
| [11-21: run_oscal_mapping](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L11) | One route's simple entry point: build graph, determine expected source coverage, validate/load, and return nodes, edges and result. |
| [24-46: run_oscal_pipeline setup](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L24) | Validates mode, loader release, unique source/model routes, required inputs, ready mappings and commit destination contracts. |
| [47-57: preview pass](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L47) | Copies each context, supplies retained lookups/source counts, builds the graph and previews it. Stores the graph for the optional commit pass. Every selected route reaches this pass before any route commits. |
| [58-67: commit pass](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L58) | In COMMIT mode, passes each retained graph to the shared loader with writes enabled. Transactions are per route; earlier successful routes stay committed if a later route fails. |
| [68-73: failure report](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L68) | Records the failed route and loader details, distinguishing a failure before any commit from one requiring commit-outcome review. |
| [76-84: notebook execution](https://github.com/theenduser009/Oscal-mapping-strategy/blob/08ab607cc288d868549c6fb62aa945d51c55f017/notebooks/cells/07_mapper_orchestrator.py#L76) | Clears old output variables, invokes the pipeline, retains error reports and always prints OSCAL_PIPELINE_REPORT. This is the statement block that actually starts the run. |

## Explaining a run result

`D` means DIM elements; `F` means FACT relationships. INSERTS are new candidate
keys, UPDATES are changed business values at matching keys, and UNCHANGED means
the candidate already matches. The persisted/committed flags describe the
operation outcome, not whether older rows already exist in the tables.

Neither passing graph validation nor a count of element types proves all
mapped fields have source values. Use the CSV field index and inspect the
appropriate payload member or linked child rows for field-level coverage.
