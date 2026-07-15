"""DISPOSABLE PROTOTYPE: ordinary versus compact-source batch placement.

Question: does one shared compact CUDA row store with per-role gathering preserve the
approved Lightning/task semantics well enough to justify the Issue 40 L40 gate?

Synthetic/fake tensors only. This is not production code, CUDA evidence, training
evidence, an artifact ABI, a scientific choice, or a placement decision. Expanded
five-tensor residency remains only a rejected comparison.
"""

from __future__ import annotations

import importlib.util
import platform
import shutil
import statistics
import sys
import tempfile
import time
from collections.abc import Sized
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

import lightning.pytorch as pl
import torch
from torch.utils.data import DataLoader, Dataset


def _load_issue_26_fixture() -> Any:
    path = Path(__file__).parents[1] / "issue-26" / "task_fixture.py"
    spec = importlib.util.spec_from_file_location("_issue_26_task_fixture", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load approved synthetic task fixture from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TASK = _load_issue_26_fixture()

Family = Literal["lstm", "transformer", "transformer_lstm"]
MAPPING_KEYS = ("inputs", "label", "target", "base_fees", "origin_block")
SEED = 2026
SEMANTIC_BATCH_SIZE = 4
PRIMARY_CONTEXT = 200
CONTEXT_GRID = (50, 100, 200, 400)
PRIMARY_HORIZON = 5
FINAL_HORIZON_GRID = (2, 3, 4, 5, 10, 15, 30, 50, 100, 200)
PHYSICAL_BATCH_SIZE = 64
ACCUMULATE_GRAD_BATCHES = 1


def _load_issue_26_artifact_probe() -> Any:
    directory = Path(__file__).parents[1] / "issue-26"
    path = directory / "single_artifact_prototype.py"
    sys.path.insert(0, str(directory))
    try:
        spec = importlib.util.spec_from_file_location("_issue_26_artifact_probe", path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load approved native artifact probe from {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(directory))


@dataclass(frozen=True, slots=True)
class BatchTrace:
    mapping: dict[str, torch.Tensor]
    action_logits: torch.Tensor
    minimum_fee_z: torch.Tensor
    decoded_actions: torch.Tensor
    loss: torch.Tensor


@dataclass(frozen=True, slots=True)
class FitTrace:
    batches: tuple[BatchTrace, ...]
    final_state: dict[str, torch.Tensor]


@dataclass(frozen=True, slots=True)
class DenseRole:
    """Rejected comparison: one expanded mapping plus batched index_select."""

    tensors: dict[str, torch.Tensor]

    @classmethod
    def materialize(
        cls,
        dataset: Dataset[dict[str, torch.Tensor]],
        device: torch.device,
        *,
        simulate_oom: bool = False,
    ) -> DenseRole:
        if simulate_oom:
            raise torch.OutOfMemoryError("synthetic role-wide allocation failure")
        items = [dataset[index] for index in range(len(cast(Sized, dataset)))]
        tensors = {
            name: torch.stack([item[name] for item in items]).to(device)
            for name in MAPPING_KEYS
        }
        return cls(tensors=tensors)

    def gather(self, positions: list[int]) -> dict[str, torch.Tensor]:
        index = torch.tensor(positions, dtype=torch.int64, device=self.device)
        return {name: value.index_select(0, index) for name, value in self.tensors.items()}

    @property
    def device(self) -> torch.device:
        return self.tensors["inputs"].device

    @property
    def sample_count(self) -> int:
        return int(self.tensors["inputs"].shape[0])

    @property
    def tensor_bytes(self) -> int:
        return _mapping_bytes(self.tensors)


class _PlacementFit(pl.LightningModule):
    """One automatic-optimization step owner; placement stays outside the task."""

    def __init__(
        self,
        definition: object,
        classification: object,
        initial_state: dict[str, torch.Tensor],
    ) -> None:
        super().__init__()
        self.model = TASK.build_frozen_model(definition)
        self.model.load_state_dict(initial_state, strict=True)
        self.classification = classification
        self.trace: list[BatchTrace] = []

    def training_step(
        self,
        batch: dict[str, torch.Tensor],
        batch_idx: int,
    ) -> torch.Tensor:
        del batch_idx
        devices = {value.device for value in batch.values()}
        if devices != {batch["inputs"].device}:
            raise RuntimeError("Lightning must place the complete five-tensor mapping together")
        output = self.model(batch["inputs"])
        loss = TASK.batch_loss(output, batch, self.classification)
        if not bool(torch.isfinite(loss)):
            raise FloatingPointError("training loss must be finite")
        self.trace.append(
            BatchTrace(
                mapping={
                    name: batch[name].detach().cpu().clone() for name in MAPPING_KEYS
                },
                action_logits=output.action_logits.detach().cpu().clone(),
                minimum_fee_z=output.minimum_fee_z.detach().cpu().clone(),
                decoded_actions=output.action_logits.argmax(dim=-1).detach().cpu().clone(),
                loss=loss.detach().cpu().clone(),
            )
        )
        return loss

    def configure_gradient_clipping(
        self,
        optimizer: torch.optim.Optimizer,
        gradient_clip_val: float | None = None,
        gradient_clip_algorithm: str | None = None,
    ) -> None:
        del optimizer, gradient_clip_algorithm
        torch.nn.utils.clip_grad_norm_(
            self.model.parameters(),
            max_norm=cast(float, gradient_clip_val),
            error_if_nonfinite=True,
        )

    def configure_optimizers(self) -> torch.optim.Optimizer:
        return torch.optim.AdamW(self.model.parameters(), lr=1e-3, weight_decay=0.0)


@dataclass(frozen=True, slots=True)
class _FakeSource:
    """Compact prepared rows shared by the training and validation roles."""

    rows: torch.Tensor
    fees: torch.Tensor
    blocks: torch.Tensor

    @classmethod
    def build(cls, row_count: int, input_width: int) -> _FakeSource:
        generator = torch.Generator().manual_seed(5102)
        return cls(
            rows=torch.randn(row_count, input_width, generator=generator),
            fees=torch.randint(
                1_000_000,
                2_000_000,
                (row_count,),
                generator=generator,
                dtype=torch.int64,
            ),
            blocks=torch.arange(10_000, 10_000 + row_count, dtype=torch.int64),
        )


class _FakeHistoricalDataset(Dataset[dict[str, torch.Tensor]]):
    """Shape-accurate lazy CPU role over one compact prepared source."""

    def __init__(
        self,
        *,
        sample_count: int,
        context_blocks: int,
        input_width: int,
        horizon: int,
        source: _FakeSource | None = None,
        origin_start: int | None = None,
    ) -> None:
        first_origin = context_blocks - 1 if origin_start is None else origin_start
        if source is None:
            source = _FakeSource.build(
                first_origin + sample_count + horizon,
                input_width,
            )
        if int(source.rows.shape[1]) != input_width:
            raise ValueError("fake source width must match the role")
        if first_origin - context_blocks + 1 < 0:
            raise ValueError("fake role lacks complete past context")
        if first_origin + sample_count + horizon > int(source.rows.shape[0]):
            raise ValueError("fake role lacks complete future outcomes")
        self._source = source
        self._rows = source.rows
        self._fees = source.fees
        self._blocks = source.blocks
        self._origins = torch.arange(
            first_origin,
            first_origin + sample_count,
            dtype=torch.int64,
        )
        self._labels = torch.remainder(torch.arange(sample_count), horizon).to(torch.int64)
        self._targets = torch.linspace(-1.0, 1.0, sample_count, dtype=torch.float32)
        self._context_blocks = context_blocks
        self._horizon = horizon

    def __len__(self) -> int:
        return int(self._origins.numel())

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        origin = int(self._origins[index])
        return {
            "inputs": self._rows[
                origin - self._context_blocks + 1 : origin + 1
            ].clone(),
            "label": self._labels[index].clone(),
            "target": self._targets[index].clone(),
            "base_fees": self._fees[
                origin + 1 : origin + 1 + self._horizon
            ].clone(),
            "origin_block": self._blocks[origin].clone(),
        }


@dataclass(frozen=True, slots=True)
class _FakePrepared:
    """Two fake fit roles sharing the same compact source rows."""

    source: _FakeSource
    training: _FakeHistoricalDataset
    validation: _FakeHistoricalDataset

    @classmethod
    def build(
        cls,
        *,
        training_count: int,
        validation_count: int,
        context_blocks: int,
        input_width: int,
        horizon: int,
    ) -> _FakePrepared:
        training_start = context_blocks - 1
        validation_start = training_start + training_count + horizon
        source = _FakeSource.build(
            validation_start + validation_count + horizon,
            input_width,
        )
        return cls(
            source=source,
            training=_FakeHistoricalDataset(
                sample_count=training_count,
                context_blocks=context_blocks,
                input_width=input_width,
                horizon=horizon,
                source=source,
                origin_start=training_start,
            ),
            validation=_FakeHistoricalDataset(
                sample_count=validation_count,
                context_blocks=context_blocks,
                input_width=input_width,
                horizon=horizon,
                source=source,
                origin_start=validation_start,
            ),
        )


@dataclass(frozen=True, slots=True)
class CompactSource:
    """One fit-scoped CUDA row store shared by both role gather owners."""

    rows: torch.Tensor
    fees: torch.Tensor
    blocks: torch.Tensor

    @classmethod
    def materialize(
        cls,
        source: _FakeSource,
        device: torch.device,
        *,
        simulate_oom: bool = False,
    ) -> CompactSource:
        if simulate_oom:
            raise torch.OutOfMemoryError("synthetic compact-source allocation failure")
        return cls(
            rows=source.rows.to(device),
            fees=source.fees.to(device),
            blocks=source.blocks.to(device),
        )

    @property
    def tensor_bytes(self) -> int:
        return sum(
            value.numel() * value.element_size()
            for value in (self.rows, self.fees, self.blocks)
        )


@dataclass(frozen=True, slots=True)
class CompactRole:
    """One role's zero-storage views and minimal per-origin CUDA state."""

    source: CompactSource
    history_windows: torch.Tensor
    fee_windows: torch.Tensor
    origins: torch.Tensor
    labels: torch.Tensor
    targets: torch.Tensor
    context_blocks: int

    @classmethod
    def from_dataset(
        cls,
        dataset: _FakeHistoricalDataset,
        source: CompactSource,
    ) -> CompactRole:
        return cls(
            source=source,
            history_windows=source.rows.unfold(
                0, dataset._context_blocks, 1
            ).transpose(1, 2),
            fee_windows=source.fees.unfold(0, dataset._horizon, 1),
            origins=dataset._origins.to(source.rows.device),
            labels=dataset._labels.to(source.rows.device),
            targets=dataset._targets.to(source.rows.device),
            context_blocks=dataset._context_blocks,
        )

    def gather(self, positions: list[int]) -> dict[str, torch.Tensor]:
        index = torch.tensor(positions, dtype=torch.int64, device=self.device)
        origins = self.origins.index_select(0, index)
        return {
            "inputs": self.history_windows.index_select(
                0, origins - self.context_blocks + 1
            ),
            "label": self.labels.index_select(0, index),
            "target": self.targets.index_select(0, index),
            "base_fees": self.fee_windows.index_select(0, origins + 1),
            "origin_block": self.source.blocks.index_select(0, origins),
        }

    @property
    def device(self) -> torch.device:
        return self.source.rows.device

    @property
    def sample_count(self) -> int:
        return int(self.labels.numel())

    @property
    def tensor_bytes(self) -> int:
        return self.source.tensor_bytes + self.role_tensor_bytes

    @property
    def role_tensor_bytes(self) -> int:
        return (
            self.origins.numel() * self.origins.element_size()
            + self.labels.numel() * self.labels.element_size()
            + self.targets.numel() * self.targets.element_size()
        )


def _ordinary_loader(
    dataset: Dataset[dict[str, torch.Tensor]],
    *,
    batch_size: int,
    shuffle: bool,
) -> DataLoader[dict[str, torch.Tensor]]:
    generator = torch.Generator().manual_seed(SEED) if shuffle else None
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
        pin_memory=False,
        drop_last=False,
    )


def _resident_loader(
    role: DenseRole | CompactRole,
    *,
    batch_size: int,
    shuffle: bool,
) -> DataLoader[dict[str, torch.Tensor]]:
    generator = torch.Generator().manual_seed(SEED) if shuffle else None
    return cast(
        DataLoader[dict[str, torch.Tensor]],
        DataLoader(
            cast(Dataset[int], range(role.sample_count)),
            batch_size=batch_size,
            shuffle=shuffle,
            generator=generator,
            collate_fn=role.gather,
            num_workers=0,
        ),
    )


def _resident_fit_loaders(
    prepared: _FakePrepared,
    device: torch.device,
) -> tuple[
    DataLoader[dict[str, torch.Tensor]],
    DataLoader[dict[str, torch.Tensor]],
]:
    """Prototype the complete private seam with one source shared by both roles."""

    source = CompactSource.materialize(prepared.source, device)
    training = CompactRole.from_dataset(prepared.training, source)
    validation = CompactRole.from_dataset(prepared.validation, source)
    return (
        _resident_loader(
            training,
            batch_size=PHYSICAL_BATCH_SIZE,
            shuffle=True,
        ),
        _resident_loader(
            validation,
            batch_size=PHYSICAL_BATCH_SIZE,
            shuffle=False,
        ),
    )


def _compact_role(
    dataset: _FakeHistoricalDataset,
    device: torch.device,
) -> CompactRole:
    source = CompactSource.materialize(dataset._source, device)
    return CompactRole.from_dataset(dataset, source)


def _initial_state(family: Family) -> dict[str, torch.Tensor]:
    pl.seed_everything(SEED, workers=True, verbose=False)
    model = TASK.build_frozen_model(TASK.model_definition(family))
    return {
        name: value.detach().cpu().clone() for name, value in model.state_dict().items()
    }


def _fit_once(
    family: Family,
    classification: object,
    initial_state: dict[str, torch.Tensor],
    loader: DataLoader[dict[str, torch.Tensor]],
) -> FitTrace:
    pl.seed_everything(SEED, workers=True, verbose=False)
    module = _PlacementFit(TASK.model_definition(family), classification, initial_state)
    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        precision="32-true",
        max_epochs=1,
        logger=False,
        enable_checkpointing=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        num_sanity_val_steps=0,
        limit_val_batches=0,
        gradient_clip_val=TASK.CLIP_NORM,
        gradient_clip_algorithm="norm",
        accumulate_grad_batches=ACCUMULATE_GRAD_BATCHES,
        deterministic=True,
    )
    trainer.fit(module, train_dataloaders=loader)
    return FitTrace(
        batches=tuple(module.trace),
        final_state={
            name: value.detach().cpu().clone()
            for name, value in module.model.state_dict().items()
        },
    )


