# Lean alternatives for the SPICE temporal ML core

Date: 2026-07-10

Status: research and candidate routes only. Nothing here approves a target, trainer,
dependency, evaluator, serving design, ADR change, or deletion. The current code, the
foundation paper, historical notes, prior ADRs, and this report are all fallible evidence.

Scope: the temporal module's preprocessing interface, tensorization, fitting host, metrics,
hyperparameter optimization, economic replay, and the serving pieces that consume model
outputs. This report asks a narrow question: what is the smallest understandable route that
retains scientifically useful capability?

Companion theory audits:

- `docs/research/issue-1/temporal-preprocessing-theory-audit.md`
- `docs/research/issue-1/temporal-training-evaluation-theory-audit.md`
- `docs/research/issue-1/temporal-paper-alignment-audit.md`
- `docs/research/issue-1/temporal-evaluation-statistics-cross-review.md`

## Bottom line

Framework substitution is not the first decision. The decision clock, action, outcome,
deadline, split ownership, and economic estimand must settle first. Those choices determine
whether masks, variable windows, Poisson arrivals, multiple prediction heads, weighted loss,
and several registries are needed at all.

Five lean candidates survive this audit:

1. Preserve the intentional current-forming-block task only if every chain's block-open
   information set and a deployable serving instant can be proved. Otherwise use the
   confirmed-head/next-block task already implied by serving. Do not silently shift the
   target.
2. Replace the current Lightning/manual hybrid with either one idiomatic automatic-Lightning
   implementation or one short direct-PyTorch implementation. The hybrid should not survive.
3. Preserve HPO as an intentional research phase, but use fixed configurations for baseline
   and ablation work. Retain Optuna only for a surviving search space large enough to need
   adaptive search and persisted trials.
4. For normalized metrics under independent homogeneous arrivals, replace Monte Carlo replay
   with deterministic weighting: fixed-interval exposure weights for named windows, or the full
   window-inclusion kernel to reproduce the current uniform-start distribution. Keep stochastic
   replay only for a paper-reproduction view or a question that genuinely depends on finite
   arrivals or request timestamps.
5. After feature and target ablations, flatten one-option registries into directly called deep
   modules. Keep dispatch only where two approved implementations actually remain.

The provisional smallest composite route is: one approved decision contract, a compact causal
feature set, fixed block contexts, classification-only control, a small LSTM, standard
`DataLoader`, direct NumPy scaling/economic metrics, deterministic named-window evaluation, and a
single fitting host selected by prototype. This is a control route, not a predetermined winner.
Optuna, engineered features, multitask loss, and larger models remain serious candidates and
return only when measured benefit justifies their concepts.

The serving-specific conclusion is less dramatic: FastAPI plus Pydantic and the standard-library
`sqlite3` module are already the lean mature choices if an HTTP demo with persistent analytics is
required. A new ORM, async database wrapper, or serving framework is unlikely to make that path
smaller. The meaningful gate is whether HTTP serving and persistent analytics belong in the
thesis scope at all.

## Method and measured surface

The audit read production code, tests, package configuration, current and historical feature
rationale, the three companion theory audits, and the earlier framework/persistence clean-break
research. Framework claims were checked against the owning projects' documentation. Small
locked-environment probes measured scaler parity and deterministic exposure weighting. No model
was trained and no production or architecture documentation was changed.

These line counts describe the present surface. They are not promised deletion totals: some
files contain behavior any replacement must retain, and groups overlap conceptually.

| Present surface | Production lines | Focused test lines | Concepts carried |
| --- | ---: | ---: | --- |
| Feature subsystem | 1,423 | 349 | catalog, source specs, feature specs, dependency graph, registry, fingerprints, three recipe families |
| Prediction subsystem | 1,023 | 467 | generic prediction contract, target batches, training state, two heads, loss, accumulator, decoding |
| Lightning host plus custom fit policy | 580 | 404 | Trainer hooks, manual optimization, custom best state, checkpoint state, callbacks |
| Narrow HPO/study core | 1,587 | 833 | typed tuned records, Optuna lifecycle, study manifest/codecs/rendering, tune workflow |
| Evaluation subsystem | 1,253 | 788 | evaluator registry/configs, two Poisson adapters, selection protocol, accounting, metric catalog, result ABI |
| Serving subsystem | 983 | 299 | FastAPI routes, RPC client, runtime assembly, inference mapping, SQLite analytics, DTOs |

