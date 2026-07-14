"""DISPOSABLE PROTOTYPE: approved unmodified Lightning best checkpoint artifact.

Question: can stock Lightning own best writing/selection, continuation, strict loading,
and the canonical model file while SPICE owns only one small typed domain record?

Synthetic full/tail tensors only. CPU strict-FP32 lifecycle evidence only; this is not
production storage, L40/CUDA evidence, model-quality evidence, or a final artifact ABI.

Run: uv run python docs/research/issue-26/single_artifact_prototype.py
"""

from __future__ import annotations

import json
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

import lightning.pytorch as pl
import torch
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
from pydantic import BaseModel, ConfigDict, model_validator
from task_fixture import (
    CLIP_NORM,
    MAX_EPOCHS,
    PATIENCE,
    SEED,
    TRAIN_BATCH_SIZE,
    VALIDATION_BATCH_SIZE,
    Family,
    TensorMapDataset,
    batch_loss,
    build_frozen_model,
    frozen_task,
    loss_terms,
    model_definition,
    model_families,
    move_model_inputs,
)
from torch.utils.data import DataLoader
from torchmetrics import MeanMetric

MONITOR = "validation_total_loss"
FIXTURE_ID = "issue-26-frozen-synthetic-full-tail"

ARTIFACT_IDS: Mapping[Family, str] = {
    "lstm": "11111111-1111-4111-8111-111111111111",
    "transformer": "22222222-2222-4222-8222-222222222222",
    "transformer_lstm": "33333333-3333-4333-8333-333333333333",
}


class _StrictRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class SyntheticSource(_StrictRecord):
    kind: Literal["synthetic"]
    fixture_id: Literal["issue-26-frozen-synthetic-full-tail"]


class SyntheticTrainRequest(_StrictRecord):
    workflow: Literal["train"]
    artifact_id: str
    source: SyntheticSource

    @model_validator(mode="after")
    def validate_artifact_id(self) -> SyntheticTrainRequest:
        if str(UUID(self.artifact_id)) != self.artifact_id:
            raise ValueError("artifact_id must be a canonical UUID")
        return self


class SyntheticFeatureState(_StrictRecord):
    ordered_features: list[str]
    means: list[float]
    scales: list[float]

    @model_validator(mode="after")
    def validate_features(self) -> SyntheticFeatureState:
        if self.ordered_features != ["synthetic_0", "synthetic_1", "synthetic_2"]:
            raise ValueError("synthetic feature order is fixed")
        if self.means != [0.0, 0.0, 0.0] or self.scales != [1.0, 1.0, 1.0]:
            raise ValueError("synthetic fitted feature state is fixed")
        return self


class SyntheticTargetState(_StrictRecord):
    transform: Literal["standardized_log_minimum"]
    mean: float
    scale: float

    @model_validator(mode="after")
    def validate_target(self) -> SyntheticTargetState:
        if self.mean != 0.0 or self.scale != 1.0:
            raise ValueError("synthetic fitted target state is fixed")
        return self


class SyntheticClassificationState(_StrictRecord):
    mode: Literal["unweighted", "corrected_inverse_frequency"]
    sample_count: int
    support: list[int]

    @model_validator(mode="after")
    def validate_support(self) -> SyntheticClassificationState:
        if self.sample_count <= 0 or len(self.support) != 3:
            raise ValueError("classification state has the wrong size")
        if any(value <= 0 for value in self.support) or sum(self.support) != self.sample_count:
            raise ValueError("classification support must cover the training samples")
        return self


class SyntheticTaskMath(_StrictRecord):
    family: Family
    context_blocks: Literal[4]
    input_width: Literal[3]
    horizon: Literal[3]
    objective: Literal["cross_entropy_plus_smooth_l1"]


class SyntheticArtifactRecord(_StrictRecord):
    request: SyntheticTrainRequest
    feature_state: SyntheticFeatureState
    target_state: SyntheticTargetState
    classification_state: SyntheticClassificationState
    task_math: SyntheticTaskMath


@dataclass(frozen=True, slots=True)
class LoadedArtifact:
    record: SyntheticArtifactRecord
    model: torch.nn.Module


