from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import polars as pl


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports" / "evaluation_window_scans"
CORPUS_IDS = tuple(
    corpus_id.strip()
    for corpus_id in os.environ.get(
        "SPICE_PECTRA_SCAN_CORPUS_ID", "cor_2edb8f7b84a4edf95e2b"
    ).split(",")
    if corpus_id.strip()
)
CORPUS_LABEL = "+".join(CORPUS_IDS)
OUTPUT_PREFIX = os.environ.get("SPICE_PECTRA_SCAN_OUTPUT_PREFIX", "ethereum_pectra_edge_case")
BLOCKS_GLOBS = tuple(
    str(ROOT / "outputs" / "corpora" / "ethereum" / corpus_id / "blocks" / "*.parquet")
    for corpus_id in CORPUS_IDS
)

TRAINING_CUTOFF = "2025-12-08T00:00:11Z"
WINDOW_HOURS = (2, 4, 6, 8, 12, 16, 24, 36, 48, 72)
START_STRIDE_SECONDS = 3600
MIN_BLOCKS_PER_HOUR = 250
CLASS_PERCENTILE = 0.10
SHORTLIST_PER_DURATION_CLASS = 6
CURRENT_EVALUATED_WINDOWS = (
    ("eth_vol_cluster_dec_08_09_2025", "2025-12-08T17:00:11Z", 72000),
    ("eth_quiet_low_fee_dec_19_2025", "2025-12-19T20:00:11Z", 129600),
    ("eth_high_fee_feb_05_2026", "2026-02-05T12:00:11Z", 54000),
    ("eth_low_vol_apr_22_2026", "2026-04-22T03:00:11Z", 64800),
    ("eth_low_vol_apr_27_2026", "2026-04-27T06:00:11Z", 57600),
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
    "fee_level_class",
    "fee_level_severity",
    "volatility_class",
    "volatility_severity",
    "class_tags",
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


def load_blocks() -> BlockSeries:
    frame = (
        pl.scan_parquet(BLOCKS_GLOBS)
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


def low_severity(percentile: float) -> str:
    if percentile <= 0.01:
        return "p1"
    if percentile <= 0.05:
        return "p5"
    if percentile <= 0.10:
        return "p10"
    return ""


def high_severity(percentile: float) -> str:
    if percentile >= 0.99:
        return "p99"
    if percentile >= 0.95:
        return "p95"
    if percentile >= 0.90:
        return "p90"
    return ""


def raw_windows(blocks: BlockSeries) -> list[dict[str, object]]:
    start_bound = utc_timestamp(TRAINING_CUTOFF)
    end_bound = int(blocks.timestamp[-1])
    rows: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        duration = hours * 3600
        min_blocks = hours * MIN_BLOCKS_PER_HOUR
        for start in range(start_bound, end_bound - duration + 1, START_STRIDE_SECONDS):
            end = start + duration
            left = np.searchsorted(blocks.timestamp, start, side="left")
            right = np.searchsorted(blocks.timestamp, end, side="left")
            if right - left < min_blocks:
                continue

            fees = blocks.base_fee_gwei[left:right]
            log_changes = np.diff(np.log(fees))
            gas_utilization = blocks.gas_utilization[left:right]
            window_id = f"eth_pectra_{hours:02d}h_{slug_timestamp(start)}"

            rows.append(
                {
                    "chain": "ethereum",
                    "corpus_id": CORPUS_LABEL,
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
            )
    return rows


def raw_windows_for_duration(blocks: BlockSeries, duration: int) -> list[dict[str, object]]:
    start_bound = utc_timestamp(TRAINING_CUTOFF)
    end_bound = int(blocks.timestamp[-1])
    hours = duration / 3600.0
    min_blocks = hours * MIN_BLOCKS_PER_HOUR
    rows: list[dict[str, object]] = []
    for start in range(start_bound, end_bound - duration + 1, START_STRIDE_SECONDS):
        end = start + duration
        left = np.searchsorted(blocks.timestamp, start, side="left")
        right = np.searchsorted(blocks.timestamp, end, side="left")
        if right - left < min_blocks:
            continue
        rows.append(window_metrics(blocks, start, duration, left, right))
    return rows


def window_metrics(
    blocks: BlockSeries,
    start: int,
    duration: int,
    left: int | None = None,
    right: int | None = None,
) -> dict[str, object]:
    end = start + duration
    if left is None:
        left = int(np.searchsorted(blocks.timestamp, start, side="left"))
    if right is None:
        right = int(np.searchsorted(blocks.timestamp, end, side="left"))
    fees = blocks.base_fee_gwei[left:right]
    log_changes = np.diff(np.log(fees))
    gas_utilization = blocks.gas_utilization[left:right]
    hours = duration / 3600.0
    window_id = f"eth_pectra_{hours:g}h_{slug_timestamp(start)}"

    return {
        "chain": "ethereum",
        "corpus_id": CORPUS_LABEL,
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


def classify(rows: list[dict[str, object]]) -> None:
    for hours in sorted({row["duration_hours"] for row in rows}):
        group = [row for row in rows if row["duration_hours"] == hours]
        median_fees = np.array([float(row["median_base_fee_gwei"]) for row in group])
        volatilities = np.array([float(row["base_fee_volatility_log_change_std"]) for row in group])
        fee_percentiles = percentile_rank(median_fees)
        volatility_percentiles = percentile_rank(volatilities)

        for row, fee_pct, vol_pct in zip(group, fee_percentiles, volatility_percentiles, strict=True):
            tags: list[str] = []
            fee_class = ""
            fee_severity = ""
            volatility_class = ""
            volatility_severity = ""

            if fee_pct <= CLASS_PERCENTILE:
                fee_class = "low_base_fee"
                fee_severity = low_severity(fee_pct)
                tags.append(f"{fee_class}:{fee_severity}")
            elif fee_pct >= 1.0 - CLASS_PERCENTILE:
                fee_class = "high_base_fee"
                fee_severity = high_severity(fee_pct)
                tags.append(f"{fee_class}:{fee_severity}")

            if vol_pct <= CLASS_PERCENTILE:
                volatility_class = "low_volatility"
                volatility_severity = low_severity(vol_pct)
                tags.append(f"{volatility_class}:{volatility_severity}")
            elif vol_pct >= 1.0 - CLASS_PERCENTILE:
                volatility_class = "high_volatility"
                volatility_severity = high_severity(vol_pct)
                tags.append(f"{volatility_class}:{volatility_severity}")

            row["median_fee_percentile_within_duration"] = float(fee_pct)
            row["volatility_percentile_within_duration"] = float(vol_pct)
            row["fee_level_class"] = fee_class
            row["fee_level_severity"] = fee_severity
            row["volatility_class"] = volatility_class
            row["volatility_severity"] = volatility_severity
            row["class_tags"] = ";".join(tags)


def class_members(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [row for row in rows if row["class_tags"]]


def class_sort_key(class_name: str):
    if class_name == "low_base_fee":
        return lambda row: float(row["median_base_fee_gwei"])
    if class_name == "high_base_fee":
        return lambda row: -float(row["median_base_fee_gwei"])
    if class_name == "low_volatility":
        return lambda row: float(row["base_fee_volatility_log_change_std"])
    if class_name == "high_volatility":
        return lambda row: -float(row["base_fee_volatility_log_change_std"])
    raise ValueError(f"Unknown class {class_name}")


def in_class(row: dict[str, object], class_name: str) -> bool:
    return row["fee_level_class"] == class_name or row["volatility_class"] == class_name


def overlaps(left: dict[str, object], right: dict[str, object]) -> bool:
    left_start = int(left["start_ts"])
    left_end = left_start + int(left["duration_seconds"])
    right_start = int(right["start_ts"])
    right_end = right_start + int(right["duration_seconds"])
    return max(left_start, right_start) < min(left_end, right_end)


def shortlist(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        duration_rows = [row for row in rows if row["duration_hours"] == hours]
        for class_name in ("low_base_fee", "high_base_fee", "low_volatility", "high_volatility"):
            candidates = sorted(
                [row for row in duration_rows if in_class(row, class_name)],
                key=class_sort_key(class_name),
            )
            picked_for_class: list[dict[str, object]] = []
            for candidate in candidates:
                if any(overlaps(candidate, picked) for picked in picked_for_class):
                    continue
                copy = dict(candidate)
                copy["shortlist_class"] = class_name
                copy["shortlist_rank"] = len(picked_for_class) + 1
                picked_for_class.append(copy)
                selected.append(copy)
                if len(picked_for_class) >= SHORTLIST_PER_DURATION_CLASS:
                    break
    return selected


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def class_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        group = [row for row in rows if row["duration_hours"] == hours]
        for class_name in ("low_base_fee", "high_base_fee", "low_volatility", "high_volatility"):
            class_rows = [row for row in group if in_class(row, class_name)]
            severity_field = (
                "fee_level_severity"
                if class_name in {"low_base_fee", "high_base_fee"}
                else "volatility_severity"
            )
            row = {
                "duration_hours": hours,
                "total_windows": len(group),
                "class_name": class_name,
                "class_windows": len(class_rows),
                "p10_or_p90_windows": sum(1 for item in class_rows if item[severity_field] in {"p10", "p90"}),
                "p5_or_p95_windows": sum(1 for item in class_rows if item[severity_field] in {"p5", "p95"}),
                "p1_or_p99_windows": sum(1 for item in class_rows if item[severity_field] in {"p1", "p99"}),
            }
            summary.append(row)
    return summary


def threshold_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for hours in WINDOW_HOURS:
        group = [row for row in rows if row["duration_hours"] == hours]
        median_fees = np.array([float(row["median_base_fee_gwei"]) for row in group])
        volatilities = np.array([float(row["base_fee_volatility_log_change_std"]) for row in group])
        summary.append(
            {
                "duration_hours": hours,
                "windows": len(group),
                "fee_p1_gwei": float(np.quantile(median_fees, 0.01)),
                "fee_p5_gwei": float(np.quantile(median_fees, 0.05)),
                "fee_p10_gwei": float(np.quantile(median_fees, 0.10)),
                "fee_p90_gwei": float(np.quantile(median_fees, 0.90)),
                "fee_p95_gwei": float(np.quantile(median_fees, 0.95)),
                "fee_p99_gwei": float(np.quantile(median_fees, 0.99)),
                "vol_p1": float(np.quantile(volatilities, 0.01)),
                "vol_p5": float(np.quantile(volatilities, 0.05)),
                "vol_p10": float(np.quantile(volatilities, 0.10)),
                "vol_p90": float(np.quantile(volatilities, 0.90)),
                "vol_p95": float(np.quantile(volatilities, 0.95)),
                "vol_p99": float(np.quantile(volatilities, 0.99)),
            }
        )
    return summary


def classify_exact_row(row: dict[str, object], distribution: list[dict[str, object]]) -> None:
    median_fees = np.array([float(item["median_base_fee_gwei"]) for item in distribution])
    volatilities = np.array([float(item["base_fee_volatility_log_change_std"]) for item in distribution])
    fee_pct = float(np.mean(median_fees <= float(row["median_base_fee_gwei"])))
    vol_pct = float(np.mean(volatilities <= float(row["base_fee_volatility_log_change_std"])))

    tags: list[str] = []
    fee_class = ""
    fee_severity = ""
    volatility_class = ""
    volatility_severity = ""
    if fee_pct <= CLASS_PERCENTILE:
        fee_class = "low_base_fee"
        fee_severity = low_severity(fee_pct)
        tags.append(f"{fee_class}:{fee_severity}")
    elif fee_pct >= 1.0 - CLASS_PERCENTILE:
        fee_class = "high_base_fee"
        fee_severity = high_severity(fee_pct)
        tags.append(f"{fee_class}:{fee_severity}")
    if vol_pct <= CLASS_PERCENTILE:
        volatility_class = "low_volatility"
        volatility_severity = low_severity(vol_pct)
        tags.append(f"{volatility_class}:{volatility_severity}")
    elif vol_pct >= 1.0 - CLASS_PERCENTILE:
        volatility_class = "high_volatility"
        volatility_severity = high_severity(vol_pct)
        tags.append(f"{volatility_class}:{volatility_severity}")

    row["median_fee_percentile_within_duration"] = fee_pct
    row["volatility_percentile_within_duration"] = vol_pct
    row["fee_level_class"] = fee_class
    row["fee_level_severity"] = fee_severity
    row["volatility_class"] = volatility_class
    row["volatility_severity"] = volatility_severity
    row["class_tags"] = ";".join(tags)


def current_evaluated_window_check(blocks: BlockSeries) -> list[dict[str, object]]:
    distributions: dict[int, list[dict[str, object]]] = {}
    checked: list[dict[str, object]] = []
    for evaluation_id, start_iso, duration in CURRENT_EVALUATED_WINDOWS:
        distributions.setdefault(duration, raw_windows_for_duration(blocks, duration))
        start = utc_timestamp(start_iso)
        row = window_metrics(blocks, start, duration)
        row["evaluation_id"] = evaluation_id
        classify_exact_row(row, distributions[duration])
        checked.append(row)
    return checked


def print_summary(rows: list[dict[str, object]], selected: list[dict[str, object]]) -> None:
    print(f"all_windows={len(rows)} class_members={len(class_members(rows))} shortlist={len(selected)}")
    for hours in WINDOW_HOURS:
        group = [row for row in rows if row["duration_hours"] == hours]
        print(f"\n{hours}h windows={len(group)}")
        for class_name in ("low_base_fee", "high_base_fee", "low_volatility", "high_volatility"):
            count = sum(1 for row in group if in_class(row, class_name))
            print(f"  {class_name}: {count}")

    print("\nshortlist examples")
    for class_name in ("low_base_fee", "high_base_fee", "low_volatility", "high_volatility"):
        examples = [row for row in selected if row["shortlist_class"] == class_name][:8]
        print(f"\n{class_name}")
        for row in examples:
            print(
                row["start_iso"],
                f"{row['duration_hours']}h",
                f"median_fee={float(row['median_base_fee_gwei']):.6g}",
                f"vol={float(row['base_fee_volatility_log_change_std']):.5f}",
                row["class_tags"],
            )


def main() -> None:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    blocks = load_blocks()
    rows = raw_windows(blocks)
    classify(rows)
    members = class_members(rows)
    selected = shortlist(members)
    summary = class_summary(rows)
    thresholds = threshold_summary(rows)
    current_check = current_evaluated_window_check(blocks)

    write_csv(EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_all.csv", rows, FIELDS)
    write_csv(EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_class_members.csv", members, FIELDS)
    write_csv(
        EXPORT_DIR / f"{OUTPUT_PREFIX}_windows_recommended.csv",
        selected,
        FIELDS + ["shortlist_class", "shortlist_rank"],
    )
    write_csv(
        EXPORT_DIR / f"{OUTPUT_PREFIX}_window_class_summary.csv",
        summary,
        [
            "duration_hours",
            "total_windows",
            "class_name",
            "class_windows",
            "p10_or_p90_windows",
            "p5_or_p95_windows",
            "p1_or_p99_windows",
        ],
    )
    write_csv(
        EXPORT_DIR / f"{OUTPUT_PREFIX}_window_thresholds.csv",
        thresholds,
        [
            "duration_hours",
            "windows",
            "fee_p1_gwei",
            "fee_p5_gwei",
            "fee_p10_gwei",
            "fee_p90_gwei",
            "fee_p95_gwei",
            "fee_p99_gwei",
            "vol_p1",
            "vol_p5",
            "vol_p10",
            "vol_p90",
            "vol_p95",
            "vol_p99",
        ],
    )
    write_csv(
        EXPORT_DIR / f"{OUTPUT_PREFIX}_current_evaluated_windows_rule_check.csv",
        current_check,
        ["evaluation_id"] + FIELDS,
    )
    print_summary(rows, selected)


if __name__ == "__main__":
    main()
