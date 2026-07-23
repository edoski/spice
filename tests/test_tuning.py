from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from pytest import MonkeyPatch

from fable import tuning
from fable.config import (
    BlockWindow,
    Deployment,
    ExperimentSemantics,
    FitMethod,
    LstmDefinition,
    Method,
    TuneRequest,
)
from fable.study import RetainedResult

STUDY_ID = UUID("10000000-0000-4000-8000-000000000001")
CORPUS_ID = UUID("20000000-0000-4000-8000-000000000001")

FIT = FitMethod(
    learning_rate=3e-4,
    weight_decay=1e-4,
    accumulation=1,
    gradient_clip_norm=0.75,
    seed=17,
    max_epochs=12,
    validate_every_completed_epoch=1,
    patience=4,
    min_delta=0.01,
)
METHOD = Method(
    model=LstmDefinition(
        family="lstm",
        hidden=16,
        layers=1,
        head_hidden=8,
        dropout=0.2,
    ),
    fit=FIT,
)
OTHER_METHOD = METHOD.model_copy(
    update={"fit": FIT.model_copy(update={"seed": 18})},
)
EXPERIMENT = ExperimentSemantics(
    training_window=BlockWindow(
        first_parent_block=10,
        last_parent_block=20,
    ),
    validation_window=BlockWindow(
        first_parent_block=30,
        last_parent_block=35,
    ),
    context_blocks=3,
    horizon_blocks=2,
    ordered_features=("log_base_fee_per_gas",),
)
REQUEST = TuneRequest(
    workflow="tune",
    study_id=STUDY_ID,
    corpus_id=CORPUS_ID,
    experiment=EXPERIMENT,
    methods=(METHOD,),
)
MULTI_METHOD_REQUEST = REQUEST.model_copy(
    update={"methods": (METHOD, OTHER_METHOD)},
)
DEPLOYMENT = Deployment(
    evaluation_batch_size=64,
    num_workers=0,
    pin_memory=False,
    prefetch_factor=None,
    persistent_workers=False,
    deterministic=True,
    benchmark=False,
    float32_matmul_precision="highest",
    cuda_matmul_allow_tf32=False,
    cudnn_allow_tf32=False,
)
RESULT = RetainedResult(
    method=METHOD,
    objective=0.4,
    selected_epoch=3,
    completed_epochs=8,
)


def test_run_candidate_prepares_fits_and_retains_one_result(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    corpus = object()
    prepared = object()
    calls: list[tuple[str, tuple[object, ...]]] = []

    def load_corpus(storage_root: Path, corpus_id: UUID) -> object:
        calls.append(("load", (storage_root, corpus_id)))
        return corpus

    def prepare_fit_history(
        loaded_corpus: object,
        experiment: ExperimentSemantics,
    ) -> object:
        calls.append(("prepare", (loaded_corpus, experiment)))
        return prepared

    def run_fit(
        request: TuneRequest,
        method: Method,
        preparation: object,
        scratch: Path,
        deployment: Deployment,
    ) -> RetainedResult:
        assert scratch.is_dir()
        calls.append(("fit", (request, method, preparation, scratch, deployment)))
        return RESULT

    def retain_result(
        storage_root: Path,
        request: TuneRequest,
        result: RetainedResult,
    ) -> None:
        calls.append(("retain", (storage_root, request, result)))

    monkeypatch.setattr(tuning, "load_corpus", load_corpus)
    monkeypatch.setattr(tuning, "prepare_fit_history", prepare_fit_history)
    monkeypatch.setattr(tuning, "_run_candidate", run_fit)
    monkeypatch.setattr(tuning, "retain_result", retain_result)

    tuning.run_candidate(tmp_path, REQUEST, METHOD, DEPLOYMENT)

    scratch = tmp_path / "studies" / f".{STUDY_ID}" / "candidate-0"
    assert calls == [
        ("load", (tmp_path, CORPUS_ID)),
        ("prepare", (corpus, EXPERIMENT)),
        ("fit", (REQUEST, METHOD, prepared, scratch, DEPLOYMENT)),
        ("retain", (tmp_path, REQUEST, RESULT)),
    ]
    assert not scratch.exists()


def test_run_candidate_uses_stable_distinct_method_scratch(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    scratches: list[Path] = []

    def run_fit(
        request: TuneRequest,
        method: Method,
        preparation: object,
        scratch: Path,
        deployment: Deployment,
    ) -> RetainedResult:
        scratches.append(scratch)
        return RESULT.model_copy(update={"method": method})

    monkeypatch.setattr(tuning, "load_corpus", lambda *_: object())
    monkeypatch.setattr(tuning, "prepare_fit_history", lambda *_: object())
    monkeypatch.setattr(tuning, "_run_candidate", run_fit)
    monkeypatch.setattr(tuning, "retain_result", lambda *_: None)

    tuning.run_candidate(tmp_path, MULTI_METHOD_REQUEST, METHOD, DEPLOYMENT)
    tuning.run_candidate(tmp_path, MULTI_METHOD_REQUEST, OTHER_METHOD, DEPLOYMENT)
    tuning.run_candidate(tmp_path, MULTI_METHOD_REQUEST, METHOD, DEPLOYMENT)

    study_scratch = tmp_path / "studies" / f".{STUDY_ID}"
    assert scratches == [
        study_scratch / "candidate-0",
        study_scratch / "candidate-1",
        study_scratch / "candidate-0",
    ]


@pytest.mark.parametrize("failure", ["fit", "retention"])
def test_run_candidate_preserves_scratch_after_failure(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    failure: str,
) -> None:
    scratch = tmp_path / "studies" / f".{STUDY_ID}" / "candidate-0"

    def run_fit(*_: object) -> RetainedResult:
        (scratch / "last.ckpt").write_bytes(b"checkpoint")
        if failure == "fit":
            raise RuntimeError("fit failed")
        return RESULT

    def retain_result(*_: object) -> None:
        if failure == "retention":
            raise RuntimeError("retention failed")

    monkeypatch.setattr(tuning, "load_corpus", lambda *_: object())
    monkeypatch.setattr(tuning, "prepare_fit_history", lambda *_: object())
    monkeypatch.setattr(tuning, "_run_candidate", run_fit)
    monkeypatch.setattr(tuning, "retain_result", retain_result)

    with pytest.raises(RuntimeError, match=f"{failure} failed"):
        tuning.run_candidate(tmp_path, REQUEST, METHOD, DEPLOYMENT)

    assert (scratch / "last.ckpt").read_bytes() == b"checkpoint"
