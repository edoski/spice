# `candidate_offset_selection`

This prediction family trains a model to choose one candidate offset by minimizing expected fee cost. It is a direct policy over action slots.

## Mental Model

For each sample, the model scores every candidate offset:

```text
candidate logits
  -> masked softmax
  -> probability per offset
  -> expected relative fee cost
```

At inference time, the family chooses the highest-logit valid offset.

## Output Head

The model must emit:

| Head | Shape | Meaning |
| --- | --- | --- |
| `candidate_logits` | `[batch, max_candidate_slots]` | Unnormalized action scores. |

Logits are not probabilities. Softmax converts them into a probability distribution for the training loss.

## Target Batch

Targets come from the temporal realization policy:

| Field | Meaning |
| --- | --- |
| `candidate_log_fees` | Log fee consequence for each action slot. |
| `candidate_mask` | Action slots that can be resolved. |
| `optimum_offsets` | Best in-window candidate offset. |
| `optimum_log_fees` | Minimum log fee in the candidate window. |
| `baseline_candidate_indices` | Baseline offset, currently first candidate. |

Overflow slots use the post-window fee under `strict_deadline_miss`.

## Loss

The loss is expected relative fee cost, not cross entropy.

```text
policy = softmax(masked_logits)
relative_fee[action] = exp(candidate_log_fee[action] - baseline_log_fee)
loss = mean(sum(policy[action] * relative_fee[action]))
```

Lower is better. The model is rewarded for putting probability mass on cheaper fee outcomes.

## Beginner Theory: Policy Loss Versus Classification Loss

This family does not ask "which offset is the labeled class?" It asks "what fee would we expect if we sampled from the model's action distribution?" That is why it uses softmax probabilities and candidate fees directly.

```text
high probability on cheap actions -> lower expected cost
high probability on expensive actions -> higher expected cost
```

The baseline-relative fee makes examples comparable across fee regimes. Paying `20` instead of `10` is a 2x cost, while paying `110` instead of `100` is a 1.1x cost. Relative cost captures that distinction.

At decode time, the system does not sample. It chooses the highest-logit valid action with masked argmax so evaluation is deterministic.

## Metrics

Validation/test metrics decode the argmax offset and compare realized fee against baseline and optimum:

| Metric | Meaning |
| --- | --- |
| `profit_over_baseline` | Fractional savings against baseline. |
| `cost_over_optimum` | Extra cost above perfect in-window choice. |
| `total_loss` | Expected-cost loss. |
| `exact_optimum_hit_rate` | Fraction of samples where argmax equals optimum offset. |

Primary metric is profit over baseline, maximized.

## Decode

Decode applies masked argmax:

```text
candidate_logits + action_mask
  -> selected offset
  -> DecodedOffsets
```

The decoded offsets are then interpreted by evaluators through the realization policy.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Missing `candidate_logits` | Model does not satisfy output spec. |
| Invalid mask shape | Batch/action dimensions disagree. |
| Non-positive baseline fee after exponentiation | Economic ratio cannot be computed. |
| No valid action | Argmax and softmax are undefined. |
