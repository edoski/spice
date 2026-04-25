# Dataset Builders Architecture

## Purpose

`modeling.dataset_builders` turns feature tables and temporal problem contracts into prepared datasets for training and inference. This is the tensorization seam.

Tensorization matters because the same temporal problem can be represented as independent rows, fixed-context sequences, or another model input shape without changing feature semantics or evaluator behavior.

## Generic Flow

```text
blocks
  |
  v
builder-local frame preparation
  |
  v
feature_contract.build_table()
  |
  v
problem_contract.build_capability_store()  train
problem_contract.build_delay_store()       evaluate
  |
  v
input normalization fit/transform
  |
  v
PreparedTrainingDataset / PreparedInferenceDataset
```

Frame preparation is intentionally local to each builder. A generic helper with flags can hide policy differences such as sort key, deduplication, or whether an empty evaluation frame is allowed. Those choices affect examples and therefore model behavior.

## Registry Dispatch

```text
coerce_dataset_builder_config(payload)
  -> dataset_builder.id
  -> local spec config_type
  -> concrete DatasetBuilderConfig

compile_dataset_builder_contract(config)
  -> local spec
  -> require_spec_config(config, spec.config_type)
  -> concrete compile_dataset_builder(config)
```

The registry does not serialize and revalidate a concrete config during compile. Coercion validates. Compile dispatch asserts the invariant.

## Runtime Metadata

Runtime metadata exists because some builders learn non-model assumptions during training. Examples include sequence length, calibrated timing assumptions, or compiler runtime metadata.

```text
training prepare
  -> builder runtime metadata
  -> artifact manifest
  -> evaluation prepare
  -> reconstruct same assumptions
```

Fixed-context inference explicitly requires `FixedContextTemporalBuilderRuntimeMetadata`. The check lives near the fixed-context use site because the requirement is builder-specific, not a generic base helper.

## Invariants

Builders must preserve:

```text
sample ordering
split assignment
candidate-window alignment
feature prerequisite validation
training/inference scaler ownership
runtime metadata round-trip
```

Sampling and split behavior are builder-owned invariants.

## Extension Points

Add a builder when model input representation changes. Keep it behind `DatasetBuilderConfig`, `CompiledDatasetBuilderContract`, and a local spec entry. Avoid workflow branches on builder ids.
