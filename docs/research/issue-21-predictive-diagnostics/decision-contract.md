# Issue 21 predictive diagnostics and loss contract

Date: 2026-07-12.

Status: complete after approved Decisions 1–11 and explicit approval of the compact
whole-contract recap. Issue 58 is closed/completed and its map pointer is live, so the
target-coordinate dependency is resolved. This file authorizes no production, test,
artifact, corpus, database, guide, or tracker change beyond Issue 21's approved
Wayfinder completion sequence.

## Ownership

- Issue 46 fixes the closed-parent, fixed-`K` action and earliest raw-fee minimum truth.
- Issue 48 fixes the exhaustive equal-weight population and required predictive suite.
- Issue 47 fixes training-only fitted populations and three chronological roles.
- Issue 58 fixes the auxiliary target identity, natural-log mapping, per-`(chain,K)`
  training-only z-score state, scalar output coordinate, and affine natural-log report
  decode. Its canonical resolution is
  https://github.com/edoski/spice/issues/58#issuecomment-4951832231.
- Issue 23 owns the later concrete head/task architecture and integration, including the
  classification action decoder. It does not reopen Issue 58's target semantics.
- Issue 16 owns checkpoint mechanics under Decision 6's approved loss-only input:
  loss direction, improvement/min-delta/tie/patience, nonfinite response, best-state
  semantics, and reproducibility. Predictive diagnostics and economic outputs cannot
  select a checkpoint, stop training, or control representative HPO.
- Issue 49 owns candidate comparison, seeds, budget, and which approved classification
  loss variant its ablation selects.

Issue 21 owns formulas, the classification class-weight candidates, fixed unit-sum loss
composition, additive reducers, scorer consumption checks, frozen-map records,
units/directions/phases, and its class-weight state.

## Owner decisions

### Decision 1 — union-active earliest-label macro-F1

**Status:** explicitly approved by Edo on 2026-07-12.

- Use conventional union-active `earliest_hindsight_label_macro_f1`.
- Validate the full class universe `k=0...K-1` and require positive `N`.
- Publish target support, prediction count, and true positives for every `k`.
- Average only classes appearing in targets or predictions.
- Target-only and prediction-only classes remain active with F1 `0`.
- Classes absent from both targets and predictions are excluded from the scalar mean.
- The zero-division value is `0`.

The direct-TorchMetrics implementation condition is also satisfied and approved. Use
fresh `MulticlassF1Score(num_classes=K, average="macro",
multidim_average="global", zero_division=0).set_dtype(torch.float64).to(device)` and
`MulticlassStatScores(num_classes=K, average=None,
multidim_average="global").to(device)` objects for each complete frozen scoring phase. Update both
for every batch, compute once after the phase, serialize ordinary results, then discard
them. `MulticlassStatScores` publishes `[TP, FP, TN, FN, support]` for each class, so
prediction count is `TP+FP`. Declare TorchMetrics directly if production imports it.
Keep no custom F1 math, minibatch-score averaging, wrapper hierarchy, metric registry,
reset interface, persisted metric state, or scikit-learn scoring path. Before updates,
SPICE—not TorchMetrics—must enforce equal nonempty one-dimensional integer tensors and
values in `0...K-1`; after compute, both support and prediction-count sums must equal
the scored `N`. Pass decoded integer actions, never logits. The focused comparison and
locked-version probes are in `torchmetrics-implementation-comparison.md`.

### Decision 2 — unweighted cross-entropy default and one bounded weighted ablation

**Status:** explicitly approved by Edo on 2026-07-12.

The lean canonical/default candidate is unweighted cross-entropy:

```text
w_k = 1
```

Retain inverse-frequency weighting only as one bounded validation ablation, not as an
inherited default or a general loss-mode matrix:

```text
n_k = training support for class k
require n_k > 0 for every k in 0...K-1
w_k = N_train / (K * n_k)
```

For either candidate, with per-origin natural-log cross-entropy NLL `a_i`:

```text
A_cls = sum_i w[y_i] * a_i
D_cls = N_map
L_cls = A_cls / N_map
```

Native PyTorch cross-entropy owns the loss. Use unreduced terms, sum them, and divide by
sample count; a training minibatch uses its sample count and a frozen map divides once
after all batches. Never use the default weighted-mean target-weight denominator. Fit
`n_k` only on canonical retained training origins and persist supports, mode, and
provenance. Do not smooth, clip, assign zero weights, or fall back. If any `n_k=0`, the
weighted ablation fails before fit; the unweighted candidate remains defined.

