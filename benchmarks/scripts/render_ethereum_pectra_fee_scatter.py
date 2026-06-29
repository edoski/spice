from __future__ import annotations

import csv
import math
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import polars as pl


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
FIGURE_DIR = ROOT / "benchmarks" / "figures"
BLOCKS_GLOB = (
    ROOT
    / "outputs"
    / "corpora"
    / "ethereum"
    / "cor_2edb8f7b84a4edf95e2b"
    / "blocks"
    / "*.parquet"
)

MODELS = ("lstm", "transformer", "transformer_lstm")
MODEL_LABELS = {
    "lstm": "LSTM",
    "transformer": "Transformer",
    "transformer_lstm": "LSTM+Transformer",
}
MODEL_COLORS = {
    "lstm": "#2468A8",
    "transformer": "#C76E18",
    "transformer_lstm": "#2D8758",
}
MODEL_MARKERS = {
    "lstm": "o",
    "transformer": "s",
    "transformer_lstm": "^",
}
MODEL_POINT_DODGE = {
    "lstm": -1.0,
    "transformer": 0.0,
    "transformer_lstm": 1.0,
}

WINDOWS = (
    "eth_vol_cluster_dec_08_09_2025",
    "eth_quiet_low_fee_dec_19_2025",
    "eth_high_fee_feb_05_2026",
    "eth_low_vol_apr_22_2026",
    "eth_low_vol_apr_27_2026",
)
WINDOW_LABELS = {
    "eth_vol_cluster_dec_08_09_2025": "High volatility\nDec 8-9",
    "eth_quiet_low_fee_dec_19_2025": "Low fee\nDec 19-21",
    "eth_high_fee_feb_05_2026": "High fee\nFeb 5",
    "eth_low_vol_apr_22_2026": "Low volatility +\nhigher fee Apr 22",
    "eth_low_vol_apr_27_2026": "Low volatility\nApr 27",
}
WINDOW_TEXT_OFFSETS = {
    "eth_vol_cluster_dec_08_09_2025": (5, 6),
    "eth_quiet_low_fee_dec_19_2025": (6, -12),
    "eth_high_fee_feb_05_2026": (-32, 5),
    "eth_low_vol_apr_22_2026": (7, 8),
    "eth_low_vol_apr_27_2026": (8, -12),
}


def read_eval_rows() -> list[dict[str, str]]:
    path = EXPORT_DIR / "edge_case_baseline_36s_evals_merged.csv"
    with path.open(newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle)
            if row["chain"] == "ethereum" and row["evaluation_id"] in WINDOWS
        ]


def window_timestamps(start_iso: str, duration_seconds: int) -> tuple[int, int]:
    start = int(datetime.fromisoformat(start_iso.replace("Z", "+00:00")).timestamp())
    return start, start + duration_seconds


def base_fee_stats(rows: list[dict[str, str]]) -> dict[str, dict[str, float]]:
    windows: dict[str, tuple[int, int]] = {}
    for row in rows:
        windows.setdefault(
            row["evaluation_id"],
            window_timestamps(row["window_start"], int(row["duration_seconds"])),
        )

    stats: dict[str, dict[str, float]] = {}
    scan = pl.scan_parquet(str(BLOCKS_GLOB))
    for window_id, (start, end) in windows.items():
        fees = (
            scan.filter((pl.col("timestamp") >= start) & (pl.col("timestamp") < end))
            .select((pl.col("base_fee_per_gas").cast(pl.Float64) / 1e9).alias("fee_gwei"))
            .collect()["fee_gwei"]
        )
        log_fees = fees.log()
        log_fee_changes = log_fees.diff().drop_nulls()
        stats[window_id] = {
            "base_fee_mean_gwei": float(fees.mean()),
            "base_fee_median_gwei": float(fees.median()),
            "base_fee_volatility_log_std": float(log_fees.std()),
            "base_fee_volatility_log_change_std": float(log_fee_changes.std()),
            "base_fee_range_gwei": float(fees.max() - fees.min()),
            "blocks": float(len(fees)),
        }
    return stats


def write_summary(rows: list[dict[str, str]], stats: dict[str, dict[str, float]]) -> None:
    out = EXPORT_DIR / "ethereum_pectra_edge_case_fee_scatter_summary.csv"
    fields = [
        "evaluation_id",
        "window_label",
        "window_start",
        "duration_seconds",
        "model",
        "profit_over_baseline_percent",
        "base_fee_mean_gwei",
        "base_fee_median_gwei",
        "base_fee_volatility_log_std",
        "base_fee_volatility_log_change_std",
        "base_fee_range_gwei",
        "blocks",
    ]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            window_stats = stats[row["evaluation_id"]]
            writer.writerow(
                {
                    "evaluation_id": row["evaluation_id"],
                    "window_label": WINDOW_LABELS[row["evaluation_id"]].replace("\n", " "),
                    "window_start": row["window_start"],
                    "duration_seconds": row["duration_seconds"],
                    "model": row["model"],
                    "profit_over_baseline_percent": float(row["profit_over_baseline"])
                    * 100.0,
                    **window_stats,
                }
            )