def _assert_trace_equal(left: FitTrace, right: FitTrace) -> None:
    if len(left.batches) != len(right.batches):
        raise AssertionError("placements produced different batch counts")
    for left_batch, right_batch in zip(left.batches, right.batches, strict=True):
        for name in MAPPING_KEYS:
            if not torch.equal(left_batch.mapping[name], right_batch.mapping[name]):
                raise AssertionError(f"placements changed prepared field {name}")
        for left_value, right_value, label in (
            (left_batch.action_logits, right_batch.action_logits, "action_logits"),
            (left_batch.minimum_fee_z, right_batch.minimum_fee_z, "minimum_fee_z"),
            (left_batch.decoded_actions, right_batch.decoded_actions, "decoded_actions"),
            (left_batch.loss, right_batch.loss, "loss"),
        ):
            if not torch.equal(left_value, right_value):
                raise AssertionError(f"placements changed {label}")
    for name in left.final_state:
        if not torch.equal(left.final_state[name], right.final_state[name]):
            raise AssertionError(f"placements changed final parameter {name}")


def _max_state_delta(left: FitTrace, right: FitTrace) -> float:
    return max(
        float((left.final_state[name] - right.final_state[name]).abs().max())
        for name in left.final_state
    )


def _family_observation(family: Family) -> dict[str, object]:
    task = TASK.frozen_task()
    dataset = _FakeHistoricalDataset(
        sample_count=5,
        context_blocks=TASK.CONTEXT_BLOCKS,
        input_width=TASK.INPUT_WIDTH,
        horizon=TASK.HORIZON,
    )
    initial_state = _initial_state(family)
    ordinary = _fit_once(
        family,
        task.classification,
        initial_state,
        _ordinary_loader(dataset, batch_size=SEMANTIC_BATCH_SIZE, shuffle=True),
    )
    dense = DenseRole.materialize(dataset, torch.device("cpu"))
    expanded = _fit_once(
        family,
        task.classification,
        initial_state,
        _resident_loader(dense, batch_size=SEMANTIC_BATCH_SIZE, shuffle=True),
    )
    compact = _compact_role(dataset, torch.device("cpu"))
    compact_fit = _fit_once(
        family,
        task.classification,
        initial_state,
        _resident_loader(compact, batch_size=SEMANTIC_BATCH_SIZE, shuffle=True),
    )
    compact_repeat = _fit_once(
        family,
        task.classification,
        initial_state,
        _resident_loader(compact, batch_size=SEMANTIC_BATCH_SIZE, shuffle=True),
    )
    _assert_trace_equal(ordinary, expanded)
    _assert_trace_equal(ordinary, compact_fit)
    _assert_trace_equal(compact_fit, compact_repeat)
    return {
        "fixture_shape": {
            "C": TASK.CONTEXT_BLOCKS,
            "F": TASK.INPUT_WIDTH,
            "K": TASK.HORIZON,
            "B": SEMANTIC_BATCH_SIZE,
            "accumulate_grad_batches": ACCUMULATE_GRAD_BATCHES,
            "scope": "micro semantic fixture; not a scientific host shape",
        },
        "batch_sizes": [int(batch.mapping["label"].numel()) for batch in ordinary.batches],
        "origin_order": [
            int(value)
            for batch in ordinary.batches
            for value in batch.mapping["origin_block"].tolist()
        ],
        "all_five_mapping_tensors_equal": True,
        "action_logits_max_abs_delta": 0.0,
        "minimum_fee_z_max_abs_delta": 0.0,
        "loss_max_abs_delta": 0.0,
        "decoded_actions_equal": True,
        "expanded_final_weight_max_abs_delta": _max_state_delta(ordinary, expanded),
        "compact_final_weight_max_abs_delta": _max_state_delta(ordinary, compact_fit),
        "compact_repeat_exact": True,
        "automatic_optimization_updates": len(ordinary.batches),
    }


