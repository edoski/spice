from __future__ import annotations

from typing import cast

from spice.config import AcquireConfig, EvaluateConfig, TrainConfig, TuneConfig, WorkflowTask
from spice.config.models import ArtifactVariant
from spice.storage.catalog.materialization import materialize_catalog_root
from spice.storage.workflow_root_materialization import (
    materialize_acquire_roots,
    materialize_evaluate_roots,
    materialize_train_roots,
    materialize_tune_roots,
    materialize_workflow_root_facts,
    produced_artifact_id,
    produced_corpus_id,
    produced_study_id,
)
from spice.storage.workflow_roots import (
    BaselineTrainWorkflowRoots,
    CorpusRootHandle,
    TunedTrainWorkflowRoots,
    artifact_root_handle_from_record,
    corpus_root_handle_from_record,
    produced_artifact_root_handle,
    produced_corpus_root_handle,
    produced_study_root_handle,
    study_root_handle_from_record,
)
from tests.catalog_helpers import artifact_record, dataset_record, study_record


def _dataset_record(tmp_path, *, corpus_id: str, chain_name: str = "ethereum"):
    root = tmp_path / "catalog" / "datasets" / corpus_id
    return dataset_record(
        root,
        corpus_id=corpus_id,
        corpus_name=f"{chain_name}_dataset",
        chain_name=chain_name,
        state_db=root / "custom-state.sqlite",
    )


def _study_record(tmp_path, *, corpus_id: str, chain_name: str = "ethereum"):
    root = tmp_path / "catalog" / "studies" / "std_existing"
    return study_record(
        root,
        study_id="std_existing",
        study_name="existing_study",
        corpus_id=corpus_id,
        corpus_name=f"{chain_name}_dataset",
        chain_name=chain_name,
        features_id="core_fee_dynamics",
        prediction_id="icdcs_2026",
        model_id="lstm",
        problem_id="current_row_nominal",
        state_db=root / "custom-state.sqlite",
    )


def _artifact_record(
    tmp_path,
    *,
    artifact_id: str = "art_existing",
    corpus_id: str,
    chain_name: str = "ethereum",
):
    root = tmp_path / "catalog" / "artifacts" / artifact_id
    return artifact_record(
        root,
        artifact_id=artifact_id,
        corpus_id=corpus_id,
        corpus_name=f"{chain_name}_dataset",
        chain_name=chain_name,
        features_id="core_fee_dynamics",
        prediction_id="icdcs_2026",
        model_id="lstm",
        problem_id="current_row_nominal",
        variant="baseline",
        study_id=None,
        study_name=None,
        state_db=root / "custom-state.sqlite",
    )


def test_acquire_producer_roots_use_produced_corpus_identity(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        AcquireConfig,
        load_workflow_config(WorkflowTask.ACQUIRE, workspace=tmp_path),
    )

    roots = materialize_acquire_roots(config)

    assert roots.corpus.corpus_id == produced_corpus_id(config)
    assert roots.corpus.corpus_name == config.corpus.name
    assert roots.corpus.chain_name == config.chain.name


def test_root_handle_constructors_own_catalog_and_producer_shapes(tmp_path) -> None:
    storage_root = tmp_path / "outputs"
    corpus_record = _dataset_record(tmp_path, corpus_id="cor_existing", chain_name="polygon")
    study = _study_record(tmp_path, corpus_id=corpus_record.corpus_id, chain_name="polygon")
    artifact = _artifact_record(
        tmp_path,
        artifact_id="art_existing",
        corpus_id=corpus_record.corpus_id,
        chain_name="polygon",
    )

    corpus = corpus_root_handle_from_record(storage_root, corpus_record)
    study_handle = study_root_handle_from_record(storage_root, study)
    artifact_handle = artifact_root_handle_from_record(storage_root, artifact)
    produced_corpus = produced_corpus_root_handle(
        storage_root,
        chain_name="polygon",
        corpus_id="cor_new",
        corpus_name="new_dataset",
    )
    produced_study = produced_study_root_handle(
        storage_root,
        corpus=produced_corpus,
        study_id="std_new",
        study_name="new_study",
    )
    produced_artifact = produced_artifact_root_handle(
        storage_root,
        corpus=produced_corpus,
        artifact_id="art_new",
        variant=ArtifactVariant.TUNED,
        study=produced_study,
    )
    corpus_location = materialize_catalog_root(storage_root, corpus_record)

    assert corpus.state_db_path == corpus_location.state_db_path
    assert corpus.blocks_dir == corpus_location.root_path / "blocks"
    assert study_handle.corpus_id == corpus.corpus_id
    assert artifact_handle.variant is ArtifactVariant.BASELINE
    assert produced_corpus.root_path == storage_root / "corpora" / "polygon" / "cor_new"
    assert produced_study.corpus_name == "new_dataset"
    assert produced_artifact.study_id == "std_new"


