"""Storage command routing."""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from ...core.errors import SpiceOperatorError
from ...remote import resolve_remote_target, run_remote_cli
from ...storage.inspect import describe_root, sectioned_summary
from ...storage.inspect_artifact import artifact_list_sections
from ...storage.inspect_dataset import dataset_list_sections
from ...storage.inspect_study import study_list_sections
from ...storage.query import (
    ArtifactSelector,
    DatasetSelector,
    DeleteBlockedError,
    SelectorResolutionError,
    StudySelector,
    delete_artifact_record,
    delete_dataset_record,
    delete_study_record,
    list_artifact_records,
    list_dataset_records,
    list_study_records,
    resolve_artifact_record,
    resolve_dataset_record,
    resolve_study_record,
)
from ..options import (
    ChainFilterOption,
    DatasetFilterOption,
    FeatureSetFilterOption,
    ModelFilterOption,
    PredictionFilterOption,
    ProblemFilterOption,
    RemoteOption,
    StorageRootDeleteOption,
    StorageRootReadOption,
    StudyFilterOption,
    VariantFilterOption,
    print_sections,
    resolve_storage_root,
)

show_app = typer.Typer(
    help="Query stored datasets, studies, and artifacts.",
    epilog=(
        "Example:\n"
        "  spice show artifact --chain ethereum --dataset icdcs_2026 --detail epochs"
    ),
    no_args_is_help=True,
)
delete_app = typer.Typer(
    help="Delete stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)


class DatasetDetail(StrEnum):
    RUNS = "runs"


class StudyDetail(StrEnum):
    TRIALS = "trials"
    CONFIG = "config"


class ArtifactDetail(StrEnum):
    EPOCHS = "epochs"
    RUNS = "runs"


DatasetDetailOption = Annotated[
    DatasetDetail | None,
    typer.Option("--detail", metavar="DETAIL", help="Show one detail table: runs."),
]
StudyDetailOption = Annotated[
    StudyDetail | None,
    typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: trials or config.",
    ),
]
ArtifactDetailOption = Annotated[
    ArtifactDetail | None,
    typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: epochs or runs.",
    ),
]


_SELECTOR_FLAGS: dict[str, dict[str, str]] = {
    "dataset": {
        "chain_name": "--chain",
        "dataset_name": "--dataset",
    },
    "study": {
        "chain_name": "--chain",
        "dataset_name": "--dataset",
        "feature_set_id": "--feature-set",
        "prediction_id": "--prediction",
        "model_id": "--model",
        "problem_id": "--problem",
        "study_name": "--study",
    },
    "artifact": {
        "chain_name": "--chain",
        "dataset_name": "--dataset",
        "feature_set_id": "--feature-set",
        "prediction_id": "--prediction",
        "model_id": "--model",
        "problem_id": "--problem",
        "variant": "--variant",
        "study_name": "--study",
    },
}


def _show_root_detail(root_path: Path, *, detail: str | None) -> None:
    description = describe_root(root_path, detail=detail)
    title, sections = sectioned_summary(description)
    print_sections(title, sections)


def _show_records(
    *,
    kind: str,
    records,
    has_filters: bool,
    detail: str | None,
    list_sections,
    selector: object,
) -> None:
    if not records:
        raise SpiceOperatorError(f"No {kind} matches found")
    if detail is not None and len(records) != 1:
        print_sections(f"{kind} matches", list_sections(records))
        raise SpiceOperatorError(
            f"--detail requires exactly one {kind} match"
            f"{_narrowing_guidance(kind, records, selector=selector)}"
        )
    if detail is not None:
        _show_root_detail(records[0].root_path, detail=detail)
        return
    if not has_filters or len(records) != 1:
        print_sections(f"{kind} list", list_sections(records))
        return
    _show_root_detail(records[0].root_path, detail=None)


def _handle_selector_error(
    error: SelectorResolutionError,
    *,
    list_sections,
    selector: object,
) -> NoReturn:
    if error.records:
        print_sections(f"{error.kind} matches", list_sections(list(error.records)))
    raise SpiceOperatorError(
        f"{error}{_narrowing_guidance(error.kind, error.records, selector=selector)}"
    )


def _narrowing_guidance(kind: str, records: Sequence[object], *, selector: object) -> str:
    if len(records) <= 1:
        return ""
    flags = [
        flag
        for attribute, flag in _SELECTOR_FLAGS.get(kind, {}).items()
        if getattr(selector, attribute, None) is None
        and len({getattr(record, attribute, None) for record in records}) > 1
    ]
    if not flags:
        return ""
    return f". Try {', '.join(flags)}."


def _handle_delete_blocked(error: DeleteBlockedError) -> NoReturn:
    if error.artifact_records:
        print_sections("artifact matches", artifact_list_sections(list(error.artifact_records)))
    if error.study_records:
        print_sections("study matches", study_list_sections(list(error.study_records)))
    raise SpiceOperatorError(str(error))


def _show_remote(args: list[str], *, storage_root: Path | None) -> None:
    if storage_root is not None:
        raise SpiceOperatorError("--storage-root is not supported with --remote")
    target = resolve_remote_target()
    result = run_remote_cli(
        target,
        [
            *args,
            "--storage-root",
            str(target.spec.paths.storage_root),
        ],
    )
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        raise SpiceOperatorError(message or "remote show failed")
    typer.echo(result.stdout, nl=False)


