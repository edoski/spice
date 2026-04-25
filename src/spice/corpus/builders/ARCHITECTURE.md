# Corpus Builders Architecture

## Purpose

`corpus.builders` prepares raw acquisition output into persisted history and evaluation block files.

## Theory

The history/evaluation split is a data-management boundary. History is available for training and calibration. Evaluation is held for scoring trained artifacts. This mirrors standard ML practice: never train on the data used for final evaluation.

## Invariants

Builders should preserve canonical block schema and window metadata. They should not create targets or tensors. Those require feature and temporal semantics and therefore belong downstream.

## Extension Points

Add builder helpers for new raw-data partitioning needs, and keep the output shape aligned with corpus storage and validation.

## Module Map

```text
builders/
  shared.py      common block-frame preparation
  history.py     history-window materialization
  evaluation.py  evaluation-window materialization
```

## Window Model

```text
requested chain time range
          |
          +--> history window
          |
          +--> evaluation window
```

History provides past context for training and calibration. Evaluation provides the held-out future region used after an artifact exists. The builder layer materializes those windows but does not decide model inputs or targets.