Issue 49 owns the comparison protocol/winner and Issue 50 owns execution. Their one
canonical complete experiment inventory—not this file—must contain exactly one bounded
CE-weighting entry: unweighted versus corrected inverse-frequency, primary `K=5`, LSTM,
Ethereum/Polygon/Avalanche, one fixed seed, identical origins and otherwise fixed
configuration, validation-only selection, and testing only after the winner is frozen.
Use Issue 48's narrow gate separately per chain/seed: prefer unweighted when captured
hindsight opportunity is within five absolute percentage points and harmful-action rate
does not increase. Do not repeat this comparison across the ten-`K` sweep, other
families, seeds, HPO, or testing, and create no ad hoc/Cartesian expansion.

The canonical Issue-49/50 inventory owns the entry's decision question, dependencies,
cell/artifact count, controls, gate, and execution order. Issue 21 retains only the loss
semantics and this handoff pointer. That order must finish bounded validation ablations
and any approved representative HPO, freeze the winning contract, then run the
ten-`K` LSTM sweep and final exhaustive testing. Never tune separately per `K` or use
testing to select.

### Decision 3 — native Smooth L1 with one-origin-one-vote reduction

**Status:** explicitly approved by Edo on 2026-07-12.

Retain native PyTorch Smooth L1 for the auxiliary regression loss. For the one scalar
`z` target and `zhat` output per origin supplied by Issue 58, require exact
equal one-dimensional shapes and finite values. Let `r_i` be the unreduced term from
the one concrete native operation fixed by Decision 11:

```text
A_reg = sum_i r_i
D_reg = N_map
L_reg = A_reg / N_map
```

A training minibatch sums its per-origin terms and divides by its sample count.
Frozen-map scoring accumulates the numerator and sample count across every batch in
float64, then divides once. This is one-origin-one-vote. Never average minibatch means,
broadcast shapes, mask origins, repair values, or use classification weights in the
regression denominator. Decision 11 fixes the exact formula and unit-sum composition;
Issue 58's coordinate must not be reopened or transferred here.

### Decision 4 — earliest-label-only diagnostic

**Status:** Edo explicitly reversed the prior three-diagnostic approval on 2026-07-12.
The original Issue-48 owner then corrected its canonical resolution in place; the live
Issue-21 body was also corrected and verified. This simplified direction is approved.

For every positive-`N` frozen validation/testing map, use the deterministic earliest
raw-integer argmin label and the Issue-23-decoded action:

```text
y_i = first argmin_k f_i[k]
p_i = Issue-23-decoded action, validated in 0...K-1

earliest_hindsight_label_accuracy
  H_earliest = sum_i 1[p_i = y_i]
  value      = H_earliest / N
```

Do not publish `tie_aware_fee_optimal_rate`, `unique_hindsight_action_accuracy`,
unique/tied counts or denominators, or any tie-specific predictive record. Add no tie
counters or dedicated tie tests. Do not claim exact ties are impossible. Ordinary
earliest argmin defines the class label; choosing a later equal minimum is a
classification miss while existing raw-fee economic regret remains zero automatically.

Derive `H_earliest` from the sum of TP already returned by the approved direct
`MulticlassStatScores` object. Add no second TorchMetrics accuracy object, confusion
matrix, generic wrapper, or stored prediction corpus.

The requested one-off Int64 check remains research evidence only. It created no
artifact or code and found rare exact ties on Avalanche, confirming why the contract
must not claim impossibility even though it adds no tie-specific machinery.

General rule: a negligible edge case already handled by standard deterministic
semantics earns no dedicated metric, mode, branch, or test unless it is materially
frequent, materially impactful, or correctness-critical. This is a direct simplicity
rule, not a generic edge-case policy framework. The stale `tie-aware hit` wording was
removed from the live Issue-21 question/body after the Issue-48 correction.

### Decision 5 — three target-explicit auxiliary regression metrics

**Status:** explicitly approved by Edo on 2026-07-12 after Issue 48's canonical
resolution was corrected and verified.

Issue 58 now supplies the exact target and two aligned views:

```text
target_id = hindsight_minimum_base_fee_per_gas_within_k
O_i        = min_k raw_integer_base_fee_i,k
ell_i      = ln(O_i / (1 native wei/gas))
z_i        = (ell_i - mu) / sigma
ellhat_i   = mu + sigma * zhat_i
```

Here float64 `mu` and population `sigma` are fitted once on retained training origins
for the exact `(chain,K)` artifact and then frozen. Issue 21 publishes exactly:

