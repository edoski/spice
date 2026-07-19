# FABLE (Fee Analysis through Blockchain Learning and Estimation) Reference

This reference defines FABLE's strict requests, completed objects, direct addresses, commands, operator YAML, serving/mobile surfaces, and evaluation schemas.

## Scalar conventions

- Object IDs are UUIDv4.
- `PositiveInt` means strict integer `>0`; `NonNegativeInt` means strict integer `≥0`. Booleans are not integers.
- Scientific floats are finite. Positive/nonnegative bounds are stated per field.
- Block ranges and origin windows are inclusive.
- Base fees are positive Int64 wei/gas unless a field explicitly says Float64 aggregation.
- Timestamps and elapsed values are integer seconds.
- Strict records reject unknown fields and revalidate nested instances.

Distribution name, import root, and installed executable are `fable`; the static distribution version is `0.1.0`.

## Requests and definitions

### Corpus

| Record | Ordered field | Type and rule |
| --- | --- | --- |
| `CorpusDefinition` | `chain_id` | PositiveInt |
|  | `first_block` | NonNegativeInt |
|  | `last_block` | NonNegativeInt, `last_block≥first_block` |
| `CorpusRequest` | `corpus_id` | UUIDv4 |
|  | `definition` | `CorpusDefinition` |

Fresh constructor:

```python
fresh_corpus_request(definition: CorpusDefinition) -> CorpusRequest
```

### Scientific semantics

| Record | Ordered field | Type and rule |
| --- | --- | --- |
| `OriginWindow` | `role` | `"training" | "validation" | "testing"` |
|  | `first_parent_block` | NonNegativeInt |
|  | `last_parent_block` | NonNegativeInt, not before first |
| `LossDefinition` | `classification_algorithm` | exactly `"cross_entropy"` |
|  | `classification_weighting` | `"unweighted" | "corrected_inverse_frequency"` |
|  | `regression_algorithm` | exactly `"smooth_l1"` |
|  | `regression_threshold` | finite float `>0` |
|  | `classification_scale` | finite float `≥0` |
|  | `regression_scale` | finite float `≥0` |
| `ExperimentSemantics` | `training_window` | `OriginWindow(role="training")` |
|  | `validation_window` | `OriginWindow(role="validation")` |
|  | `context_blocks` | PositiveInt `C` |
|  | `horizon_blocks` | PositiveInt `K` |
|  | `ordered_features` | nonempty unique tuple of nonempty strings |
|  | `loss` | `LossDefinition` |

The training last parent plus `K` must be strictly less than the validation first parent.

### Model definitions

`ModelDefinition` is a discriminated union on `family`:

| Family | Ordered fields after `family` |
| --- | --- |
| `lstm` | `hidden: PositiveInt`; `layers: PositiveInt`; `head_hidden: PositiveInt`; `dropout: 0≤float<1` |
| `transformer` | `model_width`; `attention_heads`; `transformer_layers`; `feedforward_width`; `head_hidden`: PositiveInt; `dropout: 0≤float<1` |
| `transformer_lstm` | `model_width`; `attention_heads`; `transformer_layers`; `feedforward_width`; `lstm_hidden`; `lstm_layers`; `head_hidden`: PositiveInt; `dropout: 0≤float<1` |

Transformer widths must be even and divisible by `attention_heads`.

### Method and MethodSpace

| Record | Ordered field | Type and rule |
| --- | --- | --- |
| `AdamWMethod` | `learning_rate` | finite float `>0` |
|  | `weight_decay` | finite float `≥0` |
| `FitMethod` | `accumulation` | PositiveInt |
|  | `gradient_clip_norm` | finite float `≥0` |
|  | `scheduler` | exactly `"none"` |
|  | `seed` | NonNegativeInt |
|  | `max_epochs` | PositiveInt |
|  | `validate_every_completed_epoch` | PositiveInt |
|  | `patience` | NonNegativeInt |
|  | `min_delta` | finite float `≥0` |
|  | `improvement` | exactly `"strict_lower"` |
|  | `restore` | exactly `"earliest_best"` |

Every serialized Method has ordered fields `dropout`, `optimizer`, `training_batch`, `fit`, `family`, and `capacity`. `dropout` is finite in `[0,1)`, `optimizer` is `AdamWMethod`, `training_batch` is PositiveInt, and `fit` is `FitMethod`.

