from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

import numpy as np
import polars as pl
import pytest
import torch
from pydantic import ValidationError
from torch.utils.data import DataLoader

import fable.modeling as modeling
from fable.addresses import (
    artifact_checkpoint_path,
    artifact_directory,
    artifact_fit_history_path,
)
from fable.config import (
    AdamWMethod,
    BaselineSource,
    BlockWindow,
    CorpusDefinition,
    CorpusRequest,
    ExperimentSemantics,
    FitMethod,
    LossDefinition,
    LstmCapacity,
    LstmDefinition,
    LstmMethod,
    LstmMethodSpace,
    StudyDefinition,
    TrainingDefinition,
    TrainRequest,
    TransformerDefinition,
    TransformerLstmDefinition,
    TuneRequest,
)
from fable.corpus import BlockFrame, Corpus, FinalizedAnchor
from fable.min_block_fee import (
    ClassificationLossState,
    TargetState,
    min_block_fee_loss,
)
from fable.modeling import (
    ArtifactAssociation,
    FitDeployment,
    load_artifact,
    train,
)
from fable.temporal.features import FeatureState
from fable.temporal.history import prepare_fit_history

ARTIFACT_ID = UUID("10000000-0000-4000-8000-000000000001")
CORPUS_ID = UUID("20000000-0000-4000-8000-000000000001")
_BASE_FEES = np.array(
    [11, 12, 10, 4, 9, 4, 8, 3, 5, 6, 10, 6, 2, 2],
    dtype=np.int64,
)


def _experiment() -> ExperimentSemantics:
    return ExperimentSemantics(
        training_window=BlockWindow(
            first_parent_block=12,
            last_parent_block=15,
        ),
        validation_window=BlockWindow(
            first_parent_block=20,
            last_parent_block=21,
        ),
        context_blocks=3,
        horizon_blocks=2,
        ordered_features=("log_base_fee_per_gas", "gas_utilization"),
        loss=LossDefinition(
            classification_algorithm="cross_entropy",
            classification_weighting="unweighted",
            regression_algorithm="smooth_l1",
            regression_threshold=0.6,
            classification_scale=1.2,
            regression_scale=0.7,
        ),
    )


def _request() -> TrainRequest:
    definition = TrainingDefinition(
        experiment=_experiment(),
        model=LstmDefinition(
            family="lstm",
            hidden=5,
            layers=1,
            head_hidden=3,
            dropout=0.1,
        ),
        optimizer=AdamWMethod(learning_rate=0.002, weight_decay=0.003),
        training_batch=3,
        fit=FitMethod(
            accumulation=2,
            gradient_clip_norm=0.4,
            scheduler="none",
            seed=19,
            max_epochs=4,
            validate_every_completed_epoch=1,
            patience=1,
            min_delta=0.02,
            improvement="strict_lower",
            restore="earliest_best",
        ),
    )
    return TrainRequest(
        workflow="train",
        artifact_id=ARTIFACT_ID,
        source=BaselineSource(
            kind="baseline",
            corpus_id=CORPUS_ID,
            training_definition=definition,
        ),
    )


def _corpus() -> Corpus:
    blocks = np.arange(10, 24, dtype=np.int64)
    request = _corpus_request()
    return Corpus(
        request=request,
        finalized_anchor=FinalizedAnchor(block_number=23, block_hash="a" * 64),
        blocks=BlockFrame(
            pl.DataFrame(
                {
                    "block_number": blocks,
                    "timestamp": blocks * 11,
                    "chain_id": np.ones(blocks.size, dtype=np.int64),
                    "base_fee_per_gas": _BASE_FEES,
                    "gas_used": 30 + np.arange(blocks.size, dtype=np.int64),
                    "gas_limit": np.full(blocks.size, 100, dtype=np.int64),
                    "tx_count": 4 + np.arange(blocks.size, dtype=np.int64),
                }
            ),
            request.definition,
        ),
    )


def _corpus_request() -> CorpusRequest:
    return CorpusRequest(
        corpus_id=CORPUS_ID,
        definition=CorpusDefinition(chain_id=1, first_block=10, last_block=23),
    )


def _deployment() -> FitDeployment:
    return FitDeployment(
        deterministic=True,
        benchmark=False,
        num_workers=0,
        pin_memory=False,
        prefetch_factor=None,
        persistent_workers=False,
        float32_matmul_precision="highest",
        cuda_matmul_allow_tf32=False,
        cudnn_allow_tf32=False,
    )


