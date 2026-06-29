from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl

from spice.storage.corpus import load_corpus_manifest


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports" / "evaluation_window_scans"

CHAIN = os.environ["SPICE_SCAN_CHAIN"]
CORPUS_IDS = tuple(
    corpus_id.strip()
    for corpus_id in os.environ["SPICE_SCAN_CORPUS_IDS"].split(",")
    if corpus_id.strip()
)
TRAINING_CUTOFF = os.environ["SPICE_SCAN_TRAINING_CUTOFF"]
OUTPUT_PREFIX = os.environ["SPICE_SCAN_OUTPUT_PREFIX"]
WINDOW_HOURS = tuple(
    int(value.strip())
    for value in os.environ.get("SPICE_SCAN_WINDOW_HOURS", "4,6,8,12,16,24,36,48,72").split(",")
    if value.strip()
)
START_STRIDE_SECONDS = int(os.environ.get("SPICE_SCAN_START_STRIDE_SECONDS", "3600"))
MIN_BLOCK_COVERAGE_FRACTION = float(os.environ.get("SPICE_SCAN_MIN_BLOCK_COVERAGE_FRACTION", "0.80"))
SAMPLES_PER_DURATION_METRIC_QUARTILE = int(
    os.environ.get("SPICE_SCAN_SAMPLES_PER_DURATION_METRIC_QUARTILE", "3")
)

FIELDS = [
    "chain",
    "corpus_id",
    "window_id",
    "start_iso",
    "end_iso",
    "start_ts",
    "duration_seconds",
    "duration_hours",
    "n_blocks",
    "mean_base_fee_gwei",
    "median_base_fee_gwei",
    "p10_base_fee_gwei",
    "p90_base_fee_gwei",
    "fee_range_gwei",
    "base_fee_volatility_log_change_std",
    "mean_gas_utilization",
    "median_fee_percentile_within_duration",
    "volatility_percentile_within_duration",
    "fee_quartile",
    "volatility_quartile",
    "class_tags",
]

SELECTED_FIELDS = FIELDS + [
    "shortlist_class",
    "shortlist_rank",
    "selection_metric",
    "selection_quartile",
    "selection_target_fraction_within_quartile",
]


@dataclass(frozen=True)
class BlockSeries:
    timestamp: np.ndarray
    base_fee_gwei: np.ndarray
    gas_utilization: np.ndarray


def utc_timestamp(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp())


def iso_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def slug_timestamp(value: int) -> str:
    return datetime.fromtimestamp(value, UTC).strftime("%Y%m%dT%H%M%SZ")


def blocks_globs() -> tuple[str, ...]:
    return tuple(
        str(ROOT / "outputs" / "corpora" / CHAIN / corpus_id / "blocks" / "*.parquet")
        for corpus_id in CORPUS_IDS
    )


def nominal_block_time_seconds() -> float:
    manifests = [
        load_corpus_manifest(
            ROOT / "outputs" / "corpora" / CHAIN / corpus_id / ".spice" / "state.sqlite"
        )
        for corpus_id in CORPUS_IDS
    ]
    values = {manifest.chain.runtime.nominal_block_time_seconds for manifest in manifests}
    if len(values) != 1:
        raise ValueError(f"corpora disagree on nominal block time: {sorted(values)}")
    return float(values.pop())


def min_blocks_for_duration(hours: int, nominal_dt: float) -> int:
    expected = hours * 3600.0 / nominal_dt
    return int(np.floor(expected * MIN_BLOCK_COVERAGE_FRACTION))


def load_blocks() -> BlockSeries:
    frame = (
        pl.scan_parquet(blocks_globs())
        .select(
            [
                pl.col("timestamp").cast(pl.Int64),
                (pl.col("base_fee_per_gas").cast(pl.Float64) / 1e9).alias("base_fee_gwei"),
                (pl.col("gas_used").cast(pl.Float64) / pl.col("gas_limit").cast(pl.Float64)).alias(
                    "gas_utilization"
                ),
            ]
        )
        .filter(pl.col("base_fee_gwei") > 0)
        .unique(subset=["timestamp"], keep="first")
        .sort("timestamp")
        .collect()
    )
    return BlockSeries(
        timestamp=frame["timestamp"].to_numpy(),
        base_fee_gwei=frame["base_fee_gwei"].to_numpy(),
        gas_utilization=frame["gas_utilization"].to_numpy(),
    )


def percentile_rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(len(values), dtype=float)
    ranks[order] = (np.arange(len(values), dtype=float) + 1.0) / len(values)
    return ranks


