from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from uuid import UUID

import polars as pl
import pytest

import experiments.k5_fee_conditions as fee_conditions_module
from experiments.k5_fee_conditions import write_k5_fee_condition_evidence
from fable.config import (
    AdamWMethod,
    BaselineSource,
    BlockWindow,
    EvaluateRequest,
    ExperimentSemantics,
    FitMethod,
    LstmDefinition,
    SelectedStudySource,
    TrainingDefinition,
)
from fable.corpus import Corpus
from fable.evaluation import ResolvedEvaluation

_COLUMNS = (
    "evaluation_id",
    "artifact_id",
    "corpus_id",
    "chain_id",
    "first_parent_block",
    "last_parent_block",
    "horizon_blocks",
    "descriptor",
    "quartile",
    "closed_parent_base_fee_per_gas_cutpoint_25",
    "closed_parent_base_fee_per_gas_cutpoint_50",
    "closed_parent_base_fee_per_gas_cutpoint_75",
    "signed_one_block_base_fee_log_change_cutpoint_25",
    "signed_one_block_base_fee_log_change_cutpoint_50",
    "signed_one_block_base_fee_log_change_cutpoint_75",
    "closed_parent_base_fee_per_gas_cell_median",
    "signed_one_block_base_fee_log_change_cell_median",
    "condition_origin_count",
    "earliest_hindsight_label_correct_count",
    "immediate_k0_base_fee_per_gas_sum",
    "finite_target_base_fee_per_gas_savings_sum",
    "finite_target_base_fee_per_gas_hindsight_opportunity_sum",
    "finite_target_base_fee_per_gas_hindsight_regret_sum",
    "finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0",
    "finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0",
    "finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0",
    "earliest_hindsight_label_accuracy",
)
_SCHEMA = pl.Schema(
    {
        **{name: pl.String for name in _COLUMNS[:3]},
        **{name: pl.Int64 for name in _COLUMNS[3:7]},
        "descriptor": pl.String,
        "quartile": pl.Int64,
        **{name: pl.Int64 for name in _COLUMNS[9:12]},
        **{name: pl.Float64 for name in _COLUMNS[12:17]},
        "condition_origin_count": pl.Int64,
        "earliest_hindsight_label_correct_count": pl.Int64,
        **{name: pl.Float64 for name in _COLUMNS[19:]},
    }
)
_CHAINS = (1, 137, 43_114)


def _uuid(namespace: int, index: int) -> UUID:
    return UUID(f"{namespace:08x}-0000-4000-8000-{index:012x}")


def _source(corpus_id: UUID, *, context: int = 200, horizon: int = 5) -> SelectedStudySource:
    return SelectedStudySource(
        kind="selected_study",
        corpus_id=corpus_id,
        study_id=_uuid(4, corpus_id.int % 1_000),
        study_result_index=0,
        experiment=ExperimentSemantics(
            training_window=BlockWindow(
                first_parent_block=200,
                last_parent_block=600,
            ),
            validation_window=BlockWindow(
                first_parent_block=700,
                last_parent_block=800,
            ),
            context_blocks=context,
            horizon_blocks=horizon,
            ordered_features=("log_base_fee_per_gas",),
        ),
    )