| Method family | Capacity fields |
| --- | --- |
| `lstm` | `hidden`, `layers`, `head_hidden`: PositiveInt |
| `transformer` | `model_width`, `attention_heads`, `transformer_layers`, `feedforward_width`, `head_hidden`: PositiveInt |
| `transformer_lstm` | `model_width`, `attention_heads`, `transformer_layers`, `feedforward_width`, `lstm_hidden`, `lstm_layers`, `head_hidden`: PositiveInt |

Transformer capacity obeys the same even/divisible width constraints. A `MethodSpace` has `family` plus a nonempty tuple `methods` of unique Methods from exactly that family.

### Study, training, and workflow requests

| Record | Ordered field | Type and rule |
| --- | --- | --- |
| `StudyDefinition` | `experiment` | `ExperimentSemantics` |
|  | `method_space` | family-discriminated `MethodSpace` |
| `TrainingDefinition` | `experiment` | `ExperimentSemantics` |
|  | `model` | `ModelDefinition` |
|  | `optimizer` | `AdamWMethod` |
|  | `training_batch` | PositiveInt |
|  | `fit` | `FitMethod` |
| `BaselineSource` | `kind` | exactly `"baseline"` |
|  | `corpus_id` | UUIDv4 |
|  | `training_definition` | `TrainingDefinition` |
| `SelectedStudySource` | `kind` | exactly `"selected_study"` |
|  | `corpus_id` | UUIDv4 |
|  | `study_id` | UUIDv4 |
|  | `study_result_index` | NonNegativeInt |
|  | `experiment` | `ExperimentSemantics` |
| `TrainRequest` | `workflow` | exactly `"train"` |
|  | `artifact_id` | UUIDv4 |
|  | `source` | `BaselineSource | SelectedStudySource` |
| `TuneRequest` | `workflow` | exactly `"tune"` |
|  | `study_id` | UUIDv4 |
|  | `corpus_id` | UUIDv4 |
|  | `study_definition` | `StudyDefinition` |
| `EvaluateRequest` | `workflow` | exactly `"evaluate"` |
|  | `evaluation_id` | UUIDv4 |
|  | `artifact_id` | UUIDv4 |
|  | `corpus_id` | UUIDv4 |
|  | `window` | validation or testing `OriginWindow`; training is rejected |

`WorkflowRequest` is exactly `TrainRequest | EvaluateRequest`. `TuneRequest` is intentionally separate.

Fresh constructors:

```python
fresh_train_request(source: TrainingSource) -> TrainRequest
fresh_tune_request(corpus_id: UUID, study_definition: StudyDefinition) -> TuneRequest
fresh_evaluate_request(
    artifact_id: UUID,
    corpus_id: UUID,
    window: OriginWindow,
) -> EvaluateRequest
```

## Durable addresses and objects

Given an explicit `storage_root`:

```text
corpora/<corpus_id>/corpus.json
corpora/<corpus_id>/blocks.parquet
studies/<study_id>.json
artifacts/<artifact_id>.ckpt
evaluations/<evaluation_id>/evaluation.json
evaluations/<evaluation_id>/observations.parquet
```

IDs are lowercase UUID strings produced by `str(UUID)` and appear directly in the paths above.

### Corpus object

`corpus.json` has exactly:

```text
request: CorpusRequest
finalized_anchor:
  block_number: integer >= 0
  block_hash: 64 lowercase hexadecimal characters
```

`blocks.parquet` has this exact ordered, nonnull schema:

| # | Column | Type | Unit/rule |
| ---: | --- | --- | --- |
| 1 | `block_number` | Int64 | contiguous inclusive request range |
| 2 | `timestamp` | Int64 | nonnegative seconds; nondecreasing |
| 3 | `chain_id` | Int64 | equals request chain |
| 4 | `base_fee_per_gas` | Int64 | positive wei/gas |
| 5 | `gas_used` | Int64 | gas, `0≤used≤limit` |
| 6 | `gas_limit` | Int64 | positive gas |
| 7 | `tx_count` | Int64 | nonnegative transaction count |

Direct loader:

```python
load_corpus(storage_root: Path, corpus_id: UUID4) -> Corpus
```