The dependency tree also makes the net cost visible:

- Lightning 2.6.5 brings `pytorch-lightning`, `torchmetrics`, `lightning-utilities`, and related
  framework packages.
- Optuna 4.8.0 brings Alembic and Colorlog and uses SQLAlchemy. SQLAlchemy is also a direct SPICE
  dependency, so deleting Optuna alone would not delete SQLAlchemy.
- scikit-learn 1.8.0 brings SciPy, Joblib, and Threadpoolctl. Its only production import is the
  scaler in `src/spice/temporal/input_normalization/scaling.py`.

Dependency count is evidence, not a verdict. A mature package can be cheaper than a subtly wrong
home-grown implementation. It earns its place when it deletes more SPICE concepts and tests than
it adds to the reader's mental model.

## Corrected premise: current row is intentional, not automatically wrong

Commit `e0b2e68e` (`fix(features): enforce safe current-row fee dynamics`) deliberately removed
an unsafe same-block-closed feature route and retained a block-open/current-row route. Current
`PROGRESS.md:243-249`, `ARCHIVE.md:9-36`, and
`src/spice/features/ARCHITECTURE.md:30` explain the intended information set:

- `base_fee[t]` is known from parent state before block `t` execution under EIP-1559;
- finalized gas usage, transaction count, and similar block facts are lagged to `t-1`;
- offset zero may therefore mean the next-forming/current action block `t`, not an already closed
  block.

That is a serious causal route. It corrects any framing that treats the offline anchor inclusion
as automatically accidental. It still does not prove cross-layer parity.

Current executable meanings are:

```text
offline feature/context end             row h
offline class k target and realization  row h + k
offline baseline                        row h
serving input end                        confirmed row h
serving class k broadcast                after h + k
serving class k inclusion target         h + k + 1
serving baseline                         h + 1
```

Serving fetches `latest - confirmation_depth` at
`src/spice/serving/live_blocks.py:51-65`, then performs the explicit `+1` mapping at
`src/spice/serving/inference.py:70-105`. It implements a post-confirmation task, not the documented
block-open task.

The current safe-feature claim also needs a narrower audit. Gas, limit, and transaction facts are
lagged. The default cadence/calendar features are not: `seconds_since_previous_block`, hour, and
day use realized `timestamp[h]` directly at
`src/spice/features/sets/core_fee_dynamics/_time.py:21-94`. The removed historical
`block_open_lagged` implementation lagged those timestamp-derived values. Calendar time may be
known from the decision clock, but actual inter-block duration is not automatically the same fact
as an unmined row's realized timestamp. Per-chain fee and timestamp availability must be proved;
Ethereum's EIP-1559 recurrence cannot be generalized to Polygon and Avalanche by name alone.

The finalized companion chain audit confirms that this may be a chain-and-regime decision, not
one shared rule. The Polygon corpus crosses the Lisovo activation at block `83,756,500`; the
post-Lisovo Bor v2.6 validator no longer makes the child base fee a simple exact parent-only
recurrence. Avalanche's Octane/ACP-176 calculation needs parent
`Extra` fee state plus the child timestamp, and later Granite-era fields are not in SPICE's current
canonical corpus. `temporal-chain-fee-protocol-audit.md` owns the primary-source citations and
date/block classification. No blanket “EIP-1559 means current fee is available” claim is accepted
for all chains or corpus rows.

Three routes remain:

### Route C0: preserve a block-open/current-forming-block task

Define the decision immediately before or during block `t` assembly. Build the row from parent
state plus current wall-clock facts, not by reading the finalized block and calling it ex ante.
Class zero targets inclusion in `t`. Requests arriving between openings must map to the next
eligible opening, not backward to a completed row. Serving must obtain or synthesize the same
safe row and demonstrate that broadcast can still reach the proposer.

This route preserves the intentional extension. Reject it if any supported chain cannot expose
the required facts before inclusion, or if the demo cannot act at that instant.

