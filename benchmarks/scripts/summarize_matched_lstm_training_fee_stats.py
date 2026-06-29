from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "benchmarks" / "exports" / "matched_lstm_36s_training_fee_stats.csv"


@dataclass(frozen=True)
class TrainingSource:
    label: str
    chain: str
    corpus_id: str
    cutoff_iso: str
    reference: str


SOURCES = (
    TrainingSource(
        label="ethereum_pectra_lstm_reference",
        chain="ethereum",
        corpus_id="cor_2edb8f7b84a4edf95e2b",
        cutoff_iso="2025-12-08T00:00:11Z",
        reference="completed artifact art_428e9ef4dda2748668ba",
    ),
    TrainingSource(
        label="polygon_bhilai_lstm_1p53m_target",
        chain="polygon",
        corpus_id="cor_61fb33e47c948a9cebd0",
        cutoff_iso="2025-08-09T01:41:10Z",
        reference="submitted artifact art_699ec8cf57ce7926d5cc",
    ),
    TrainingSource(
        label="avalanche_octane_lstm_1p53m_target",
        chain="avalanche",
        corpus_id="cor_3ef359c91addcab77e9f",
        cutoff_iso="2025-05-04T15:00:52Z",
        reference="submitted artifact art_151d4c9012a282d7a333",
    ),
)

FIELDS = [
    "label",
    "chain",
    "corpus_id",
    "reference",
    "scope",
    "cutoff_iso",
    "row_count",
    "first_timestamp_iso",
    "last_timestamp_iso",
    "mean_base_fee_gwei",
    "median_base_fee_gwei",
    "std_base_fee_gwei",
    "variance_base_fee_gwei",
    "p1_base_fee_gwei",
    "p5_base_fee_gwei",
    "p10_base_fee_gwei",
    "p90_base_fee_gwei",
    "p95_base_fee_gwei",
    "p99_base_fee_gwei",
    "base_fee_volatility_log_change_std",
    "mean_gas_utilization",
]


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def iso_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_training_rows(source: TrainingSource) -> pl.DataFrame:
    cutoff = utc_timestamp(source.cutoff_iso)
    glob = ROOT / "outputs" / "corpora" / source.chain / source.corpus_id / "blocks" / "*.parquet"
    return (
        pl.scan_parquet(str(glob))
        .select(
            [
                pl.col("timestamp").cast(pl.Int64),
                (pl.col("base_fee_per_gas").cast(pl.Float64) / 1e9).alias("base_fee_gwei"),
                (pl.col("gas_used").cast(pl.Float64) / pl.col("gas_limit").cast(pl.Float64)).alias(
                    "gas_utilization"
                ),
            ]
        )
        .filter((pl.col("timestamp") < cutoff) & (pl.col("base_fee_gwei") > 0))
        .sort("timestamp")
        .collect()
    )


def stats_row(
    source: TrainingSource,
    *,
    scope: str,
    frame: pl.DataFrame,
) -> dict[str, object]:
    fees = frame["base_fee_gwei"].to_numpy()
    timestamps = frame["timestamp"].to_numpy()
    gas_utilization = frame["gas_utilization"].to_numpy()
    log_changes = np.diff(np.log(fees))
    return {
        "label": source.label,
        "chain": source.chain,
        "corpus_id": source.corpus_id,
        "reference": source.reference,
        "scope": scope,
        "cutoff_iso": source.cutoff_iso,
        "row_count": int(frame.height),
        "first_timestamp_iso": iso_timestamp(int(timestamps[0])),
        "last_timestamp_iso": iso_timestamp(int(timestamps[-1])),
        "mean_base_fee_gwei": float(np.mean(fees)),
        "median_base_fee_gwei": float(np.median(fees)),
        "std_base_fee_gwei": float(np.std(fees, ddof=1)),
        "variance_base_fee_gwei": float(np.var(fees, ddof=1)),
        "p1_base_fee_gwei": float(np.quantile(fees, 0.01)),
        "p5_base_fee_gwei": float(np.quantile(fees, 0.05)),
        "p10_base_fee_gwei": float(np.quantile(fees, 0.10)),
        "p90_base_fee_gwei": float(np.quantile(fees, 0.90)),
        "p95_base_fee_gwei": float(np.quantile(fees, 0.95)),
        "p99_base_fee_gwei": float(np.quantile(fees, 0.99)),
        "base_fee_volatility_log_change_std": float(np.std(log_changes, ddof=1)),
        "mean_gas_utilization": float(np.mean(gas_utilization)),
    }


def source_rows(source: TrainingSource) -> list[dict[str, object]]:
    frame = load_training_rows(source)
    train_end = max(1, int(frame.height * 0.8))
    return [
        stats_row(source, scope="pre_cutoff_rows", frame=frame),
        stats_row(source, scope="approx_chronological_train_80pct", frame=frame[:train_end]),
    ]


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for source in SOURCES:
        rows.extend(source_rows(source))
    with OUTPUT.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUTPUT} rows={len(rows)}")


if __name__ == "__main__":
    main()