### Study object

`studies/<study_id>.json` is a strict `Study`:

```text
request: TuneRequest
trials: nonempty ordered tuple[RetainedResult, ...]
```

Each `RetainedResult` has exact ordered fields:

| Field | Type/rule |
| --- | --- |
| `method` | exact Method contained in the request MethodSpace |
| `objective` | finite float validation total loss |
| `selected_epoch` | integer `≥1` |
| `completed_epochs` | integer `≥selected_epoch` and `≤method.fit.max_epochs` |

### Native Lightning artifact

`artifacts/<artifact_id>.ckpt` is the native Lightning weights-only best checkpoint. Its `ArtifactAssociation` contains:

| Ordered field | Type/rule |
| --- | --- |
| `request` | exact `TrainRequest`; embedded artifact UUID must match path |
| `feature_state` | Float64 means and positive standard deviations, equal feature width |
| `target_state` | Float64 finite mean and positive standard deviation |
| `classification_state` | null for unweighted; positive class-support tuple of length `K` for corrected weighting |
| `study_result_index` | absent/null for baseline; exact nonnegative source index for selected Study |
| `method` | absent/null for baseline; exact selected Method for selected Study |

Direct loader:

```python
load_artifact(
    storage_root: Path,
    artifact_id: UUID,
) -> tuple[ArtifactAssociation, torch.nn.Module]
```

### Evaluation object

`evaluation.json` is exactly the `EvaluateRequest`. `observations.parquet` is the canonical schema below. Aggregations and TSVs are derived from this directory.

## CLI

Four public command leaves:

```text
fable submit REQUEST.json [REQUEST.json ...]
fable corpus acquire REQUEST.json --rpc-url URL --poa|--no-poa
fable study run TUNE_REQUEST.json METHOD.json
fable study finalize STUDY_ID
```

- `submit` accepts one or more WorkflowRequest files and prints one positive Slurm job ID per request.
- `corpus acquire` reads `STORAGE_ROOT`, requires an absolute path, and requires an explicit PoA choice.
- `study run` validates one strict TuneRequest and one strict Method, then prints the candidate Slurm job ID.
- `study finalize` requires UUIDv4, reads absolute `STORAGE_ROOT`, and publishes existing progress.

Two help-hidden generated-job leaves:

```text
fable remote workflow
fable remote candidate
```

Generated Slurm scripts call these leaves with strict JSON envelopes on standard input.

## Remote submission

`from fable.execution import submit` is the public execution seam:

```python
submit(request: WorkflowRequest) -> int
```

It reads cwd-local `REMOTE.yaml` with this exact strict schema:

| Section | Ordered field | Type/rule |
| --- | --- | --- |
| root | `ssh` | nonempty string passed to OpenSSH |
|  | `executable` | nonempty absolute installed-executable path |
|  | `storage_root` | nonempty absolute path |
|  | `log_root` | nonempty absolute path |
| `resources` | `partition` | nonempty string |
|  | `gres` | string |
|  | `cpus_per_task` | PositiveInt |
|  | `memory_gb` | PositiveInt, rendered as `--mem=<n>G` |
|  | `time_limit` | nonempty Slurm time string |
| `deployment` | `evaluation_batch_size` | PositiveInt |
|  | `num_workers` | NonNegativeInt |
|  | `pin_memory` | bool |
|  | `prefetch_factor` | PositiveInt or null |
|  | `persistent_workers` | bool |
|  | `deterministic` | bool or exactly `"warn"` |
|  | `benchmark` | bool |
|  | `float32_matmul_precision` | `"highest" | "high"` |
|  | `cuda_matmul_allow_tf32` | bool |
|  | `cudnn_allow_tf32` | bool |

The generated script requests one node/task, writes `%j.out` under `log_root`, exports `STORAGE_ROOT`, and executes `fable remote workflow` or `fable remote candidate` with a stdin heredoc. Submission is one `ssh -T -o BatchMode=yes … sbatch --parsable` call.

`STORAGE_ROOT`, `ETHEREUM_RPC_URL`, `POLYGON_RPC_URL`, and `AVALANCHE_RPC_URL` are the neutral operator spellings. `STORAGE_ROOT` is the implicit environment input to current CLI/remote Python paths. RPC endpoints arrive through explicit invocation or YAML values.