def _mapping_bytes(mapping: dict[str, torch.Tensor]) -> int:
    return sum(value.numel() * value.element_size() for value in mapping.values())


def _measure_epoch(loader: DataLoader[dict[str, torch.Tensor]], repeats: int = 3) -> float:
    durations: list[float] = []
    for _ in range(repeats):
        started = time.perf_counter()
        observed = 0.0
        for batch in loader:
            observed += float(batch["inputs"][0, 0, 0])
        if not torch.isfinite(torch.tensor(observed)):
            raise RuntimeError("timing traversal produced a nonfinite sink")
        durations.append(time.perf_counter() - started)
    return statistics.median(durations)


def _assert_loader_equal(
    reference: DataLoader[dict[str, torch.Tensor]],
    candidate: DataLoader[dict[str, torch.Tensor]],
) -> None:
    reference_batches = tuple(reference)
    candidate_batches = tuple(candidate)
    if len(reference_batches) != len(candidate_batches):
        raise AssertionError("placements produced different data-only batch counts")
    for expected, observed in zip(reference_batches, candidate_batches, strict=True):
        for name in MAPPING_KEYS:
            if not torch.equal(expected[name], observed[name]):
                raise AssertionError(f"placements changed shape-accurate {name}")


def _bound_compact_role(
    loader: DataLoader[dict[str, torch.Tensor]],
) -> CompactRole:
    role = getattr(loader.collate_fn, "__self__", None)
    if not isinstance(role, CompactRole):
        raise AssertionError("resident loader must bind exactly one CompactRole.gather")
    return role


