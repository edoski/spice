# Current predictive reducer and parity audit

Date: 2026-07-12. Audited revision: `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`.

Status: code, config, test, documentation, and live-ticket evidence for
[issue 21](https://github.com/edoski/spice/issues/21). This report makes no owner
choice. It changed no production code, test, config, artifact, corpus, database, ADR,
normative guide, or remote state.

Issue 21 owns loss, weighting, reducers, frozen-checkpoint scorer consumption, and
malformed scorer-state behavior. Issue 58 now fixes the auxiliary target,
natural-log/z-score state, scalar output coordinate, and affine log-reporting view;
Issue 23 owns later task/head integration. This audit records those as upstream inputs
without reopening them. Issue 47 owns input preprocessing and the three-role split.
Issue 48 already fixes exhaustive finite-census economics and the required predictive
suite. Issue 49 owns the ablation protocol.

## Verdict

The current fit and standalone in-process scorer share one accumulator, but weighted
classification loss is not a full-map reducer. PyTorch divides each batch by that
batch's target-weight sum; SPICE then multiplies the batch mean by sample count. The
reported classification and total losses change when identical frozen predictions are
partitioned differently. Validation checkpoint selection and HPO inherit the error.

Current accuracy is exact equality against the earliest minimum-fee label. Current
`macro_f1` is nonstandard: it drops every target-absent class, including a class with
false-positive predictions. Class supports exist transiently inside the accumulator but
are discarded. Tie-aware and unique-minimum diagnostics do not exist. Economic
`exact_optimum_hit_rate` compares row identity and is also not tie-aware.

The auxiliary target state lives only in the training process. Artifacts persist input
scaler state and model weights, but not target mean/std, class weights, target supports,
or target-transform provenance. Reloaded offline evaluation and live serving can decode
offsets but cannot reproduce frozen-checkpoint loss or regression diagnostics. Training
summaries persist only validation and internal-test total loss; benchmark conversion
keeps only internal-test total loss.

## Exact current contract

### Targets and fitted state

The feature layer converts base fee to float64, silently clamps values below `1`, takes
natural log, and stores float32 log fees
([feature series](../../../src/spice/features/core.py#L299-L324)). For each selected
origin, target materialization masks unreachable actions with infinity, applies
`np.argmin`, and takes the corresponding logged fee
([target materialization](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L13-L35)).
`np.argmin` therefore chooses the smallest offset among equal reachable logged fees.

Training-state fitting consumes the retained training origins once. Let `n_c` be the
number of training targets for class `c`, and let `C+` be the number of classes with
positive support. Current class weights are

```text
a = C+ / sum_{j:n_j>0}(1 / n_j)
w_c = a / n_c  when n_c > 0
w_c = 0        otherwise
```

The implementation is
[inverse-frequency fitting](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L214-L232).
The common multiplier `a` cancels from PyTorch's current weighted-mean CE, so it does
not normalize the current classification value or its gradient relative to regression.
It would become consequential under a different fixed denominator.

The same training targets fit scalar float32 `fee_mean` and population `fee_std`, then
silently add `1e-8`
([state fit](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py#L34-L51)).
The regression target is

```text
z_i = (ln_fee_i - fee_mean) / fee_std
```

Issue 47's approved population rule is met narrowly: each retained training origin
contributes its declared scalar target once. The state does not record population count,
content identity, units, dtype contract, class supports, or provenance. Persistence and
the exact transform remain issue-23 decisions.

### Batch and epoch loss

For sample `i`, let `ell_i` be negative log probability of its earliest-minimum class.
For batch `b`, PyTorch's current weighted CE is

```text
CE_b = sum_{i in b}(w[y_i] * ell_i) / sum_{i in b}(w[y_i])
```

because [`F.cross_entropy`](../../../src/spice/prediction/families/min_block_fee_multitask/loss.py#L24-L28)
uses its default `reduction="mean"`. Current regression uses default Smooth L1 with
`beta=1` and mean reduction over one scalar per example
([regression and composition](../../../src/spice/prediction/families/min_block_fee_multitask/loss.py#L29-L40)):

```text
R_b = sum_{i in b}(smooth_l1(pred_i, z_i; beta=1)) / n_b
T_b = CE_b + 0.5 * R_b
```

Each optimizer step backpropagates `T_b`. Class composition therefore changes the
normalization of each training gradient, not only reporting.

The accumulator reconstructs alleged sums as `n_b * batch_mean`, then divides every
loss by total sample count `N`
([batch totals](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L168-L207),
[finalization](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L235-L248)):

```text
CE_current = sum_b(n_b * CE_b) / N
R_current  = sum_b(n_b * R_b) / N
T_current  = sum_b(n_b * T_b) / N
```

`R_current` is correct for one scalar per origin. `CE_current` is not the full-set
weighted mean unless every batch has the same average target weight. `T_current`
inherits that defect. If class weights were removed, sample-count aggregation of
ordinary mean CE would be exact; no unweighted production/config path currently exists.

The log errors are additive and partition-invariant: predictions are inverted only from
z-score to natural-log fee, then absolute and squared errors are summed per batch and
divided by `N`
([log-error accumulation](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L185-L207),
[reduction](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L235-L248)).
There is no inverse to chain-native fee and no native-unit MAE. Raw integer fees are not
carried by the target batch, so exact native-unit scoring cannot be reconstructed from
the current float32 log target without upstream issue-23 work.

### Hand-computable partition defect

Take four frozen examples with labels `[0, 0, 0, 1]` and realizable per-sample NLLs
`[0.1, 0.2, 0.3, 0.4]`. Current inverse-frequency fitting gives weights
`[0.5, 1.5]`.

| Partition | Batch weighted means | Current epoch result |
|---|---:|---:|
| One batch of four | `(0.5*0.1 + 0.5*0.2 + 0.5*0.3 + 1.5*0.4) / 3 = 0.3000` | `0.3000` |
| Batches `[0,0]`, `[0,1]` | `0.1500`, `0.3750` | `(2*0.1500 + 2*0.3750)/4 = 0.2625` |

Identical examples and predictions therefore report either `0.3000` or `0.2625`.
With zero regression error, total loss differs by the same amount. A local PyTorch probe
reproduced both values.

The zero weights for training-absent classes add another failure. A validation example
whose class had no training support contributes zero numerator and zero denominator
weight when mixed with supported classes, so its CE error is ignored. A batch containing
only such targets returns `NaN`. The phase-level finite gate then stops or rejects the
run; the scorer does not fail at state validation with the class/support context.

## Current classification diagnostics

Truth and prediction both have an earliest-offset tie rule:

- Target `np.argmin` selects the first reachable fee minimum
  ([batch.py:21-30](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L21-L30)).
- Masked `torch.argmax` selects the first maximum logit
  ([outputs.py:24-39](../../../src/spice/prediction/families/min_block_fee_multitask/outputs.py#L24-L39));
  the focused test fixes this behavior
  ([test_decoded_offsets.py:41-60](../../../tests/prediction/test_decoded_offsets.py#L41-L60)).
- `offset_accuracy` is exact predicted-offset equality against that earliest target
  ([counts](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L23-L54),
  [reduction](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L235-L248)).

This matches Issue 48's required earliest-label accuracy in substance, but the id does
not say `earliest` and no target support is published.

Current macro-F1 loops over the action width but skips every class with
`target_count <= 0`
([macro reducer](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L76-L94)).
For `K=3`, targets `[0,0]`, and predictions `[0,1]`:

```text
current target-supported macro-F1 = 2/3
union-active macro-F1             = (2/3 + 0) / 2 = 1/3
fixed-universe K=3, zero=0        = (2/3 + 0 + 0) / 3 = 2/9
```

Thus current `macro_f1` is neither union-active nor a fixed-universe `0...K-1`
reducer. `true_positive_by_class`, `predicted_by_class`, and `target_by_class` are kept
transiently, but only the scalar F1 and accuracy leave the accumulator
([count state](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L15-L20),
[metric output](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L239-L248)).

No predictive tie-aware hit or unique-minimum diagnostic exists. The old evaluator's
`exact_optimum_hit_rate` compares realized row identity with the earliest `np.argmin`
row
([optimum](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L48-L56),
[row hit](../../../src/spice/evaluation/temporal_accounting.py#L102-L117)).
For fees `[10, 8, 8]` and prediction `k=2`, current earliest accuracy and exact-row hit
are both `0`, while raw-fee tie-aware hit is `1`; the origin is not unique. Issue 48's
closed resolution originally required new predictive counts. Edo later reversed that
direction and Issue 48's canonical resolution was corrected: retain only earliest-label
accuracy and delete `exact_optimum_hit_rate` rather than replacing it with tie-specific
machinery.

## Checkpoint and scorer flow

The fit host creates the same family accumulator for training and validation. It
backpropagates batch total loss, accumulates batch state, and finalizes once per phase
([Lightning training](../../../src/spice/modeling/lightning_module.py#L82-L125),
[validation](../../../src/spice/modeling/lightning_module.py#L127-L172)). Validation
batches are unshuffled, but their partition still comes from configured batch size
([training runtime](../../../src/spice/modeling/training_runtime.py#L47-L68)). Several
checked-in tuning spaces vary batch size, so HPO compares differently partitioned
objectives as well as different optimization trajectories
([example space](../../../src/spice/conf/tuning_space/lstm_large_capacity.yaml#L1-L10)).

Checkpoint selection is hard-coded to validation `total_loss`; it does not consume the
prediction contract's declared primary id or direction
([selection constant](../../../src/spice/modeling/_fit_policy.py#L15),
[comparison](../../../src/spice/modeling/_fit_policy.py#L199-L210)). A checkpoint is
replaced only when `current < best - min_delta`. `min_delta` therefore controls both
patience and which state is called best. A later raw minimum within `min_delta` is not
saved. The default is patience `20`, `min_delta=0.0001`
([training config](../../../src/spice/conf/training/default.yaml#L1-L12)). The selected
CPU clone is restored before returning
([best-state clone](../../../src/spice/modeling/_fit_policy.py#L101-L134),
[restore](../../../src/spice/modeling/training_runner.py#L113-L125)).

After fit, `score_prediction_metrics` runs the same target preparation, batch loss, and
accumulator over the restored checkpoint
([scorer](../../../src/spice/modeling/scoring.py#L88-L116)). Current persisted training
scores validation and an internal test suffix with the in-memory fitted state
([post-fit scoring](../../../src/spice/modeling/persisted_training.py#L93-L124)). Issue
47 has already approved deletion of that internal-test role; official Issue-48 testing
is the separate later artifact-evaluation path.

All finalized metrics, not only the selection metric, must be finite. A nonfinite phase
before any best state raises; after a best state it early-stops without recording the
bad epoch
([finite policy](../../../src/spice/modeling/_fit_policy.py#L72-L90)). Final in-process
validation/test scoring also applies an all-metric finite gate
([persisted gate](../../../src/spice/modeling/persisted_training.py#L122-L124)). The
scorer itself neither validates output finiteness before loss calculation nor validates
that returned metric ids match descriptors. By contrast, decoded inference rejects a
nonfinite tensor in any head, including the operationally unused regression head
([inference gate](../../../src/spice/modeling/scoring.py#L119-L158)).

## Persistence, conversion, and parity

The artifact manifest persists authored configs, input `ScalerStats`, feature and
temporal semantics, action width, and training metric descriptors
([manifest shape](../../../src/spice/modeling/results.py#L66-L132),
[construction](../../../src/spice/modeling/artifacts.py#L28-L59)). Model weights are
saved separately. `MinBlockFeeTrainingState` is not in either artifact payload
([artifact persistence](../../../src/spice/modeling/artifacts.py#L62-L102)). A loaded
artifact therefore cannot reproduce weighted loss, target-z inversion, or log errors.
Native-unit regression scoring was later removed from the required suite.

The training runtime summary stores only best epoch, validation total loss, and internal
test total loss
([summary shape](../../../src/spice/modeling/results.py#L135-L152),
[builder](../../../src/spice/modeling/results.py#L230-L248)). It discards validation and
test accuracy, macro-F1, component losses, log MAE/MSE, class supports, and every raw
numerator/denominator. Benchmark collection converts only internal-test total loss to a
`training_test` metric record
([record conversion](../../../src/spice/benchmarks/result_records.py#L101-L125)). The
result index has named columns for the discarded prediction metrics, but no current
producer supplies them through this path
([export columns](../../../src/spice/benchmarks/result_index.py#L29-L61)).
There is no production artifact-conversion scorer that reconstructs target state or
predictive numerators. Because those facts were never persisted, a clean conversion
cannot recover them from current weights and manifests; old artifacts remain archival
under Issue 46.

| Surface | Inputs/state available | Current predictive result | Parity finding |
|---|---|---|---|
| Training epoch | model, targets, fitted class/fee state | all seven current metrics | Shared accumulator; weighted loss partition-dependent |
| In-fit validation | same fitted state, ordered batches | all seven current metrics; selects checkpoint | Same formula; batch size still changes result |
| Final in-process validation | restored best model plus live training state | all seven, then only total persisted | Numerically same scorer when batch plan matches |
| Internal test | live training state | all seven, then only total persisted | Approved for deletion by Issue 47 |
| Reloaded offline evaluation | model, input scaler, decoded action state; no target state | old economic replay metrics only | Cannot produce required frozen predictive suite |
| Live serving | model, input scaler, decoded action state; no target state | selected offset only | Shares offset decode; regression output ignored but must be finite |
| Benchmark conversion | training summary plus evaluation summary | internal-test total plus economic metrics | Other predictive columns are unpopulated |

External evaluation loads the artifact, rebuilds inputs, and creates only an
`EvaluationScoringRuntimePlan` for decoded actions
([artifact inference](../../../src/spice/modeling/artifact_inference.py#L79-L192)). Live
serving calls the same `predict_decoded_result` and selects only `DecodedOffsets`
([serving decode](../../../src/spice/serving/inference.py#L63-L105)). The auxiliary
scalar is not exposed in the serving response
([response schema](../../../src/spice/serving/schemas.py#L26-L45)). Retaining the head
does not currently imply a live consumer.

## Malformed state and silent repairs

Current scorer-state checks are incomplete. `MinBlockFeeTrainingState` converts values
to CPU float32 and requires scalar mean/std plus `std > 0`, but does not require finite
mean/std, a finite nonnegative one-dimensional class-weight vector, exact width `K`,
positive support for validation labels, or provenance
([state validation](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L84-L145)).
`NaN` std passes the `<= 0` comparison; positive infinity also passes. No focused test
covers malformed state or an unseen validation class.

Silent-repair inventory, with owner boundary:

| Current behavior | Evidence | Owner consequence |
|---|---|---|
| Nonpositive raw fee becomes `1` before natural log | [`features/core.py:305-324`](../../../src/spice/features/core.py#L305-L324) | Issue 58 requires an exact positive raw target and no replacement; Issue 47 owns canonical input failure |
| Constant target fee gets `fee_std=1e-8` | [`__init__.py:44-50`](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py#L44-L50) | Issue 58 requires finite strictly positive population `sigma` and failure without epsilon |
| Training-absent class gets weight zero | [`metrics.py:223-232`](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L223-L232) | Issue 21 loss/scorer choice; currently ignores mixed validation examples or yields NaN |
| Input scaler stores/uses unit scale for constant or nonpositive scale | [`scaling.py:34-70`](../../../src/spice/temporal/input_normalization/scaling.py#L34-L70) | Issue 47 already approved strict project-owned replacement |
| Offline and live preparers sort and keep the first duplicate block | [`fixed_sequence_temporal.py:31-38`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L31-L38), [`serving/inference.py:201-208`](../../../src/spice/serving/inference.py#L201-L208) | Issue 47 already approved fail-closed canonical input |
| Native fee is approximated by exponentiating float32 log fee in old evaluation | [`temporal_accounting.py:91-99`](../../../src/spice/evaluation/temporal_accounting.py#L91-L99) | Issue 48 economics consumes raw integer fees; Issue 58 authorizes no exponential/native prediction decode |

## Comparability limits

- **Across batches:** current weighted classification and total losses are not comparable
  when batch partitions differ. This includes batch-size HPO and a different final
  scoring batch size.
- **Across K:** accuracy, fixed-universe macro-F1, class supports, class weights, chance
  behavior, and action difficulty all change with K. Loss ids contain no K; artifact
  action width supplies context only when retained with the value. Never rank K by an
  unqualified scalar. Issue 48 fixes common origins and descriptive per-K reporting, not
  cross-K metric equivalence.
- **Across chains:** target distributions and fitted transforms differ. Log errors and
  target coordinates remain chain/state-specific. Total loss
  combines per-artifact classification weights and target scaling. Issue 48 requires
  separate chain reports.
- **Across seeds:** formulas can match, but one seed is descriptive model evidence, not
  training-randomness stability. Issue 48 and Issue 49 already fix that claim boundary.
- **Across phases:** current in-process scorer can be shared, but persisted values omit
  phase, exact support, numerator, denominator, and fitted-state provenance. A bare
  `total_loss` or `macro_f1` is insufficient evidence.

Current training descriptors contain id, label, and role only; every direction is
`None`
([descriptor declarations](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L133-L165)).
`PredictionSemantics` separately persists one primary id and direction
([semantics](../../../src/spice/semantics.py#L43-L52)), while checkpoint code ignores
both. `MetricDescriptor` has no unit, phase, denominator, zero/tie rule, support, or
provenance fields
([metric ABI](../../../src/spice/metrics.py#L11-L37)).

## Lean clean-break candidates

Manual reference searches found these production consumers; no Vulture inference is
used here.

1. **Delete the current macro-F1 implementation, not only rename it.**
   `OffsetClassificationCounts`, tuple conversion/addition helpers, and
   `macro_f1_from_counts` are private to the one family accumulator
   ([metrics.py:15-105](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L15-L105)).
   Replace them with the approved direct TorchMetrics F1/statistics phase calls. Keep no
   alias that preserves target-supported semantics.
2. **Delete sample-count reconstruction of weighted batch means.**
   `_MinBlockFeeMetricTotals` and `compute_batch_loss_and_state` currently lose the CE
   numerator and weight denominator before accumulation
   ([metrics.py:108-207](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L108-L207)).
   A streaming scorer still earns one small accumulator, but it should carry exact
   additive numerators, denominators, supports, and per-class statistics.
3. **Do not preserve the current class-weight normalization as compatibility behavior.**
   Its common scale cancels under current weighted mean and becomes arbitrary under a
   new denominator. Edo approved unweighted CE as the lean default and retained weighted
   CE only for one bounded Issue-49 validation ablation. If weighted CE is not selected,
   delete class-weight fit/state entirely; if it is selected, implement only the
   approved weight and sample-denominator formula.
4. **Collapse duplicate checkpoint-selection metadata under approved Decision 6.**
   Selection is hard-coded to `total_loss`, while prediction contract/semantics also
   carry `primary_metric_id` and `direction`; the latter currently serve reporting and
   persistence, not selection
   ([contract](../../../src/spice/prediction/contracts.py#L105-L129),
   [reporting consumers](../../../src/spice/workflows/reporting.py#L284-L294)). A fixed
   checkpoint contract needs one owner, not a generic objective layer plus a hard-coded
   second truth. Decision 6 fixes complete-validation total
   loss as the only checkpoint/early-stop/representative-HPO input. Issue 16 retains
   only loss direction and improvement/min-delta/tie/patience/nonfinite/best-state/
   reproducibility mechanics. Predictive diagnostics and economic evaluation remain
   separate and cannot select the checkpoint.
5. **Delete the internal-test compatibility surface already rejected by Issue 47.**
   This includes `test_total_loss`, `training_test`, its codecs/inspection/reporting,
   and tests that only preserve that role. Replace it with the approved validation and
   official testing predictive records; do not migrate old summaries.
6. **Treat one-family generic prediction plumbing as Issue-23/architecture work.**
   `prediction.registry` dispatches one family
   ([registry](../../../src/spice/prediction/registry.py#L8-L37));
   `EpochMetricAccumulator` and multiple callable fields generalize one implementation
   ([contracts](../../../src/spice/prediction/contracts.py#L45-L76)). A direct task module
   can delete this registry/protocol surface if Issue 23's approved interface confirms
   one task. Issue 21 should not silently decide that interface.
7. **Apply Issue 47's already-approved scaler deletions separately.**
   scikit-learn is imported only by input scaling. `_train_scaler` and `_scale_store` are
   pass-through wrappers, and `context_row_multiplicities` is reduced immediately to
   `>0`
   ([builder wrappers](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L85-L95),
   [scale wrapper](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L236-L241),
   [covered rows](../../../src/spice/temporal/input_normalization/scaling.py#L51-L63)).
   Issue 47 already approved a small strict NumPy z-score scaler and deletion of
   scikit-learn, multiplicity plumbing, safe-scale repair, and unused modes.

PyTorch is already mandatory and supplies per-element or sum-reduced cross entropy and
Smooth L1. No new loss library is needed. This audit initially found three small
project-owned integer vectors leaner than relying on Lightning's undeclared transitive
TorchMetrics dependency. A later focused API audit and conditional owner approval
supersede that implementation preference: use fresh direct TorchMetrics F1 and
per-class-statistics objects, declare TorchMetrics directly, and expose no wrapper,
registry, reset interface, or custom F1 math. Do not retain scikit-learn solely for F1.

Three focused implementation tests would cover the deep contract without transition
tests: one partition-invariance fixture for every loss/error numerator and denominator;
one fixed-K absent-class fixture covering earliest accuracy, macro-F1, and supports; and
one artifact-reload scorer fixture covering strict malformed state, phase/provenance,
and the log reporting view. Existing single-batch tests
do not cover those boundaries
([current family tests](../../../tests/prediction/test_min_block_fee_multitask.py#L92-L301)).
