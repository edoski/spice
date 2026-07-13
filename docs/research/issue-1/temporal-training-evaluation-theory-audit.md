# Temporal training and evaluation theory audit

Date: 2026-07-10

Status: research evidence and candidate route only. Nothing here approves a target, loss, metric, trainer, tuning policy, dependency, migration, or deletion. The professor's paper, current code, existing ADRs, and this audit are all challengeable inputs. Every consequential choice ends in an owner gate.

Scope: the temporal module's target, loss, fitting loop, early stopping, checkpoints, tuning, predictive metrics, economic replay, and statistical reporting. Preprocessing is covered only where it changes training or evaluation validity; the detailed companion is `docs/research/issue-1/temporal-preprocessing-theory-audit.md`. Paper-wide alignment is in `docs/research/issue-1/temporal-paper-alignment-audit.md`.

Method: production code, configuration, tests, benchmark scripts, the checked-in results database, and all 11 pages of `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf` were inspected. Framework semantics were checked against primary documentation. Small locked-environment probes tested weighted-loss aggregation and F1 behavior. Historical database queries were read-only. No training run was launched, no production code was changed, and no existing result was treated as proof of the right design.

## Findings by status

The distinction between a defect and a design choice matters. A coherent unusual choice is not a bug merely because a library or paper does something else. Conversely, reproducing the paper does not make a choice theoretically sound.

| Status | Finding | Consequence |
| --- | --- | --- |
| **Confirmed cross-layer defect** | Offline class `k` is realized at row `h+k`, while serving targets inclusion at `h+k+1`. | Training, historical economic replay, and deployment do not currently evaluate one action. The intentional block-open/current-row rationale is supported for some features; offline/serving parity remains unresolved. |
| **Confirmed defect** | Class-weighted cross-entropy is accumulated as batch mean times sample count. | Reported epoch loss depends on batch partition, and batch size is tuned. Best epoch and trial ranking can change without changing predictions. |
| **Confirmed defect** | The configured seed is set after model construction. | It does not control initial weights. |
| **Confirmed defect** | Every tuning trial computes test metrics, although only validation loss is returned. | It wastes work and repeatedly opens the nominally sealed test set. There is no current objective leakage, but there is procedural exposure. |
| **Confirmed defect** | Optuna pruning is asked only after the complete training run and summary. | It saves no epoch work and can label an already completed computation as pruned. This is a defect in the extension's implementation, not an argument against HPO. |
| **Confirmed defect** | Internal chronological splits have no outcome-horizon purge. | Some training labels use outcomes in the nominal validation interval, and some validation labels use outcomes in the nominal test interval. |
| **Confirmed defect** | A resumed fit rebuilds the shuffled sampler at epoch zero and does not restore global RNG state. | Resume is not the stochastic continuation implied by a full training checkpoint. |
| **Confirmed metric mismatch** | SPICE macro F1 averages target-supported classes only; standard multiclass implementations use union-active classes by default. | The custom value can be more favorable when the model predicts a class absent from targets. |
| **Confirmed evaluation mismatch** | Offline replay reports the mean of per-event percentages; serving reports a ratio of aggregate savings to aggregate baseline fees. | They answer different questions. Historical Polygon conclusions change sign for some aggregations. |
| **Confirmed semantic flaw** | Deadline overflow can receive ordinary economic credit, including negative regret versus the reachable optimum. | A service-constraint violation can improve the reported score. |
| **Open design choice** | Offset zero may intentionally mean the current/next-forming block. | It can be coherent only under an explicit pre-inclusion decision instant and an availability proof for every feature. It must not be silently replaced with “next confirmed block.” |
| **Open design choice** | HPO is an intentional extension beyond the paper. | It has real scientific and operational value. Retain Optuna as a serious candidate; simplify its policy and lifecycle only if a prototype is leaner without losing that value. |
| **Open design choice** | Inverse-frequency class weighting and the auxiliary fee head reproduce paper ideas. | Both alter the learned objective; neither is justified by the paper's reported experiments. They need ablation, not automatic retention or deletion. |
| **Open design choice** | Macro F1, exact block accuracy, and exact optimum hit rate are diagnostics. | Correct implementation does not establish usefulness. Ordered, tied, economically asymmetric actions make them incomplete. |
| **Defensible current choice** | Train-only normalization, chronological intent, AdamW, gradient clipping, validation early stopping, and a unidirectional LSTM are ordinary choices. | Preserve unless a simpler route subsumes them. There is no evidence that a scheduler or a more complex optimizer is needed. |

## Correctness starts with the decision, not the network

A temporal model is correct only relative to a decision problem:

```text
information available at decision time
        -> allowed action
        -> operational realization
        -> outcome and service constraint
        -> utility / metric
```

The paper supplies a valuable research motivation but leaves the decision timestamp, submission timing, and inclusion timing under-specified. It says the scheduler observes recent fees, predicts a future minimum inside the next `M` seconds, and compares against immediate next-block inclusion (Secs. IV-A and VI-C). It does not say whether the action means desired submission time, desired block, or guaranteed inclusion block. Current SPICE made an intentional current-row extension; that extension must be judged on internal causal coherence rather than paper fidelity.

This rationale is documented history, not a reconstruction invented by this audit. Commit `e0b2e68e` (`fix(features): enforce safe current-row fee dynamics`) deliberately removed the unsafe `same_block_closed` route and retained a block-open/current-row route. `ARCHIVE.md:9-36`, `PROGRESS.md:241-255`, and `src/spice/features/ARCHITECTURE.md:30` state the intended information set: `base_fee[t]` is available because the EIP-1559 fee for block `t` is deterministic from parent state before execution, while finalized facts such as gas used and transaction count are lagged to `t-1`. This is a serious causal design, not an accidental off-by-one inferred merely from divergence with the paper.

