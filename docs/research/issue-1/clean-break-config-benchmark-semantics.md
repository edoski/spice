# SPICE clean-break configuration, benchmark, runtime, and serving research

Date: 2026-07-10

This memo investigates the configuration and benchmark parts of the proposed SPICE clean break, plus the coupled runtime, inference, serving, documentation, dependency, and size gates. Local source is the primary source for current behavior. External claims link to the documentation owned by Pydantic, Optuna, Python, FastAPI, SQLite, aiosqlite, or rsync.

Facts and recommendations are kept separate. A recommendation below is not an accepted architecture decision.

## Findings at a glance

The candidate direction is technically credible, but it is not yet an executable specification. The main missing decisions are the workflow-config algebra, recipe versus executable identity, benchmark matrix grammar, data-flow versus scheduling semantics, resumable submission behavior, exact-file collection protocol, evaluation-parent identity, serving durability, and the disposition of accepted ADRs.

Several candidate statements need correction or qualification:

- There are 23 checked-in benchmark YAML files. Seventeen files use case-level Cartesian dimensions; “17 checked-in benchmarks” is not the total inventory.
- A Pydantic workflow discriminator requires Literal fields. The current WorkflowTask-typed defaults are not sufficient.
- Baseline and tuned training cannot both be top-level variants with the same “train” discriminator. Training needs a nested explicit source discriminator, a callable discriminator, or one Train model with manual optional-field validation.
- Slot spacing has two zero-payload choices. A Literal or StrEnum field is smaller than two Pydantic models and a dispatch table.
- Exact evaluation lookup needs chain, artifact ID, and evaluation ID because the target path nests evaluations below the artifact ID. The proposed generic transfer descriptor containing only kind, ID, and chain cannot derive that path.
- Moving evaluations outside artifact roots adds an artifact-deletion dependency. Artifact deletion must refuse or explicitly cascade while evaluation files remain.
- A tuned-train benchmark plan cannot contain the final effective training definition before its tune step completes. It can contain a resolved request that references a study; the artifact stage later freezes the applied definition.
- WAL is not automatically the leanest serving choice. Durability and deployment concurrency must be decided first. A bounded strict atomic JSON snapshot is a credible one-process alternative that the candidate omitted.
- The current Vulture run is clean. “Verified dead helpers” is primarily a post-refactor audit, not a large established baseline deletion source.

## Reproduced baseline

These commands were run in the repository worktree without changing production code.

| Check | Result |
| --- | --- |
| Production Python LOC, src/spice/**/*.py | 29,004, exactly matching the candidate baseline |
| pytest | 427 passed, 1 failed |
| Failing test | tests/cli/test_config_cli.py expects an evaluator list without block_poisson_replay_300 |
| Ruff | green |
| Pyright | one existing optional block_numbers narrowing error at src/spice/temporal/problem_store.py:133 |
| Vulture at repository 90% threshold | no findings |
| Installed Pydantic | 2.12.5 |
| Installed Optuna | 4.8.0 |
| Installed FastAPI | 0.138.0 |
| SQLite linked by the current uv environment | 3.53.3, threadsafety 3 |

The relevant production-module sizes are configuration 2,333 lines, benchmarks 2,891, serving 983, core 548, modeling 5,171, temporal 1,548, evaluation 1,253, execution 931, and storage 5,429. The hard cap requires at least 2,904 net deleted lines. The expected range requires 4,354–5,804 net deleted lines.

The following existing files alone total 3,482 lines, although most need smaller replacements rather than wholesale deletion: workflow snapshot parsing, resolved-workflow records, core spec helpers, model base/registry/tuned-config helpers, the three config-group modules, temporal/prediction registries, benchmark root/result/run-state layers, and the custom async runner. The benchmark SQL index and schema are a direct 536-line deletion candidate: [result_index.py](../../../src/spice/benchmarks/result_index.py) and [_result_schema.py](../../../src/spice/benchmarks/_result_schema.py).

## Configuration and dispatch

### Pydantic can replace the manual snapshot codec, but the tags must be explicit

