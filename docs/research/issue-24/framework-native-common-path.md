# Issue 24: framework-native common path

Status: design candidate. It consumes the closed decisions in issues 10, 46, 47, 48, 21, 11, and 58, plus the retained task/head constraint owned by open sibling issue 23. It does not reopen them.

## Recommendation

Make historical preparation the one deep direct module. Make action geometry a tiny pure module shared by preparation, evaluation, historical inference, and serving. Let PyTorch's data stack own dataset indexing, collation, batching, shuffling, worker execution, and host-memory pinning. Keep device transfer in the training host, and keep model construction, loss/metrics, evaluation, artifacts, and serving as separate callers.

This is a clean break. There is no compiler selector, execution-policy selector, prediction selector, evaluator selector, runtime metadata codec, action mask, input mask, compatibility reader, or old/new mode.

The current stack pays for variation that the thesis no longer owns. `ProblemCompilerSpec` is a one-entry dispatch table (`src/spice/temporal/compilers/registry.py:35-40`, `:79-97`). `CompiledProblemContract` is a project abstract base implemented with `NotImplementedError` (`src/spice/temporal/contracts.py:31-77`). `CompiledProblemStore` carries variable timestamp-window geometry and repeated view helpers (`src/spice/temporal/problem_store.py:31-110`, `:138-200`). `CompiledExecutionPolicyContract` carries callable slots around one policy (`src/spice/temporal/execution_policy/base.py:152-173`, `:235-270`). None survives the fixed `C`, `K`, closed-parent, complete-outcome contract.

The dataset layer then repairs that generic geometry: it silently sorts and deduplicates sealed rows (`src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:31-38`), derives sequence length from seconds (`:41-70`), recompiles and resplits the store (`:244-322`), and reconstructs a delay-specific store for inference (`:325-376`). The representation layer pads variable contexts and copies masks row by row (`src/spice/modeling/representations/sequence_inputs.py:152-220`). The batch layer builds project protocols, a signature sorter, a custom sampler, and a custom collator around `DataLoader(range(...))` (`src/spice/modeling/batch_plan.py:33-68`, `:71-134`, `:237-274`). Fixed equal-length contexts remove the reason for all of it.

## Direct interface

`src/spice/temporal/preparation.py` should expose these owner functions and only small frozen values:

```python
@dataclass(frozen=True, slots=True)
class OriginRows:
    training: torch.LongTensor
    validation: torch.LongTensor
    testing: torch.LongTensor


@dataclass(frozen=True, slots=True)
class PreparationState:
    chain_id: int
    regime: str
    K: int
    feature_names: tuple[str, ...]
    feature_mean: torch.DoubleTensor
    feature_std: torch.DoubleTensor
    target_mean: float
    target_std: float
    training_start_block: int
    training_end_block: int
    training_count: int


@dataclass(frozen=True, slots=True)
class PreparedHistory:
    training: HistoricalDataset
    validation: HistoricalDataset
    testing: HistoricalDataset
    state: PreparationState


def compile_origins(rows: pl.DataFrame, definition: TrainingDefinition) -> OriginRows: ...

def fit_preparation(
    rows: pl.DataFrame,
    definition: TrainingDefinition,
    origins: OriginRows,
) -> PreparationState: ...

def prepare_history(
    rows: pl.DataFrame,
    definition: TrainingDefinition,
    origins: OriginRows,
    state: PreparationState,
) -> PreparedHistory: ...

def earliest_minimum(base_fees: torch.LongTensor, *, K: int) -> torch.LongTensor: ...
```

`compile_origins` returns row positions, not a generic store. It enforces the fixed issue-47 role/regime windows and the `h + K < B` purge. Each origin means one closed parent `h`; the context is exactly rows `h-C+1..h`; the outcomes are exactly `h+1..h+K`. An origin missing any context or outcome row is ineligible. It is never retained with a mask.

