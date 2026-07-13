# Issue 21 auxiliary-regression loss and scorer theory

Date: 2026-07-12

Status: bounded research evidence for issue 21. No production, test, artifact, or
tracker mutation is authorized here.

## Ownership boundary

Issue 58 now canonically fixes the target id, raw positive within-`K` minimum,
natural-log mapping, per-`(chain,K)` training-only float64 population z-score, scalar
model-output coordinate, persisted state, and affine natural-log reporting decode
([resolution](https://github.com/edoski/spice/issues/58#issuecomment-4951832231)). Issue
23 retains only the later concrete head/task architecture and integration. Its owner
comment also fixes that the auxiliary head remains
([owner constraint](https://github.com/edoski/spice/issues/23#issuecomment-4950344149)).

Issue 21 owns the regression loss family, exact reducer and composition, full-map
aggregation, required regression scorers, and the behavior when
the Issue-58 state cannot be consumed safely. Issue 48 fixes the required frozen-artifact
suite: target-explicit Smooth-L1 loss plus target-explicit log-view MAE/MSE, with no
native-unit regression MAE or inverse-reporting requirement
(`docs/research/issue-48-temporal-evaluation/decision-contract.md:139-165`). Issue 49 owns
seeds, budget, ablation candidates, and representative-HPO configurations, while
retaining the head. Issue 16 owns early-stopping mechanics under Decision 6's approved
complete-validation-total-loss-only input
([constraint](https://github.com/edoski/spice/issues/49#issuecomment-4950344147)).

Approved issue-47 facts that issue 21 must consume, not reopen, are:

- training alone owns fitted target statistics;
- target-transform statistics use each declared target element of each retained training
  origin once;
- the fitted state, population count/type, and content-bound training provenance are
  persisted and frozen for validation, testing, replay, and serving;
- validation selects the training-fitted checkpoint and testing never selects.

See `docs/research/issue-47/issue-47-owner-decisions.md:102-148`. Numeric role endpoints and
other still-pending issue-47 choices remain upstream.

## Approved owner contract

Edo approved native PyTorch Smooth L1 and the exact one-origin-one-vote/sample-count
reducer on 2026-07-12. Frozen-map scoring sums unreduced per-origin terms and divides
once by the complete scored-origin count; it never averages minibatch means. Issue 58
has now resolved the target coordinate. Edo approved the standard native operation and
one-copy composition without project threshold or multiplier fields. The earlier
stateful `beta=1`, `lambda_reg=1` proposal remains rejected.

Edo approved Decision 5 on 2026-07-12 after Issue 48 was corrected: auxiliary reporting
is exactly target-explicit Smooth-L1 loss, log-view MAE, and log-view MSE. All use
one-origin-one-vote complete-map reducers. Native-unit MAE, a native reporting view, and
inverse provenance are not required for scoring.

Issue 58 fixes:

```text
O_i      = min_k raw_integer_base_fee_i,k
ell_i    = ln(O_i / (1 native wei/gas))
z_i      = (ell_i - mu_chain,K) / sigma_chain,K
ellhat_i = mu_chain,K + sigma_chain,K * zhat_i
```

The approved lean representation is:

```text
regression_terms = torch.nn.functional.smooth_l1_loss(
    zhat,
    z,
    reduction="none",
)
A_total = A_cls + A_reg
L_total = A_total / N
```

The native functional API's standard/default transition is mathematically one
z-coordinate unit, so it still means one fitted training-target population standard
deviation. The contract removes project `beta` state; it does not claim the
transition disappeared. Likewise, summing `A_cls + A_reg` means each component enters
once. Remove the `lambda_reg` concept rather than persisting/configuring the number one.
This does **not** claim equal loss magnitude or gradient influence. Adaptive methods
such as uncertainty weighting and GradNorm exist precisely because unit composition
does not establish equal task influence
([Kendall et al. 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Kendall_Multi-Task_Learning_Using_CVPR_2018_paper.html),
[Chen et al. 2018](https://proceedings.mlr.press/v80/chen18a.html)). Those methods add
learned task state or another balancing objective/hyperparameter. Two tasks in a bounded
thesis do not justify that machinery without evidence.

The approved coordinate gives a useful scale check without pretending to prove task
balance. On the fitted training population, `mean(z)=0` and `mean(z^2)=1`. For a zero
auxiliary prediction and `beta=1`, PyTorch's formula satisfies
`rho_1(z) <= 0.5*z^2`, so the mean regression term is at most `0.5`. Uniform-logit
cross-entropy is `ln(K)`, at least `ln(2) ~= 0.693` on the approved grid. Also,
`abs(d rho_1 / d zhat) <= 1`, while each cross-entropy logit derivative is bounded by
one. Thus one-copy composition is not an obvious numerical blow-up, but these
head-output bounds do not establish equal shared-trunk gradients. They support the lean
no-extra-rescaling convention, not a balance claim or new ablation.

The approved Smooth L1 family is preferable to the nearby simple alternatives. PyTorch
defines a quadratic region near zero and an absolute-error tail with slope one; it is less sensitive to
outliers than MSE. The native standard transition at one is identical to Huber loss at
that threshold
([PyTorch 2.11 SmoothL1Loss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.SmoothL1Loss.html)).
Pure L1 removes `beta` but gives up the smooth region. MSE gives large residuals
quadratically increasing influence. Neither has evidence here sufficient to displace the
already coherent Smooth L1 family.

Omitting the explicit keyword is robust for the locked environment. The local PyTorch
2.11.0 signature is
`smooth_l1_loss(..., reduction="mean", beta=1.0)` and the official functional API
documents `1.0` as the default. The lock also resolves PyTorch 2.7.1+cu118 for Linux
x86, whose standard functional contract uses the same default. A literal `beta=1.0` at
the sole call would defend against a future unreviewed default change, but would duplicate
the invariant in project code. The lockfile, exact piecewise formula, and focused
behavior test are the cleaner reproducibility boundary. Use
`smooth_l1_loss(..., reduction="none")` with no project constant or keyword. Any lock
upgrade must revalidate the formula. The broad `torch>=2.5` declaration alone is not a
reproducibility guarantee; thesis runs must use the reviewed lock. A local float64
boundary fixture at residuals `[-2, -1, -0.5, 0, 0.5, 1, 2]` made the omitted-default,
explicit-`1.0`, and piecewise-formula values exactly equal, and made the omitted and
explicit gradients exactly equal under locked PyTorch 2.11.0.

The paper supports only the family, not these numerics. It names
`alpha * L_block + beta * L_fee`, inverse-frequency cross-entropy, and Smooth L1, but
does not state either coefficient, Smooth L1 threshold, reducer, target normalization,
or inverse (`/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`,
PDF p. 8). Visual and text inspection agree. The coherent paper-repository script sets
`alpha_block=1`, `beta_fee=0.5`, standardizes the log target, and constructs default
Smooth L1 (`/Users/edo/dev/python/ICDCS-Model-Training/train_model_classific.py:55-57,
189-215,563-566`). Older repository branches instead use `0.4/0.6` Smooth L1 or three
unit-weight losses with fee MSE
(`/Users/edo/dev/python/ICDCS-Model-Training/train_model.py:648-677`;
`train_model2.py:656-688`). The repository therefore supplies lineage, not a canonical
coefficient.

## Exact loss and reducers

Issue 58 supplies one target-coordinate scalar `z_i` and the model emits one scalar
`zhat_i` for every retained origin `i=1...N`. Require exact shape `(N,)` before calling
PyTorch; its functional implementation can broadcast mismatched shapes after warning,
which is unsafe for a scorer
([PyTorch 2.11 source](https://github.com/pytorch/pytorch/blob/v2.11.0/torch/nn/functional.py#L3647-L3705)).

The proposed native standard Smooth-L1 semantics are:

```text
e_i = zhat_i - z_i

rho(e_i) = 0.5 * e_i^2   if abs(e_i) < 1
           abs(e_i) - 0.5 otherwise

A_reg = sum_i rho(e_i)
D_reg = N
L_reg = A_reg / D_reg
```

This is PyTorch's documented unreduced Smooth L1 formula. Use
`torch.nn.functional.smooth_l1_loss(..., reduction="none")`; sum those terms
for the scorer and mean them for a minibatch optimization step. One scalar exists per
origin, so the regression denominator is the number of origins, not a batch count,
sequence length, K, fee magnitude, target variance, or sum of classification weights.

The independent red-team identified a tighter multitask contract: classification and
regression should share the sample denominator. Let the classification contract provide
`A_cls = sum_i w[y_i] * nll_i`, with unweighted `w=1` or train-normalized inverse
weights whose mean over training origins is one. The full frozen-map objective is:

```text
L_cls(map)   = A_cls / N
L_reg(map)   = A_reg / N
A_total(map) = A_cls + A_reg
L_total(map) = A_total / N
```

Accumulate `A_cls`, `A_reg`, and `N` separately over every batch, then divide and
compose once. Never average batch `L_reg`, `L_cls`, or `L_total` values. Use float64
score accumulators. The reducer is mathematically invariant to batch partition; normal
floating-point roundoff does not imply bitwise identity across different reduction
orders.

The optimization loss for a minibatch divides both local numerators by that batch's
sample count. This avoids PyTorch's target-weight batch denominator silently changing
the relative auxiliary coefficient with class composition. SGD updates still
necessarily depend on batch size, composition, order, and the
changing parameters. "Partition invariant" applies to a frozen model's validation or
testing score, not to the fitted parameter trajectory. Issue 48 already states that
training minibatch loss while weights change is operational progress, not a
frozen-checkpoint score (`decision-contract.md:147-154`).

### Rechecked current aggregation

Current SPICE calls default-mean weighted cross-entropy and default-mean scalar Smooth
L1, composes them with `0.5`, then multiplies every batch mean by batch sample count
(`src/spice/prediction/families/min_block_fee_multitask/loss.py:12-40`;
`metrics.py:168-207`). PyTorch's weighted cross-entropy mean uses a target-weight
denominator, so the classification and total-loss reducers depend on minibatch class
composition
([PyTorch 2.11 CrossEntropyLoss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.CrossEntropyLoss.html)).
The scalar Smooth L1 part alone is sample-correct because it has exactly one element per
origin.

A four-origin hand fixture under locked PyTorch 2.11 confirmed the distinction. Two
partitions of identical logits/targets produced current classification means
`0.9039263` and `1.3936275`; the regression mean was `1.375` under both. Global additive
reduction produced classification `1.3936274` and regression `1.375`. The fix is not a
special regression reducer. It is separate additive component totals followed by one
composition.

## Frozen-checkpoint scorer and selection boundary

Decision 6 is approved. It hard-constrains
checkpoint selection, early stopping, and any representative HPO to the correctly
reduced complete-validation `multitask_total_loss`; accuracy, macro-F1, log MAE/MSE,
and every economic result are diagnostics and cannot control them. Issue 16 retains
only loss direction, `min_delta`/tie/patience, nonfinite-run response, best-state, and
reproducibility mechanics under that approved loss-only boundary.

For each completed epoch `e`, reduce the predictive total loss over the same complete
Issue-47/49-approved validation origin map with that epoch's frozen model and the same
frozen Issue-58 state. Do not compute the full diagnostic/economic suite during fitting.
After Issue 21 fixes the representation, the selection total is:

```text
V_e = (A_cls,e + A_reg,e) / N_e
```

All loss terms must be finite before the predictive loss pass returns its total. A
nonfinite loss is a scorer failure with exact context; Issue 16 decides the fit-level
response. After Issue 16 selects and restores a state, recompute the complete predictive
validation suite and later the sealed predictive testing suite through the task scorer.
The fitting validation pass is not temporal economic replay.

Current SPICE uses the same `min_delta` test both to reset patience and to replace the
stored best state
(`src/spice/modeling/_fit_policy.py:92-134,199-210`), so it can retain an earlier epoch
even when a later epoch has lower loss by less than `min_delta`. That evidence is handed
to Issue 16; it is not resolved here.

Loss values select only within one fixed `(artifact configuration, chain, K, target
state, validation map)` run. Post-fit reporting reuses the existing
`src/spice/evaluation` responsibility and one inference traversal over a supplied block
range. Two internal calculators remain distinct: predictive totals consume
outputs/labels, while economic totals consume decoded actions/target fees. Economics
never backpropagates, selects an epoch, or controls HPO. Issue 48's `K=5` leanness gate
remains separate post-fit validation evidence for model/feature simplification: it
compares frozen candidates economically after each candidate has completed loss-only
fit/checkpoint/HPO control. Testing never selects.

## Required regression scorers

Issue 58 supplies the frozen affine natural-log view without refitting:

```text
ell_i    = ln(O_i / (1 native wei/gas))
ellhat_i = mu + sigma * zhat_i
```

Issue 21 defines:

```text
A_log_abs    = sum_i abs(ellhat_i - ell_i)
A_log_square = sum_i (ellhat_i - ell_i)^2

hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae = A_log_abs / N
hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse = A_log_square / N
```

The required metric surface is:

| Metric id | Unit | Direction | Required frozen phases |
| --- | --- | --- | --- |
| `multitask_total_loss` | composite loss coordinate; no physical unit | minimize | validation, testing |
| `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss` | dimensionless standardized-target loss | minimize | validation, testing |
| `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae` | nat | minimize | validation, testing |
| `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse` | nat² | minimize | validation, testing |

Online optimization telemetry must use an explicit `optimization_batch_*` name or be
omitted; it must not reuse frozen-map ids under a weak phase qualifier. The
classification-loss id belongs to the classification contract.
Issue 48 requires the wider suite full-range only, not condition plots
(`decision-contract.md:247-252`).

Decision 8 persists one shared context plus one `PredictiveTotals` source of truth with
`A_reg`, both log-error sums, and `N`; the named scalars are derived. The context carries
chain, `K`, range, artifact/checkpoint/seed/corpus identity, and Issue-58 state
provenance. The revised Decision-11 proposal removes provisional `beta`/multiplier
fields. `scored_N` must equal eligible `N>0`.

Do not preserve the current ambiguous ids `regression_loss`, `log_fee_mae`, and
`log_fee_mse`. Issue 58 fixes the exact target meaning; add no aliases or templates.

## Fail-closed consumption

Before loss or scoring, require:

- nonempty one-dimensional prediction and target tensors with identical shapes;
- one scalar per eligible origin and exact origin-order identity;
- finite predictions, targets, per-example losses, decoded log values, component
  numerators, and final metrics;
- present Issue-58 state with the expected target/transform id, chain, K, dtype, fitted
  population count, and content-bound training provenance;
- every fitted scalar finite and every scale strictly positive.

Any violation fails the whole phase with the failing field/origin. Do not broadcast,
clip, round, substitute, refit, add epsilon, set a zero scale to one, drop an origin,
`nan_to_num`, reuse a state from another K/chain, or fall back to classification-only.

Current state validation is insufficient. `MinBlockFeeTrainingState` checks only scalar
rank and `fee_std <= 0`; NaN means/scales and positive infinity pass, and the fitter adds
`1e-8` to every standard deviation
(`src/spice/prediction/families/min_block_fee_multitask/__init__.py:34-51`;
`batch.py:84-145`). Current predictive scoring does not validate finite output heads
before computing losses (`src/spice/modeling/scoring.py:88-116`); finite validation is
applied only to decoded action inference at `scoring.py:119-158`. Current fit policy can
turn nonfinite post-best metrics into early stop rather than failure
(`src/spice/modeling/_fit_policy.py:72-90`). None should survive as silent repair.

## Comparability limits

| Comparison | Valid interpretation |
| --- | --- |
| Different minibatch partitions | Same frozen-map formula and denominator. Expect numerical agreement within declared floating tolerance, not necessarily bitwise identity. |
| Different K | Do not compare total, classification, or regression loss as performance ranks. K changes task, class width/distribution, target minimum, and often fitted target state. Report each K separately. |
| Different chains | Losses and log errors remain separate chain facts; chain-specific target distributions/state prevent universal ranking. |
| Different named ranges | Comparable only when origin population and target state are intentionally the same; otherwise report provenance and avoid rank claims. |
| Different seeds | Compare only under identical chain, K, origins, configuration, and target state. Issue 49 owns seed count and any aggregation. The approved initial sweep has one seed and supports no seed-robustness claim. |
| Log error across units | Issue 58 fixes `ln(O/(1 native wei/gas))`; report each chain separately under its own fitted state and add no cross-chain normalized score. |

`multitask_total_loss` is a checkpoint coordinate, not a cross-K or cross-chain scientific
outcome. Even with one fixed operation/composition, cross-entropy changes with K and class
distribution, while a separately fitted target scale changes what one regression-loss
unit means.

## Smallest implementation surface

Use the lock-resolved PyTorch operation for unreduced Smooth L1. Use direct
tensor absolute/square sums and one small project-owned float64 totals record for
`A_reg`, `A_log_abs`, `A_log_square`, and `N`. No scikit-learn metric, TorchMetrics object,
registry, loss protocol, or adaptive multitask package reduces total code here.

Do not introduce `StandardScaler` for a one-scalar target state. The repository already
depends on scikit-learn 1.8, but its official contract treats NaNs as missing during fit
and assigns zero-variance inputs a scale of one
([official 1.8 docs](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html)).
Those defaults require extra fail-closed wrapping. Issue 58 already chooses one tiny
validated float64 scalar state, so a generic scaler adds machinery and conflicting
repair semantics.

Clean-break implementation candidates:

- fold the one-function `min_block_fee_multitask/loss.py` wrapper into the eventual
  issue-23 task module and call PyTorch's unreduced function directly;
- replace `_MinBlockFeeMetricTotals`/`MinBlockFeeEpochAccumulator` with one scorer totals
  structure that stores actual numerators and denominators rather than reconstructed
  `batch_mean * batch_size` values (`metrics.py:108-130,168-278`);
- delete `ResolvedMinBlockFeeTrainingState`'s legacy device-cache/state surface when
  Issue 23 integrates Issue 58's persisted validated target state; retain no
  compatibility reader;
- persist the full predictive suite and transform provenance. Current final artifacts
  persist model/input-scaler state but not fee-target state
  (`src/spice/modeling/artifacts.py:28-102`), and the training summary persists only best
  validation/test total loss (`src/spice/modeling/results.py:142-151`). A reloaded
  artifact therefore cannot reproduce current regression diagnostics.

The scalar head remains independent of action decoding. Current evaluation and serving
use only offset logits (`src/spice/prediction/families/min_block_fee_multitask/__init__.py:71-84`;
`src/spice/serving/inference.py:74-105`). Retaining and scoring the auxiliary head does
not authorize it to change an action or expose an actionable live fee estimate.

## Evidence conclusion

Rechecking the earlier auxiliary-head audit supports its reducer diagnosis. It does not
support inheriting the target transform or `0.5`. The paper leaves exact loss semantics
open; the reference repository contains conflicting choices; the historical
total-loss/economic A/B is incomplete; and TODO's “CLASS-ONLY (BETTER)” note plus later
retraining reminder (`/Users/edo/Documents/Obsidian/the-vault/notes/TODO.md:94-111,363-365`)
use superseded evidence and cannot reopen retained-head ownership.

The lean Issue-21 contract is therefore one native standard Smooth-L1 reducer, one-copy
classification-plus-regression composition, one full-map scorer, and strict failure.
Issue 58 resolves the former scale dependency; Decision 11 deletes project
`beta`/multiplier state while documenting the native transition.

## Primary sources

- SPICE professor paper:
  `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`, PDF pp. 5
  and 8.
- Paper-reference source:
  `/Users/edo/dev/python/ICDCS-Model-Training/train_model_classific.py:55-57,159-215,480-595`.
- [PyTorch 2.11 `SmoothL1Loss`](https://docs.pytorch.org/docs/2.11/generated/torch.nn.SmoothL1Loss.html),
  [`CrossEntropyLoss`](https://docs.pytorch.org/docs/2.11/generated/torch.nn.CrossEntropyLoss.html),
  [MSELoss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.MSELoss.html), and
  [L1Loss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.L1Loss.html).
- Alex Kendall, Yarin Gal, and Roberto Cipolla,
  [“Multi-Task Learning Using Uncertainty to Weigh Losses for Scene Geometry and Semantics”](https://openaccess.thecvf.com/content_cvpr_2018/html/Kendall_Multi-Task_Learning_Using_CVPR_2018_paper.html),
  CVPR 2018.
- Zhao Chen et al.,
  [“GradNorm: Gradient Normalization for Adaptive Loss Balancing in Deep Multitask Networks”](https://proceedings.mlr.press/v80/chen18a.html),
  ICML 2018.
- [scikit-learn 1.8 `StandardScaler`](https://scikit-learn.org/1.8/modules/generated/sklearn.preprocessing.StandardScaler.html).
- [NumPy 2.4 `log`](https://numpy.org/doc/2.4/reference/generated/numpy.log.html),
  [`log1p`](https://numpy.org/doc/2.4/reference/generated/numpy.log1p.html), and
  [`expm1`](https://numpy.org/doc/2.4/reference/generated/numpy.expm1.html).
