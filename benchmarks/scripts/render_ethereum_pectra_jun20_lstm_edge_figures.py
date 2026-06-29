from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
FIGURE_DIR = ROOT / "benchmarks" / "figures"
OBSIDIAN_FIGURE_DIR = (
    Path("/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures")
)
COLLECTION_PATH = (
    ROOT
    / "outputs"
    / "benchmarks"
    / "runs"
    / "ethereum_pectra_jun20_edge_case_lstm_36s"
    / "20260620T161342Z_4h_plus_completed"
    / "collection.json"
)
SCAN_PATH = (
    EXPORT_DIR
    / "evaluation_window_scans"
    / "ethereum_pectra_jun20_edge_case_windows_recommended.csv"
)
WINDOW_ID_RE = re.compile(r"\.evaluations-(?P<window_id>eth_pectra_[^.]+)\.")

POINT_COLORS = {
    "low": "#2468A8",
    "middle": "#6B7280",
    "high": "#B44E33",
}

BASE_FEE_TICKS = [0.02, 0.03, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10]


def read_scan_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    with SCAN_PATH.open(newline="") as handle:
        for row in csv.DictReader(handle):
            rows.setdefault(row["window_id"], row)
    return rows


def metric_value(metrics: list[dict[str, object]], metric_id: str) -> float:
    for metric in metrics:
        if metric["metric_id"] == metric_id:
            return float(metric["value"])
    raise KeyError(metric_id)


def window_metric_summary(
    window_metrics: list[dict[str, object]],
    metric_id: str,
) -> tuple[float, float]:
    for metric in window_metrics:
        if metric["metric_id"] == metric_id:
            return float(metric["mean"]), float(metric["std"])
    raise KeyError(metric_id)


def record_window_id(run_id: str) -> str:
    match = WINDOW_ID_RE.search(run_id)
    if match is None:
        raise ValueError(f"cannot parse window id from run id: {run_id}")
    return match.group("window_id")


def joined_rows() -> list[dict[str, object]]:
    scan = read_scan_rows()
    collection = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for record in collection["records"]:
        window_id = record_window_id(str(record["run_id"]))
        scan_row = scan[window_id]
        metrics = record["metrics"]
        profit_mean, profit_std = window_metric_summary(
            record["window_metrics"],
            "profit_over_baseline",
        )
        hit_mean, hit_std = window_metric_summary(
            record["window_metrics"],
            "exact_optimum_hit_rate",
        )
        repetitions = 50
        rows.append(
            {
                "window_id": window_id,
                "run_id": record["run_id"],
                "start_iso": scan_row["start_iso"],
                "end_iso": scan_row["end_iso"],
                "duration_hours": float(scan_row["duration_hours"]),
                "n_blocks": int(scan_row["n_blocks"]),
                "mean_base_fee_gwei": float(scan_row["mean_base_fee_gwei"]),
                "median_base_fee_gwei": float(scan_row["median_base_fee_gwei"]),
                "base_fee_volatility_log_change_std": float(
                    scan_row["base_fee_volatility_log_change_std"]
                ),
                "mean_gas_utilization": float(scan_row["mean_gas_utilization"]),
                "median_fee_percentile_within_duration": float(
                    scan_row["median_fee_percentile_within_duration"]
                )
                * 100.0,
                "volatility_percentile_within_duration": float(
                    scan_row["volatility_percentile_within_duration"]
                )
                * 100.0,
                "fee_level_class": scan_row["fee_level_class"] or "middle_fee",
                "fee_level_severity": scan_row["fee_level_severity"],
                "volatility_class": scan_row["volatility_class"] or "middle_volatility",
                "volatility_severity": scan_row["volatility_severity"],
                "class_tags": scan_row["class_tags"],
                "shortlist_class": scan_row["shortlist_class"],
                "profit_over_baseline": metric_value(metrics, "profit_over_baseline"),
                "profit_over_baseline_window_mean": profit_mean,
                "profit_over_baseline_window_std": profit_std,
                "profit_over_baseline_ci95_half_width": 1.96
                * profit_std
                / math.sqrt(repetitions),
                "cost_over_optimum": metric_value(metrics, "cost_over_optimum"),
                "baseline_cost_over_optimum": metric_value(
                    metrics, "baseline_cost_over_optimum"
                ),
                "exact_optimum_hit_rate": metric_value(metrics, "exact_optimum_hit_rate"),
                "exact_optimum_hit_rate_window_mean": hit_mean,
                "exact_optimum_hit_rate_window_std": hit_std,
                "exact_optimum_hit_rate_ci95_half_width": 1.96
                * hit_std
                / math.sqrt(repetitions),
                "sample_count": int(record["sample_count"]),
                "total_events": int(record["total_events"]),
            }
        )
    return sorted(rows, key=lambda row: (float(row["duration_hours"]), str(row["start_iso"])))