```text
hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss
  value = A_reg / N under Decision 3
  unit = dimensionless standardized-target loss

hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae
  A_log_abs = sum_i abs(ellhat_i - ell_i)
  value = A_log_abs / N
  unit = nat

hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse
  A_log_square = sum_i (ellhat_i - ell_i)^2
  value = A_log_square / N
  unit = nat^2
```

All three are minimized and use one-origin-one-vote. For each complete frozen
validation/testing map, require positive `N`, accumulate float64 numerators across every
batch, then divide once. Scored `N` must equal eligible `N`. Preserve the three source
numerators with exact `N` and range/artifact/state provenance. Their named outputs have
the declared units and minimize direction. Approved Decision 8 separately fixes the
lean concrete storage shape without changing Decision 5's metric formulas.

These are literal fields, not templates. Add no runtime registry, aliases, or
compatibility names such as bare `regression_loss`, `log_fee_mae`, or `log_fee_mse`.
Consume Issue 58's frozen state and affine log view. Missing, misordered, wrong-shaped,
nonfinite, domain-invalid, or provenance-mismatched facts fail the scoring call; never
refit, reconstruct, clip, round, repair, or drop an origin. Add no RMSE, MAPE, median
error, R-squared, regression TorchMetrics object, or metric framework.

There is no exponential/native-fee decode, native-unit regression MAE, native reporting
view, serving field, or action use. Raw integer outcomes already own economic accounting.

### Decision 6 — loss-only fitting and one existing post-fit evaluator

**Status:** explicitly approved by Edo on 2026-07-12 and confirmed without correction.

- Gradients optimize only the approved multitask total loss.
- Complete-validation total loss alone selects checkpoints, early stopping, and any
  representative HPO. No predictive diagnostic or economic metric controls them.
- Training remains outside `src/spice/evaluation` and uses the concrete task loss
  reducer.
- After the checkpoint is restored and frozen, keep and cleanly rebuild the existing
  `src/spice/evaluation` responsibility as one range-driven post-fit evaluator. Do not
  add a parallel evaluator module.
- Post-fit validation evidence and sealed testing use the same evaluator entry point;
  only the declared block range changes.
- The evaluator traverses model inference once and returns separate `predictive` and
  `economic` result sections. Internally it calls the concrete prediction-task scorer
  and temporal economic accounting. Their formulas and ownership remain separate.
- Serving performs inference only because future outcomes needed by either post-fit
  calculation are unavailable.
- Through each owning implementation inventory, make a clean break from Poisson/random
  replay, evaluator registries/config variants, old ambiguous metric names, and obsolete
  overflow/fallback machinery. Add no compatibility surface.
- Preserve the approved post-fit `K=5` validation leanness gate as separate frozen-model
  candidate-selection evidence. It is never a gradient, checkpoint, early-stopping, or
  HPO objective, and testing never selects.

### Decision 7 — retire the historical 648-window macro-F1 audit branch

**Status:** explicitly approved by Edo on 2026-07-12.

Retain approved union-active macro-F1 for every new clean fixed-`K` frozen checkpoint.
Treat the historical issues 4/9 648-window audit branch as archival and outside the
thesis-facing protocol. Preserve every old output unchanged. Do not rerun, backfill,
reconstruct, reinterpret, cache, or add compatibility aliases for retired artifacts,
and do not use them to validate the clean scorer.

Validate the clean scorer only with focused partition/absent-class behavior cases and
fresh post-fit validation/testing results. The original map owner has closed issues 4
and 9 as `not_planned`/out of thesis scope and added one linked map pointer. Issue 21
does not reinterpret those tickets or artifacts.

### Decision 8 — one lean atomic fresh-artifact predictive result

**Status:** explicitly approved by Edo on 2026-07-12.

For one restored/frozen clean artifact and one declared validation or testing range,
publish one complete predictive result or fail the predictive section.

`PredictiveResultContext` stores shared context once: role/range, chain, `K`,
eligible/scored `N`, corpus/artifact/checkpoint/seed/config identities, Issue-58
target/state/view references, the Issue-23 action-decoder reference, class-loss
mode/provenance. Existing artifact/config identity fixes the reviewed code/dependency
revision. Decision 11 adds no threshold or multiplier field.

`PredictiveTotals` stores `N` once plus only these additive/source facts:

```text
A_cls
A_reg
log_abs_error_sum
log_squared_error_sum
earliest_correct_count
target_support_by_k[K]
prediction_count_by_k[K]
true_positive_by_k[K]
N
```

