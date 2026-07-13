# SPICE temporal paper alignment and ML-theory audit

Date: 2026-07-10

Status: research evidence only. No architecture, metric, model, dependency, or paper interpretation in this note is approved. The paper and the current code are both treated as fallible evidence.

Scope: the temporal module only, with emphasis on preprocessing, supervised target construction, fitting, model selection, evaluation, and the live action produced from a trained artifact. The paper's spatial routing and distributed-reputation proposals are described only where they affect the temporal experiment. They were not audited as implementation requirements.

Method: all 11 PDF pages at `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf` were rendered to images and visually inspected, then cross-checked against extracted text. Production code, packaged configuration, tests, representative benchmark definitions, commit `e0b2e68e` (`fix(features): enforce safe current-row fee dynamics`), and the current `PROGRESS.md`/`ARCHIVE.md` rationale were read independently. This report was cross-checked against `docs/research/issue-1/temporal-training-evaluation-theory-audit.md`. Small locked-environment probes were used for weighted-loss aggregation and macro-F1 semantics. Primary sources are linked for framework and statistical claims.

## Bottom line

The current temporal implementation is not a direct reproduction of the paper's operational decision, but this difference is intentional rather than an accidental off-by-one. Commit `e0b2e68e`, `ARCHIVE.md:9-36`, and `PROGRESS.md:243-255` document a safe block-open extension: offset zero is intended to target the current/forming block `h`; the design treats `base_fee[h]` as derivable before execution; and finalized facts for `h`, such as gas used and transaction count, are lagged to `h-1`. The parent-derived fee premise is supported for Ethereum; it still requires chain- and fork-specific proof for Polygon and Avalanche.

The confirmed problem is narrower and still fundamental: offline training/replay and current serving do not instantiate that intentional contract in the same way:

- training labels class `k` with the fee at block-open candidate row `h + k`;
- offline replay realizes the same `h + k` row but discards the sampled request timestamp needed to prove that the forming block was still actionable;
- live serving treats `h` as the latest confirmed block and targets inclusion block `h + k + 1`, without constructing the virtual/safe block-open row used by the training interpretation;
- the paper describes the baseline as next-block execution and the prediction target as a future block.

Therefore the current training loss, offline economic result, and live action do not yet prove one shared task. This does **not** establish that current-row offset zero is wrong or causally impossible. It establishes an owner-gated choice: preserve and operationally reconcile the block-open extension, redefine offset zero around an explicit decision/action slot, or restore the paper's next-block route. Historical savings should not approve any clean-break route until that choice and its feature-availability proof are fixed.

Four other confirmed defects affect scientific conclusions:

1. Internal train/validation/test splits are adjacent splits of anchor samples. Training outcome horizons cross into validation anchors, and validation outcome horizons cross into test anchors, despite the paper's claim of non-overlapping temporal intervals.
2. Epoch `total_loss` is batch-partition-dependent because SPICE multiplies PyTorch's class-weighted mean cross-entropy by sample count. The same four predictions reproduced reported loss values from `0.6539` to `0.7936` solely by changing batch partitions. Batch size is itself tuned.
3. A missing in-window block can be resolved to the first post-deadline block and receive economic credit. A checked-in test explicitly accepts negative `cost_over_optimum` when that late block is cheaper than every reachable block.
4. The configured training seed is applied after model construction, so it does not control initial weights.

The paper alone does not justify the current model complexity. It compares only LSTM, Transformer, and Transformer-LSTM; omits naive, deterministic, linear, and small-model forecasting baselines; uses one deliberately selected evaluation day; fixes one trained model per condition; and repeats only Poisson-window sampling. Its scalar fee head has no stated scheduling use. Current code confirms that the scalar head is ignored during decoding and serving.

HPO is different: it is a purposeful extension, not unexplained machinery. `PROGRESS.md:135-153,215-226` defines one bounded 32-trial calibration per chain/model cell, explicitly avoids retuning structural-ablation cells, and requires explicit presets before transplanting selected parameters. That is a serious retain candidate because it records and regularizes calibration. Its current weighted-loss, test-opening, pruning, and seed defects still need repair before its results can support selection.

The earlier TorchMetrics finding needs a narrower interpretation. TorchMetrics 1.9 does implement union-active macro F1 correctly; current SPICE does not. That proves a library-semantic difference, not that macro F1 belongs in SPICE. The paper never reports macro F1, and F1 does not measure transaction-cost regret. Deleting it is a valid, leaner candidate. If it is retained as a diagnostic, the current target-supported custom version should not be described as standard macro F1.

## What the paper actually specifies

| Topic | Paper fact | Paper location | Missing or weak specification |
|---|---|---|---|
| Objective | Observe recent fee history and select the minimum-cost future execution block inside an application-defined delay window. | Sec. IV-A, PDF pp. 4-5 | It does not formalize whether the action is submission time, desired inclusion block, or achieved inclusion block. |
| Baseline | No temporal prediction means the transaction is added to the next block. | Sec. VI-C, PDF p. 9 | The decision timestamp relative to block production is not defined. |
| Target | Two heads: min-block offset classification and scalar minimum-fee regression. | Sec. VI-A, PDF pp. 7-8 | No rule uses the scalar fee prediction. The heads' consistency is not defined. |
| Horizons | Separate 12, 24, and 36 second conditions; a separate model is trained for each chain and horizon. | Sec. VI-A, PDF p. 8 | Seconds are converted to block counts even though Avalanche cadence is acknowledged as irregular. |
| Input history | A 600 second lookback divided by nominal block time. | Sec. VI-A, PDF p. 8 | Rolling-200-block features already depend on observations much older than 600 seconds on Ethereum. |
| Features | Block metadata; hour/day cyclic encodings; elapsed position; a trend indicator; rolling mean/std for fee and gas utilization at 10/50/200 blocks. | Table II, PDF p. 8 | Trend, source lag, null handling, rolling inclusion boundary, and exact feature formulas are absent. |
| Transform | Fee-related values are log transformed. All features are standardized with training-split statistics. | Sec. VI-A, PDF p. 8 | Exact log convention, clipping, and constant-column behavior are absent. |
| Split | Temporally ordered, non-overlapping train, validation, and test intervals; about 400k samples; test evaluated once. | Sec. VI-A, PDF p. 8 | Dates, proportions, gap/purge rule, and whether horizons may cross boundaries are absent. |
| Models | LSTM, Transformer encoder, and Transformer-LSTM, each with two MLP heads. | Sec. VI-A, PDF pp. 7-8 | No parameter counts, initialization, number of seeds, or simple model baselines. |
| Loss | `alpha * L_block + beta * L_fee`; inverse-frequency weighted cross-entropy plus Smooth L1. | Sec. VI-A, PDF p. 8 | `alpha`, `beta`, fee-target scaling, class-weight normalization, and reduction semantics are absent. |
| Predictive metrics | Average total loss and block-offset accuracy. | Sec. VI-A, PDF p. 8 | No regression error, class distribution, per-class performance, calibration, or economic model-selection metric. Macro F1 is not present. |
| Economic metrics | Mean base-fee excess over hindsight optimum and percentage gain over immediate baseline. | Figs. 5-7, PDF pp. 9-10 | Exact aggregation formulas and error-bar meaning are absent. Harmful-delay frequency and deadline misses are absent. |
| Arrival process | Requests follow a Poisson process with rate `0.05/s`; each run selects a random two-hour window; 50 repetitions. | Sec. VI-A, PDF p. 7 | Repetitions vary arrivals/windows only. They do not measure training-seed or day/regime uncertainty, and windows may overlap. |
| Evaluation data | All reported economic evaluation uses 9 November 2025, deliberately chosen because the cheapest chain changed that day. | Sec. VI-A, PDF p. 7 | Selecting a day after inspecting its outcome creates selection bias and cannot establish general behavior. |
| Cost | Base fee per gas is treated as dominant; priority fee is neglected; immediate next-block inclusion is assumed. | Secs. III and VI-A, PDF pp. 3 and 7 | Base fee per gas is not full transaction cost. The assumption may be useful, but its scope must be explicit. |
| Claims | Temporal gains reach about 2.5% Ethereum, 0.15% in the abstract or 0.2% in the body for Polygon, and 1% Avalanche. | Abstract; Sec. VI-C, PDF pp. 1 and 9 | Polygon's headline is internally inconsistent. One Avalanche Transformer/36s result is negative despite broader "consistently" language. |