### Route C1: confirmed-head/next-block task

Observe finalized/confirmed row `h`. Class zero targets the first eligible future block `h+1`.
Keep row `h` base fee as an input, shift offline outcomes/baseline forward, and make replay retain
the actual request-time rule. This matches the current serving information set and the paper's
next-block wording, but it changes the intentional extension and needs explicit approval.

### Route C2: expose both tasks

Keep separate named task definitions, artifacts, evaluators, and serving claims. This is coherent
but doubles theory and testing. For a lean undergraduate project, reject it unless comparing
block-open and post-confirmation decisions is itself a thesis question.

Required prototype: one three-block fixture per chain must pass feature availability, target
construction, decoded action, offline realization, and serving response with the same row meaning.
No framework or model comparison should decide the route.

## Fitting host: choose one owner

The current path uses Lightning as a host for a manual loop. `SpiceLightningModule` disables
automatic optimization, then manually zeros gradients, runs backward, clips, and steps one AdamW
optimizer at `src/spice/modeling/lightning_module.py:57-107`. SPICE also owns the best-state policy,
nonfinite handling, checkpoint payload, callback protocol, runtime plan, and batch sampler.
Lightning checkpointing is disabled by `src/spice/modeling/training_runner.py:94-105`.

Lightning's own documentation recommends automatic optimization for ordinary single-optimizer
research cases and reserves manual optimization for advanced cases such as multiple optimizers or
GANs ([Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)).
SPICE has one optimizer, true 32-bit precision, and one GPU. No distributed, mixed-precision, or
multi-optimizer requirement is currently implemented.

### Route T0: direct PyTorch

One `fit(...) -> FitResult` module owns the epoch loop, AdamW, gradient clipping, validation,
raw-best state, patience, and the approved resume guarantee. PyTorch's beginner workflow presents
this loop directly, so its mechanics are teachable rather than hidden
([PyTorch optimization loop](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)).

Likely advantages:

- delete Lightning, framework hooks, wrapper state, and framework-specific tests;
- make the scientific order explicit: seed, construct, train, validate, select;
- keep one device and one precision because those are the actual requirements;
- expose per-epoch validation directly to Optuna without a separate integration package.

Capability at risk:

- framework-managed accelerator/precision/distributed evolution;
- stock callback/checkpoint lifecycle;
- convenient future multi-device training.

Reject this route if the approved resume/checkpoint/progress contract expands the direct loop into
a local reimplementation of Trainer. Current resume is already not an exact stochastic
continuation, so the owner can also choose epoch-boundary restart or no mid-fit resume instead of
preserving machinery by default.

### Route T1: idiomatic automatic Lightning

Return the differentiable loss from `training_step`; let Trainer own zero-grad, backward, step,
and configured clipping. Use stock `EarlyStopping`/`ModelCheckpoint` only where their exact
semantics are approved, plus the smallest finite-map callback that cannot be expressed safely by
stock callbacks. Use native checkpoint resume.

Likely advantages:

- keep managed device, checkpoint, callback, and Optuna integration capability;
- delete manual optimization and much of the custom fit/checkpoint policy;
- use a common research framework rather than a private lifecycle.

Costs:

- an undergraduate must learn Lightning hooks, logging reduction, callback order, and checkpoint
  ABI in addition to PyTorch;
- stock `ModelCheckpoint` is not finite-gated, and raw-best versus `min_delta`-qualified best must
  still be chosen;
- a reconstructed shuffled `DataLoader` does not automatically resume its advanced generator
  state.

Reject this route if the prototype retains `_fit_policy.py`, manual optimizer calls, custom
checkpoint envelopes, and duplicate precision/device policy. That would preserve the current
shallow layering.

### Route T2: Lightning Fabric or another trainer library

Fabric can retain Lightning's device/backward conveniences while exposing a direct loop. In the
current one-GPU, 32-bit setting it retains the dependency and adds a second framework vocabulary
without deleting the loop. Ignite, skorch, Hugging Face Trainer, and similar new dependencies have
the same burden for this custom temporal task. Reject these middle routes unless a concrete
prototype is smaller than both T0 and T1.

### Host acceptance test

