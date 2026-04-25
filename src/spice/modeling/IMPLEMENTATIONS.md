# Concrete Modeling Runtime

The modeling runtime builds datasets, trains CUDA neural networks, decodes predictions, runs evaluation objectives, persists artifacts, and tunes hyperparameters.

## Mental Model

SPICE trains a model to choose a candidate offset for each temporal sample.

```text
corpus rows
  -> feature matrix
  -> temporal problem store
  -> dataset builder
  -> model batches
  -> prediction contract
  -> loss/metrics
  -> artifact manifest + model.pt
```

The artifact manifest records exact configs, semantic fingerprints, scaler, dataset-builder metadata, model metadata, and training/evaluation results.

## Training Context

Training starts by compiling all contracts:

```text
feature_set config      -> feature contract
problem config          -> temporal problem contract
prediction config       -> prediction contract
objective config        -> objective contract
dataset_builder config  -> dataset builder contract
input_normalization     -> scaler policy
model config            -> model family
```

The compiled context is the source of truth for model input width, prediction output heads, action-space size, target batches, and objective metric direction.

## Batch Source

The sequence representation builds tensors:

| Tensor | Shape | Meaning |
| --- | --- | --- |
| `inputs` | `[batch, max_context, features]` | Padded feature windows. |
| `input_mask` | `[batch, max_context]` | True where a row is real input. |
| `action_mask` | `[batch, max_candidate_slots]` | True where the action can be resolved. |
| `sample_positions` | `[batch]` | Positions into the selected sample array. |

Windows are front-packed. Models use `take_last_valid` to read the final real context position.

## Training Loop

Training is CUDA-only. It sets seeds, configures deterministic behavior when requested, probes memory, and chooses device-resident batch storage when possible.

```text
for epoch:
    train batches
    compute prediction loss
    clip gradients
    validate
    evaluate objective metric
    save best checkpoint
    apply early stopping
```

Optimizer is AdamW. Mixed precision uses CUDA support when enabled. Best checkpoint reload happens before final artifact persistence.

## Inference

Inference allocates one decoded result buffer sized to the selected samples. Each batch writes decoded offsets back by sample position.

```text
sample_indices
  -> batches
  -> model outputs
  -> prediction contract decode
  -> DecodedOffsets buffer
```

`DecodedOffsets` is the current decoded ABI consumed by evaluators.

## Scoring Service

`score_evaluation()` is the bridge from model to evaluator:

```text
validate evaluator accepts prediction contract
  -> predict_with_model
  -> evaluator.run(store, realization_policy, decoded_offsets)
```

This keeps evaluation scoring independent from training-loop details.

## Artifact Persistence

A trained artifact contains:

| Item | Meaning |
| --- | --- |
| `model.pt` | PyTorch state. |
| Artifact manifest | Exact authored configs and semantic identity. |
| Scaler | Training-fitted input normalization. |
| Builder runtime metadata | Dataset-builder-specific inference metadata. |
| Training summary/epochs | Runtime training metrics. |
| Evaluation summaries | Stored diagnostic evaluation runs. |

Evaluate workflow validates that the requested config matches artifact semantics before running inference.

## Tuning

Tuning uses Optuna. Each trial samples typed params, applies them to the base config, trains in a trial directory without persisting an artifact, records best epoch metadata, and returns the selected objective metric.

Study state stores the study manifest and Optuna tables. Trial user attributes record sampled params and best epoch.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| No CUDA | Current training implementation requires NVIDIA CUDA. |
| Model/prediction shape mismatch | Output heads do not match prediction contract. |
| Empty split | Dataset builder produced no samples for a split. |
| Objective metric missing | Prediction/evaluator metrics do not expose configured metric. |
| Artifact semantic mismatch | Evaluation config does not match trained artifact. |
| Tuning identity mismatch | Existing study state belongs to a different request. |

## Extension Pattern

New modeling implementations should enter through contracts: model families own architectures, prediction families own output/loss/decode, dataset builders own sample construction, and workflows only orchestrate those pieces.