### Paper interpretation

The paper supports a bounded, decision-focused forecasting problem. It does not establish that its exact multitask formulation is theoretically preferable. Its statement that predicting only the minimum is safer than forecasting the short trajectory is an interpretation, not a tested result: no trajectory, regression, statistical, or heuristic forecast baseline is included.

The paper's strongest ideas are chronological evaluation, train-only normalization, one final test evaluation, and explicit economic comparison against immediate execution and hindsight optimum. Those ideas are sound only if the implementation's decision clock, split boundaries, and metric aggregation are sound.

## Paper-to-code alignment map

`Exact` means the code materially implements the stated paper rule. `Refinement` means it deliberately adds or sharpens behavior. `Partial` means important semantics remain different or unstated. `Divergence` means the executable behavior conflicts with the paper or serving behavior.

| Concern | Current code evidence | Verdict |
|---|---|---|
| 600s / 36s defaults | `src/spice/conf/problem/current_row_nominal.yaml:1-9` | Partial: values match, but the realized input/action timelines do not strictly match seconds. |
| Separate horizon training in standard sweeps | `src/spice/conf/benchmark/delay_degradation_sweep.yaml:26-39` grids `max_delay_seconds` and trains each expanded case. | Exact relative to the paper. It is incorrect to characterize the standard delay sweep as one 36s model reused for every horizon. |
| Supported shorter-delay artifact reuse | Evaluation accepts `delay_seconds <= capability_max_delay_seconds` at `src/spice/modeling/artifact_inference.py:112-118`; the store retains the artifact action width at `src/spice/temporal/compilers/observed_time_window.py:204-247`; serving masks allowed offsets at `src/spice/serving/inference.py:181-191`. | Partial: this is an extra API path, not the standard paper benchmark. Equivalence to a separately trained shorter-horizon model has not been demonstrated. |
| Fixed temporal input | Sequence length is estimated from training median cadence and clipped at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:41-57,261-274`. | Refinement with a semantic mismatch: it uses observed median, not paper nominal cadence, and clipping can override 600s. |
| Candidate origin | Production compiler sets `candidate_start_rows = anchor_candidates` at `src/spice/temporal/compilers/observed_time_window.py:352-363`. | Intentional refinement and paper divergence: the anchor is the current/forming block under the documented block-open extension. This is coherent only if its pre-inclusion instant, safe feature row, and actionability are proved. |
| Min-block label | Reachable candidate log fees are argmin-labeled at `src/spice/prediction/families/min_block_fee_multitask/batch.py:13-35`. | Exact relative to the current-row store. Its operational validity depends on reconciling that store with feature availability, replay timing, and serving; it is not automatically a wrong label. |
| Two prediction heads | `src/spice/prediction/families/min_block_fee_multitask/outputs.py:9-20`; both MLP heads are built by `src/spice/modeling/families/_heads.py:33-57`. | Exact architecture reproduction. |
| Inference decision | Decode uses only offset logits at `src/spice/prediction/families/min_block_fee_multitask/__init__.py:71-84`. | Partial: the fee head is not part of the action. |
| LSTM/Transformer/hybrid | `src/spice/modeling/families/lstm.py:52-79`, `transformer.py:67-91`, `transformer_lstm.py:73-106`. | Exact at the architectural level. |
| Feature recipe | 45 core outputs at `src/spice/conf/features/core_fee_dynamics.yaml:1-47`; 46 with elapsed position; 77 with priority-fee context. | Refinement: substantially broader than Table II. No evidence yet that the extra lags/windows earn their complexity. |
| Block-open feature policy | Current base fee is retained under the documented pre-execution-derivability premise; gas used, gas limit, and transaction count are shifted one row at `src/spice/features/sets/core_fee_dynamics/_block_facts.py:27-47`; rolling transforms are trailing at `_transforms.py:59-69`. | Intentional and substantially causal for the proved sources. Ethereum supports the fee premise; Polygon/Avalanche need fork-aware proof. Realized `timestamp[h]` still feeds cadence/calendar values, so the complete forming-row information set is not yet proved. |
| Log transform | Current base fee uses clipped natural log at `src/spice/features/sets/core_fee_dynamics/_base_fee.py:27-39` and `_transforms.py:17-23`. | Exact in intent; more explicit than the paper. |
| Train-only scaling | Scaler is fitted from rows covered by train contexts at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:85-95,283-287`; transform uses persisted stats at `src/spice/temporal/input_normalization/scaling.py:51-80`. | Exact and defensible. |
| Chronological split | Contiguous 80/10/10 anchor positions at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:204-233`; config at `src/spice/conf/split/default.yaml:1-2`. | Partial: ordered, but supervised outcome windows cross internal boundaries. |
| External evaluation cutoff | Training retains only samples whose last outcome is before cutoff at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:102-118`; named evaluation suites supply the earliest window as cutoff at `src/spice/config/models.py:144-153` and `src/spice/config/resolution.py:157-164`; evaluation rejects windows before artifact cutoff at `src/spice/modeling/artifact_inference.py:123-132`. | Refinement and good practice. It does not repair internal split leakage. |
| Loss | Weighted CE plus normalized Smooth L1, with hard-coded coefficient `0.5`, at `src/spice/prediction/families/min_block_fee_multitask/loss.py:12-41`. | Partial: paper coefficient is unspecified; current economic meaning is unproven. |
| Early stopping/model selection | Total validation loss is the fixed selection metric at `src/spice/modeling/_fit_policy.py:15,101-134`; tuning returns the same value at `src/spice/modeling/tuning_execution.py:201-228`. | Partial: technically coherent intent, but not aligned with economic utility and currently misaggregated. |
| Predictive metrics | Accuracy, custom macro F1, component losses, log-fee MAE/MSE at `src/spice/prediction/families/min_block_fee_multitask/metrics.py:133-165,235-248`. | Refinement, but macro F1 is nonstandard and no classification metric is the operational objective. |
| Economic metrics | Per-event relative savings/regret, exact-hit rate, and fee sums at `src/spice/evaluation/temporal_accounting.py:91-130`; descriptors at `src/spice/evaluation/_temporal_replay_metric_catalog.py:32-83`. | Useful refinement, but decision timing and aggregation need correction. |
| Repetition | Packaged Poisson replay uses two hours, 50 repetitions, rate `0.05/s`, seed 2026 at `src/spice/conf/evaluator/poisson_replay.yaml:1-5`. | Exact reproduction of the paper's simulation randomness, not a complete uncertainty protocol. |
| Paper corpus recipe | `src/spice/conf/corpus/icdcs_2026.yaml:1-4` covers only 8-10 November 2025. | Divergence/ambiguity: this config alone cannot reproduce the paper's approximately 400k pre-day samples per chain. Current benchmark corpus IDs point to later, larger materialized corpora. |
| Live action | Serving maps offset `k` to broadcast after confirmed block `h+k` and target block `h+k+1` at `src/spice/serving/inference.py:82-105`. | Cross-layer divergence: serving does not synthesize the safe forming-block row assumed by the current-row training route. Its `+1` is coherent for a post-confirmation request and closer to the paper's next-block baseline. |

