# Objectives Architecture

## Purpose

`objectives` defines what optimization and tuning should maximize or minimize.

## Theory

An objective can be a validation metric from the training loop or a benchmark metric from evaluator scoring. Separating objective selection from prediction and evaluation lets you train one prediction task while tuning for a decision-quality metric.

## Invariants

Validation objectives read validation metrics directly. Evaluation objectives use the scoring service, which checks the evaluator's accepted decoded-result id, runs inference, and returns evaluator metrics. Objective configs must match the selected evaluation when they benchmark an evaluator.

## Extension Points

Add an objective type when the source of objective metrics changes. Do not put evaluator execution in tuning code; route through the objective contract and scoring service.

## Objective Flow

```text
training epoch
    |
    +--> validation metrics --------+
    |                               |
    +--> optional evaluator scoring +
                                    |
                                    v
                              objective metric
                                    |
                                    v
                         early stopping / tuning direction
```

## Beginner Context

The objective is the scalar value used to compare model states or tuning trials. A metric can be useful for diagnostics without being the objective. For example, an evaluator may report many economic metrics, but tuning needs one primary metric and one direction.

## Evaluation Objective Boundary

Evaluation-backed objectives use `modeling.scoring`. That service performs the generic sequence:

```text
check decoded-result id -> predict -> evaluate -> return metrics
```

This keeps Optuna and training loops from knowing evaluator internals.
