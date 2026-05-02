# Model Families Architecture

## Purpose

`modeling.families` owns concrete neural network architectures and their config models.

## Theory

A model family defines the function approximator. It does not define the prediction target. This separation lets an LSTM, transformer, or hybrid model train against the same prediction family contract.

## Invariants

Families construct models from typed configs and representation/prediction contracts. They should not resolve YAML, read storage, compute evaluator metrics, or build temporal labels.

## Extension Points

Add a family for a new architecture. Keep model-specific hyperparameters in the family config and tune-space config, not in generic training config.

## Family Flow

```text
ModelConfig
    |
    v
representation contract + prediction output spec
    |
    v
TemporalModel
    |
    v
training/inference services
```

## Beginner Context

An LSTM, transformer, or hybrid architecture is a way to transform input tensors into output tensors. It should not decide which target is correct or which fee metric matters. Those decisions belong to prediction and evaluation.

## Hyperparameter Boundary

Model-family config owns architectural hyperparameters such as hidden size, dropout, layers, or attention dimensions. Training config owns optimizer and loop behavior such as learning rate, epochs, batch size, and early stopping.

Config-facing model-family coercion normalizes invalid payload envelopes to `ConfigResolutionError` and returns already typed model configs unchanged.
