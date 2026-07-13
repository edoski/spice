# SPICE clean-break cross-cut red team

Research date: 2026-07-10. Repository revision: `b9b9a53f`. Scope: omissions and
cross-couplings outside the storage, configuration/benchmark, and framework-focused
research notes. Recommendations are candidate decisions, not approvals.

## Conclusion

The proposed direction is credible, but the route is not ready for implementation. It
needs additional decisions around training-objective semantics, the one-family prediction
interface, feature compatibility, RPC retry ownership, the serving/mobile trust model,
research-script consumers, software provenance, dependencies, security, and replacement
of shallow tests.

The strongest new findings are:

- Total-loss-only training and tuning landed in `e804880b` while the repository's own A/B
  tracker still says the economic comparison is unfinished. The clean-break map must not
  silently ratify that behavior.
- The final gate “no SQLAlchemy ... dependencies” is impossible while retaining Optuna
  4.8. Optuna declares SQLAlchemy and Alembic as mandatory dependencies even when SPICE
  uses JournalStorage. The correct gate is no SPICE SQLAlchemy imports, no direct
  SQLAlchemy dependency, and no SQL-backed SPICE persistence.
- Web3.py 7.15 retries ordinary allow-listed HTTP methods, but its batch implementation
  bypasses that retry path. SPICE's batch-provider override and outer acquisition
  controller are not duplicate pass-throughs: one supplies delayed transport retry, the
  other range retry, batch splitting, and adaptive concurrency. They may be unified, but
  one cannot simply be deleted.
- Serving is not only a SQLite choice. The unauthenticated API exposes pending request IDs,
  accepts arbitrary transaction hashes, permits repeated overwrite, never enforces expiry,
  and has no retention. The mobile client also schedules against an unconfirmed head while
  the backend predicts from a confirmed head, shortening the requested delay.
- Sixteen tracked research scripts, 6,374 lines total, consume private modules, artifact
  SQLite, old collection fields, Matplotlib, and SciPy. Phase 5 and phase 6 will break them.
  Each must be approved as maintained, frozen historical evidence, or deleted.
- The proposed final gates cover only Python. The tracked Expo app and Solidity file are
  real consumers. The Solidity contract and `demo_contract_address` are currently unused
  by the mobile transaction flow and are clean deletion candidates unless the product
  explicitly chooses to bind observations to that contract.

## Cross-verification of the candidate and existing research

