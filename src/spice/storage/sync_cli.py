"""CLI transport wrapper for remote storage sync operations."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, cast

from .engine import RootKind
from .roots import (
    ArtifactSelector,
    StudySelector,
    resolve_artifact_record,
    resolve_study_record,
)
from .staging import cleanup_root_stage, prepare_root_stage, promote_root_stage


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m spice.storage.sync_cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-stage")
    prepare.add_argument("--destination-root", required=True)
    prepare.add_argument("--staged-root", required=True)
    prepare.add_argument("--replace", action="store_true")
    prepare.set_defaults(func=_prepare_stage_command)

    finalize = subparsers.add_parser("finalize-stage")
    finalize.add_argument("--storage-root", required=True)
    finalize.add_argument("--destination-root", required=True)
    finalize.add_argument("--staged-root", required=True)
    finalize.add_argument("--expected-root-kind", required=True)
    finalize.add_argument("--replace", action="store_true")
    finalize.set_defaults(func=_finalize_stage_command)

    cleanup = subparsers.add_parser("cleanup-stage")
    cleanup.add_argument("--staged-root", required=True)
    cleanup.set_defaults(func=_cleanup_stage_command)

    resolve_study = subparsers.add_parser("resolve-study-record")
    resolve_study.add_argument("--storage-root", required=True)
    resolve_study.add_argument("--selector-json", required=True)
    resolve_study.set_defaults(func=_resolve_study_record_command)

    resolve_artifact = subparsers.add_parser("resolve-artifact-record")
    resolve_artifact.add_argument("--storage-root", required=True)
    resolve_artifact.add_argument("--selector-json", required=True)
    resolve_artifact.set_defaults(func=_resolve_artifact_record_command)

    namespace = parser.parse_args(argv)
    namespace.func(namespace)


def _prepare_stage_command(args: argparse.Namespace) -> None:
    prepare_root_stage(
        destination_root=Path(args.destination_root),
        staged_root=Path(args.staged_root),
        replace=args.replace,
    )


def _finalize_stage_command(args: argparse.Namespace) -> None:
    storage_root = Path(args.storage_root)
    destination_root = Path(args.destination_root)
    staged_root = Path(args.staged_root)
    promote_root_stage(
        storage_root=storage_root,
        destination_root=destination_root,
        staged_root=staged_root,
        expected_root_kind=RootKind(args.expected_root_kind),
        replace=args.replace,
    )


def _cleanup_stage_command(args: argparse.Namespace) -> None:
    cleanup_root_stage(Path(args.staged_root))


def _resolve_study_record_command(args: argparse.Namespace) -> None:
    selector_payload = json.loads(args.selector_json)
    record = resolve_study_record(
        Path(args.storage_root),
        selector=StudySelector(**selector_payload),
    )
    _emit_record_json(record)


def _resolve_artifact_record_command(args: argparse.Namespace) -> None:
    selector_payload = json.loads(args.selector_json)
    record = resolve_artifact_record(
        Path(args.storage_root),
        selector=ArtifactSelector(**selector_payload),
    )
    _emit_record_json(record)


def _emit_record_json(record: object) -> None:
    if not is_dataclass(record) or isinstance(record, type):
        raise TypeError("record must be a dataclass instance")
    payload = asdict(cast(Any, record))
    print(
        json.dumps(
            {
                key: (str(value) if isinstance(value, Path) else value)
                for key, value in payload.items()
            }
        )
    )


if __name__ == "__main__":
    main()
