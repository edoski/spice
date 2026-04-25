# Realization Policy Architecture

## Purpose

`temporal.realization` defines how a selected candidate offset becomes a realized outcome.

## Theory

Prediction chooses an action. Evaluation needs to know what that action would have cost under the problem definition. A realization policy is this bridge from action to outcome.

## Invariants

Policies must be compiled contracts, not workflow branches. Config-facing payload errors use `ConfigResolutionError`. Evaluators receive a realization-policy contract and a decoded prediction result, then compute metrics from the problem store.

## Extension Points

Add a policy for a new action-to-outcome rule. Keep policy metadata explicit so artifacts can be understood later.

## Flow

```text
decoded action offset
        +
problem store candidate rows
        |
        v
realized fee / outcome
        |
        v
evaluator metric calculation
```

## Beginner Context

The model's output is not automatically an economic result. It is an action. The realization policy defines how that action interacts with the temporal problem. This keeps "what did the model choose?" separate from "what happened because of that choice?"

## Contract Rule

Evaluators receive a realization contract, not a policy id string. That contract should expose behavior and semantics needed for scoring without requiring evaluator engines to know concrete policy classes.