def _shared_fit_loader_observation() -> dict[str, object]:
    prepared = _FakePrepared.build(
        training_count=65,
        validation_count=65,
        context_blocks=PRIMARY_CONTEXT,
        input_width=6,
        horizon=PRIMARY_HORIZON,
    )
    training, validation = _resident_fit_loaders(prepared, torch.device("cpu"))
    _assert_loader_equal(
        _ordinary_loader(
            prepared.training,
            batch_size=PHYSICAL_BATCH_SIZE,
            shuffle=True,
        ),
        training,
    )
    _assert_loader_equal(
        _ordinary_loader(
            prepared.validation,
            batch_size=PHYSICAL_BATCH_SIZE,
            shuffle=False,
        ),
        validation,
    )
    training_role = _bound_compact_role(training)
    validation_role = _bound_compact_role(validation)
    if training_role.source is not validation_role.source:
        raise AssertionError("fit roles duplicated the compact CUDA source")
    return {
        "interface": "_resident_fit_loaders(prepared, device) -> (train, validation)",
        "shape": {
            "C": PRIMARY_CONTEXT,
            "F": 6,
            "K": PRIMARY_HORIZON,
            "B": PHYSICAL_BATCH_SIZE,
            "accumulate_grad_batches": ACCUMULATE_GRAD_BATCHES,
            "scope": "fake full/tail seam fixture",
        },
        "training_batch_sizes": [64, 1],
        "validation_batch_sizes": [64, 1],
        "all_five_mapping_tensors_equal": True,
        "one_shared_source": True,
        "source_bytes_counted_once": training_role.source.tensor_bytes,
        "training_role_bytes": training_role.role_tensor_bytes,
        "validation_role_bytes": validation_role.role_tensor_bytes,
        "pin_memory_argument": "omitted",
        "drop_last_argument": "omitted; DataLoader default false",
        "num_workers": 0,
    }