@dataclass(frozen=True, slots=True)
class FitOutcome:
    best_checkpoint: Path
    total_loss: float
    earliest_best_epoch: int
    completed_epochs: int
    stop_reason: Literal["patience", "max_epochs"]


def _artifact_record(family: Family) -> SyntheticArtifactRecord:
    classification = cast(Any, frozen_task().classification)
    return SyntheticArtifactRecord(
        request=SyntheticTrainRequest(
            workflow="train",
            artifact_id=ARTIFACT_IDS[family],
            source=SyntheticSource(kind="synthetic", fixture_id=FIXTURE_ID),
        ),
        feature_state=SyntheticFeatureState(
            ordered_features=["synthetic_0", "synthetic_1", "synthetic_2"],
            means=[0.0, 0.0, 0.0],
            scales=[1.0, 1.0, 1.0],
        ),
        target_state=SyntheticTargetState(
            transform="standardized_log_minimum",
            mean=0.0,
            scale=1.0,
        ),
        classification_state=SyntheticClassificationState(
            mode=classification.mode,
            sample_count=classification.sample_count,
            support=list(classification.support),
        ),
        task_math=SyntheticTaskMath(
            family=family,
            context_blocks=4,
            input_width=3,
            horizon=3,
            objective="cross_entropy_plus_smooth_l1",
        ),
    )


def _task_validation_losses(
    output: object,
    batch: dict[str, torch.Tensor],
    classification: object,
) -> torch.Tensor:
    """Task-owned per-origin objective; the fit host sees one loss vector."""
    classification_terms, regression_terms = loss_terms(output, batch, classification)
    return classification_terms.detach().to(torch.float64) + regression_terms.detach().to(
        torch.float64
    )


class FitModule(pl.LightningModule):
    """Loss-agnostic automatic host with a typed constructor record."""

    def __init__(self, artifact: dict[str, object]) -> None:
        super().__init__()
        self.artifact = SyntheticArtifactRecord.model_validate(artifact, strict=True)
        self.save_hyperparameters(
            {"artifact": self.artifact.model_dump(mode="json")},
            logger=False,
        )
        self.model = build_frozen_model(model_definition(self.artifact.task_math.family))
        task = frozen_task()
        expected_classification = self.artifact.classification_state
        classification = cast(Any, task.classification)
        if (
            classification.mode != expected_classification.mode
            or classification.sample_count != expected_classification.sample_count
            or list(classification.support) != expected_classification.support
        ):
            raise ValueError("fitted classification state does not match the task")
        self.classification = classification
        self.validation_samples = len(task.validation)
        self.validation_objective = MeanMetric(
            nan_strategy="disable",
            sync_on_compute=False,
        ).set_dtype(torch.float64)

    def training_step(
        self,
        batch: dict[str, torch.Tensor],
        batch_idx: int,
    ) -> torch.Tensor:
        del batch_idx
        loss = batch_loss(self.model(batch["inputs"]), batch, self.classification)
        if not bool(torch.isfinite(loss)):
            raise FloatingPointError("training loss must be finite")
        return loss

    def validation_step(
        self,
        batch: dict[str, torch.Tensor],
        batch_idx: int,
    ) -> None:
        del batch_idx
        losses = _task_validation_losses(
            self.model(batch["inputs"]),
            batch,
            self.classification,
        )
        self.validation_objective.update(losses)

    def on_validation_epoch_end(self) -> None:
        if not bool(self.validation_objective.weight == self.validation_samples):
            raise RuntimeError("complete validation must observe every sample exactly once")
        total = self.validation_objective.compute()
        if not bool(torch.isfinite(total)):
            raise FloatingPointError("complete validation total_loss must be finite")
        self.log(
            MONITOR,
            self.validation_objective,
            on_step=False,
            on_epoch=True,
            logger=False,
            sync_dist=False,
        )

    def transfer_batch_to_device(
        self,
        batch: dict[str, torch.Tensor],
        device: torch.device,
        dataloader_idx: int,
    ) -> dict[str, torch.Tensor]:
        del dataloader_idx
        return move_model_inputs(batch, device)

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
        return torch.optim.AdamW(self.model.parameters(), lr=0.0, weight_decay=0.0)

    def on_load_checkpoint(self, checkpoint: dict[str, Any]) -> None:
        """Validate only SPICE's domain association; Lightning validates its state."""
        hparams = checkpoint.get(self.CHECKPOINT_HYPER_PARAMS_KEY)
        if not isinstance(hparams, Mapping):
            raise ValueError("checkpoint has no saved domain record")
        saved = SyntheticArtifactRecord.model_validate(hparams.get("artifact"), strict=True)
        if saved != self.artifact:
            raise ValueError("checkpoint domain record does not match this fit")