def rc_params() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "legend.fontsize": 9,
            "figure.dpi": 160,
            "savefig.dpi": 240,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#9A9A9A",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
        }
    )


def y_limits(values: list[float]) -> tuple[float, float]:
    high = max(values)
    low = min(0.0, min(values))
    padding = max((high - low) * 0.18, 0.15)
    return low - padding if low < 0 else 0.0, high + padding


def plot(rows: list[dict[str, str]], stats: dict[str, dict[str, float]], x_key: str, filename: str) -> None:
    rc_params()
    fig, ax = plt.subplots(figsize=(7.8, 5.45))
    ax.set_facecolor("#F5F7F2")
    ax.grid(True, color="#FFFFFF", linewidth=0.95)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.7)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.6)

    window_xs = [stats[window_id][x_key] for window_id in WINDOWS]
    linear_dodge_step = (max(window_xs) - min(window_xs)) * 0.012
    all_y: list[float] = []
    for model in MODELS:
        model_rows = [row for row in rows if row["model"] == model]
        xs = [stats[row["evaluation_id"]][x_key] for row in model_rows]
        if x_key == "base_fee_mean_gwei":
            dodge_factor = 1.0 + MODEL_POINT_DODGE[model] * 0.018
            xs = [x * dodge_factor for x in xs]
        else:
            dodge = MODEL_POINT_DODGE[model] * linear_dodge_step
            xs = [x + dodge for x in xs]
        ys = [float(row["profit_over_baseline"]) * 100.0 for row in model_rows]
        all_y.extend(ys)
        ax.scatter(
            xs,
            ys,
            label=MODEL_LABELS[model],
            color=MODEL_COLORS[model],
            marker=MODEL_MARKERS[model],
            s=54,
            edgecolors="#222222",
            linewidths=0.75,
            alpha=0.92,
            zorder=3,
        )

    for window_id in WINDOWS:
        window_rows = [row for row in rows if row["evaluation_id"] == window_id]
        if not window_rows:
            continue
        x = stats[window_id][x_key]
        y = sum(float(row["profit_over_baseline"]) * 100.0 for row in window_rows) / len(
            window_rows
        )
        dx, dy = WINDOW_TEXT_OFFSETS[window_id]
        ax.annotate(
            WINDOW_LABELS[window_id],
            xy=(x, y),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8,
            color="#222222",
            ha="left" if dx >= 0 else "right",
            va="bottom" if dy >= 0 else "top",
            bbox={
                "boxstyle": "round,pad=0.18",
                "facecolor": "#F5F7F2",
                "edgecolor": "none",
                "alpha": 0.88,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": "#525252",
                "linewidth": 0.8,
                "shrinkA": 2,
                "shrinkB": 5,
                "connectionstyle": "arc3,rad=0.08",
            },
        )

    if x_key == "base_fee_mean_gwei":
        ax.set_xscale("log")
        ax.set_xticks([0.03, 0.1, 0.3, 1.0, 3.0, 10.0])
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{value:g}"))
        ax.set_xlabel("Mean base fee during evaluation window (gwei; log scale)")
        title = "Ethereum Pectra: profit vs base-fee level"
    else:
        ax.set_xlabel(
            "Base-fee volatility during evaluation window "
            "(std. dev. of block-to-block log changes)"
        )
        title = "Ethereum Pectra: profit vs base-fee volatility"

    ax.set_ylabel("Profit over baseline (%)")
    ax.set_title(title, loc="left", pad=12, fontweight="bold")
    ax.set_ylim(*y_limits(all_y))
    ax.margins(x=0.12)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        title="Model",
        loc="lower center",
        ncol=len(MODELS),
        frameon=False,
        bbox_to_anchor=(0.5, 0.035),
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.88, bottom=0.23)
    for suffix in (".png", ".pdf", ".svg"):
        fig.savefig(FIGURE_DIR / f"{filename}{suffix}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = read_eval_rows()
    stats = base_fee_stats(rows)
    write_summary(rows, stats)
    plot(rows, stats, "base_fee_mean_gwei", "ethereum_pectra_profit_vs_base_fee")
    plot(
        rows,
        stats,
        "base_fee_volatility_log_change_std",
        "ethereum_pectra_profit_vs_base_fee_volatility",
    )


if __name__ == "__main__":
    main()
