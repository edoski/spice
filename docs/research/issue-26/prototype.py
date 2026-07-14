"""HISTORICAL terminal driver for the disposable host comparison.

Its repeat hashes and checkpoint inventories are rejected final-design alternatives,
retained only as bounded comparison evidence. See decision-contract.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import torch
from direct_candidate import fit_direct, inspect_direct_checkpoint, seed_direct
from lightning_candidate import (
    _AutomaticTask,
    fit_lightning,
    inspect_lightning_checkpoint,
)
from task_fixture import (
    CLIP_NORM,
    PATIENCE,
    SEED,
    TRAIN_BATCH_SIZE,
    VALIDATION_BATCH_SIZE,
    CandidateSuccess,
    Family,
    FitResult,
    build_frozen_model,
    candidate_success,
    frozen_task,
    loss_terms,
    model_definition,
    model_families,
)
from torch.utils.data import DataLoader

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"

FitCandidate = Callable[..., FitResult | None]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run every bounded synthetic probe")
    args = parser.parse_args()
    if args.all:
        print(json.dumps(run_all(), indent=2, sort_keys=True))
    else:
        run_tui()


def run_all() -> dict[str, object]:
    task = frozen_task()
    observations: dict[str, object] = {}
    successes: list[CandidateSuccess] = []
    with tempfile.TemporaryDirectory(prefix="spice-issue-26-") as raw_root:
        root = Path(raw_root)
        for family in model_families():
            definition = model_definition(family)
            direct_dir = root / family / "direct"
            lightning_dir = root / family / "lightning"
            direct = _fit_with_resume(
                fit_direct,
                definition,
                task.training,
                task.validation,
                task.classification,
                direct_dir,
            )
            lightning = _fit_with_resume(
                fit_lightning,
                definition,
                task.training,
                task.validation,
                task.classification,
                lightning_dir,
            )
            minibatches_per_epoch = len(
                _batch_sizes(task.training, TRAIN_BATCH_SIZE, shuffle=False)
            )
            _require_policy_result(direct, len(task.training), minibatches_per_epoch)
            _require_policy_result(lightning, len(task.training), minibatches_per_epoch)
            if direct.best_validation != lightning.best_validation:
                raise AssertionError("both hosts must expose the same exact validation reduction")

            direct_state = direct.best_state_dict
            lightning_state = lightning.best_state_dict
            if _state_hash(direct_state) != _state_hash(lightning_state):
                raise AssertionError("seeded best weights must match across the two hosts")
            _verify_reload(family, direct_state, task.validation, task.classification)
            _verify_reload(family, lightning_state, task.validation, task.classification)

            successes.extend(
                (
                    candidate_success(direct, method=family),
                    candidate_success(lightning, method=family),
                )
            )
            observations[family] = {
                "direct": _result_observation(direct),
                "lightning": _result_observation(lightning),
                "seeded_best_state_match": True,
                "strict_cpu_reload": True,
                "direct_boundary": inspect_direct_checkpoint(direct_dir / "boundary.pt"),
                "lightning_boundary": inspect_lightning_checkpoint(lightning_dir / "last.ckpt"),
            }

        failure = {
            "finite_training_loss": {
                "direct": _nonfinite_training_loss(
                    fit_direct, root / "failure" / "training" / "direct", task
                ),
                "lightning": _nonfinite_training_loss(
                    fit_lightning, root / "failure" / "training" / "lightning", task
                ),
            },
            "native_gradient_error_if_nonfinite": _native_gradient_nonfinite(task),
            "complete_validation_after_prior_best": {
                "direct": _nonfinite_after_best(
                    fit_direct,
                    root / "failure" / "validation" / "direct",
                    task,
                    ("boundary.pt",),
                ),
                "lightning": _nonfinite_after_best(
                    fit_lightning,
                    root / "failure" / "validation" / "lightning",
                    task,
                    ("best.ckpt", "last.ckpt"),
                ),
            },
        }
        sqlite_files = list(root.rglob("*.sqlite")) + list(root.rglob("*.db"))
        if sqlite_files:
            raise AssertionError("fit lifecycle must not create artifact SQLite")

        return {
            "question": "choose one lean host for the complete frozen fit lifecycle",
            "fixture": {
                "device": "cpu",
                "precision": "strict_fp32",
                "seed": SEED,
                "families": list(model_families()),
                "training_samples": len(task.training),
                "validation_samples": len(task.validation),
                "training_batch_sizes": _batch_sizes(
                    task.training, TRAIN_BATCH_SIZE, shuffle=False
                ),
                "validation_batch_sizes": _batch_sizes(
                    task.validation,
                    VALIDATION_BATCH_SIZE,
                    shuffle=False,
                ),
                "optimizer_learning_rate": 0.0,
                "optimizer_note": "prototype-only zero learning rate forces exact ties",
            },
            "hosts": observations,
            "distinct_numerical_boundaries": failure,
            "foreign_checkpoint_provenance": {
                "direct": _foreign_checkpoint_rejected(
                    fit_direct,
                    root / "provenance" / "direct",
                    task,
                    "boundary.pt",
                ),
                "lightning": _foreign_checkpoint_rejected(
                    fit_lightning,
                    root / "provenance" / "lightning",
                    task,
                    "last.ckpt",
                ),
            },
            "private_hpo_handoff": {
                "successful_results": len(successes),
                "fields": sorted(asdict(successes[0])),
                "per_epoch_hook": False,
                "checkpoints_or_paths_exposed": False,
            },
            "artifact_sqlite_files": 0,
            "reporting": {
                "lightning_callback_state_in_boundary_checkpoint": True,
                "canonical_history_persisted": False,
                "logger_dependency_added": False,
            },
            "prototype_host_lines": {
                "direct": _source_lines(Path(__file__).with_name("direct_candidate.py")),
                "lightning": _source_lines(Path(__file__).with_name("lightning_candidate.py")),
            },
            "checks": "pass",
        }


def _fit_with_resume(
    fit: FitCandidate,
    definition: object,
    training: object,
    validation: object,
    classification: object,
    work_dir: Path,
) -> FitResult:
    partial = fit(
        definition,
        training,
        validation,
        classification,
        work_dir,
        _job_epoch_limit=2,
    )
    if partial is not None:
        raise AssertionError("the first job must stop after a completed validation boundary")
    result = fit(
        definition,
        training,
        validation,
        classification,
        work_dir,
        resume=True,
    )
    if result is None:
        raise AssertionError("resumed fit must complete")
    return result


def _require_policy_result(
    result: FitResult,
    training_samples: int,
    minibatches_per_epoch: int,
) -> None:
    if result.earliest_best_epoch != 1:
        raise AssertionError("exact ties must retain the earliest best epoch")
    if result.completed_epochs != PATIENCE + 1:
        raise AssertionError("epoch-one best must stop after exactly patience non-improvements")
    if result.stop_reason != "patience":
        raise AssertionError("the frozen equality curve must stop by patience")
    if result.optimization_examples != result.completed_epochs * training_samples:
        raise AssertionError("fit accounting must include every completed-epoch example")
    expected_updates = result.completed_epochs * minibatches_per_epoch
    if result.minibatches != expected_updates or result.optimizer_updates != expected_updates:
        raise AssertionError("one physical minibatch must produce one optimizer update")


def _nonfinite_training_loss(
    fit: FitCandidate,
    work_dir: Path,
    task: object,
) -> bool:
    try:
        fit(
            model_definition("lstm"),
            task.invalid_training,
            task.validation,
            task.classification,
            work_dir,
        )
    except FloatingPointError:
        pass
    else:
        raise AssertionError("nonfinite training loss must fail before backward")
    if list(work_dir.glob("*.pt")) or list(work_dir.glob("*.ckpt")):
        raise AssertionError("failed training must not create a completed-validation checkpoint")
    return True


def _native_gradient_nonfinite(task: object) -> dict[str, bool]:
    parameter = torch.nn.Parameter(torch.zeros(()))
    parameter.grad = torch.full_like(parameter, float("inf"))
    try:
        torch.nn.utils.clip_grad_norm_([parameter], CLIP_NORM, error_if_nonfinite=True)
    except RuntimeError:
        direct = True
    else:
        raise AssertionError("direct native clipping must reject a nonfinite gradient")

    seed_direct()
    module = _AutomaticTask(
        model_definition("lstm"),
        task.classification,
        len(task.validation),
    )
    first_parameter = next(module.model.parameters())
    first_parameter.grad = torch.full_like(first_parameter, float("inf"))
    try:
        module.configure_gradient_clipping(
            module.configure_optimizers(),
            gradient_clip_val=CLIP_NORM,
            gradient_clip_algorithm="norm",
        )
    except RuntimeError:
        lightning = True
    else:
        raise AssertionError("Lightning's supported clipping hook must reject a nonfinite gradient")
    return {"direct": direct, "lightning": lightning, "duplicate_post_check": False}


def _foreign_checkpoint_rejected(
    fit: FitCandidate,
    work_dir: Path,
    task: object,
    checkpoint_name: str,
) -> bool:
    partial = fit(
        model_definition("lstm"),
        task.training,
        task.validation,
        task.classification,
        work_dir,
        _job_epoch_limit=1,
    )
    if partial is not None:
        raise AssertionError("provenance probe must first create one native boundary")
    checkpoint_path = work_dir / checkpoint_name
    before = _file_hash(checkpoint_path)
    try:
        fit(
            model_definition("transformer"),
            task.training,
            task.validation,
            task.classification,
            work_dir,
            resume=True,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("foreign checkpoint provenance must fail before restoration")
    if _file_hash(checkpoint_path) != before:
        raise AssertionError("foreign checkpoint rejection must preserve the private boundary")
    return True


def _nonfinite_after_best(
    fit: FitCandidate,
    work_dir: Path,
    task: object,
    checkpoint_names: tuple[str, ...],
) -> bool:
    definition = model_definition("lstm")
    first = fit(
        definition,
        task.training,
        task.validation,
        task.classification,
        work_dir,
        _job_epoch_limit=1,
    )
    if first is not None:
        raise AssertionError("failure probe must first create one valid private boundary")
    checkpoint_paths = tuple(work_dir / name for name in checkpoint_names)
    before = tuple(_file_hash(path) for path in checkpoint_paths)
    try:
        fit(
            definition,
            task.training,
            task.invalid_validation,
            task.classification,
            work_dir,
            resume=True,
        )
    except FloatingPointError:
        pass
    else:
        raise AssertionError("nonfinite complete validation must fail the fit")
    after = tuple(_file_hash(path) for path in checkpoint_paths)
    if before != after:
        raise AssertionError("nonfinite failure must preserve the prior private boundary unchanged")
    return True


def _verify_reload(
    family: Family,
    state: dict[str, torch.Tensor],
    dataset: object,
    classification: object,
) -> None:
    seed_direct()
    model = build_frozen_model(model_definition(family))
    model.load_state_dict(state, strict=True)
    model.eval()
    loader = DataLoader(dataset, batch_size=VALIDATION_BATCH_SIZE, shuffle=False)
    batch_sizes: list[int] = []
    with torch.inference_mode():
        for batch in loader:
            output = model(batch["inputs"])
            batch_sizes.append(int(output.action_logits.shape[0]))
            loss_terms(output, batch, classification)
    if batch_sizes != [2, 1]:
        raise AssertionError("strict reload must cover validation full and tail batches")


def _result_observation(result: FitResult) -> dict[str, object]:
    return {
        "best_validation": asdict(result.best_validation),
        "best_validation_total_loss": result.best_validation.total_loss,
        "earliest_best_epoch": result.earliest_best_epoch,
        "completed_epochs": result.completed_epochs,
        "stop_reason": result.stop_reason,
        "optimization_examples": result.optimization_examples,
        "minibatches": result.minibatches,
        "optimizer_updates": result.optimizer_updates,
        "final_plain_weights": True,
    }


def _batch_sizes(dataset: object, batch_size: int, *, shuffle: bool) -> list[int]:
    return [
        int(batch["label"].shape[0])
        for batch in DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)
    ]


def _state_hash(state: dict[str, torch.Tensor]) -> str:
    digest = hashlib.sha256()
    for name in sorted(state):
        value = state[name].detach().cpu().contiguous()
        digest.update(name.encode())
        digest.update(str(value.dtype).encode())
        digest.update(str(tuple(value.shape)).encode())
        digest.update(value.numpy().tobytes())
    return digest.hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_lines(path: Path) -> int:
    return sum(
        bool(line.strip()) and not line.lstrip().startswith("#")
        for line in path.read_text().splitlines()
    )


def run_tui() -> None:
    state: dict[str, object] = {
        "status": "ready",
        "question": "compare complete direct-PyTorch and Lightning fit lifecycles",
    }
    while True:
        print("\033[2J\033[H", end="")
        print(f"{BOLD}Issue 26 disposable training-host prototype{RESET}")
        print(f"{DIM}{json.dumps(state, indent=2, sort_keys=True)}{RESET}")
        print()
        print(f"{BOLD}[a]{RESET} run all bounded probes  {BOLD}[q]{RESET} quit")
        action = input("> ").strip().lower()
        if action == "q":
            return
        if action == "a":
            state = run_all()
        else:
            state = {"status": "unknown action"}


if __name__ == "__main__":
    main()