The current resolved snapshot path branches manually by workflow, reconstructs field records, redispatches nested owners, and guesses the evaluation-window type from its field names: [workflow_snapshots.py](../../../src/spice/config/workflow_snapshots.py#L83-L294). A parallel resolved-field layer duplicates the workflow shapes: [resolved_workflows.py](../../../src/spice/config/resolved_workflows.py#L39-L202).

Pydantic recommends discriminated unions because they select one predictable branch, requires the common discriminator field to accept Literal values, supports nested discriminators, and recommends TypeAdapter for validating a bare union. It also says a discriminated union cannot contain only one variant. See the [Pydantic 2.12 union documentation](https://docs.pydantic.dev/2.12/concepts/unions/) and [TypeAdapter documentation](https://docs.pydantic.dev/2.12/concepts/type_adapter/).

The current workflow fields are WorkflowTask values with defaults, not Literals: [models.py](../../../src/spice/config/models.py#L559-L640). A direct prototype using workflow as the discriminator fails with PydanticUserError because TrainConfig.workflow is not a Literal. A prototype with concrete Literal-tagged branches validates and serializes correctly.

Recommendation: use one module-level TypeAdapter over a concrete union and make every durable branch explicit. A clean algebra is:

~~~text
ResolvedWorkflowRequest
  train -> TrainRequest
             source -> BaselineTrainSource | TunedTrainSource
  tune -> TuneRequest
  evaluate -> EvaluateRequest
~~~

The outer workflow fields are Literal["train"], Literal["tune"], and Literal["evaluate"]. TrainRequest contains a source union tagged with Literal["corpus"] or Literal["study"]. This avoids two top-level members competing for the same train tag and removes the current optional corpus_id/study_id validator in [models.py](../../../src/spice/config/models.py#L591-L613). A callable discriminator is supported by Pydantic, but an explicit nested tag is easier to inspect in durable JSON.

The exact branches need the storage identity design to be settled first. Subject to that decision, they should contain:

- baseline train: chain, corpus ID, minted artifact ID, and the selected training definition;
- tuned train: chain, study ID, minted artifact ID, and no echoed full Surface;
- tune: chain, corpus ID, minted study ID, and the study definition/search space;
- evaluate: chain, artifact ID, corpus ID, minted evaluation ID, tagged evaluation window, evaluator config, delay, and batch size.

EvaluateConfig currently has no chain field: [models.py](../../../src/spice/config/models.py#L634-L648). Direct canonical discovery therefore requires a clean-break schema change in every evaluate selection and benchmark plan.

New study, artifact, and evaluation IDs may be minted from UUID4, but their field type should remain an opaque path-safe string. Phase 6 preserves legacy study and artifact IDs, so a strict UUID type would reject valid converted state. Fresh resolution should explicitly mint once; hydration should require and preserve the serialized value. A default factory on a durable model risks accidental reminting when an old or incomplete payload is loaded.

Evaluation windows also need an explicit tag such as kind: timestamp or kind: blocks. The current structural guess at [workflow_snapshots.py](../../../src/spice/config/workflow_snapshots.py#L280-L294) is precisely the sort of manual polymorphism the clean break aims to remove.

The project uses SerializeAsAny because fields are annotated as abstract bases such as ModelConfig and EvaluatorConfig. Pydantic 2.12 normally serializes a model-like subclass according to its annotated base schema; SerializeAsAny asks it to inspect the runtime type instead. See [Pydantic 2.12 serialization](https://docs.pydantic.dev/2.12/concepts/serialization/#serializing-with-duck-typing). Concrete union annotations make the known serialized branches explicit and remove that reason for SerializeAsAny.

### Recipe names, executable discriminators, and domain identities are three different things

The current group catalog applies one identity rule broadly. It records an identity field and often requires the YAML filename to equal that field: [group_catalog.py](../../../src/spice/config/group_catalog.py#L54-L61) and [group_catalog.py](../../../src/spice/config/group_catalog.py#L235-L267). Tests enforce the same coupling: [test_resolution.py](../../../tests/config/test_resolution.py#L39-L84).

The evaluator block_poisson_replay_300 exposes the concrete failure mode. Its recipe file carries that name, the evaluator config accepts it as an implementation ID, and the evaluator registry duplicates the same adapter under both names: [evaluation/config.py](../../../src/spice/evaluation/config.py#L10-L57) and [evaluation/registry.py](../../../src/spice/evaluation/registry.py#L42-L53). Collection then treats the recipe-flavored evaluator ID as durable matching identity.

The final schema should classify each name instead of deleting every internal name:

| Category | Meaning | Examples |
| --- | --- | --- |
| Recipe name | Operator-facing checked-in file/coordinate | block_poisson_replay_300, lstm_default |
| Executable discriminator | Chooses a real code branch | model kind, evaluator kind, feature catalog kind |
| Domain identity | Is part of the modeled or storage fact | chain name, provider reference, corpus definition |

Two credible config-file interfaces remain:

1. The file name is the recipe coordinate and the payload contains only genuine fields plus a kind discriminator where alternatives exist. This is the smallest option and is recommended.
2. A generic NamedConfig[T] wrapper carries recipe_name beside the typed payload. This makes provenance explicit but adds a wrapper at every call site.

The second option is justified only if recipe identity must travel through runtime APIs. Benchmark coordinates and artifact effective-definition provenance can usually retain the recipe name without putting it back into every executable config.

Chain.name and similar domain facts should not be stripped merely because they match a filename today. Conversely, ProblemSpec.id and PredictionConfig.id need evidence that they describe durable semantics rather than a recipe. ProblemSpec already contains the behavior-defining lookback, delay, and slot spacing. Prediction has one implementation but currently persists both a recipe-like prediction ID and a family ID: [models.py](../../../src/spice/config/models.py#L334-L348) and [prediction/registry.py](../../../src/spice/prediction/registry.py#L8-L37). A missed simplification candidate is to remove the prediction group/family selector while retaining a small explicit semantic-contract version in the artifact manifest if behavior evolution needs durable identification.

Consolidating group implementation does not erase the real raw/typed distinction in ADR 0002. Show, edit, template seed, and benchmark loading need canonical mappings; workflow resolution needs typed models. The current implementation is split across [group_catalog.py](../../../src/spice/config/group_catalog.py), [groups.py](../../../src/spice/config/groups.py), and [typed_groups.py](../../../src/spice/config/typed_groups.py). One config-file module can expose two explicit functions, load_raw and load_typed, backed by one metadata table.

### One-implementation dispatch should collapse to values or direct calls

Observed-time-window slot spacing has only nominal and recent_median choices. Both config subclasses carry no data beyond their ID, and a table plus owner coercer exists solely to select the empty subclass: [observed_time_window.py](../../../src/spice/temporal/compilers/observed_time_window.py#L31-L137). Recommendation: put slot_spacing: Literal["nominal", "recent_median"] or a StrEnum directly on ProblemSpec. This is smaller than a discriminated model union and still validates the real alternatives.

The temporal compiler registry is 148 lines while the concrete observed-time-window implementation contains the real domain work. Delete the registry, not the compiler logic: [temporal/compilers/registry.py](../../../src/spice/temporal/compilers/registry.py) and [observed_time_window.py](../../../src/spice/temporal/compilers/observed_time_window.py). The same test applies to the sole strict-deadline policy and min-block-fee prediction family. Feature catalogs, model families, and evaluators have real alternatives and should keep owner-local direct dispatch.

### Flat Optuna parameters remove tuned-model records, not validation

Optuna records all suggested parameters in one string-keyed dictionary. Its Trial API exposes params as a dictionary containing all parameters, and suggestion APIs take explicit names. See the matching [Optuna 4.8 Trial documentation](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.trial.Trial.html#optuna.trial.Trial.params) and [Pythonic search-space guide](https://optuna.readthedocs.io/en/v4.8.0/tutorial/10_key_features/002_configurations.html).

SPICE already names trial parameters with training., problem., and model. prefixes, then reconstructs nested tuned-parameter models: [tuned_config.py](../../../src/spice/modeling/tuned_config.py#L171-L219). Those intermediate models can go. The replacement still needs one pure, typed operation used both during trials and when applying the best FrozenTrial:

~~~text
apply_trial_params(study_definition, flat_params) -> EffectiveTrainingDefinition
~~~

It must reject unknown names, validate the selected model branch, re-run cross-field constraints, and derive Transformer feedforward_dim from d_model and the multiplier. The current Transformer derivation and compatibility checks are in [_transformer_shared.py](../../../src/spice/modeling/families/_transformer_shared.py#L52-L80).

Two implementation choices are credible:

- explicit per-domain/per-model application functions with allowlisted parameter names;
- a generic dotted-path patcher over arbitrary model dumps.

The explicit functions are recommended. A generic patcher is short but recreates an untyped configuration language, makes misspelled paths runtime concerns, and weakens the clean-break goal. Config-only model branches plus a small constructor table remove the circularity that motivated lazy model loaders: [families/base.py](../../../src/spice/modeling/families/base.py) and [families/registry.py](../../../src/spice/modeling/families/registry.py).

## Accepted ADR review

The candidate conflicts with accepted ADRs. The conflict should be resolved by a human gate, not by silently deleting the ADR files.

| ADR | Evidence worth retaining | Conflict or stale premise |
| --- | --- | --- |
| [ADR 0001](../../adr/0001-root-id-consumer-workflows.md) | Existing-root consumers should use exact IDs; evaluation remains manifest-first; same-chain evaluation is explicit. | Producer IDs are config-derived in the ADR but UUID4 instances in the candidate. The ADR says regenerate old roots; phase 6 converts state. |
| [ADR 0002](../../adr/0002-config-resolution-hydration-loading.md) | Fresh resolution, durable hydration, raw config-file operations, and typed loading are genuinely different callers. | Concrete owner redispatch and manual hydration become unnecessary with explicit unions. Consolidating modules need not collapse the raw/typed interfaces. |
| [ADR 0003](../../adr/0003-representation-seam-retained.md) | Sequence input preparation has useful locality. | The claimed durable representation ID and registry do not exist in production Python. Repository search finds only direct sequence_inputs imports. BatchPlan, which the ADR assigns policy ownership, is itself proposed for deletion. |
| [ADR 0004](../../adr/0004-compiler-materialization-existing-root-vocabulary.md) | Temporal compilation and benchmark planning still own substantial domain logic. | Catalog-backed root materialization, selectors, handles, root facts, and benchmark ledgers are exactly the structures the candidate removes. One implementation does not justify a compiler registry. |
| [ADR 0005](../../adr/0005-custom-execution-session-retained.md) | SSH, rsync, Slurm, following, and remote invocation form one real interface. | The catalog-envelope consequence becomes stale, but the decision remains aligned with the candidate. |

Recommendation: preserve the ADR history and mark each retained, amended, or superseded with links to the new decision. ADR 0003's current factual premise should be corrected even if the focused sequence-input module survives. “Retain only the custom Execution Session decision” is too aggressive until this review is approved.

## Benchmark planning and collection

### Inventory supports Cartesian matrices but not the current special cases

Structured inspection of src/spice/conf/benchmark found:

| Fact | Count |
| --- | ---: |
| YAML files | 23 |
| Cases | 43 |
| Steps | 64 |
| Files with case-level dimensions | 17 |
| Cases with dimensions | 21 |
| Steps with dimensions | 0 |
| Files with a generic problem grid | 7 |
| Steps with after | 33 across 17 files |
| Steps with artifact_from | 18 across 16 files |
| External Slurm dependencies embedded in after | 13 across 5 files |

This supports retaining Cartesian expansion and deleting step-local dimensions. It also supports replacing the special ProblemGrid in [schema.py](../../../src/spice/benchmarks/schema.py#L69-L100) and [_problem_grid.py](../../../src/spice/benchmarks/plan_materialization/_problem_grid.py) with ordinary labelled options.

Two matrix languages are credible:

1. Generic labelled axes. Each axis maps an explicit coordinate label to a typed selection patch. This is the most generic and smallest schema.
2. Retain named axis categories such as data, models, problems, and scoring, but require labels and remove the special problem-grid syntax. This gives stronger author guidance at the cost of schema-specific allowlists.

The current hardcoded categories and allowed fields are visible in [schema.py](../../../src/spice/benchmarks/schema.py#L17-L45). Recommendation: prototype both grammars against three representative definitions before approval: a 648-job matrix, tune to tuned-train to evaluate, and an external-ID evaluation suite. The chosen grammar must specify merge order, reject conflicting patches, make labels the durable coordinates, and never generate coordinates from serialized patches.

Explicit rows or Python benchmark generators are a third alternative, but they lose the concise reproducible shape that materially helps the large suites. They should be chosen only if the two declarative prototypes fail.

### Data flow and scheduling need one approved rule

The current planner creates separate dependency, selection, root-fact, and root ledgers. It matches upstream entries by compatible coordinate subsets and implicitly adds a scheduling edge for artifact_from: [_dependencies.py](../../../src/spice/benchmarks/plan_materialization/_dependencies.py#L30-L179) and [_roots.py](../../../src/spice/benchmarks/plan_materialization/_roots.py).

The clean target can reduce this to output IDs inside workflow requests plus local scheduling dependencies inside each plan entry. It still needs a rule for study_from and artifact_from:

- Data source implies scheduling. A local study_from/artifact_from edge both copies the upstream minted ID and orders the consumer. after is only for non-data barriers. This is recommended because the source cannot exist until its local producer runs.
- Data source and scheduling are independent. Authors must declare both and validation must prove the source is scheduled transitively before the consumer. This permits unusual pre-existing/retry cases but duplicates intent.

Explicit pre-existing IDs should not use study_from or artifact_from; they should be direct chain-plus-ID references in the workflow request. That keeps the first rule compatible with resume/retry.

Coordinate joins also need a decision. Current compatible-subset matching is concise for matrices but can become accidentally ambiguous when axes are added. Alternatives are uniqueness-checked compatible-coordinate joining or an explicit match-axis list on each source edge. Either must fail at plan time on zero or multiple producers.

after should contain only local plan-entry IDs. slurm_dependencies should contain external job specifications. The current union puts both in after: [schema.py](../../../src/spice/benchmarks/schema.py#L47-L53) and [schema.py](../../../src/spice/benchmarks/schema.py#L103-L140).

### plan.json and submissions.json need state-machine semantics

The current run stores metadata.json, plan.jsonl, submission.jsonl, and collection.json. Plan writes are non-atomic and submission records append: [_run_state_codec.py](../../../src/spice/benchmarks/_run_state_codec.py#L18-L110). Submission refuses any run that already contains a submission, so one partial remote failure makes the persisted run non-resumable: [submission.py](../../../src/spice/benchmarks/submission.py#L44-L89).

One plan.json should be an envelope, not only a list. It must retain benchmark name, run ID, creation time, schema version, target, source revision or plan hash, and entries. Otherwise the target directory layout drops metadata that submission and collection need.

submissions.json should be an atomically replaced mapping keyed by plan-entry ID. Its contract must decide pending, submitted, and failed attempts; whether rerun skips already-submitted entries; how it resumes after a process crash; and how local dependency job IDs are recovered. A later resume must reject a different remote Git commit unless the operator explicitly approves a mixed-revision run. The current code reads the remote revision once per submit invocation, so this is a real partial-resume hazard.

“Delete the dependency ledger” should mean delete a parallel ledger. Plan entries still need their minimal local and external scheduling dependencies.

### Exact-ID collection exposes a path and transfer contradiction

The target evaluation path is:

~~~text
evaluations/<chain>/<artifact_id>/<evaluation_id>.json
~~~

Therefore chain plus evaluation ID cannot determine the canonical path. A typed EvaluationRef needs chain, artifact_id, and evaluation_id, or the benchmark plan must persist the exact validated relative path. A generic root descriptor containing only kind, ID, and chain remains sufficient for corpus, study, and artifact roots, but evaluations are not roots under that algebra.

This matters because current collection pulls the whole artifact root, then searches artifact-local evaluation state by evaluator ID, delay, and provenance: [collection.py](../../../src/spice/benchmarks/collection.py#L36-L97) and [collection_resolver.py](../../../src/spice/benchmarks/collection_resolver.py#L61-L214). The clean collector should join the exact evaluation ID from the persisted EvaluateRequest, then validate artifact ID, corpus ID, chain, and submission provenance inside the fetched record.

Moving the evaluation file outside artifacts creates a new deletion edge. Artifact deletion must scan evaluations/<chain>/<artifact_id>/ and refuse while immutable evaluation results exist, or the product must approve an explicit cascade/archive policy. The candidate currently mentions dependency checks for deleting corpora and studies but not artifacts.

The collector still needs artifact manifest.json and training_summary.json once per artifact while refusing to pull best.ckpt. Two exact transfer designs are credible:

1. Extend the retained Execution Session with one rsync files-from transfer into a temporary collection tree. The list contains exact evaluation files plus deduplicated manifest and summary paths. Rsync officially supports reading the source-file list from --files-from; see the [rsync man page](https://download.samba.org/pub/rsync/rsync.1#OPTION_SUMMARY). This is recommended because it reuses the accepted SSH/rsync boundary and adds no remote bundle format.
2. Run a typed remote SPICE command that validates and emits a collection-input bundle, then transfer that bundle once. This provides remote-side validation but creates another protocol, bundle schema, and cleanup lifecycle.

In either design, collection builds and validates a complete candidate snapshot in a temporary location and atomically replaces collection.json only after every exact join succeeds. A failed recollection must preserve the previous snapshot.

The normalized collection can store an artifacts mapping keyed by artifact ID, containing one manifest and training summary, and evaluation rows containing coordinates, evaluation reference, optional submission provenance, and aggregate results. Training and evaluation metric namespaces must be explicit so equal metric IDs cannot silently collide.

Direct list/filter/export over collection snapshots is credible after results.sqlite deletion. The specification still needs stable ordering, malformed-run policy, target/run metadata columns, and metric namespace rules. The current index embeds fixed columns and collision behavior: [result_index.py](../../../src/spice/benchmarks/result_index.py#L29-L61) and [result_index.py](../../../src/spice/benchmarks/result_index.py#L380-L397).

## Runtime, inference, and serving

### asyncio.run covers the custom runner's platform responsibility

The custom runner creates and closes an event loop, installs SIGINT handling, cancels the main task, shuts down async generators, and shuts down the executor: [async_runtime.py](../../../src/spice/core/async_runtime.py). Its only production caller is acquire: [workflows/acquire.py](../../../src/spice/workflows/acquire.py#L9-L44).

Python 3.11 asyncio.run manages the loop, finalizes async generators, and closes the executor. Its Runner installs a SIGINT handler, cancels the main task, permits finally cleanup, then raises KeyboardInterrupt. See the [Python 3.11 runner documentation](https://docs.python.org/3.11/library/asyncio-runner.html). Replacing the one caller is supported, provided acquire's own cleanup remains in finally/async context managers.

The package import mutates MPLCONFIGDIR and creates a directory: [src/spice/__init__.py](../../../src/spice/__init__.py). There is no direct Matplotlib import in SPICE. Remove the mutation only after a fresh-environment import plus Lightning/TorchMetrics smoke, including the cluster's home/cache constraints. If the cluster still needs an override, it belongs in the execution environment adapter, not package import.

Vulture currently reports nothing. Two public helpers have no repository references: LiveSepoliaClient.latest_block_number and ServingRuntime.artifact_id. They are deletion candidates only after confirming they are not an intentionally supported external API.

### One-frame historical inference does not prove one online algorithm

Historical evaluation loads one block frame and currently passes an empty frame plus the full frame into inference preparation: [artifact_inference.py](../../../src/spice/modeling/artifact_inference.py#L119-L169). A one-frame plus requested-window API removes that artificial split.

Online serving is semantically different. It has no future outcome rows, constructs one right-edge sample, and applies a request-specific action mask: [serving/inference.py](../../../src/spice/serving/inference.py#L144-L198). Two designs deserve a small prototype:

- keep focused historical and online preparation functions, sharing feature scaling and sequence tensorization;
- use one preparation interface with explicit historical-window and online-right-edge request variants.

The first is safer unless the prototype shows meaningful duplication. A generic mode flag that merely hides two algorithms would be a shallower interface.

Serving also deliberately separates the live Sepolia chain from artifact_chain_name: [serving/config.py](../../../src/spice/serving/config.py#L21-L74) and [serving/runtime.py](../../../src/spice/serving/runtime.py#L58-L74). Direct discovery must carry artifact chain explicitly. Human approval is required before either preserving cross-chain serving or enforcing same-chain serving; evaluation's same-chain ADR does not answer this serving policy.

### FastAPI lifecycle is currently lazy and never closed

The module-level app has no lifespan. The first request synchronously and lazily builds the service, so startup failures and model-loading cost surface on that request rather than before readiness: [serving/api.py](../../../src/spice/serving/api.py#L23-L26) and [serving/api.py](../../../src/spice/serving/api.py#L79-L87). LiveSepoliaClient has close(), but no caller invokes it: [live_blocks.py](../../../src/spice/serving/live_blocks.py#L43-L49).

FastAPI recommends its lifespan async context manager for startup and shutdown resources. Code before yield runs before requests; code after yield releases resources at shutdown. See [FastAPI lifespan events](https://fastapi.tiangolo.com/advanced/events/). The service, model/runtime, and live RPC clients should be initialized once in lifespan and closed there. Tests should enter the real lifespan rather than bypass it.

### Serving analytics storage requires an explicit product decision

Current behavior is small but genuinely stateful:

| Operation | Current need |
| --- | --- |
| record_prediction | durable insert keyed by request ID |
| get_prediction | exact lookup used later to price an observed transaction |
| record_observation | mutate the prediction row with receipt/fee/savings facts |
| analytics | return the newest 100 rows and totals over all observed rows |

The evidence is [analytics.py](../../../src/spice/serving/analytics.py#L29-L174) and the only behavior test is [test_analytics.py](../../../tests/serving/test_analytics.py). No worker count, multi-host deployment, retention period, or requirement to survive restart is documented. The default is one local file at .spice/serving.sqlite: [serving/config.py](../../../src/spice/serving/config.py#L13-L15).

The current implementation has three correctness/operation issues independent of backend choice:

- with self._connect() commits or rolls back but does not close the sqlite3 connection. Python explicitly says the Connection context manager does not close; use close() or contextlib.closing(). See [Python sqlite3 context-manager documentation](https://docs.python.org/3.11/library/sqlite3.html#how-to-use-the-connection-context-manager).
- record_observation ignores whether any row was updated. Cursor.rowcount reports modified rows for UPDATE, so exactly one should be required. See [Python sqlite3 rowcount](https://docs.python.org/3.11/library/sqlite3.html#sqlite3.Cursor.rowcount).
- FastAPI async handlers call these synchronous utility methods directly. FastAPI only offloads normal path functions/dependencies it invokes; directly called utility functions run directly. See [FastAPI's utility-function rule](https://fastapi.tiangolo.com/async/#other-utility-functions). Python provides asyncio.to_thread for I/O that would otherwise block the event loop: [Python 3.11 asyncio.to_thread](https://docs.python.org/3.11/library/asyncio-task.html#asyncio.to_thread).

The storage alternatives are:

| Alternative | Strength | Total cost/risk | Fit |
| --- | --- | --- | --- |
| Lifespan-owned in-memory dict/ring | No dependency or disk schema; smallest code | Loses outstanding request IDs and analytics on restart; each worker diverges | Best only if durability is explicitly unnecessary and serving is one process |
| Strict atomic JSON snapshot | Reuses the proposed Pydantic/atomic-JSON layer; survives restart without a database; can store pending predictions, the newest 100 rows, and aggregate counters | Rewrites the bounded file on each mutation; needs a single-process lock, expiry pruning, corruption policy, and exact counter updates; separate workers would overwrite each other | Strong candidate when one process needs restart durability but not shared multi-worker state |
| stdlib sqlite3, direct SQL | No new dependency; transactions, exact lookup, update, ordering, and aggregation fit one table | Blocking calls must be offloaded; connection and journal policy must be explicit | Recommended when multiple processes on one host need shared durable state or retained history outgrows a bounded snapshot |
| aiosqlite | Awaitable API and automatic async connection closing | New dependency; it uses one shared worker thread and request queue per connection, so it changes the interface more than storage semantics | Consider only if measured load or code clarity justifies it |
| Append-only JSONL events | Simple append shape and inspectable file | Must reconstruct mutable request state and totals; needs multi-process locking, partial-record recovery, retention/compaction, and an in-memory index | Not lean for the current update and query contract |
| SQLModel/SQLAlchemy | ORM models and framework tutorial support | Restores/retains the large dependency being removed and adds sessions/engine/schema abstractions for one table | Not justified |
| External PostgreSQL/service | Shared multi-host durability and stronger concurrency | New service, driver, deployment, migrations, and operations | Only if multi-host shared state becomes a requirement |

aiosqlite's own documentation says it avoids blocking by using one shared thread per connection and executes actions through a shared request queue: [aiosqlite details](https://aiosqlite.omnilib.dev/en/stable/#details). FastAPI does not require SQL and permits any database library; its SQLModel example is built on SQLAlchemy: [FastAPI SQL database guide](https://fastapi.tiangolo.com/tutorial/sql-databases/).

Conditional recommendation:

1. First decide whether outstanding predictions and analytics must survive restart, whether multiple worker processes write the same store, whether multiple hosts share it, and the retention limit.
2. If restart durability is not required, use an in-memory store and state the loss semantics.
3. If exactly one process needs restart durability, prototype a strict bounded atomic snapshot first. Keep pending predictions keyed by request ID, prune them by their existing expiry timestamp, retain only the rows the API can return, and update integer aggregate counters in the same atomic replacement. Reject it if pending-state bounds or whole-file mutation cost are not explicit.
4. If multiple processes on one host need shared durable state, retain one direct stdlib sqlite3 module. Offload its operations from async routes, close every per-operation connection, set an explicit lock timeout, make observation transition semantics exact, and keep the database node-local.
5. Add aiosqlite only after measurement demonstrates a benefit. Do not add SQLModel merely because it appears in FastAPI's tutorial.

WAL is a separate decision, not part of choosing SQLite. SQLite says WAL permits concurrent readers and a writer but only one writer, requires all processes on the same host, and does not work over a network filesystem. PRAGMA journal_mode=WAL returns “wal” only if activation succeeds. See [SQLite WAL](https://www.sqlite.org/wal.html). The default rollback journal plus an explicit sqlite3.connect timeout may be sufficient for this low-volume API; Python's connect timeout already waits on locks.

Current SQLite documentation also describes a rare WAL-reset corruption bug affecting versions through 3.51.2 when multiple connections write/checkpoint concurrently. Fixes are 3.51.3, 3.50.7, and 3.44.6. The local uv environment links 3.53.3, but Python's linked SQLite is deployment-dependent. If WAL is approved, the deployed version and local-filesystem assumption must be an acceptance gate, not inferred from this workstation.

## Replay totals, docs, dependencies, and size gates

The replay metric catalog is 258 lines of string-keyed descriptor and aggregation machinery: [_temporal_replay_metric_catalog.py](../../../src/spice/evaluation/_temporal_replay_metric_catalog.py). A typed ReplayTotals record can own event totals, fee totals, count, conversion, finite checks, and merge behavior. A small descriptor tuple may still be required for public metric metadata; “typed totals” should not delete validation or dynamically return undocumented keys.

The repository contains 45 package Markdown files, about 3,530 lines, plus 1,569 lines in root architecture/progress/context/ADR documents. Several are already stale: CONFIGURATION describes removed objective/dataset fields, README and architecture docs describe catalog/SQLAlchemy/result-index behavior, and PROGRESS is dated. Two documentation strategies are credible:

- minimal normative docs: README, concise architecture/configuration, the single CONTEXT.md vocabulary required by docs/agents/domain.md, agent docs, and ADR history;
- retained per-domain architecture docs rewritten against the new interfaces.

The first is recommended for the stated maintenance goal. Accepted ADR history should remain as short supersession records rather than being erased.

SQLAlchemy imports are confined to storage/catalog/benchmark-index code scheduled for deletion, so the dependency should disappear after that cut. scikit-learn is used only by the scaler replacement target. After code changes, regenerate uv.lock, create a fresh environment, and verify import plus acquire/train/evaluate/collect/load/serve. Package-import MPLCONFIGDIR removal belongs in the same smoke.

The hard line cap is a gate; the expected range should not become a minimum that encourages compression. Report gross additions, deletions, and net by subsystem using the same find/wc measurement. Defer final subsystem budgets until the storage and training designs are also resolved. Run Vulture after the new seams exist and manually review framework callbacks, validators, CLI registration, reflection, and config-driven use as AGENTS.md requires.

## Proposed Wayfinder tickets

These are copy-ready decision questions. Titles, not numeric IDs, should be used in blocking relationships. Names that belong to other investigation areas may be adjusted once the complete map is assembled.

### Ratify the clean break against accepted architecture decisions

Label: wayfinder:grilling. No blockers.

## Question

Review ADR 0001 through ADR 0005 against current code and the clean-break destination. For each, approve retained principles, amended claims, superseding decisions, and document disposition. Explicitly decide hybrid deterministic/UUID identity, raw-versus-typed config interfaces, focused sequence-input locality, temporal/planning locality without shallow registries, and retention of the custom Execution Session. Do not presume that every old ADR survives or that every old ADR is superseded.

### Classify recipe names, executable discriminators, and domain identities

Label: wayfinder:grilling. Blocked by Ratify the clean break against accepted architecture decisions.

## Question

Inventory every checked-in config group and classify each current name/id as recipe coordinate, executable branch discriminator, or genuine domain identity. Choose between file-name-plus-payload-kind and a NamedConfig wrapper. Resolve the block_poisson_replay_300 duplication, one-implementation prediction/compiler/policy selectors, ProblemSpec identity, and the provenance location for recipe labels.

### Choose the resolved workflow configuration algebra

Label: wayfinder:grilling. Blocked by Classify recipe names, executable discriminators, and domain identities and the map's canonical persisted identity/direct-discovery decision.

## Question

Specify the exact Literal-tagged train, tune, and evaluate request models, including nested baseline-versus-study training source, chain, opaque output IDs, tagged evaluation windows, runtime-only fields, and strict hydration behavior. Decide flat chain-plus-ID fields versus small typed root references. Require a Pydantic 2.12 TypeAdapter round trip without manual owner coercers, resolved-field records, SerializeAsAny, or accidental reminting.

### Choose the model-space and tuned-parameter application seam

Label: wayfinder:grilling. Blocked by Choose the resolved workflow configuration algebra.

## Question

Define config-only model and model-space unions, the constructor dispatch table, Optuna parameter names, and one pure best-trial application operation. Compare explicit typed parameter applicators with a generic dotted-path patcher. Preserve unknown-parameter rejection, cross-field validation, and explicit Transformer feedforward derivation while deleting tuned-parameter models and lazy loaders.

### Choose the labelled Cartesian benchmark language

Label: wayfinder:prototype. Blocked by Choose the resolved workflow configuration algebra.

## Question

Produce small YAML prototypes for generic labelled axes and retained named axis categories, converting a 648-job suite, a tune-to-train-to-evaluate suite, and an external evaluation suite. Decide defaults, merge/conflict rules, durable coordinate labels, problem options, and overrides. The result must cover all 23 files, retain Cartesian value, and remove zero-use step dimensions and the seven generic problem grids.

### Choose benchmark data-flow and scheduling edge semantics

Label: wayfinder:grilling. Blocked by Choose the labelled Cartesian benchmark language and the map's canonical persisted identity/direct-discovery decision.

## Question

Decide whether local study_from/artifact_from implies scheduling or must be paired with after; define explicit pre-existing ID references, coordinate matching or match-axis syntax, local after edges, external slurm_dependencies, ambiguity failures, chain propagation, and once-only output-ID minting. Require every local consumer to be provably ordered after its producer.

### Specify atomic benchmark plans and resumable submissions

Label: wayfinder:grilling. Blocked by Choose benchmark data-flow and scheduling edge semantics.

## Question

Define the plan.json envelope and minimal entry schema, plan hashing/version/target metadata, atomic creation, and the submissions.json state machine. Decide partial-failure resume, already-submitted handling, dependency job recovery, retries, failure records, remote revision invariance, and the operator gate for any mixed-revision continuation.

### Specify exact-ID benchmark collection and minimal remote transfer

Label: wayfinder:prototype. Blocked by Specify atomic benchmark plans and resumable submissions and the map's immutable artifact/evaluation record decision.

## Question

Prototype the collection schema and exact transfer manifest. Compare one rsync files-from pull with a remote validated bundle. Include EvaluationRef's artifact parent, deduplicated artifact manifest/training summary paths, exact evaluation/provenance joins, metric namespaces, stable scan/export order, malformed-run behavior, and atomic preservation of the prior collection on any failure. Resolve artifact deletion while evaluation dependents exist.

### Decide serving analytics durability and storage

Label: wayfinder:grilling. No technical blocker; it can run in parallel after the map is created.

## Question

Decide whether outstanding predictions and aggregate analytics survive process restart, how long records are retained, whether multiple worker processes share state, and whether multiple hosts require one view. Compare lifespan memory, a bounded strict atomic JSON snapshot, direct stdlib sqlite3 with rollback journal, stdlib sqlite3 with WAL and deployment gates, aiosqlite, append-only events, SQLModel/SQLAlchemy, and an external database. For the snapshot, decide pending-record expiry/bounds, recent-row retention, aggregate-counter invariants, single-process locking, corruption handling, and whole-file rewrite limits. Choose the lowest total interface and dependency cost that meets the approved durability/concurrency contract.

### Define serving resource lifecycle and artifact-chain policy

Label: wayfinder:grilling. Blocked by Decide serving analytics durability and storage and the map's canonical persisted identity/direct-discovery decision.

## Question

Specify FastAPI lifespan construction/cleanup, injected-service ownership in tests, RPC/model/analytics resource closure, blocking database offload if applicable, exact observation update semantics, and artifact discovery by chain plus ID. Explicitly approve or reject cross-chain artifact serving on live Sepolia.

### Choose historical and online inference preparation boundaries

Label: wayfinder:prototype. Blocked by Choose the resolved workflow configuration algebra and the map's artifact-manifest contract decision.

## Question

Prototype a one-frame historical requested-window API and compare a focused online right-edge preparer with one tagged inference-request union. Preserve coverage checks, no-future online semantics, scaling, sequence selection, action masks, and artifact compatibility. Choose the interface that removes real duplication without hiding distinct algorithms behind a mode flag.

### Prove custom runtime glue can be deleted

Label: wayfinder:task, AFK. Blocked by Ratify the clean break against accepted architecture decisions.

## Question

Run fresh-environment and cluster-representative import/Lightning/TorchMetrics/acquire-interrupt probes to decide whether asyncio.run fully replaces core.async_runtime and whether MPLCONFIGDIR can be removed or must move to execution-environment configuration. Record environment versions and cleanup behavior; do not add a compatibility shim.

### Set code-size, dependency, documentation, and final audit gates

Label: wayfinder:grilling. Blocked by Ratify the clean break against accepted architecture decisions and the major storage/training design tickets.

## Question

Approve one production-LOC measurement, the hard cap without an artificial lower bound, per-subsystem gross/net reporting, fresh lock/environment dependency proof, post-refactor Vulture manual review, normative-versus-historical documentation policy, ADR supersession format, and required end-to-end smoke matrix.

## Fog to retain on the map

- The exact post-refactor dead-helper and dependency-removal list cannot be known until the replacement interfaces exist.
- Exact conversions for all 23 benchmark YAML files depend on the labelled-matrix and edge decisions.
- Final collection export columns depend on the artifact/training-summary/evaluation record schemas.
- Final per-phase LOC allocation depends on storage and training investigations; only the global cap is sharp now.
- Final documentation wording depends on the accepted ADR and interface decisions.
- Analytics migration or deliberate loss cannot be specified until durability is approved.

## Suggested scope boundary

The Wayfinder destination should be an approved, dependency-ordered clean-break specification and verification contract. Production implementation, legacy compatibility shims, adding Hydra, adding an ORM without an approved need, and replacing the accepted SSH/rsync/Slurm Execution Session are beyond that planning destination.