## Serving and mobile

The serving factory is `fable.serving:create_app`; its display title is `FABLE Inference API`. It reads cwd-local `SERVING.yaml` once during application lifespan and uses its values literally.

Exact strict serving fields:

| # | Field | Rule |
| ---: | --- | --- |
| 1 | `storage_root` | absolute path |
| 2 | `ethereum_rpc_url` | nonempty string |
| 3 | `polygon_rpc_url` | nonempty string |
| 4 | `avalanche_rpc_url` | nonempty string |
| 5 | `ethereum_k2_artifact_id` | UUIDv4 |
| 6 | `ethereum_k3_artifact_id` | UUIDv4 |
| 7 | `ethereum_k4_artifact_id` | UUIDv4 |
| 8 | `ethereum_k5_artifact_id` | UUIDv4 |
| 9 | `polygon_k2_artifact_id` | UUIDv4 |
| 10 | `polygon_k3_artifact_id` | UUIDv4 |
| 11 | `polygon_k4_artifact_id` | UUIDv4 |
| 12 | `polygon_k5_artifact_id` | UUIDv4 |
| 13 | `avalanche_k2_artifact_id` | UUIDv4 |
| 14 | `avalanche_k3_artifact_id` | UUIDv4 |
| 15 | `avalanche_k4_artifact_id` | UUIDv4 |
| 16 | `avalanche_k5_artifact_id` | UUIDv4 |

All configured artifact IDs must be distinct.

Serving expects Ethereum chain ID `1`, Polygon `137`, and Avalanche C-Chain `43114`; the Polygon and Avalanche clients install the PoA extra-data middleware.

The strict request is:

```text
chain: "ethereum" | "polygon" | "avalanche"
K: 2 | 3 | 4 | 5
```

`POST /inference` returns nonnegative integers:

```text
head_block
selected_action_k
target_block = head_block + 1 + selected_action_k
```

OpenAPI and interactive documentation routes are disabled. The server verifies provider chain ID, loads the exact selected-Study artifact, requires request `K` to equal artifact `K`, reads the latest head plus `C-1` predecessors, prepares float32 `[1,C,F]`, and runs CPU inference.

The private Expo app manifest is fixed at:

| Fact | Value |
| --- | --- |
| display | `FABLE Demo` |
| package | `fable-mobile-demo` |
| Expo slug/scheme | `fable-demo` |
| iOS bundle ID | `dev.edoski.fable.demo` |
| Android package | `dev.edoski.fable.demo` |
| entry | `expo/AppEntry` |

Its only backend variable is `EXPO_PUBLIC_FABLE_BACKEND_URL`. It posts the strict request to `/inference` and displays only the three response fields.

## Evaluation API

Public exports from `fable.evaluation`:

```python
class EvaluationDeployment:
    batch_size: PositiveInt
    num_workers: NonNegativeInt
    pin_memory: bool
    prefetch_factor: PositiveInt | None
    persistent_workers: bool
    deterministic: bool | Literal["warn"]
    benchmark: bool
    float32_matmul_precision: Literal["highest", "high"]
    cuda_matmul_allow_tf32: bool
    cudnn_allow_tf32: bool

evaluate(
    request: EvaluateRequest,
    storage_root: Path,
    deployment: EvaluationDeployment,
) -> None

reduce_evaluation(
    storage_root: Path,
    evaluation_id: UUID,
) -> polars.DataFrame

write_sealed_report(
    storage_root: Path,
    evaluation_ids: tuple[UUID, ...],
    destination: Path,
) -> None
```

### S12 canonical observations

Destination: `evaluations/<evaluation_id>/observations.parquet`. Status: canonical, ordered, nonnull, one row per inclusive origin in ascending block order.

