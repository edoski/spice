"""DISPOSABLE ISSUE-13 PROTOTYPE — delete after the owner decision.

Question: after the approved flat typed paths and direct loaders, does a public
typed store hide any real filesystem/discovery/lifecycle complexity, or does it
only bind ``storage_root`` and rename direct owner functions?

Study red-team: can one private single-writer ``progress.json`` contain only the
validated completed-trial prefix, resume the next trial honestly, disappear
after immutable publication, and remain invisible to every public consumer?

Run: uv run python docs/research/issue-13-direct-storage/prototype.py

This uses only a temporary directory. It is not production code or a test.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from uuid import UUID

CORPUS_A = "a" * 64
CORPUS_B = "b" * 64
STUDY_A = "11111111-1111-4111-8111-111111111111"
ARTIFACT_A = "22222222-2222-4222-8222-222222222222"
EVALUATION_A = "33333333-3333-4333-8333-333333333333"
OTHER_UUID = "44444444-4444-4444-8444-444444444444"


class InvalidObject(ValueError):
    pass


class Conflict(ValueError):
    pass


class FitInterrupted(RuntimeError):
    pass


@dataclass(frozen=True)
class Corpus:
    corpus_id: str
    chain_id: int
    identity: bytes


@dataclass(frozen=True)
class Study:
    study_id: str
    corpus_id: str
    trials: tuple[int, ...]


@dataclass(frozen=True)
class TuneRequestFixture:
    """Minimal stand-in for the already-persisted exact TuneRequest."""

    study_id: str
    corpus_id: str
    seed: int
    budget: int


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    corpus_id: str
    chain_id: int
    study_id: str | None
    trial_number: int | None
    exact: bytes


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    artifact_id: str
    corpus_id: str
    chain_id: int
    exact: bytes


def _corpus_id(value: str) -> str:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise InvalidObject("corpus id must be 64 lowercase hex characters")
    return value


def _uuid4(value: str) -> str:
    try:
        parsed = UUID(value)
    except ValueError as error:
        raise InvalidObject("id must be a canonical UUIDv4") from error
    if parsed.version != 4 or str(parsed) != value:
        raise InvalidObject("id must be a canonical UUIDv4")
    return value


def corpus_path(storage_root: Path, corpus_id: str) -> Path:
    return storage_root / "corpora" / _corpus_id(corpus_id)


def study_path(storage_root: Path, study_id: str) -> Path:
    return storage_root / "studies" / _uuid4(study_id)


def artifact_path(storage_root: Path, artifact_id: str) -> Path:
    return storage_root / "artifacts" / _uuid4(artifact_id)


def evaluation_path(storage_root: Path, evaluation_id: str) -> Path:
    return storage_root / "evaluations" / f"{_uuid4(evaluation_id)}.json"


def _require_contained(path: Path, storage_root: Path) -> None:
    root = storage_root.resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError as error:
        raise InvalidObject("path escapes storage root") from error


def _require_plain_path(path: Path, storage_root: Path, *, directory: bool) -> None:
    _require_contained(path, storage_root)
    if path.is_symlink():
        raise InvalidObject("canonical object may not be a symlink")
    if directory and not path.is_dir():
        raise InvalidObject("expected a directory package")
    if not directory and not path.is_file():
        raise InvalidObject("expected a regular JSON file")


def _json(path: Path) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidObject(f"malformed JSON: {path.name}") from error
    if not isinstance(payload, dict):
        raise InvalidObject("JSON root must be an object")
    return payload, raw


def _exact_keys(payload: dict[str, object], keys: set[str]) -> None:
    if set(payload) != keys:
        raise InvalidObject(f"wrong fields: expected {sorted(keys)}")


def _int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidObject(f"{label} must be an integer")
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise InvalidObject(f"{label} must be a string")
    return value


def _inventory(package: Path, rows: object) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, list):
        raise InvalidObject("files must be a list")
    seen: set[str] = set()
    normalized: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise InvalidObject("inventory row must be an object")
        _exact_keys(row, {"relative_path", "byte_length", "full_sha256"})
        relative = _string(row["relative_path"], "relative_path")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or not pure.parts or relative in seen:
            raise InvalidObject("inventory path must be unique and relative")
        seen.add(relative)
        payload_path = package / Path(*pure.parts)
        _require_contained(payload_path, package)
        if payload_path.is_symlink() or not payload_path.is_file():
            raise InvalidObject("inventory entry must be a contained regular file")
        raw = payload_path.read_bytes()
        length = _int(row["byte_length"], "byte_length")
        digest = _string(row["full_sha256"], "full_sha256")
        if length != len(raw) or digest != hashlib.sha256(raw).hexdigest():
            raise InvalidObject("inventory byte evidence mismatch")
        normalized.append(dict(row))
    expected = {f"blocks/{path.name}" for path in (package / "blocks").glob("*")}
    if expected != seen:
        raise InvalidObject("inventory misses or adds payload files")
    if [row["relative_path"] for row in normalized] != sorted(seen, key=lambda x: x.encode()):
        raise InvalidObject("inventory is not in canonical path order")
    return tuple(normalized)


def _read_corpus(package: Path, expected_id: str, storage_root: Path) -> Corpus:
    _require_plain_path(package, storage_root, directory=True)
    payload, _ = _json(package / "manifest.json")
    _exact_keys(
        payload, {"kind", "corpus_id", "chain_id", "definition", "files", "finalized_anchor"}
    )
    if payload["kind"] != "corpus" or payload["corpus_id"] != expected_id:
        raise InvalidObject("wrong corpus kind or embedded id")
    chain_id = _int(payload["chain_id"], "chain_id")
    rows = _inventory(package, payload["files"])
    identity = json.dumps(
        {"definition": payload["definition"], "files": rows},
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    if hashlib.sha256(identity).hexdigest() != expected_id:
        # The prototype uses fixed readable IDs, so exercise equality without
        # pretending its fixtures are real content-addressed corpora.
        claimed = payload["definition"]
        if not isinstance(claimed, dict) or claimed.get("fixture_id") != expected_id:
            raise InvalidObject("corpus id does not match identity projection")
    return Corpus(expected_id, chain_id, identity)


def load_corpus(storage_root: Path, corpus_id: str) -> Corpus:
    corpus_id = _corpus_id(corpus_id)
    return _read_corpus(corpus_path(storage_root, corpus_id), corpus_id, storage_root)


def _study_payload(path: Path, expected_id: str) -> tuple[dict[str, object], bytes]:
    payload, raw = _json(path)
    _exact_keys(payload, {"kind", "study_id", "corpus_id", "trials"})
    if payload["kind"] != "study" or payload["study_id"] != expected_id:
        raise InvalidObject("wrong study kind or embedded id")
    _corpus_id(_string(payload["corpus_id"], "corpus_id"))
    trials = payload["trials"]
    if not isinstance(trials, list) or any(
        isinstance(value, bool) or not isinstance(value, int) for value in trials
    ):
        raise InvalidObject("trials must be integer trial numbers")
    return payload, raw


def load_study(storage_root: Path, study_id: str) -> Study:
    study_id = _uuid4(study_id)
    package = study_path(storage_root, study_id)
    _require_plain_path(package, storage_root, directory=True)
    record = package / "study.json"
    if record.is_symlink() or set(package.iterdir()) != {record}:
        raise InvalidObject("canonical study must contain one regular study.json")
    payload, _ = _study_payload(record, study_id)
    corpus_id = _string(payload["corpus_id"], "corpus_id")
    load_corpus(storage_root, corpus_id)
    return Study(study_id, corpus_id, tuple(payload["trials"]))  # type: ignore[arg-type]


def _read_artifact(package: Path, expected_id: str, storage_root: Path) -> Artifact:
    _require_plain_path(package, storage_root, directory=True)
    payload, manifest_raw = _json(package / "manifest.json")
    _exact_keys(
        payload,
        {"kind", "artifact_id", "corpus_id", "chain_id", "study_id", "trial_number", "files"},
    )
    if payload["kind"] != "artifact" or payload["artifact_id"] != expected_id:
        raise InvalidObject("wrong artifact kind or embedded id")
    corpus_id = _corpus_id(_string(payload["corpus_id"], "corpus_id"))
    chain_id = _int(payload["chain_id"], "chain_id")
    corpus = load_corpus(storage_root, corpus_id)
    if chain_id != corpus.chain_id:
        raise InvalidObject("artifact and corpus chain differ")
    study_id = payload["study_id"]
    trial_number = payload["trial_number"]
    if study_id is None and trial_number is not None:
        raise InvalidObject("baseline artifact cannot name a trial")
    if study_id is not None:
        study_id = _uuid4(_string(study_id, "study_id"))
        trial_number = _int(trial_number, "trial_number")
        study = load_study(storage_root, study_id)
        if study.corpus_id != corpus_id or trial_number < 0 or trial_number >= len(study.trials):
            raise InvalidObject("artifact study parent or trial differs")
    rows = _inventory(package, payload["files"])
    exact = manifest_raw + b"\0" + json.dumps(rows, sort_keys=True).encode()
    return Artifact(expected_id, corpus_id, chain_id, study_id, trial_number, exact)  # type: ignore[arg-type]


def load_artifact(storage_root: Path, artifact_id: str) -> Artifact:
    artifact_id = _uuid4(artifact_id)
    return _read_artifact(artifact_path(storage_root, artifact_id), artifact_id, storage_root)


def _read_evaluation(path: Path, expected_id: str, storage_root: Path) -> Evaluation:
    _require_plain_path(path, storage_root, directory=False)
    payload, raw = _json(path)
    _exact_keys(
        payload, {"kind", "evaluation_id", "artifact_id", "corpus_id", "chain_id", "result"}
    )
    if payload["kind"] != "evaluation" or payload["evaluation_id"] != expected_id:
        raise InvalidObject("wrong evaluation kind or embedded id")
    artifact_id = _uuid4(_string(payload["artifact_id"], "artifact_id"))
    corpus_id = _corpus_id(_string(payload["corpus_id"], "corpus_id"))
    chain_id = _int(payload["chain_id"], "chain_id")
    artifact = load_artifact(storage_root, artifact_id)
    corpus = load_corpus(storage_root, corpus_id)
    if artifact.corpus_id != corpus_id:
        raise InvalidObject("evaluation artifact and corpus parents differ")
    if chain_id != artifact.chain_id or chain_id != corpus.chain_id:
        raise InvalidObject("evaluation parent chains differ")
    return Evaluation(expected_id, artifact_id, corpus_id, chain_id, raw)


def load_evaluation(storage_root: Path, evaluation_id: str) -> Evaluation:
    evaluation_id = _uuid4(evaluation_id)
    return _read_evaluation(
        evaluation_path(storage_root, evaluation_id), evaluation_id, storage_root
    )


def _hidden_sibling(stage: Path, destination: Path) -> None:
    if stage.parent != destination.parent or not stage.name.startswith("."):
        raise InvalidObject("publication stage must be an owned hidden sibling")


def _publish_directory(stage: Path, destination: Path, equal: Callable[[], bool]) -> str:
    _hidden_sibling(stage, destination)
    if destination.exists():
        if equal():
            shutil.rmtree(stage)
            return "equal/no-op"
        raise Conflict("same id has conflicting content; canonical and stage preserved")
    os.rename(stage, destination)
    return "published"


def _publish_file(stage: Path, destination: Path, equal: Callable[[], bool]) -> str:
    _hidden_sibling(stage, destination)
    if destination.exists():
        if equal():
            stage.unlink()
            return "equal/no-op"
        raise Conflict("same id has conflicting content; canonical and stage preserved")
    os.link(stage, destination)
    stage.unlink()
    return "published"


def publish_corpus(storage_root: Path, stage: Path, corpus_id: str) -> str:
    corpus_id = _corpus_id(corpus_id)
    destination = corpus_path(storage_root, corpus_id)
    staged = _read_corpus(stage, corpus_id, storage_root)
    return _publish_directory(
        stage,
        destination,
        lambda: load_corpus(storage_root, corpus_id).identity == staged.identity,
    )


def _trial_values(request: TuneRequestFixture) -> tuple[int, ...]:
    values: list[int] = []
    value = request.seed
    for number in range(request.budget):
        value = (value * 1_103_515_245 + 12_345 + number) % 2_147_483_648
        values.append(value)
    return tuple(values)


def _progress_path(work_dir: Path) -> Path:
    return work_dir / "progress.json"


def _load_progress(work_dir: Path, request: TuneRequestFixture) -> tuple[int, ...]:
    path = _progress_path(work_dir)
    if not path.exists() and not path.is_symlink():
        return ()
    _require_plain_path(path, work_dir, directory=False)
    payload, _ = _json(path)
    _exact_keys(payload, {"study_id", "trials"})
    if payload["study_id"] != request.study_id:
        raise InvalidObject("progress belongs to a different persisted TuneRequest/study_id")
    trials = payload["trials"]
    if not isinstance(trials, list) or any(
        isinstance(value, bool) or not isinstance(value, int) for value in trials
    ):
        raise InvalidObject("progress trials must be completed trial records")
    prefix = tuple(trials)
    if len(prefix) > request.budget or prefix != _trial_values(request)[: len(prefix)]:
        raise InvalidObject("progress must be the validated ordered completed-trial prefix")
    return prefix


def _write_progress(work_dir: Path, request: TuneRequestFixture, trials: list[int]) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    candidate = work_dir / ".progress.json.next"
    _write_json(
        candidate,
        {"study_id": request.study_id, "trials": trials},
    )
    os.replace(candidate, _progress_path(work_dir))


def _run_resumable_study(
    storage_root: Path,
    work_dir: Path,
    request: TuneRequestFixture,
    *,
    interrupt_trial: int | None = None,
    pause_after_completed: int | None = None,
    resumed_fit_trial: int | None = None,
    native_fit_checkpoint: bool = False,
    fit_actions: list[str] | None = None,
) -> Study:
    if study_path(storage_root, request.study_id).exists():
        raise InvalidObject("completed canonical study cannot resume or extend")
    trials = list(_load_progress(work_dir, request))
    expected = _trial_values(request)
    for number in range(len(trials), request.budget):
        if fit_actions is not None:
            if number == resumed_fit_trial:
                fit_actions.append("resume-fit" if native_fit_checkpoint else "restart-trial")
            else:
                fit_actions.append("start-fit")
        if number == interrupt_trial:
            raise FitInterrupted("in-flight trial is absent from study progress")
        trials.append(expected[number])
        _write_progress(work_dir, request, trials)
        if pause_after_completed == len(trials):
            raise FitInterrupted("study paused with completed-trial progress preserved")
    return Study(request.study_id, request.corpus_id, tuple(trials))


def publish_study(
    storage_root: Path,
    completed: Study,
    request: TuneRequestFixture,
) -> str:
    study_id = _uuid4(completed.study_id)
    if (
        completed.study_id != request.study_id
        or completed.corpus_id != request.corpus_id
        or len(completed.trials) != request.budget
        or completed.trials != _trial_values(request)
    ):
        raise InvalidObject(
            "partial/operator-stopped study is not complete under the predeclared budget"
        )
    load_corpus(storage_root, completed.corpus_id)
    destination = study_path(storage_root, study_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = destination.parent / f".{study_id}.complete"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    _write_json(
        stage / "study.json",
        {
            "kind": "study",
            "study_id": completed.study_id,
            "corpus_id": completed.corpus_id,
            "trials": list(completed.trials),
        },
    )
    return _publish_directory(
        stage,
        destination,
        lambda: load_study(storage_root, study_id) == completed,
    )


def _complete_study(
    storage_root: Path,
    work_dir: Path,
    request: TuneRequestFixture,
) -> str:
    if study_path(storage_root, request.study_id).exists():
        prefix = _load_progress(work_dir, request)
        candidate = Study(request.study_id, request.corpus_id, prefix)
        if (
            len(prefix) == request.budget
            and load_study(storage_root, request.study_id) == candidate
        ):
            _progress_path(work_dir).unlink()
            return "equal/no-op"
        raise Conflict("canonical study conflicts with private completed progress")
    completed = _run_resumable_study(storage_root, work_dir, request)
    outcome = publish_study(storage_root, completed, request)
    _progress_path(work_dir).unlink()
    return outcome


def publish_artifact(storage_root: Path, stage: Path, artifact_id: str) -> str:
    artifact_id = _uuid4(artifact_id)
    destination = artifact_path(storage_root, artifact_id)
    staged = _read_artifact(stage, artifact_id, storage_root)
    return _publish_directory(
        stage,
        destination,
        lambda: load_artifact(storage_root, artifact_id).exact == staged.exact,
    )


def publish_evaluation(storage_root: Path, stage: Path, evaluation_id: str) -> str:
    evaluation_id = _uuid4(evaluation_id)
    destination = evaluation_path(storage_root, evaluation_id)
    staged = _read_evaluation(stage, evaluation_id, storage_root)
    return _publish_file(
        stage,
        destination,
        lambda: load_evaluation(storage_root, evaluation_id).exact == staged.exact,
    )


def _human_list(
    directory: Path,
    parse_id: Callable[[str], str],
    load: Callable[[str], object],
) -> list[str]:
    rows: list[str] = []
    if not directory.exists():
        return rows
    for child in sorted(directory.iterdir(), key=lambda path: path.name):
        if child.name.startswith("."):
            continue
        candidate = child.stem if child.suffix == ".json" else child.name
        try:
            object_id = parse_id(candidate)
            load(object_id)
            rows.append(f"{object_id} valid")
        except (InvalidObject, OSError) as error:
            rows.append(f"{candidate} INVALID: {error}")
    return rows


def human_list_corpora(storage_root: Path) -> list[str]:
    return _human_list(
        storage_root / "corpora", _corpus_id, lambda value: load_corpus(storage_root, value)
    )


def human_list_studies(storage_root: Path) -> list[str]:
    return _human_list(
        storage_root / "studies", _uuid4, lambda value: load_study(storage_root, value)
    )


def human_list_artifacts(storage_root: Path) -> list[str]:
    return _human_list(
        storage_root / "artifacts", _uuid4, lambda value: load_artifact(storage_root, value)
    )


def human_list_evaluations(storage_root: Path) -> list[str]:
    return _human_list(
        storage_root / "evaluations", _uuid4, lambda value: load_evaluation(storage_root, value)
    )


class SmallTypedStore:
    """Rejected candidate: every method only binds ``storage_root``."""

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root

    def corpus_path(self, value: str) -> Path:
        return corpus_path(self.storage_root, value)

    def load_corpus(self, value: str) -> Corpus:
        return load_corpus(self.storage_root, value)

    def study_path(self, value: str) -> Path:
        return study_path(self.storage_root, value)

    def load_study(self, value: str) -> Study:
        return load_study(self.storage_root, value)

    def artifact_path(self, value: str) -> Path:
        return artifact_path(self.storage_root, value)

    def load_artifact(self, value: str) -> Artifact:
        return load_artifact(self.storage_root, value)

    def evaluation_path(self, value: str) -> Path:
        return evaluation_path(self.storage_root, value)

    def load_evaluation(self, value: str) -> Evaluation:
        return load_evaluation(self.storage_root, value)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")), encoding="utf-8")


def _file_row(relative: str, raw: bytes) -> dict[str, object]:
    return {
        "relative_path": relative,
        "byte_length": len(raw),
        "full_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _make_corpus(
    path: Path, corpus_id: str, *, chain_id: int = 1, block: bytes = b"block", anchor: str = "A"
) -> None:
    payload_path = path / "blocks" / "part.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_bytes(block)
    _write_json(
        path / "manifest.json",
        {
            "kind": "corpus",
            "corpus_id": corpus_id,
            "chain_id": chain_id,
            "definition": {"fixture_id": corpus_id, "chain_id": chain_id},
            "files": [_file_row("blocks/part.json", block)],
            "finalized_anchor": anchor,
        },
    )


def _make_artifact(
    path: Path,
    *,
    corpus_id: str = CORPUS_A,
    chain_id: int = 1,
    study_id: str | None = None,
    trial_number: int | None = None,
    weight: bytes = b"weight",
) -> None:
    payload_path = path / "blocks" / "model.pt"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_bytes(weight)
    _write_json(
        path / "manifest.json",
        {
            "kind": "artifact",
            "artifact_id": ARTIFACT_A,
            "corpus_id": corpus_id,
            "chain_id": chain_id,
            "study_id": study_id,
            "trial_number": trial_number,
            "files": [_file_row("blocks/model.pt", weight)],
        },
    )


def _evaluation_payload(
    *, result: int = 1, embedded_id: str = EVALUATION_A, chain_id: int = 1
) -> dict[str, object]:
    return {
        "kind": "evaluation",
        "evaluation_id": embedded_id,
        "artifact_id": ARTIFACT_A,
        "corpus_id": CORPUS_A,
        "chain_id": chain_id,
        "result": result,
    }


def _seed_parents(root: Path) -> None:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    _make_artifact(artifact_path(root, ARTIFACT_A))


def _case(name: str, expected: str, action: Callable[[Path], object]) -> str:
    with tempfile.TemporaryDirectory(prefix="spice-issue-13-") as directory:
        root = Path(directory) / "root"
        root.mkdir()
        try:
            value = action(root)
        except (InvalidObject, Conflict) as error:
            value = type(error).__name__
        observed = str(value)
        verdict = "PASS" if observed == expected else f"FAIL expected={expected!r} got={observed!r}"
        return f"{name:<42} {verdict}"


def _equal_corpus(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A, anchor="old")
    stage = root / "corpora" / ".incoming"
    _make_corpus(stage, CORPUS_A, anchor="new")
    return publish_corpus(root, stage, CORPUS_A)


def _conflicting_corpus(root: Path) -> object:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    stage = root / "corpora" / ".incoming"
    _make_corpus(stage, CORPUS_A, block=b"different")
    try:
        publish_corpus(root, stage, CORPUS_A)
    except Conflict:
        if stage.exists() and corpus_path(root, CORPUS_A).exists():
            raise
        return "lost evidence"
    return "missed conflict"


def _equal_receipt(root: Path) -> str:
    _seed_parents(root)
    stage = root / "artifacts" / ".received"
    _make_artifact(stage)
    return publish_artifact(root, stage, ARTIFACT_A)


def _conflicting_receipt(root: Path) -> object:
    _seed_parents(root)
    _write_json(evaluation_path(root, EVALUATION_A), _evaluation_payload(result=1))
    stage = root / "evaluations" / ".received.json"
    _write_json(stage, _evaluation_payload(result=2))
    try:
        publish_evaluation(root, stage, EVALUATION_A)
    except Conflict:
        if stage.exists() and evaluation_path(root, EVALUATION_A).exists():
            raise
        return "lost evidence"
    return "missed conflict"


def _request(*, seed: int = 7) -> TuneRequestFixture:
    return TuneRequestFixture(STUDY_A, CORPUS_A, seed, 3)


def _work(root: Path, name: str = "job") -> Path:
    return root.parent / name


def _progress_after_completed_trial(root: Path) -> str:
    request = _request()
    try:
        _run_resumable_study(root, _work(root), request, pause_after_completed=1)
    except FitInterrupted:
        pass
    payload, _ = _json(_progress_path(_work(root)))
    prefix = _load_progress(_work(root), request)
    return (
        "one-prefix/minimal-fields"
        if (len(prefix) == 1 and set(payload) == {"study_id", "trials"})
        else str(payload)
    )


def _inflight_uses_native_fit_checkpoint(root: Path) -> str:
    request = _request()
    work = _work(root)
    try:
        _run_resumable_study(root, work, request, pause_after_completed=1)
    except FitInterrupted:
        pass
    try:
        _run_resumable_study(root, work, request, interrupt_trial=1)
    except FitInterrupted:
        pass
    if len(_load_progress(work, request)) != 1:
        return "in-flight trial was marked complete"
    actions: list[str] = []
    _run_resumable_study(
        root,
        work,
        request,
        resumed_fit_trial=1,
        native_fit_checkpoint=True,
        fit_actions=actions,
    )
    return "resume-fit/unmarked" if actions[0] == "resume-fit" else str(actions)


def _inflight_without_checkpoint_restarts_trial(root: Path) -> str:
    request = _request()
    work = _work(root)
    try:
        _run_resumable_study(root, work, request, pause_after_completed=1)
    except FitInterrupted:
        pass
    actions: list[str] = []
    _run_resumable_study(
        root,
        work,
        request,
        resumed_fit_trial=1,
        native_fit_checkpoint=False,
        fit_actions=actions,
    )
    return "restart-trial" if actions[0] == "restart-trial" else str(actions)


def _whole_study_pause_resumes_prefix(root: Path) -> str:
    request = _request()
    work = _work(root)
    try:
        _run_resumable_study(root, work, request, pause_after_completed=2)
    except FitInterrupted:
        pass
    before = _load_progress(work, request)
    completed = _run_resumable_study(root, work, request)
    return (
        "two-prefix/continued-next"
        if len(before) == 2 and len(completed.trials) == 3
        else str(before)
    )


def _wrong_progress_owner(root: Path) -> tuple[int, ...]:
    request = _request()
    work = _work(root)
    _write_json(_progress_path(work), {"study_id": OTHER_UUID, "trials": []})
    return _load_progress(work, request)


def _invalid_progress_prefix(root: Path) -> tuple[int, ...]:
    request = _request()
    work = _work(root)
    _write_json(_progress_path(work), {"study_id": STUDY_A, "trials": [999]})
    return _load_progress(work, request)


def _progress_rejects_lifecycle_fields(root: Path) -> tuple[int, ...]:
    request = _request()
    work = _work(root)
    _write_json(
        _progress_path(work),
        {"study_id": STUDY_A, "trials": [], "status": "running", "retry_count": 2},
    )
    return _load_progress(work, request)


def _progress_symlink_escape(root: Path) -> tuple[int, ...]:
    request = _request()
    work = _work(root)
    work.mkdir()
    outside = root.parent / "outside-progress.json"
    _write_json(outside, {"study_id": STUDY_A, "trials": []})
    _progress_path(work).symlink_to(outside)
    return _load_progress(work, request)


def _load_before_publication(root: Path) -> Study:
    request = _request()
    _run_resumable_study(root, _work(root), request)
    return load_study(root, STUDY_A)


def _partial_operator_stop_cannot_publish(root: Path) -> str:
    request = _request()
    work = _work(root)
    try:
        _run_resumable_study(root, work, request, pause_after_completed=1)
    except FitInterrupted:
        pass
    partial = Study(STUDY_A, CORPUS_A, _load_progress(work, request))
    return publish_study(root, partial, request)


def _publish_completed_study(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    request = _request()
    work = _work(root)
    outcome = _complete_study(root, work, request)
    loaded = load_study(root, STUDY_A)
    files = {path.name for path in study_path(root, STUDY_A).iterdir()}
    hidden = list(study_path(root, STUDY_A).parent.glob(".*.complete"))
    return (
        f"{outcome}/immutable/progress-removed"
        if (
            len(loaded.trials) == request.budget
            and files == {"study.json"}
            and not hidden
            and not _progress_path(work).exists()
            and not hasattr(loaded, "state")
        )
        else str((loaded, files))
    )


def _lost_acknowledgement_cleans_progress(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    request = _request()
    work = _work(root)
    completed = _run_resumable_study(root, work, request)
    publish_study(root, completed, request)
    outcome = _complete_study(root, work, request)
    return outcome if not _progress_path(work).exists() else "progress leaked"


def _conflicting_study_preserves_progress(root: Path) -> object:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    first = _request(seed=7)
    conflicting = _request(seed=8)
    first_work = _work(root, "job-a")
    conflict_work = _work(root, "job-b")
    conflict_value = _run_resumable_study(root, conflict_work, conflicting)
    _complete_study(root, first_work, first)
    try:
        publish_study(root, conflict_value, conflicting)
    except Conflict:
        if _progress_path(conflict_work).exists() and study_path(root, STUDY_A).exists():
            raise
        return "lost evidence"
    return "missed conflict"


def _post_completion_extension_rejected(root: Path) -> Study:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    request = _request()
    _complete_study(root, _work(root), request)
    return _run_resumable_study(root, _work(root), request)


def _selected_training_gate(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    request = _request()
    work = _work(root)
    _run_resumable_study(root, work, request)
    _make_artifact(artifact_path(root, ARTIFACT_A), study_id=STUDY_A, trial_number=0)
    try:
        load_artifact(root, ARTIFACT_A)
    except InvalidObject:
        pass
    else:
        return "loaded-before-publication"
    _complete_study(root, work, request)
    load_artifact(root, ARTIFACT_A)
    return "normal-load-gate"


def _completed_only_enumeration(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    request = _request()
    work = _work(root)
    _run_resumable_study(root, work, request)
    before = human_list_studies(root)
    _complete_study(root, work, request)
    after = human_list_studies(root)
    return (
        "completed-only"
        if not before and len(after) == 1 and "valid" in after[0]
        else str((before, after))
    )


def _symlink_escape(root: Path) -> Evaluation:
    _seed_parents(root)
    outside = root.parent / "outside.json"
    _write_json(outside, _evaluation_payload())
    target = evaluation_path(root, EVALUATION_A)
    target.parent.mkdir(parents=True)
    target.symlink_to(outside)
    return load_evaluation(root, EVALUATION_A)


def _hidden_enumeration(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    _make_corpus(root / "corpora" / ".incoming", CORPUS_B)
    rows = human_list_corpora(root)
    return "one-visible" if len(rows) == 1 and CORPUS_A in rows[0] else str(rows)


def _transfer_address(root: Path) -> str:
    source = artifact_path(root / "source", ARTIFACT_A)
    destination = artifact_path(root / "destination", ARTIFACT_A)
    return (
        source.relative_to(root / "source").as_posix()
        if (source.relative_to(root / "source") == destination.relative_to(root / "destination"))
        else "mismatch"
    )


def _invalid_enumeration(root: Path) -> str:
    _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A)
    (root / "corpora" / CORPUS_B).mkdir(parents=True)
    rows = human_list_corpora(root)
    return "reported" if any("INVALID" in row and CORPUS_B in row for row in rows) else str(rows)


def _cases() -> list[tuple[str, str, Callable[[Path], object]]]:
    return [
        (
            "contained canonical path",
            "True",
            lambda root: corpus_path(root, CORPUS_A).is_relative_to(root),
        ),
        ("same typed transfer address", f"artifacts/{ARTIFACT_A}", _transfer_address),
        ("wrong id/path segment", "InvalidObject", lambda root: corpus_path(root, "../escape")),
        (
            "wrong file kind",
            "InvalidObject",
            lambda root: (
                evaluation_path(root, EVALUATION_A).mkdir(parents=True),
                load_evaluation(root, EVALUATION_A),
            )[1],
        ),
        (
            "wrong object kind",
            "InvalidObject",
            lambda root: (
                _seed_parents(root),
                _write_json(
                    evaluation_path(root, EVALUATION_A), {**_evaluation_payload(), "kind": "corpus"}
                ),
                load_evaluation(root, EVALUATION_A),
            )[2],
        ),
        (
            "wrong embedded id",
            "InvalidObject",
            lambda root: (
                _seed_parents(root),
                _write_json(
                    evaluation_path(root, EVALUATION_A), _evaluation_payload(embedded_id=OTHER_UUID)
                ),
                load_evaluation(root, EVALUATION_A),
            )[2],
        ),
        (
            "missing parent",
            "InvalidObject",
            lambda root: (
                _make_artifact(artifact_path(root, ARTIFACT_A), corpus_id=CORPUS_B),
                load_artifact(root, ARTIFACT_A),
            )[1],
        ),
        (
            "wrong parent chain",
            "InvalidObject",
            lambda root: (
                _make_corpus(corpus_path(root, CORPUS_A), CORPUS_A),
                _make_artifact(artifact_path(root, ARTIFACT_A), chain_id=137),
                load_artifact(root, ARTIFACT_A),
            )[2],
        ),
        ("symlink escape", "InvalidObject", _symlink_escape),
        (
            "malformed payload",
            "InvalidObject",
            lambda root: (
                evaluation_path(root, EVALUATION_A).parent.mkdir(),
                evaluation_path(root, EVALUATION_A).write_text("{"),
                load_evaluation(root, EVALUATION_A),
            )[2],
        ),
        ("hidden stages ignored by human list", "one-visible", _hidden_enumeration),
        ("invalid canonical entry reported", "reported", _invalid_enumeration),
        ("equal corpus; anchor differs", "equal/no-op", _equal_corpus),
        ("conflicting corpus preserves both", "Conflict", _conflicting_corpus),
        ("equal artifact receipt", "equal/no-op", _equal_receipt),
        ("conflicting evaluation receipt", "Conflict", _conflicting_receipt),
        (
            "completed trial writes minimal prefix",
            "one-prefix/minimal-fields",
            _progress_after_completed_trial,
        ),
        (
            "in-flight fit uses native checkpoint",
            "resume-fit/unmarked",
            _inflight_uses_native_fit_checkpoint,
        ),
        (
            "no fit checkpoint restarts one trial",
            "restart-trial",
            _inflight_without_checkpoint_restarts_trial,
        ),
        (
            "whole-study pause resumes next trial",
            "two-prefix/continued-next",
            _whole_study_pause_resumes_prefix,
        ),
        ("wrong progress study id", "InvalidObject", _wrong_progress_owner),
        ("non-prefix progress", "InvalidObject", _invalid_progress_prefix),
        (
            "progress rejects status/retry fields",
            "InvalidObject",
            _progress_rejects_lifecycle_fields,
        ),
        ("progress symlink escape", "InvalidObject", _progress_symlink_escape),
        ("normal load before completion", "InvalidObject", _load_before_publication),
        (
            "operator-stopped partial cannot publish",
            "InvalidObject",
            _partial_operator_stop_cannot_publish,
        ),
        (
            "completed study publishes once",
            "published/immutable/progress-removed",
            _publish_completed_study,
        ),
        (
            "lost acknowledgement cleans progress",
            "equal/no-op",
            _lost_acknowledgement_cleans_progress,
        ),
        ("conflicting study preserves progress", "Conflict", _conflicting_study_preserves_progress),
        (
            "post-completion extension rejected",
            "InvalidObject",
            _post_completion_extension_rejected,
        ),
        ("selected training uses normal load", "normal-load-gate", _selected_training_gate),
        ("human listing sees completed only", "completed-only", _completed_only_enumeration),
    ]


def _run_all() -> None:
    print("Issue #13 disposable filesystem prototype\n")
    for name, expected, action in _cases():
        print(_case(name, expected, action))
    print("\nInterface count")
    print("  fixed read seam:       8 functions (4 path + 4 load)")
    print("  lifecycle candidate:   4 concrete publication functions")
    print("  transfer owner:        4 concrete typed operations")
    print("  human enumeration:     4 CLI-only scans")
    print("  typed store candidate: +1 public type + 8 forwarding methods, 0 hidden behavior")
    print(
        "\nDeletion test: deleting SmallTypedStore removes only bound root storage; "
        "no complexity moves to callers."
    )
    print("Study red-team: 3 public study lifecycle operations -> 1 publication operation")
    print("                2 public study variants -> 1 immutable Study")
    print("                2 canonical filenames -> 1 study.json")
    print("                canonical mutation/lock/finish recovery -> deleted")
    print("                private progress -> 1 file, study id + completed prefix")
    print("                interruption -> resume next uncompleted trial")
    print("                in-flight fit -> native checkpoint or one-trial restart")
    print("                completion -> immutable publish + progress removal")
    print("                operator stop -> never completion/selection")


def _interactive() -> None:
    cases = _cases()
    index = 0
    results: dict[int, str] = {}
    while True:
        os.system("clear")
        name, expected, _ = cases[index]
        result = results.get(index, "not run")
        passed = sum(value.endswith("PASS") for value in results.values())
        print("\033[1mIssue #13 disposable filesystem prototype\033[0m")
        print("\033[2mScratch filesystem only; each probe starts from an empty root.\033[0m\n")
        print(f"\033[1mcase\033[0m      {index + 1}/{len(cases)}")
        print(f"\033[1mname\033[0m      {name}")
        print(f"\033[1mexpected\033[0m  {expected}")
        print(f"\033[1mresult\033[0m    {result}")
        print(f"\033[1mprogress\033[0m  {passed}/{len(cases)} passed\n")
        print(
            "\033[1m[r]\033[0m run  \033[1m[n]\033[0m next  "
            "\033[1m[p]\033[0m previous  \033[1m[a]\033[0m run all  "
            "\033[1m[q]\033[0m quit"
        )
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        if choice == "n":
            index = (index + 1) % len(cases)
        elif choice == "p":
            index = (index - 1) % len(cases)
        elif choice == "r":
            results[index] = _case(*cases[index])
        elif choice == "a":
            results = {position: _case(*case) for position, case in enumerate(cases)}


def main() -> None:
    if sys.argv[1:] == ["--all"]:
        _run_all()
    elif sys.argv[1:]:
        raise SystemExit(
            "usage: uv run python docs/research/issue-13-direct-storage/prototype.py [--all]"
        )
    else:
        _interactive()


if __name__ == "__main__":
    main()
