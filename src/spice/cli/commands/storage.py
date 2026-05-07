"""Storage command routing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from ...core.errors import SpiceOperatorError
from ...storage.operator import (
    ArtifactInspectionDetail,
    DatasetInspectionDetail,
    StorageDeleteCommand,
    StorageDeleteCompleted,
    StorageDeleteFailure,
    StorageRootKind,
    StorageShowFailure,
    StorageShowQuery,
    StorageShowRendered,
    StudyInspectionDetail,
    delete_storage,
    refresh_storage_catalog,
    render_catalog_refresh,
    show_storage,
)
from ...storage.selectors import ArtifactSelector, DatasetSelector, StudySelector
from ..errors import OperatorTyper
from ..options import (
    ChainFilterOption,
    DatasetFilterOption,
    FeaturesFilterOption,
    ModelFilterOption,
    PredictionFilterOption,
    ProblemFilterOption,
    StorageRootDeleteOption,
    StorageRootReadOption,
    StudyFilterOption,
    VariantFilterOption,
    resolve_storage_root,
)
from ..output import echo_sections

show_app = OperatorTyper(
    help="Query stored datasets, studies, and artifacts.",
    epilog=(
        "Example:\n"
        "  spice show artifact --chain ethereum --dataset icdcs_2026 --detail epochs"
    ),
    no_args_is_help=True,
)
delete_app = OperatorTyper(
    help="Delete stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)
refresh_app = OperatorTyper(
    help="Rebuild derived storage indexes.",
    no_args_is_help=True,
)


DatasetDetailOption = Annotated[
    DatasetInspectionDetail | None,
    typer.Option("--detail", metavar="DETAIL", help="Show one detail table: runs."),
]
StudyDetailOption = Annotated[
    StudyInspectionDetail | None,
    typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: trials or config.",
    ),
]
ArtifactDetailOption = Annotated[
    ArtifactInspectionDetail | None,
    typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: epochs or runs.",
    ),
]


@dataclass(frozen=True, slots=True)
class _StorageCliSpec:
    kind: StorageRootKind
    selector_flags: dict[str, str]


_CLI_SPECS: tuple[_StorageCliSpec, ...] = (
    _StorageCliSpec(
        kind="dataset",
        selector_flags={
            "chain_name": "--chain",
            "dataset_name": "--dataset",
        },
    ),
    _StorageCliSpec(
        kind="study",
        selector_flags={
            "chain_name": "--chain",
            "dataset_name": "--dataset",
            "features_id": "--features",
            "prediction_id": "--prediction",
            "model_id": "--model",
            "problem_id": "--problem",
            "study_name": "--study",
        },
    ),
    _StorageCliSpec(
        kind="artifact",
        selector_flags={
            "chain_name": "--chain",
            "dataset_name": "--dataset",
            "features_id": "--features",
            "prediction_id": "--prediction",
            "model_id": "--model",
            "problem_id": "--problem",
            "variant": "--variant",
            "study_name": "--study",
        },
    ),
)
_SELECTOR_FLAGS = tuple(spec.selector_flags for spec in _CLI_SPECS)


def _dataset_selector(
    *,
    dataset_id: str | None = None,
    chain: str | None,
    dataset: str | None,
) -> DatasetSelector:
    return DatasetSelector(dataset_id=dataset_id, chain_name=chain, dataset_name=dataset)


def _raise_show_failure(outcome: StorageShowFailure) -> NoReturn:
    for diagnostic in outcome.diagnostics:
        _print_sections(diagnostic.title, diagnostic.sections, err=True)
    raise SpiceOperatorError(
        f"{outcome.message}{_narrowing_guidance(outcome.narrowing_attributes)}"
    )


def _raise_delete_failure(outcome: StorageDeleteFailure) -> NoReturn:
    for diagnostic in outcome.diagnostics:
        _print_sections(diagnostic.title, diagnostic.sections, err=True)
    raise SpiceOperatorError(
        f"{outcome.message}"
        f"{_cascade_guidance(outcome)}"
        f"{_narrowing_guidance(outcome.narrowing_attributes)}"
    )


def _narrowing_guidance(attributes: tuple[str, ...]) -> str:
    flags = [
        flag for kind_flags in _SELECTOR_FLAGS for attribute in attributes
        if (flag := kind_flags.get(attribute)) is not None
    ]
    if not flags:
        return ""
    return f". Try {', '.join(dict.fromkeys(flags))}."


def _cascade_guidance(outcome: StorageDeleteFailure) -> str:
    return " Re-run with --cascade." if outcome.cascade_available else ""


def _render_show(outcome: StorageShowRendered | StorageShowFailure) -> None:
    if isinstance(outcome, StorageShowFailure):
        _raise_show_failure(outcome)
    _print_sections(outcome.renderable.title, outcome.renderable.sections)


def _print_sections(
    title: str,
    sections: list[tuple[str, list[tuple[str, str]]]],
    *,
    err: bool = False,
) -> None:
    echo_sections(title, sections, err=err)


def _handle_delete(outcome: StorageDeleteCompleted | StorageDeleteFailure) -> None:
    if isinstance(outcome, StorageDeleteFailure):
        _raise_delete_failure(outcome)


def _run_show(
    *,
    storage_root: Path | None,
    kind: StorageRootKind,
    selector: DatasetSelector | StudySelector | ArtifactSelector,
    detail: str | None,
) -> None:
    _render_show(
        show_storage(
            StorageShowQuery(
                storage_root=resolve_storage_root(storage_root),
                kind=kind,
                selector=selector,
                detail=detail,
            )
        )
    )


def _run_delete(
    *,
    storage_root: Path | None,
    kind: StorageRootKind,
    selector: DatasetSelector | StudySelector | ArtifactSelector,
    cascade: bool = False,
) -> None:
    _handle_delete(
        delete_storage(
            StorageDeleteCommand(
                storage_root=resolve_storage_root(storage_root),
                kind=kind,
                selector=selector,
                cascade=cascade,
            )
        )
    )


@show_app.command(
    "dataset",
    short_help="Show datasets.",
    help="List datasets or show one dataset in detail.",
)
def show_dataset_command(
    dataset_id: Annotated[
        str | None,
        typer.Option("--dataset-id", metavar="DATASET_ID", help="Show this dataset root."),
    ] = None,
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: DatasetDetailOption = None,
) -> None:
    selector = _dataset_selector(dataset_id=dataset_id, chain=chain, dataset=dataset)
    _run_show(
        storage_root=storage_root,
        kind="dataset",
        selector=selector,
        detail=None if detail is None else detail.value,
    )


@show_app.command(
    "study",
    short_help="Show studies.",
    help="List studies or show one study in detail.",
)
def show_study_command(
    study_id: Annotated[
        str | None,
        typer.Option("--study-id", metavar="STUDY_ID", help="Show this study root."),
    ] = None,
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    features: FeaturesFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: StudyDetailOption = None,
) -> None:
    selector = StudySelector(
        study_id=study_id,
        chain_name=chain,
        dataset_name=dataset,
        features_id=features,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        study_name=study,
    )
    _run_show(
        storage_root=storage_root,
        kind="study",
        selector=selector,
        detail=None if detail is None else detail.value,
    )


@show_app.command(
    "artifact",
    short_help="Show artifacts.",
    help="List artifacts or show one artifact in detail.",
)
def show_artifact_command(
    artifact_id: Annotated[
        str | None,
        typer.Option("--artifact-id", metavar="ARTIFACT_ID", help="Show this artifact root."),
    ] = None,
    dataset_id: Annotated[
        str | None,
        typer.Option("--dataset-id", metavar="DATASET_ID", help="Filter by dataset root."),
    ] = None,
    study_id: Annotated[
        str | None,
        typer.Option("--study-id", metavar="STUDY_ID", help="Filter by study root."),
    ] = None,
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    features: FeaturesFilterOption = None,
    prediction: PredictionFilterOption = None,
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    variant: VariantFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: ArtifactDetailOption = None,
) -> None:
    selector = ArtifactSelector(
        artifact_id=artifact_id,
        dataset_id=dataset_id,
        study_id=study_id,
        chain_name=chain,
        dataset_name=dataset,
        features_id=features,
        prediction_id=prediction,
        model_id=model,
        problem_id=problem,
        variant=variant,
        study_name=study,
    )
    _run_show(
        storage_root=storage_root,
        kind="artifact",
        selector=selector,
        detail=None if detail is None else detail.value,
    )


@delete_app.command(
    "artifact",
    short_help="Delete one artifact.",
    help="Delete exactly one artifact.",
)
def delete_artifact_command(
    artifact_id: Annotated[
        str,
        typer.Option("--artifact-id", metavar="ARTIFACT_ID", help="Delete this artifact root."),
    ],
    storage_root: StorageRootDeleteOption = None,
) -> None:
    _run_delete(
        storage_root=storage_root,
        kind="artifact",
        selector=ArtifactSelector(artifact_id=artifact_id),
    )


@delete_app.command(
    "study",
    short_help="Delete one study.",
    help=("Delete exactly one study. Use --cascade to also delete dependent tuned artifacts."),
)
def delete_study_command(
    study_id: Annotated[
        str,
        typer.Option("--study-id", metavar="STUDY_ID", help="Delete this study root."),
    ],
    storage_root: StorageRootDeleteOption = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent tuned artifacts."),
    ] = False,
) -> None:
    _run_delete(
        storage_root=storage_root,
        kind="study",
        selector=StudySelector(study_id=study_id),
        cascade=cascade,
    )


@refresh_app.command("catalog", short_help="Rebuild the derived storage catalog.")
def refresh_catalog_command(
    storage_root: StorageRootReadOption = None,
) -> None:
    root = resolve_storage_root(storage_root)
    typer.echo(render_catalog_refresh(refresh_storage_catalog(root)))


@delete_app.command(
    "dataset",
    short_help="Delete one dataset.",
    help=(
        "Delete exactly one dataset. Use --cascade to also delete dependent studies and artifacts."
    ),
)
def delete_dataset_command(
    dataset_id: Annotated[
        str,
        typer.Option("--dataset-id", metavar="DATASET_ID", help="Delete this dataset root."),
    ],
    storage_root: StorageRootDeleteOption = None,
    cascade: Annotated[
        bool,
        typer.Option("--cascade", help="Also delete dependent studies and artifacts."),
    ] = False,
) -> None:
    _run_delete(
        storage_root=storage_root,
        kind="dataset",
        selector=DatasetSelector(dataset_id=dataset_id),
        cascade=cascade,
    )