`fit_preparation` reads training origins only. It fits the issue-47 feature statistics and issue-58 target statistics in float64 and records the few facts needed to reject state reuse across a chain, regime, `K`, feature order, or training interval. `prepare_history` applies the exact saved state and exposes three concrete map-style datasets. It keeps one canonical raw integer fee vector plus aligned origin positions; it derives fixed `[K]` windows on access and computes labels in bounded chunks before any logarithm or floating conversion. `earliest_minimum` checks integer dtype, exact width `K`, positive fees, and nonempty rows, then returns `torch.argmin(base_fees, dim=1)` for each bounded window chunk. PyTorch specifies that `argmin` returns the first index when minima tie, so the required tie rule needs no custom loop or tolerance ([PyTorch `argmin`](https://docs.pytorch.org/docs/stable/generated/torch.argmin.html)).

`HistoricalDataset` is the only dataset class. It subclasses PyTorch's framework `Dataset`, not a project abstract base. It stores one scaled row tensor `[R, F]`, one raw fee vector `[R]`, origin positions `[N]`, labels `[N]`, standardized regression targets `[N]`, and origin block numbers `[N]`. `__getitem__` slices `features[p-C+1:p+1]` and `base_fees[p+1:p+1+K]`, then returns a plain mapping with `inputs`, `label`, `target`, `base_fees`, and `origin_block`. It materializes neither overlapping `[N, C, F]` contexts nor a persistent `[N, K]` fee matrix.

Callers use ordinary framework code:

```python
loader = DataLoader(
    prepared.training,
    batch_size=batch_size,
    shuffle=True,
    generator=generator,
    pin_memory=device.type == "cuda",
)
```

PyTorch defines map-style datasets through `__getitem__` and optional `__len__`; `DataLoader` derives sequential or shuffled sampling, and default collation adds the batch dimension while preserving mappings ([PyTorch data loading](https://docs.pytorch.org/docs/stable/data.html)). Since every input is `[C, F]` and every outcome is `[K]`, default collation can stack them. `torch.stack` requires equal shapes, which is now an invariant rather than something to repair ([PyTorch `stack`](https://docs.pytorch.org/docs/stable/generated/torch.stack.html)). `DataLoader` returns host batches; the training host owns transfer to its selected device. Add `__getitems__` only after profiling proves batched fetching matters; PyTorch documents it as an optional speed path, not required architecture.

`src/spice/temporal/actions.py` should contain the shared physical facts:

```python
def require_action(k: int, K: int) -> int: ...

def target_block(h: int, k: int, K: int) -> int:
    return h + 1 + require_action(k, K)

def broadcast_after_block(h: int, k: int, K: int) -> int:
    return h + require_action(k, K)
```

There is no action-space object and no action mask. `K` is fixed by the artifact; every `k in range(K)` is available. `k=0` has trigger block `h`, so it broadcasts immediately from the frozen `h/hash(h)` decision. `k>0` waits until `h+k` closes, then broadcasts the same prebuilt transaction once. Training labels, historical decoding, economic accounting, serving responses, and the mobile scheduler call these functions instead of restating arithmetic.

The prediction task stays separate. Its direct surface is `build_heads(hidden_width, K)`, `loss(outputs, batch, state)`, and `decode(logits)`. `decode` checks finite `[B, K]` logits and returns `torch.argmax(logits, dim=1)` as an ordinary `LongTensor`; PyTorch returns the first maximal index on a tie ([PyTorch `argmax`](https://docs.pytorch.org/docs/stable/generated/torch.argmax.html)). The retained classification and scalar regression heads remain issue-23/21 work. They do not justify a prediction family registry or decoded-result ABI.

Evaluation stays separate as one direct `evaluate_decisions(fee_rows, origins, actions, K, metadata)`. It requires one raw integer fee vector, integer aligned `[N]` origins and actions, complete model outputs, and all `N` eligible origins. It gathers the required `B`, `R`, and `O` facts from each origin's fixed future window and computes the issue-48 `S`, `G`, and `Q` arrays and summaries. It never recompiles geometry, samples replay windows, exponentiates logged fees, or realizes a policy through callbacks. Current accounting does those indirect steps (`src/spice/evaluation/temporal_accounting.py:34-146`), while current evaluator selection is another spec table (`src/spice/evaluation/registry.py:25-84`).

Serving gets a distinct `prepare_live(rows, artifact) -> LiveInput` in `src/spice/serving/inference.py`. Historical rows have future outcomes; live rows do not, so a mode flag would hide two algorithms. `prepare_live` requires exactly the support needed for feature warmup plus the final `C` consecutive closed rows, freezes `h/hash(h)`, applies the artifact's ordered feature formulas and scaler, and returns `[1, C, F]`. It never builds a fake `CompiledProblemStore`. The current serving path does exactly that and then synthesizes a seconds-derived mask (`src/spice/serving/inference.py:144-198`, `:211-221`); it also sorts and deduplicates input (`:201-208`), which must become a boundary error.

## Artifact boundary

Persist one concrete manifest plus a model state dict. The manifest carries direct facts: chain and regime identity, `C`, `K`, ordered feature names and formulas, feature scaler state and training provenance, target state and training provenance, concrete model inputs/hidden settings, fixed two-head outputs, corpus/role ranges, and training metadata. It carries no compiler ID, execution-policy ID, prediction/evaluator ID, slot spacing metadata, action-width duplicate, generic semantics bundle, or project-owned version marker.

Use one strict Pydantic model at the persistence boundary with `ConfigDict(extra="forbid", strict=True, frozen=True)` and `model_validate_json`. Pydantic otherwise coerces values and ignores extra fields by default; strict mode and forbidden extras make an obsolete or malformed shape fail at its first owner ([Pydantic models and extra data](https://docs.pydantic.dev/latest/concepts/models/), [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/)). Pydantic validates JSON structure, not tensor internals, so `load_training_artifact` must then validate cross-field facts and tensor shapes directly:

- `C > 0`, `K > 0`, unique ordered features, matching scaler widths, positive finite standard deviations, and exact training provenance.
- model input width equals feature count; classification output width equals `K`; regression output width is one.
- requested chain, regime, and serving `K` equal the artifact; serving never masks a larger artifact.
- state-dict keys and tensor shapes match the directly built model. `load_state_dict` already defaults to `strict=True`, requiring exact keys ([PyTorch `load_state_dict`](https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.load_state_dict)).

Keep `torch.load(..., weights_only=True)` from `src/spice/modeling/artifacts.py:73-78`. Remove the reconstruction through `compile_prediction_contract` at `:62-71`.

## Exact deletion and replacement map

| Delete or strip | Direct replacement |
|---|---|
| `src/spice/temporal/compilers/` | `temporal/preparation.py: compile_origins` |
| `src/spice/temporal/contracts.py`, `capability.py`, `problem_store.py`, `temporal/semantics.py` | `OriginRows`, `PreparationState`, `PreparedHistory`; direct `C` and `K` |
| `src/spice/temporal/execution_policy/` | `temporal/actions.py`; complete actions and raw fee matrix |
| Problem/execution/capability types in `src/spice/semantics.py:25-40`, `:55-81` | concrete manifest fields; no duplicated semantic projection |
| `src/spice/modeling/dataset_builders/` and `modeling/representations/sequence_inputs.py` | direct preparation plus one concrete `HistoricalDataset` |
| `src/spice/modeling/batch_plan.py` | standard `DataLoader(dataset, batch_size, shuffle, generator, workers, pin_memory)` plus training-host-owned device transfer |
| `src/spice/prediction/registry.py`, `base.py`, `contracts.py`, `decoded_offsets.py`, `decoding.py`, family compile bundle | direct retained task functions; plain tensors |
| `src/spice/evaluation/config.py`, `registry.py`, `contracts.py`, replay adapters/runners/results/catalog | one exhaustive direct scorer owned by issue 48 |
| `TemporalCapabilityPayload` and generic manifest dict codecs in `src/spice/storage/artifact_codecs.py:88-118`, `:165-262` | one strict concrete manifest model; no runtime metadata codec |
| capability/semantics echo fields in `TrainingArtifactManifest` (`src/spice/modeling/results.py:66-132`) | direct nonduplicated fields and fitted state |
| compiled contracts and seconds conversion in `src/spice/serving/runtime.py:24-55`, `:76-118` | loaded artifact, concrete model, exact support-row count |
| fake store, mask, and seconds allowance in `src/spice/serving/inference.py:144-221` | `prepare_live`, `decode`, and `temporal.actions` |

Retain provider/RPC code as concrete infrastructure. Loader worker count, pinning, device choice, RPC retry, and polling cadence are ephemeral runtime choices. They are not artifact capabilities or domain interfaces. A small caller may read an environment variable where the host is launched, but no `HostLoaderPolicy`, compiler metadata, or provider tuning value is persisted.

## Fail-closed checks

The sealed corpus loader is the only place allowed to establish canonical row order and uniqueness. Preparation checks and rejects; it never sorts, deduplicates, drops, fills, pads, truncates, or imputes. Errors use `ValueError` with the failing field, row/block, expected value, and actual value. Persistence keeps Pydantic's `ValidationError`; state-dict mismatch keeps PyTorch's `RuntimeError`. A project error hierarchy would add indirection without a caller that needs polymorphic recovery.

Historical preparation checks chain/regime containment, consecutive block numbers, monotone timestamps, required raw columns, exact role windows, `C` context, all `K` future rows, purge geometry, feature domains, finite transformed values, state provenance, and tensor shapes. It checks the label against raw integer fees before target transformation.

Live preparation additionally checks the selected artifact mapping, exact closed-head identity, unchanged `h/hash(h)` across preparation and response construction, exact `C`, ordered feature parity, and finite model outputs. A head change, reorg, missing row, stale snapshot, wrong artifact, or passed scheduling trigger fails the request. It never re-predicts, reschedules, or replaces the transaction.

## Lean tests

Delete tests whose subject disappears: `tests/temporal/test_observed_time_window.py`, `test_problem_store.py`, `test_temporal_capability.py`, `test_execution_policy_contract.py`, and `test_realization.py`; `tests/modeling/test_batch_plan.py`, `test_representations.py`, and the old `test_dataset_builders.py`; `tests/prediction/test_decoded_offsets.py`; `tests/evaluation/test_evaluators.py`, `test_temporal_replay.py`, and the old accounting tests; and the seconds-cap test in `tests/serving/test_inference.py`. They currently protect selector coercion, runtime metadata round-trips, variable masks/padding, custom worker policy, Poisson replay, and seconds conversion rather than the fixed contract (for examples, `tests/temporal/test_observed_time_window.py:42-65`, `:112-173`; `tests/modeling/test_batch_plan.py:108-213`; `tests/modeling/test_representations.py:52-83`; `tests/evaluation/test_evaluators.py:82-180`; `tests/serving/test_inference.py:6-21`).

Replace them with five focused tests:

1. One hand-written sealed corpus proves inclusive `C`, complete `K`, role purge, raw fee matrix, and earliest exact tie label.
2. One map-style dataset test proves default collation shapes `[B,C,F]`, `[B,K]`, `[B]` and deterministic generator-based shuffling.
3. One offline/live parity fixture proves the same frozen `h`, feature order, scaler, and model input.
4. One hand-computable evaluation fixture proves every origin is counted once and `S + Q = G` for every row.
5. One artifact/live boundary table covers wrong chain or `K`, scaler width, head width, missing row, and changed `h/hash(h)`; one scheduler test covers immediate `k=0` and exact one-shot `k>0` broadcast.

There should be no compatibility, migration, registry, codec-round-trip, old/new parity, or architecture-transition tests.

## Red team and ownership

The tempting smaller design is `TensorDataset` over a prebuilt `[N,C,F]` tensor. It is fewer lines but duplicates each row up to `C` times. At primary `C=200`, that is an avoidable memory multiplier. Persisting a second `[N,K]` fee matrix is smaller at the current `K`, but is also unnecessary because each window is a slice of the canonical fee vector. One concrete map-style dataset is the better deep module: it hides both slices and their alignment while standard `DataLoader` still owns batching.

The tempting generic design is a `PreparedBatch` dataclass shared by training, evaluation, and serving. Reject it. Training has labels and regression targets, historical evaluation has outcomes, and serving has neither. Combining them creates optional fields and illegal states. Share only immutable preparation state and action arithmetic.

The direct functions are worth keeping because deleting them would scatter the same causal geometry across training, evaluation, artifact inference, and serving. The registries are not: deleting them makes their complexity vanish because there is one owned task and one fixed contract. Future uncertainty quantification, adaptive decisions, Transformers, or hybrids should add a new seam only when approved work produces a second current caller.

Issue 24 owns these interfaces, their cross-caller use, the clean-break deletions, and boundary validation. It consumes without changing: issue 46 geometry/schedule/ties; issue 47 regimes/features/scaler/splits; issue 48 `K` grid and economic estimands; issue 21 loss/diagnostics; issue 23 retained task/heads; issue 58 target coordinate; issue 11 artifact identity/loading. Model architecture, trainer behavior, metric reporting details, RPC transport, and mobile presentation remain with their owners.