def test_tune_consumer_roots_resolve_dataset_and_produced_study(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        TuneConfig,
        load_workflow_config(WorkflowTask.TUNE, workspace=tmp_path),
    )
    corpus = _dataset_record(tmp_path, corpus_id=config.corpus_id, chain_name="polygon")
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_corpus_record",
        lambda *_args, **_kwargs: corpus,
    )

    roots = materialize_tune_roots(config)
    dataset_location = materialize_catalog_root(config.storage.root, corpus)

    assert roots.corpus.corpus_id == config.corpus_id
    assert roots.corpus.state_db_path == dataset_location.state_db_path
    assert roots.study.study_id == produced_study_id(config)
    assert roots.study.corpus_id == corpus.corpus_id
    assert roots.study.chain_name == "polygon"


def test_baseline_train_consumer_roots_resolve_dataset_and_produced_artifact(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(WorkflowTask.TRAIN, workspace=tmp_path),
    )
    assert config.corpus_id is not None
    corpus = _dataset_record(tmp_path, corpus_id=config.corpus_id, chain_name="polygon")
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_corpus_record",
        lambda *_args, **_kwargs: corpus,
    )

    roots = materialize_train_roots(config)
    dataset_location = materialize_catalog_root(config.storage.root, corpus)

    assert isinstance(roots, BaselineTrainWorkflowRoots)
    assert roots.corpus.state_db_path == dataset_location.state_db_path
    assert roots.artifact.artifact_id == produced_artifact_id(
        config,
        corpus_id=corpus.corpus_id,
    )
    assert roots.artifact.variant is ArtifactVariant.BASELINE


def test_tuned_train_consumer_roots_use_study_dataset_for_artifact_identity(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            variant="tuned",
        ),
    )
    study = _study_record(tmp_path, corpus_id="cor_from_study", chain_name="polygon")
    corpus = _dataset_record(tmp_path, corpus_id=study.corpus_id, chain_name="polygon")
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_study_record",
        lambda *_args, **_kwargs: study,
    )
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_corpus_record",
        lambda *_args, **_kwargs: corpus,
    )

    roots = materialize_train_roots(config)
    study_location = materialize_catalog_root(config.storage.root, study)

    assert isinstance(roots, TunedTrainWorkflowRoots)
    assert roots.study.state_db_path == study_location.state_db_path
    assert roots.corpus.corpus_id == "cor_from_study"
    assert roots.artifact.artifact_id == produced_artifact_id(
        config,
        corpus_id="cor_from_study",
    )
    assert roots.artifact.study_id == study.study_id


def test_evaluate_consumer_roots_resolve_dataset_and_artifact_independently(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        EvaluateConfig,
        load_workflow_config(WorkflowTask.EVALUATE, workspace=tmp_path),
    )
    corpus = _dataset_record(tmp_path, corpus_id=config.corpus_id, chain_name="polygon")
    artifact = _artifact_record(
        tmp_path,
        artifact_id=config.artifact_id,
        corpus_id="cor_artifact",
        chain_name="polygon",
    )
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_corpus_record",
        lambda *_args, **_kwargs: corpus,
    )
    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_artifact_record",
        lambda *_args, **_kwargs: artifact,
    )

    roots = materialize_evaluate_roots(config)
    dataset_location = materialize_catalog_root(config.storage.root, corpus)
    artifact_location = materialize_catalog_root(config.storage.root, artifact)

    assert roots.corpus.corpus_id == config.corpus_id
    assert roots.artifact.artifact_id == config.artifact_id
    assert roots.corpus.state_db_path == dataset_location.state_db_path
    assert roots.artifact.state_db_path == artifact_location.state_db_path
    assert roots.artifact.corpus_id == "cor_artifact"


