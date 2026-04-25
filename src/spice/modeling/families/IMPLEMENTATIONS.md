# Concrete Model Families

Model families turn padded temporal input tensors into prediction heads. Current models are neural sequence encoders: they read rows of features over time and produce tensors consumed by a prediction family.

## Mental Model

A model does not know economic metrics. It maps sequences to output heads.

```text
inputs + input_mask
  -> sequence encoder
  -> final valid hidden state
  -> prediction heads
```

Prediction families define the head names and target losses. Model families provide the shared sequence representation.

## Shared Sequence Rule

All current families use the final real context row as the sample representation. Padding exists only to batch variable-length windows.

```text
input_mask:  true true true false false
last valid:             ^
```

This lets models ignore padded rows.

## `lstm`

The LSTM family uses an input projection, recurrent LSTM layers, and MLP prediction heads.

Why LSTM works here:

| Concept | Meaning |
| --- | --- |
| Hidden state | Carries information from earlier rows. |
| Gates | Learn what to keep or forget over time. |
| Final valid state | Summary of the observed context window. |

The implementation is CUDA-oriented and does not use compile-time graph capture.

## `transformer`

The Transformer family uses input projection, sinusoidal positional encoding, and a Transformer encoder with a padding mask.

Attention lets each row compare against other rows in the same context window. Positional encoding tells the model where a row sits in the sequence, because attention alone is order-insensitive.

Important constraints:

| Constraint | Why |
| --- | --- |
| `d_model` must be even | Sinusoidal position encoding uses paired dimensions. |
| `d_model` divisible by `nhead` | Multi-head attention splits hidden dimensions evenly. |
| Padding mask supplied | Attention must ignore padded rows. |

Large CUDA runs can use model compilation. Precision uses bf16 when supported, otherwise fp16 where configured.

## `transformer_lstm`

This family runs a Transformer encoder first, then an LSTM. The Transformer builds context-aware row embeddings; the LSTM aggregates them in temporal order.

```text
project inputs
  -> positional encoding
  -> transformer encoder
  -> LSTM
  -> final valid hidden state
  -> heads
```

This combines attention-based context mixing with recurrent sequence summarization.

## Output Heads

Model families do not hard-code economic targets. They ask the prediction contract for output specs and create one head per output. For example:

| Prediction family | Output heads |
| --- | --- |
| `candidate_offset_selection` | `candidate_logits` |
| `min_block_fee_multitask` | `min_block_offset_logits`, `min_block_log_fee` |

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Input width mismatch | Feature contract and model input dimension disagree. |
| Invalid Transformer dimensions | Attention/position encoding cannot be built. |
| Missing output head | Model does not satisfy prediction contract. |
| CUDA unavailable | Current training path cannot run. |

## Extension Pattern

A new model family should consume the same `ModelInputBatch` and emit the output heads requested by the prediction contract. Keep target economics in prediction families, not in model architecture code.