def _callbacks(work_dir: Path) -> tuple[EarlyStopping, ModelCheckpoint, ModelCheckpoint]:
    early_stopping = EarlyStopping(
        monitor=MONITOR,
        mode="min",
        min_delta=0.0,
        patience=PATIENCE,
        strict=True,
        check_finite=False,
        check_on_train_epoch_end=False,
    )
    best = ModelCheckpoint(
        dirpath=work_dir,
        filename="best-{epoch:02d}",
        auto_insert_metric_name=False,
        monitor=MONITOR,
        mode="min",
        save_top_k=1,
        save_weights_only=True,
        save_on_train_epoch_end=False,
        enable_version_counter=False,
    )
    last = ModelCheckpoint(
        dirpath=work_dir,
        filename="last",
        save_top_k=1,
        save_weights_only=False,
        save_on_train_epoch_end=False,
        enable_version_counter=False,
    )
    return early_stopping, best, last


def _trainer(
    work_dir: Path,
    *,
    max_epochs: int,
) -> tuple[pl.Trainer, EarlyStopping, ModelCheckpoint, ModelCheckpoint]:
    early_stopping, best, last = _callbacks(work_dir)
    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        precision="32-true",
        max_epochs=max_epochs,
        callbacks=[early_stopping, best, last],
        logger=False,
        enable_progress_bar=False,
        enable_model_summary=False,
        num_sanity_val_steps=0,
        gradient_clip_val=CLIP_NORM,
        gradient_clip_algorithm="norm",
        deterministic=True,
    )
    return trainer, early_stopping, best, last


def _loaders(
    training: TensorMapDataset,
    validation: TensorMapDataset,
) -> tuple[DataLoader[dict[str, torch.Tensor]], DataLoader[dict[str, torch.Tensor]]]:
    generator = torch.Generator().manual_seed(SEED)
    return (
        DataLoader(
            training,
            batch_size=TRAIN_BATCH_SIZE,
            shuffle=True,
            generator=generator,
            drop_last=False,
        ),
        DataLoader(
            validation,
            batch_size=VALIDATION_BATCH_SIZE,
            shuffle=False,
            drop_last=False,
        ),
    )


def _fit_job(
    record: SyntheticArtifactRecord,
    training: TensorMapDataset,
    validation: TensorMapDataset,
    work_dir: Path,
    *,
    max_epochs: int,
    resume: bool,
) -> tuple[pl.Trainer, EarlyStopping, ModelCheckpoint]:
    pl.seed_everything(SEED, workers=True, verbose=False)
    module = FitModule(record.model_dump(mode="json"))
    train_loader, validation_loader = _loaders(training, validation)
    trainer, early_stopping, best, _ = _trainer(work_dir, max_epochs=max_epochs)
    trainer.fit(
        module,
        train_dataloaders=train_loader,
        val_dataloaders=validation_loader,
        ckpt_path=work_dir / "last.ckpt" if resume else None,
        weights_only=True,
    )
    return trainer, early_stopping, best


def _best_epoch(path: Path) -> int:
    prefix = "best-"
    suffix = ".ckpt"
    if not path.name.startswith(prefix) or not path.name.endswith(suffix):
        raise ValueError("stock best path does not match the controlled filename")
    zero_based = int(path.name[len(prefix) : -len(suffix)])
    return zero_based + 1


def artifact_path(storage_root: Path, artifact_id: str) -> Path:
    return storage_root / "artifacts" / f"{artifact_id}.ckpt"