Prototype T0 and T1 on the same corrected tiny task. Measure the whole implementation, not only
the central loop:

- production, test, and config lines changed/deleted;
- concepts a reader must learn;
- initial-state reproducibility;
- exact validation numerator/denominator;
- finite failure before and after a valid best;
- interruption at an epoch boundary and the approved resume behavior;
- best weights/value/one-based epoch;
- an Optuna intermediate report and actual early prune;
- full and tail batch behavior.

Choose one host. Do not create a framework-neutral trainer interface with both adapters unless both
will remain supported; one adapter would be a hypothetical seam.

## HPO: preserve the research question, shrink the boundary

HPO is an intentional extension, not accidental machinery. `PROGRESS.md:213-227` already proposes
a sensible policy: a bounded calibration search on the canonical feature set, then fixed
train/evaluate grids for structural ablations. The current `large_capacity_hpo` benchmark runs 32
trials for each chain/model cell.

The search spaces are not small exhaustive grids:

| Space | Cartesian combinations |
| --- | ---: |
| LSTM large capacity | 10,368 |
| Transformer large capacity | 6,144 |
| Transformer-LSTM large capacity | 36,864 |

An explicit exhaustive grid is not a capability-equivalent replacement for those spaces. Optuna's
TPE sampler is a legitimate candidate for mixed categorical search, and its RDB backend records
and resumes expensive studies ([TPESampler](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html),
[RDB resume](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/001_rdb.html)).

The current boundary has four correctness problems:

1. Every trial computes both validation and test summaries through
   `src/spice/modeling/persisted_training.py:93-124,192-214`; only validation loss is returned.
2. `trial.report`/`should_prune` run after full fitting at
   `src/spice/modeling/tuning_execution.py:201-228`. Pruning saves no training work. Optuna requires
   intermediate reporting during iteration
   ([Optuna pruning](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html)).
3. The current validation loss changes with batch partition because weighted CE is reduced
   incorrectly, while batch size is tuned.
4. Fresh studies get seeded TPE and configured Median/Nop pruning at
   `src/spice/storage/study_optuna.py:71-85`; resumed studies call `load_study` without sampler or
   pruner at line 91. Optuna documents that RDB storage does not save sampler/pruner instance state.
   Resume therefore does not continue the declared seeded sampler state, and a no-pruning study
   reloads a default pruner object even though current objective code happens not to call it.

Candidate routes:

### Route H0: fixed declared configuration

Use for the baseline ladder and every ablation whose question is one named change. It gives the
clearest causal comparison and needs no tuning trial. It is not a proposal to remove HPO globally.

### Route H1: small explicit grid

After the model is reduced, use existing benchmark Cartesian dimensions for a genuinely small
theory-driven design, such as a few learning rates and two hidden sizes. No new grid package is
needed. Prefer this when every combination is affordable and the table itself is explainable.

### Route H2: retained Optuna

Use for the approved wide or conditional space. Keep one exploration seed, common validation
origins, validation-only trials, explicit sampler/pruner, real per-epoch reports, and persisted
trial history. Rerun a few finalists on the same three-to-five declared seeds before final
selection. The final test remains sealed until configuration and seed protocol are frozen.

Do not add JournalStorage merely because it is newer. SQLAlchemy already exists in SPICE, and a
journal introduces application locking and recovery questions without solving sampler-state
resume. Retain RDB unless a measured filesystem or lifecycle problem proves Journal materially
smaller.

Rejection rules:

- H0/H1 fail if undocumented manual choice replaces an approved large search.
- H2 fails if it tunes on different validation examples, sees test, cannot prune but claims to,
  or keeps a huge space whose 32 trials are too sparse to answer the thesis question.
- Any route fails if “best validation trial” is reported as an unbiased test result.

## Replay: deterministic weighting before simulation

Current Poisson replay samples arrival timestamps, maps each to the latest sample timestamp, then
discards the arrival timestamp at `src/spice/evaluation/poisson_replay.py:28-61,79-105`. The model,
chain, and subsequent decisions do not depend on arrival count. Randomness therefore only repeats
decision rows with random weights.