| # | Field | Type | Unit/meaning |
| ---: | --- | --- | --- |
| 1 | `origin_block` | Int64 | closed parent `h` |
| 2 | `origin_timestamp` | Int64 | `timestamp(h)`, seconds |
| 3 | `selected_action_k` | Int64 | decoded `k∈[0,K)` |
| 4 | `earliest_hindsight_action_k` | Int64 | first raw-fee argmin |
| 5 | `classification_loss_contribution` | Float64 | per-origin CE after weighting and classification scale |
| 6 | `predicted_hindsight_minimum_base_fee_z` | Float32 | auxiliary standardized log-minimum prediction |
| 7 | `previous_closed_parent_base_fee_per_gas` | Int64 | fee at `h-1`, wei/gas |
| 8 | `closed_parent_base_fee_per_gas` | Int64 | fee at `h`, wei/gas |
| 9 | `immediate_k0_base_fee_per_gas` | Int64 | fee at `h+1`, wei/gas |
| 10 | `selected_target_base_fee_per_gas` | Int64 | fee at `h+1+k`, wei/gas |
| 11 | `hindsight_minimum_base_fee_per_gas` | Int64 | raw minimum over `h+1…h+K`, wei/gas |
| 12 | `selected_action_wait_seconds` | Int64 | `timestamp(h+k)-timestamp(h)`; zero for `k=0` |
| 13 | `full_horizon_elapsed_seconds` | Int64 | `timestamp(h+K)-timestamp(h)` |

### S14 transient reduction

Destination: none. `reduce_evaluation()` returns a one-row DataFrame. Status: derived, transient, noncanonical. Every field is nonnull except field 22, whose null rule is exact `sum(G)==0`. `selected_action_count_by_k` is a native `List(Int64)` of length `K` whose values sum to the eligible count.

