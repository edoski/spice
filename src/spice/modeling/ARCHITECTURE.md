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
  +--> objective metric source
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
run_training_fit()
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
Artifact Inference Context
  |
  +--> validate artifact semantics
  +--> reconstruct runtime metadata
  +--> prepare inference dataset
  |
  v
EvaluationScoringContext
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

Artifact inference preparation is centralized in `modeling.artifact_inference`. It turns an active evaluate workflow config plus a trained artifact into trusted scoring inputs. Evaluator execution stays in `modeling.scoring` when model inference is involved.

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
  batch_plan.py           training/inference batch planning
  forward_runtime.py      forward-only warmup, memory measurement, and execution
  training_runtime.py     training warmup, budget planning, and prediction state fitting
  training_runner.py      fit and split metric execution
  _epoch_execution.py     private train/validation batch mechanics
  _fit_policy.py          private best-state and early-stop policy
  objective_metrics.py    objective metric production during training
  inference.py            model prediction over prepared stores
  scoring.py              model inference -> evaluator bridge
  artifacts.py            artifact loading/validation helpers
  artifact_inference.py   artifact validation -> inference scoring context
  persisted_training.py   training artifact write path
```

## Extension Points

Add a model family for a new neural architecture. Add a dataset builder for a new tensorization strategy. Add scoring behavior only when it is generic model-to-evaluator bridging; evaluator-specific scoring belongs in `evaluation`.

Runtime planning is intentionally split from fit policy. `forward_runtime.py` owns forward-only host warmup and measured final batch planning for inference and split metrics. `training_runtime.py` owns the destructive gradient-bearing probe, restores model state, clears CUDA cache after that probe, and returns one reusable prediction training state. `training_runner.py` remains the public fit interface and keeps callback, best-state, and result assembly ownership.
