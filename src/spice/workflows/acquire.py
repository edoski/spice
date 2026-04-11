"""Hydra entrypoint for direct block dataset acquisition."""

from __future__ import annotations

import json
from pathlib import Path

import hydra
from omegaconf import DictConfig

from ..acquisition.datasets import (
    ensure_evaluation_dataset,
    ensure_history_dataset,
)
from ..acquisition.metadata import (
    build_dataset_metadata,
    check_existing_dataset_metadata,
)
from ..acquisition.rpc import Web3BlockClient, evaluation_range
from ..acquisition.windowing import (
    history_range_from_metadata,
    initial_history_range,
    required_history_block_count,
)
from ..core.config import ExperimentConfig, coerce_config
from ..core.console import Reporter
from ..core.json import write_json
from ..core.tracking import log_artifacts
from ._shared import managed_workflow


def run(config: ExperimentConfig, *, reporter: Reporter | None = None) -> None:
    history_dir = Path(config.paths.history_dir)
    evaluation_dir = Path(config.paths.evaluation_dir)
    metadata_path = Path(config.paths.dataset_metadata_path)

    required_history_blocks = required_history_block_count(config)
    history_window = initial_history_range(
        config,
        required_history_blocks=required_history_blocks,
    )
    evaluation_window = evaluation_range(
        config.dataset.window.start_timestamp,
        config.dataset.window.end_timestamp,
    )
    existing_metadata = check_existing_dataset_metadata(
        config=config,
        metadata_path=metadata_path,
        overwrite=config.acquisition.overwrite,
    )
    if existing_metadata is not None and not config.acquisition.overwrite:
        history_window = history_range_from_metadata(existing_metadata)

    block_client = Web3BlockClient(config.provider, config.chain)
    with managed_workflow(
        config,
        run_name=f"acquire-{config.chain.name.value}-{config.provider.name.value}",
        reporter=reporter,
    ) as session:
        if config.acquisition.dry_run:
            history_plan = block_client.plan_window(
                history_window,
                chunk_size=config.acquisition.chunk_size,
            )
            evaluation_plan = block_client.plan_window(
                evaluation_window,
                chunk_size=config.acquisition.chunk_size,
            )
            session.reporter.log(
                json.dumps(
                    {
                        "dataset_id": config.dataset.id,
                        "history_window": {
                            "start_timestamp": history_window.start,
                            "end_timestamp": history_window.end,
                            "block_start": history_plan.block_range.start,
                            "block_end": history_plan.block_range.end,
                            "expected_rows": history_plan.expected_rows,
                            "expected_files": history_plan.expected_files,
                        },
                        "evaluation_window": {
                            "start_timestamp": evaluation_window.start,
                            "end_timestamp": evaluation_window.end,
                            "block_start": evaluation_plan.block_range.start,
                            "block_end": evaluation_plan.block_range.end,
                            "expected_rows": evaluation_plan.expected_rows,
                            "expected_files": evaluation_plan.expected_files,
                        },
                        "history_validation": "dry_run",
                        "evaluation_validation": "dry_run",
                    }
                )
            )
            return

        history_result, history_validation, history_window = ensure_history_dataset(
            config=config,
            block_client=block_client,
            output_dir=history_dir,
            history_window=history_window,
            required_history_blocks=required_history_blocks,
            reporter=session.reporter,
        )
        evaluation_result, evaluation_validation = ensure_evaluation_dataset(
            config=config,
            block_client=block_client,
            output_dir=evaluation_dir,
            evaluation_window=evaluation_window,
            reporter=session.reporter,
        )
        metadata = build_dataset_metadata(
            config=config,
            history_dir=history_dir,
            evaluation_dir=evaluation_dir,
            history_window_start=history_window.start,
            history_window_end=history_window.end,
            evaluation_window_start=evaluation_window.start,
            evaluation_window_end=evaluation_window.end,
            history_validation=history_validation,
            evaluation_validation=evaluation_validation,
        )
        metadata_task = session.reporter.start_task("write dataset metadata")
        write_json(metadata_path, metadata)
        session.reporter.finish_task(metadata_task, message=str(metadata_path))
        session.reporter.log(
            json.dumps(
                {
                    "history_rows": history_validation.row_count,
                    "evaluation_rows": evaluation_validation.row_count,
                    "history_validation": history_validation.status,
                    "evaluation_validation": evaluation_validation.status,
                    "history_files": 0 if history_result is None else history_result.expected_files,
                    "evaluation_files": (
                        0 if evaluation_result is None else evaluation_result.expected_files
                    ),
                    "required_history_blocks": required_history_blocks,
                }
            )
        )
        if session.tracking_enabled:
            import mlflow

            mlflow.log_metrics(
                {
                    "history_files": float(
                        0 if history_result is None else history_result.expected_files
                    ),
                    "evaluation_files": float(
                        0 if evaluation_result is None else evaluation_result.expected_files
                    ),
                    "history_gap_count": float(history_validation.gap_count),
                    "evaluation_gap_count": float(evaluation_validation.gap_count),
                }
            )
            log_artifacts([metadata_path])


@hydra.main(version_base=None, config_path="../conf", config_name="acquire")
def main(cfg: DictConfig) -> None:
    run(coerce_config(cfg, task="acquire"))


if __name__ == "__main__":
    main()