| # | Field | Type |
| ---: | --- | --- |
| 1 | `evaluation_id` | String |
| 2 | `eligible_origin_count` | Int64 |
| 3 | `earliest_hindsight_label_correct_count` | Int64 |
| 4 | `earliest_hindsight_label_cross_entropy_loss_sum` | Float64 |
| 5 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum` | Float64 |
| 6 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_absolute_error_sum` | Float64 |
| 7 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_squared_error_sum` | Float64 |
| 8 | `earliest_hindsight_label_cross_entropy_loss` | Float64 |
| 9 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss` | Float64 |
| 10 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae` | Float64 |
| 11 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse` | Float64 |
| 12 | `multitask_total_loss` | Float64 |
| 13 | `earliest_hindsight_label_accuracy` | Float64 |
| 14 | `earliest_hindsight_label_macro_f1` | Float64 |
| 15 | `immediate_k0_base_fee_per_gas_sum` | Float64 |
| 16 | `finite_target_base_fee_per_gas_savings_sum` | Float64 |
| 17 | `finite_target_base_fee_per_gas_hindsight_opportunity_sum` | Float64 |
| 18 | `finite_target_base_fee_per_gas_hindsight_regret_sum` | Float64 |
| 19 | `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0` | Float64 |
| 20 | `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0` | Float64 |
| 21 | `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0` | Float64 |
| 22 | `signed_captured_hindsight_opportunity_ratio` | nullable Float64 |
| 23 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_sum` | Float64 |
| 24 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_defined_origin_count` | Int64 |
| 25 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_zero_denominator_exclusion_count` | Int64 |
| 26 | `mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0` | Float64 |
| 27 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum` | Float64 |
| 28 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count` | Int64 |
| 29 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count` | Int64 |
| 30 | `mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 31 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum` | Float64 |
| 32 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count` | Int64 |
| 33 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count` | Int64 |
| 34 | `mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 35 | `harmful_action_count` | Int64 |
| 36 | `harmful_action_rate` | Float64 |
| 37 | `selected_action_count_by_k` | List(Int64) |
| 38 | `extra_wait_block_opportunities_vs_immediate_k0_sum` | Float64 |
| 39 | `mean_extra_wait_block_opportunities_vs_immediate_k0` | Float64 |
| 40 | `selected_action_wait_seconds_sum` | Float64 |
| 41 | `mean_selected_action_wait_seconds` | Float64 |
| 42 | `full_horizon_elapsed_seconds_sum` | Float64 |
| 43 | `mean_full_horizon_elapsed_seconds` | Float64 |

Fields 15–18 and 38, 40, 42 are sums in their named units; their ratios/means use one eligible origin as the unit. Fee sums are wei/gas represented as Float64 after exact Int64 differences.

### S15 sealed testing TSV

Destination: caller-supplied absent path to `write_sealed_report()`. Status: derived, noncanonical TSV; rows follow explicit evaluation-ID order. List fields use compact JSON arrays. Nulls use empty TSV fields. Only `study_id`, `study_result_index`, and `signed_captured_hindsight_opportunity_ratio` may be null under their stated conditions.

| # | Column | TSV type/encoding |
| ---: | --- | --- |
| 1 | `evaluation_id` | String |
| 2 | `artifact_id` | String |
| 3 | `corpus_id` | String |
| 4 | `chain_id` | Int64 |
| 5 | `window_role` | String, exactly testing |
| 6 | `first_parent_block` | Int64 (`T`) |
| 7 | `last_parent_block` | Int64 (`E`) |
| 8 | `corpus_endpoint_block` | Int64 (`L`) |
| 9 | `testing_candidate_origin_count` | Int64, `L-T+1` |
| 10 | `testing_incomplete_kmax_outcome_exclusion_count` | Int64, `L-E` |
| 11 | `testing_elapsed_seconds` | Int64, `timestamp(E)-timestamp(T)` |
| 12 | `source_kind` | String |
| 13 | `study_id` | nullable String; empty for baseline |
| 14 | `study_result_index` | nullable Int64; empty for baseline |
| 15 | `model_family` | String |
| 16 | `context_blocks` | Int64 |
| 17 | `horizon_blocks` | Int64 |
| 18 | `ordered_features` | compact JSON array of String |
| 19 | `classification_loss` | String classification-weighting value |
| 20 | `trainable_parameter_count` | Int64 |
| 21 | `eligible_origin_count` | Int64 |
| 22 | `earliest_hindsight_label_correct_count` | Int64 |
| 23 | `earliest_hindsight_label_cross_entropy_loss_sum` | Float64 |
| 24 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_sum` | Float64 |
| 25 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_absolute_error_sum` | Float64 |
| 26 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_squared_error_sum` | Float64 |
| 27 | `earliest_hindsight_label_cross_entropy_loss` | Float64 |
| 28 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss` | Float64 |
| 29 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae` | Float64 |
| 30 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse` | Float64 |
| 31 | `multitask_total_loss` | Float64 |
| 32 | `earliest_hindsight_label_accuracy` | Float64 |
| 33 | `earliest_hindsight_label_macro_f1` | Float64 |
| 34 | `immediate_k0_base_fee_per_gas_sum` | Float64 |
| 35 | `finite_target_base_fee_per_gas_savings_sum` | Float64 |
| 36 | `finite_target_base_fee_per_gas_hindsight_opportunity_sum` | Float64 |
| 37 | `finite_target_base_fee_per_gas_hindsight_regret_sum` | Float64 |
| 38 | `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0` | Float64 |
| 39 | `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0` | Float64 |
| 40 | `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0` | Float64 |
| 41 | `signed_captured_hindsight_opportunity_ratio` | nullable Float64; empty iff exact `sum(G)==0` |
| 42 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_sum` | Float64 |
| 43 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_defined_origin_count` | Int64 |
| 44 | `target_base_fee_per_gas_savings_fraction_vs_immediate_k0_zero_denominator_exclusion_count` | Int64 |
| 45 | `mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0` | Float64 |
| 46 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum` | Float64 |
| 47 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count` | Int64 |
| 48 | `selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count` | Int64 |
| 49 | `mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 50 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_sum` | Float64 |
| 51 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_defined_origin_count` | Int64 |
| 52 | `immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_zero_denominator_exclusion_count` | Int64 |
| 53 | `mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 54 | `harmful_action_count` | Int64 |
| 55 | `harmful_action_rate` | Float64 |
| 56 | `selected_action_count_by_k` | compact JSON array of Int64 |
| 57 | `extra_wait_block_opportunities_vs_immediate_k0_sum` | Float64 |
| 58 | `mean_extra_wait_block_opportunities_vs_immediate_k0` | Float64 |
| 59 | `selected_action_wait_seconds_sum` | Float64 |
| 60 | `mean_selected_action_wait_seconds` | Float64 |
| 61 | `full_horizon_elapsed_seconds_sum` | Float64 |
| 62 | `mean_full_horizon_elapsed_seconds` | Float64 |

### S16 context-history TSV

Owner: `experiments.context_history.write_context_history_evidence`. Destination: caller-supplied absent path. Status: derived, noncanonical TSV. Rows follow the function's exact caller/coordinate order. Tuple/list values use compact JSON arrays; non-C200 rows encode fields 70–71 as `[]`. Only captured opportunity and its delta may be null, encoded as an empty field; null propagates when either compared captured value is null. Every `_delta_vs_same_chain_c200` is current value minus the same-chain C200 value.

| # | Column | TSV type/encoding |
| ---: | --- | --- |
| 1 | `evaluation_id` | String |
| 2 | `artifact_id` | String |
| 3 | `corpus_id` | String |
| 4 | `chain_id` | Int64 |
| 5 | `model_family` | String |
| 6 | `context_blocks` | Int64 |
| 7 | `horizon_blocks` | Int64 |
| 8 | `ordered_features` | compact JSON array of String |
| 9 | `classification_loss` | String |
| 10 | `training_first_parent_block` | Int64 |
| 11 | `training_last_parent_block` | Int64 |
| 12 | `training_origin_count` | Int64 |
| 13 | `training_examples_per_epoch` | Int64 |
| 14 | `training_minibatches_per_epoch` | Int64 |
| 15 | `training_optimizer_updates_per_epoch` | Int64 |
| 16 | `training_context_span_seconds_minimum` | Int64 |
| 17 | `training_context_span_seconds_median` | Float64 |
| 18 | `training_context_span_seconds_mean` | Float64 |
| 19 | `training_context_span_seconds_maximum` | Int64 |
| 20 | `validation_first_parent_block` | Int64 |
| 21 | `validation_last_parent_block` | Int64 |
| 22 | `validation_origin_count` | Int64 |
| 23 | `validation_context_span_seconds_minimum` | Int64 |
| 24 | `validation_context_span_seconds_median` | Float64 |
| 25 | `validation_context_span_seconds_mean` | Float64 |
| 26 | `validation_context_span_seconds_maximum` | Int64 |
| 27 | `testing_first_parent_block` | Int64 |
| 28 | `testing_last_parent_block` | Int64 |
| 29 | `testing_origin_count` | Int64 |
| 30 | `testing_context_span_seconds_minimum` | Int64 |
| 31 | `testing_context_span_seconds_median` | Float64 |
| 32 | `testing_context_span_seconds_mean` | Float64 |
| 33 | `testing_context_span_seconds_maximum` | Int64 |
| 34 | `earliest_hindsight_label_cross_entropy_loss` | Float64 |
| 35 | `earliest_hindsight_label_cross_entropy_loss_delta_vs_same_chain_c200` | Float64 |
| 36 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss` | Float64 |
| 37 | `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss_delta_vs_same_chain_c200` | Float64 |
| 38 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae` | Float64 |
| 39 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae_delta_vs_same_chain_c200` | Float64 |
| 40 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse` | Float64 |
| 41 | `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse_delta_vs_same_chain_c200` | Float64 |
| 42 | `multitask_total_loss` | Float64 |
| 43 | `multitask_total_loss_delta_vs_same_chain_c200` | Float64 |
| 44 | `earliest_hindsight_label_accuracy` | Float64 |
| 45 | `earliest_hindsight_label_accuracy_delta_vs_same_chain_c200` | Float64 |
| 46 | `earliest_hindsight_label_macro_f1` | Float64 |
| 47 | `earliest_hindsight_label_macro_f1_delta_vs_same_chain_c200` | Float64 |
| 48 | `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0` | Float64 |
| 49 | `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0_delta_vs_same_chain_c200` | Float64 |
| 50 | `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0` | Float64 |
| 51 | `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0_delta_vs_same_chain_c200` | Float64 |
| 52 | `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0` | Float64 |
| 53 | `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0_delta_vs_same_chain_c200` | Float64 |
| 54 | `signed_captured_hindsight_opportunity_ratio` | nullable Float64 |
| 55 | `signed_captured_hindsight_opportunity_ratio_delta_vs_same_chain_c200` | nullable Float64 |
| 56 | `mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0` | Float64 |
| 57 | `mean_origin_target_base_fee_per_gas_savings_fraction_vs_immediate_k0_delta_vs_same_chain_c200` | Float64 |
| 58 | `mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 59 | `mean_origin_selected_target_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_delta_vs_same_chain_c200` | Float64 |
| 60 | `mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k` | Float64 |
| 61 | `mean_origin_immediate_k0_base_fee_per_gas_increase_fraction_vs_hindsight_best_within_k_delta_vs_same_chain_c200` | Float64 |
| 62 | `harmful_action_rate` | Float64 |
| 63 | `harmful_action_rate_delta_vs_same_chain_c200` | Float64 |
| 64 | `mean_extra_wait_block_opportunities_vs_immediate_k0` | Float64 |
| 65 | `mean_extra_wait_block_opportunities_vs_immediate_k0_delta_vs_same_chain_c200` | Float64 |
| 66 | `mean_selected_action_wait_seconds` | Float64 |
| 67 | `mean_selected_action_wait_seconds_delta_vs_same_chain_c200` | Float64 |
| 68 | `mean_full_horizon_elapsed_seconds` | Float64 |
| 69 | `mean_full_horizon_elapsed_seconds_delta_vs_same_chain_c200` | Float64 |
| 70 | `final_k_horizon_blocks` | compact JSON array of Int64 |
| 71 | `final_k_artifact_ids` | compact JSON array of String |