## Confirmed critical findings

### 1. Training/replay and serving instantiate different decision rows

**Fact.** The production compiler deliberately includes its block-open anchor in the candidate window, while serving uses the last confirmed block as its anchor:

```text
offline block-open anchor/candidate  h
training target class k              fee(h + k)
offline realized class k            fee(h + k)
serving last confirmed block         h
live broadcast class k               after block h + k
live target class k                  block h + k + 1
```

The compiler assignment is at `src/spice/temporal/compilers/observed_time_window.py:352-363`. Baseline rows remain `candidate_start_rows` at `src/spice/temporal/execution_policy/strict_deadline_miss.py:69-107`. Offline evaluation reads fees at the resulting rows at `src/spice/evaluation/temporal_accounting.py:85-105`. Serving fetches confirmed blocks, selects the last row as its anchor at `src/spice/serving/inference.py:70-73,144-176`, and makes the `+1` target explicit at lines 85-103.

**Recovered intent.** Commit `e0b2e68e` deliberately removed the unsafe `same_block_closed` route and retained a safe current-row/block-open route. `ARCHIVE.md:9-36`, `PROGRESS.md:243-255`, and `src/spice/features/ARCHITECTURE.md` define its causal idea: derive `base_fee[h]` before execution and expose finalized `h` facts as lagged `h-1` sources. Ethereum's specification supports the parent-derived base-fee fact ([EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)); equivalent availability is not assumed for Polygon or Avalanche across their corpus forks. The paper instead says the model estimates the next `M` seconds, identifies a *future block* (PDF p. 5), and uses a *next block* baseline (PDF p. 9).

**Interpretation.** Offset zero can coherently mean the current/forming block if the decision occurs before inclusion closes and every feature is available then. Ethereum's current base fee and the deliberately lagged finalized block facts substantially support that contract; other chain/fork fee rules remain to prove. The complete information set does not yet: `seconds_since_previous_block`, hour, and day-of-week use realized `timestamp[h]` at `src/spice/features/sets/core_fee_dynamics/_time.py:27-94`; exact forming-block cadence is not ordinarily available through the confirmed-block RPC path. Serving also does not create a virtual forming row from parent state and decision-time values. Conversely, if serving's `h` is kept as the latest fully confirmed block, targeting `h` is no longer available and the `+1` mapping is coherent. The defect is lack of one cross-layer definition, not the existence of the intentional current-row definition.

**Risk.** Historical training/replay results describe the intended block-open task, while deployed serving describes a post-confirmation task. They cannot be compared as one policy. Calling the offline numbers automatically optimistic would overstate the evidence; optimism follows only if the block-open availability/actionability assumptions fail. Those assumptions and per-chain fee rules are not yet proved.

**Test gap.** Existing tests prove local target and accounting formulas, but no worked fixture proves that compiler inputs, feature availability, replay realization, and serving response refer to the same decision instant and action.

**Owner-gated routes.** At least three routes deserve explicit comparison; none is approved here:

1. **Preserve and reconcile the block-open extension.** Keep physical forming block `h` as offset zero. Construct the same safe/virtual row offline and live from parent-derived fee state, lagged finalized facts, and decision-time replacements for realized timestamp/cadence; prove the transaction can still target `h` on each chain.
2. **Redefine offset zero as an action slot.** Make zero mean “broadcast now at decision time `tau`,” not “select physical row `h`.” Map each wait action to its first eligible realized inclusion block through one outcome function. This can preserve immediate-action intuition without pretending the feature row and outcome row are the same object.
3. **Restore a paper-next-block route.** Keep the latest confirmed block as context, make class zero/baseline target the first future block, and realign training/replay with serving. Treat prior current-row results as archival rather than silently relabeling them as paper reproduction.

Every route needs one executable decision record shared by dataset labels, offline replay, and serving:

- decision timestamp or observed head;
- whether the row is confirmed, forming, or virtual;
- allowed wait action;
- submission/broadcast timestamp;
- first eligible inclusion block;
- realized base fee and optional priority fee;
- baseline action;
- deadline rule;
- feature availability proof for each supported chain.

The owner must choose the route and whether delay constrains submission time or achieved inclusion time before targets or historical results are reclassified.

### 2. Poisson arrivals are discarded before economic accounting

**Fact.** Replay samples exponential arrival timestamps, but maps each arrival to the latest sample timestamp at or before it (`searchsorted(..., side="right") - 1`) at `src/spice/evaluation/poisson_replay.py:28-61`. Only selected sample positions survive at lines 79-105. The actual arrival timestamps are not passed to temporal accounting. The baseline then uses the selected sample's block-open candidate start.

