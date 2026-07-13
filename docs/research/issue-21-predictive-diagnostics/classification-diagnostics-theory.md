# Classification diagnostic theory for issue 21

**Status:** research input, captured 2026-07-12. This note does not approve an
owner choice or change executable behavior.

[Issue 46](https://github.com/edoski/spice/issues/46#issuecomment-4948024446)
fixes actions as `k=0,...,K-1`, targets as `h+1,...,h+K`, and training truth as
the earliest raw-fee minimum. The later
[Issue 48 resolution](https://github.com/edoski/spice/issues/48#issuecomment-4950650999)
makes macro-F1 part of the required frozen-checkpoint suite. Macro-F1 deletion
is therefore no longer an Issue-21 option, despite the older wording in
[Issue 21](https://github.com/edoski/spice/issues/21). Issue 21 still owns the
exact reducer.

## Owner reversal and canonical correction

Edo explicitly reversed the earlier three-action-diagnostic recommendation on
2026-07-12. The original Issue-48 owner corrected its closed canonical contract in place.
Retain only `earliest_hindsight_label_accuracy` plus the separately approved macro-F1.
All tie-aware/unique-action formulas below are superseded research reasoning, not an
active recommendation. Add no tie-specific metric, count, mode, branch, test, or
generic edge-case policy framework.

## Approved active contract

For an exhaustive map of `N > 0` eligible origins and a fixed `K > 0`, let
`f_i[k]` be the raw chain-native integer target base fee for action `k`. Define

```text
y_i = first argmin_k f_i[k]            # earliest-hindsight label
p_i in 0..K-1                           # decoded model action
```

The label uses ordinary deterministic argmin on raw integers before any logarithm,
target transform, floating conversion, or tolerance. The scorer accepts
`p_i` under Issue 23's canonical output/decoding contract; Issue 21 does not
choose logit shape, output validation, or equal-logit behavior. Current
`torch.argmax` and the paper-reference implementation both select the first
maximum ([PyTorch](https://docs.pytorch.org/docs/stable/generated/torch.argmax.html),
[reference code at pinned commit](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L504-L523)),
but that remains evidence for Issue 23 rather than an Issue-21 decision. The
scorer rejects decoded actions outside `0..K-1`, out-of-range labels,
incomplete fee vectors, and empty maps. It does not clamp, mask, drop, repair,
or return a plausible zero.

Use these metric ids and meanings:

| Metric id | Exact value | Unit / direction | Meaning and owner boundary |
| --- | --- | --- | --- |
| `earliest_hindsight_label_accuracy` | `sum_i 1[p_i=y_i] / N` | fraction / maximize | Exact earliest-label match and the sole action-accuracy view. |
| `earliest_hindsight_label_macro_f1` | conventional union-active macro-F1 below | fraction / maximize | Required secondary class-balance diagnostic. It uses earliest labels and ignores action order and fee magnitude. |

Do not emit a second `paper_accuracy` alias. Record
`comparison_role=paper_style_exact_label` as metadata on the first metric. The
paper says it reports block-offset classification accuracy and describes an
accurate choice as selecting the optimum-fee block (local foundation paper
`ICDCS_2026.pdf`, Sections VI-A and VI-C), while its reference code counts exact
label equality.
It does not specify equal-fee treatment. SPICE's earliest argmin rule comes from
Issue 46, and its fixed-block `K` task differs from the paper's time-window
task; “paper-style” is therefore a comparison role, not an identical estimand.

Do not claim exact ties are impossible. A later equal-minimum prediction is an
earliest-label classification miss; existing raw-fee economic regret remains zero
without another predictive metric. The one-off exact-Int64 check found rare Avalanche
ties but no material need for dedicated machinery.

## Exact macro-F1

The declared class universe is always `U_K={0,...,K-1}`. Validate both labels
against it and persist target support for every class:

```text
C[a,b] = sum_i 1[y_i=a and p_i=b]
s_k    = sum_b C[k,b]                  # target support
q_k    = sum_a C[a,k]                  # prediction count
t_k    = C[k,k]
d_k    = s_k + q_k                     # 2 TP + FP + FN
D      = {k in U_K : d_k > 0}          # union-active classes
F1_k   = 2 t_k / d_k                   # k in D
macro  = sum_{k in D} F1_k / abs(D)
```

`D` cannot be empty when `N > 0`. A target-only class and a prediction-only
class are both active and receive exact F1 `0` when they have no true
positives. A class absent from both target and prediction is inactive and does
not enter the scalar mean. If a per-class vector is exported, give that class
value `0`, support `0`, prediction count `0`, and `active=false`; the active
flag prevents the placeholder from being confused with an averaged value.

Edo approved this conventional union-active definition on 2026-07-12. Scikit-learn
1.8 defines macro averaging
as the unweighted mean over included labels, defaults those labels to the
sorted union of `y_true` and `y_pred`, and defines support as occurrences in
`y_true` ([`f1_score`](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.f1_score.html),
[`precision_recall_fscore_support`](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.precision_recall_fscore_support.html)).
TorchMetrics 1.9 also removes only classes with
`TP+FP+FN=0` from multiclass macro reduction; its tagged source sets their
averaging weight to zero
([`_adjust_weights_safe_divide`](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93)).

Set `zero_division=0` in any library reference call. Under union-active
reduction this controls per-class output/warnings; it does not add an
absent-from-both class to the scalar denominator. Do not use
`zero_division=np.nan`, because scikit-learn excludes NaNs from averages and
would introduce another version-sensitive rule. The official API documents
both behaviors
([scikit-learn 1.8](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.f1_score.html)).

An alternative, **not recommended**, is fixed-universe macro-F1:

```text
(1/K) * sum_{k in U_K} (0 if d_k=0 else 2*t_k/d_k)
```

Scikit-learn implements that alternative when called with
`labels=range(K), average="macro", zero_division=0`; its API explicitly allows
labels absent from the data and assigns them zero samples. It is a supported
metric, but it is not union-active. It assigns model failure to classes that
the finite map never asks the model to predict and causes values to shrink as
unused `K` classes are added. Choose it only through an explicit owner answer.

### Hand fixture and library check

Locked local versions were scikit-learn 1.8.0 and TorchMetrics 1.9.0. For
`K=3`, `y=[0,0]`, and `p=[0,1]`:

| Reducer | Value | Why |
| --- | ---: | --- |
| Current SPICE target-supported reducer | `2/3` | Incorrectly skips class 1 because its target support is zero. |
| Conventional union-active macro-F1 | `1/3` | Mean of class-0 F1 `2/3` and prediction-only class-1 F1 `0`; class 2 is inactive. |
| Fixed-universe macro-F1 | `2/9` | Mean of `2/3, 0, 0` over all three declared classes. |

For `y=p=[0,0]`, union-active macro-F1 is `1`; fixed-universe macro-F1 is
`1/3`. These fixtures recheck and refine the earlier audits: they correctly
identified current SPICE as nonstandard, but often treated “exact `K` class
universe” and “union-active denominator” as if they were the same choice.

## Earliest accuracy and supports

Scikit-learn defines normalized accuracy as the fraction of correctly
classified samples
([`accuracy_score`](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.accuracy_score.html)).
That matches the exact-label paper-reference code. The clean name retains
`earliest_hindsight` because it measures the deterministic earliest raw-integer argmin,
not generic economic optimality. A later equal-minimum action is a classification miss;
raw-fee regret already records zero economic gap without another metric.

Always export `support_by_k=[s_0,...,s_{K-1}]`. Also retain
`prediction_count_by_k` and `true_positive_by_k`; they are the minimal raw
facts needed to recompute F1 and detect prediction-only classes. Per-class
accuracy/recall, tolerance-within-`±k`, balanced accuracy, top-k accuracy, and
confusion plots are not part of the required suite. They add machinery without
answering a fixed thesis question. F1 itself contains no true-negative or fee
magnitude term, as is visible from the standard formula
`2TP/(2TP+FP+FN)` documented by scikit-learn.

## Full-map reduction and implementation choice

All classification facts are integer-additive. Each batch contributes three
`K`-length vectors—target support, prediction count, and true positives. Sum these states
over the complete map, then divide once. Never average per-minibatch F1. The sum of TP
provides earliest-label hits. Sample-weighted batch accuracy happens to equal the
full-map result, but using the same count path removes a needless special case.

The approved suite needs no off-diagonal confusion pairs. At the approved
maximum `K=200`, a full 40,000-cell confusion matrix would add an unapproved
analysis surface. A later focused audit established the lean approved surface:

- fresh direct `MulticlassF1Score` state supplies the union-active scalar;
- fresh direct `MulticlassStatScores(average=None)` state supplies TP, support,
  and prediction count for every class;
- both stream exact complete-phase state without retaining predictions; and
- ordinary results are serialized before the metric objects are discarded, so
  reset/distributed/state-persistence options do not enter SPICE's interface.

This conditional implementation choice was approved after locked TorchMetrics 1.9.0
probes confirmed the exact semantics. Declare TorchMetrics directly if production
imports it; do not rely on Lightning's transitive declaration. Do not retain
scikit-learn solely for scoring, implement custom F1 math, expose a metric-object
lifecycle, or add a wrapper/registry. The full comparison is in
[`torchmetrics-implementation-comparison.md`](torchmetrics-implementation-comparison.md).
The formulas and serialized raw counts, not an undocumented library default, remain the
durable contract.

During fitting, each eligible epoch gets only the correctly reduced
complete-validation multitask total loss. After Issue 16 restores and freezes the
winner, the existing post-fit evaluator scores this diagnostic reducer once over the
declared validation range and later through the same entry point over the sealed testing
range. Minibatch metrics produced while parameters change are optimization telemetry,
not frozen-checkpoint evidence. Issue 48 retains ownership of the exhaustive
eligible-origin population; Decision 6 fixes complete-validation total loss as the only
checkpoint/early-stop/representative-HPO input.

## Comparability limits

- **Across batches:** raw counts merge exactly. Scalar minibatch means are not
  comparable evidence and macro-F1 means are mathematically wrong.
- **Across `K`:** each `K` has a different class universe and label set, and an
  independently trained artifact. Common origins permit paired reporting, but
  accuracy and macro-F1 remain different tasks. Show descriptive `K` curves;
  do not rank horizons from their raw values.
- **Across chains:** report separately. Different class supports mix protocol dynamics
  with model behavior.
- **Across ranges/conditions:** compute the frozen full-range suite once. Issue
  48 permits the secondary condition view only at `K=5` and only earliest-label
  accuracy among predictive metrics; it does not authorize quartile macro-F1
  selection.
- **Across seeds:** a metric belongs to one fitted artifact and seed. Issue 48
  fixes one predeclared seed and explicitly makes no seed-robustness claim.
  If Issue 49 later approves a multi-seed comparison, keep its seeds paired and
  individually reported; never pool their origin counts as if repeated fits
  were extra observations.

## Clean deletion candidates

After the shared scorer replaces them, delete rather than alias:

- current target-supported `macro_f1_from_counts` and its bespoke
  `OffsetClassificationCounts`/merge surface, replaced by the approved direct
  TorchMetrics F1/statistics calls, in
  [`metrics.py`](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py);
- any proposed full confusion-matrix state unless a later thesis question
  explicitly needs off-diagonal pairs;
- the ambiguous `offset_accuracy` id, replaced by
  `earliest_hindsight_label_accuracy`;
- the old replay `exact_optimum_hit_rate`; retain only the clearly named
  `earliest_hindsight_label_accuracy`;
- duplicate standalone, conversion, and evaluator diagnostic accumulators once one
  concrete post-fit prediction scorer serves them; training keeps only the separate task
  loss reducer; and
- compatibility aliases for the old metric ids and formulas.

Keep no metric registry or configurable absent-class policy. One explicit
contract is enough.

The separate historical 648-window audit branch
([issues 4](https://github.com/edoski/spice/issues/4) and
[9](https://github.com/edoski/spice/issues/9)) is not needed for the required
new-protocol macro-F1. Existing collections contain only three artifact-level
old `macro_f1` values, not per-origin/per-class facts, and use obsolete
variable-window/action semantics
([frozen-evidence audit](../issue-1/clean-break-verification-semantics.md#historical-648-window-evidence),
[current evaluation audit](../issue-48-temporal-evaluation/current-code-and-frozen-evidence-audit.md)).
Re-running 648 archival windows would quantify the impact of correcting a retired
metric on retired artifacts; it would not validate the clean fixed-`K` scorer or support
the approved thesis estimand. Decision 7 therefore retires that branch as archival and
outside the thesis scope. Preserve the outputs unchanged, add no compatibility path,
and validate only with focused clean-scorer cases and fresh post-fit results.

## Resolved owner choices

The complete-contract recap must preserve these classification choices:

1. Union-active macro-F1 and its fresh direct TorchMetrics F1/statistics surface are
   approved.
2. Edo reversed the three-action-diagnostic direction and the Issue-48 owner corrected
   the canonical resolution. Earliest-label accuracy alone is approved. Output decoding
   remains an Issue-23 decision and is only consumed here.
3. Decision 7 retires the historical 648-window macro-F1 audit branch; required
   macro-F1 remains for clean fixed-`K` frozen checkpoints.