Let `h` be the row called the anchor. Current executable behavior is:

```text
offline context ends                  h
offline class k target / realization h + k
offline baseline                     h
serving observed confirmed block     h
serving broadcast after class k      h + k
serving inclusion target             h + k + 1
serving baseline                     h + 1
```

The compiler sets `candidate_start_rows = anchor_candidates` at `src/spice/temporal/compilers/observed_time_window.py:352-364`. The execution policy assigns candidate rows and the baseline from that start at `src/spice/temporal/execution_policy/strict_deadline_miss.py:69-106,130-149`. Accounting charges those rows at `src/spice/evaluation/temporal_accounting.py:85-105`. Serving instead fetches a confirmed window and applies the explicit `+1` inclusion mapping at `src/spice/serving/inference.py:70-105`.

This proves a cross-layer mismatch. It does **not** prove that an offset-zero current-block design is inherently invalid. The documented block-open interpretation is:

- decision time is before candidate block `h` has selected transactions;
- class zero means submit for inclusion in that forming block;
- the base fee of `h` is already knowable from the parent under the chain's fee rule;
- every input feature is available or computable at that instant;
- replay models whether submission can still reach the proposer.

The current feature catalog partially satisfies it. `base_fee_per_gas[h]`, its deltas, and rolling fee features through `h` are causally available on Ethereum if they are recomputed from parent state rather than read after the fact. Gas used, gas limit, and transaction count are explicitly shifted to `h-1` at `src/spice/features/sets/core_fee_dynamics/_block_facts.py:27-47`, which correctly avoids the archived same-block-closed leakage.

The cadence/calendar subset still needs proof. `seconds_since_previous_block`, hour, and day-of-week for row `h` use the realized `timestamp[h]` at `src/spice/features/sets/core_fee_dynamics/_time.py:21-94`. A public oracle cannot ordinarily read an unmined block's final timestamp through the same confirmed-block RPC path. Wall-clock time could replace calendar values at decision time, but offline use of the realized timestamp would then need an equivalence/error argument; exact inter-block duration is not known before the block exists. The same issue applies to the optional elapsed-position feature. Ethereum's fee recurrence also does not by itself prove equivalent pre-execution availability for Polygon's and Avalanche's EIP-1559-inspired rules.

Live serving does not construct the documented block-open row. It builds features from confirmed blocks, selects the last confirmed row as the anchor, and creates a one-row candidate store at `src/spice/serving/inference.py:145-198`. It then maps offset `k` to broadcast after that confirmed block plus `k` and inclusion at `+1`. To deploy the retained current-row semantics, serving would instead need to synthesize or obtain the forming block's safe feature row from parent state and current decision time, then prove the transaction can still target it. Its current `+1` is rational for a post-confirmation request, which explains the implementation, but it is not equivalent to the trained block-open task.

The first owner gate is therefore not “change `+0` to `+1`.” It is:

> Choose the decision instant and define one worked example containing observed head, request time, available features, action `k`, broadcast time, first eligible inclusion block, deadline, fallback, baseline, and realized fee for each supported chain.

Two serious candidates should be prototyped:

1. **Pre-inclusion/current-forming-block contract.** Preserve the intentional offset-zero extension and its safe-feature rationale. Replace or justify realized timestamp features, prove each chain's fee availability, rebuild serving around the pre-inclusion instant, and demonstrate that a request can operationally act on it.
2. **Post-confirmation/next-block contract.** Keep serving's current information set. Make offline class zero and baseline refer to the first eligible future block.

No target, model, economic metric, or old result should be approved before the same fixture passes dataset target construction, offline realization, and serving mapping.

## Target and loss theory

### Offset classification is simple, but its errors are not exchangeable

The paper and code turn “choose the cheapest candidate” into multiclass classification. This gives a compact action and a familiar cross-entropy loss. It is not wrong by definition. Its limitations are material:

- classes are ordered in time, but cross-entropy treats every wrong class as categorically different rather than nearer or farther;
- equal-fee minima are collapsed by `argmin` to the earliest row even when multiple actions have the same economic outcome;
- class error cost changes per example: choosing a nearby block can be cheap or expensive depending on its fee;
- a class probability estimates the argmin label distribution, not the future fee trajectory or expected cost of each action.

Those limitations are acceptable only if a simple classification baseline performs economically well enough. They do not justify adding a sophisticated loss before a baseline comparison.

### Exact ties are common on Polygon

NumPy `argmin` selects the first exact minimum. A read-only diagnostic over up to one million current-corpus anchors found exact-minimum ties in approximately 39.03% of Polygon windows, near zero on Ethereum, and about 0.003% on Avalanche. Exact reconstruction and caveats are in the preprocessing companion audit.

Current `offset_accuracy` marks a later equally cheap action wrong. `exact_optimum_hit_rate` is stricter still: it compares row identity at `src/spice/evaluation/temporal_accounting.py:102-116`. These metrics can disagree with the economic outcome without any model error.

Candidate tie rule: define the optimal action set `A_i* = {a : fee(i,a) = min_a fee(i,a)}`. A tie-aware hit is `1[prediction in A_i*]`. If shorter waits are preferable, keep earliest-minimum as the training label but report that preference explicitly as a latency tie-break, not as fee correctness. The owner must choose whether equal fee but longer delay is equivalent, secondarily worse, or application-specific.

### The weighted cross-entropy reduction is mathematically wrong at epoch level

PyTorch's weighted `cross_entropy(..., reduction="mean")` divides a batch's summed weighted losses by the sum of target weights in that batch, not by batch size ([PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)). Current loss uses that default at `src/spice/prediction/families/min_block_fee_multitask/loss.py:24-28`. The accumulator then multiplies the scalar by the number of samples at `metrics.py:194-203` and divides the epoch total by sample count at lines 235-248.

