from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from spice.config import EvaluateConfig, WorkflowTask
from spice.config.models import ChainRuntimeSpec
from spice.core.errors import ConfigResolutionError
from spice.modeling.artifact_inference import prepare_artifact_inference_context
from spice.storage.workflow_paths import WorkflowIdentity, build_workflow_paths


def _evaluate_config(load_workflow_config, tmp_path, model_workflow_override) -> EvaluateConfig:
    del model_workflow_override
    return cast(
        EvaluateConfig,
        load_workflow_config(
            WorkflowTask.EVALUATE,
            workspace=tmp_path,
        ),
    )


def _paths(config: EvaluateConfig):
    return build_workflow_paths(
        output_root=config.storage.root,
        chain_name="ethereum",
        identity=WorkflowIdentity(
            corpus_id=config.dataset_id,
            artifact_id=config.artifact_id,
        ),
    )


def _install_artifact_context_fakes(monkeypatch, config: EvaluateConfig, *, max_delay: int = 36):
    calls: list[str] = []
    runtime_metadata = SimpleNamespace(compiler_runtime_metadata={"compiler": "payload"})
    compiler_metadata = object()
    loaded_artifact = SimpleNamespace(
        manifest=SimpleNamespace(
            chain_name="ethereum",
            max_delay_seconds=max_delay,
            dataset_builder=SimpleNamespace(id="fixed_sequence_temporal"),
            builder_runtime_metadata=runtime_metadata,
            scaler=object(),
            max_candidate_slots=4,
            model=object(),
            features=object(),
            feature_graph_fingerprint="feature-fp",
            feature_prerequisites=("base_fee",),
            problem=object(),
            prediction=SimpleNamespace(id="icdcs_2026", family_id="fee_offset"),
        ),
        model=object(),
        dataset_builder_contract=object(),
        representation_contract=object(),
    )
    feature_contract = SimpleNamespace(
        feature_graph_fingerprint="feature-fp",
        feature_prerequisites=("base_fee",),
    )
    problem_contract = SimpleNamespace(
        compiler_id="observed_time_window",
        max_delay_seconds=max_delay,
        required_history_seconds=120,
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
    corpus_manifest = SimpleNamespace(
        chain=SimpleNamespace(
            name="ethereum",
            runtime=ChainRuntimeSpec(
                chain_id=1,
                uses_poa_extra_data=False,
                nominal_block_time_seconds=12.0,
            ),
        ),
        coverage=SimpleNamespace(
            evaluation=SimpleNamespace(start_timestamp=1000, end_timestamp=2000)
        ),
    )

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.load_training_artifact",
        lambda artifact_root: (
            calls.append(f"load_artifact:{artifact_root.name}") or loaded_artifact
        ),
    )
    monkeypatch.setattr(
        "spice.modeling.artifact_inference.compile_feature_contract",
        lambda **_kwargs: calls.append("compile_features") or feature_contract,
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
        lambda _path: calls.append("load_dataset_manifest") or corpus_manifest,
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
    paths = _paths(config)
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
        "load_dataset_manifest",
        "compile_features",
        "compile_problem",
        "compile_prediction",
        "compile_evaluator",
        "validate_coverage",
        "coerce_runtime",
        "decode_compiler",
        "load_blocks:history",
        "load_blocks:evaluation",
        "prepare_inference",
    ]


def test_artifact_inference_uses_exclusive_end_after_final_observed_timestamp(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(load_workflow_config, tmp_path, model_workflow_override)
    paths = _paths(config)
    captured: dict[str, int] = {}
    _install_artifact_context_fakes(monkeypatch, config)

    def fake_prepare_inference_dataset(*_args, **kwargs):
        captured["window_start_timestamp"] = kwargs["window_start_timestamp"]
        captured["window_end_timestamp"] = kwargs["window_end_timestamp"]
        return SimpleNamespace(
            n_history_rows=10,
            n_evaluation_rows=5,
            sample_count=1,
            execution_policy=object(),
            store=object(),
            sample_indices=np.array([0], dtype=np.int64),
        )

    monkeypatch.setattr(
        "spice.modeling.artifact_inference.prepare_inference_dataset",
        fake_prepare_inference_dataset,
    )

    prepare_artifact_inference_context(config, paths=paths)

    assert captured == {
        "window_start_timestamp": 1000,
        "window_end_timestamp": 2001,
    }


def test_artifact_inference_context_rejects_artifact_semantic_mismatch(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
) -> None:
    config = _evaluate_config(load_workflow_config, tmp_path, model_workflow_override)
    paths = _paths(config)
    calls, loaded_artifact, *_ = _install_artifact_context_fakes(monkeypatch, config)

    loaded_artifact.manifest.feature_graph_fingerprint = "other"

    with pytest.raises(ConfigResolutionError, match="feature graph"):
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
    config = config.model_copy(update={"delay_seconds": 36})
    paths = _paths(config)
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
    paths = _paths(config)
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