For a fixed interval, let decision state `i` own an exposure duration `e_i` and deterministic
metric `m_i`. A homogeneous Poisson process of rate `lambda` gives expected count
`lambda * e_i`. Conditional on at least one arrival, the expected request mean is exactly:

```text
sum_i e_i m_i / sum_i e_i
```

For long-run spend with gas weight `g_i`:

```text
sum_i e_i g_i (baseline_i - realized_i)
-----------------------------------------
        sum_i e_i g_i baseline_i
```

`lambda` cancels from normalized metrics. Counts in disjoint intervals and their expected
`lambda * duration` are the defining homogeneous-Poisson properties; see the official MIT course
notes on [Poisson processes](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/).

A locked synthetic diagnostic used timestamps `[0, 10, 30, 45]`, state values
`[1, 2, -1, 4]`, window `[0,45)`, and rate `0.05`. Exact exposure weights were
`[10,20,15,0]`, giving `0.7777778`. One hundred thousand current-algorithm repetitions pooled
225,941 arrivals and produced `0.7788936`, the expected Monte Carlo approximation.

That diagnostic fixes the interval. The production evaluator also samples the interval start
uniformly. Whole-corpus duration weights are not equivalent because edge states appear in fewer
possible windows. An exact deterministic reproduction must integrate this window-inclusion
kernel; adopting named fixed windows is simpler, but changes the evaluation protocol.

Three estimands must not be conflated:

- equal weight per block/decision opportunity: evaluate every state once;
- equal weight per unit request time under homogeneous arrivals: exposure weighting;
- finite or coupled request workload: retain actual arrivals and stochastic simulation.

Route E0 is deterministic all-state or exposure-weighted evaluation on predeclared named windows,
or exact inclusion-kernel integration when the current random-window distribution must be
preserved. Route E1 retains Poisson only for faithful paper reproduction or a finite-workload question. If E1
survives, arrival timestamps must reach realization; otherwise it remains a weighting simulation,
not a request-time simulator.

The approved decision clock determines exposure direction. A current-forming-block policy maps
arrivals since the previous opening forward to the next eligible opening. A confirmed-head policy
may hold one observed state between blocks but must realize the first eligible future outcome.
The present backward `searchsorted` plus current-row fee cannot be approved for both tasks.

Benefits of E0:

- remove arrival-rate, repetition, and seed configuration for normalized metrics;
- remove conditional Monte Carlo integration noise and prevent its intervals from being mistaken
  for generalization uncertainty;
- make every model compare on identical decisions and weights;
- expose exact harmful-decision and deadline rates.

Reject E0 if the question depends on total event count, within-block arrival latency, capacity,
queueing, stateful re-decisions, stochastic inclusion, or request interactions. Validate E0 against
a high-repetition simulator, then delete the dual production path unless paper reproduction is a
named secondary result.

## Metrics and scaling: use packages only after choosing the questions

### Macro F1 correction

The earlier statement that stock TorchMetrics matched current SPICE was incorrect. TorchMetrics
1.9 and scikit-learn use union-active behavior by default; current SPICE skips every class with no
target support even if predictions activate it. For targets `[0,0]` and predictions `[0,1]`, SPICE
returns `2/3`; both standard implementations return `1/3`.

This correction does not make F1 useful. Offset classes are ordered economic actions, ties are
common on Polygon, and the paper does not report F1. The lean order is:

1. delete macro F1 if it answers no approved thesis question;
2. if Lightning and conventional F1 remain, use TorchMetrics and declare it directly;
3. if scikit-learn remains for simple research baselines, use its offline `f1_score`;
4. do not retain either dependency solely for F1.