For batch `b`, sample loss `ell_i`, target weight `w_i`, and batch size `n_b`, SPICE reports

```text
sum_b n_b * (sum_{i in b} w_i ell_i / sum_{i in b} w_i)
----------------------------------------------------------------
                         sum_b n_b
```

The intended whole-split weighted mean is

```text
sum_i w_i ell_i
----------------
    sum_i w_i
```

They are unequal whenever batches have different class composition. A local PyTorch probe over the same three examples produced whole-split weighted CE `0.10230064` but current two-batch accumulation `0.08765156`. A four-example cross-check produced reported values from `0.6539` to `0.7936` solely by repartitioning identical predictions. Because the tuning spaces include batch size, `total_loss` is not a common objective across trials.

This is a confirmed defect independent of whether class weighting remains. Lean fixes are:

- use `reduction="sum"`, separately accumulate the exact denominator, then divide once; or
- compute an unweighted sample mean if the owner selects unweighted CE.

The scorer should own numerator and denominator directly. “Batch mean times count” should not survive either route.

### Inverse-frequency weights change the estimand

Weights are computed from training offsets only at `metrics.py:214-232`. Full inverse-frequency weighting makes each present class contribute approximately equally regardless of deployment prevalence. It is not a neutral correction for imbalance. It teaches a class-balanced decision rule, shifts logits and argmax behavior toward rare offsets, and means softmax scores no longer estimate posterior probabilities under the deployment class prior without adjustment.

An absent training class receives weight zero. If it appears in validation, its classification contribution can be ignored; a batch containing only zero-weight targets can make the weighted mean undefined. The current sampled largest-class shares—about 31.00% Ethereum, 24.35% Polygon, and 8.02% Avalanche—do not by themselves establish severe collapse requiring inverse weighting.

Candidate experiment, in order of simplicity:

1. unweighted CE;
2. current weighted CE with the reduction fixed;
3. only if a named operational failure remains, a cost-sensitive objective tied to actual regret.

Compare on identical validation origins and seeds. Approve weighting only if it improves predeclared economic and harmful-delay measures, not merely macro F1.

### The auxiliary fee head has no demonstrated decision role

The second head predicts the standardized log of the minimum candidate fee. The loss is

```text
weighted_cross_entropy + 0.5 * smooth_l1(standardized_min_log_fee)
```

at `src/spice/prediction/families/min_block_fee_multitask/loss.py:29-40`. The paper specifies `alpha L_block + beta L_fee` but does not give the weights or an ablation. Current code hard-codes `0.5`. Decoding ignores the fee head at `src/spice/prediction/families/min_block_fee_multitask/__init__.py:71-84`; serving uses only offsets. Thus the head can only help indirectly as multitask regularization. Its total-loss scale is also horizon- and dataset-dependent, making “total loss” scientifically hard to interpret.