**Interpretation.** The replay is a random weighting of decision rows, not a complete request-time simulator. Under the intentional block-open route, the discarded arrival time is precisely what would establish whether request arrival preceded the pre-inclusion cutoff for candidate `h`. Under a confirmed-block route, it is needed to identify the first eligible future block. Mapping to row `h` is therefore not automatically wrong, but the current mapping cannot prove either route's timing contract.

**Risk.** The paper's Poisson-process interpretation and the current metric labels overstate what the code simulates. Late-in-block arrival, forming-block actionability, first eligibility, and actual predicted wait cannot be measured correctly from sample positions alone.

**Candidate.** After the owner selects a decision route, either:

1. model request-time decisions and retain each arrival timestamp through outcome realization; or
2. explicitly define a block-bound exposure-weighting policy, rename the evaluator, and specify which arrivals each safe decision row represents.

Mixing request-time Poisson wording with block-bound accounting should not survive the clean break.

### 3. Block offsets do not implement a strict seconds-bounded policy

**Fact.** Action width is `floor(max_delay_seconds / slot_spacing_seconds) + 1` at `src/spice/temporal/compilers/observed_time_window.py:313-319`, but outcome columns are consecutive physical block rows at `src/spice/temporal/execution_policy/strict_deadline_miss.py:77-100`. The action space marks every column available, even when a historical window contains fewer blocks (`strict_deadline_miss.py:33-45`). Missing columns are filled with the first row after the time window and marked overflow (`strict_deadline_miss.py:92-106`).

**Interpretation.** Offset `k` is trained as the `k`-th observed block, while serving describes it as roughly `k * nominal_spacing` seconds. Those are different quantities on irregular cadence.

**Local diagnostic.** A separate one-million-anchor diagnostic over the current materialized Polygon and Avalanche training corpora found large count/width mismatch: 72.8% of sampled Polygon 36s windows had fewer than the nominal 19 physical candidates; Avalanche windows had fewer than 23 candidates in 37.1% and more than 23 in 54.2%. This diagnostic is evidence of scale, not an approved benchmark; exact corpus paths, cutoff approximation, and method are recorded in `docs/research/issue-1/temporal-preprocessing-theory-audit.md`.

**Risk.** `max_delay_seconds` can be violated, action meaning shifts by chain/regime, and a live block-number wait is not equivalent to the trained time horizon.

**Candidate.** A simpler truthful action space is wait duration, such as `{0, 12, 24, 36}` seconds. For decision time `tau` and wait `d`, define submission at `tau+d` and outcome as the first eligible inclusion block after submission. Multiple waits mapping to the same block can tie-break toward the shorter wait. This handles irregular cadence without pretending a physical block index is elapsed time. It still needs an explicit rule for inclusion latency beyond the submission deadline.

### 4. Deadline misses can improve the reported objective

**Fact.** Overflow requests execute at the first post-window row at `src/spice/temporal/execution_policy/strict_deadline_miss.py:119-149`. Economic accounting includes that row's fee normally and records only an `overflow_count` metadata value at `src/spice/evaluation/temporal_accounting.py:91-130`. `tests/evaluation/test_temporal_accounting.py:94-118` expects `cost_over_optimum == -1/8` when a post-window overflow block is cheaper than the reachable optimum.

**Interpretation.** Negative regret relative to a reachable optimum is possible only because the model violated the reachable window and was rewarded for the later fee. The name `strict_deadline_miss` does not make the economic objective deadline-aware.

**Risk.** A model can appear economically better by missing the service constraint. Aggregate results do not expose a deadline-miss rate.

**Candidate.** A deadline miss must be one of:

- impossible because unavailable actions are masked;
- executed by a separately defined fallback and scored as a miss;
- assigned an explicit application penalty.

It should never silently enter ordinary savings as though it were in-window success.

### 5. Internal split labels cross temporal boundaries

