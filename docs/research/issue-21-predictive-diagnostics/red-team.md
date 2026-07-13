# Issue 21 predictive-contract red-team

Date: 2026-07-12.

Status: independent planning evidence. This note changes no production code, test,
artifact, corpus, database, normative guide, or tracker state.

Owner override on 2026-07-12: every recommendation here for tie-aware or unique-action
predictive metrics, counters, denominators, null handling, and dedicated tests is
superseded. Issue 48's canonical resolution was corrected; retain only deterministic
earliest-label accuracy. Exact ties remain possible; raw-fee regret already handles a
later equal minimum. Add no tie-specific machinery or generic edge-case framework.

Owner override on 2026-07-12: Decision 5 retains exactly target-explicit Smooth-L1
loss plus target-explicit log-view MAE and MSE. Every native-unit regression MAE,
native reporting view, inverse provenance, and scoring-only inverse requirement in this
note is superseded.

Decision 6 is approved. Only complete-validation multitask total loss controls
checkpointing, early stopping, and representative HPO. Predictive diagnostics and
downstream economics cannot control them. Post-fit validation/testing reuse the
existing top-level evaluation path and one inference traversal, with separate
predictive and economic calculators. Issue 48's `K=5` leanness gate remains a separate
post-fit validation comparison.

Decision 8 is approved. One shared predictive-result context plus one task-specific
additive totals record is the only persisted predictive source of truth. All scalars
are derived; malformed input fails the whole predictive section with no partial,
nullable, repaired, converted, or generic-metric output.

Decision 9 is approved as a short reporting rule only. Context and additive totals
already carry every needed comparison boundary. Add no normalized/adjusted metric,
comparator mode, pooled result, plot subsystem, or extended thesis discussion; state
briefly that different `K` values define different class problems.

Decision 10 is approved. Replace the legacy predictive metric surface outright with
one concrete native-PyTorch task loss reducer, Decision 8's context/totals, and direct
TorchMetrics. Delete the enumerated custom counts, accumulators, predictive generic
metric hooks, duplicate scoring traversal, legacy ids, and obsolete compatibility tests;
leave shared last-consumer deletion to Issues 16, 18, 23, 47, and 48.

Issue 21 owns loss formulas, reducers, weights, scorer consumption, required predictive
records, and malformed-state behavior. Issue 58 now fixes the auxiliary target,
natural-log mapping, per-`(chain,K)` training z-score state, scalar output coordinate,
and affine log-reporting view. Issue 23 owns later task/head integration. Under approved Decision 6,
Issue 16 owns loss direction, improvement/min-delta/tie/patience, nonfinite fit response,
best-state semantics, and reproducibility. This review does not transfer or duplicate
those choices.

## Verdict

The emerging contract is directionally correct: deterministic earliest-label accuracy,
union-active macro-F1, additive full-map reducers, and strict state reuse. A later
focused audit and conditional owner approval supersede this pass's initial no-library
preference: direct TorchMetrics F1 plus per-class stats is lean and exact when kept as
fresh phase-local state. No tie-specific diagnostic remains.

Decisions 1–11 resolve the scorer/reducer defects from this pass. Issue 58 resolves the
former target-coordinate and naming dependency. Decision 11 deletes project
threshold/multiplier state in favor of one native standard Smooth-L1 operation and
one-copy composition. Only the complete-contract recap remains.

## Counterexamples

### Raw fees cannot be recovered from float32 logs

For `K=2`, take exact raw target fees:

```text
f = [1_000_000_001, 1_000_000_000]
```

The unique raw minimum is action `1`. Current SPICE converts both values through
float64 natural log and then stores float32:

```text
float32(log(f)) = [20.723267, 20.723267]
```