def _candidate_request(method: LstmMethod) -> TuneRequest:
    return TuneRequest(
        workflow="tune",
        study_id=UUID("40000000-0000-4000-8000-000000000001"),
        corpus_id=CORPUS_ID,
        study_definition=StudyDefinition(
            experiment=method_experiment(),
            method_space=LstmMethodSpace(family="lstm", methods=(method,)),
        ),
    )


def method_experiment() -> ExperimentSemantics:
    experiment = _experiment()
    return ExperimentSemantics(
        training_window=experiment.training_window,
        validation_window=experiment.validation_window,
        context_blocks=experiment.context_blocks,
        horizon_blocks=experiment.horizon_blocks,
        ordered_features=experiment.ordered_features,
        loss=LossDefinition(
            classification_algorithm="cross_entropy",
            classification_weighting="unweighted",
            regression_algorithm="smooth_l1",
            regression_threshold=0.6,
            classification_scale=0.0,
            regression_scale=0.0,
        ),
    )


def _definition(
    model: LstmDefinition | TransformerDefinition | TransformerLstmDefinition,
) -> TrainingDefinition:
    return TrainingDefinition(
        experiment=_experiment(),
        model=model,
        optimizer=AdamWMethod(learning_rate=0.002, weight_decay=0.003),
        training_batch=3,
        fit=FitMethod(
            accumulation=1,
            gradient_clip_norm=0.8,
            scheduler="none",
            seed=29,
            max_epochs=1,
            validate_every_completed_epoch=1,
            patience=0,
            min_delta=0.0,
            improvement="strict_lower",
            restore="earliest_best",
        ),
    )


def _train_request(
    artifact_id: UUID,
    model: LstmDefinition | TransformerDefinition | TransformerLstmDefinition,
) -> TrainRequest:
    return TrainRequest(
        workflow="train",
        artifact_id=artifact_id,
        source=BaselineSource(
            kind="baseline",
            corpus_id=CORPUS_ID,
            training_definition=_definition(model),
        ),
    )


def test_artifact_association_round_trips_strict_json() -> None:
    association = ArtifactAssociation(
        request=_request(),
        feature_state=FeatureState(
            means=(1.0, 2.0),
            standard_deviations=(0.5, 0.25),
        ),
        target_state=TargetState(mean=3.0, standard_deviation=0.75),
    )

    assert (
        ArtifactAssociation.model_validate_json(
            association.model_dump_json(exclude_none=True),
            strict=True,
        )
        == association
    )


def test_artifact_association_rejects_only_owned_mismatches() -> None:
    feature_state = FeatureState(
        means=(1.0, 2.0),
        standard_deviations=(0.5, 0.25),
    )
    target_state = TargetState(mean=3.0, standard_deviation=0.75)
    method = LstmMethod(
        family="lstm",
        capacity=LstmCapacity(hidden=5, layers=1, head_hidden=3),
        dropout=0.1,
        optimizer=AdamWMethod(learning_rate=0.002, weight_decay=0.003),
        training_batch=3,
        fit=FitMethod(
            accumulation=2,
            gradient_clip_norm=0.4,
            scheduler="none",
            seed=19,
            max_epochs=4,
            validate_every_completed_epoch=1,
            patience=1,
            min_delta=0.02,
            improvement="strict_lower",
            restore="earliest_best",
        ),
    )

    with pytest.raises(ValidationError, match="baseline artifacts"):
        ArtifactAssociation(
            request=_request(),
            feature_state=feature_state,
            target_state=target_state,
            study_result_index=0,
            method=method,
        )
    with pytest.raises(ValidationError, match="feature state width"):
        ArtifactAssociation(
            request=_request(),
            feature_state=FeatureState(
                means=(1.0,),
                standard_deviations=(0.5,),
            ),
            target_state=target_state,
        )

    experiment = _experiment()
    corrected_experiment = ExperimentSemantics(
        training_window=experiment.training_window,
        validation_window=experiment.validation_window,
        context_blocks=experiment.context_blocks,
        horizon_blocks=experiment.horizon_blocks,
        ordered_features=experiment.ordered_features,
        loss=LossDefinition(
            classification_algorithm="cross_entropy",
            classification_weighting="corrected_inverse_frequency",
            regression_algorithm="smooth_l1",
            regression_threshold=0.6,
            classification_scale=1.2,
            regression_scale=0.7,
        ),
    )
    corrected_request = TrainRequest(
        workflow="train",
        artifact_id=ARTIFACT_ID,
        source=BaselineSource(
            kind="baseline",
            corpus_id=CORPUS_ID,
            training_definition=TrainingDefinition(
                experiment=corrected_experiment,
                model=LstmDefinition(
                    family="lstm",
                    hidden=5,
                    layers=1,
                    head_hidden=3,
                    dropout=0.1,
                ),
                optimizer=method.optimizer,
                training_batch=method.training_batch,
                fit=method.fit,
            ),
        ),
    )
    with pytest.raises(ValidationError, match="support width"):
        ArtifactAssociation(
            request=corrected_request,
            feature_state=feature_state,
            target_state=target_state,
            classification_state=ClassificationLossState(class_support=(2,)),
        )


