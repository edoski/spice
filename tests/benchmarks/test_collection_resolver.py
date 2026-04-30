from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from spice.benchmarks.collection_resolver import resolve_benchmark_evaluation
from spice.config import EvaluateConfig, StorageSpec
from spice.config.registry import load_named_group
from spice.core.errors import SelectorResolutionError, SpiceOperatorError
from spice.evaluation.registry import coerce_evaluator_config


def _evaluate_config(tmp_path: Path) -> EvaluateConfig:
    return EvaluateConfig(
        storage=StorageSpec(root=tmp_path / "outputs"),
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        evaluation=coerce_evaluator_config(load_named_group("poisson_replay_2h", "evaluation")),
        delay_seconds=36,
    )


def _summary(config, *, delay_seconds: int | None = None, evaluation_id: str | None = None):
    return SimpleNamespace(
        runtime=SimpleNamespace(
            delay_seconds=config.delay_seconds if delay_seconds is None else delay_seconds,
            evaluation_id=config.evaluation.id if evaluation_id is None else evaluation_id,
        )
    )


def _manifest(*, max_delay_seconds: int = 36):
    return SimpleNamespace(max_delay_seconds=max_delay_seconds)


def test_collection_resolver_pulls_baseline_artifact_and_loads_matching_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)
    session = SimpleNamespace()
    pulled: list[object] = []
    training = SimpleNamespace(runtime=SimpleNamespace(test_metrics=None))
    summary = _summary(config)
    record = SimpleNamespace(state_db_path=tmp_path / "state.sqlite")

    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.pull_artifact_from_cluster",
        lambda **kwargs: pulled.append(kwargs) or (SimpleNamespace(), False),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.resolve_artifact_record",
        lambda *_args, **_kwargs: record,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_training_summary",
        lambda _path: training,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_artifact_manifest",
        lambda _path: _manifest(),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.list_evaluation_summaries",
        lambda _path: [summary],
    )

    resolved = resolve_benchmark_evaluation(config, session=session)

    assert resolved is not None
    assert resolved.evaluation is summary
    assert resolved.training is training
    assert pulled[0]["session"] is session
    assert pulled[0]["artifact_id"] == config.artifact_id
    assert pulled[0]["replace"] is True


def test_collection_resolver_returns_none_when_summary_is_missing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)
    record = SimpleNamespace(state_db_path=tmp_path / "state.sqlite")
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.pull_artifact_from_cluster",
        lambda **_kwargs: (SimpleNamespace(), False),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.resolve_artifact_record",
        lambda *_args, **_kwargs: record,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_training_summary",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_artifact_manifest",
        lambda _path: _manifest(),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.list_evaluation_summaries",
        lambda _path: [],
    )

    assert resolve_benchmark_evaluation(config, session=SimpleNamespace()) is None


def test_collection_resolver_rejects_duplicate_matching_summaries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)
    record = SimpleNamespace(state_db_path=tmp_path / "state.sqlite")
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.pull_artifact_from_cluster",
        lambda **_kwargs: (SimpleNamespace(), False),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.resolve_artifact_record",
        lambda *_args, **_kwargs: record,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_training_summary",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_artifact_manifest",
        lambda _path: _manifest(),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.list_evaluation_summaries",
        lambda _path: [_summary(config), _summary(config)],
    )

    with pytest.raises(SpiceOperatorError, match="Multiple evaluation summaries"):
        resolve_benchmark_evaluation(config, session=SimpleNamespace())


def test_collection_resolver_matches_default_delay_to_artifact_capability(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path).model_copy(update={"delay_seconds": None})
    matching = _summary(config, delay_seconds=72)
    stale = _summary(config, delay_seconds=36)
    record = SimpleNamespace(state_db_path=tmp_path / "state.sqlite")
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.pull_artifact_from_cluster",
        lambda **_kwargs: (SimpleNamespace(), False),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.resolve_artifact_record",
        lambda *_args, **_kwargs: record,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_training_summary",
        lambda _path: None,
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.load_artifact_manifest",
        lambda _path: _manifest(max_delay_seconds=72),
    )
    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.list_evaluation_summaries",
        lambda _path: [stale, matching],
    )

    resolved = resolve_benchmark_evaluation(config, session=SimpleNamespace())

    assert resolved is not None
    assert resolved.evaluation is matching


def test_collection_resolver_surfaces_selector_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = _evaluate_config(tmp_path)

    def missing_artifact(**_kwargs):
        raise SelectorResolutionError(kind="artifact", records=[])

    monkeypatch.setattr(
        "spice.benchmarks.collection_resolver.pull_artifact_from_cluster",
        missing_artifact,
    )

    with pytest.raises(SelectorResolutionError):
        resolve_benchmark_evaluation(config, session=SimpleNamespace())