def quartile(percentile: float) -> str:
    if percentile <= 0.25:
        return "q1"
    if percentile <= 0.50:
        return "q2"
    if percentile <= 0.75:
        return "q3"
    return "q4"


def window_metrics(
    blocks: BlockSeries,
    *,
    start: int,
    duration: int,
    left: int,
    right: int,
) -> dict[str, object]:
    end = start + duration
    fees = blocks.base_fee_gwei[left:right]
    log_changes = np.diff(np.log(fees))
    gas_utilization = blocks.gas_utilization[left:right]
    hours = duration / 3600.0
    window_id = f"{CHAIN}_{hours:g}h_{slug_timestamp(start)}"
    return {
        "chain": CHAIN,
        "corpus_id": "+".join(CORPUS_IDS),
        "window_id": window_id,
        "start_iso": iso_timestamp(start),
        "end_iso": iso_timestamp(end),
        "start_ts": start,
        "duration_seconds": duration,
        "duration_hours": hours,
        "n_blocks": int(right - left),
        "mean_base_fee_gwei": float(np.mean(fees)),
        "median_base_fee_gwei": float(np.median(fees)),
        "p10_base_fee_gwei": float(np.quantile(fees, 0.10)),
        "p90_base_fee_gwei": float(np.quantile(fees, 0.90)),
        "fee_range_gwei": float(np.max(fees) - np.min(fees)),
        "base_fee_volatility_log_change_std": float(np.std(log_changes, ddof=1)),
        "mean_gas_utilization": float(np.mean(gas_utilization)),
    }


def raw_windows(blocks: BlockSeries) -> list[dict[str, object]]:
    start_bound = utc_timestamp(TRAINING_CUTOFF)
    end_bound = int(blocks.timestamp[-1])
    nominal_dt = nominal_block_time_seconds()
    rows: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        duration = hours * 3600
        min_blocks = min_blocks_for_duration(hours, nominal_dt)
        for start in range(start_bound, end_bound - duration + 1, START_STRIDE_SECONDS):
            end = start + duration
            left = int(np.searchsorted(blocks.timestamp, start, side="left"))
            right = int(np.searchsorted(blocks.timestamp, end, side="left"))
            if right - left < min_blocks:
                continue
            rows.append(
                window_metrics(blocks, start=start, duration=duration, left=left, right=right)
            )
    return rows


def classify_quartiles(rows: list[dict[str, object]]) -> None:
    for hours in sorted({row["duration_hours"] for row in rows}):
        group = [row for row in rows if row["duration_hours"] == hours]
        median_fees = np.array([float(row["median_base_fee_gwei"]) for row in group])
        volatilities = np.array([float(row["base_fee_volatility_log_change_std"]) for row in group])
        fee_percentiles = percentile_rank(median_fees)
        volatility_percentiles = percentile_rank(volatilities)

        for row, fee_pct, vol_pct in zip(group, fee_percentiles, volatility_percentiles, strict=True):
            fee_q = quartile(float(fee_pct))
            vol_q = quartile(float(vol_pct))
            row["median_fee_percentile_within_duration"] = float(fee_pct)
            row["volatility_percentile_within_duration"] = float(vol_pct)
            row["fee_quartile"] = fee_q
            row["volatility_quartile"] = vol_q
            row["class_tags"] = f"fee_{fee_q};volatility_{vol_q}"


def overlaps(left: dict[str, object], right: dict[str, object]) -> bool:
    left_start = int(left["start_ts"])
    left_end = left_start + int(left["duration_seconds"])
    right_start = int(right["start_ts"])
    right_end = right_start + int(right["duration_seconds"])
    return max(left_start, right_start) < min(left_end, right_end)


def metric_key(metric: str) -> str:
    if metric == "fee":
        return "median_base_fee_gwei"
    if metric == "volatility":
        return "base_fee_volatility_log_change_std"
    raise ValueError(f"unknown metric: {metric}")


def metric_quartile_key(metric: str) -> str:
    if metric == "fee":
        return "fee_quartile"
    if metric == "volatility":
        return "volatility_quartile"
    raise ValueError(f"unknown metric: {metric}")


def evenly_spaced_candidates(
    candidates: list[dict[str, object]],
) -> list[tuple[float, int, dict[str, object]]]:
    total = len(candidates)
    if total == 0:
        return []
    count = min(SAMPLES_PER_DURATION_METRIC_QUARTILE, total)
    targets = [(index + 0.5) / count for index in range(count)]
    resolved: list[tuple[float, int, dict[str, object]]] = []
    for target in targets:
        position = int(round(target * (total - 1)))
        resolved.append((target, position, candidates[position]))
    return resolved


