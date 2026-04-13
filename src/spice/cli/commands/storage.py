"""Storage command routing."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from ...storage.inspect import (
    artifact_list_sections,
    dataset_list_sections,
    describe_root,
    sectioned_summary,
    study_list_sections,
)
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
    ProblemFilterOption,
    StorageRootDeleteOption,
    StorageRootReadOption,
    StudyFilterOption,
    VariantFilterOption,
    fail,
    print_sections,
    resolve_storage_root,
)

show_app = typer.Typer(
    help="Query stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)
delete_app = typer.Typer(
    help="Delete stored datasets, studies, and artifacts.",
    no_args_is_help=True,
)


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
) -> None:
    if not records:
        fail(f"No {kind} matches found")
    if detail is not None and len(records) != 1:
        print_sections(f"{kind} matches", list_sections(records))
        fail(f"--detail requires exactly one {kind} match")
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
) -> None:
    if error.records:
        print_sections(f"{error.kind} matches", list_sections(list(error.records)))
    fail(str(error))


def _handle_delete_blocked(error: DeleteBlockedError) -> None:
    if error.artifact_records:
        print_sections("artifact matches", artifact_list_sections(list(error.artifact_records)))
    if error.study_records:
        print_sections("study matches", study_list_sections(list(error.study_records)))
    fail(str(error))


@show_app.command(
    "dataset",
    short_help="Show datasets.",
    help="List datasets or show one dataset in detail.",
)
def show_dataset_command(
    chain: ChainFilterOption = None,
    dataset: DatasetFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: str | None = typer.Option(
        "--detail", metavar="DETAIL", help="Show one detail table: runs."
    ),
) -> None:
    root = resolve_storage_root(storage_root)
    records = list_dataset_records(
        root,
        selector=DatasetSelector(chain_name=chain, dataset_name=dataset),
    )
    _show_records(
        kind="dataset",
        records=records,
        has_filters=chain is not None or dataset is not None,
        detail=detail,
        list_sections=dataset_list_sections,
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
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: str | None = typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: trials or config.",
    ),
) -> None:
    root = resolve_storage_root(storage_root)
    records = list_study_records(
        root,
        selector=StudySelector(
            chain_name=chain,
            dataset_name=dataset,
            feature_set_id=feature_set,
            model_id=model,
            problem_id=problem,
            study_name=study,
        ),
    )
    _show_records(
        kind="study",
        records=records,
        has_filters=any(
            value is not None for value in (chain, dataset, feature_set, model, problem, study)
        ),
        detail=detail,
        list_sections=study_list_sections,
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
    model: ModelFilterOption = None,
    problem: ProblemFilterOption = None,
    variant: VariantFilterOption = None,
    study: StudyFilterOption = None,
    storage_root: StorageRootReadOption = None,
    detail: str | None = typer.Option(
        "--detail",
        metavar="DETAIL",
        help="Show one detail table: epochs or runs.",
    ),
) -> None:
    root = resolve_storage_root(storage_root)
    records = list_artifact_records(
        root,
        selector=ArtifactSelector(
            chain_name=chain,
            dataset_name=dataset,
            feature_set_id=feature_set,
            model_id=model,
            problem_id=problem,
            variant=variant,
            study_name=study,
        ),
    )
    _show_records(
        kind="artifact",
        records=records,
        has_filters=any(
            value is not None
            for value in (chain, dataset, feature_set, model, problem, variant, study)
        ),
        detail=detail,
        list_sections=artifact_list_sections,
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
        model_id=model,
        problem_id=problem,
        variant=variant,
        study_name=study,
    )
    try:
        record = resolve_artifact_record(root, selector=selector)
    except SelectorResolutionError as error:
        _handle_selector_error(error, list_sections=artifact_list_sections)
        return
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
        model_id=model,
        problem_id=problem,
        study_name=study,
    )
    try:
        record = resolve_study_record(root, selector=selector)
    except SelectorResolutionError as error:
        _handle_selector_error(error, list_sections=study_list_sections)
        return
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
        _handle_selector_error(error, list_sections=dataset_list_sections)
        return
    try:
        delete_dataset_record(root, record=record, cascade=cascade)
    except DeleteBlockedError as error:
        _handle_delete_blocked(error)