def _local_timing() -> dict[str, object]:
    sample_count = 4_097
    batch_size = PHYSICAL_BATCH_SIZE
    dataset = _FakeHistoricalDataset(
        sample_count=sample_count,
        context_blocks=max(CONTEXT_GRID),
        input_width=6,
        horizon=max(FINAL_HORIZON_GRID),
    )
    ordinary = _ordinary_loader(dataset, batch_size=batch_size, shuffle=False)
    setup_started = time.perf_counter()
    role = DenseRole.materialize(dataset, torch.device("cpu"))
    resident_setup = time.perf_counter() - setup_started
    resident = _resident_loader(role, batch_size=batch_size, shuffle=False)
    compact_setup_started = time.perf_counter()
    compact_role = _compact_role(dataset, torch.device("cpu"))
    compact_setup = time.perf_counter() - compact_setup_started
    compact = _resident_loader(compact_role, batch_size=batch_size, shuffle=False)
    _assert_loader_equal(
        _ordinary_loader(dataset, batch_size=batch_size, shuffle=False),
        _resident_loader(role, batch_size=batch_size, shuffle=False),
    )
    _assert_loader_equal(
        _ordinary_loader(dataset, batch_size=batch_size, shuffle=False),
        _resident_loader(compact_role, batch_size=batch_size, shuffle=False),
    )
    ordinary_seconds = _measure_epoch(ordinary)
    resident_seconds = _measure_epoch(resident)
    compact_seconds = _measure_epoch(compact)
    return {
        "scope": (
            "local CPU data-path maximum-axis envelope only; C400/K200 is not "
            "an approved Cartesian science cell or CUDA/model throughput evidence"
        ),
        "shape": {
            "N": sample_count,
            "C": max(CONTEXT_GRID),
            "F": 6,
            "K": max(FINAL_HORIZON_GRID),
            "B": batch_size,
        },
        "host_accumulate_grad_batches": ACCUMULATE_GRAD_BATCHES,
        "all_five_mapping_tensors_equal": True,
        "tail_batch": sample_count % batch_size,
        "resident_materialization_ms": resident_setup * 1_000.0,
        "ordinary_epoch_ms": ordinary_seconds * 1_000.0,
        "resident_epoch_ms": resident_seconds * 1_000.0,
        "compact_materialization_ms": compact_setup * 1_000.0,
        "compact_epoch_ms": compact_seconds * 1_000.0,
        "ordinary_samples_per_second": sample_count / ordinary_seconds,
        "resident_samples_per_second": sample_count / resident_seconds,
        "compact_samples_per_second": sample_count / compact_seconds,
        "resident_tensor_bytes": role.tensor_bytes,
        "compact_tensor_bytes": compact_role.tensor_bytes,
        "cuda_timing_available": False,
        "peak_cuda_memory_available": False,
    }