Total, classification, and Smooth-L1 losses; earliest-label accuracy; union-active
macro-F1; and log MAE/MSE are deterministic properties or serialization output derived
from the context and totals. Do not persist duplicate scalar values that can disagree.
Units and directions come from fixed named-field and Issue-58 target/view semantics,
not repeated metric payloads or descriptors.

Publish only when the exact ordered origin set satisfies
`totals.N = scored_N = eligible_N > 0` and every required tensor, count, total, and
provenance fact validates and every derived scalar is finite. Otherwise fail with field
and origin context and publish no partial, nullable, or repaired predictive result.
Never broadcast, mask, clip, round, sort, deduplicate, drop, fill, refit, substitute
state, or fall back.

Score only fresh clean artifacts carrying the final required state. Retired artifacts
remain archival; do not convert or backfill them. The predictive scorer consumes model
outputs, canonical labels, decoded actions, and Issue-58-supplied target/log views. Raw
target fees remain sibling temporal-economic-accounting input and ownership.

Add no `MetricSet`/`MetricDescriptor`-style generic dictionary, metric registry,
nullable container, metric-specific wrapper hierarchy, formula strings, stored
prediction corpus, or repeated per-metric provenance.

### Decision 9 — lean predictive comparability rule

**Status:** explicitly approved by Edo on 2026-07-12.

This is a short interpretation/reporting rule backed only by Decision 8's context and
additive totals:

- Partitioning the same frozen artifact and exact declared range differently must leave
  integer totals exact and float64-derived values equal within the declared numerical
  tolerance. Merge source totals only; never average minibatch scalars or F1. A
  different training batch size is a different fitted configuration, not another
  partition of one result.
- Complete-validation total loss may compare checkpoints and representative-HPO
  candidates only with identical chain, `K`, validation origins, Issue-58
  target/state/view contract, class-loss mode, config identity, and native loss
  operation. Different weighted/unweighted objectives cannot be selected by raw total
  loss; Decision 2's separate frozen `K=5` validation gate owns that choice.
- Predictive `K` curves are descriptive. Different `K` values define different class
  problems and fitted targets/artifacts; do not use raw predictive scores to rank or
  select `K`. Add no normalization or chance correction, and make no strict monotonicity
  claim.
- Keep chains separate. Do not pool predictive totals, vectors, losses, or log errors
  into one chain score.
- One declared validation or testing range gets one result. Chunks of that same exact
  range may merge source totals under identical artifact/state and then rederive
  scalars. Never average range scalars, merge validation with testing, or let testing
  select.
- Each seed is a separate fitted artifact/result, not extra origins. Never sum
  per-origin totals/vectors across seeds. The approved one-seed sweep is descriptive and
  makes no stability claim; Issue 49 owns any later-approved model-replicate summary.
- Optimization telemetry, fitting-time complete-validation loss, post-fit validation,
  and sealed testing remain distinct facts.

Keep the thesis/report note brief: different `K` values define different class problems.
Add no adjusted metric, comparator mode, registry, pooled scorer, extra result record,
special plot machinery, or extended discussion. Issue 48 still owns economic
comparisons and Issue 49 owns candidate/seed aggregation.

### Decision 10 — clean scorer/loss deletion inventory

**Status:** explicitly approved by Edo on 2026-07-12.

Replace the current predictive metric framework with the already-approved direct
surfaces; do not migrate it:

- Delete `OffsetClassificationCounts`, its tuple/add/merge helpers,
  `macro_f1_from_counts`, `_MinBlockFeeMetricTotals`, `MinBlockFeeEpochAccumulator`,
  `_metric_set_from_totals`, `_add_metric_totals`, and their old tests. Fresh direct
  TorchMetrics plus Decision 8's `PredictiveTotals` replace them. Compute macro-F1 once
  from the complete phase through direct TorchMetrics and emit it as Decision 8's
  derived serialization/report output while the phase metric exists; add no custom
  count-to-F1 property or reload recomputation path.
- Split `compute_batch_loss_and_state`. Training computes only differentiable task loss
  and the additive component facts required for complete-validation total loss; it does
  not decode actions or compute diagnostics. Post-fit scoring alone builds
  `PredictiveTotals` and direct TorchMetrics state.
- Remove prediction-task uses of `MetricSet`, `MetricDescriptor`,
  `EpochMetricAccumulator`, `CreateEpochAccumulatorFn`, training metric descriptors,
  generic primary-metric ids/directions, and accumulator factory callables. Training
  keeps only its concrete task loss reducer and the complete-validation total needed by
  Issue 16; post-fit scoring returns Decision 8's two concrete records. Add no generic
  replacement.