def test_corpus_root_handle_loads_manifest(tmp_path, monkeypatch) -> None:
    corpus = _dataset_record(tmp_path, corpus_id="cor_existing")
    location = materialize_catalog_root(tmp_path, corpus)
    root = CorpusRootHandle(
        storage_root=tmp_path,
        corpus_id=corpus.corpus_id,
        corpus_name=corpus.corpus_name,
        chain_name=corpus.chain_name,
        root_path=location.root_path,
        state_db_path=location.state_db_path,
        blocks_dir=location.root_path / "blocks",
    )
    manifest = object()
    calls: list[object] = []

    monkeypatch.setattr(
        "spice.storage.workflow_roots.load_corpus_manifest",
        lambda db_path: calls.append(db_path) or manifest,
    )

    assert root.load_manifest() is manifest
    assert calls == [location.state_db_path]


def test_workflow_root_facts_use_known_benchmark_sources_before_catalog(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(
            WorkflowTask.TRAIN,
            workspace=tmp_path,
            variant="tuned",
        ),
    )
    config = config.model_copy(update={"study_id": "std_from_benchmark", "corpus_id": None})

    facts = materialize_workflow_root_facts(
        config,
        known_study_corpus_ids={"std_from_benchmark": "cor_from_benchmark"},
    )

    assert facts.consumed.study_id == "std_from_benchmark"
    assert facts.consumed_study_corpus_id == "cor_from_benchmark"
    assert facts.produced_artifact_corpus_id == "cor_from_benchmark"


def test_workflow_root_facts_do_not_resolve_baseline_train_dataset_catalog(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        TrainConfig,
        load_workflow_config(WorkflowTask.TRAIN, workspace=tmp_path),
    )

    def fail_resolve_dataset(*_args, **_kwargs):
        raise AssertionError("scalar baseline train facts must not resolve corpus catalog")

    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_corpus_record",
        fail_resolve_dataset,
    )

    facts = materialize_workflow_root_facts(config)

    assert facts.consumed.corpus_id == config.corpus_id
    assert facts.produced_artifact_corpus_id == config.corpus_id


def test_workflow_root_facts_preserve_evaluate_dataset_and_artifact_source(
    tmp_path,
    load_workflow_config,
) -> None:
    config = cast(
        EvaluateConfig,
        load_workflow_config(WorkflowTask.EVALUATE, workspace=tmp_path),
    )

    facts = materialize_workflow_root_facts(
        config,
        known_artifact_corpus_ids={config.artifact_id: "cor_artifact_source"},
    )

    assert facts.consumed.corpus_id == config.corpus_id
    assert facts.consumed.artifact_id == config.artifact_id
    assert facts.consumed_artifact_corpus_id == "cor_artifact_source"


def test_workflow_root_facts_use_artifact_source_corpus_before_catalog(
    tmp_path,
    monkeypatch,
    load_workflow_config,
) -> None:
    config = cast(
        EvaluateConfig,
        load_workflow_config(WorkflowTask.EVALUATE, workspace=tmp_path),
    )

    def fail_resolve_artifact(*_args, **_kwargs):
        raise AssertionError("artifact_from source facts must not resolve artifact catalog")

    monkeypatch.setattr(
        "spice.storage.workflow_root_materialization.resolve_artifact_record",
        fail_resolve_artifact,
    )

    facts = materialize_workflow_root_facts(
        config,
        artifact_source_corpus_id="cor_artifact_from_train",
    )

    assert facts.consumed.corpus_id == config.corpus_id
    assert facts.consumed.artifact_id == config.artifact_id
    assert facts.source.artifact_corpus_id == "cor_artifact_from_train"
    assert facts.consumed_artifact_corpus_id == "cor_artifact_from_train"
