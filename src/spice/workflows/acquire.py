"""Hydra entrypoint for dataset acquisition and enrichment."""

from __future__ import annotations

import json
from pathlib import Path

import hydra
import mlflow
from omegaconf import DictConfig
from pydantic import BaseModel, ConfigDict

from ..acquisition.cryo import evaluation_range, history_range_for_chain, run_cryo
from ..acquisition.enrich import enrich_path
from ..acquisition.raw_validation import validate_raw_pull
from ..acquisition.rpc import Web3BlockClient
from ..core.config import ExperimentConfig, coerce_config
from ..core.console import Reporter, RichReporter
from ..core.tracking import configure_mlflow, log_artifacts, log_config
from ..data.io import load_enriched_block_frame
from ._shared import start_run_if_enabled


class EnrichedValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    path: str
    error: str | None = None


def _write_report(path: Path, payload: BaseModel) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")


def _validate_enriched(path: Path) -> EnrichedValidationReport:
    try:
        load_enriched_block_frame(path)
        return EnrichedValidationReport(status="clean", path=str(path))
    except Exception as exc:  # pragma: no cover - surfaced in workflow smoke tests
        return EnrichedValidationReport(status="error", path=str(path), error=str(exc))


def run(config: ExperimentConfig, *, reporter: Reporter | None = None) -> None:
    raw_history_dir = Path(config.paths.raw_history_dir)
    raw_evaluation_dir = Path(config.paths.raw_evaluation_dir)
    enriched_history_dir = Path(config.paths.enriched_history_dir)
    enriched_evaluation_dir = Path(config.paths.enriched_evaluation_dir)
    validation_dir = Path(config.paths.validation_report_dir)
    if config.tracking.enabled:
        configure_mlflow(config)

    history_window = history_range_for_chain(config.chain)
    evaluation_window = evaluation_range()
    block_client = Web3BlockClient(config.provider, config.chain.name)
    active_reporter = reporter or RichReporter()
    run_context = start_run_if_enabled(
        config,
        run_name=f"acquire-{config.chain.name.value}-{config.provider.name.value}",
    )
    try:
        if run_context is not None:
            run_context.__enter__()
            log_config(config)
            mlflow.set_tags(config.tracking.tags)

        history_result = run_cryo(
            config.chain,
            config.pull,
            raw_history_dir,
            history_window,
            provider=config.provider,
            overwrite=config.pull.overwrite,
            dry_run=config.pull.dry_run,
            reporter=active_reporter,
        )
        evaluation_result = run_cryo(
            config.chain,
            config.pull,
            raw_evaluation_dir,
            evaluation_window,
            provider=config.provider,
            overwrite=config.pull.overwrite,
            dry_run=config.pull.dry_run,
            reporter=active_reporter,
        )
        history_validation = validate_raw_pull(
            raw_history_dir,
            expected_chain_name=config.chain.name.value,
            expected_chain_id=config.chain.chain_id,
            expected_start_timestamp=history_window.start,
            expected_end_timestamp=history_window.end,
            expected_chunk_size=config.pull.chunk_size,
        )
        evaluation_validation = validate_raw_pull(
            raw_evaluation_dir,
            expected_chain_name=config.chain.name.value,
            expected_chain_id=config.chain.chain_id,
            expected_start_timestamp=evaluation_window.start,
            expected_end_timestamp=evaluation_window.end,
            expected_chunk_size=config.pull.chunk_size,
        )
        enrich_path(
            raw_history_dir,
            enriched_history_dir,
            fetch_gas_limits=block_client.get_block_gas_limits,
            batch_size=config.pull.enrich_batch_size,
            max_methods_per_second=config.pull.max_methods_per_second,
            reporter=active_reporter,
        )
        enrich_path(
            raw_evaluation_dir,
            enriched_evaluation_dir,
            fetch_gas_limits=block_client.get_block_gas_limits,
            batch_size=config.pull.enrich_batch_size,
            max_methods_per_second=config.pull.max_methods_per_second,
            reporter=active_reporter,
        )

        history_enriched = _validate_enriched(enriched_history_dir)
        evaluation_enriched = _validate_enriched(enriched_evaluation_dir)
        history_report_path = validation_dir / "history_raw.json"
        evaluation_report_path = validation_dir / "evaluation_raw.json"
        history_enriched_path = validation_dir / "history_enriched.json"
        evaluation_enriched_path = validation_dir / "evaluation_enriched.json"
        _write_report(history_report_path, history_validation)
        _write_report(evaluation_report_path, evaluation_validation)
        _write_report(history_enriched_path, history_enriched)
        _write_report(evaluation_enriched_path, evaluation_enriched)
        active_reporter.log(
            json.dumps(
                {
                    "history_completed_chunks": history_result.completed_chunks,
                    "evaluation_completed_chunks": evaluation_result.completed_chunks,
                    "history_validation": history_validation.status,
                    "evaluation_validation": evaluation_validation.status,
                    "history_enriched": history_enriched.status,
                    "evaluation_enriched": evaluation_enriched.status,
                }
            )
        )
        if config.tracking.enabled:
            mlflow.log_metrics(
                {
                    "history_completed_chunks": float(history_result.completed_chunks),
                    "evaluation_completed_chunks": float(evaluation_result.completed_chunks),
                    "history_gap_count": float(history_validation.gap_count),
                    "evaluation_gap_count": float(evaluation_validation.gap_count),
                    "history_overlap_count": float(history_validation.overlap_count),
                    "evaluation_overlap_count": float(evaluation_validation.overlap_count),
                }
            )
            log_artifacts(
                [
                    history_report_path,
                    evaluation_report_path,
                    history_enriched_path,
                    evaluation_enriched_path,
                ]
            )
    finally:
        if run_context is not None:
            run_context.__exit__(None, None, None)
        if reporter is None:
            active_reporter.close()


@hydra.main(version_base=None, config_path="../conf", config_name="acquire")
def main(cfg: DictConfig) -> None:
    run(coerce_config(cfg, task="acquire"))


if __name__ == "__main__":
    main()