Multi-task learning can help when tasks share useful representation, but task weights are a real optimization problem rather than a harmless constant; Kendall et al. is one well-known learned-weight approach, not a reason to add that machinery here ([CVPR 2018 paper](https://openaccess.thecvf.com/content_cvpr_2018/html/Kendall_Multi-Task_Learning_Using_CVPR_2018_paper.html)). For this undergraduate codebase, the lean test is stronger:

- train classification-only and current multitask models on the same splits/seeds;
- select with a correctly reduced validation criterion;
- compare economic outcomes and variability;
- delete the scalar head, normalization state, loss component, metrics, and persisted fields if it has no stable material benefit.

This is an ablation gate, not a presumptive deletion.

### Three objective families deserve a bounded comparison

| Candidate | What it learns | Strength | Cost / conceptual burden |
| --- | --- | --- | --- |
| Unweighted offset classification | Probability of the selected argmin label | Fewest changes; easiest to teach | Ignores ordered/economic size of errors and needs a tie rule |
| Future fee-vector regression, then `argmin` | Fee for each allowed action | Action and cost are directly inspectable; ties natural | More outputs; requires a clear robust regression scale and action mask |
| Expected economic cost/regret | Utility of each action | Aligns training with use | Most assumption-heavy; denominator, gas, latency, and deadline penalties become training design |

Start with classification-only as the control, not the predetermined winner. A fee-vector prototype is justified because it may remove the classification label, class weights, scalar auxiliary head, and several metrics at once. Direct economic training should be attempted only if simpler objectives leave a material operational gap; otherwise it adds theory and policy to the gradient path.

Proper losses such as unweighted log loss support honest class-probability estimation ([Gneiting and Raftery, 2007](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)). Calibration metrics, Brier score, or temperature scaling should be added only if probabilities drive expected-cost choice, abstention, or uncertainty. An argmax-only thesis does not benefit from calibration machinery by default.

## Predictive metrics

### The macro-F1 correction does not make macro F1 the right metric

The earlier cross-verification correctly cleared one false alarm: TorchMetrics 1.9's stock multiclass macro F1 excludes classes with neither target nor prediction support, matching union-active averaging ([tagged 1.9 source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93)). Scikit-learn's standard default has the same union-active effect when labels are inferred ([scikit-learn `f1_score`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html); [TorchMetrics F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)).

Current SPICE is different. `macro_f1_from_counts` skips every class with `target_count == 0` even when the model predicted that class (`metrics.py:76-94`). With targets `[0, 0]` and predictions `[0, 1]`, current SPICE returns `2/3`; standard union-active macro F1 returns `1/3` because false-positive-only class 1 receives zero F1.

That establishes a semantic mismatch, not metric relevance. The paper never reports F1. F1 discards true negatives, treats offsets as unordered, does not account for tied fees, and does not measure savings, regret, or delay. The lean candidates are:

1. delete macro F1 if it answers no thesis question; or
2. retain it as a clearly secondary diagnostic using an existing implementation and explicit labels/zero-division semantics.

Do not maintain a custom metric solely because it is already present. Do not add a direct TorchMetrics dependency solely to save a small function if the metric itself is deleted. Scikit-learn is already a direct dependency and is adequate for offline diagnostics.

### Minimal predictive set

For a classification-only model, a lean set is:

- correctly aggregated validation loss for selection;
- tie-aware offset hit rate as an intuitive diagnostic;
- ordinary exact accuracy only when comparison with the paper is required;
- confusion counts only as an on-demand analysis artifact.

If the fee head remains, report its error in original, understandable units as well as log units, and explain why that error matters to a decision. Otherwise remove `regression_loss`, `log_fee_mae`, and `log_fee_mse`. Training minibatch loss is measured while weights change and dropout is active; label it “online training loss” or omit it from final scientific comparison rather than treating it as the fitted model's train score.

## Fitting, early stopping, and reproducibility

### Seed timing is a confirmed bug

`run_training` constructs the model at `src/spice/modeling/pipeline.py:251-255`. The configured seed is first applied inside `build_training_modeling_runtime_plan` at `runtime_planning.py:73-82`, after construction. It therefore controls later PyTorch draws but not initial weights.

The minimum correction is to seed immediately before model construction. A stronger design passes one seed record into model initialization, loader generation, and trial metadata. PyTorch explicitly warns that complete reproducibility is not guaranteed across releases, platforms, or devices and documents the relevant RNG and deterministic-algorithm controls ([PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)). The thesis should promise reproducibility within a declared environment, not universal bitwise identity.

Recommended seed protocol:

- one predeclared seed for cheap HPO exploration is acceptable;
- rerun finalists on at least three predeclared seeds; five is preferable if affordable;
- pair competing models on the same seeds and validation/test windows;
- report all points plus mean/SD or median/IQR rather than only the best run;
- store seed, package lock, device, determinism policy, corpus identity, and split cutoffs with every result.

### The current Lightning layer owns too little and too much

`SpiceLightningModule` sets `automatic_optimization = False` and manually performs zero-grad, forward, backward, clipping, and step for one AdamW optimizer at `src/spice/modeling/lightning_module.py:57-104`. SPICE also owns fit policy, best-state cloning, checkpoint payloads, sampler epochs, precision context, and callbacks. Lightning's automatic optimization is designed for ordinary one-optimizer training and can own backward/step/clipping ([Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)).

There are two credible clean-break hosts:

| Host | Keep it if | Delete / avoid |
| --- | --- | --- |
| Idiomatic Lightning automatic optimization | callbacks, device/precision handling, checkpointing, and Optuna integration remove more SPICE code than they add concepts | manual optimization, duplicate fit policy, custom checkpoint state, duplicate precision and clipping logic |
| Small pure-PyTorch loop | the complete fit can be taught in a short module and checkpoint/resume requirements remain modest | Lightning wrapper, Trainer lifecycle translation, framework-specific callbacks |

Do not build a trainer abstraction over both without two enduring implementations. Prototype the same tiny classifier with early stopping, interruption, resume, and tuning callback under both routes; count total production/test/config concepts and inspect the failure paths. Then approve one host and delete the other. The deep module should expose a narrow in-process operation such as:

```python
fit(model, train_data, validation_data, config, checkpoint=None) -> FitResult
```

Its interface should hide optimizer steps and framework callbacks. It should not hide the scientifically important selection metric, seed policy, or resume guarantee.

### Early stopping currently conflates “best” and `min_delta`

`TrainingFitPolicy` promotes a checkpoint only when `current < best - min_delta` at `src/spice/modeling/_fit_policy.py:101-113,199-210`. A later raw minimum smaller than the stored best by less than `min_delta` is not saved. Therefore `best_validation_loss` can mean “last material improvement,” not “lowest observed validation loss.” Both semantics are possible, but the name is currently too strong.

The lean candidate is to track raw minimum for best-state selection and apply `min_delta` only to patience, or set `min_delta = 0`. If owner preference is “material-improvement checkpoint,” rename it and preserve the rule explicitly. Validation remains the right stopping split; test must not participate.

### Current resume is not stochastic continuation

`TrainingCheckpoint` stores completed epoch, model, optimizer, and fit-policy state only (`src/spice/modeling/training_runner_types.py:13-18`). `_PositionBatchSampler` starts `_epoch = 0` on construction and derives each permutation from `[seed, epoch]` (`batch_plan.py:71-124`). Rebuilding it for resume repeats initial epoch permutations. Python, NumPy, CPU, and CUDA RNG states are not stored, so dropout also follows a reset trajectory.

This can be honestly supported in one of three ways:

1. **Exact-environment continuation:** store/restore RNG and loader/sampler position plus model, optimizer, scaler, epoch, and early-stop state.
2. **Epoch-boundary state restart:** resume optimizer/model but explicitly promise a new stochastic trajectory.
3. **No mid-fit resume:** keep training runs small/restartable and delete the checkpoint machinery.

Lightning checkpoints can include loop, optimizer, scheduler, precision, callback, datamodule, and hyperparameter state ([Lightning checkpoint contents](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)), but a rebuilt DataLoader's custom generator still needs a defined policy. Framework adoption does not remove the semantic choice.

### Ordinary choices that should not attract machinery

AdamW is a standard optimizer and gradient clipping is reasonable for recurrent models. Validation early stopping is reasonable once its objective is correct. Absence of a learning-rate scheduler is not a defect. No scheduler, optimizer family, mixed-precision mode, or deterministic-kernel flag should be added without measured benefit or a reproducibility requirement. The simplest understandable configuration that trains stably should win.

## HPO is a valid extension; its current boundary needs repair

The paper reports fixed training settings and mentions preliminary experiments. Current Optuna HPO is an intentional extension. Its rationale is visible in `PROGRESS.md:213-227`: use one bounded broad calibration search, avoid tuning every structural-ablation cell, and materialize explicit presets before reusing selected parameters outside the exact study identity. That is a sensible GPU-hour and comparability policy, not gratuitous machinery.

HPO can improve scientific practice by declaring the search space, recording every trial, reducing undocumented hand tuning, resuming expensive searches, and exposing parameter interactions. Those benefits are material for a thesis. HPO is therefore a serious retain candidate, not an accidental deviation or automatic deletion target.

Three current implementation problems remain:

1. `run_trial_training` calls `_build_summary`, which scores both validation and test at `src/spice/modeling/persisted_training.py:93-124,192-214`. `_trial_objective` returns only `best_validation_total_loss` (`tuning_execution.py:201-228`). There is no direct test-to-objective leakage today, but test is repeatedly computed and becomes available to observers/logs. Trials should return validation evidence only.
2. `trial.report` and `should_prune` run after full training and summary construction (`tuning_execution.py:220-227`). Proper pruning reports the validation objective at each epoch and stops then; Optuna's MedianPruner documentation describes this intermediate-value contract ([MedianPruner](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.pruners.MedianPruner.html)). Either wire an epoch callback or use `NopPruner`; the current switch is misleading.
3. Tuning `lookback_seconds` changes which anchors survive fixed-context filtering and can move role boundaries. Trials can therefore compare validation loss on different examples. Candidate configurations should share predeclared validation origins, with ineligible origins rejected or evaluated under an explicit common subset.

TPE is reasonable for mixed search spaces, and Optuna's storage/lifecycle can earn its dependency. For a small categorical thesis space, seeded random search is easier to explain and remains a strong baseline; random search is efficient when only some dimensions matter ([Bergstra and Bengio, JMLR 2012](https://jmlr.org/papers/v13/bergstra12a.html)). The choice should not be “Optuna or random”: Optuna can run a seeded `RandomSampler`, TPE, or enqueued finite design while preserving the journal and trial record.

Owner gate:

> Retain HPO as an explicit research phase, then choose the simplest Optuna sampling/pruning policy that produces a fair common-case validation comparison. The final test is evaluated once after the configuration, seed protocol, metric formulas, and checkpoint-selection rule are frozen.

An undergraduate-friendly workflow is:

```text
small declared search space
  -> fixed validation origins and one exploration seed
  -> Optuna records all trials
  -> select a few finalists
  -> rerun finalists across predeclared seeds
  -> freeze one configuration
  -> open final test once
```

Do not report the best TPE trial as an unbiased estimate of generalization. It is a selected validation result.

## Economic evaluation

### Current formulas answer two different aggregation questions

For event `i`, let `B_i` be baseline fee, `R_i` realized model fee, and `O_i` hindsight optimum. Offline accounting computes:

```text
profit_over_baseline_i       = (B_i - R_i) / B_i
cost_over_optimum_i          = (R_i - O_i) / O_i
baseline_cost_over_optimum_i = (B_i - O_i) / O_i
```

and reports event means (`src/spice/evaluation/temporal_accounting.py:91-123`). Serving first multiplies base fee per gas by the receipt's gas used at `src/spice/serving/inference.py:121-126`, then sums observed baseline and model transaction costs and reports

```text
sum_i (B_i - R_i) / sum_i B_i
```

at `src/spice/serving/analytics.py:120-153`.

The mean of percentages gives every request equal influence. The ratio of sums gives expensive requests more influence and answers “what fraction of total baseline spend was saved?” Both are legitimate. They are not interchangeable. If `B_i` is base fee per gas, the operational total-cost formula should weight by gas used `g_i`; if serving values already contain full observed fee amounts, that weighting is implicit.

Historical `benchmarks/results.sqlite` makes the choice concrete. It contains 1,296 result observations: two collections of 648, three artifacts, and 432 observations per chain. Reconstructing a ratio of stored fee sums per observation gives:

| Chain | Mean current event percentage | Mean ratio of fee sums | Event-mean negatives | Sign disagreements |
| --- | ---: | ---: | ---: | ---: |
| Avalanche | 0.384616% | 0.535235% | 139 / 432 | 28 |
| Ethereum | 1.181614% | 1.314268% | 2 / 432 | 2 |
| Polygon | -0.060895% | +0.046088% | 276 / 432 | 50 |

Across all chains, 80 of 1,296 observations change sign between the two aggregations. These historical values use the current unresolved action clock and selected replay windows, so they are not efficacy evidence. They do prove that the estimand choice is material and cannot be hidden behind a generic label such as “profit.”

Candidate metric vocabulary:

- `total_base_fee_savings_ratio = sum g_i(B_i-R_i) / sum g_i B_i` as the operational primary when gas/transaction costs are available;
- `mean_request_savings_ratio = mean((B_i-R_i)/B_i)` as a distribution-fair secondary and paper-comparison measure;
- never call either “profit” unless revenue, priority fee, gas use, latency utility, and other costs are included.

### One denominator makes the oracle relationship teachable

Current model regret and oracle opportunity use `O_i` as denominator while savings uses `B_i`. A cleaner secondary decomposition uses the same baseline denominator:

```text
model_savings_i  = (B_i - R_i) / B_i
oracle_savings_i = (B_i - O_i) / B_i
model_regret_i   = (R_i - O_i) / B_i

model_savings_i + model_regret_i = oracle_savings_i
```

The identity gives an immediate interpretation: how much available opportunity the model captured versus left behind. Keep optimum-normalized excess only if comparison with the paper requires it; label it separately rather than mixing denominator meanings.

### Deadline failure must not look like success

For unavailable requested offsets, `strict_deadline_miss` realizes the first post-window row (`src/spice/temporal/execution_policy/strict_deadline_miss.py:119-149`). Accounting charges that row normally and only adds `overflow_count` metadata (`temporal_accounting.py:91-130`). A checked-in test accepts negative `cost_over_optimum` when the post-deadline fee is cheaper than every reachable fee (`tests/evaluation/test_temporal_accounting.py:94-118`).

This is a confirmed semantic flaw under any strict deadline. The owner must choose one simple policy:

- unavailable actions are masked and cannot be selected;
- a deadline miss triggers a named fallback and is scored as a miss; or
- a miss receives an explicit application penalty.

Minimum reporting should include deadline-miss or harmful-delay rate. Ordinary savings must never silently reward an outcome outside the advertised service window.

### “Exact optimum hit” should be demoted or replaced

Row equality is not economic equality under ties. It also hides near-optimal choices and makes longer horizons mechanically harder. A lean economic set does not need both offset accuracy and exact row hit as headline measures.

Candidate final set:

- total base-fee savings ratio;
- baseline-normalized oracle regret;
- harmful-delay/deadline-miss rate;
- mean waiting time or delayed-request rate;
- mean-request savings for paper comparison;
- tie-aware optimal-action hit only as an intuitive diagnostic.

Raw fee sums over repeated synthetic replay runs are arbitrary workload totals and should not be presented as deployment savings. Keep them internally only when they are the numerator/denominator of an approved ratio.

### Retain exact economic values when possible

The problem store retains float32 log base fees and accounting reconstructs fees with `exp` (`temporal_accounting.py:91-99`; source conversion in `src/spice/features/core.py:321-324`). This is suitable for model input but unnecessarily loses exactness for economic accounting. A candidate store can keep raw integer base fee per gas for outcomes while exposing transformed floats only to the model. This may be both more accurate and easier to explain.

## Poisson replay can probably become deterministic

Current replay samples homogeneous Poisson arrivals, maps each arrival to the most recent sample timestamp with `searchsorted(..., side="right") - 1`, then discards the arrival timestamp (`src/spice/evaluation/poisson_replay.py:28-61,79-105`). Accounting sees only repeated sample positions. It is therefore a random weighting of block-bound decisions, not a full request-time simulator. This also contributes to the action-clock mismatch: the first inclusion opportunity after each actual arrival is never carried forward.

For a fixed approved interval under the current independent per-request policy, the normalized estimand can be computed exactly. Let decision/sample `i` represent an arrival-valid interval of duration `e_i`, and let `m_i` be its deterministic per-request metric. Under a homogeneous Poisson process with rate `lambda`, the expected arrival count is `lambda e_i`. Conditional on at least one arrival, the expected sample mean is therefore

```text
expected mean request metric = sum_i e_i m_i / sum_i e_i
```

The ratio of expected aggregate savings to expected aggregate baseline spend is

```text
sum_i e_i g_i (B_i - R_i)
--------------------------------
       sum_i e_i g_i B_i
```

The constant `lambda` cancels. This ratio of expected sums is also the long-run spend ratio. It is not generally equal to the expectation of a finite random ratio `E[sum savings / sum baseline]`; use the deterministic formula only when the approved estimand is ratio of expected/long-run spend. With one equally long decision interval per block, weighting reduces to equal blocks; with irregular block time, exposure duration supplies the correct weight.

The current evaluator also samples the interval start uniformly. Plain whole-corpus exposure weighting does not reproduce that distribution because states near the corpus edges occur in fewer possible windows. An exact deterministic refactor of the current evaluator must integrate the uniform-start window-inclusion kernel. Choosing several named fixed intervals and applying the simpler weights above is likely easier to teach, but it is a deliberate protocol change rather than an equivalent implementation. Neither deterministic route needs a Monte Carlo rate, repetition count, or random seed for these normalized estimands.

This simplification is valid only while requests are independent and do not affect queues, capacity, fee dynamics, batching, or the model's state. Keep stochastic simulation if the thesis asks about finite workload totals, coupled arrivals, concurrency, latency distributions within a block, or application behavior that depends on arrival count. In that case preserve actual arrival timestamps through realization. For expected total request count or cost, `lambda` matters as a scale even though it cancels from normalized ratios.

Candidate prototype:

1. choose between reproducing the current uniform-start distribution and adopting several predeclared named intervals;
2. derive the exact window-inclusion and decision-exposure weights from the approved decision clock;
3. evaluate every state once;
4. compute exposure-weighted metrics directly;
5. compare against a high-repetition Monte Carlo only as a validation test of the derivation;
6. if equivalent within Monte Carlo error, delete production replay randomness and repetition summaries.

This is a high-value lean candidate: it can remove arrival RNG, rate configuration for normalized metrics, repetitions, sampled-window integration noise, and misleadingly broad interpretations of Monte Carlo intervals.

## Statistical reporting

`temporal_replay_window_metrics` stores the mean and population standard deviation across replay runs at `src/spice/evaluation/_temporal_replay_metric_catalog.py:223-238`. Benchmark scripts turn this into `1.96 * std / sqrt(repetitions)`, for example `benchmarks/scripts/render_lstm_block_count_quartile_results.py:185-215`. Those bars quantify, at best, Monte Carlo variability conditional on one fitted model, one fixed trace, and the window-selection mechanism. They do not measure uncertainty across training seeds, days, fee regimes, chains, or corpus draws.

Conditional on the fixed trace, independently sampled window starts and Poisson arrivals are independent simulator draws even when their historical spans overlap. A Monte Carlo standard error can therefore quantify integration error for that conditional expectation. The fixed trace is still not new data, so it remains invalid to present that narrow error as uncertainty across future days, regimes, chains, or fitted models.

The paper uses one deliberately selected date, 9 November 2025, because the cheapest chain changed that day, and repeats only random two-hour window/arrival sampling. That is a useful case study, not an unbiased estimate of typical performance. Its claims should be worded accordingly.

Lean reporting protocol:

- predeclare multiple dates or non-overlapping day/regime windows before inspecting model outcomes;
- run all competing methods on the same windows and seeds;
- use at least three seeds for finalists, preferably five if affordable;
- show raw paired points, then mean/SD or median/IQR;
- distinguish conditional replay error from between-seed and between-day variability;
- use a day/block-aware bootstrap only if an inferential interval is genuinely needed; do not add it merely for visual polish.

Block bootstrap is the appropriate family when dependence must be respected ([Künsch, 1989](https://doi.org/10.1214/aos/1176347265)). Forecast-evaluation guidance likewise stresses time-respecting validation and the match between evaluation design and deployment information ([Hewamalage et al., 2023](https://doi.org/10.1007/s10618-022-00894-5)). For a bachelor's thesis, transparent paired descriptive results across named dates and seeds may be easier to defend than elaborate but fragile confidence intervals.

## Simple baselines are missing

The paper compares only LSTM, Transformer, and Transformer-LSTM. That cannot show that deep learning, large hidden sizes, the auxiliary head, or attention earns its complexity. Current large spaces reach hidden size 768 and Transformer dimension 1024 without a small baseline ladder.

Run baselines in increasing complexity on the same decision contract, split, validation origins, and economic scorer:

1. immediate/no-delay policy;
2. majority training offset via scikit-learn `DummyClassifier` ([documentation](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html));
3. deterministic protocol-informed forecast, such as next Ethereum base fee plus a documented persistence rule for later actions; chain-specific rules are required for Polygon and Avalanche;
4. multinomial logistic regression over the latest feature row or a very small declared summary, using the already installed scikit-learn API ([LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html));
5. shallow MLP on the same compact input;
6. one-layer LSTM with hidden size 64 or 128 and a direct linear output head;
7. current LSTM;
8. Transformer/hybrid only if the simpler ladder leaves a stable material economic gap.

The point is not to make every baseline production-pluggable. A small research harness can answer whether sequence modeling and added capacity help. Promote only the winning understandable family into the main architecture.

A particularly lean LSTM candidate is one unidirectional layer, no input projection unless feature dimension demands it, final hidden state to one linear logits layer, classification-only objective, and ordinary DataLoader batches. Add dropout, stacked layers, MLP heads, or the auxiliary output only when an ablation earns them.

## Proposed deep-module boundary

Training and evaluation are pure computational domains; they do not need broad adapter hierarchies. A deep module can hide mechanics behind two narrow operations:

```python
fit(model, train_data, validation_data, config, checkpoint=None) -> FitResult
evaluate_decisions(actions, outcomes, exposure_weights) -> DecisionMetrics
```

`fit` owns the chosen host, optimizer, gradient handling, selection rule, and checkpoint details. `evaluate_decisions` owns the approved formulas and tie/deadline policy. Dataset construction supplies causally valid action/outcome facts. Serving consumes the same action semantics, not a reinterpreted offset.

Do not create framework-neutral trainer, metric, or evaluator plug-in seams without real substitutable implementations. The local filesystem checkpoint is a legitimate internal seam because interruption exists. Lightning and Optuna integrations are framework boundaries only if those frameworks are approved; wrap them once rather than mirroring their abstractions in SPICE dataclasses.

Tests should move through the deep interface:

- one worked decision fixture must agree across labels, replay, and serving;
- loss aggregation must be invariant to validation batch partition;
- seed must reproduce initial state in the declared environment;
- resume must satisfy its approved exact or restart contract;
- tuning must not score test and pruning must stop before max epochs;
- fixed-window exposure weights or the random-window inclusion kernel must match high-sample simulation for the same declared estimand;
- tied minima and deadline misses must follow explicit policy;
- economic identities and aggregate formulas need tiny hand-computable examples.

When the new interface replaces the old route, delete transition tests and unit tests that only preserve custom sampler, metric-catalog, policy-state, or callback shapes. Keep behavioral proof, not architectural fossils.

## Candidate minimal thesis protocol

This is a coherent low-machinery route, not an approved answer.

1. Freeze one decision clock and action unit with an offline/serving parity fixture.
2. Purge split boundaries so every role owns its outcome interval; keep train-only scaling.
3. Establish immediate, majority, deterministic, logistic, shallow-MLP, and small-LSTM baselines.
4. Use unweighted classification-only CE as the control; fix exact loss reduction.
5. Ablate class weighting and the auxiliary head. Prototype fee-vector regression only if it can delete more concepts than it adds.
6. Choose Lightning automatic optimization or a short PyTorch loop after a bounded prototype; retain one.
7. Retain Optuna as a serious extension with a small declared search, validation-only trials, common origins, and real epoch pruning or no pruning.
8. Select finalists on validation, repeat finalists across predeclared seeds, then freeze the configuration.
9. Evaluate the test once across predeclared named dates/regimes with deterministic exposure weighting if its assumptions hold.
10. Report total savings ratio, baseline-normalized regret, harmful-delay/deadline-miss rate, wait, and a small diagnostic set. Show paired raw results.

This route prefers deletion only after evidence: the fee head, macro F1, Monte Carlo replay, custom manual Lightning optimization, or complex models leave only when a simpler candidate preserves useful information and performs adequately.

## Ticket-ready owner gates

These extend the original clean-break map. Its prior exclusion of a new prediction target or economic objective is no longer appropriate because the owner explicitly broadened the investigation. None should be implemented or marked superseding without owner approval.

| Ticket | Type | Decision / proof | Blocks |
| --- | --- | --- | --- |
| **Choose the temporal decision clock** | `grilling` / HITL | Approve pre-inclusion current-forming-block or post-confirmation next-block semantics per chain. Define feature availability, broadcast, inclusion, deadline, fallback, and baseline. | Every target, evaluation, serving, and historical-result decision |
| **Prototype action/outcome parity** | `prototype` / HITL | One fixture passes compiler target, evaluator realization, and serving response with identical action meaning. | Objective/model experiments |
| **Prove purged split ownership** | `prototype` / HITL | Zero training outcomes cross validation start; zero validation outcomes cross test start; contexts may look backward. Record sample impact. | Trustworthy selection and test |
| **Choose tie and deadline policy** | `grilling` / HITL | Approve equal-fee action semantics, latency tie-break, unavailable-action behavior, and harmful-delay definition. | Labels and metrics |
| **Fix and prove loss reduction** | `implement` after approval | Exact numerator/denominator; invariant to validation batch partition; selection value named. | Early stopping and HPO |
| **Compare lean objectives** | `prototype` / HITL | Paired unweighted classification, corrected weighted classification, current multitask, and fee-vector candidate if warranted. Report complexity and economic results. | Prediction-family choice |
| **Build the simple baseline ladder** | `research` + `prototype` / HITL | Immediate, majority, deterministic, linear, shallow MLP, small LSTM, current LSTM on common cases/seeds. | Model-family/capacity choice |
| **Choose the training host** | `prototype` + `grilling` / HITL | Automatic Lightning versus pure PyTorch, including interruption/resume and Optuna hook. Compare concepts, LOC, tests, and failure semantics. | Training clean break |
| **Choose seed and resume guarantees** | `grilling` / HITL | Seed timing, deterministic environment, finalist seed count, exact continuation versus stochastic restart. | Trainer/checkpoint contract |
| **Repair the intentional HPO extension** | `prototype` / HITL | Optuna validation-only trial; common validation origins; real epoch pruning or `NopPruner`; declared sampler/budget; coherent resume. | Study migration and final selection |
| **Choose economic estimands and names** | `grilling` / HITL | Approve total-cost ratio versus mean-request percentage, gas weighting, baseline denominator, latency/deadline measures, and paper-comparison metrics. | Evaluator and serving analytics |
| **Prototype deterministic evaluation** | `prototype` / HITL | Derive fixed-window exposure weights and, if preserving random starts, their inclusion kernel; compare like-for-like with high-repetition Poisson simulation and state when rate still matters. | Evaluator simplification |
| **Freeze uncertainty and test-seal protocol** | `grilling` / HITL | Predeclared dates/regimes, paired windows, seed count, descriptive summaries/optional block bootstrap, single final test opening. | Thesis claims and benchmark renderers |
| **Reassess historical results** | `research` / HITL | Mark which results are archival, recomputable, or invalid after decision/metric changes. Never silently relabel old observations. | Migration/publication claims |
| **Modernize ML architecture/implementation docs** | `implement` after decisions | Teach the approved decision clock, loss math, fitting lifecycle, HPO, evaluation formulas, uncertainty limits, and worked examples; remove rejected routes rather than documenting both as active. | Final clean-break docs |

The dependency order is deliberate: semantics before loss; correct loss before tuning; validated selection before final test; approved metrics before benchmark presentation. Owner review occurs at every `grilling` gate.

## Sources

Local primary evidence:

- professor paper: `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`, especially Secs. IV-A, VI-A, and VI-C;
- action compiler and policy: `src/spice/temporal/compilers/observed_time_window.py`, `src/spice/temporal/execution_policy/strict_deadline_miss.py`;
- target/loss/metrics: `src/spice/prediction/families/min_block_fee_multitask/`;
- fit/tuning: `src/spice/modeling/pipeline.py`, `runtime_planning.py`, `lightning_module.py`, `_fit_policy.py`, `batch_plan.py`, `persisted_training.py`, `tuning_execution.py`;
- evaluation/serving: `src/spice/evaluation/temporal_accounting.py`, `poisson_replay.py`, `_temporal_replay_metric_catalog.py`, `src/spice/serving/inference.py`, `analytics.py`;
- historical diagnostic: `benchmarks/results.sqlite`.

External primary sources:

- [EIP-1559 specification](https://eips.ethereum.org/EIPS/eip-1559)
- [PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)
- [PyTorch SmoothL1Loss](https://docs.pytorch.org/docs/stable/generated/torch.nn.SmoothL1Loss.html)
- [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html)
- [Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)
- [Lightning checkpoint contents](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)
- [Lightning ModelCheckpoint](https://lightning.ai/docs/pytorch/stable/api/lightning.pytorch.callbacks.ModelCheckpoint.html)
- [Optuna MedianPruner](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.pruners.MedianPruner.html)
- [scikit-learn F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html)
- [TorchMetrics multiclass F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)
- [scikit-learn TimeSeriesSplit `gap`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [Gneiting and Raftery, strictly proper scoring rules](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf)
- [Bergstra and Bengio, random search](https://jmlr.org/papers/v13/bergstra12a.html)
- [Kendall et al., multitask loss weighting](https://openaccess.thecvf.com/content_cvpr_2018/html/Kendall_Multi-Task_Learning_Using_CVPR_2018_paper.html)
- [Hewamalage et al., forecast evaluation pitfalls](https://doi.org/10.1007/s10618-022-00894-5)
- [Künsch, block bootstrap](https://doi.org/10.1214/aos/1176347265)