- Delete the standalone `PredictionMetricScoringRuntimePlan` /
  `score_prediction_metrics` path. Decision 6 composes predictive scoring inside the
  existing post-fit evaluator's single inference traversal; a second prediction-only
  traversal no longer earns an interface.
- Delete every old predictive id/alias and its serializer/report/config/test surface:
  bare `total_loss`, `classification_loss`, `regression_loss`, `offset_accuracy`,
  `macro_f1`, `log_fee_mae`, and `log_fee_mse`. The final named fields and
  target-explicit report labels come from Decisions 1, 5, and 8; do not read or backfill
  old artifacts.
- Replace the current `compute_multitask_loss` implementation—default weighted-mean CE,
  implicit mean reductions, masked variable-width logits, and hard-coded `0.5`—with one
  concrete beginner-readable task loss reducer that directly calls native PyTorch under
  Decisions 2, 3, and 11. A single concrete function earns its existence; a loss
  registry/protocol/wrapper hierarchy does not. Issue 58 fixes target/state semantics;
  Issue 23 still owns concrete task/head integration, mask/decoder inputs, and final
  file layout.
- Delete the current `inverse_frequency_class_weights` formula in every outcome. If the
  bounded ablation selects unweighted CE, delete class-weight fit/state/persistence
  entirely. If it selects weighted CE, retain only the approved positive-support
  `N_train/(K*n_k)` facts and direct state—never the current zero-weight/renormalized
  helper or a mode framework.
- Within Issue 21's scorer/loss inventory, keep focused clean-contract behavior cases:
  the exact loss/reducer formula and partition-invariant source totals; earliest labels
  plus absent classes; and strict fresh-artifact reload/failure. Delete tests whose only
  purpose is old metric dictionaries, ids, accumulators, aliases, retired-artifact
  conversion, or transition compatibility. Other owners retain their own lean target,
  checkpoint, economic, and artifact tests.

Ownership limits remain explicit. Issue 21 adds no scikit-learn scoring use; Issue 47
owns the input-scaler/multiplicity deletion and any dependency removal. Issue 23 owns
fixed-`K` masking/decoder and one-family task-interface cleanup; Issue 58 owns target
state semantics. Issue 16
owns the minimal fit-loss carrier and checkpoint mechanics. Issue 48 owns deletion of
the remaining economic replay/metric consumers. Issue 18 owns the broader benchmark
runner/index cleanup, including old benchmark metric columns. Remove shared generic
types when their last owning consumer disappears; add no shim to keep them alive.

Declare `torchmetrics` directly. There is no scikit-learn scorer to preserve today;
scikit-learn's sole production import belongs to Issue 47's input-scaler inventory.
Keep the auxiliary regression head.

## Approved classification diagnostics

For `N > 0`, fixed `K`, exact raw target fees `f_i[k]`, earliest label
`y_i = min {k : f_i[k] = min_j f_i[j]}`, and the Issue-23-decoded action `p_i`:

```text
earliest_hindsight_label_accuracy = sum 1[p_i = y_i] / N
```

Empty maps and malformed inputs fail. The label is the ordinary deterministic earliest
raw-integer argmin; no tie-specific predictive metric is derived. Issue 21 validates
decoded actions against `0...K-1` but does not choose decoder behavior.

For macro-F1, publish three additive `K`-length integer vectors from the direct
TorchMetrics stats result:

```text
s_k = target support
q_k = prediction count
t_k = true positives
```

The approved scalar is union-active `earliest_hindsight_label_macro_f1`: average
`2*t_k/(s_k+q_k)` only where
`s_k+q_k>0`. Target-only and prediction-only classes are active with score zero;
absent-from-both classes stay in the arrays with `active=false` and do not enter the
scalar. Store `K`, all three vectors, sample count, and earliest hits. The active set is
derived from the vectors; do not persist redundant flags or counts. No full confusion
matrix is needed.

## Approved classification loss details

Issue 49 may compare the two approved formulas within Decision 2's bounded handoff. It
chooses the winner; Issue 21 chooses neither from validation evidence.
Let `a_i` be cross-entropy NLL in natural-log units for earliest label `y_i`.

Unweighted:

```text
w_k = 1
```

Corrected inverse-frequency weighted candidate, using retained training origins once:

```text
n_k = training support for class k
require n_k > 0 for every k in 0...K-1
w_k = N_train / (K * n_k)
```

For either candidate and every frozen map:

```text
A_cls = sum_i w[y_i] * a_i
D_cls = N
L_cls = A_cls / N
```

The weighted training-map value is the unweighted mean of per-class mean NLLs, and its
mean training weight is one. Use PyTorch unreduced cross-entropy and divide by sample
count. Do not use PyTorch's default target-weight denominator: within a multitask
minibatch it makes the effective regression weight vary with class composition. Never
set an absent class weight to zero, smooth counts, or fit weights outside training. A
zero-support weighted cell fails before fit; the unweighted candidate remains defined.

### Decision 11 — native Smooth L1 and unit-sum composition without project constants

**Status:** explicitly approved by Edo on 2026-07-12. The earlier proposal to
persist/configure `beta=1` and `lambda_reg=1` remains rejected.

Issue 58 supplies one scalar standardized target `z_i` and model output `zhat_i` per
origin, with `z_i=(ell_i-mu)/sigma` under the frozen per-`(chain,K)` training state. Use
one concrete native PyTorch operation:

```python
regression_terms = torch.nn.functional.smooth_l1_loss(
    zhat,
    z,
    reduction="none",
)
```

The native operation still mathematically fixes its transition at one standardized
target unit:

```text
e_i = zhat_i - z_i
rho(e_i) = 0.5 * e_i^2   when abs(e_i) < 1
           abs(e_i) - 0.5 otherwise

A_reg = sum_i rho(e_i)
L_reg = A_reg / N
A_total = A_cls + A_reg
L_total = A_total / N
```

Each approved component enters once. Remove `lambda_reg` entirely as a multiplier,
constant, field, validation rule, configuration/CLI option, HPO dimension, registry
entry, provenance value, or compatibility surface. Smooth L1's threshold has not
mathematically disappeared; it is fixed by this one native operation rather than
represented as project state. Remove project `beta` constants, fields, validation,
configuration, provenance, and compatibility surfaces as well.
`A_total` is a derived sum, not another persisted source field.

The lock resolves PyTorch 2.11.0 on the local platform and 2.7.1+cu118 on the Linux
x86 executor. The inspected 2.11 functional signature and documented API use
`beta=1.0` by default; 2.7 retains the same standard. Omitting the keyword is idiomatic
under these locked revisions and avoids duplicating the invariant. A literal
`beta=1.0` at the sole call would be marginally defensive against an unreviewed future
default change, but the lockfile, exact formula above, and focused behavior test are the
proper reproducibility boundary. The approved call omits the keyword; any dependency
update must revalidate the exact formula. The broad `torch>=2.5` declaration alone is
not that boundary; thesis runs must use the reviewed lock.

Add no `beta`/multiplier ablation, per-chain/`K`/seed override, scheduler, adaptive
weighting, dormant mode, or new inventory cell. This does not claim equal loss values,
gradients, or task influence. The approved sample-count reducers and loss-only
training/checkpoint/HPO boundary remain unchanged.

This decision removes the provisional future threshold/multiplier fields and equality
checks formerly mentioned in Decisions 8–10. Comparability instead requires the same
locked code/dependency loss operation plus the existing context. It changes no other
part of those decisions.

The required frozen regression records are:

```text
hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss = A_reg / N
hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae
  = sum abs(ellhat - ell) / N
hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse
  = sum square(ellhat - ell) / N
```

Decision 5 approves exactly these three target-explicit records. Issue 58 supplies the
frozen target coordinate and affine natural-log reporting view. Issue 21 requires no
native view or exponential inverse for scoring.

## Decision 6 implementation consequences

The approved Decision 6 creates five hard boundaries:

1. **Gradient objective:** training backpropagates only the approved multitask loss.
   Per-batch loss uses the approved local sample denominator. It never includes savings,
   regret, captured opportunity, harmful-action rate, accuracy, macro-F1, or log errors.
   Training stays outside `src/spice/evaluation` and calls only the prediction task's
   loss reducer.
2. **Checkpoint and representative HPO control:** every eligible frozen epoch is scored
   over the complete validation sample map. Checkpoint selection, early stopping, and
   any later-approved representative HPO consume only Decision 11's
   complete-validation multitask total loss. Accuracy, macro-F1, log MAE,
   log MSE, and every economic output are diagnostics and cannot select the epoch or HPO
   configuration. Issue 16 owns only the loss direction and checkpoint mechanics named
   in the ownership section.
