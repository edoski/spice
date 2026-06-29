from __future__ import annotations

import csv
import json
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from scipy.stats import t


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
EVALS_CSV = EXPORT_DIR / "edge_case_baseline_36s_evals_merged.csv"
FEE_STATS_CSV = EXPORT_DIR / "ethereum_pectra_edge_case_fee_scatter_summary.csv"

SELECTED_WINDOWS = (
    "eth_vol_cluster_dec_08_09_2025",
    "eth_quiet_low_fee_dec_19_2025",
    "eth_high_fee_feb_05_2026",
    "eth_low_vol_apr_22_2026",
    "eth_low_vol_apr_27_2026",
)

REGIME_CLASS = {
    "eth_vol_cluster_dec_08_09_2025": "high_volatility",
    "eth_quiet_low_fee_dec_19_2025": "low_fee_level",
    "eth_high_fee_feb_05_2026": "high_fee_level",
    "eth_low_vol_apr_22_2026": "low_volatility_high_fee",
    "eth_low_vol_apr_27_2026": "low_volatility",
}

TAG_CLASSES = {
    "eth_vol_cluster_dec_08_09_2025": ("high_volatility", "sustained"),
    "eth_quiet_low_fee_dec_19_2025": ("low_fee_level", "extended"),
    "eth_high_fee_feb_05_2026": ("high_fee_level", "regime_shift"),
    "eth_low_vol_apr_22_2026": ("low_volatility", "high_fee_level"),
    "eth_low_vol_apr_27_2026": ("low_volatility",),
}


@dataclass(frozen=True)
class EvalRunRecord:
    evaluation_id: str
    window_start: str
    duration_seconds: int
    model: str
    artifact_id: str
    corpus_id: str
    evaluation_storage_id: str
    plotted_profit_percent: float
    run_profit_percent: float


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((value - m) ** 2 for value in values) / (len(values) - 1))


def ci95(values: list[float]) -> dict[str, float | int]:
    n = len(values)
    m = mean(values)
    std = sample_std(values)
    se = std / math.sqrt(n) if n else math.nan
    critical = float(t.ppf(0.975, n - 1)) if n > 1 else math.nan
    half_width = critical * se if n > 1 else math.nan
    return {
        "n": n,
        "mean_profit_percent": m,
        "std_profit_percent": std,
        "se_profit_percent": se,
        "ci95_low_percent": m - half_width,
        "ci95_high_percent": m + half_width,
        "ci95_half_width_percent": half_width,
    }


def read_fee_stats() -> dict[str, dict[str, str]]:
    stats: dict[str, dict[str, str]] = {}
    with FEE_STATS_CSV.open(newline="") as handle:
        for row in csv.DictReader(handle):
            stats.setdefault(row["evaluation_id"], row)
    return stats


def read_eval_rows() -> list[dict[str, str]]:
    with EVALS_CSV.open(newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row["chain"] == "ethereum" and row["evaluation_id"] in SELECTED_WINDOWS
        ]


def evaluation_runs(row: dict[str, str]) -> list[EvalRunRecord]:
    db_path = (
        ROOT
        / "outputs"
        / "artifacts"
        / "ethereum"
        / row["artifact_id"]
        / ".spice"
        / "state.sqlite"
    )
    with sqlite3.connect(db_path) as conn:
        payload_row = conn.execute(
            "select payload from evaluation_summary where evaluation_id = ?",
            (row["evaluation_storage_id"],),
        ).fetchone()
    if payload_row is None:
        raise RuntimeError(
            f"Missing evaluation summary {row['evaluation_storage_id']} for {row['artifact_id']}"
        )
    payload = json.loads(payload_row[0])
    return [
        EvalRunRecord(
            evaluation_id=row["evaluation_id"],
            window_start=row["window_start"],
            duration_seconds=int(row["duration_seconds"]),
            model=row["model"],
            artifact_id=row["artifact_id"],
            corpus_id=row["corpus_id"],
            evaluation_storage_id=row["evaluation_storage_id"],
            plotted_profit_percent=float(row["profit_over_baseline"]) * 100.0,
            run_profit_percent=float(run["metrics"]["profit_over_baseline"]) * 100.0,
        )
        for run in payload["runs"]
    ]


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def add_fee_columns(row: dict[str, object], fee_stats: dict[str, dict[str, str]], window_id: str) -> None:
    stats = fee_stats[window_id]
    row.update(
        {
            "base_fee_mean_gwei": float(stats["base_fee_mean_gwei"]),
            "base_fee_median_gwei": float(stats["base_fee_median_gwei"]),
            "base_fee_volatility_log_change_std": float(
                stats["base_fee_volatility_log_change_std"]
            ),
            "blocks": int(float(stats["blocks"])),
        }
    )