def _dense_bytes(sample_count: int, context: int, width: int, horizon: int) -> int:
    # Five approved tensors: float32 inputs/target, int64 label/fees/origin.
    return sample_count * (4 * context * width + 4 + 8 + 8 * horizon + 8)


def _polygon_workload_memory() -> dict[str, object]:
    width = 6
    batch_size = PHYSICAL_BATCH_SIZE
    estimated_validation_span = 308_848
    shared_row_count = 3_576_915
    shapes = (
        (
            "primary",
            PRIMARY_CONTEXT,
            PRIMARY_HORIZON,
            3_267_668,
            308_648,
            "common origins with complete Kmax=200 support",
        ),
        (
            "descriptive_context_max",
            max(CONTEXT_GRID),
            PRIMARY_HORIZON,
            3_267_663,
            308_843,
            "natural C400/K5 eligibility inside the frozen roles",
        ),
        (
            "final_horizon_max",
            PRIMARY_CONTEXT,
            max(FINAL_HORIZON_GRID),
            3_267_668,
            308_648,
            "common C200 origins with complete Kmax=200 support",
        ),
    )
    observations: list[dict[str, object]] = []
    for name, context, horizon, training_count, validation_count, origin_rule in shapes:
        sample_count = training_count + validation_count
        expanded = _dense_bytes(sample_count, context, width, horizon)
        compact = (
            shared_row_count * (4 * width + 8 + 8)
            + sample_count * (8 + 8 + 4)
        )
        batch = _dense_bytes(batch_size, context, width, horizon)
        observations.append(
            {
                "name": name,
                "shape": {
                    "C": context,
                    "F": width,
                    "K": horizon,
                    "B": batch_size,
                    "accumulate_grad_batches": ACCUMULATE_GRAD_BATCHES,
                    "N_train": training_count,
                    "N_validation": validation_count,
                    "R_shared": shared_row_count,
                },
                "origin_rule": origin_rule,
                "tails": {
                    "training": training_count % batch_size,
                    "validation": validation_count % batch_size,
                },
                "expanded_rejected_bytes": expanded,
                "expanded_rejected_GiB": expanded / 1024**3,
                "compact_bytes": compact,
                "compact_MiB": compact / 1024**2,
                "batch_bytes": batch,
                "batch_MiB": batch / 1024**2,
            }
        )
    return {
        "scope": (
            "Polygon planning counts for the actual approved workload axes; "
            "expanded residency is rejected"
        ),
        "validation_count_is_estimated": True,
        "estimated_validation_span_rows": estimated_validation_span,
        "each_extra_validation_row_compact_bytes": 60,
        "shapes": observations,
        "actual_cuda_headroom_known": False,
    }


