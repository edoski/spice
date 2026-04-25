# Modeling Architecture

## Purpose

`modeling` owns tensorization, model-family construction, training loops, inference, scoring, trained artifact assembly, and model result payload codecs.

It is the bridge between generic temporal examples and neural network execution.

## Training Flow

```text
TrainConfig
  |
  v
build_training_spec()
  |
  +--> feature contract
  +--> problem contract
  +--> prediction contract
  +--> objective contract
  +--> dataset-builder contract
  +--> input-normalization contract
  |
  v
prepare_training_dataset()
  |
  v
build model family
  |
  v
train_model()
  |
  v
persist artifact state
```

The model family is only one part of learning. The same model architecture can learn a different task if the prediction family changes. The same prediction task can use a different model family if model config changes.

## Evaluation/Scoring Flow

```text
loaded artifact
  |
  v
prepare inference dataset
  |
  v
score_evaluation()
  |
  +--> evaluator checks accepted decoded-result id
  +--> predict_with_model()
  +--> evaluator.run()
  |
  v
EvaluationSummary
```

Evaluator execution is centralized in `modeling.scoring` when model inference is involved. Objectives and evaluate workflows route through this service instead of duplicating inference-plus-evaluation logic.

## Dataset Builders

Dataset builders adapt temporal stores into model-ready training and inference datasets. They own tensorization policy, split behavior, runtime metadata, and scaler fitting inputs. They do not own feature semantics, problem compilers, prediction losses, or evaluator metrics.

```text
raw/canonical blocks
    |
    v
builder-local frame preparation
    |
    v
feature table
    |
    v
problem store
    |
    v
prepared dataset + runtime metadata
```

Shared dataset-builder abstractions should remove real duplication without hiding sample-ordering, split, candidate-window, or empty-frame policy.

## Module Map

```text
modeling/
  pipeline.py             spec construction and dataset preparation facade
  dataset_builders/       tensorization strategies and runtime metadata
  families/               neural network family configs/builders/tuning hooks
  training.py             fit/evaluate loops
  inference.py            model prediction over prepared stores
  scoring.py              model inference -> evaluator bridge
  artifacts.py            artifact loading/validation helpers
  result_codecs.py        persisted ML result payload codecs
  persisted_training.py   training artifact write path
```

## Extension Points

Add a model family for a new neural architecture. Add a dataset builder for a new tensorization strategy. Add scoring behavior only when it is generic model-to-evaluator bridging; evaluator-specific scoring belongs in `evaluation`.
