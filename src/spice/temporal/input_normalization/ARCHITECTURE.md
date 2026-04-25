# Input Normalization Architecture

## Purpose

`temporal.input_normalization` owns scaler fitting policies for temporal problem stores. It decides how normalization statistics are learned from training data.

Applying a scaler to a feature matrix is generic and lives in temporal scaling helpers. The input-normalization contract owns fitting, not matrix transformation.

## Flow

```text
TrainingConfig.input_normalization
        |
        v
coerce_input_normalization_config()
        |
        v
compile_input_normalization_contract()
        |
        v
fit_scaler(feature_matrix, context_start_rows, anchor_rows, train_sample_indices)
        |
        v
ScalerStats
        |
        v
transform_feature_matrix(feature_matrix, scaler)
```

The same saved `ScalerStats` is used later during inference/evaluation so that evaluation data is transformed with training-time statistics.

## Registry Pattern

Input-normalization configs use `id` as the implementation selector. The local registry maps ids to concrete config types and compile hooks. Compile dispatch uses `require_spec_config` to ensure the already-coerced config matches the selected spec.

```text
id -> config_type -> concrete compile hook -> CompiledInputNormalizationContract
```

## Theory

Normalization stabilizes model training by putting features on comparable scales. Temporal normalization must avoid leakage: statistics should be fit from allowed training rows, not future evaluation rows.

Different policies can choose different fitting windows or weights. Dataset builders call the compiled contract and do not need to know policy internals.

## Extension Points

Add a normalization policy when the fitting rule changes. Keep scaler application generic so builders can apply any fitted scaler uniformly.
