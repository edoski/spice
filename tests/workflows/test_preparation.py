from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from spice.config import AcquireConfig, TuneConfig, WorkflowTask
from spice.storage.workflow_roots import CorpusRootHandle
from spice.workflows import preparation
from tests.root_handle_helpers import (
    corpus_handle,
    study_handle,
    tune_roots,
)


def test_acquire_preparation_materializes_roots_and_corpus_assembly_request(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    acquire_override,
) -> None:
    config = cast(
        AcquireConfig,
        load_workflow_config(
            WorkflowTask.ACQUIRE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=acquire_override(),
        ),
    )
    roots = preparation.materialize_acquire_roots(config)
    captured: dict[str, object] = {}
    assembly_request = object()

    def fake_prepare_corpus_assembly_request(*, config, roots):
        captured["corpus"] = config.corpus.name
        captured["corpus_id"] = roots.corpus.corpus_id
        return assembly_request

    monkeypatch.setattr(preparation, "materialize_acquire_roots", lambda _config: roots)
    monkeypatch.setattr(
        preparation,
        "prepare_corpus_assembly_request",
        fake_prepare_corpus_assembly_request,
    )

    prepared = preparation.prepare_acquire(config)

    assert prepared.roots is roots
    assert prepared.assembly_request is cast(Any, assembly_request)
    assert captured == {
        "corpus": config.corpus.name,
        "corpus_id": roots.corpus.corpus_id,
    }


def test_tune_preparation_uses_resolved_corpus_manifest(
    tmp_path,
    monkeypatch,
    load_workflow_config,
    model_workflow_override,
    tune_override,
) -> None:
    override = model_workflow_override() | tune_override()
    config = cast(
        TuneConfig,
        load_workflow_config(
            WorkflowTask.TUNE,
            workspace=tmp_path,
            surface="current_row_fee_dynamics",
            override=override,
        ),
    )
    corpus = corpus_handle(
        tmp_path / "outputs",
        chain_name="polygon",
        corpus_id=cast(str, config.corpus_id),
        corpus_name="polygon_dataset",
    )
    roots = tune_roots(
        tmp_path / "outputs",
        corpus=corpus,
        study=study_handle(
            tmp_path / "outputs",
            corpus=corpus,
            study_id="std_test",
            study_name=config.study.name,
        ),
    )
    corpus_manifest = SimpleNamespace(
        chain=SimpleNamespace(name="polygon", runtime=SimpleNamespace()),
        corpus=SimpleNamespace(name="polygon_dataset"),
    )
    captured: dict[str, object] = {}

    def fake_build_tuning_coverage_spec(active_config, *, corpus_manifest, **_kwargs):
        captured["chain"] = active_config.chain.name
        captured["manifest_chain"] = corpus_manifest.chain.name
        return SimpleNamespace(problem_contract=object(), feature_contract=object())

    monkeypatch.setattr(preparation, "materialize_tune_roots", lambda _config: roots)
    monkeypatch.setattr(CorpusRootHandle, "load_manifest", lambda _self: corpus_manifest)
    monkeypatch.setattr(
        preparation,
        "_build_tuning_coverage_spec",
        fake_build_tuning_coverage_spec,
    )
    monkeypatch.setattr(
        preparation,
        "training_coverage_requirement",
        lambda *_args: object(),
    )
    monkeypatch.setattr(
        preparation,
        "validate_corpus_coverage",
        lambda *_args, **_kwargs: None,
    )

    prepared = preparation.prepare_tune(config)

    assert prepared.roots is roots
    assert captured == {"chain": "ethereum", "manifest_chain": "polygon"}