**Fact.** Samples are first constructed with future candidate windows. Selected sample indices are then sliced contiguously into 80/10/10 roles at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:204-233,253-305`. There is no gap between the final training anchor and first validation anchor, or between validation and test. The final training sample's candidate window therefore contains rows at or after early validation anchors whenever the horizon spans more than zero rows.

**Interpretation.** Overlapping past context is not inherently leakage; a deployed forecaster legitimately uses earlier observed history. The defect is future-label overlap: a training target consumes outcomes from the nominal validation interval.

Scikit-learn's official time-series splitter exposes a `gap` specifically to exclude samples between training and evaluation partitions ([TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)). The forecasting literature likewise warns that validation must preserve temporal order and the real information set ([Hewamalage et al., 2023](https://doi.org/10.1007/s10618-022-00894-5)).

**Risk.** Validation and test results are mildly optimistic and conflict with the paper's non-overlapping-interval statement. The amount depends on horizon and cadence.

**Candidate.** Define raw timestamp cutoffs first. Permit evaluation contexts to look backward, but require:

- every training outcome ends before validation starts;
- every validation outcome ends before test starts;
- every external-training outcome ends before the external evaluation cutoff.

The third rule is already implemented well at `fixed_sequence_temporal.py:102-118`; reuse that same explicit outcome-end rule internally.

### 6. Reported weighted loss depends on batch partition

**Fact.** Classification uses `F.cross_entropy(..., weight=class_weights)` with default mean reduction at `src/spice/prediction/families/min_block_fee_multitask/loss.py:24-28`. PyTorch defines this mean as weighted loss sum divided by the sum of target-class weights, not by sample count ([CrossEntropyLoss](https://docs.pytorch.org/docs/2.13/generated/torch.nn.CrossEntropyLoss.html)). SPICE then multiplies each scalar batch mean by batch sample count and divides accumulated totals by sample count at `src/spice/prediction/families/min_block_fee_multitask/metrics.py:168-207,235-248`.

Locked-environment reproduction on the same four logits/targets/class weights:

| Batch partition | SPICE-style reported CE |
|---|---:|
| `[4]` | 0.793620 |
| `[2, 2]` | 0.693627 |
| `[1, 3]` | 0.653926 |

**Interpretation.** This is not the full-split weighted cross-entropy. Validation score can change with tail batches and class composition even when predictions do not.

**Risk.** Checkpoint selection, early stopping, and Optuna trial ranking use this value. Large-capacity tuning includes batch size as a hyperparameter (`src/spice/conf/tuning_space/lstm_large_capacity.yaml:1-10` and corresponding Transformer spaces), so the objective itself changes with a tuned batching choice.

**Candidate.** If weighted CE survives, accumulate its exact numerator and summed target weights. Accumulate regression numerator and sample count separately. Define the combined full-split loss explicitly. A leaner candidate is to ablate class weighting or the whole multitask objective before preserving reducer machinery.

### 7. The selection loss is not the downstream objective

**Fact.** The target family fits inverse-frequency class weights and fee normalization from train targets at `src/spice/prediction/families/min_block_fee_multitask/__init__.py:34-51`. Total loss is `weighted CE + 0.5 * normalized SmoothL1` at `loss.py:24-40`. `total_loss` is always the primary metric and model-selection direction at `src/spice/prediction/families/min_block_fee_multitask/__init__.py:87-104` and `src/spice/modeling/_fit_policy.py:15,101-134`.

**Interpretation.** Inverse-frequency CE gives rare optimum offsets equalized influence. That may improve balanced class recognition, but it need not improve savings. It can encourage delay when the economically dominant action is immediate execution. Cross-entropy also penalizes a harmless near-tie and a costly miss similarly.

Decision-focused research distinguishes predictive error from downstream decision regret; better prediction metrics do not guarantee better decisions ([Mandi, Bucarey, and Guns, ICML 2022](https://proceedings.mlr.press/v162/mandi22a/mandi22a.pdf)). This does not mandate a complicated decision-focused loss. It does mandate evaluating the actual action.

**Risk.** Hyperparameter search can select a lower multitask loss and worse economic policy. Current evidence does not establish otherwise.

**Candidate.** Compute deterministic, full-validation economic regret/savings for every checkpoint candidate, without Poisson resampling. Compare these lean objectives before choosing:

1. unweighted offset classification only;
2. a single vector of future-fee predictions with Smooth L1, decoded by argmin;
3. the current multitask loss;
4. a simple cost-sensitive or ranking surrogate only if the first three fail materially.

Choose the simplest option that is economically indistinguishable under a pre-approved tolerance.

### 8. The scalar fee head is operationally unused

**Fact.** Models emit offset logits and one scalar fee (`outputs.py:9-20`) and train both (`loss.py:12-41`). Decoding reads only offset logits at `src/spice/prediction/families/min_block_fee_multitask/__init__.py:71-84`. Offline evaluators accept decoded offsets, not predicted fees (`src/spice/evaluation/temporal_replay_runner.py:70-137`). Serving also reads only decoded offsets (`src/spice/serving/inference.py:74-89`).

**Interpretation.** Fee regression is an auxiliary representation-learning task, not a required output. Its target is the true global minimum fee even when the offset head selects another block, so the heads are not constrained to describe one coherent predicted action.

**Risk.** It adds a head, target normalization state, loss coefficient, metrics, persistence, and teaching burden without demonstrated value.

**Candidate.** Run a paired ablation. Delete the fee head if it does not produce a material, repeatable economic improvement. If predicted fee is intended for a later chain-selection or confidence decision, specify that consumer before retaining it.

### 9. `lookback_seconds` is not the effective information horizon

**Fact.** Default `lookback_seconds` is 600, while default sequence bounds are 64-4096 at `src/spice/conf/training/default.yaml:11-13`. Ethereum's nominal 600/12 calculation is 50 rows, but `_compute_seq_len` clips it to 64 at `src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:41-57`. The sequence therefore spans about 768 nominal seconds, not 600.

The 45-feature core includes rolling-200 fee and previous-gas-utilization summaries (`src/spice/conf/features/core_fee_dynamics.yaml:33-47`). The earliest row of a 64-row Ethereum sequence can depend on raw gas data about 263 blocks before the anchor because the rolling window and previous-row shift compose. At nominal cadence this is about 3,156 seconds, or 52.6 minutes.

**Interpretation.** A fixed sequence can legitimately contain features summarized from older history, but then `lookback_seconds=600` is not the observed-data horizon described by the paper. The paper inherits the same conceptual weakness by combining a 600s sequence with rolling-200 features.

**Risk.** Thesis readers cannot tell what information the model actually uses. Lookback ablations do not isolate history length while rolling windows remain fixed.

**Candidate.** Choose one truthful concept:

- `sequence_length_blocks`, with feature-history span documented separately;
- an actual time-bounded raw history with features restricted to it; or
- a small fixed feature vector where each feature's history is explicit.

For readability, first ablate duplicated lag features and long rolling summaries. An LSTM already sees earlier sequence rows; six explicit fee-change lags and six utilization lags may not earn their extra surface.

### 10. The configured seed does not control model initialization

**Fact.** `build_model(...)` runs at `src/spice/modeling/pipeline.py:251-255`. The training seed is not set until `run_training_fit` prepares the runtime, which calls `set_global_seed` through `src/spice/modeling/runtime_planning.py:73-82`; `set_global_seed` itself is at `src/spice/modeling/_runtime.py:60-63`.

**Interpretation.** Initial weights depend on ambient RNG state. `training.seed: 2026` controls later sampling but not the parameter initialization it appears to control.

**Risk.** First runs, repeated runs, and trial comparisons are not reproducible under the stated seed. A fixed single seed would still not estimate seed uncertainty, but it should at least reproduce one run.

**Candidate.** Seed once at the workflow boundary before dataset preparation and model construction. If Lightning remains, its documented automatic path is the idiomatic place to centralize ordinary one-optimizer training; Lightning recommends automatic optimization for most research cases ([Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)). Exact checkpoint/nonfinite semantics still need the separate prototype already identified in the clean-break map.

## Metrics: what is correct, misleading, or unnecessary

### Macro F1

**Fact.** The paper never reports macro F1. Current SPICE skips every class with no target support at `src/spice/prediction/families/min_block_fee_multitask/metrics.py:76-94`, even if the model predicted that class. TorchMetrics 1.9 excludes only fully inactive classes where `TP + FP + FN == 0`; predicted-only classes remain active with F1 zero ([tagged TorchMetrics reduction](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93), [F1 API](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)).

Locked-environment diagnostic with targets `[0, 0]`, predictions `[0, 2]`, and three classes:

- current SPICE target-supported macro F1: `0.6667`;
- TorchMetrics union-active macro F1: `0.3333`.

**Interpretation.** The earlier false alarm was correctly removed: TorchMetrics is not the bug. Current SPICE's metric is nonstandard. More importantly, neither macro definition expresses fee savings, regret, or deadline safety.

**Candidate.** Delete macro F1 unless a thesis question explicitly needs class-balanced discrimination. If retained as a diagnostic, use the existing locked TorchMetrics implementation rather than custom count/reduction code. TorchMetrics is already present transitively through Lightning (`uv.lock:2701-2702`); importing it as a supported API would require a direct dependency if Lightning remains.

### Accuracy and exact optimum hit rate

**Fact.** Paper accuracy and current `offset_accuracy` count exact argmin matches. Current replay also reports `exact_optimum_hit_rate`.

**Interpretation.** These are understandable diagnostics, but classes are economic actions, not equally costly labels. Choosing the second-best block for a negligible difference is counted as fully wrong; choosing a disastrous block is also counted once. Accuracy can stay as an explanatory metric, not the primary result.

### Economic aggregation

**Fact.** Current primary replay metric is the event mean of `(baseline_fee - realized_fee) / baseline_fee` at `src/spice/evaluation/temporal_accounting.py:102-117` and `_temporal_replay_metric_catalog.py:32-40`. Fee sums are also persisted, but no ratio-of-sums metric is exposed.

**Interpretation.** Mean percentage per request gives cheap and expensive baseline events equal weight. Aggregate economic savings for equal-gas transactions is instead:

```text
(sum(baseline_fee) - sum(realized_fee)) / sum(baseline_fee)
```

Neither is universally "the" correct metric; they answer different questions and should be named.

**Candidate metric set.** Keep a small set with distinct jobs:

- primary economic result: owner-approved aggregate savings definition;
- opportunity/regret: realized versus reachable optimum;
- safety: harmful-decision rate (`realized > baseline`) and deadline-miss rate;
- latency: chosen wait distribution;
- diagnostic: exact-hit accuracy;
- fee MAE only if a fee prediction remains an actual product output.

`baseline_cost_over_optimum`, custom macro F1, component losses, and duplicate fee summaries should survive only if each answers a documented thesis question.

### Window uncertainty

**Fact.** Window summaries compute mean and population standard deviation over replay runs at `src/spice/evaluation/_temporal_replay_metric_catalog.py:223-238`. The paper's 50 runs draw from one day and one fixed trained model.

**Interpretation.** That standard deviation is Monte Carlo variation in selected windows/arrivals. Conditional on the fixed trace, independently sampled runs remain independent simulator draws even when their historical spans overlap, so a Monte Carlo standard error can describe integration error. It is not a confidence interval for model training, future days, or blockchain regimes.

**Candidate.** For final thesis claims, predeclare multiple evaluation days/windows covering fee level and volatility regimes, compare methods on the same events/windows, and repeat stochastic training with a small approved seed set. Report the paired distribution across independent windows/days separately from training-seed variation. Do not inflate runtime machinery; an experiment driver can own repetition.

## Preprocessing review

### Defensible current choices

- The current-row source policy is deliberate. Commit `e0b2e68e` removed finalized same-block inputs, retained `base_fee_per_gas[h]` for the block-open decision, and shifted finalized gas/transaction facts to `h-1`; `ARCHIVE.md:9-36` records why. Ethereum's parent-derived base-fee rule supports that specific fee input at a pre-execution instant.
- Base fee and count-like variables use log/log1p transforms before standardization (`src/spice/features/sets/core_fee_dynamics/_transforms.py:17-23`; `_block_facts.py:50-82`). This is reasonable for positive heavy-tailed values.
- Calendar cycles use sine/cosine instead of raw ordinal hour/day (`src/spice/features/sets/core_fee_dynamics/_time.py:37-54`).
- Rolling features are trailing, not centered (`_transforms.py:59-69`), so they do not themselves read future rows.
- Scaler statistics come from train-covered rows only and are reused for validation/test/inference (`fixed_sequence_temporal.py:85-95,283-287,364-365`). This follows the standard fit/transform contract documented by scikit-learn ([StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)).
- The optional elapsed-position feature is not in the default core set. It is isolated in an ablation config (`src/spice/conf/features/core_fee_dynamics_elapsed_position.yaml:1-48`). That is safer than silently making an arbitrary corpus origin part of every model.

### Unresolved risks

- Causality is only meaningful after the decision timestamp is fixed. A feature can be row-causal yet unavailable for a transaction decision tied to an earlier point in the block lifecycle; this is a qualification of the safe block-open route, not evidence that the route was accidental.
- The Ethereum EIP-1559 recurrence is not a blanket proof for Polygon and Avalanche across every fork in the materialized corpora. Polygon Bor v2.6 config places mainnet Bhilai, Dandeli, and Lisovo at blocks 73,440,256, 81,424,000, and 83,756,500; its verifier switches after Lisovo from exact `CalcBaseFee` equality to accepting a producer-selected child base fee within a +/-5% parent-fee boundary ([Bor fork config](https://github.com/0xPolygon/bor/blob/v2.6.0/params/config.go), [Bor EIP-1559 verifier](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go)). The current large Polygon corpus crosses those upgrades, so parent state alone cannot reconstruct every `base_fee[h]` in its suffix. Avalanche also requires fork-aware parent state and timestamp analysis. Exact corpus/fork evidence belongs to `docs/research/issue-1/temporal-chain-fee-protocol-audit.md`.
- `seconds_since_previous_block`, hour, and day-of-week use realized `timestamp[h]` (`src/spice/features/sets/core_fee_dynamics/_time.py:27-94`). A forming-block route needs a decision-time replacement or an equivalence/error argument; exact cadence into an unconfirmed row is not supplied by the current confirmed-block serving source.
- The default 45 features mix current fee, shifted block facts, repeated lags, rolling min/mean/std at five windows, and calendar values. This is much broader than the paper and hard for an undergraduate reader to reason about.
- Long rolling summaries confound lookback ablations.
- `elapsed_seconds` is relative to the first row of whichever combined frame is built (`src/spice/features/sets/core_fee_dynamics/_time.py:21-24`), so training and live origins need not share semantic meaning.
- The priority-fee ablation adds priority-fee inputs, but targets and economic evaluation remain base-fee-only (`batch.py:21-30`; `temporal_accounting.py:91-105`). It does not test full transaction-cost optimization.

### Lean candidates

1. Begin the ablation ladder with a small causal feature set: current log base fee, previous gas utilization, recent fee change, elapsed block interval, and only the shortest justified rolling context.
2. Add calendar cycles and longer rolling summaries one group at a time, retaining a group only for material economic improvement across predeclared windows.
3. If sequence models remain, test deletion of explicit lag columns first; the sequence already exposes prior timesteps.
4. If scikit-learn is not retained for simple baselines, replace its sole production use - `StandardScaler` fitting - with NumPy mean/population-std and remove the dependency. The existing clean-break framework research already found float32 parity. If a scikit-learn linear/tree baseline earns its place, the dependency may instead become justified.

## Training, model selection, and tuning review

### What is idiomatic or defensible

- AdamW, gradient norm clipping, validation-based early stopping, and a held-out test role are ordinary choices. Their presence alone is not evidence that their hyperparameters are right.
- Class weights and fee normalization are fitted on training targets only (`src/spice/modeling/training_runtime.py:36-69`).
- Final persisted training recomputes validation and test metrics from selected best weights (`src/spice/modeling/persisted_training.py:93-145`).
- Named evaluation suites establish a cutoff, and external evaluation must follow it.

### HPO is purposeful bounded calibration

HPO is an intentional research extension beyond the paper. `PROGRESS.md:135-153,215-226` gives it a bounded role: one 32-trial calibration for each chain/model cell on the canonical feature set, no retuning inside structural sweeps, and no reuse outside the exact study identity until selected values become explicit presets. This policy can reduce undocumented hand tuning, preserve a trial journal, expose interactions, and spend GPU hours consistently. Optuna is therefore a serious retain candidate, not an automatic deletion target.

Its approval still depends on a lean, scientifically valid boundary:

- trials compare a common, validation-only surface;
- corrected loss reduction makes the objective comparable across batch sizes;
- intermediate pruning actually stops epochs, or the study openly uses no pruning;
- the final test remains sealed until the configuration and seed protocol are frozen;
- finalists, not every trial, are repeated across the approved seeds.

### Complexity or implementation that still needs evidence or repair

- SPICE uses Lightning manual optimization for one AdamW optimizer (`src/spice/modeling/lightning_module.py:57-104`) while also maintaining a custom fit-policy state machine, checkpoint format, metric accumulators, and batch planner. This takes the least idiomatic part of both Lightning and a hand-written PyTorch loop.
- The current prediction-family implementation alone includes custom training-state, target, loss, metric, and two-head plumbing. Much of it disappears if the fee head, weights, and macro F1 fail ablation.
- Large tuning spaces reach hidden sizes 768 and Transformer dimensions 1024 (`src/spice/conf/tuning_space/*_large_capacity.yaml`). Bounded calibration can legitimately include them, but a small-model baseline ladder is still needed to show that the resulting capacity earns its teaching and runtime cost.
- Optuna pruning is checked only after full trial training and summary construction (`src/spice/modeling/tuning_execution.py:201-228`), so it cannot save epoch work. This is a defect in the HPO implementation, not an argument against HPO.
- Every Optuna trial calls `run_trial_training`, which builds a summary including test metrics (`src/spice/modeling/persisted_training.py:192-214,93-124`). The test score is not returned as the objective, but repeatedly computing it is unnecessary procedural exposure and work.
- Structural choices such as lookback can change eligible anchors. Any tuned dimension that changes sample geometry needs common predeclared validation origins or a documented common-subset rule.

### Framework candidates, not decisions

**Candidate A: idiomatic Lightning.** Use automatic optimization, normal `self.log`/TorchMetrics state, stock callbacks where their semantics are accepted, and a very small custom boundary only for requirements stock callbacks do not satisfy. This likely removes manual optimizer code and custom metric accumulation. Exact finite-best and resume semantics still need the existing prototype gate.

**Candidate B: small pure-PyTorch fit loop.** For one GPU, one optimizer, no distributed training, and a thesis-sized model, a direct loop may be easier to teach than a framework wrapped in custom policy. It must still handle best weights, early stopping, device transfer, and deterministic seeding correctly.

Do not choose by framework fashion. Prototype both against the approved semantics and compare production lines, concepts a reader must learn, failure behavior, and test burden.

### Baseline ladder required before retaining complex models

The paper cannot show that deep or hybrid architectures are necessary because it compares only deep candidates. Forecast-evaluation research explicitly recommends meaningful naive and simple baselines; large competitions also show why complexity must earn itself empirically ([Hewamalage et al.](https://doi.org/10.1007/s10618-022-00894-5), [M4 competition](https://doi.org/10.1016/j.ijforecast.2019.04.014)).

Run a paired ladder on exactly the same splits and decisions:

1. always execute immediately;
2. majority-offset predictor;
3. deterministic EIP-1559 next-base-fee plus a persistence/simple future rule;
4. linear/logistic or shallow MLP on a small current feature vector;
5. single-layer small LSTM;
6. current LSTM;
7. Transformer and Transformer-LSTM only if earlier candidates leave a material gap.

The operational no-delay baseline remains necessary even if it is not called a forecasting model. Majority and deterministic baselines answer whether high accuracy comes from imbalance or protocol mechanics. A model family should survive only if its economic improvement exceeds an owner-approved practical threshold across days and seeds.

## Evaluation and paper-claim review

### Paper weaknesses inherited or still unresolved

- **Selected-day bias.** The paper chose 9 November after observing chain switching. Temporal results from the same day are therefore descriptive case-study evidence, not general performance.
- **No training uncertainty.** Fifty replay repetitions reuse one fixed trained model. A fixed seed helps reproducibility but does not measure sensitivity to initialization or minibatch order.
- **No simple forecasting baseline.** "Forecast beats immediate execution" does not establish that the architecture predicts better than a simple policy.
- **Undefined error bars.** Figures show bars without defining SD, SEM, interval method, or independence unit.
- **Metric/claim mismatch.** Accuracy and total loss do not establish economic benefit. The economic figures are more relevant but one-day and timing-ambiguous.
- **Cost simplification.** Base fee per gas is acceptable for a within-chain base-component experiment with fixed gas, but it should not be called complete transaction cost. Priority fee and inclusion behavior remain assumptions.
- **Unsupported robustness claim.** The paper asserts that min-only prediction is safer than trajectory forecasting without evaluating the alternative.
- **Overstated consistency.** The paper itself reports a negative Transformer result on Avalanche/36s.

### Benign current refinements

- Packaged evaluation suites now cover many timestamp and block windows rather than only one day.
- Edge-case, fee-level, volatility, delay, lookback, priority-fee, and elapsed-position experiments exist as explicit benchmark candidates.
- External evaluation windows are guarded against training-cutoff overlap.
- Economic formulas and raw fee sums are executable and testable rather than figure-only prose.

These refinements do not validate prior results while the cross-layer decision contract remains unresolved. Window selection must also be frozen before final comparisons to prevent post-hoc benchmark selection.

## Shared contract required after route choice

This is a route-neutral checklist, not an approved design. It does not choose among preserving the forming-block route, redefining offset zero as an immediate action slot, or restoring paper-next-block semantics.

1. **Decision instant.** State whether `tau` is before a forming block, after a confirmed block, or an arbitrary request time.
2. **Information set.** Every input has an `available_at <= tau` proof for the relevant chain and fork; virtual/decision-time values are distinguished from finalized block fields.
3. **Action.** State whether class `k` selects a physical block, a broadcast time, or a wait slot.
4. **Outcome.** Map the action to an eligible inclusion block under an explicit inclusion assumption.
5. **Baseline and oracle.** Apply the same timing/inclusion rules to immediate execution and hindsight choice; define fee ties and latency preference.
6. **Constraint.** State whether max delay constrains broadcast or inclusion. Report violations separately.
7. **Training sample.** Inputs contain only facts available at `tau`; train/validation/test roles are assigned by cutoffs before labels, and each label horizon stays inside its role.
8. **Primary model selection.** Full-validation economic regret/savings under the same decision contract.
9. **Diagnostics.** Predictive loss and exact action accuracy explain behavior but do not override economics/safety.
10. **Final evidence.** Predeclared windows/days, a small seed set, paired model comparisons, and a frozen test surface.

One approved implementation of this contract would remove the current distinction between what a class means in training, replay, and serving. It may also allow one prediction head and substantially fewer metrics.

## Owner approval gates

Nothing below is decided by this report:

1. Which action route survives: preserve-and-reconcile block-open, redefine offset zero as an immediate action slot, paper-next-block, or another explicitly worked route?
2. If block-open survives, can each feature and `base_fee[h]` be computed before execution for every supported chain/fork, and can a request still target that forming block?
3. Does delay constrain broadcast time or achieved inclusion time?
4. Is inference allowed only at block boundaries, at a pre-inclusion instant, or at arbitrary request arrival times?
5. Which aggregate economic formula is primary: mean request percentage, ratio of fee sums, or an application-specific utility?
6. What penalty/fallback applies when inclusion misses the deadline?
7. Does the scalar fee prediction have a concrete consumer?
8. Are class weights justified by economics, or should classification be unweighted?
9. Is macro F1 needed for a stated thesis question?
10. What practical tolerance allows a simpler model to replace a more complex one?
11. Which feature groups survive causal/economic ablation?
12. Which training host is easier to understand after semantic prototypes: idiomatic Lightning or pure PyTorch?
13. Does bounded Optuna HPO remain, and if so which sampler, pruning policy, validation surface, budget, and preset-materialization rule are simplest and fair?
14. How many seeds and which predeclared days/windows are sufficient for the undergraduate thesis claim?
15. Should a 36s artifact be allowed to serve shorter requested waits, or must each supported horizon have its own trained artifact as in the paper experiments?

## Ticket-ready investigation additions

These are candidates for aggregation into the existing Wayfinder map, not automatically published or approved:

### Define the temporal decision clock and deadline

Type: grilling / owner decision.

Question: compare preserve-and-reconcile block-open, redefined immediate-action-slot, and paper-next-block routes with one worked example per chain; choose decision instant, broadcast versus inclusion deadline, first eligibility, baseline, tie rule, and deadline-miss behavior.

Blocks: every target, replay, serving, objective, and conversion decision.

### Prototype one shared action-outcome function

Type: prototype.

Question: can one compact function generate aligned labels, offline realized outcomes, and live response fields, including irregular cadence and post-deadline behavior?

Blocks: approved decision-clock contract.

### Prove purged internal split boundaries

Type: research/prototype.

Question: for each chain/horizon, do train outcomes end before validation decisions and validation outcomes before test decisions while retaining causal past context?

Blocks: shared action-outcome semantics.

### Compare lean prediction objectives

Type: research experiment.

Question: on frozen paired windows, compare unweighted classification, vector fee regression, current multitask loss, and only then a cost-sensitive surrogate; select by approved economic/safety metrics.

Blocks: decision clock, exact metric definitions, corrected split.

### Run the simple-model and feature-ablation ladder

Type: research experiment.

Question: what is the least complex feature/model combination practically indistinguishable from the best candidate across approved days and seeds?

Blocks: corrected target, split, objective, frozen evaluation protocol.

### Choose and prototype the lean training host

Type: prototype / owner decision.

Question: after the objective/head/metric gates, is idiomatic automatic Lightning or a direct PyTorch loop smaller and easier to teach while satisfying approved checkpoint, finite, and reproducibility semantics?

Blocks: objective/head decision and existing framework-semantics gates.

### Repair the intentional HPO extension

Type: prototype / owner decision.

Question: can bounded Optuna calibration use validation-only trials, common origins, corrected loss, a declared sampler/budget, and either real epoch pruning or `NopPruner`, while preserving its useful trial journal and explicit preset promotion?

Blocks: corrected split/loss, seed protocol, and training-host hook.

### Freeze the thesis uncertainty and reporting protocol

Type: grilling / owner decision.

Question: predeclare evaluation days/regimes, seed count, pairing unit, interval/statistic labels, and practical equivalence threshold before final model comparison.

Blocks: metric definitions and baseline ladder design.

## Sources

Primary project evidence is cited inline by file and line. Recovered local design evidence:

- Commit `e0b2e68e` (`fix(features): enforce safe current-row fee dynamics`).
- Current `PROGRESS.md`, especially the bounded-HPO policy at lines 135-153 and 215-226 and safe block-open rationale at lines 243-255.
- Current `ARCHIVE.md:9-36`, distinguishing the removed unsafe same-block route from the retained current-row route.
- Companion cross-check: `docs/research/issue-1/temporal-training-evaluation-theory-audit.md`.
- Chain/fork qualification: `docs/research/issue-1/temporal-chain-fee-protocol-audit.md`; no blanket cross-chain parent-determinism claim is made here.

External sources used for interpretation:

- Local foundation paper: `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`.
- Ethereum protocol: [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559).
- Polygon protocol: [Bor v2.6 mainnet fork config](https://github.com/0xPolygon/bor/blob/v2.6.0/params/config.go), [Bor v2.6 EIP-1559 verification](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go).
- Weighted classification reduction: [PyTorch `CrossEntropyLoss`](https://docs.pytorch.org/docs/2.13/generated/torch.nn.CrossEntropyLoss.html).
- Time-ordered split API and gap: [scikit-learn `TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
- Train-fit/transform normalization contract: [scikit-learn `StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
- Macro F1 API and exact union-active reduction: [TorchMetrics F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html), [TorchMetrics 1.9 source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93).
- Forecast-evaluation pitfalls and baseline guidance: [Hewamalage et al., *Forecast evaluation for data scientists*](https://doi.org/10.1007/s10618-022-00894-5).
- Large-scale forecasting benchmark evidence: [Makridakis, Spiliotis, and Assimakopoulos, M4](https://doi.org/10.1016/j.ijforecast.2019.04.014).
- Decision quality versus predictive error: [Mandi, Bucarey, and Guns, ICML 2022](https://proceedings.mlr.press/v162/mandi22a/mandi22a.pdf).
- Lightning's intended single-optimizer path: [Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html).
