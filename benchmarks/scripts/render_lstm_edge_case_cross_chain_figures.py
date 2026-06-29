from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
SCAN_DIR = EXPORT_DIR / "evaluation_window_scans"
FIGURE_DIR = ROOT / "benchmarks" / "figures"
OBSIDIAN_FIGURE_DIR = Path("/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures")

LARGE_COLLECTION_PATH = (
    ROOT
    / "outputs"
    / "benchmarks"
    / "runs"
    / "lstm_36s_large_polygon_avalanche_edge_eval"
    / "20260622T091628Z"
    / "collection.json"
)
ETHEREUM_JOINED_PATH = EXPORT_DIR / "ethereum_pectra_jun20_edge_case_lstm_36s_4h_plus_joined.csv"


POINT_COLORS = {
    "low": "#2468A8",
    "middle": "#6B7280",
    "high": "#B44E33",
}
CHAIN_COLORS = {
    "ethereum": "#4F6F52",
    "polygon": "#6D5BD0",
    "avalanche": "#C2413D",
}
CHAIN_LABELS = {
    "ethereum": "Ethereum Pectra",
    "polygon": "Polygon Bhilai",
    "avalanche": "Avalanche Octane",
}
SCAN_FILES = {
    "polygon": SCAN_DIR / "polygon_bhilai_large_lstm_edge_case_windows_recommended.csv",
    "avalanche": SCAN_DIR / "avalanche_octane_large_lstm_edge_case_windows_recommended.csv",
}


@dataclass(frozen=True)
class ChainInput:
    chain: str
    joined_csv: Path
    figure_prefix: str


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


def read_scan_rows(path: Path) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    shortlist_classes: dict[str, list[str]] = defaultdict(list)
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            window_id = row["window_id"]
            rows.setdefault(window_id, row)
            if row.get("shortlist_class"):
                shortlist_classes[window_id].append(row["shortlist_class"])
    for window_id, classes in shortlist_classes.items():
        rows[window_id]["shortlist_class"] = ";".join(dict.fromkeys(classes))
    return rows


def joined_rows_from_collection(chain: str, scan_path: Path) -> list[dict[str, object]]:
    scan = read_scan_rows(scan_path)
    collection = json.loads(LARGE_COLLECTION_PATH.read_text(encoding="utf-8"))
    rows: list[dict[str, object]] = []
    for record in collection["records"]:
        if record["chain_name"] != chain:
            continue
        window_id = record["dimension_labels"]["evaluations"]
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
                "chain": chain,
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
                    metrics,
                    "baseline_cost_over_optimum",
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