Each `C`-row span covers `C-1` timestamp intervals.

### S18 primary K=5 fee-condition TSV

Owner: `experiments.k5_fee_conditions.write_k5_fee_condition_evidence`. Destination: caller-supplied absent path. Status: derived, noncanonical TSV. It writes 24 rows in exact caller-chain order: two descriptors × four quartile cells for each required input evaluation. Nulls are empty fields.

Only the active descriptor's cutpoints and median are populated. Empty cells have zero counts and Float64 sums, but null medians, ratios, and accuracy.

| # | Column | TSV type/encoding |
| ---: | --- | --- |
| 1 | `evaluation_id` | String |
| 2 | `artifact_id` | String |
| 3 | `corpus_id` | String |
| 4 | `chain_id` | Int64 |
| 5 | `first_parent_block` | Int64 |
| 6 | `last_parent_block` | Int64 |
| 7 | `horizon_blocks` | Int64, fixed K=5 by protocol |
| 8 | `descriptor` | String |
| 9 | `quartile` | Int64, 1–4 |
| 10 | `closed_parent_base_fee_per_gas_cutpoint_25` | nullable Int64 |
| 11 | `closed_parent_base_fee_per_gas_cutpoint_50` | nullable Int64 |
| 12 | `closed_parent_base_fee_per_gas_cutpoint_75` | nullable Int64 |
| 13 | `signed_one_block_base_fee_log_change_cutpoint_25` | nullable Float64 |
| 14 | `signed_one_block_base_fee_log_change_cutpoint_50` | nullable Float64 |
| 15 | `signed_one_block_base_fee_log_change_cutpoint_75` | nullable Float64 |
| 16 | `closed_parent_base_fee_per_gas_cell_median` | nullable Float64 |
| 17 | `signed_one_block_base_fee_log_change_cell_median` | nullable Float64 |
| 18 | `condition_origin_count` | Int64 |
| 19 | `earliest_hindsight_label_correct_count` | Int64 |
| 20 | `immediate_k0_base_fee_per_gas_sum` | Float64 |
| 21 | `finite_target_base_fee_per_gas_savings_sum` | Float64 |
| 22 | `finite_target_base_fee_per_gas_hindsight_opportunity_sum` | Float64 |
| 23 | `finite_target_base_fee_per_gas_hindsight_regret_sum` | Float64 |
| 24 | `finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0` | nullable Float64 |
| 25 | `finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0` | nullable Float64 |
| 26 | `finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0` | nullable Float64 |
| 27 | `earliest_hindsight_label_accuracy` | nullable Float64 |

The descriptors are closed-parent base fee per gas and signed `ln(fee_h/fee_h-1)`. Cutpoints use inverse-CDF indices `ceil(N/4)-1`, `ceil(N/2)-1`, and `ceil(3N/4)-1`; ties are never split, and duplicate cutpoints/empty cells remain. Raw Int64 `B/R/O` produces `S/G/Q` before Float64 casting. Counts recombine exactly; floating sums use the gamma-bound specified in the [theory](theory.md#k5-fee-conditions).