def load_artifact(storage_root: Path, artifact_id: str) -> LoadedArtifact:
    """Thin domain facade; Lightning owns parsing and strict weight restoration."""
    module = FitModule.load_from_checkpoint(
        artifact_path(storage_root, artifact_id),
        map_location="cpu",
        weights_only=True,
        strict=True,
    )
    if module.artifact.request.artifact_id != artifact_id:
        raise ValueError("loaded TrainRequest does not match the requested artifact")
    module.eval()
    return LoadedArtifact(record=module.artifact, model=module.model)


def train_and_publish(family: Family, storage_root: Path) -> FitOutcome:
    task = frozen_task()
    record = _artifact_record(family)
    artifact_id = record.request.artifact_id
    artifacts = storage_root / "artifacts"
    artifacts.mkdir(parents=True)
    scratch = artifacts / f".{artifact_id}"
    scratch.mkdir()

    _fit_job(
        record,
        task.training,
        task.validation,
        scratch,
        max_epochs=2,
        resume=False,
    )
    trainer, early_stopping, best = _fit_job(
        record,
        task.training,
        task.validation,
        scratch,
        max_epochs=MAX_EPOCHS,
        resume=True,
    )

    best_path = Path(best.best_model_path)
    last_path = scratch / "last.ckpt"
    score = best.best_model_score
    if not best_path.is_file() or not last_path.is_file() or score is None:
        raise RuntimeError("stock weights-only best and broad last are required")
    if early_stopping.wait_count < PATIENCE:
        raise AssertionError("bounded equality curve must stop by strict patience")

    outcome = FitOutcome(
        best_checkpoint=best_path,
        total_loss=float(score.detach().cpu()),
        earliest_best_epoch=_best_epoch(best_path),
        completed_epochs=trainer.current_epoch,
        stop_reason="patience" if early_stopping.stopped_epoch > 0 else "max_epochs",
    )
    canonical = artifact_path(storage_root, artifact_id)
    if canonical.exists():
        raise FileExistsError(canonical)
    best_path.rename(canonical)
    return outcome


def _consumer_probe(
    storage_root: Path,
    family: Family,
) -> dict[str, object]:
    """Separate consumer probe, not a publication-time reload step."""
    artifact_id = ARTIFACT_IDS[family]
    loaded = load_artifact(storage_root, artifact_id)
    task = frozen_task()
    _, validation_loader = _loaders(task.training, task.validation)
    batch_sizes: list[int] = []
    with torch.inference_mode():
        for batch in validation_loader:
            batch_loss(loaded.model(batch["inputs"]), batch, task.classification)
            batch_sizes.append(int(batch["inputs"].shape[0]))
    if batch_sizes != [2, 1]:
        raise AssertionError("native loaded artifact must cover full and tail batches")
    return {
        "artifact_id": artifact_id,
        "family": loaded.record.task_math.family,
        "validation_batch_sizes": batch_sizes,
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="spice-issue-26-native-artifact-") as raw_root:
        root = Path(raw_root)
        outcomes: dict[Family, FitOutcome] = {}
        for family in model_families():
            outcomes[family] = train_and_publish(family, root / family)

        consumers = {family: _consumer_probe(root / family, family) for family in model_families()}
        print(
            json.dumps(
                {
                    "question": "can the stock selected best be the canonical artifact?",
                    "runtime": {
                        "device": "cpu",
                        "precision": "strict_fp32",
                        "scope": "synthetic lifecycle only; not L40/CUDA evidence",
                    },
                    "families": {
                        family: {
                            "scratch": f"artifacts/.{ARTIFACT_IDS[family]}/",
                            "canonical": f"artifacts/{ARTIFACT_IDS[family]}.ckpt",
                            "best_total_loss": outcome.total_loss,
                            "earliest_best_epoch": outcome.earliest_best_epoch,
                            "completed_epochs": outcome.completed_epochs,
                            "stop_reason": outcome.stop_reason,
                            "native_consumer": consumers[family],
                        }
                        for family, outcome in outcomes.items()
                    },
                    "checks": "pass",
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