def write_joined_csv(rows: list[dict[str, object]]) -> Path:
    out = EXPORT_DIR / "ethereum_pectra_jun20_edge_case_lstm_36s_4h_plus_joined.csv"
    fields = list(rows[0])
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return out


def ci95(values: list[float]) -> tuple[float, float]:
    if len(values) <= 1:
        return (0.0, 0.0)
    mean = float(np.mean(values))
    sem = float(np.std(values, ddof=1) / math.sqrt(len(values)))
    half = 1.96 * sem
    return mean - half, mean + half


def write_summary_csv(rows: list[dict[str, object]]) -> Path:
    out = EXPORT_DIR / "ethereum_pectra_jun20_edge_case_lstm_36s_4h_plus_summary.csv"
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        for tag in str(row["class_tags"]).split(";"):
            if tag:
                groups[tag.split(":", 1)[0]].append(row)
    groups["consolidated"] = rows

    fields = [
        "class",
        "windows",
        "mean_profit_percent",
        "ci95_low_percent",
        "ci95_high_percent",
        "mean_base_fee_gwei",
        "mean_volatility_log_change_std",
        "mean_sample_count",
        "mean_total_events",
    ]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for class_name in (
            "low_base_fee",
            "high_base_fee",
            "low_volatility",
            "high_volatility",
            "consolidated",
        ):
            class_rows = groups[class_name]
            profits = [float(row["profit_over_baseline"]) * 100.0 for row in class_rows]
            low, high = ci95(profits)
            writer.writerow(
                {
                    "class": class_name,
                    "windows": len(class_rows),
                    "mean_profit_percent": float(np.mean(profits)),
                    "ci95_low_percent": low,
                    "ci95_high_percent": high,
                    "mean_base_fee_gwei": float(
                        np.mean([float(row["mean_base_fee_gwei"]) for row in class_rows])
                    ),
                    "mean_volatility_log_change_std": float(
                        np.mean(
                            [
                                float(row["base_fee_volatility_log_change_std"])
                                for row in class_rows
                            ]
                        )
                    ),
                    "mean_sample_count": float(
                        np.mean([int(row["sample_count"]) for row in class_rows])
                    ),
                    "mean_total_events": float(
                        np.mean([int(row["total_events"]) for row in class_rows])
                    ),
                }
            )
    return out


def rc_params() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 12,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "axes.edgecolor": "#3A3A3A",
            "axes.linewidth": 0.8,
            "figure.facecolor": "#F7F5F0",
            "savefig.facecolor": "#F7F5F0",
        }
    )


def y_limits(values: list[float]) -> tuple[float, float]:
    low = min(values)
    high = max(values)
    pad = max((high - low) * 0.14, 0.1)
    return low - pad, high + pad


def raw_axis_classes(values: list[float]) -> tuple[list[str], dict[str, float]]:
    p1, p5, p10, p90, p95, p99 = np.percentile(values, [1, 5, 10, 90, 95, 99])
    classes = [
        "low" if value <= p10 else "high" if value >= p90 else "middle"
        for value in values
    ]
    thresholds = {
        "p1": float(p1),
        "p5": float(p5),
        "p10": float(p10),
        "p90": float(p90),
        "p95": float(p95),
        "p99": float(p99),
    }
    return classes, thresholds


def add_raw_axis_bands(
    ax,
    *,
    thresholds: dict[str, float],
    log_scale: bool,
) -> None:
    x_min, x_max = ax.get_xlim()
    ax.axvspan(x_min, thresholds["p10"], color="#6BAED6", alpha=0.10, zorder=0)
    ax.axvspan(x_min, thresholds["p5"], color="#6BAED6", alpha=0.08, zorder=0)
    ax.axvspan(x_min, thresholds["p1"], color="#6BAED6", alpha=0.08, zorder=0)
    ax.axvspan(thresholds["p90"], x_max, color="#E07A5F", alpha=0.10, zorder=0)
    ax.axvspan(thresholds["p95"], x_max, color="#E07A5F", alpha=0.08, zorder=0)
    ax.axvspan(thresholds["p99"], x_max, color="#E07A5F", alpha=0.08, zorder=0)
    ax.axvline(
        thresholds["p10"],
        color="#2468A8",
        linewidth=0.8,
        alpha=0.75,
        linestyle="--",
        zorder=5,
    )
    ax.axvline(
        thresholds["p90"],
        color="#B44E33",
        linewidth=0.8,
        alpha=0.75,
        linestyle="--",
        zorder=5,
    )
    ax.set_xlim(x_min, x_max)