3. **One existing post-fit entry point:** keep `src/spice/evaluation`'s responsibility.
   After the winning checkpoint is restored and frozen, its offline entry point accepts
   the artifact plus one declared
   validation or testing block range, traverses inference once, and returns two clearly
   separated result sections: `predictive` and `economic`. Post-fit validation and
   sealed testing use the same entry point; only the declared range changes.
4. **Two internal calculations:** the entry point calls the concrete prediction-task
   scorer for predictive totals from outputs, labels, target state, and log views. It
   calls concrete temporal accounting for economic totals from decoded actions and
   lossless raw target fees. They share origin identity,
   prepared batches, decoded actions, and one model-inference traversal, but do not
   merge formulas or ownership. Economic calculations never backpropagate, select an
   epoch, control early stopping, or change representative HPO.
5. **Serving:** live serving runs neither predictive reporting nor temporal economic
   evaluation because future outcomes are unavailable. It only performs the
   Issue-23-owned inference/decoding needed for the live action.

Issue 48's already-approved `K=5` leanness gate remains separate post-fit validation
evidence for model/feature simplification. Each candidate is first fitted, checkpointed,
and—where applicable—representatively tuned under loss-only control. The gate then
compares the candidates' frozen validation economic results on identical origins. It is
not a gradient term, checkpoint selector, or HPO objective, and testing never selects.
This statement does not reopen that gate.

The complete validation pass during fitting is a predictive loss pass over validation
samples, not temporal economic replay. Optimization-batch logs are omitted or named
`optimization_batch_*`; they are never frozen-map evidence. Never average minibatch
losses or diagnostics to produce a complete-map value.

The repository already has `src/spice/evaluation`, the top-level
`spice.workflows.evaluate` path, and the `modeling.scoring` inference bridge. Current
predictive totals live in
`prediction/families/min_block_fee_multitask/metrics.py`; current economic replay lives
in `evaluation/temporal_accounting.py`. Compose those responsibilities through one
clean post-fit path; do not add a second evaluator module or run the model twice. The
predictive calculator consumes:

- exact origin identities and exhaustive eligible count;
- Issue-23 classification outputs and decoded actions plus Issue-58 target state,
  scalar target/output, and log-reporting truth/prediction;
- deterministic earliest labels in the fixed `0...K-1` universe;
- Issue-21 class-weight mode and training supports/provenance.

It accumulates integer diagnostic counts plus float64 loss/error numerators, then divides
once after the complete map. Create fresh direct TorchMetrics and task-total state for
each complete predictive calculation. The sibling economic calculator receives the
same origins' decoded actions and raw fee facts from that traversal. Return one ordinary
post-fit result with separate predictive and economic sections. Add no duplicate
evaluator classes, metric registry, wrapper hierarchy, reset API, optional-mode
framework, stored prediction corpus, second inference pass, or scikit-learn path.

Clean-break `src/spice/evaluation`: through the relevant owning implementation
inventories, replace Poisson/random replay, evaluator registry/config variants, old
ambiguous profit/cost/metric names, overflow/fallback machinery, and indirect evaluator
contracts with the approved exhaustive per-origin implementation. Do not preserve
current class names, registries, Poisson configs, or compatibility surfaces. Retain the
module's responsibility and one post-fit interface, not its current implementation
shape.

Decision 7 retires the obsolete 648-window macro-F1 audit branch as archival and outside
the thesis scope. It measures retired artifacts and variable-window semantics, not the
required clean fixed-`K` scorer. Preserve those outputs unchanged and leave issues 4/9
closed `not_planned`/out of scope under their original map owner.

## Approved compact whole-contract recap

**Status:** explicitly approved by Edo on 2026-07-12 as the final Issue 21 contract;
Decisions 1–11 remain preserved exactly.

1. **Truth and upstream contracts.** For fixed `K`, classification truth is Issue 46's
   deterministic earliest raw-integer argmin. Issue 58 owns the auxiliary natural-log
   target, per-`(chain,K)` training-only population z-score state, scalar output
   coordinate, and affine natural-log reporting view. Consume Issue 23's eventual
   concrete head integration and action decoder without changing either upstream
   contract. Retain the auxiliary head. Add no tie-specific metric, native-fee inverse
   reporting requirement, serving regression output, or action use for the regression
   head.
2. **One exact training objective.** Native unreduced PyTorch cross-entropy supplies
   `A_cls`; unweighted CE is the default, while corrected positive-support
   `N_train/(K*n_k)` weighting is only the predeclared bounded validation ablation.
   Native `smooth_l1_loss(zhat, z, reduction="none")` supplies `A_reg` at its standard
   one-unit transition. There is no project threshold or regression multiplier state:
   `A_total=A_cls+A_reg` and `L_total=(A_cls+A_reg)/N`. Every component uses the sample
   denominator; never use weighted CE's target-weight denominator or average minibatch
   means into a frozen score.