def select_quartile_windows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        duration_rows = [row for row in rows if row["duration_hours"] == hours]
        for metric in ("fee", "volatility"):
            value_key = metric_key(metric)
            quartile_key = metric_quartile_key(metric)
            for q in ("q1", "q2", "q3", "q4"):
                candidates = sorted(
                    [row for row in duration_rows if row[quartile_key] == q],
                    key=lambda row: float(row[value_key]),
                )
                picked_for_group: list[dict[str, object]] = []
                for target, position, _candidate in evenly_spaced_candidates(candidates):
                    indexed_candidates = list(enumerate(candidates))
                    for _index, alternate in sorted(
                        indexed_candidates,
                        key=lambda item: abs(item[0] - position),
                    ):
                        if any(overlaps(alternate, picked) for picked in picked_for_group):
                            continue
                        copy = dict(alternate)
                        copy["shortlist_class"] = f"{metric}_{q}"
                        copy["shortlist_rank"] = len(picked_for_group) + 1
                        copy["selection_metric"] = metric
                        copy["selection_quartile"] = q
                        copy["selection_target_fraction_within_quartile"] = target
                        picked_for_group.append(copy)
                        selected.append(copy)
                        break
    return selected


def merge_selected_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    class_tags: dict[str, list[str]] = {}
    shortlist_classes: dict[str, list[str]] = {}
    for row in rows:
        window_id = str(row["window_id"])
        if window_id not in merged:
            merged[window_id] = dict(row)
            class_tags[window_id] = []
            shortlist_classes[window_id] = []
        for tag in str(row["class_tags"]).split(";"):
            if tag and tag not in class_tags[window_id]:
                class_tags[window_id].append(tag)
        shortlist = str(row.get("shortlist_class", ""))
        if shortlist and shortlist not in shortlist_classes[window_id]:
            shortlist_classes[window_id].append(shortlist)
    for window_id, row in merged.items():
        row["class_tags"] = ";".join(class_tags[window_id])
        row["shortlist_class"] = ";".join(shortlist_classes[window_id])
        row["shortlist_rank"] = ""
        row["selection_metric"] = ""
        row["selection_quartile"] = ""
        row["selection_target_fraction_within_quartile"] = ""
    return list(merged.values())


def quartile_summary(rows: list[dict[str, object]], selected: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        duration_rows = [row for row in rows if row["duration_hours"] == hours]
        selected_rows = [row for row in selected if row["duration_hours"] == hours]
        for metric in ("fee", "volatility"):
            quartile_key = metric_quartile_key(metric)
            for q in ("q1", "q2", "q3", "q4"):
                all_q = [row for row in duration_rows if row[quartile_key] == q]
                selected_q = [
                    row
                    for row in selected_rows
                    if str(row.get("shortlist_class", "")).startswith(f"{metric}_{q}")
                ]
                summary.append(
                    {
                        "duration_hours": hours,
                        "metric": metric,
                        "quartile": q,
                        "candidate_windows": len(all_q),
                        "selected_source_rows": len(selected_q),
                        "selected_unique_windows": len({row["window_id"] for row in selected_q}),
                    }
                )
    return summary


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def print_summary(rows: list[dict[str, object]], selected: list[dict[str, object]], unique: list[dict[str, object]]) -> None:
    print(f"chain={CHAIN} corpora={'+'.join(CORPUS_IDS)} cutoff={TRAINING_CUTOFF}")
    print(f"all_windows={len(rows)} selected_source_rows={len(selected)} unique_windows={len(unique)}")
    for hours in WINDOW_HOURS:
        source_count = sum(1 for row in selected if row["duration_hours"] == hours)
        unique_count = sum(1 for row in unique if row["duration_hours"] == hours)
        print(f"  {hours}h source={source_count} unique={unique_count}")


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = load_blocks()
    rows = raw_windows(blocks)
    classify_quartiles(rows)
    selected = select_quartile_windows(rows)
    unique = merge_selected_rows(selected)
    summary = quartile_summary(rows, selected)

    write_csv(EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_all.csv", rows, FIELDS)
    write_csv(EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_selected_source.csv", selected, SELECTED_FIELDS)
    write_csv(EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_recommended.csv", unique, SELECTED_FIELDS)
    write_csv(
        EXPORT_DIR / f"{OUTPUT_PREFIX}_window_quartile_summary.csv",
        summary,
        [
            "duration_hours",
            "metric",
            "quartile",
            "candidate_windows",
            "selected_source_rows",
            "selected_unique_windows",
        ],
    )
    print_summary(rows, selected, unique)


if __name__ == "__main__":
    main()