Current `np.argmin` therefore returns action `0`. A scorer using transformed equality
would also invent a two-action tie. This is not a rare one-wei edge: around this scale,
many adjacent integer fees share one float32 logarithm. The current conversion is in
[`features/core.py`](../../../src/spice/features/core.py#L299), and target `argmin` is in
[`batch.py`](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L13).

Exact fix: the scorer must consume the issue-23/temporal contract's lossless raw
chain-native target-fee matrix for the same `h+1...h+K` origins. Form tie sets with exact
raw equality before any transform. Do not reconstruct fees with `exp(float32_log)`, use
`isclose`, round, or derive labels from the auxiliary coordinate. This is a scorer input
requirement, not an issue-21 target definition.

### Current weighted CE changes with batch partition

Take labels `[0,0,0,1]`, per-origin NLLs `[0.1,0.2,0.3,0.4]`, and current weights
`[0.5,1.5]`.

```text
one batch:             weighted CE = 0.3000
batches [0,0],[0,1]:  current epoch CE = 0.2625
```

The examples and frozen predictions are identical. PyTorch's default weighted mean
divides each batch by that batch's target-weight sum; SPICE later multiplies by batch
sample count. The current audit gives the full derivation in
[`current-code-reducer-audit.md`](current-code-reducer-audit.md#hand-computable-partition-defect).

Accumulating the correct global weighted numerator and denominator repairs frozen-map
reporting, but not the composed optimization objective. With

```text
CE_b = sum(w[y_i] * nll_i) / sum(w[y_i])
total_b = CE_b + 0.5 * mean(reg_i)
```

the effective regression weight changes whenever a batch's class mix changes. That is
the same hidden coupling in a cleaner accumulator.

Recommended exact candidate semantics:

```text
unweighted: w_k = 1

weighted:   n_k = training target support for class k
            require n_k > 0 for every k in 0...K-1
            w_k = N_train / (K * n_k)

A_cls = sum_i w[y_i] * nll_i
D_cls = N_map
A_reg = sum_i smooth_l1_i
D_reg = N_map
L_total = (A_cls + A_reg) / N_map
```

The weighted training-map loss is then the unweighted mean of per-class mean NLLs, and
the mean training weight is exactly one. A minibatch optimizes
`mean(w[y] * nll + smooth_l1)`. The component balance no longer gains a hidden
batch target-weight denominator. Frozen scoring adds the same numerators and divides
once.

Do not preserve zero weights for training-absent classes. They ignore those validation
errors and can produce `NaN` on an all-unseen-class batch. The lean behavior is to mark
the weighted candidate invalid for that chain/K when any training support is zero;
unweighted CE remains defined. Smoothing or a made-up unseen-class weight would be a new
owner choice and more machinery.

This common-`N` recommendation is consequential. The alternative PyTorch target-weight
denominator is standards-supported, but it must be explicitly chosen with its varying
multitask balance consequence; it is not a harmless implementation detail.

### One-copy composition is a convention, not a balance claim

Smooth L1 with `beta=1` gives `rho(0.5)=0.125`; coordinate rescaling would change both
the loss value and gradient regime. Issue 58 now removes that ambiguity by fixing a
finite dimensionless training z-score separately per `(chain,K)`. The native standard
transition therefore means one fitted training-target standard deviation. Summing the
classification and regression numerators once adds no second arbitrary rescaling, but
does not establish equal task influence. The current `0.5`, the paper, and the reference repository do not settle them; the
regression theory report documents the evidence in
[`auxiliary-regression-theory.md`](auxiliary-regression-theory.md#recommendation).

### No nullable predictive metric remains

The owner reversal removed unique/tie-specific ratios. With required `N>0`, every
approved predictive scalar is defined. Do not add nullable metric machinery: malformed,
incomplete, or nonfinite scorer input fails the predictive result.

## Classification contract corrections

The recommended union-active macro-F1 is coherent, but its two universes must stay
explicit:

- validation universe: every label and prediction must be in `0...K-1`;
- scalar averaging set: classes with `target_support + prediction_count > 0`.

Absent-from-both classes remain in fixed-length support/provenance arrays with
`active=false`; they do not enter the macro scalar. Persist `K`, active-class count,
target support, prediction count, and true positives. This prevents a perfect scalar on
one active class from masquerading as evidence about all `K` actions. Fixed-universe
macro-F1, which assigns zero to absent-from-both classes, remains a real alternative and
needs an explicit owner rejection.

A full confusion matrix is not required. The complete approved classification suite is
recoverable from:

```text
target_support_by_k[K]
prediction_count_by_k[K]
true_positive_by_k[K]
N
earliest_label_hits
```

These additive integers produce earliest-label accuracy, union-active macro-F1, and
supports. A `K x K` matrix adds 40,000 cells at `K=200` and an unapproved
confusion-analysis surface. Keep it only if a later thesis question needs off-diagonal
pairs.

Issue 23 must choose the decoder's finite-logit, exact-shape, and equal-maximum rules;
Issue 21 only consumes a decoded action in `0...K-1`. Fixed-K eligible origins have all
`K` outcomes. As evidence for that upstream choice, current `masked_offset_logits` can
overwrite a nonfinite value in a masked slot and turn bad output into a plausible
action. Dynamic masks also belong to the retired variable-width and seconds-narrowing
contract. Delete the masking path only after issue 23 installs the fixed task interface;
do not preserve it as a compatibility option.

## Leakage, frozen scoring, and parity

- Fit class supports and any weights on retained training labels only, once per origin.
  Persist training supports separately from validation/testing supports.
- Consume Issue 58's frozen target state. Never refit or repair it on validation,
  testing, conversion, replay, or live data.
- Old artifacts lack class weights, target transform state, and target provenance.
  Decision 8 keeps them archival; never convert, backfill, or fit missing state from an
  evaluation range.
- Score each completed epoch only while its weights are frozen and the model is in
  evaluation mode. Training-batch values span changing parameters and are optimization
  telemetry, not artifact evidence. They should use separate `optimization_batch_*`
  names or remain logs.
- Recompute the complete predictive validation suite after issue 16 restores its chosen
  state, then compute sealed predictive testing once later. Under approved Decision 6,
  total loss alone is the selection input; Issue 16 owns only its direction,
  improvement mechanics, and fit-level response to scorer failure.
- Require scored-origin count to equal eligible-origin count. Never drop an invalid
  output, retry it as `k=0`, or condition offline metrics on serving success.
- Live serving consumes the action decoder, not the frozen-map scorer. The auxiliary
  scalar currently has no live consumer. Do not add a serving regression display,
  target-state registry, or live metric pipeline merely because the head remains.

One concrete task implementation should expose unreduced loss terms to fitting and its
complete-validation total-loss pass. After restoration/freeze, the existing post-fit
evaluator calls the concrete prediction scorer and separate temporal accounting over
one inference traversal. Standalone post-fit validation and sealed testing reuse that
same range-driven entry point. PyTorch supplies unreduced cross-entropy and Smooth L1.
Fresh direct `MulticlassF1Score` and
`MulticlassStatScores` objects supply standard macro-F1 evidence for each complete
phase, then are discarded. No scikit-learn scorer, custom F1 math, metric wrapper or
registry, exposed reset lifecycle, or loss protocol reduces total code.

## Malformed consumption boundary

Validate before counting or loss composition:

- nonempty origin set and exact origin identity/order;
- logits shape `[N,K]`, auxiliary output/target shape `[N]`, and no broadcasting;
- canonical earliest labels, decoded actions, and applicable training support vectors
  of exact width/range;
- all model outputs, target coordinates, log views, weights,
  per-origin losses, and floating totals finite;
- weights strictly positive when the weighted candidate is active;
- exact match among artifact, chain, K, the Issue-58 state references, locked native
  loss operation, loss state, and content-bound training provenance;
- Issue 58's state/view validator succeeds and every eligible origin is decoded.

Raw target fees belong to temporal economic accounting, not the predictive scorer.
Issue 21 requires Issue 58's state contract to validate; it does not reopen or repair
target-transform internals.

Fail with the field and origin. Do not broadcast, clamp, mask, sort, deduplicate, drop,
fill, add epsilon, set a scale to one, refit, substitute a different state, or fall back
to classification-only or partial predictive output. No approved metric has a valid
zero denominator or `null` result.

Use float64 floating numerators and integer denominators. This makes the mathematical
reducer independent of batch partition. Normal roundoff can differ across reduction
orders; issue 21 should not promise bitwise cross-device equality. Issue 16 owns the
reproducibility claim.

## Names and provenance

Delete ambiguous ids instead of aliasing them:

- `offset_accuracy` -> `earliest_hindsight_label_accuracy`;
- current `macro_f1` -> `earliest_hindsight_label_macro_f1` with the approved active rule;
- delete evaluator `exact_optimum_hit_rate`; retain only
  `earliest_hindsight_label_accuracy`;
- `regression_loss`, `log_fee_mae`, and `log_fee_mse` -> the three Issue-58-target-explicit
  ids fixed in Decision 5;
- `total_loss` -> one explicit multitask-objective id with its components and formula.

Issue 58 resolves the former placeholders as
`hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss` and its
`natural_log_mae/mse` companions. Add no aliases or runtime naming layer.

Put shared range/artifact/config/state provenance once in one
`PredictiveResultContext`. Store only additive/source facts in one task-specific
`PredictiveTotals`: classification and regression loss sums, two log-error sums,
earliest-correct count, three class-count vectors, and `N`. Derive all scalar outputs;
do not persist duplicate values, per-metric `N`/units/directions, active flags, or a
family of nested metric payloads. The current `MetricSet`/`MetricDescriptor` split gives
bare floats plus incomplete metadata; expanding it into a generic policy registry would
deepen the wrong abstraction.

## Comparability limits

- **Batches:** only additive frozen-map states combine. Never average scalar batch loss
  or F1.
- **K:** action universe, target set, chance level, supports, CE scale, regression
  target, and fitted state change. Common origins permit paired description, not ranking
  K by raw predictive losses or rates.
- **Chains:** report separately. Different supports, regimes, and fitted states prevent
  a universal predictive ranking.
- **Ranges:** compare only under the same declared origin population and frozen state.
  Full-range metrics do not become additive by averaging range scalars.
- **Seeds:** each seed is one fitted artifact on the same origins, not extra origins.
  Never pool count numerators across seeds. The approved initial sweep has one seed and
  no stability claim.
- **Phases:** optimization telemetry, frozen validation, and sealed testing are different
  evidence. A shared formula does not erase phase ownership.

## Clean deletion candidates

After the final owners resolve their seams, delete without shims:

- current target-supported `macro_f1_from_counts`, loss reconstruction by
  `batch_mean * batch_size`, and their private accumulator helpers;
- fixed-K `action_mask`, `masked_offset_logits`, and masked-argmax paths;
- ambiguous metric ids and old `exact_optimum_hit_rate` row-identity plumbing;
- internal-test `test_total_loss` / `training_test` storage and reporting surfaces already
  rejected by issue 47;
- duplicate fitting, standalone, conversion, and evaluator score reducers;
- scikit-learn retained solely for scoring, the custom F1 reducer, and any exposed
  TorchMetrics wrapper/lifecycle surface;
- one-family prediction registry/protocol/callable plumbing only through issue 23's
  eventual task-interface decision.

Do not delete the auxiliary head. Do not add compatibility aliases, a metric registry,
an absent-class policy mode, a loss-family registry, or transition tests.

## Resolved consequential choices

The complete-contract recap must preserve these resolved choices:

1. Union-active macro-F1 and its direct TorchMetrics implementation remain approved.
   The three-action-diagnostic direction is reversed and Issue 48 is corrected;
   earliest-label accuracy alone is approved. Consume Issue 23's eventual decoder rule
   without deciding it here.
2. The common-sample-denominator formulas are approved: unweighted is the lean default,
   while corrected inverse-frequency weighting remains only one bounded Issue-49-owned
   validation ablation at primary `K=5`. It is not a general mode matrix.
3. Smooth L1 and its one-origin-one-vote sample reducer are approved. Issue 58 now fixes
   the finite dimensionless train-standardized coordinate. Decision 11 uses native
   standard Smooth L1 without project `beta` state and sums each loss component once
   without a multiplier field. This is lean, not a balance claim.
4. The three target-explicit regression metrics are approved: Smooth-L1 loss, log-view
   MAE, and log-view MSE. No native MAE or scoring-only inverse requirement remains.
5. The corrected loss-only checkpoint/HPO boundary and one existing post-fit evaluator
   with separate predictive/economic calculations are approved. Leave only loss
   direction and checkpoint mechanics to issue 16.
6. Decision 7 retires the obsolete 648-window macro-F1 audit branch as archival and
   outside the thesis scope. Keep only focused clean-scorer cases and fresh post-fit
   validation/testing evidence.