def scatter_plot(
    rows: list[dict[str, object]],
    *,
    x_key: str,
    y_key: str,
    y_ci_key: str,
    y_label: str,
    title_metric: str,
    filename: str,
) -> None:
    rc_params()
    fig, ax = plt.subplots(figsize=(9.2, 5.45))
    ax.set_facecolor("#F5F7F2")
    ax.grid(True, color="#FFFFFF", linewidth=0.95)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.7)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.6)

    xs = [float(row[x_key]) for row in rows]
    ys = [float(row[y_key]) * 100.0 for row in rows]
    yerr = [float(row[y_ci_key]) * 100.0 for row in rows]
    sizes = [28.0 for _ in rows]
    classes, thresholds = raw_axis_classes(xs)
    colors = [POINT_COLORS[class_name] for class_name in classes]

    if x_key == "median_base_fee_gwei":
        low_label = "≤p10 fee"
        high_label = "≥p90 fee"
        legend_labels = ("≤p10 fee", "p10-p90 fee", "≥p90 fee")
        ax.set_xscale("log")
        ax.set_xlim(0.018, 11.0)
        ax.xaxis.set_major_locator(mticker.FixedLocator(BASE_FEE_TICKS))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{value:g}"))
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_xlabel("Median base fee during evaluation window (gwei; log scale)")
        title = f"Ethereum Pectra LSTM: {title_metric} vs median base-fee level"
        log_scale = True
    else:
        low_label = "≤p10 volatility"
        high_label = "≥p90 volatility"
        legend_labels = ("≤p10 volatility", "p10-p90 volatility", "≥p90 volatility")
        ax.set_xlabel("Base-fee volatility (std. dev. of block-to-block log changes)")
        title = f"Ethereum Pectra LSTM: {title_metric} vs base-fee volatility"
        log_scale = False

    ax.errorbar(
        xs,
        ys,
        yerr=yerr,
        fmt="none",
        ecolor="#4B5563",
        elinewidth=0.45,
        capsize=1.0,
        alpha=0.18,
        zorder=2,
    )
    ax.scatter(
        xs,
        ys,
        c=colors,
        s=sizes,
        edgecolors="#222222",
        linewidths=0.35,
        alpha=0.70,
        zorder=3,
    )
    ax.set_ylabel(y_label)
    ax.set_title(title, loc="left", pad=12, fontweight="bold")
    ax.set_ylim(*y_limits(ys))
    if x_key != "median_base_fee_gwei":
        ax.margins(x=0.08)
    add_raw_axis_bands(
        ax,
        thresholds=thresholds,
        log_scale=log_scale,
    )

    handles = [
        plt.Line2D([], [], marker="o", linestyle="", color=POINT_COLORS["low"], label=legend_labels[0]),
        plt.Line2D([], [], marker="o", linestyle="", color=POINT_COLORS["middle"], label=legend_labels[1]),
        plt.Line2D([], [], marker="o", linestyle="", color=POINT_COLORS["high"], label=legend_labels[2]),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=3,
        frameon=False,
        bbox_to_anchor=(0.5, 0.035),
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.88, bottom=0.22)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".pdf", ".svg"):
        fig.savefig(FIGURE_DIR / f"{filename}{suffix}", bbox_inches="tight")
    fig.savefig(OBSIDIAN_FIGURE_DIR / f"{filename}.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = joined_rows()
    joined = write_joined_csv(rows)
    summary = write_summary_csv(rows)
    scatter_plot(
        rows,
        x_key="median_base_fee_gwei",
        y_key="profit_over_baseline",
        y_ci_key="profit_over_baseline_ci95_half_width",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename="ethereum_pectra_jun20_lstm_profit_vs_base_fee",
    )
    scatter_plot(
        rows,
        x_key="base_fee_volatility_log_change_std",
        y_key="profit_over_baseline",
        y_ci_key="profit_over_baseline_ci95_half_width",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename="ethereum_pectra_jun20_lstm_profit_vs_base_fee_volatility",
    )
    scatter_plot(
        rows,
        x_key="median_base_fee_gwei",
        y_key="exact_optimum_hit_rate",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename="ethereum_pectra_jun20_lstm_accuracy_vs_base_fee",
    )
    scatter_plot(
        rows,
        x_key="base_fee_volatility_log_change_std",
        y_key="exact_optimum_hit_rate",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename="ethereum_pectra_jun20_lstm_accuracy_vs_base_fee_volatility",
    )
    print(f"rows={len(rows)}")
    print(f"joined={joined}")
    print(f"summary={summary}")
    print(f"figures={FIGURE_DIR}")
    print(f"obsidian={OBSIDIAN_FIGURE_DIR}")


if __name__ == "__main__":
    main()