def _oom_observation() -> dict[str, object]:
    task = TASK.frozen_task()
    try:
        DenseRole.materialize(
            task.training,
            torch.device("cpu"),
            simulate_oom=True,
        )
    except torch.OutOfMemoryError as error:
        dense = {
            "candidate_allocation_error": f"{type(error).__name__}: {error}",
            "propagates": True,
            "fallback": False,
            "ordinary_path_selected_implicitly": False,
        }
    else:
        raise AssertionError("simulated role-wide allocation failure did not propagate")
    try:
        dataset = _FakeHistoricalDataset(
            sample_count=5,
            context_blocks=TASK.CONTEXT_BLOCKS,
            input_width=TASK.INPUT_WIDTH,
            horizon=TASK.HORIZON,
        )
        CompactSource.materialize(
            dataset._source,
            torch.device("cpu"),
            simulate_oom=True,
        )
    except torch.OutOfMemoryError as error:
        compact = {
            "candidate_allocation_error": f"{type(error).__name__}: {error}",
            "propagates": True,
            "fallback": False,
            "ordinary_path_selected_implicitly": False,
        }
    else:
        raise AssertionError("simulated compact-source allocation failure did not propagate")
    return {"expanded": dense, "compact": compact}


def _artifact_portability() -> dict[str, object]:
    native = _load_issue_26_artifact_probe()
    family: Family = "lstm"
    artifact_id = native.ARTIFACT_IDS[family]
    with tempfile.TemporaryDirectory(prefix="spice-issue-56-transfer-") as raw_root:
        root = Path(raw_root)
        producer = root / "producer"
        consumer = root / "consumer"
        native.train_and_publish(family, producer)
        source = native.artifact_path(producer, artifact_id)
        destination = native.artifact_path(consumer, artifact_id)
        destination.parent.mkdir(parents=True)
        shutil.copyfile(source, destination)
        observation = native._consumer_probe(consumer, family)
    return {
        "transfer": "ordinary file copy to a separate root; no manifest or receipt",
        "consumer_host": platform.system(),
        "native_loader": (
            "FitModule.load_from_checkpoint(map_location='cpu', "
            "weights_only=True, strict=True)"
        ),
        "family": observation["family"],
        "validation_batch_sizes": observation["validation_batch_sizes"],
        "placement_fields_added": 0,
        "custom_abi_added": False,
        "accepted_all_family_evidence": "Issue 26 native artifact probe",
    }