def test_write_k5_fee_condition_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluation_ids: tuple[UUID, UUID, UUID] = (
        _uuid(1, 1),
        _uuid(1, 2),
        _uuid(1, 3),
    )
    artifact_ids = tuple(_uuid(2, index) for index in range(1, 4))
    corpus_ids = tuple(_uuid(3, index) for index in range(1, 4))
    fees = [100, 100, 100, 100, 200, 300, 400, 500]
    savings = [10, 20, 30, 40, -10, -20, -30, -40]
    opportunities = [50, 60, 70, 80, 50, 60, 70, 80]
    selected_actions = [0, 1, 2, 3, 4, 0, 1, 2]
    hindsight_actions = [0, 4, 2, 4, 4, 3, 1, 4]
    observations = pl.DataFrame(
        {
            "previous_closed_parent_base_fee_per_gas": [100] * 8,
            "closed_parent_base_fee_per_gas": fees,
            "selected_action_k": selected_actions,
            "earliest_hindsight_action_k": hindsight_actions,
            "immediate_k0_base_fee_per_gas": [1_000] * 8,
            "selected_target_base_fee_per_gas": [1_000 - value for value in savings],
            "hindsight_minimum_base_fee_per_gas": [1_000 - value for value in opportunities],
        },
        schema={
            name: pl.Int64
            for name in (
                "previous_closed_parent_base_fee_per_gas",
                "closed_parent_base_fee_per_gas",
                "selected_action_k",
                "earliest_hindsight_action_k",
                "immediate_k0_base_fee_per_gas",
                "selected_target_base_fee_per_gas",
                "hindsight_minimum_base_fee_per_gas",
            )
        },
    )
    sources: dict[UUID, BaselineSource | SelectedStudySource] = {
        artifact_id: _source(corpus_id)
        for artifact_id, corpus_id in zip(artifact_ids, corpus_ids, strict=True)
    }
    corpora: dict[UUID, Corpus] = {
        corpus_id: cast(
            Corpus,
            SimpleNamespace(request=SimpleNamespace(definition=SimpleNamespace(chain_id=chain_id))),
        )
        for corpus_id, chain_id in zip(corpus_ids, _CHAINS, strict=True)
    }
    reductions = {
        evaluation_id: pl.DataFrame(
            {
                "eligible_origin_count": [8],
                "immediate_k0_base_fee_per_gas_sum": [8_000.0],
                "finite_target_base_fee_per_gas_savings_sum": [math.nextafter(0.0, math.inf)],
                "finite_target_base_fee_per_gas_hindsight_opportunity_sum": [520.0],
                "finite_target_base_fee_per_gas_hindsight_regret_sum": [520.0],
            }
        )
        for evaluation_id in evaluation_ids
    }
    requests: dict[UUID, EvaluateRequest] = {}
    for index, (evaluation_id, artifact_id, corpus_id) in enumerate(
        zip(evaluation_ids, artifact_ids, corpus_ids, strict=True)
    ):
        request = EvaluateRequest(
            workflow="evaluate",
            evaluation_id=evaluation_id,
            artifact_id=artifact_id,
            corpus_id=corpus_id,
            testing_window=BlockWindow(
                first_parent_block=1_000 + index * 100,
                last_parent_block=1_007 + index * 100,
            ),
        )
        requests[evaluation_id] = request
    resolution_calls: list[tuple[UUID, ...]] = []

    def resolve_evaluations(
        _storage_root: Path,
        selected_ids: tuple[UUID, ...],
    ) -> tuple[ResolvedEvaluation, ...]:
        resolution_calls.append(selected_ids)
        resolved: list[ResolvedEvaluation] = []
        for evaluation_id in selected_ids:
            request = requests[evaluation_id]
            source = sources[request.artifact_id]
            definition = (
                source.training_definition
                if isinstance(source, BaselineSource)
                else TrainingDefinition(
                    experiment=source.experiment,
                    model=LstmDefinition(
                        family="lstm",
                        hidden=1,
                        layers=1,
                        head_hidden=1,
                        dropout=0.0,
                    ),
                    optimizer=AdamWMethod(learning_rate=0.001, weight_decay=0.0),
                    training_batch=1,
                    fit=FitMethod(
                        accumulation=1,
                        gradient_clip_norm=1.0,
                        scheduler="none",
                        seed=1,
                        max_epochs=1,
                        validate_every_completed_epoch=1,
                        patience=0,
                        min_delta=0.0,
                        improvement="strict_lower",
                        restore="earliest_best",
                    ),
                )
            )
            resolved.append(
                ResolvedEvaluation(
                    request=request,
                    training_source=source,
                    training_definition=definition,
                    corpus=corpora[request.corpus_id],
                    observations=observations.lazy(),
                    reduction=reductions[evaluation_id],
                    trainable_parameter_count=0,
                )
            )
        return tuple(resolved)

    monkeypatch.setattr(fee_conditions_module, "resolve_evaluations", resolve_evaluations)

    destination = tmp_path / "k5-fee-conditions.tsv"
    write_k5_fee_condition_evidence(tmp_path, evaluation_ids, destination)

    assert resolution_calls == [evaluation_ids]
    assert not destination.with_name(f".{destination.name}").exists()
    evidence = pl.read_csv(destination, separator="\t", null_values="")
    assert evidence.schema == _SCHEMA
    assert evidence["chain_id"].to_list() == [chain_id for chain_id in _CHAINS for _ in range(8)]
    assert evidence["descriptor"].to_list() == [
        descriptor
        for _ in _CHAINS
        for descriptor in (
            "closed_parent_base_fee_per_gas",
            "signed_one_block_base_fee_log_change",
        )
        for _ in range(4)
    ]
    assert evidence["quartile"].to_list() == [1, 2, 3, 4] * 6

    raw = evidence.filter(
        (pl.col("chain_id") == 1) & (pl.col("descriptor") == "closed_parent_base_fee_per_gas")
    )
    assert raw["closed_parent_base_fee_per_gas_cutpoint_25"].to_list() == [100] * 4
    assert raw["closed_parent_base_fee_per_gas_cutpoint_50"].to_list() == [100] * 4
    assert raw["closed_parent_base_fee_per_gas_cutpoint_75"].to_list() == [300] * 4
    assert raw["signed_one_block_base_fee_log_change_cutpoint_25"].null_count() == 4
    assert raw["closed_parent_base_fee_per_gas_cell_median"].to_list() == [
        100.0,
        None,
        250.0,
        450.0,
    ]
    assert raw["condition_origin_count"].to_list() == [4, 0, 2, 2]
    assert raw["earliest_hindsight_label_correct_count"].to_list() == [2, 0, 1, 1]
    assert raw["immediate_k0_base_fee_per_gas_sum"].to_list() == [
        4_000.0,
        0.0,
        2_000.0,
        2_000.0,
    ]
    assert raw["finite_target_base_fee_per_gas_savings_sum"].to_list() == [
        100.0,
        0.0,
        -30.0,
        -70.0,
    ]
    assert raw["finite_target_base_fee_per_gas_hindsight_opportunity_sum"].to_list() == [
        260.0,
        0.0,
        110.0,
        150.0,
    ]
    assert raw["finite_target_base_fee_per_gas_hindsight_regret_sum"].to_list() == [
        160.0,
        0.0,
        140.0,
        220.0,
    ]
    assert raw["finite_target_base_fee_per_gas_savings_ratio_vs_immediate_k0"].to_list() == [
        0.025,
        None,
        -0.015,
        -0.035,
    ]
    assert raw[
        "finite_target_base_fee_per_gas_hindsight_opportunity_ratio_vs_immediate_k0"
    ].to_list() == [
        0.065,
        None,
        0.055,
        0.075,
    ]
    assert raw[
        "finite_target_base_fee_per_gas_hindsight_regret_ratio_vs_immediate_k0"
    ].to_list() == [
        0.04,
        None,
        0.07,
        0.11,
    ]
    assert raw["earliest_hindsight_label_accuracy"].to_list() == [0.5, None, 0.5, 0.5]

    log = evidence.filter(
        (pl.col("chain_id") == 1) & (pl.col("descriptor") == "signed_one_block_base_fee_log_change")
    )
    assert log["closed_parent_base_fee_per_gas_cutpoint_25"].null_count() == 4
    assert log["signed_one_block_base_fee_log_change_cutpoint_25"].to_list() == [0.0] * 4
    assert log["signed_one_block_base_fee_log_change_cutpoint_50"].to_list() == [0.0] * 4
    assert log["signed_one_block_base_fee_log_change_cutpoint_75"].to_list() == pytest.approx(
        [math.log(3.0)] * 4
    )
    assert log["signed_one_block_base_fee_log_change_cell_median"].to_list() == pytest.approx(
        [0.0, None, (math.log(2.0) + math.log(3.0)) / 2, (math.log(4.0) + math.log(5.0)) / 2]
    )

    def fails(
        name: str,
        message: str,
        ids: tuple[UUID, UUID, UUID] = evaluation_ids,
    ) -> None:
        output = tmp_path / f"{name}.tsv"
        with pytest.raises(ValueError, match=message):
            write_k5_fee_condition_evidence(tmp_path, ids, output)

    fails("duplicate", "distinct", (evaluation_ids[0], evaluation_ids[0], evaluation_ids[2]))
    fails("order", "chain", (evaluation_ids[1], evaluation_ids[0], evaluation_ids[2]))

    original_source = sources[artifact_ids[0]]
    sources[artifact_ids[0]] = BaselineSource(
        kind="baseline",
        corpus_id=corpus_ids[0],
        training_definition=TrainingDefinition(
            experiment=_source(corpus_ids[0]).experiment,
            model=LstmDefinition(
                family="lstm",
                hidden=1,
                layers=1,
                head_hidden=1,
                dropout=0.0,
            ),
            optimizer=AdamWMethod(learning_rate=0.001, weight_decay=0.0),
            training_batch=1,
            fit=FitMethod(
                accumulation=1,
                gradient_clip_norm=1.0,
                scheduler="none",
                seed=1,
                max_epochs=1,
                validate_every_completed_epoch=1,
                patience=0,
                min_delta=0.0,
                improvement="strict_lower",
                restore="earliest_best",
            ),
        ),
    )
    fails("source", "SelectedStudySource")
    sources[artifact_ids[0]] = _source(corpus_ids[0], context=100)
    fails("context", "C200")
    sources[artifact_ids[0]] = _source(corpus_ids[0], horizon=10)
    fails("horizon", "K=5")
    sources[artifact_ids[0]] = original_source

    corpora[corpus_ids[0]].request.definition.chain_id = 137
    fails("chain", "chain")
    corpora[corpus_ids[0]].request.definition.chain_id = 1

    reductions[evaluation_ids[0]] = reductions[evaluation_ids[0]].with_columns(
        pl.lit(1.0).alias("finite_target_base_fee_per_gas_savings_sum")
    )
    fails("regrouping", "recombine")
    reductions[evaluation_ids[0]] = reductions[evaluation_ids[1]]

    occupied = tmp_path / "occupied.tsv"
    occupied.write_text("owner", encoding="utf-8")
    with pytest.raises(ValueError, match="destination"):
        write_k5_fee_condition_evidence(tmp_path, evaluation_ids, occupied)
    assert occupied.read_text(encoding="utf-8") == "owner"
    hidden_destination = tmp_path / "hidden.tsv"
    hidden_destination.with_name(f".{hidden_destination.name}").write_text(
        "owner", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="hidden"):
        write_k5_fee_condition_evidence(tmp_path, evaluation_ids, hidden_destination)
    assert not hidden_destination.exists()

    sources[artifact_ids[2]] = _source(corpus_ids[2], horizon=10)
    late = tmp_path / "late.tsv"
    with pytest.raises(ValueError, match="K=5"):
        write_k5_fee_condition_evidence(tmp_path, evaluation_ids, late)
    assert not late.exists()
