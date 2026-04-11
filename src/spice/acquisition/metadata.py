"""Dataset metadata helpers for acquisition workflows."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any

from ..core.config import ExperimentConfig
from ..data.io import iter_block_files
from ..data.validation import BlockDatasetValidationReport
from .raw_validation import RawPullValidationReport


def has_block_files(path: Path) -> bool:
    try:
        return bool(iter_block_files(path))
    except ValueError:
        return False


def load_dataset_metadata(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Dataset metadata is not a JSON object: {path}")
    return payload


def provider_metadata(config: ExperimentConfig) -> dict[str, str]:
    endpoint = config.provider.endpoint_for(config.chain.name)
    return {
        "name": config.provider.name.value,
        "reference": config.provider.reference_for(config.chain.name),
        "endpoint_fingerprint": sha256(endpoint.encode("utf-8")).hexdigest()[:16],
    }


def check_existing_dataset_metadata(
    *,
    config: ExperimentConfig,
    metadata_path: Path,
    overwrite: bool,
) -> dict[str, Any] | None:
    metadata = load_dataset_metadata(metadata_path)
    if metadata is None:
        if not overwrite and _metadata_has_dataset_files(config):
            raise ValueError(
                f"Dataset files exist without canonical metadata at {metadata_path}; "
                "rerun with acquisition.overwrite=true to replace them."
            )
        return None

    if overwrite:
        return metadata

    expected = {
        "dataset_id": config.dataset.id,
        "chain_name": config.chain.name.value,
        "chain_id": config.chain.chain_id,
        "provider": provider_metadata(config),
        "evaluation_window": {
            "start_timestamp": config.dataset.window.start_timestamp,
            "end_timestamp": config.dataset.window.end_timestamp,
        },
    }
    actual = {
        "dataset_id": metadata.get("dataset", {}).get("id"),
        "chain_name": metadata.get("chain", {}).get("name"),
        "chain_id": metadata.get("chain", {}).get("chain_id"),
        "provider": metadata.get("provider"),
        "evaluation_window": metadata.get("windows", {}).get("evaluation"),
    }
    if actual != expected:
        raise ValueError(
            "Existing dataset metadata does not match the requested dataset window/provider. "
            f"Expected {expected}, got {actual}. Use acquisition.overwrite=true to replace it."
        )
    return metadata


def compact_validation_report(
    report: RawPullValidationReport | BlockDatasetValidationReport,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": report.status,
        "rows": report.row_count,
        "block_range": {
            "first": report.first_block_number,
            "last": report.last_block_number,
        },
        "timestamp_range": {
            "first": report.first_timestamp,
            "last": report.last_timestamp,
        },
    }
    if isinstance(report, RawPullValidationReport):
        payload["files"] = report.file_count

    issue_counts: dict[str, int] = {}
    for name in (
        "gap_count",
        "overlap_count",
        "duplicate_count",
        "chain_id_mismatch_count",
        "below_start_count",
        "above_end_count",
    ):
        value = getattr(report, name, 0)
        if value:
            issue_counts[name.removesuffix("_count")] = int(value)
    if issue_counts or report.errors:
        payload["issues"] = {
            **issue_counts,
            **({"errors": report.errors} if report.errors else {}),
        }
    return payload


def build_dataset_metadata(
    *,
    config: ExperimentConfig,
    raw_history_dir: Path,
    raw_evaluation_dir: Path,
    enriched_history_dir: Path,
    enriched_evaluation_dir: Path,
    history_window_start: int,
    history_window_end: int,
    evaluation_window_start: int,
    evaluation_window_end: int,
    history_validation: RawPullValidationReport,
    evaluation_validation: RawPullValidationReport,
    history_enriched: BlockDatasetValidationReport,
    evaluation_enriched: BlockDatasetValidationReport,
) -> dict[str, object]:
    return {
        "dataset": {
            "id": config.dataset.id,
        },
        "chain": {
            "name": config.chain.name.value,
            "chain_id": config.chain.chain_id,
        },
        "provider": provider_metadata(config),
        "paths": {
            "raw": {
                "history": raw_history_dir.as_posix(),
                "evaluation": raw_evaluation_dir.as_posix(),
            },
            "enriched": {
                "history": enriched_history_dir.as_posix(),
                "evaluation": enriched_evaluation_dir.as_posix(),
            },
        },
        "windows": {
            "history": {
                "start_timestamp": history_window_start,
                "end_timestamp": history_window_end,
            },
            "evaluation": {
                "start_timestamp": evaluation_window_start,
                "end_timestamp": evaluation_window_end,
            },
        },
        "settings": {
            "sampling": {
                "anchor_count": config.dataset.sampling.anchor_count,
                "history_anchor_count": config.dataset.sampling.effective_history_anchor_count,
            },
            "temporal": {
                "lookback_seconds": config.dataset.temporal.lookback_seconds,
                "max_delay_seconds": config.dataset.temporal.max_delay_seconds,
            },
            "acquisition": {
                "chunk_size": config.acquisition.chunk_size,
                "enrich_batch_size": config.acquisition.enrich_batch_size,
                "max_methods_per_second": config.acquisition.max_methods_per_second,
            },
        },
        "validation": {
            "raw": {
                "history": compact_validation_report(history_validation),
                "evaluation": compact_validation_report(evaluation_validation),
            },
            "enriched": {
                "history": compact_validation_report(history_enriched),
                "evaluation": compact_validation_report(evaluation_enriched),
            },
        },
    }


def _metadata_has_dataset_files(config: ExperimentConfig) -> bool:
    for candidate in (
        Path(config.paths.raw_history_dir),
        Path(config.paths.raw_evaluation_dir),
        Path(config.paths.enriched_history_dir),
        Path(config.paths.enriched_evaluation_dir),
    ):
        if has_block_files(candidate):
            return True
    return False