def summarize() -> None:
    fee_stats = read_fee_stats()
    eval_rows = read_eval_rows()
    records = [record for row in eval_rows for record in evaluation_runs(row)]

    by_model_window: list[dict[str, object]] = []
    grouped_model_window: dict[tuple[str, str], list[EvalRunRecord]] = defaultdict(list)
    for record in records:
        grouped_model_window[(record.evaluation_id, record.model)].append(record)

    for (window_id, model), group in sorted(grouped_model_window.items()):
        first = group[0]
        row: dict[str, object] = {
            "evaluation_id": window_id,
            "regime_class": REGIME_CLASS[window_id],
            "window_start": first.window_start,
            "duration_seconds": first.duration_seconds,
            "model": model,
            "artifact_id": first.artifact_id,
            "corpus_id": first.corpus_id,
            "evaluation_storage_id": first.evaluation_storage_id,
            "plotted_profit_percent": first.plotted_profit_percent,
            **ci95([record.run_profit_percent for record in group]),
        }
        add_fee_columns(row, fee_stats, window_id)
        by_model_window.append(row)

    by_window: list[dict[str, object]] = []
    grouped_window: dict[str, list[EvalRunRecord]] = defaultdict(list)
    for record in records:
        grouped_window[record.evaluation_id].append(record)

    for window_id, group in sorted(grouped_window.items()):
        first = group[0]
        plotted_values = {
            (record.model, record.artifact_id, record.evaluation_storage_id): record.plotted_profit_percent
            for record in group
        }
        row = {
            "evaluation_id": window_id,
            "regime_class": REGIME_CLASS[window_id],
            "window_start": first.window_start,
            "duration_seconds": first.duration_seconds,
            "models": ",".join(sorted({record.model for record in group})),
            "model_count": len({record.model for record in group}),
            "mean_plotted_profit_percent": mean(list(plotted_values.values())),
            **ci95([record.run_profit_percent for record in group]),
        }
        add_fee_columns(row, fee_stats, window_id)
        by_window.append(row)

    class_rows: list[dict[str, object]] = []
    class_groups: dict[tuple[str, str], list[EvalRunRecord]] = defaultdict(list)
    for record in records:
        class_groups[("regime", REGIME_CLASS[record.evaluation_id])].append(record)
        for tag in TAG_CLASSES[record.evaluation_id]:
            class_groups[("tag", tag)].append(record)
        class_groups[("consolidated", "selected_pectra_edge_cases")].append(record)

    for (class_kind, class_name), group in sorted(class_groups.items()):
        windows = sorted({record.evaluation_id for record in group})
        models = sorted({record.model for record in group})
        row = {
            "class_kind": class_kind,
            "class_name": class_name,
            "evaluation_ids": ",".join(windows),
            "window_count": len(windows),
            "models": ",".join(models),
            "model_count": len(models),
            **ci95([record.run_profit_percent for record in group]),
        }
        class_rows.append(row)

    write_rows(
        EXPORT_DIR / "ethereum_pectra_edge_case_ci_by_model_window.csv",
        list(by_model_window[0]),
        by_model_window,
    )
    write_rows(
        EXPORT_DIR / "ethereum_pectra_edge_case_ci_by_window.csv",
        list(by_window[0]),
        by_window,
    )
    write_rows(
        EXPORT_DIR / "ethereum_pectra_edge_case_ci_by_class.csv",
        list(class_rows[0]),
        class_rows,
    )


if __name__ == "__main__":
    summarize()
