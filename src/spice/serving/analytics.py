"""SQLite persistence for serving predictions and savings."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .schemas import (
    AnalyticsResponse,
    AnalyticsRow,
    AnalyticsTotals,
    ObserveTransactionResponse,
    PredictionResponse,
)

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class StoredPrediction:
    request_id: str
    baseline_block: int
    target_block: int
    recommended_wait_seconds: int


class ServingAnalyticsStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def record_prediction(self, prediction: PredictionResponse) -> None:
        now = _unix_now()
        with self._connect() as conn:
            conn.execute(
                """
                insert into serving_runs (
                    request_id, schema_version, created_at_unix, updated_at_unix,
                    chain_name, chain_id, artifact_id, observed_block, observed_timestamp,
                    baseline_block, broadcast_after_block, target_block,
                    target_timestamp_estimate, selected_offset, recommended_wait_seconds,
                    expires_at_unix, support_start_block, support_end_block, status
                )
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'predicted')
                """,
                (
                    prediction.request_id,
                    SCHEMA_VERSION,
                    now,
                    now,
                    prediction.chain_name,
                    prediction.chain_id,
                    prediction.artifact_id,
                    prediction.observed_block,
                    prediction.observed_timestamp,
                    prediction.baseline_block,
                    prediction.broadcast_after_block,
                    prediction.target_block,
                    prediction.target_timestamp_estimate,
                    prediction.selected_offset,
                    prediction.recommended_wait_seconds,
                    prediction.expires_at_unix,
                    prediction.support_start_block,
                    prediction.support_end_block,
                ),
            )

    def get_prediction(self, request_id: str) -> StoredPrediction:
        with self._connect() as conn:
            row = conn.execute(
                """
                select request_id, baseline_block, target_block, recommended_wait_seconds
                from serving_runs
                where request_id = ?
                """,
                (request_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown prediction request_id: {request_id}")
        return StoredPrediction(
            request_id=str(row["request_id"]),
            baseline_block=int(row["baseline_block"]),
            target_block=int(row["target_block"]),
            recommended_wait_seconds=int(row["recommended_wait_seconds"]),
        )

    def record_observation(self, observation: ObserveTransactionResponse) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                update serving_runs
                set updated_at_unix = ?,
                    observed_at_unix = ?,
                    status = 'observed',
                    tx_hash = ?,
                    included_block = ?,
                    gas_used = ?,
                    baseline_fee_wei = ?,
                    model_fee_wei = ?,
                    savings_wei = ?,
                    savings_percent = ?
                where request_id = ?
                """,
                (
                    _unix_now(),
                    _unix_now(),
                    observation.tx_hash,
                    observation.included_block,
                    observation.gas_used,
                    observation.baseline_fee_wei,
                    observation.model_fee_wei,
                    observation.savings_wei,
                    observation.savings_percent,
                    observation.request_id,
                ),
            )

    def analytics(self) -> AnalyticsResponse:
        with self._connect() as conn:
            rows = conn.execute(
                """
                select request_id, created_at_unix, tx_hash, recommended_wait_seconds,
                       baseline_block, included_block, baseline_fee_wei, model_fee_wei,
                       savings_wei, savings_percent
                from serving_runs
                order by created_at_unix desc
                limit 100
                """
            ).fetchall()
            observed = conn.execute(
                """
                select baseline_fee_wei, model_fee_wei, savings_wei
                from serving_runs
                where status = 'observed'
                """
            ).fetchall()
        baseline_total = sum(_optional_int(row["baseline_fee_wei"]) for row in observed)
        model_total = sum(_optional_int(row["model_fee_wei"]) for row in observed)
        savings_total = sum(_optional_int(row["savings_wei"]) for row in observed)
        savings_percent = (
            0.0 if baseline_total <= 0 else float(savings_total / baseline_total * 100.0)
        )
        win_count = sum(1 for row in observed if _optional_int(row["savings_wei"]) > 0)
        return AnalyticsResponse(
            totals=AnalyticsTotals(
                run_count=len(observed),
                baseline_fee_total_wei=str(baseline_total),
                model_fee_total_wei=str(model_total),
                savings_total_wei=str(savings_total),
                savings_percent=savings_percent,
                win_count=win_count,
            ),
            rows=[
                AnalyticsRow(
                    request_id=str(row["request_id"]),
                    created_at=_iso_timestamp(int(row["created_at_unix"])),
                    tx_hash=row["tx_hash"],
                    wait_seconds=int(row["recommended_wait_seconds"]),
                    baseline_block=int(row["baseline_block"]),
                    included_block=(
                        None if row["included_block"] is None else int(row["included_block"])
                    ),
                    baseline_fee_wei=row["baseline_fee_wei"],
                    model_fee_wei=row["model_fee_wei"],
                    savings_wei=row["savings_wei"],
                    savings_percent=(
                        None if row["savings_percent"] is None else float(row["savings_percent"])
                    ),
                )
                for row in rows
            ],
        )

    def _ensure_schema(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                create table if not exists serving_runs (
                    request_id text primary key,
                    schema_version integer not null,
                    created_at_unix integer not null,
                    updated_at_unix integer not null,
                    chain_name text not null,
                    chain_id integer not null,
                    artifact_id text not null,
                    observed_block integer not null,
                    observed_timestamp integer not null,
                    baseline_block integer not null,
                    broadcast_after_block integer not null,
                    target_block integer not null,
                    target_timestamp_estimate integer not null,
                    selected_offset integer not null,
                    recommended_wait_seconds integer not null,
                    expires_at_unix integer not null,
                    support_start_block integer not null,
                    support_end_block integer not null,
                    status text not null,
                    error text,
                    tx_hash text,
                    included_block integer,
                    gas_used text,
                    baseline_fee_wei text,
                    model_fee_wei text,
                    savings_wei text,
                    savings_percent real,
                    observed_at_unix integer
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn


def _unix_now() -> int:
    return int(datetime.now(tz=UTC).timestamp())


def _iso_timestamp(unix_timestamp: int) -> str:
    return datetime.fromtimestamp(unix_timestamp, tz=UTC).isoformat()


def _optional_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"expected optional integer value, got {type(value).__name__}")
