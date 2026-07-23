"""Author and reduce the frozen held-out evaluations."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from uuid import UUID, uuid4

import polars as pl

from fable.addresses import corpus_json_path, study_json_path
from fable.config import BlockWindow, CorpusRequest
from fable.evaluation.resolution import reduce_evaluation, reduce_rolling
from fable.experiments import ExperimentKind, load_experiment_manifest
from fable.requests import fresh_evaluate_request
from fable.study import Study

_MAX_HORIZON = 200


def _bundle_path(storage_root: Path, experiment_id: UUID) -> Path:
    return storage_root / "experiments" / "held_out" / f".{experiment_id}"


def _load_study(storage_root: Path, study_id: UUID) -> Study:
    return Study.model_validate_json(
        study_json_path(storage_root, study_id).read_bytes(),
        strict=True,
    )


def _corpus_last_block(storage_root: Path, corpus_id: UUID) -> int:
    document = json.loads(corpus_json_path(storage_root, corpus_id).read_bytes())
    return CorpusRequest.model_validate(document["request"]).definition.last_block


def prepare(
    storage_root: Path,
    hpo_experiment_id: UUID,
    k_experiment_id: UUID,
    experiment_id: UUID,
) -> None:
    if experiment_id.version != 4:
        raise ValueError("experiment_id must be a UUIDv4")

    storage_root = storage_root.resolve()
    hpo = load_experiment_manifest(storage_root, ExperimentKind.HPO, hpo_experiment_id)
    k_study = load_experiment_manifest(storage_root, ExperimentKind.K_STUDY, k_experiment_id)
    studies = {
        entry.cell: _load_study(storage_root, entry.study_id)
        for entry in hpo.entries
        if entry.study_id is not None
    }
    bundle = _bundle_path(storage_root, experiment_id)
    requests = bundle / "requests"
    requests.mkdir(parents=True)

    rows: list[tuple[str, Path, UUID]] = []
    rolling: list[tuple[str, int, UUID]] = []
    for index, entry in enumerate(k_study.entries):
        if entry.artifact_id is None:
            raise ValueError("K-study entry must reference an artifact")
        chain, family, horizon_label = entry.cell.split(".")
        horizon = int(horizon_label.removeprefix("K"))
        study = studies[f"{chain}.{family}"]
        validation_end = study.request.experiment.validation_window.last_parent_block
        first_parent = validation_end + _MAX_HORIZON + 1 + max(0, 5 - horizon)
        last_parent = (
            _corpus_last_block(storage_root, study.request.corpus_id)
            - _MAX_HORIZON
            + max(0, 5 - horizon)
        )
        request = fresh_evaluate_request(
            entry.artifact_id,
            study.request.corpus_id,
            BlockWindow(
                first_parent_block=first_parent,
                last_parent_block=last_parent,
            ),
        )
        request_path = requests / f"{index:02d}.json"
        request_path.write_text(request.model_dump_json(), encoding="utf-8")
        rows.append((entry.cell, request_path, request.evaluation_id))
        if horizon in (2, 3, 4, 5):
            rolling.append((f"{chain}.{family}", horizon, request.evaluation_id))

    with (bundle / "cells.tsv").open("x", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, delimiter="\t", lineterminator="\n")
        writer.writerow(("cell", "request", "evaluation_id"))
        writer.writerows(rows)
    with (bundle / "rolling.tsv").open("x", newline="", encoding="utf-8") as destination:
        writer = csv.writer(destination, delimiter="\t", lineterminator="\n")
        writer.writerow(("cell", "horizon", "evaluation_id"))
        writer.writerows(rolling)

    print(experiment_id)


def report(storage_root: Path, experiment_id: UUID) -> None:
    storage_root = storage_root.resolve()
    bundle = _bundle_path(storage_root, experiment_id)
    with (bundle / "cells.tsv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))

    results = [
        pl.DataFrame({"cell": [row["cell"]]}).hstack(
            reduce_evaluation(storage_root, UUID(row["evaluation_id"]))
        )
        for row in rows
    ]
    print(pl.concat(results).write_csv(None, separator="\t"), end="")


def rolling(storage_root: Path, experiment_id: UUID) -> None:
    storage_root = storage_root.resolve()
    bundle = _bundle_path(storage_root, experiment_id)
    with (bundle / "rolling.tsv").open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    roster: dict[str, dict[int, UUID]] = {}
    for row in rows:
        roster.setdefault(row["cell"], {})[int(row["horizon"])] = UUID(row["evaluation_id"])
    print(reduce_rolling(storage_root, roster).write_csv(None, separator="\t"), end="")


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("storage_root", type=Path)
    prepare_parser.add_argument("hpo_experiment_id", type=UUID)
    prepare_parser.add_argument("k_experiment_id", type=UUID)
    prepare_parser.add_argument("--experiment-id", type=UUID, default=None)
    report_parser = commands.add_parser("report")
    report_parser.add_argument("storage_root", type=Path)
    report_parser.add_argument("experiment_id", type=UUID)
    rolling_parser = commands.add_parser("rolling")
    rolling_parser.add_argument("storage_root", type=Path)
    rolling_parser.add_argument("experiment_id", type=UUID)
    arguments = parser.parse_args()

    if arguments.command == "prepare":
        prepare(
            arguments.storage_root,
            arguments.hpo_experiment_id,
            arguments.k_experiment_id,
            arguments.experiment_id or uuid4(),
        )
    elif arguments.command == "report":
        report(arguments.storage_root, arguments.experiment_id)
    else:
        rolling(arguments.storage_root, arguments.experiment_id)


if __name__ == "__main__":
    main()