def test_transformer_encoder_layers_have_independent_matrix_initialization() -> None:
    torch.manual_seed(71)
    encoder = modeling._encoder(
        width=4,
        heads=2,
        feedforward=7,
        layers=2,
        dropout=0.1,
    )
    matrices = [
        [parameter for parameter in layer.parameters() if parameter.ndim > 1]
        for layer in encoder.layers
    ]

    assert matrices[0]
    assert all(
        not torch.equal(first, second)
        for first, second in zip(matrices[0], matrices[1], strict=True)
    )


def test_epoch_logs_weight_short_batches_in_float64(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = prepare_fit_history(_corpus(), _experiment())
    association = ArtifactAssociation(
        request=_request(),
        feature_state=prepared.feature_state,
        target_state=prepared.target_state,
        classification_state=prepared.classification_state,
    )
    torch.manual_seed(89)
    module = modeling._FitModule(modeling._json_association(association)).eval()
    batches = list(DataLoader(prepared.training, batch_size=3, shuffle=False))
    complete = next(iter(DataLoader(prepared.training, batch_size=4, shuffle=False)))
    with torch.no_grad():
        expected = float(module._loss(complete).mean_total)
    logged: dict[str, list[tuple[torch.Tensor, dict[str, Any]]]] = {
        "training_total_loss": [],
        "validation_total_loss": [],
    }

    def capture(name: str, value: torch.Tensor, **kwargs: Any) -> None:
        logged[name].append((value, kwargs))

    monkeypatch.setattr(module, "log", capture)
    with torch.no_grad():
        for batch_index, batch in enumerate(batches):
            module.training_step(batch, batch_index)
            module.validation_step(batch, batch_index)

    for entries in logged.values():
        assert [kwargs["batch_size"] for _, kwargs in entries] == [3, 1]
        assert all(value.dtype == torch.float64 for value, _ in entries)
        assert all(kwargs["on_step"] is False for _, kwargs in entries)
        assert all(kwargs["on_epoch"] is True for _, kwargs in entries)
        assert all(kwargs["logger"] is False for _, kwargs in entries)
        weighted = sum(float(value) * int(kwargs["batch_size"]) for value, kwargs in entries) / 4
        unweighted = sum(float(value) for value, _ in entries) / 2
        assert weighted == pytest.approx(expected)
        assert unweighted != pytest.approx(expected)


@pytest.mark.parametrize(
    ("artifact_id", "model"),
    [
        (
            UUID("30000000-0000-4000-8000-000000000001"),
            LstmDefinition(
                family="lstm",
                hidden=5,
                layers=1,
                head_hidden=3,
                dropout=0.1,
            ),
        ),
        (
            UUID("30000000-0000-4000-8000-000000000002"),
            TransformerDefinition(
                family="transformer",
                model_width=4,
                attention_heads=2,
                transformer_layers=1,
                feedforward_width=7,
                head_hidden=3,
                dropout=0.1,
            ),
        ),
        (
            UUID("30000000-0000-4000-8000-000000000003"),
            TransformerLstmDefinition(
                family="transformer_lstm",
                model_width=4,
                attention_heads=2,
                transformer_layers=1,
                feedforward_width=7,
                lstm_hidden=5,
                lstm_layers=1,
                head_hidden=3,
                dropout=0.1,
            ),
        ),
    ],
)
def test_all_three_models_train_load_and_apply_direct_loss(
    artifact_id: UUID,
    model: LstmDefinition | TransformerDefinition | TransformerLstmDefinition,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared = prepare_fit_history(_corpus(), _experiment())
    request = _train_request(artifact_id, model)
    real_trainer: Any = modeling.pl.Trainer

    def cpu_trainer(**kwargs: Any) -> Any:
        kwargs["accelerator"] = "cpu"
        return real_trainer(**kwargs)

    monkeypatch.setattr(modeling.pl, "Trainer", cpu_trainer)

    train(request, prepared, tmp_path, _deployment())
    association, loaded_model = load_artifact(tmp_path, artifact_id)

    assert association.request == request
    directory = artifact_directory(tmp_path, artifact_id)
    assert sorted(path.name for path in directory.iterdir()) == ["fit.csv", "model.ckpt"]
    assert artifact_checkpoint_path(tmp_path, artifact_id).is_file()
    fit_history = pl.read_csv(artifact_fit_history_path(tmp_path, artifact_id))
    assert fit_history.schema == {
        "epoch": pl.Int64,
        "training_total_loss": pl.Float64,
        "validation_total_loss": pl.Float64,
    }
    assert fit_history["epoch"].to_list() == [1]
    assert fit_history.select(
        pl.col("training_total_loss").is_finite().all(),
        pl.col("validation_total_loss").is_finite().all(),
    ).row(0) == (True, True)
    batches = list(DataLoader(prepared.training, batch_size=3, shuffle=False))
    for batch in batches:
        output = loaded_model(batch["inputs"])
        assert output.action_logits.shape == (batch["inputs"].shape[0], 2)
        assert output.minimum_fee_z.shape == (batch["inputs"].shape[0],)
        assert torch.isfinite(output.action_logits).all()
        assert torch.isfinite(output.minimum_fee_z).all()
        loss = min_block_fee_loss(
            output,
            label=batch["label"],
            target=batch["target"],
            loss_definition=_experiment().loss,
            classification_state=None,
        )
        assert torch.isfinite(loss.mean_total)

    if isinstance(model, LstmDefinition):
        mismatched_id = UUID("30000000-0000-4000-8000-000000000009")
        artifact_directory(tmp_path, artifact_id).rename(
            artifact_directory(tmp_path, mismatched_id)
        )
        with pytest.raises(ValueError, match="embedded artifact ID"):
            load_artifact(tmp_path, mismatched_id)


def test_full_checkpoint_resume_restores_fit_history(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    method = LstmMethod(
        family="lstm",
        capacity=LstmCapacity(hidden=5, layers=1, head_hidden=3),
        dropout=0.0,
        optimizer=AdamWMethod(learning_rate=0.004, weight_decay=0.002),
        training_batch=3,
        fit=FitMethod(
            accumulation=1,
            gradient_clip_norm=0.0,
            scheduler="none",
            seed=37,
            max_epochs=4,
            validate_every_completed_epoch=2,
            patience=10,
            min_delta=0.0,
            improvement="strict_lower",
            restore="earliest_best",
        ),
    )
    request = _candidate_request(method)
    prepared = prepare_fit_history(_corpus(), request.study_definition.experiment)
    real_trainer: Any = modeling.pl.Trainer
    fit_kwargs: list[dict[str, object]] = []

    class TrainerSpy:
        def __init__(self, **kwargs: Any) -> None:
            kwargs["accelerator"] = "cpu"
            if not fit_kwargs:
                kwargs["max_epochs"] = 2
            self._trainer = real_trainer(**kwargs)

        def fit(self, module: Any, **kwargs: Any) -> None:
            fit_kwargs.append(dict(kwargs))
            self._trainer.fit(module, **kwargs)

        def __getattr__(self, name: str) -> object:
            return getattr(self._trainer, name)

    monkeypatch.setattr(modeling.pl, "Trainer", TrainerSpy)
    scratch = tmp_path / "candidate"
    association = modeling._CandidateAssociation(
        request=request,
        method=method,
        feature_state=prepared.feature_state,
        target_state=prepared.target_state,
        classification_state=prepared.classification_state,
    )

    first = modeling._fit(association, prepared, scratch, _deployment())
    second = modeling._fit(association, prepared, scratch, _deployment())

    assert first.objective == 0.0
    assert first.selected_epoch == 2
    assert first.completed_epochs == 2
    assert second.objective == first.objective
    assert second.selected_epoch == first.selected_epoch
    assert second.completed_epochs == method.fit.max_epochs
    assert [row.epoch for row in first.fit_history] == [1, 2]
    assert [row.epoch for row in second.fit_history] == [1, 2, 3, 4]
    assert [row.validation_total_loss for row in second.fit_history] == [None, 0.0, None, 0.0]
    assert all(row.training_total_loss == 0.0 for row in second.fit_history)
    assert fit_kwargs[0]["ckpt_path"] is None
    assert fit_kwargs[1]["ckpt_path"] == scratch / "last.ckpt"
    assert "weights_only" not in fit_kwargs[1]
    assert sorted(path.name for path in scratch.iterdir()) == ["best-01.ckpt", "last.ckpt"]
    best_checkpoint = torch.load(scratch / "best-01.ckpt", map_location="cpu", weights_only=True)
    last_checkpoint = torch.load(scratch / "last.ckpt", map_location="cpu", weights_only=True)
    assert "optimizer_states" not in best_checkpoint
    assert "optimizer_states" in last_checkpoint