def read_joined_csv(path: Path, chain: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            converted: dict[str, object] = {"chain": chain}
            for key, value in row.items():
                if key in {
                    "duration_hours",
                    "mean_base_fee_gwei",
                    "median_base_fee_gwei",
                    "base_fee_volatility_log_change_std",
                    "mean_gas_utilization",
                    "median_fee_percentile_within_duration",
                    "volatility_percentile_within_duration",
                    "profit_over_baseline",
                    "profit_over_baseline_window_mean",
                    "profit_over_baseline_window_std",
                    "profit_over_baseline_ci95_half_width",
                    "cost_over_optimum",
                    "baseline_cost_over_optimum",
                    "exact_optimum_hit_rate",
                    "exact_optimum_hit_rate_window_mean",
                    "exact_optimum_hit_rate_window_std",
                    "exact_optimum_hit_rate_ci95_half_width",
                }:
                    converted[key] = float(value)
                elif key in {"n_blocks", "sample_count", "total_events"}:
                    converted[key] = int(value)
                else:
                    converted[key] = value
            rows.append(converted)
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def ci95(values: list[float]) -> tuple[float, float, float]:
    if len(values) <= 1:
        mean = float(np.mean(values)) if values else 0.0
        return mean, mean, mean
    mean = float(np.mean(values))
    sem = float(np.std(values, ddof=1) / math.sqrt(len(values)))
    half = 1.96 * sem
    return mean, mean - half, mean + half


def summary_rows(rows_by_chain: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    all_rows = [row for rows in rows_by_chain.values() for row in rows]
    grouped_inputs = {**rows_by_chain, "all_chains": all_rows}
    class_order = (
        "low_base_fee",
        "high_base_fee",
        "low_volatility",
        "high_volatility",
        "consolidated",
    )
    for chain, rows in grouped_inputs.items():
        groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in rows:
            for tag in str(row["class_tags"]).split(";"):
                if tag:
                    groups[tag.split(":", 1)[0]].append(row)
        groups["consolidated"] = rows
        for class_name in class_order:
            class_rows = groups[class_name]
            profits = [float(row["profit_over_baseline"]) * 100.0 for row in class_rows]
            accuracies = [float(row["exact_optimum_hit_rate"]) * 100.0 for row in class_rows]
            profit_mean, profit_low, profit_high = ci95(profits)
            acc_mean, acc_low, acc_high = ci95(accuracies)
            summary.append(
                {
                    "chain": chain,
                    "class": class_name,
                    "windows": len(class_rows),
                    "mean_profit_percent": profit_mean,
                    "ci95_profit_low_percent": profit_low,
                    "ci95_profit_high_percent": profit_high,
                    "mean_exact_optimum_hit_rate_percent": acc_mean,
                    "ci95_accuracy_low_percent": acc_low,
                    "ci95_accuracy_high_percent": acc_high,
                    "mean_median_base_fee_gwei": float(
                        np.mean([float(row["median_base_fee_gwei"]) for row in class_rows])
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
    return summary


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


def y_limits(values: list[float], *, floor_zero: bool = False) -> tuple[float, float]:
    low = min(values)
    high = max(values)
    pad = max((high - low) * 0.14, 0.1)
    y_low = low - pad
    if floor_zero:
        y_low = max(0.0, y_low)
    return y_low, high + pad


def raw_axis_classes(values: list[float]) -> tuple[list[str], dict[str, float]]:
    p1, p5, p10, p90, p95, p99 = np.percentile(values, [1, 5, 10, 90, 95, 99])
    classes = [
        "low" if value <= p10 else "high" if value >= p90 else "middle"
        for value in values
    ]
    return classes, {
        "p1": float(p1),
        "p5": float(p5),
        "p10": float(p10),
        "p90": float(p90),
        "p95": float(p95),
        "p99": float(p99),
    }


def log_xlim(values: list[float]) -> tuple[float, float]:
    low = min(value for value in values if value > 0)
    high = max(values)
    log_low = math.log10(low)
    log_high = math.log10(high)
    pad = max((log_high - log_low) * 0.045, 0.08)
    return 10 ** (log_low - pad), 10 ** (log_high + pad)


def log_ticks(values: list[float]) -> list[float]:
    low, high = log_xlim(values)
    start = math.floor(math.log10(low))
    stop = math.ceil(math.log10(high))
    decades = stop - start + 1
    multiples = (1, 2, 5) if decades <= 7 else (1,)
    ticks = [
        multiple * (10**power)
        for power in range(start, stop + 1)
        for multiple in multiples
        if low <= multiple * (10**power) <= high
    ]
    return ticks


def format_tick(value: float, _: int) -> str:
    if value == 0:
        return "0"
    if 0.001 <= abs(value) < 10_000:
        return f"{value:g}"
    return f"{value:.0e}".replace("e-0", "e-").replace("e+0", "e")


def add_axis_bands(ax, thresholds: dict[str, float]) -> None:
    x_min, x_max = ax.get_xlim()
    ax.axvspan(x_min, thresholds["p10"], color="#6BAED6", alpha=0.10, zorder=0)
    ax.axvspan(x_min, thresholds["p5"], color="#6BAED6", alpha=0.08, zorder=0)
    ax.axvspan(x_min, thresholds["p1"], color="#6BAED6", alpha=0.08, zorder=0)
    ax.axvspan(thresholds["p90"], x_max, color="#E07A5F", alpha=0.10, zorder=0)
    ax.axvspan(thresholds["p95"], x_max, color="#E07A5F", alpha=0.08, zorder=0)
    ax.axvspan(thresholds["p99"], x_max, color="#E07A5F", alpha=0.08, zorder=0)
    for key, color in (("p10", "#2468A8"), ("p90", "#B44E33")):
        ax.axvline(
            thresholds[key],
            color=color,
            linewidth=0.8,
            alpha=0.75,
            linestyle="--",
            zorder=5,
        )
    ax.set_xlim(x_min, x_max)


def save_figure(fig, filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".pdf", ".svg"):
        fig.savefig(FIGURE_DIR / f"{filename}{suffix}", bbox_inches="tight")
    fig.savefig(OBSIDIAN_FIGURE_DIR / f"{filename}.png", bbox_inches="tight")


def scatter_plot(
    rows: list[dict[str, object]],
    *,
    chain: str,
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
    classes, thresholds = raw_axis_classes(xs)
    colors = [POINT_COLORS[class_name] for class_name in classes]

    if x_key == "median_base_fee_gwei":
        legend_labels = ("≤p10 fee", "p10-p90 fee", "≥p90 fee")
        ax.set_xscale("log")
        ax.set_xlim(*log_xlim(xs))
        ax.xaxis.set_major_locator(mticker.FixedLocator(log_ticks(xs)))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_tick))
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_xlabel("Median base fee during evaluation window (gwei; log scale)")
        title = f"{CHAIN_LABELS[chain]} LSTM: {title_metric} vs median base-fee level"
    else:
        legend_labels = ("≤p10 volatility", "p10-p90 volatility", "≥p90 volatility")
        ax.set_xlabel("Base-fee volatility (std. dev. of block-to-block log changes)")
        title = f"{CHAIN_LABELS[chain]} LSTM: {title_metric} vs base-fee volatility"
        ax.margins(x=0.08)

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
        s=28.0,
        edgecolors="#222222",
        linewidths=0.35,
        alpha=0.70,
        zorder=3,
    )
    ax.set_ylabel(y_label)
    ax.set_title(title, loc="left", pad=12, fontweight="bold")
    ax.set_ylim(*y_limits(ys, floor_zero=y_key == "exact_optimum_hit_rate"))
    add_axis_bands(ax, thresholds)

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
    save_figure(fig, filename)
    plt.close(fig)


def class_bar_plot(
    summary: list[dict[str, object]],
    *,
    metric: str,
    low_key: str,
    high_key: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    rc_params()
    classes = ["low_base_fee", "high_base_fee", "low_volatility", "high_volatility", "consolidated"]
    chains = ["ethereum", "polygon", "avalanche"]
    labels = ["Low fee", "High fee", "Low vol.", "High vol.", "All"]
    by_key = {(row["chain"], row["class"]): row for row in summary}

    fig, ax = plt.subplots(figsize=(9.2, 5.2))
    ax.set_facecolor("#F5F7F2")
    ax.grid(True, axis="y", color="#FFFFFF", linewidth=0.95)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.6)
    x = np.arange(len(classes))
    width = 0.24
    for idx, chain in enumerate(chains):
        offsets = x + (idx - 1) * width
        means = [float(by_key[(chain, class_name)][metric]) for class_name in classes]
        lows = [float(by_key[(chain, class_name)][low_key]) for class_name in classes]
        highs = [float(by_key[(chain, class_name)][high_key]) for class_name in classes]
        lower_err = [mean - low for mean, low in zip(means, lows, strict=True)]
        upper_err = [high - mean for mean, high in zip(means, highs, strict=True)]
        ax.bar(
            offsets,
            means,
            width=width,
            color=CHAIN_COLORS[chain],
            alpha=0.82,
            label=CHAIN_LABELS[chain],
            edgecolor="#222222",
            linewidth=0.35,
            zorder=3,
        )
        ax.errorbar(
            offsets,
            means,
            yerr=[lower_err, upper_err],
            fmt="none",
            ecolor="#333333",
            elinewidth=0.7,
            capsize=2.0,
            alpha=0.75,
            zorder=4,
        )
    ax.set_xticks(x, labels)
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", pad=12, fontweight="bold")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.10), ncol=3, frameon=False)
    fig.subplots_adjust(left=0.105, right=0.985, top=0.88, bottom=0.22)
    save_figure(fig, filename)
    plt.close(fig)


def render_chain_figures(chain_input: ChainInput, rows: list[dict[str, object]]) -> None:
    scatter_plot(
        rows,
        chain=chain_input.chain,
        x_key="median_base_fee_gwei",
        y_key="profit_over_baseline",
        y_ci_key="profit_over_baseline_ci95_half_width",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename=f"{chain_input.figure_prefix}_profit_vs_base_fee",
    )
    scatter_plot(
        rows,
        chain=chain_input.chain,
        x_key="base_fee_volatility_log_change_std",
        y_key="profit_over_baseline",
        y_ci_key="profit_over_baseline_ci95_half_width",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename=f"{chain_input.figure_prefix}_profit_vs_base_fee_volatility",
    )
    scatter_plot(
        rows,
        chain=chain_input.chain,
        x_key="median_base_fee_gwei",
        y_key="exact_optimum_hit_rate",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename=f"{chain_input.figure_prefix}_accuracy_vs_base_fee",
    )
    scatter_plot(
        rows,
        chain=chain_input.chain,
        x_key="base_fee_volatility_log_change_std",
        y_key="exact_optimum_hit_rate",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename=f"{chain_input.figure_prefix}_accuracy_vs_base_fee_volatility",
    )


def main() -> None:
    rows_by_chain: dict[str, list[dict[str, object]]] = {
        "ethereum": read_joined_csv(ETHEREUM_JOINED_PATH, "ethereum"),
        "polygon": joined_rows_from_collection("polygon", SCAN_FILES["polygon"]),
        "avalanche": joined_rows_from_collection("avalanche", SCAN_FILES["avalanche"]),
    }
    chain_inputs = {
        "polygon": ChainInput(
            chain="polygon",
            joined_csv=EXPORT_DIR / "polygon_bhilai_large_lstm_edge_case_lstm_36s_joined.csv",
            figure_prefix="polygon_bhilai_large_lstm_edge_case_lstm_36s",
        ),
        "avalanche": ChainInput(
            chain="avalanche",
            joined_csv=EXPORT_DIR / "avalanche_octane_large_lstm_edge_case_lstm_36s_joined.csv",
            figure_prefix="avalanche_octane_large_lstm_edge_case_lstm_36s",
        ),
    }

    for chain, chain_input in chain_inputs.items():
        write_csv(chain_input.joined_csv, rows_by_chain[chain])
        render_chain_figures(chain_input, rows_by_chain[chain])

    all_rows = [row for rows in rows_by_chain.values() for row in rows]
    write_csv(EXPORT_DIR / "lstm_36s_edge_case_all_chains_joined.csv", all_rows)
    summary = summary_rows(rows_by_chain)
    write_csv(EXPORT_DIR / "lstm_36s_edge_case_cross_chain_summary.csv", summary)
    class_bar_plot(
        summary,
        metric="mean_profit_percent",
        low_key="ci95_profit_low_percent",
        high_key="ci95_profit_high_percent",
        ylabel="Profit over baseline (%)",
        title="LSTM edge-case profit by chain and class",
        filename="lstm_36s_edge_case_cross_chain_profit_by_class",
    )
    class_bar_plot(
        summary,
        metric="mean_exact_optimum_hit_rate_percent",
        low_key="ci95_accuracy_low_percent",
        high_key="ci95_accuracy_high_percent",
        ylabel="Exact optimum hit rate (%)",
        title="LSTM edge-case accuracy by chain and class",
        filename="lstm_36s_edge_case_cross_chain_accuracy_by_class",
    )

    print("joined:")
    for chain, rows in rows_by_chain.items():
        print(f"  {chain}: {len(rows)}")
    print(f"all_rows={len(all_rows)}")
    print(f"summary={EXPORT_DIR / 'lstm_36s_edge_case_cross_chain_summary.csv'}")
    print(f"figures={FIGURE_DIR}")
    print(f"obsidian={OBSIDIAN_FIGURE_DIR}")


if __name__ == "__main__":
    main()
