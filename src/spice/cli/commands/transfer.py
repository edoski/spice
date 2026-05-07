"""Storage transfer command routing."""

from __future__ import annotations

from typing import Annotated

import typer

from ...execution.transfer_transaction import open_storage_transfer_transaction
from ...storage.catalog.records import CatalogArtifactRecord, CatalogDatasetRecord
from ...storage.engine import RootKind
from ...storage.inspect_artifact import artifact_local_dependency_warnings
from ..errors import OperatorTyper
from ..options import (
    DEFAULT_REMOTE_TARGET,
    RemoteTargetOption,
    StorageRootReadOption,
    resolve_storage_root,
)

push_app = OperatorTyper(
    help="Copy one local root into cluster storage.",
    no_args_is_help=True,
)
pull_app = OperatorTyper(
    help="Copy one cluster root into local storage.",
    no_args_is_help=True,
)
app = OperatorTyper(
    help="Copy storage roots between local and cluster storage.",
    no_args_is_help=True,
)
app.add_typer(push_app, name="push")
app.add_typer(pull_app, name="pull")
ReplaceOption = Annotated[
    bool,
    typer.Option("--replace", help="Replace an existing destination root."),
]


@push_app.command("dataset", short_help="Push one dataset root to cluster storage.")
def push_dataset_command(
    dataset_id: Annotated[
        str,
        typer.Option("--dataset-id", metavar="DATASET_ID", help="Push this dataset root."),
    ],
    storage_root: StorageRootReadOption = None,
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
    replace: ReplaceOption = False,
) -> None:
    root = resolve_storage_root(storage_root)
    transaction = open_storage_transfer_transaction(target, local_storage_root=root)
    transferred = transaction.push_root(RootKind.CORPUS, dataset_id, replace=replace)
    record = transferred.destination_record
    if not isinstance(record, CatalogDatasetRecord):
        raise TypeError("transfer push dataset returned non-dataset record")
    typer.echo(f"push dataset={record.dataset_name} dataset_id={record.dataset_id}")


@pull_app.command("artifact", short_help="Pull one artifact root from cluster storage.")
def pull_artifact_command(
    artifact_id: Annotated[
        str,
        typer.Option("--artifact-id", metavar="ARTIFACT_ID", help="Pull this artifact root."),
    ],
    storage_root: StorageRootReadOption = None,
    target: RemoteTargetOption = DEFAULT_REMOTE_TARGET,
    replace: ReplaceOption = False,
) -> None:
    root = resolve_storage_root(storage_root)
    transaction = open_storage_transfer_transaction(target, local_storage_root=root)
    pulled = transaction.pull_root(RootKind.ARTIFACT, artifact_id, replace=replace)
    record = pulled.destination_record
    if not isinstance(record, CatalogArtifactRecord):
        raise TypeError("transfer pull artifact returned non-artifact record")
    typer.echo(f"pull artifact={record.artifact_id}")
    for warning in artifact_local_dependency_warnings(root, record):
        typer.echo(f"warning: {warning}", err=True)