3. **Loss-only fitting lifecycle.** Gradients, checkpoint selection, early stopping, and
   representative HPO consume only complete-validation total loss. Diagnostics and
   economic outputs control none of them. After restoration and freeze, the existing
   `src/spice/evaluation` responsibility performs one range-driven inference traversal
   and returns separate predictive and economic sections from two concrete
   calculations. Validation and sealed testing use that same entry point with different
   declared ranges; testing never selects. The separate frozen-model `K=5` validation
   leanness gate remains economic candidate evidence, not a fit/checkpoint/HPO
   objective. Serving performs inference/decoding only because outcomes are unavailable.
4. **Predictive records.** Publish earliest-label accuracy as direct
   `MulticlassStatScores` TP sum divided by `N`; publish no tie counters or alternate
   action accuracy. Publish union-active earliest-label macro-F1 over `0...K-1`:
   target-only and prediction-only classes are active with F1 zero, absent-from-both are
   excluded, and `zero_division=0`. Publish target support, prediction count, and TP for
   every class. Auxiliary reporting is exactly target-explicit Smooth-L1 loss,
   natural-log MAE, and natural-log MSE—no native MAE, inverse-only provenance, RMSE,
   MAPE, median, or R-squared.
5. **Complete-map arithmetic and failure.** For one frozen artifact and exact ordered
   range, accumulate integer counts and float64 source numerators across all batches,
   then divide once by `N`. Require exact shapes/class universe, finite required facts,
   complete provenance, and `totals.N=scored_N=eligible_N>0`. Any malformed, missing,
   misordered, incomplete, or nonfinite input fails the whole predictive section with
   context; publish no partial/null/repaired result.
6. **One lean result surface.** `PredictiveResultContext` carries shared range, chain,
   `K`, count, corpus/artifact/checkpoint/seed/config, Issue-58, decoder, and class-loss
   provenance once. `PredictiveTotals` carries only `N`, `A_cls`, `A_reg`, both log-error
   sums, earliest-correct count, and the three per-class vectors. Derive loss, accuracy,
   and log-error scalar serialization from those facts without persisting duplicate
   values. Direct fresh TorchMetrics computes and serializes phase macro-F1 once; retain
   its stats vectors, not metric state or custom count-to-F1 machinery. Declare
   TorchMetrics directly.
7. **Comparability and experiment order.** Merge only source totals for chunks of the
   same artifact/state/range. Objective comparisons require identical chain, `K`,
   origins, target state, loss mode, and config. Keep chains, ranges, lifecycle roles,
   and seeds separate. Different `K` values define different descriptive class
   problems; add no normalization or chance correction. Issues 49/50 own one bounded
   six-cell CE ablation (`K=5`, LSTM, three chains, one fixed seed, identical controls),
   then any approved representative HPO, then contract freeze, the ten-`K` sweep, and
   sealed exhaustive testing. Add no Cartesian expansion or per-`K` tuning.
8. **Clean break.** Replace the legacy predictive counts, accumulators, generic metric
   descriptors/sets/factories, standalone scoring traversal, old ids, invalid weighting,
   hard-coded `0.5`, and their obsolete focused tests with the concrete native loss
   reducer, `PredictiveResultContext`/`PredictiveTotals`, and direct TorchMetrics. Add no
   registry, wrapper hierarchy, compatibility alias, conversion, backfill, or stored
   prediction corpus. Historical 648-window outputs remain unchanged archival evidence;
   validate the clean scorer only with focused behavior cases and fresh post-fit data.

Ownership remains with Issues 16 (checkpoint mechanics), 23 (head/task integration and
decoder), 47 (populations/roles and input-scaler cleanup), 48 (economic accounting),
49/50 (ablation choice/execution), and 18 (broader benchmark cleanup). Issue 21 neither
duplicates nor silently changes those contracts. No owner gate remains.

## Evidence

- `classification-diagnostics-theory.md`
- `auxiliary-regression-theory.md`
- `current-code-reducer-audit.md`
- `red-team.md`
- `torchmetrics-implementation-comparison.md`
- `../auxiliary-fee-regression-head-conceptual-audit.md`
- `../issue-48-temporal-evaluation/decision-contract.md`
- `../issue-47-owner-decisions.md`
- `../issue-58-target-coordinate/decision-contract.md`
