"""DISPOSABLE PROTOTYPE: frozen synthetic Min-Block-Fee fit fixture.

Question: can direct PyTorch and Lightning automatic optimization implement the same
complete fit lifecycle without changing the approved task, model, or DataLoader seams?

Synthetic tensors only. This is not production code or scientific evidence.
Historical FitResult/component types below support the superseded host comparison only;
the approved interface and native artifact are frozen in decision-contract.md.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeAlias, cast

import torch
from torch.utils.data import Dataset


def _load_issue_23_task() -> object:
    path = Path(__file__).parents[1] / "issue-23" / "prototype_task.py"
    spec = importlib.util.spec_from_file_location("_issue_23_prototype_task", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load frozen Issue 23 prototype from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TASK = _load_issue_23_task()

HistoricalBatch = TASK.HistoricalBatch
LstmDefinition = TASK.LstmDefinition
TransformerDefinition = TASK.TransformerDefinition
TransformerLstmDefinition = TASK.TransformerLstmDefinition
ModelDefinition = TASK.ModelDefinition
ConcreteModel = TASK.ConcreteModel
ClassificationLossState = TASK.ClassificationLossState
MinBlockFeeOutput = TASK.MinBlockFeeOutput
build_model = TASK.build_model
min_block_fee_loss = TASK.min_block_fee_loss

Family: TypeAlias = Literal["lstm", "transformer", "transformer_lstm"]
StopReason: TypeAlias = Literal["patience", "max_epochs"]

SEED = 2026
CONTEXT_BLOCKS = 4
INPUT_WIDTH = 3
HORIZON = 3
TRAIN_BATCH_SIZE = 4
VALIDATION_BATCH_SIZE = 2
MAX_EPOCHS = 36
PATIENCE = 8
CLIP_NORM = 1.0


@dataclass(frozen=True, slots=True)
class FitResult:
    best_state_dict: dict[str, torch.Tensor]
    best_validation: ValidationTotals
    earliest_best_epoch: int
    completed_epochs: int
    stop_reason: StopReason
    optimization_examples: int
    minibatches: int
    optimizer_updates: int


@dataclass(frozen=True, slots=True)
class CandidateSuccess:
    method: str
    total_loss: float
    earliest_best_epoch: int
    completed_epochs: int


@dataclass(frozen=True, slots=True)
class ValidationTotals:
    sample_count: int
    classification_sum: float
    regression_sum: float

    @property
    def total_loss(self) -> float:
        return (self.classification_sum + self.regression_sum) / self.sample_count


class CompleteValidationLoss:
    """One additive float64 accumulator for the fit/HPO selection objective."""

    def __init__(self) -> None:
        self._sums: tuple[torch.Tensor, torch.Tensor] | None = None
        self._sample_count = 0

    def update(
        self,
        classification_terms: torch.Tensor,
        regression_terms: torch.Tensor,
    ) -> None:
        classification_sum = classification_terms.detach().to(torch.float64).sum()
        regression_sum = regression_terms.detach().to(torch.float64).sum()
        if self._sums is None:
            self._sums = classification_sum, regression_sum
        else:
            self._sums = (
                self._sums[0] + classification_sum,
                self._sums[1] + regression_sum,
            )
        self._sample_count += int(classification_terms.numel())

    def finalize(self, expected_sample_count: int) -> tuple[ValidationTotals, torch.Tensor]:
        if (
            expected_sample_count <= 0
            or self._sample_count != expected_sample_count
            or self._sums is None
        ):
            raise RuntimeError("complete validation must observe every sample exactly once")
        classification_sum, regression_sum = self._sums
        total = (classification_sum + regression_sum) / self._sample_count
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("complete validation total_loss must be finite")
        totals = ValidationTotals(
            sample_count=self._sample_count,
            classification_sum=float(classification_sum.detach().cpu()),
            regression_sum=float(regression_sum.detach().cpu()),
        )
        return totals, total


@dataclass(frozen=True, slots=True)
class FrozenTask:
    training: TensorMapDataset
    invalid_training: TensorMapDataset
    validation: TensorMapDataset
    invalid_validation: TensorMapDataset
    classification: object


class TensorMapDataset(Dataset[dict[str, torch.Tensor]]):
    def __init__(self, values: dict[str, torch.Tensor]) -> None:
        lengths = {int(value.shape[0]) for value in values.values()}
        if len(lengths) != 1:
            raise ValueError("all synthetic dataset tensors must share their first dimension")
        self._values = values
        self._length = lengths.pop()

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        return {name: value[index].clone() for name, value in self._values.items()}


def model_definition(family: Family) -> object:
    match family:
        case "lstm":
            return LstmDefinition(5, 7, 1, 0.0, 6)
        case "transformer":
            return TransformerDefinition(8, 2, 1, 16, 0.0, 6)
        case "transformer_lstm":
            return TransformerLstmDefinition(8, 2, 1, 16, 7, 1, 0.0, 6)


def model_families() -> tuple[Family, ...]:
    return "lstm", "transformer", "transformer_lstm"


def frozen_task() -> FrozenTask:
    generator = torch.Generator().manual_seed(4001)
    training_labels = torch.tensor([0, 1, 2, 1, 0], dtype=torch.int64)
    validation_labels = torch.tensor([2, 0, 1], dtype=torch.int64)
    training = _dataset(
        inputs=torch.randn(5, CONTEXT_BLOCKS, INPUT_WIDTH, generator=generator),
        labels=training_labels,
        targets=torch.tensor([-0.8, -0.2, 0.4, 0.9, 0.1], dtype=torch.float32),
        first_origin=1000,
    )
    invalid_training_values = {
        name: torch.stack([training[index][name] for index in range(len(training))])
        for name in training[0]
    }
    invalid_training_values["target"][1] = float("nan")
    validation = _dataset(
        inputs=torch.randn(3, CONTEXT_BLOCKS, INPUT_WIDTH, generator=generator),
        labels=validation_labels,
        targets=torch.tensor([0.3, -0.6, 0.8], dtype=torch.float32),
        first_origin=2000,
    )
    invalid_values = {
        name: torch.stack([validation[index][name] for index in range(len(validation))])
        for name in validation[0]
    }
    invalid_values["target"][1] = float("nan")
    classification = ClassificationLossState.fit(
        training_labels,
        horizon=HORIZON,
        mode="unweighted",
    )
    return FrozenTask(
        training=training,
        invalid_training=TensorMapDataset(invalid_training_values),
        validation=validation,
        invalid_validation=TensorMapDataset(invalid_values),
        classification=classification,
    )


def _dataset(
    *,
    inputs: torch.Tensor,
    labels: torch.Tensor,
    targets: torch.Tensor,
    first_origin: int,
) -> TensorMapDataset:
    count = int(labels.numel())
    fees = torch.arange(1, HORIZON + 1, dtype=torch.int64).repeat(count, 1) + 100
    return TensorMapDataset(
        {
            "inputs": inputs.to(torch.float32),
            "label": labels,
            "target": targets,
            "base_fees": fees,
            "origin_block": torch.arange(first_origin, first_origin + count),
        }
    )


def build_frozen_model(definition: object) -> torch.nn.Module:
    return cast(
        torch.nn.Module,
        build_model(
            input_width=INPUT_WIDTH,
            context_blocks=CONTEXT_BLOCKS,
            horizon=HORIZON,
            definition=definition,
        ),
    )


def move_model_inputs(
    batch: dict[str, torch.Tensor],
    device: torch.device,
) -> dict[str, torch.Tensor]:
    moved = dict(batch)
    for name in ("inputs", "label", "target"):
        moved[name] = moved[name].to(device)
    return moved


def loss_terms(
    output: object,
    batch: dict[str, torch.Tensor],
    classification: object,
) -> tuple[torch.Tensor, torch.Tensor]:
    terms = TASK._loss_terms(
        output,
        label=batch["label"],
        target=batch["target"],
        classification=classification,
    )
    return cast(tuple[torch.Tensor, torch.Tensor], terms)


def batch_loss(
    output: object,
    batch: dict[str, torch.Tensor],
    classification: object,
) -> torch.Tensor:
    result = min_block_fee_loss(
        output,
        label=batch["label"],
        target=batch["target"],
        classification=classification,
    )
    return cast(torch.Tensor, result.total)


def candidate_success(result: FitResult, *, method: str) -> CandidateSuccess:
    """Private HPO handoff: one completed fit, never an epoch/pruning callback."""
    return CandidateSuccess(
        method=method,
        total_loss=result.best_validation.total_loss,
        earliest_best_epoch=result.earliest_best_epoch,
        completed_epochs=result.completed_epochs,
    )