TorchMetrics correctly accumulates state and synchronizes distributed metrics
([TorchMetrics overview](https://lightning.ai/docs/torchmetrics/stable/pages/overview.html)). It
does not automatically repair SPICE's weighted-loss denominator. That reducer still needs exact
classification numerator/summed-target-weight and regression numerator/sample-count state if
weighted multitask loss survives.

| Route | Best fit | Net burden |
| --- | --- | --- |
| Direct PyTorch/NumPy counts | One device, accuracy/tie counts, approved economic formulas | No dependency; a few transparent reductions and hand fixtures, but SPICE owns edge semantics |
| TorchMetrics | Retained Lightning/DDP plus conventional F1/accuracy/MAE state | Deletes distributed/state boilerplate; adds a direct dependency and metric lifecycle concepts |
| scikit-learn metrics | Offline research baselines already justify scikit-learn | Familiar CPU reference; moving predictions to CPU is acceptable for final scoring, but keeping SciPy/Joblib solely for one metric is poor leverage |

The differentiable training loss remains direct PyTorch under every route. Economic evaluation is
already array-oriented NumPy and has domain-specific denominators no general metric package can
choose. Use a package for a standardized metric, not to hide the approved economic definition.

For a classification-only thesis route, the minimal predictive surface is correctly aggregated
validation loss, tie-aware hit rate, and ordinary accuracy only for paper comparison. Economic
savings/regret, harmful-delay/deadline rate, and waiting behavior belong in the decision evaluator.

### StandardScaler versus NumPy

Current scaling is substantively sound but scikit-learn is used nowhere else in production.
`StandardScaler` uses training mean, population standard deviation, and scale `1` for constant
features ([scikit-learn StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)).
NumPy exposes the same mean and `ddof=0` standard deviation directly.

A local locked probe compared the installed `StandardScaler` with float64 NumPy mean/std and
zero-scale replacement:

| Matrix | Max mean delta | Max scale delta | Max transformed float32 delta |
| --- | ---: | ---: | ---: |
| 10,000 x 45 normal float32 | 0 | 0 | `4.77e-7` |
| constant plus ramp columns | 0 | 0 | 0 |
| large `1e12` offset plus noise | 0 | `1.18e-8` | `1.19e-7` |

Route S0 keeps scikit-learn when logistic regression and other simple baselines make it a justified
research dependency. Route S1 replaces production scaling with explicit NumPy stats, validates
nonempty equal widths, finite means, and positive scales, and removes scikit-learn only if no other
approved use remains. Validate S1 on actual corpus-covered rows and constant/near-constant columns
before deletion.

Do not introduce a scikit-learn `Pipeline`: temporal splitting, overlapping contexts, persisted
stats, and artifact inference already require explicit domain steps. A generic pipeline would add
an interface without hiding those facts.

## Features, task, and tensors: flatten only after ablation

The current feature module carries `SourceSpec`, `FeatureSpec`, a dependency graph, compiled
contract, registry, fingerprints, and three named catalogs. The temporal path has one compiler,
one execution policy, one fixed builder, one scaler, and one prediction family. These are mostly
in-process computations. One adapter at each seam is hypothetical variability.

The feature variants are scientifically real ablation recipes, but they do not automatically
require runtime plug-in architecture. After the final feature set is chosen, a direct Polars
builder can express shifts and trailing windows with readable native expressions. Polars describes
expressions as composable, human-readable transformations its engine can optimize
([Polars expressions](https://docs.pola.rs/user-guide/concepts/expressions-and-contexts/)).

Candidate deep module:

```python
build_temporal_features(blocks, feature_set) -> FeatureFrame
```

Its small interface states canonical input invariants, decision-time availability, ordered output
names, warmup, and required acquisition columns. Its implementation may use several private
formula helpers. It need not expose a source/feature dependency language if no external caller
defines formulas.

Keep the current catalog only if arbitrary output selection, acquisition planning, and multiple
approved feature implementations demonstrably need it after ablation. Reject a direct rewrite
that simply copies all 77 formulas into one unreadable function; feature reduction should precede
architectural flattening.

Fixed preparation currently rewrites every context to one length, but tensorization still pads,
builds masks, groups by context signature, and loops through each sample. PyTorch's standard
`DataLoader` already owns batching, shuffling, workers, collation, and pinning
([PyTorch DataLoader](https://docs.pytorch.org/docs/stable/data.html)). A fixed-context candidate
can use one focused dataset/collator, no padding mask, no context signatures, and the LSTM's final
hidden state directly. `sliding_window_view`, `Tensor.unfold`, or vectorized row indices are
implementation options; benchmark memory and contiguity before choosing.

Candidate deep modules and seams:

```text
canonical blocks
  -> build_temporal_features(...)
  -> build_examples(..., decision_contract, split_cutoffs)
  -> fit(...)
  -> evaluate_decisions(...)
```

Each interface exposes scientifically important units and invariants, while implementation
mechanics remain local. The deletion test should remove concepts rather than move them into a new
facade. Tests cross these interfaces with hand-computable behavior; old tests of registries,
sampler signatures, metric catalogs, and pass-through contracts should be replaced, not layered.

Keep direct dispatch for the three model families while all three remain experimental candidates.
Once the baseline ladder decides the final production family, model HPO configs can remain in a
research harness without making every production artifact caller generic over hypothetical model
plugins.

## Serving: scope beats another framework

The HTTP layer is 87 lines and already uses FastAPI/Pydantic for request parsing, validation,
response schemas, OpenAPI, and interactive documentation. Those are the exact capabilities the
framework is designed to provide
([FastAPI request models](https://fastapi.tiangolo.com/tutorial/body/)). Replacing it with a lower
level ASGI app would save a dependency only by recreating validation and documentation or losing
them.

Serving analytics already uses standard-library `sqlite3`, not SQLAlchemy. Python describes SQLite
as a lightweight disk database requiring no separate server
([Python sqlite3](https://docs.python.org/3/library/sqlite3.html)). For one mutable table with
insert, update, and aggregate queries, it is leaner than an ORM, JSONL replay, DuckDB, or a new
async wrapper.

Two local fixes are warranted if serving survives:

- a SQLite connection context commits/rolls back but does not close; use explicit closing and set
  timeout/connection policy on every operation;
- construct/close the RPC client through FastAPI lifespan rather than lazy global state.

These are lifecycle fixes, not reasons to change databases. Adding `aiosqlite`, SQLModel, or
SQLAlchemy would introduce another adapter and schema vocabulary without a demonstrated
concurrency requirement.

Two serving routes remain:

- **SV0: thesis inference function/CLI only.** Delete HTTP and analytics if live API/persistence is
  not part of the assessed outcome.
- **SV1: keep FastAPI plus raw SQLite.** Rebuild response/storage fields around the approved action
  contract and fix lifecycle ownership. This retains a demonstrable live system with little extra
  conceptual surface.

Do not choose a storage replacement before the model's meaning stabilizes. Current persisted
`observed_block`, `baseline_block`, `broadcast_after_block`, `target_block`, offset, and wait fields
encode the unresolved `+1` serving interpretation.

## Integrated candidate routes

### Route A: thesis-minimal control

- one approved current-forming or next-block contract;
- small protocol-grounded feature set;
- fixed block context and standard DataLoader;
- unweighted classification-only control;
- immediate, deterministic, logistic, shallow-MLP, and small-LSTM baselines;
- direct PyTorch if its checkpoint prototype stays short;
- fixed configs or a small explicit grid for baseline work;
- deterministic named-window or exact-kernel evaluation;
- NumPy production scaler and direct economic calculations;
- serving optional; FastAPI/SQLite only if required.

This has the lowest pedagogical burden. It loses framework-managed scaling and the current broad
research surface unless those paths are retained separately as experiments.

### Route B: idiomatic research framework

- the same approved domain contract and reduced task;
- automatic Lightning, stock lifecycle where exact semantics fit, TorchMetrics only for retained
  conventional metrics;
- standard DataLoader;
- Optuna retained for bounded calibration with real epoch reports;
- deterministic named-window or exact-kernel primary evaluation plus a named Poisson
  paper-reproduction view;
- FastAPI/SQLite serving.

This keeps mature experiment/checkpoint integration. It wins only if its prototype deletes the
custom fit policy and remains easier to explain than Route A as a whole.

### Route C: preserve broad experimentation, flatten hypothetical seams

- retain three model families, feature ablation recipes, multitask/weighted candidates, Optuna,
  and both evaluator estimands;
- remove one-option compiler, policy, prediction, representation, and scaler registries;
- keep owner-local direct dispatch only for real alternatives;
- separate research harness outputs from the final production/thesis path.

This minimizes migration risk and preserves research breadth, but it is not the leanest final
codebase. It is justified only if the remaining experiments are part of the thesis plan.

No route is approved. A mixed route is possible: for example direct PyTorch plus retained Optuna,
or Lightning plus no F1. The choices are orthogonal once interfaces are small.

## Prototype and measurement queue

The order prevents framework work from fossilizing unresolved theory.

1. **Prove per-chain block-open facts.** For corpus dates and current regimes, verify base-fee
   determinism, timestamp/cadence availability, inclusion timing, and priority-fee assumptions for
   Ethereum, Polygon PoS, and Avalanche C-Chain. Classify each current feature as available,
   computable, estimated, or post-close.
2. **Approve one action/outcome fixture.** Owner chooses current-forming or confirmed-head semantics,
   deadline/fallback, ties, and baseline. The fixture must pass offline and serving paths.
3. **Prototype deterministic evaluation.** Compare fixed-window exposure weights and, if current
   random starts must remain, the exact inclusion kernel with high-repetition simulation on hand
   data and several real windows. Record when event-mean and spend-ratio estimands differ.
4. **Run the simple objective/model ladder.** Use common purged splits, validation origins, and
   seeds. Measure economic utility, harmful delays, concepts, parameter count, train time, and
   source/test surface.
5. **Prototype direct PyTorch versus automatic Lightning.** Same selected tiny task, resume policy,
   nonfinite cases, exact reducer, and Optuna prune hook. Report net diff and choose one.
6. **Measure HPO value.** Compare declared fixed baseline, small seeded random/TPE calibration, and
   finalist multi-seed results. Narrow the space before deciding whether Optuna earns production
   architecture.
7. **Prototype fixed tensorization and direct feature construction.** Verify exact rows, same-weight
   outputs/decisions, memory, throughput, worker behavior, and source reduction. Delete the dual
   path after evidence.
8. **Run NumPy scaler parity on real train-covered rows.** Include constant/near-constant features,
   artifact round trip, and serving transform before removing scikit-learn.
9. **Choose serving scope.** If HTTP demo remains, retain FastAPI/raw SQLite and fix lifecycle. If
   not, expose one inference function/CLI and remove the rest cleanly.

## Owner gates

Approval is required for each of these decisions. None may be inferred from this report:

1. Current-forming-block versus confirmed-head/next-block decision, per supported chain.
2. Block offsets versus wall-clock waits, and whether the deadline constrains broadcast or
   inclusion.
3. Tie utility and unavailable/deadline-miss behavior.
4. Primary economic estimand: mean request percentage, ratio of total spend, or another utility;
   gas/priority-fee scope and metric names.
5. Classification-only, fee-vector, multitask, weighting, and the auxiliary head.
6. Minimum practical improvement required to retain a feature, model, or framework.
7. Direct PyTorch versus automatic Lightning, including best/min-delta, nonfinite, seed, and resume
   guarantees.
8. Fixed configuration, explicit grid, or retained Optuna policy; sampler, pruning, failed-trial
   budget, and resume reproducibility.
9. Macro F1 and each other diagnostic's explicit thesis question.
10. NumPy scaler versus retaining scikit-learn for approved simple baselines.
11. Which one-option registries are deleted after semantics and experiments stabilize.
12. CLI-only inference versus FastAPI/SQLite serving.

Architecture and implementation guides should be rewritten only after these gates. Documenting
all candidates as equally active would make the code harder to learn; the final guides should
teach the approved route, give one worked timeline and formula set, and record rejected routes in
decision notes.

## Primary references

- Local foundation paper: `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`
- [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)
- [PyTorch optimization loop](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)
- [PyTorch DataLoader](https://docs.pytorch.org/docs/stable/data.html)
- [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)
- [Lightning automatic/manual optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)
- [Lightning checkpoint contents](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)
- [TorchMetrics state/reduction](https://lightning.ai/docs/torchmetrics/stable/pages/overview.html)
- [Optuna TPE](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html)
- [Optuna pruning](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html)
- [Optuna RDB resume](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/001_rdb.html)
- [scikit-learn StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [scikit-learn F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)
- [Polars expressions](https://docs.pola.rs/user-guide/concepts/expressions-and-contexts/)
- [FastAPI request models](https://fastapi.tiangolo.com/tutorial/body/)
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)
- [MIT Poisson-process notes](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/)
