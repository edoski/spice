# Bounded HPO framework comparison

Research date: 2026-07-12. This resolves [Compare mature bounded-HPO frameworks for the final training host](https://github.com/edoski/spice/issues/61). It is evidence for, not a decision that closes, [Choose the bounded HPO, trial-budget, and study-lifecycle policy](https://github.com/edoski/spice/issues/29).

## Scope and frozen criteria

Assumption: the later owner chooses a small, predeclared conditional space and a single Lightning-or-direct-PyTorch host. That host is still open. This report does not assume the search space, host, budget, or pruning decision is closed.

Every route was screened against these fixed requirements:

- one finite complete-validation `total_loss` objective; no test scoring;
- deterministic trial/model seeds, bounded trial count, explicit complete/pruned/failed states, and honest restart or continuation semantics;
- one approved writer and durable local recovery; independent Slurm trial execution if selected;
- optional pruning only if it earns its complexity;
- fit with Lightning and direct PyTorch without a generic adapter;
- maintained, pinned Python 3.11/PyTorch-compatible packages; and
- least dependency weight, production code/config/runtime concepts, and undergraduate explanation burden.

This is deliberately not a performance contest. Search algorithms are distinct from orchestration/lifecycle frameworks: distributed actors, dashboards, cloud services, multiwriter coordination, and generic adapters earn no credit because SPICE does not need them.

## Recommendation

Choose **SPICE-owned direct seeded search** as the default policy route: enumerate the finite conditional space when it is small; otherwise draw a predeclared number of configurations from a seeded `random.Random` stream. Store the frozen candidate list, seed, configuration digest, and one terminal record per candidate in SPICE-owned study state. Run a candidate through the selected training host, report only its complete-validation total loss, and rank only terminal finite completed records using the policy ticket's deterministic tie rule.

Do not retain pruning by default. It requires intermediate, comparable validation reports and a semantic policy for what a pruned result means; a bounded thesis search can instead use full trials and an explicit small budget. If the later owner proves that pruning is material, use Optuna rather than inventing a pruner.

This route is the smallest one that meets the stated requirements. It has no new runtime dependency; its random stream is deterministic, conditional candidates are explicit data rather than hidden sampler behaviour, and Slurm can run independent frozen candidates without a coordinator. Recovery is honest: a restarted candidate is a new declared attempt unless the later policy specifies checkpoint continuation. One local writer records terminal outcomes after each candidate or collects independently produced immutable candidate results. No shared writer is required.

**Conditional escalation:** choose Optuna only if the owner approves a genuinely wider adaptive conditional space or pruning whose saved trial history materially reduces the fixed budget. Then pin the existing Optuna line, use one local writer and one storage route, and keep the Optuna lifecycle local to the tuning workflow. Optuna documents seeded samplers, persistent studies with `RDBStorage`, `Trial.report`/`should_prune`, and pruned/failed trial states ([samplers](https://optuna.readthedocs.io/en/stable/reference/samplers/index.html), [RDB persistence](https://optuna.readthedocs.io/en/stable/tutorial/20_recipes/001_rdb.html), [pruning](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html)). It is a good fallback, not the default.

## Requirements matrix

| Route | Bounded conditional space and seed | Trial states / recovery | Pruning | One-writer persistence | Slurm-independent trials | Net result |
| --- | --- | --- | --- | --- | --- | --- |
| Direct seeded search | Exact: SPICE serializes candidates and seed | SPICE owns terminal records and restart policy | Deliberately absent unless approved | Exact: existing root-local state | Exact: submit frozen candidates; collect once | **Best default** |
| Optuna 4.8.0 | Native conditional suggestions and seeded samplers | Native complete/pruned/fail history and persistent study | Native, via reports | Native, but storage must remain single-writer | Possible, but adaptive sampling couples dispatch | Best escalation |
| Lightning `Tuner` | No general conditional HPO | No study lifecycle | LR/batch-size utilities only | None | No | Reject |
| Ray Tune | Yes | Full experiment/checkpoint lifecycle | Native schedulers | Full runtime storage model | Yes, through Ray actors | Reject: orchestration excess |
| Ax/BoTorch | Yes | Client/experiment lifecycle | Possible | Experiment persistence | Possible | Reject: Bayesian experiment platform |
| SMAC | Yes | Runhistory/output lifecycle | Hyperband facade | Own output machinery | Worker model | Reject: heavier SMBO stack |
| Nevergrad | Yes | SPICE must persist ask/tell state | No training-aware pruning | SPICE must build it | Executor-based | Reject: no lifecycle advantage |
| Hyperopt | Yes | In-memory `Trials`; persistence/parallelism adds Mongo | No comparable native lifecycle here | Mongo for distributed trials | Mongo workers | Reject: extra service |
| scikit-optimize | Yes | Caller-owned | No training-aware lifecycle | Caller-owned | Caller-owned | Reject: no advantage over direct |

The pinned lock already contains Optuna 4.8.0 and Lightning 2.6.5; it contains no finalist alternatives. Optuna itself adds Alembic, Colorlog, SQLAlchemy, tqdm, and related lifecycle concepts. SQLAlchemy is already a SPICE dependency, but that does not make Optuna's study schema, sampler, pruner, and RDB lifecycle free. See [pyproject.toml](../../../pyproject.toml) and [uv.lock](../../../uv.lock).

## Candidate evidence and rejection reasons

**Direct seeded search.** Python's standard library provides the deterministic PRNG; SPICE needs only a frozen candidate materializer and its own records. This is not a weaker version of a platform: it is the fitting algorithm for a finite experiment. It avoids turning configuration selection into a `Study`, sampler, pruner, storage backend, and callback API.

**Optuna.** It is mature and current enough for the fallback. Its RDB recipe documents persistent/resumable studies, while its RDB API warns against SQLite for parallel optimization ([RDB storage](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.storages.RDBStorage.html)). The already accepted filesystem evidence also limits Journal to one local writer and leaves remote NFS conditional ([filesystem and Journal evidence](../target-filesystem-root-journal-constraints.md)). SPICE's current `RDBStorage` implementation is therefore not a reason to keep Optuna: it is historical WIP subject to clean-break deletion.

**Lightning-native facilities.** Lightning's `Tuner` performs learning-rate range testing and batch-size scaling, not general conditional HPO or a durable trial lifecycle ([Lightning Tuner](https://lightning.ai/docs/pytorch/stable/api/pytorch_lightning.tuner.tuning.Tuner.html)). It cannot replace either direct search or Optuna.

**Ray Tune.** Ray Tune provides remote actors, controller/checkpoints, trial retries, persistent experiment storage, and cluster recovery ([Tune lifecycle](https://docs.ray.io/en/latest/tune/tutorials/tune-lifecycle.html), [fault tolerance](https://docs.ray.io/en/latest/tune/tutorials/tune-fault-tolerance.html)). Those features are valuable for distributed tuning, but introduce a second scheduler/runtime beside Slurm and persistence/checkpoint concepts SPICE expressly excludes.

**Ax/BoTorch.** Ax requires Python 3.11 and its installation points to a substantial direct-dependency set; its documented Client owns trials, generation strategies, and persistence ([Ax installation](https://ax.dev/docs/installation/), [Client tutorial](https://ax.dev/docs/tutorials/getting_started/)). This Bayesian experiment platform does more than a small fixed search needs.

**SMAC.** SMAC's documented minimum needs a configuration space, target function, scenario, and facade ([SMAC getting started](https://automl.github.io/SMAC3/latest/3_getting_started/)). Its Hyperband and worker concepts solve larger adaptive optimization, not this fixed experiment.

**Nevergrad.** Nevergrad offers seeded ask/tell optimizers and executor-driven parallel evaluation, but leaves trial persistence and training lifecycle to SPICE ([optimization guide](https://facebookresearch.github.io/nevergrad/optimization.html)). It supplies an optimizer without deleting the required lifecycle code.

**Hyperopt.** Plain `Trials` is an in-process object. Its documented parallel/persistent route is `MongoTrials`, a MongoDB service plus workers ([Hyperopt scale-out](https://hyperopt.github.io/hyperopt/scaleout/mongodb/)). That is out of scope.

**scikit-optimize.** It supplies sequential model-based minimizers and an ask/tell API, but its documented focus includes scikit-learn estimator search and caller-managed callbacks ([scikit-optimize](https://scikit-optimize.readthedocs.io/en/latest/)). Its canonical repository is archived ([repository](https://github.com/scikit-optimize/scikit-optimize)), so it also fails the maintenance criterion. It deletes no SPICE lifecycle code.

## Local implications

If the policy selects direct search, delete rather than wrap the current Optuna-specific path: [study_optuna.py](../../../src/spice/storage/study_optuna.py), Optuna imports/types in [tuning_execution.py](../../../src/spice/modeling/tuning_execution.py) and [study_models.py](../../../src/spice/storage/study_models.py), the `optuna` dependency, and Optuna-only inspection/config paths. Replace them with one SPICE-owned bounded-candidate materializer and one typed terminal-result record. Keep only the domain facts that remain useful: immutable study definition, typed parameter payload, selected training-host call, and downstream preset application. Do not preserve an optimizer-neutral adapter.

If the policy selects Optuna, remove the current RDB-specific assumption rather than adding another backend. The filesystem ticket's one-local-writer Journal route and current `RDBStorage` are mutually exclusive clean-break choices; archive/discard old studies, do not migrate or provide compatibility readers.

## Handoff to the policy owner

The policy ticket should decide, in this order:

1. Whether the approved space is finite enough to enumerate or needs seeded random draws; declare it and the exact candidate materialization before trials run.
2. The exploration/finalist seeds, budget, complete/pruned/failed/retry accounting, and whether any pruning benefit pays for Optuna.
3. The one-writer record format, resume meaning, and Slurm submission/collection boundary after the training host is chosen.
4. The deterministic ranking and explicit preset promotion rule, using the selection ticket's canonical complete-validation total-loss semantics.

No framework choice here declares the final host, model/search space, budget, or selection/loss/evaluation policy closed.