@show_app.command(
    "dataset",
    short_help="Show datasets.",
    help="List datasets or show one dataset in detail.",
)
def show_dataset_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: DatasetDetailOption = None,
    remote: RemoteOption = False,
) -> None:
    if remote:
        args = ["show", "dataset"]
        if chain is not None:
            args.extend(["--chain", chain])
        if dataset is not None:
            args.extend(["--dataset", dataset])
        if detail is not None:
            args.extend(["--detail", detail.value])
        _show_remote(args, storage_root=storage_root)
        return
    root = resolve_storage_root(storage_root)
    selector = DatasetSelector(chain_name=chain, dataset_name=dataset)
    records = list_dataset_records(
        root,
        selector=selector,
    )
    _show_records(
        kind="dataset",
        records=records,
        has_filters=chain is not None or dataset is not None,
        detail=None if detail is None else detail.value,
        list_sections=dataset_list_sections,
        selector=selector,
    )


@show_app.command(
    "study",
    short_help="Show studies.",
    help="List studies or show one study in detail.",
)
def show_study_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    feature_set: FeatureSetFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: StudyDetailOption = None,
    remote: RemoteOption = False,
) -> None:
    if remote:
        args = ["show", "study"]
        if chain is not None:
            args.extend(["--chain", chain])
        if dataset is not None:
            args.extend(["--dataset", dataset])
        if feature_set is not None:
            args.extend(["--feature-set", feature_set])
        if prediction is not None:
            args.extend(["--prediction", prediction])
        if model is not None:
            args.extend(["--model", model])
        if problem is not None:
            args.extend(["--problem", problem])
        if study is not None:
            args.extend(["--study", study])
        if detail is not None:
            args.extend(["--detail", detail.value])
        _show_remote(args, storage_root=storage_root)
        return
    root = resolve_storage_root(storage_root)
    selector = StudySelector(
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        study_name=study,
    )
    records = list_study_records(
        root,
        selector=selector,
    )
    _show_records(
        kind="study",
        records=records,
        has_filters=any(
            value is not None
            for value in (chain, dataset, feature_set, prediction, model, problem, study)
        ),
        detail=None if detail is None else detail.value,
        list_sections=study_list_sections,
        selector=selector,
    )


@show_app.command(
    "artifact",
    short_help="Show artifacts.",
    help="List artifacts or show one artifact in detail.",
)
def show_artifact_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    feature_set: FeatureSetFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    variant: VariantFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: ArtifactDetailOption = None,
    remote: RemoteOption = False,
) -> None:
    if remote:
        args = ["show", "artifact"]
        if chain is not None:
            args.extend(["--chain", chain])
        if dataset is not None:
            args.extend(["--dataset", dataset])
        if feature_set is not None:
            args.extend(["--feature-set", feature_set])
        if prediction is not None:
            args.extend(["--prediction", prediction])
        if model is not None:
            args.extend(["--model", model])
        if problem is not None:
            args.extend(["--problem", problem])
        if variant is not None:
            args.extend(["--variant", variant])
        if study is not None:
            args.extend(["--study", study])
        if detail is not None:
            args.extend(["--detail", detail.value])
        _show_remote(args, storage_root=storage_root)
        return
    root = resolve_storage_root(storage_root)
    selector = ArtifactSelector(
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        variant=variant,
        study_name=study,
    )
    records = list_artifact_records(
        root,
        selector=selector,
    )
    _show_records(
        kind="artifact",
        records=records,
        has_filters=any(
            value is not None
            for value in (chain, dataset, feature_set, prediction, model, problem, variant, study)
        ),
        detail=None if detail is None else detail.value,
        list_sections=artifact_list_sections,
        selector=selector,
    )


@delete_app.command(
    "artifact",
    short_help="Delete one artifact.",
    help="Delete exactly one artifact.",
)
def delete_artifact_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    feature_set: FeatureSetFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    variant: VariantFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootDeleteOption = None,
) -> None:
    root = resolve_storage_root(storage_root)
    selector = ArtifactSelector(
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        variant=variant,
        study_name=study,
    )
    try:
        record = resolve_artifact_record(root, selector=selector)
    except SelectorResolutionError as error:
        _handle_selector_error(error, list_sections=artifact_list_sections, selector=selector)
    delete_artifact_record(root, record=record)


@delete_app.command(
    "study",
    short_help="Delete one study.",
    help=("Delete exactly one study. Use --cascade to also delete dependent tuned artifacts."),
)
def delete_study_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    feature_set: FeatureSetFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootDeleteOption = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent tuned artifacts."),
    ] = False,
) -> None:
    root = resolve_storage_root(storage_root)
    selector = StudySelector(
        chain_name=chain,
        dataset_name=dataset,
        feature_set_id=feature_set,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        study_name=study,
    )
    try:
        record = resolve_study_record(root, selector=selector)
    except SelectorResolutionError as error:
        _handle_selector_error(error, list_sections=study_list_sections, selector=selector)
    try:
        delete_study_record(root, record=record, cascade=cascade)
    except DeleteBlockedError as error:
        _handle_delete_blocked(error)


@delete_app.command(
    "dataset",
    short_help="Delete one dataset.",
    help=(
        "Delete exactly one dataset. Use --cascade to also delete dependent studies and artifacts."
    ),
)
def delete_dataset_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    storage_root: StorageRootDeleteOption = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent studies and artifacts."),
    ] = False,
) -> None:
    root = resolve_storage_root(storage_root)
    selector = DatasetSelector(chain_name=chain, dataset_name=dataset)
    try:
        record = resolve_dataset_record(root, selector=selector)
    except SelectorResolutionError as error:
        _handle_selector_error(error, list_sections=dataset_list_sections, selector=selector)
    try:
        delete_dataset_record(root, record=record, cascade=cascade)
    except DeleteBlockedError as error:
        _handle_delete_blocked(error)
