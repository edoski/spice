# TorchMetrics implementation comparison for Issue 21

Date: 2026-07-12.

Status: focused primary-source/API audit. It changes no production code, dependency,
test, artifact, or tracker state.

## Conclusion

The conditional direct-TorchMetrics approval is satisfied. The smallest approved
standard-metric surface is two fresh official objects per frozen scoring phase:

```python
f1 = MulticlassF1Score(
    num_classes=K,
    average="macro",
    multidim_average="global",
    zero_division=0,
).set_dtype(torch.float64).to(device)

stats = MulticlassStatScores(
    num_classes=K,
    average=None,
    multidim_average="global",
).to(device)
```

Pass canonical decoded integer actions and integer earliest labels to both objects.
Call `.update()` on every batch and `.compute()` once after the complete phase. Never
call the objects for batch scores and never average minibatch F1. Discard both objects
after ordinary result serialization; do not persist or reuse their state, build a
wrapper, expose reset/distributed options, or add a registry.

`MulticlassF1Score` supplies the approved scalar without project-owned F1 math.
`MulticlassStatScores(average=None)` supplies a public `K x 5` tensor ordered
`[TP, FP, TN, FN, support]`; serialize:

```text
true_positive_by_k   = stats[:, 0]
prediction_count_by_k = stats[:, 0] + stats[:, 1]
target_support_by_k  = stats[:, 4]
```

The two objects duplicate a bounded amount of integer count state, but that is smaller
total conceptual cost under Edo's mature-API preference than reimplementing and testing
union-active F1. At `K=200`, the duplicate O(K) states are negligible. A full
`MulticlassConfusionMatrix` adds K-squared state that the approved suite does not need.

Declare TorchMetrics directly if production imports it, for example
`torchmetrics>=1.9,<2`. The lock currently resolves `1.9.0` transitively through
Lightning `2.6.5`; a direct declaration installs no new distribution today but makes
ownership explicit.

## Exact approved semantics

Installed versions are PyTorch `2.11.0`, TorchMetrics `1.9.0`, and scikit-learn
`1.8.0`.

TorchMetrics computes per-class F1 from TP/FP/FN and, for multiclass macro reduction,
sets the averaging weight to zero only where `TP+FP+FN==0`. Therefore:

- target-only and prediction-only classes stay active and score zero when TP is zero;
- classes absent from both are excluded from the scalar mean;
- `zero_division=0` supplies the approved per-class zero;
- `num_classes=K` retains the fixed validation universe without forcing absent-from-both
  classes into the average.

This is visible in the official
[`_fbeta_reduce`](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/functional/classification/f_beta.py#L37-L58)
and
[`_adjust_weights_safe_divide`](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93)
source. The public APIs are documented by
[`MulticlassF1Score`](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)
and
[`MulticlassStatScores`](https://lightning.ai/docs/torchmetrics/stable/classification/stat_scores.html).

Locked probes confirmed:

```text
K=3, target=[0,0], prediction=[0,1]
one complete update:  macro F1 = 1/3
two batch updates:    macro F1 = 1/3
mean batch F1:        1/2  # wrong and forbidden

stats:
class 0 [TP=1, FP=0, TN=0, FN=1, support=2]
class 1 [TP=0, FP=1, TN=1, FN=0, support=0]
class 2 [TP=0, FP=0, TN=2, FN=0, support=0]
```

For `target=prediction=[0,0]`, TorchMetrics returns macro F1 `1`, not fixed-universe
`1/3`. This proves absent-from-both classes are inactive.

## State, device, reset, and distributed behavior

TorchMetrics `Metric` owns device transfer, state synchronization, and reset. Its
official base-class source documents `.to(device)`, `sync_on_compute=True`,
`dist_sync_on_step=False`, and `.reset()`
([Metric source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/metric.py#L52-L84),
[reset/device source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/metric.py#L758-L885)).

For the approved single-device thesis route:

- create both metrics fresh for each post-fit validation or sealed-testing predictive
  calculation after the winning checkpoint is restored and frozen;
- move them once to the decoded integer tensors' device;
- update them over the entire phase and compute once;
- discard them, so no reset rule enters SPICE's interface;
- serialize only the computed scalar and count arrays;
- keep `MulticlassStatScores` integer states as the exact audit authority;
- use public `set_dtype(torch.float64)` on the F1 object if a float64 scalar is wanted;
  `.double()` is intentionally a no-op in TorchMetrics.

Default distributed synchronization is inert without an initialized process group.
No DDP configuration or wrapper belongs in this single-device contract. Metric states
are not checkpoint-persistent by default, which is correct: a frozen checkpoint is
rescored from fresh state.

## Mandatory boundary validation

TorchMetrics `validate_args=True` is not the SPICE domain boundary. Version-1.9 probes
showed that some out-of-range or negative integer values can be mis-binned rather than
rejected, and floats can be coerced. The official validation/update implementation is
in the
[`MulticlassStatScores` source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/classification/stat_scores.py#L308-L352)
and functional
[`multiclass_stat_scores`](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/functional/classification/stat_scores.py#L483-L594).

Before either metric receives a batch, the task scorer must require:

- positive declared full-phase `N` and nonempty batches;
- integer one-dimensional target and decoded-action tensors with equal shape;
- every value inside `0...K-1`;
- the same fixed K and origin ordering across the phase;
- final target-support sum and prediction-count sum both equal scored `N`.

Pass decoded integer actions, not raw logits. TorchMetrics accepts float logits and
would run `argmax`, silently taking ownership of Issue 23's decoder/tie rule.

## Alternatives

| Route | Exactness | Total cost |
| --- | --- | --- |
| Direct F1 + StatScores | Matches approved union-active scalar; exact int64 per-class evidence; phase state is additive | Two obvious official objects and one direct dependency; no custom F1 math, wrapper, registry, reset interface, or stored prediction arrays |
| Tiny project count reducer | Three `bincount` vectors can produce every required count | No new dependency, but SPICE owns union-active F1 arithmetic, device/state aggregation, and more behavioral tests; rejected under the explicit mature-API preference once the direct route proved exact |
| scikit-learn offline | Default inferred-label `f1_score` is union-active | Stateless CPU interface; must retain/concatenate all observations or separately accumulate counts; needs another API for audit fields; retaining it solely for scoring also retains SciPy/Joblib/threadpool machinery |

Scikit-learn's official
[`f1_score`](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.f1_score.html)
uses the sorted target/prediction union when `labels=None`. Passing `labels=range(K)`
instead implements the rejected fixed-universe scalar. Its
[`confusion_matrix`](https://scikit-learn.org/1.8/modules/generated/sklearn.metrics.confusion_matrix.html)
can supply counts but silently excludes out-of-label observations unless SPICE validates
first. It adds a separate CPU scoring path and does not support phase-state updates.

## Lean implementation checks

Keep only focused behavioral fixtures:

1. approved prediction-only/absent-from-both example and exact per-class stats;
2. one-batch versus multi-batch updates producing the same complete-phase scalar/counts;
3. positive-N, dtype, range, and final-count boundary rejection;
4. same-device update and float64 F1 serialization.

Do not add transition tests for the retired target-supported reducer or an abstraction
around TorchMetrics.