def run_all() -> dict[str, object]:
    return {
        "question": (
            "Does the owner-authorized compact-source candidate earn final placement "
            "consideration after Issue 40's L40 evidence?"
        ),
        "owner_decision": {
            "issue_40_candidate": "compact-source only",
            "expanded_five_tensor_residency": "rejected",
            "ordinary_path_remains_approved": True,
            "integration_authorized": False,
            "real_execution_authorized": False,
        },
        "scientific_shape_authority": {
            "primary_context": PRIMARY_CONTEXT,
            "descriptive_context_grid": list(CONTEXT_GRID),
            "primary_horizon": PRIMARY_HORIZON,
            "final_horizon_grid": list(FINAL_HORIZON_GRID),
            "physical_batch_size": PHYSICAL_BATCH_SIZE,
            "accumulate_grad_batches": ACCUMULATE_GRAD_BATCHES,
            "placement_selects_science": False,
            "approved_boundary_cells": [
                {"C": max(CONTEXT_GRID), "K": PRIMARY_HORIZON},
                {"C": PRIMARY_CONTEXT, "K": max(FINAL_HORIZON_GRID)},
            ],
        },
        "budget": {
            "data": "synthetic/fake only",
            "device": "local CPU",
            "candidate_count": "one Issue 40 challenger: compact-source",
            "expanded_scope": "rejected comparison only",
            "stop": "full/tail + one-update semantics, bounded timing/sizing, fail behavior",
        },
        "semantics": {
            family: _family_observation(family)
            for family in ("lstm", "transformer", "transformer_lstm")
        },
        "shared_fit_loader_seam": _shared_fit_loader_observation(),
        "failure": _oom_observation(),
        "local_timing": _local_timing(),
        "polygon_workload_memory": _polygon_workload_memory(),
        "surface": {
            "ordinary": [
                "HistoricalDataset",
                "ordinary DataLoader/default collation",
                "pin_memory=True on L40",
                "Lightning native recursive whole-batch transfer",
            ],
            "expanded_rejected_adds": [
                "expanded role-wide device materialization",
                "index-only DataLoader with custom collate",
                "five index_select allocations per batch",
                "device-resident train/validation lifetime and VRAM budgeting",
                "fail-loud role-allocation boundary",
            ],
            "compact_candidate_adds": [
                "shared compact device rows and raw fees",
                "per-role device origins, labels, and targets",
                "index-only DataLoader with one GPU collate owner",
                "zero-copy sliding-window views and device index_select gathers",
                "fail-loud source/gather/model allocation boundaries",
            ],
            "num_workers": 0,
            "pin_memory_argument": "omitted",
            "drop_last_argument": "omitted; default false",
            "candidate_config_fields": 0,
            "candidate_fallbacks": 0,
            "execution_only_branch": False,
        },
        "artifact": _artifact_portability(),
        "checks": "pass",
    }
