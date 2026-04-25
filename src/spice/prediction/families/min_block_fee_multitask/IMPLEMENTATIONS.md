# `min_block_fee_multitask`

This prediction family trains two related tasks at once: classify the minimum-fee offset and regress the minimum log fee. Inference uses the offset classifier.

## Mental Model

The family asks the model to answer:

1. Which offset has the minimum block fee?
2. What is that minimum log fee value?

```text
sequence representation
  -> offset logits
  -> min-log-fee scalar
```

The scalar head gives an auxiliary training signal. The decoded action still comes from offset logits.

## Output Heads

| Head | Shape | Meaning |
| --- | --- | --- |
| `min_block_offset_logits` | `[batch, max_candidate_slots]` | Class scores for optimum offset. |
| `min_block_log_fee` | `[batch, 1]` | Predicted minimum log fee. |

## Target Batch

Targets include:

| Field | Meaning |
| --- | --- |
| `candidate_mask` | Valid resolvable action slots. |
| `min_block_offsets` | Class label for optimum offset. |
| `min_block_log_fees` | Regression target for minimum log fee. |

The optimum offset is the in-window minimum. Overflow slots remain selectable at decode time but the target class points to the best in-window row.

## Training State

The family computes training statistics:

| Statistic | Purpose |
| --- | --- |
| Inverse-frequency class weights | Balances rare optimum offsets in cross-entropy. |
| Fee mean and std | Normalizes the scalar fee regression target. |

Fee std has a small epsilon to avoid division by zero.

## Loss

The total loss combines classification and regression:

```text
classification = weighted_cross_entropy(offset_logits, target_offset)
regression = smooth_l1(normalized_predicted_fee, normalized_target_fee)
total_loss = classification + 0.5 * regression
```

The classification head chooses the action. The regression head helps the shared representation learn fee level.

## Metrics

| Metric | Meaning |
| --- | --- |
| `total_loss` | Combined training objective. |
| `offset_accuracy` | Fraction of samples with correct optimum offset. |
| `classification_loss` | Weighted cross-entropy component. |
| `regression_loss` | SmoothL1 component. |

Primary metric is `total_loss`, minimized.

## Decode

Decode ignores the scalar fee head:

```text
min_block_offset_logits + action_mask
  -> masked argmax
  -> DecodedOffsets
```

The evaluator receives only candidate offsets.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Missing output head | Model does not satisfy the multitask contract. |
| Invalid class target | Optimum offset outside head width. |
| No valid action | Masked argmax cannot choose. |
| Fee stats unavailable | Regression target cannot be normalized. |