| Claim | Result | Evidence |
| --- | --- | --- |
| Production Python is 29,004 lines; pytest has one stale evaluator-list failure; 23 benchmark YAML files exist and 17 use case dimensions. | Confirmed by the configuration/benchmark research and current tree. “17 checked-in benchmarks” is not the total inventory. | [configuration/benchmark research](clean-break-config-benchmark-semantics.md) |
| Stock Lightning checkpoints are finite-gated. | Disproved. The framework research's source and runtime diagnostic are sound: `ModelCheckpoint` can write a first nonfinite monitored value. | [framework research](clean-break-framework-semantics.md) |
| Native Lightning resume also restores a freshly reconstructed DataLoader generator's advanced shuffle state. | Disproved by the framework research. The candidate must approve restarted permutations or persist generator state. | [framework research](clean-break-framework-semantics.md) |
| Direct evaluation discovery works with `{kind,id,chain}`. | Disproved. The proposed path also needs parent artifact ID. | [persistence research](clean-break-persistence-semantics.md), [configuration/benchmark research](clean-break-config-benchmark-semantics.md) |
| Promoted roots are immutable while studies resume in place. | Internally contradictory until studies are declared append-only mutable or hidden until terminal. | [persistence research](clean-break-persistence-semantics.md) |
| Two output-directory renames make cutover atomic. | Disproved. They create a crash/visibility gap; the persistence research's recoverable-state-machine recommendation stands. | [persistence research](clean-break-persistence-semantics.md) |
| Local active storage has eight artifact databases and five corpus databases. | Confirmed by current filesystem inventory. Historical backup databases are additional conversion inputs. | `find outputs -path '*/.spice/state.sqlite'` on 2026-07-10 |
| WAL is automatically the lean serving backend. | Disproved. Durability, process count, filesystem, and trust model must be approved first. Memory, bounded JSON, and rollback-journal SQLite remain credible. | [configuration/benchmark research](clean-break-config-benchmark-semantics.md) |
| Removing SPICE's SQL persistence removes SQLAlchemy as a dependency. | Disproved, including the configuration/benchmark note's statement that the dependency should disappear. Optuna 4.8 mandates `sqlalchemy>=1.4.2` and Alembic. | [configuration/benchmark research](clean-break-config-benchmark-semantics.md), [Optuna 4.8 package metadata](https://github.com/optuna/optuna/blob/v4.8.0/pyproject.toml#L192-L202) |
| Web3's configured exception retry also covers `AsyncHTTPProvider.make_batch_request`. | Disproved in Web3.py 7.15 source. Ordinary requests call the exponential-backoff path; batch requests call the HTTP session directly. | [Web3.py 7.15 `AsyncHTTPProvider`](https://github.com/ethereum/web3.py/blob/v7.15.0/web3/providers/rpc/async_rpc.py#L120-L189) |
| The current architecture has an active Objective Runtime and representation registry/identity. | Disproved. Objective Runtime was deleted in `e804880b`; production has no representation registry or persisted representation ID. `CONTEXT.md` and ADR 0003 are stale on these facts. | [CONTEXT.md](../../../CONTEXT.md), [ADR 0003](../../adr/0003-representation-seam-retained.md), `git show e804880b` |

One existing research claim is therefore disproved: deleting SPICE's SQL-backed modules
does not remove the transitive SQLAlchemy package while Optuna 4.8 remains. The direct
dependency and every SPICE import can still disappear. Other inspected claims were
confirmed or need the cross-cutting qualifications above. This note adds blockers; it does
not supersede the three earlier notes.

## Training objective, evaluator, and tuning semantics

Current training selection is hard-coded to validation `total_loss` in
[`_fit_policy.py`](../../../src/spice/modeling/_fit_policy.py). The sole prediction family also
declares `total_loss` as its primary metric in
[`min_block_fee_multitask/__init__.py`](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py).
Optuna returns `best_validation_total_loss` in
[`tuning_execution.py`](../../../src/spice/modeling/tuning_execution.py). Evaluators still
declare `profit_over_baseline` as their primary metric, but that primary designation is now
reporting metadata; it does not select epochs or trials.

This is a recent semantic change, not a long-settled baseline. Commit `e804880b` removed the
Objective models, the evaluation-objective runtime, the `profit_poisson_replay` recipe, and
economic selection. [`CLEAN_BREAK_TRACKER.md`](../../../CLEAN_BREAK_TRACKER.md) still records the
total-loss-versus-profit A/B as in progress and says the economic metrics and decision remain
to do. The route must freeze and adjudicate that evidence before declaring the current
behavior safe.

The macro-F1 audit answers a different question. Macro-F1 is diagnostic and does not drive
current model or trial selection. Its audit cannot approve the move from economic selection
to validation loss. Likewise, fixing full-split weighted cross-entropy can change every
validation objective and therefore Optuna rankings. The loss-denominator decision must be
made before accepting total-loss A/B results as final, or the old and new formulas must be
reported separately.

Recommended route rule: select one explicit training-selection contract and persist it in
study and artifact definitions. If it is fixed `validation.total_loss`, remove generic
primary/direction duplication from prediction semantics. If economic selection returns,
retain a small explicit choice rather than rebuilding a generic objective/evaluator plugin
stack.

## Prediction and feature interfaces

Features have three real checked-in alternatives and substantial graph behavior. The
Feature module earns its seam: it resolves dependencies, source requirements, warmup,
formulas, and a selected output matrix. Keep owner-local direct dispatch.

Prediction has one family. [`CompiledPredictionContract`](../../../src/spice/prediction/contracts.py)
has ten callable fields plus generic input, target, accumulator, and decoded-result
protocols. Every current evaluator and serving path ultimately requires concrete candidate
offsets. Deleting that callable bundle would not force alternative-specific branches across
callers because there is no alternative. It would remove a hypothetical seam.

A deeper concrete shape is one Min-Block-Fee task module that owns target fitting, target
materialization, loss/scorer construction, output heads, and offset decoding behind a small
interface used by Lightning and inference. Model families remain real adapters because
three architectures consume the same output-head description. Evaluators remain real
adapters because time-Poisson and block-Poisson select different event windows. The
`block_poisson_replay_300` alias is a recipe-name issue, not a third evaluator.

Feature compatibility also needs a decision. The current
[`feature_graph_fingerprint`](../../../src/spice/features/core.py) hashes selected names and raw
bytes for whole implementation files, including `core.py` and formula modules. A comment,
refactor, or change to an unused formula can invalidate every artifact; a NumPy or Polars
behavior change is not represented. This is an implementation-source fingerprint, not a
semantic contract fingerprint.

The lean choices are:

1. Persist an explicit feature-contract version plus ordered selected outputs, source
   requirements, and normal software provenance. Bump the version only for compatible
   behavior changes. This is recommended for understandability.
2. Keep the source-byte hash, name it honestly, and accept refactor-driven incompatibility.
3. Build normalized formula/AST hashes. This adds machinery and is not justified without a
   stronger content-addressing requirement.

The artifact conversion contract depends on this choice. Old feature hashes cannot be
silently reinterpreted as explicit semantic versions.

## Acquisition RPC: retain behavior, choose one retry owner

[`RetryingBatchAsyncHTTPProvider`](../../../src/spice/acquisition/rpc/transport.py) overrides
only batch transport. Web3.py's documented retry configuration applies exponential backoff
to ordinary allow-listed methods. In the 7.15 source, `make_batch_request` bypasses that
method-aware retry helper and posts once. Web3 also documents that async `gather()` of
ordinary requests can outperform JSON-RPC batching, but changing to one HTTP request per
block changes provider rate-limit and maximum-batch behavior, so documentation alone does
not justify it. See [Web3 retry behavior](https://web3py.readthedocs.io/en/v7.7.0/internals.html#retry-requests-for-http-providers),
[7.15 batch source](https://github.com/ethereum/web3.py/blob/v7.15.0/web3/providers/rpc/async_rpc.py#L171-L189),
and [batch guidance](https://web3py.readthedocs.io/en/v7.8.0/web3.main.html#batch-requests).

[`AcquisitionPullController`](../../../src/spice/acquisition/pull.py) adds different behavior:
ordered prefix writes, bounded range attempts, oversize splitting, provider-pressure
tracking, concurrency rung reduction/recovery, and a persisted runtime snapshot. Its outer
retry has no sleep. Deleting the provider override today would preserve retry count but
remove the only delayed backoff for batch calls. Keeping both layers multiplies the worst
case to provider retries inside each of up to 32 range attempts.

The clean design should make the full pull operation the deep module and keep controller
details internal. Prototype two implementations against PublicNode and Tenderly-compatible
fixtures:

- current JSON-RPC batches with one explicit transport backoff plus adaptive outer policy;
- stock Web3 ordinary calls via bounded `asyncio.gather`, using public per-method retry plus
  the same adaptive outer policy.

Preserve exact ordered rows, fee-history alignment, oversize classification, transient
classification, cancellation cleanup, provider-specific concurrency recovery, and the
runtime counters. Choose one owner for delay/backoff and one global attempt ceiling. Do not
replace these facts with a generic retry decorator.

Corpus identity also needs a finality rule. Acquisition validates block-number continuity
but stores no block hash or parent hash. Two pulls of the same semantic window can observe
different canonical bytes across a reorganization. The persistence ticket's same-ID,
different-content rejection is necessary; human approval should also decide confirmation
depth or an explicit “historical RPC view, no reorg proof” limitation.

## Serving, mobile, and contract form one behavioral slice

The current storage alternatives research is correct but downstream of a missing trust
decision. Current behavior is unsafe for a public network service:

- [`api.py`](../../../src/spice/serving/api.py) has no authentication or rate limit. Prediction
  is an RPC/model/database write and can be called without a bound.
- [`analytics.py`](../../../src/spice/serving/analytics.py) returns the newest rows, including
  pending rows and their request IDs. The mobile app filters pending rows only after the API
  response.
- [`inference.py`](../../../src/spice/serving/inference.py) accepts any receipt-bearing
  transaction hash for an exposed request ID. It does not enforce expiry, one-time state
  transition, transaction sender/recipient/value, target timing, or included-block relation.
  Repeated observations overwrite the row and analytics.
- Pending predictions are never expired or pruned. Leaving the mobile app cancels locally
  but leaves durable pending state.

The scheduling protocol also mixes heads. The backend subtracts
`confirmation_depth` before inference in
[`live_blocks.py`](../../../src/spice/serving/live_blocks.py), then expresses
`broadcast_after_block` relative to that confirmed block. The mobile scheduler compares it
to `provider.getBlockNumber()`, the unconfirmed latest head, in
[`scheduler.ts`](../../../apps/mobile/src/scheduler.ts) and
[`sepolia.ts`](../../../apps/mobile/src/sepolia.ts). With the default depth two, offsets one and
two can broadcast immediately, and longer offsets are shortened by about two blocks.
`prediction_ttl_seconds` is also independent of artifact max delay, so a future artifact
with delay above the default 600 seconds can expire before its scheduled broadcast.

The Solidity contract is not part of the flow. The server requires and returns
`demo_contract_address`, but the app sends a native transfer to an arbitrary user-entered
recipient. Nothing calls [`SpiceDemo.ping`](../../../contracts/SpiceDemo.sol). The lean default
is to delete the contract, environment variable, response field, and validation. Keeping it
requires a concrete protocol that binds request, sender, and on-chain event; that is product
work, not a storage refactor.

Decide first whether serving is a loopback/single-user demo or a network service. For a
loopback demo, bind locally, state the loss/trust assumptions, use one process, and choose
memory or a bounded snapshot if restart durability is needed. For a network service, define
authentication, authorization/capability ownership, rate limits, observation attestation,
retention, and multi-process behavior before selecting persistence.

The TypeScript types manually duplicate Pydantic response shapes, and `fetch<T>` only casts
JSON. `npm run typecheck` passes in the current workspace, but it cannot detect a backend
schema change. The clean route should choose one lean contract check: generated OpenAPI
types, or one exact OpenAPI/property compatibility test without adding a runtime schema
library. Final verification must include `npm ci` and `npm run typecheck`. No Solidity gate
is needed if the unused contract is deleted.

## Benchmark scripts and research assets are hidden consumers

There are 16 tracked scripts under `benchmarks/scripts`, totaling 6,374 lines. Examples of
clean-break coupling include:

- [`merge_ethereum_pectra_jun20_corpus.py`](../../../benchmarks/scripts/merge_ethereum_pectra_jun20_corpus.py)
  imports private Parquet materialization, current root materialization, and SQLite corpus
  state.
- [`summarize_ethereum_pectra_edge_case_ci.py`](../../../benchmarks/scripts/summarize_ethereum_pectra_edge_case_ci.py)
  queries artifact `evaluation_summary` SQLite directly.
- Window scanners load current SQLite corpus manifests.
- Figure renderers hard-code current `collection.json` records and exported column names.

The test suite does not execute these scripts. Matplotlib and SciPy are not declared project
dependencies; they currently arrive incidentally through the scientific dependency graph.
Removing scikit-learn or changing Lightning extras can break research reproduction even
when all Python package tests pass.

Classify each script before phase 5:

- maintained operator/research tool: rewrite against public manifest/collection records,
  add a small representative fixture, and declare a `research` dependency extra;
- frozen historical method: retain script, exact inputs, lock/hash, and outputs together in
  an external archive rather than pretending current code supports it;
- one-shot obsolete helper: retain provenance in the conversion inventory, then delete it.

Local ignored `benchmarks/exports` and `benchmarks/figures` occupy about 253 MB. They are not
part of Git or active-output cutover but may be the only publication evidence. Freeze or
archive selected assets before renaming storage. Do not ingest them into canonical runtime
records.

The 22 checked-in evaluation-suite YAML files contain 11,236 lines and ship inside the
wheel. Large generated window lists may belong with benchmark research data rather than
general package configuration. Whether to move them cannot be decided until the labelled
benchmark language and maintained-script classification are approved.

## Packaging, security, execution, and provenance

The dependency gate needs precise meanings:

- Optuna 4.8 mandates SQLAlchemy and Alembic. “No SQLAlchemy dependencies” is false. Require
  no SPICE imports, no direct dependency, and no SQL-backed SPICE persistence instead.
- SPICE directly imports `aiohttp` and `eth_typing` but declares neither. If the RPC design
  still handles aiohttp exceptions/timeouts, declare aiohttp directly. Remove the
  `eth_typing.HexStr` import or declare it; a transitive type-only dependency is not a clean
  interface.
- Directly imported TorchMetrics and the official Lightning pruning callback require direct
  `torchmetrics` and `optuna-integration` dependencies, as the framework research found.
- `uvicorn[standard]` should be compared with plain `uvicorn` or a `serving` extra. The
  standard extra is justified only if its event loop, parser, watch, dotenv, or WebSocket
  features are intentionally used.
- Matplotlib and SciPy belong in a research extra only for scripts approved as maintained.

`uv audit --locked --python-platform x86_64-unknown-linux-gnu` currently returns 29 advisory
records across the lock's platform variants for aiohttp, Mako, Torch, and urllib3; some are
duplicate GHSA/PYSEC records and some may be unreachable in SPICE. The final gate should
not be a context-free zero count. It should update fixable direct/transitive versions,
record target-platform resolution, classify reachability, and require explicit acceptance
for unresolved findings. The existing tracker already flags this work in
[`CLEAN_BREAK_TRACKER.md`](../../../CLEAN_BREAK_TRACKER.md).

ADR 0005's core conclusion survives the deletion test: removing the Execution Session
would spread SSH, rsync, Slurm, remote Python, provenance, and follow behavior across several
callers. Its catalog-envelope consequence does not survive. The implementation can also
use Slurm's official `sbatch --parsable` output instead of parsing English text; Slurm
documents an ID with optional semicolon-separated cluster name
([`sbatch --parsable`](https://slurm.schedmd.com/sbatch.html#OPT_parsable)). Verify final-state
normalization and log-follow behavior on the actual cluster before preserving the rest by
default.

The target artifact manifest describes domain/config provenance but not normal software
provenance. `remote_git_commit()` is captured for benchmark submission, not standalone
artifacts. The feature source hash is an incomplete substitute. Define one small durable
record shared by study/artifact/evaluation/benchmark evidence: schema version, SPICE package
version, source revision when available, Python, and the small framework/version set that
changes numerical or storage behavior. Device/GPU facts belong in the training summary or
audit record, not duplicated across definitions. Never record RPC URLs or credentials.

`src/spice/__init__.py` mutates the environment at import and duplicates the package version
as unused `__version__ = "0.1.0"`. If the Matplotlib mutation is removed, the lean package
initializer can be empty; package metadata should be the single version source.

Final packaging verification should build and install the wheel in a fresh environment,
then exercise config-resource loading and the CLI entry point. `uv sync` from the worktree
does not prove that Hatch includes every required YAML/data resource.

## Test depth

The current suite is about 15,585 Python lines. Benchmark, storage, and modeling tests alone
are about 7,668 lines, with extensive monkeypatching across module internals. That is
expected for the current shallow architecture but must not be carried forward as a second
compatibility layer.

Use replace-not-layer testing:

- delete catalog, codec, selector, root-handle, BatchPlan, fit-policy, result-index, and
  collection-resolver tests with their modules;
- test direct root storage/discovery, the concrete prediction/scorer module, Lightning fit,
  exact collection, and serving through their new interfaces;
- keep small pure formula tests for features, temporal accounting, and evaluator selection;
- add only behavior-level conversion evidence, not tests asserting that old classes or
  payloads stay absent/present;
- add one maintained-script fixture, wheel-install smoke, and mobile type/contract check.

Do not set a test-line target. Require that a replaced shallow module does not retain its old
unit-test layer once the deeper interface test covers the same behavior.

## Wayfinder ticket additions

The titles and questions below are copy-ready. Blocking relationships use ticket names.

### Freeze the total-loss versus economic-objective A/B evidence

Type: `wayfinder:task` (AFK). No blockers.

## Question

Recover the submitted total-loss and profit-selected A/B run identified in
`CLEAN_BREAK_TRACKER.md`; record terminal job states, exact source revision, configs,
artifact/corpus/evaluation IDs, objective formulas, loss aggregation formula, sample/window
joins, and economic plus predictive metrics. Freeze raw plans, submissions, collections,
logs, and hashes without rewriting them. If the run is incomplete, state exactly what can
and cannot be concluded rather than rerunning under changed semantics.

### Choose training and tuning selection semantics

Type: `wayfinder:grilling` (HITL).

Blockers: **Freeze the total-loss versus economic-objective A/B evidence** and **Define
shared metric scorer semantics**.

## Question

Approve the one metric/formula that selects best epochs, early stopping, Optuna trials, and
pruning: fixed validation total loss, economic replay profit, or a deliberately scoped
choice. Decide whether evaluator “primary” remains reporting-only, whether min-delta affects
selection or only stopping, and how the chosen selection contract is persisted in studies
and artifacts. Do not infer approval from the current hard-coded total-loss implementation.

### Prototype the concrete one-family prediction interface

Type: `wayfinder:prototype` (HITL).

Blockers: **Choose training and tuning selection semantics**, **Define shared metric scorer
semantics**, and **Classify recipe names, executable discriminators, and domain identities**.

## Question

Compare the current callable-heavy `CompiledPredictionContract` with one concrete
Min-Block-Fee task module. The prototype must cover output heads, fitted class/fee state,
target batches, shared scorer/loss, offset decoding, model-family construction, evaluator
input, and serving while deleting the one-family registry and generic target/accumulator/
decoded-result protocols. Keep feature, model-family, and evaluator dispatch only where real
alternatives remain. Choose the smallest interface with the highest locality.

### Choose feature compatibility and fingerprint semantics

Type: `wayfinder:grilling` (HITL).

Blockers: the map's artifact-manifest contract decision and **Prototype the concrete
one-family prediction interface**.

## Question

Choose whether artifact compatibility uses an explicit feature-contract version plus
ordered outputs/source requirements, the current raw-source implementation hash, or another
minimal contract. Define what changes remain compatible, how software revision complements
the feature identifier, and how converted hashes are mapped or rejected. Reject both silent
formula drift and refactor-only incompatibility unless deliberately approved.

### Prototype one-owner RPC retry and adaptive acquisition

Type: `wayfinder:prototype` (HITL).

No blockers.

## Question

Against deterministic failure fixtures and representative PublicNode/provider probes,
compare JSON-RPC batch acquisition with explicit batch backoff against bounded ordinary
Web3 calls using public retry. Preserve ordered prefix writes, fee-history alignment,
oversize splitting, transient classification, cancellation, concurrency rung reduction and
recovery, runtime counters, and exact attempt ceilings. Choose one owner for delay/backoff
and document why Web3 7.15's non-retrying batch path is or is not wrapped.

### Define serving trust, exposure, and observation transitions

Type: `wayfinder:grilling` (HITL).

No blockers. This ticket becomes a blocker for **Decide serving analytics durability and
storage**.

## Question

Decide whether serving is loopback single-user, trusted-LAN, or public. Define prediction
rate/bounds, request ownership, pending expiry and retention, one-time observation
transitions, duplicate/idempotent behavior, transaction attestation, analytics visibility,
and multi-process/host assumptions. Choose the minimum authentication and authorization
needed for that exposure. Do not use an exposed request ID as authority.

### Reconcile confirmed-head inference with the mobile timed-transfer protocol

Type: `wayfinder:prototype` (HITL).

Blockers: **Define serving trust, exposure, and observation transitions**, **Choose
historical and online inference preparation boundaries**, and **Define serving resource
lifecycle and artifact-chain policy**.

## Question

Exercise backend and Expo client together and choose one scheduling contract for confirmed
observation head, live head, selected offset, broadcast threshold, target block, TTL,
background cancellation, receipt observation, and RPC disagreement. Validate chain/artifact
metadata and API shape. Decide whether to delete the unused SpiceDemo contract and
`demo_contract_address`, or define the exact event/transaction protocol that makes them
real. Choose generated OpenAPI types or one lean schema-compatibility test.

### Classify research scripts and generated benchmark assets

Type: `wayfinder:grilling` (HITL).

No blockers.

## Question

Classify every tracked `benchmarks/scripts` file and every publication-critical ignored
export/figure as maintained tool, frozen historical method, or obsolete one-shot helper.
For maintained tools, name their public input interface and direct dependencies. For frozen
methods, name the exact code/input/output/hash bundle and archive location. Approve whether
large evaluation-suite YAML remains package configuration or becomes benchmark data.

### Prototype maintained research consumers on clean collection records

Type: `wayfinder:prototype` (HITL).

Blockers: **Classify research scripts and generated benchmark assets** and **Specify
exact-ID benchmark collection and minimal remote transfer**.

## Question

Port one maintained window scanner, one CI summarizer, and one figure renderer to strict
manifest/collection JSON without private imports or artifact SQLite. Define stable metric
namespaces, run-level data needed for confidence intervals, deterministic ordering, and the
small `research` dependency extra. Use the result to approve the public research-tool
interface before updating or deleting the remaining scripts.

### Set dependency, packaging, and vulnerability policy

Type: `wayfinder:grilling` (HITL).

Blockers: **Prototype Journal lifecycle and coherent locking**, **Validate per-epoch pruning
without trial artifacts**, and **Prototype one-owner RPC retry and adaptive acquisition**.

## Question

Approve direct runtime, serving, research, and development dependency sets; correct the
SQLAlchemy gate to account for Optuna's mandatory transitive dependency; decide plain versus
standard Uvicorn; remove or declare direct aiohttp/eth-typing use; and require direct
TorchMetrics/Optuna-integration dependencies. Define wheel-install, lock-per-target,
`npm ci`/typecheck, and vulnerability-review gates, including how fixable, unreachable, and
unfixed advisories are handled.

### Define minimal software and runtime provenance

Type: `wayfinder:grilling` (HITL).

Blockers: the map's study/artifact/evaluation record decisions, **Specify atomic benchmark
plans and resumable submissions**, and **Set dependency, packaging, and vulnerability
policy**.

## Question

Define the one small software-provenance record shared or referenced by studies, artifacts,
evaluations, benchmark collections, conversion reports, and audits. Include only facts
needed to interpret/reproduce behavior: schema, SPICE version, source revision when
available, Python, behavior-critical frameworks, and target hardware facts where relevant.
Specify safe startup/run logging for artifact ID, chain, revision, schema, and sanitized RPC
reference while excluding URLs and credentials.

### Audit the retained Execution Session against public CLIs

Type: `wayfinder:research` (AFK).

Blockers: **Ratify the clean break against accepted architecture decisions**.

## Question

Apply the deletion test to the current Execution Session and verify its SSH, rsync, Slurm,
follow, provenance, remote-revision, and remote-runner behavior against the installed local
and cluster command versions. Identify implementation that public OpenSSH/rsync/Slurm
interfaces replace, including `sbatch --parsable`, without deleting the deep target-bound
session or retaining catalog envelopes. Record state-normalization, log-race, quoting, and
config-size findings.

### Approve replacement test surfaces

Type: `wayfinder:grilling` (HITL).

Blockers: all selected storage, configuration, training, prediction, benchmark, acquisition,
and serving interface/prototype tickets.

## Question

For each approved deep module, name its interface-level invariants and the old shallow test
files it replaces. Require focused pure-domain tests, real CPU Lightning and lifespan tests,
filesystem/crash tests at storage interfaces, one maintained research-script fixture,
wheel-install smoke, and mobile contract/typecheck. Reject compatibility and architecture-
transition tests that merely assert deleted names or layouts.

## Blocking changes to existing tickets

- **Decide serving analytics durability and storage** must be blocked by **Define serving
  trust, exposure, and observation transitions**.
- **Define serving resource lifecycle and artifact-chain policy** must feed **Reconcile
  confirmed-head inference with the mobile timed-transfer protocol**.
- **Prototype strict best-checkpoint and summary conversion** must also be blocked by
  **Choose training and tuning selection semantics** and **Choose feature compatibility and
  fingerprint semantics**.
- **Set code-size, dependency, documentation, and final audit gates** must also be blocked by
  **Set dependency, packaging, and vulnerability policy**, **Classify research scripts and
  generated benchmark assets**, and **Approve replacement test surfaces**.
- The canonical corpus-identity ticket must explicitly decide reorganization/finality
  limits, same-definition/different-content rejection, and whether block hashes are outside
  the raw schema by design.

## Fog to retain

- Whether the submitted economic-objective A/B completed with joinable evidence is unknown
  until its frozen run and cluster state are inspected.
- Exact maintained-script ports and dependency extras depend on script classification and
  the final collection schema.
- Whether JSON-RPC batches or ordinary concurrent calls behave better depends on measured
  PublicNode/Tenderly limits; the current source analysis only establishes retry semantics.
- Final vulnerability exceptions and target-platform lock deltas depend on the selected
  framework versions and CUDA index.
- Exact software-provenance fields depend on the final durable record schemas and whether
  execution can run from installed wheels without a Git checkout.
- The post-refactor dead-code and test-deletion list becomes sharp only after replacement
  interfaces exist; Vulture is currently clean and must be rerun with manual review.
- Final disposition of the 11,236-line evaluation-suite data depends on the benchmark
  language and research-consumer decisions.

## Suggested out-of-scope boundaries

- Replacing Optuna solely to eliminate its transitive SQLAlchemy dependency. That trades a
  truthful packaging gate for a larger custom tuner.
- Designing new prediction targets or economic objectives beyond choosing between the
  already implemented total-loss and replay-profit semantics.
- Building a multi-tenant public serving platform if the approved destination is a local
  demo. Conversely, public exposure cannot be declared out of scope while deploying the
  unauthenticated API publicly.
- Rewriting frozen historical plotting methods to current interfaces when an immutable
  code/input/output bundle preserves the result more faithfully.
- Adding smart-contract behavior unless the approved mobile protocol needs it.
- Permanent compatibility readers, dual metrics under one name, or transition tests.
