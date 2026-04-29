from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from spice.config import EvaluateConfig, WorkflowTask
from spice.core.errors import ConfigResolutionError
from spice.modeling.artifact_inference import prepare_artifact_inference_context
from spice.storage.workflow_paths import resolve_workflow_paths


def _evaluate_config(load_workflow_config, tmp_path, model_workflow_override) -> EvaluateConfig:
    return cast(
        EvaluateConfig,
        load_workflow_config(
            WorkflowTask.EVALUATE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=model_workflow_override(),
        ),
    )


def _install_artifact_context_fakes(monkeypatch, config: EvaluateConfig, *, max_delay: int = 36):
    calls: list[str] = []
    runtime_metadata = SimpleNamespace(compiler_runtime_metadata={"compiler": "payload"})
    compiler_metadata = object()
    loaded_artifact = SimpleNamespace(
        manifest=SimpleNamespace(
            max_delay_seconds=max_delay,
            dataset_builder=config.dataset_builder,
            builder_runtime_metadata=runtime_metadata,
            scaler=object(),
            max_candidate_slots=4,
            model=config.model,
        ),
        model=object(),
        representation_contract=object(),
    )
    feature_contract = SimpleNamespace()
    dataset_builder_contract = SimpleNamespace()
    problem_contract = SimpleNamespace(
        compiler_id="observed_time_window",
        max_delay_seconds=config.problem.max_delay_seconds,
        required_history_seconds=config.problem.lookback_seconds,
        warmup_rows=0,
    )
    prediction_contract = SimpleNamespace(decoded_result_id="offsets")
    evaluator_contract = SimpleNamespace(
        evaluation_id="poisson_replay_2h",
        config_payload={"id": "poisson_replay_2h"},
        metric_descriptors=(),
    )
    prepared = SimpleNamespace(
        n_history_rows=10,
        n_evaluation_rows=5,
        sample_count=2,
        execution_policy=object(),
        store=object(),
        sample_indices=np.array([0, 1], dtype=np.int64),
    )

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.load_training_artifact",
        lambda artifact_root: (
            calls.append(f"load_artifact:{artifact_root.name}") or loaded_artifact
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.validate_artifact_semantics",
        lambda *_args, **_kwargs: calls.append("validate_artifact")
        or SimpleNamespace(
            feature_contract=feature_contract,
            dataset_builder_contract=dataset_builder_contract,
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.compile_problem_contract",
        lambda **_kwargs: calls.append("compile_problem") or problem_contract,
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.compile_prediction_contract",
        lambda **_kwargs: calls.append("compile_prediction") or prediction_contract,
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.compile_evaluator_contract",
        lambda _config: calls.append("compile_evaluator") or evaluator_contract,
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.load_dataset_manifest",
        lambda _path: calls.append("load_dataset_manifest") or object(),
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.validate_corpus_coverage",
        lambda *_args, **_kwargs: calls.append("validate_coverage"),
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.coerce_builder_runtime_metadata",
        lambda _builder_id, metadata: calls.append("coerce_runtime") or metadata,
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.compiler_runtime_metadata_from_builder_payload",
        lambda metadata, **_kwargs: calls.append("decode_compiler") or compiler_metadata,
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.load_block_frame",
        lambda path: calls.append(f"load_blocks:{path.name}") or object(),
    )

    def fake_prepare_inference_dataset(*_args, **kwargs):
        calls.append("prepare_inference")
        assert kwargs["builder_runtime_metadata"] is runtime_metadata
        assert kwargs["compiler_runtime_metadata"] is compiler_metadata
        assert kwargs["max_candidate_slots"] == loaded_artifact.manifest.max_candidate_slots
        return prepared

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.prepare_inference_dataset",
        fake_prepare_inference_dataset,
    )
    return calls, loaded_artifact, prepared, evaluator_contract, prediction_contract


def test_artifact_inference_context_prepares_scoring_inputs(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(load_workflow_config, tmp_path, model_workflow_override)
    paths = resolve_workflow_paths(config)
    calls, loaded_artifact, prepared, evaluator_contract, prediction_contract = (
        _install_artifact_context_fakes(monkeypatch, config)
    )

    context = prepare_artifact_inference_context(config, paths=paths)

    assert context.loaded_artifact is loaded_artifact
    assert context.prepared is prepared
    assert context.evaluator_contract is evaluator_contract
    assert context.scoring_context.model is loaded_artifact.model
    assert context.scoring_context.prediction_contract is prediction_contract
    assert context.scoring_context.sample_indices.tolist() == [0, 1]
    assert calls == [
        f"load_artifact:{paths.artifact_root.name}",
        "validate_artifact",
        "compile_problem",
        "compile_prediction",
        "compile_evaluator",
        "load_dataset_manifest",
        "validate_coverage",
        "coerce_runtime",
        "decode_compiler",
        "load_blocks:history",
        "load_blocks:evaluation",
        "prepare_inference",
    ]


def test_artifact_inference_context_rejects_artifact_semantic_mismatch(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(load_workflow_config, tmp_path, model_workflow_override)
    paths = resolve_workflow_paths(config)
    _install_artifact_context_fakes(monkeypatch, config)

    def fail_validation(*_args, **_kwargs):
        raise ConfigResolutionError("Configured model does not match")

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.validate_artifact_semantics",
        fail_validation,
    )

    with pytest.raises(ConfigResolutionError, match="Configured model"):
        prepare_artifact_inference_context(config, paths=paths)


def test_artifact_inference_context_rejects_delay_beyond_artifact_capability(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(
        load_workflow_config,
        tmp_path,
        lambda: model_workflow_override(max_delay_seconds=36, delay_seconds=36),
    )
    paths = resolve_workflow_paths(config)
    _install_artifact_context_fakes(monkeypatch, config, max_delay=12)

    with pytest.raises(ConfigResolutionError, match="delay_seconds exceeds artifact capability"):
        prepare_artifact_inference_context(config, paths=paths)


def test_artifact_inference_context_validates_coverage_before_inference_preparation(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(load_workflow_config, tmp_path, model_workflow_override)
    paths = resolve_workflow_paths(config)
    calls, *_ = _install_artifact_context_fakes(monkeypatch, config)

    def fail_coverage(*_args, **_kwargs):
        calls.append("validate_coverage")
        raise ConfigResolutionError("coverage mismatch")

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.validate_corpus_coverage",
        fail_coverage,
    )

    with pytest.raises(ConfigResolutionError, match="coverage mismatch"):
        prepare_artifact_inference_context(config, paths=paths)

    assert "prepare_inference" not in calls
