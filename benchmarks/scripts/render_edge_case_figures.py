from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
FIGURE_DIR = ROOT / "benchmarks" / "figures"

CHAINS = ("ethereum", "polygon", "avalanche")
MODELS = ("lstm", "transformer", "transformer_lstm")

CHAIN_LABELS = {
    "ethereum": "Ethereum Pectra",
    "polygon": "Polygon Bhilai",
    "avalanche": "Avalanche Octane",
}
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
MODEL_LINESTYLES = {
    "lstm": "-",
    "transformer": "--",
    "transformer_lstm": ":",
}
CHAIN_BANDS = {
    "ethereum": "#EAF2FB",
    "polygon": "#F3ECE3",
    "avalanche": "#F1F3EA",
}

WINDOW_ORDER = {
    "ethereum": (
        "eth_vol_cluster_dec_08_2025",
        "eth_vol_cluster_dec_08_09_2025",
        "eth_quiet_low_fee_dec_19_2025",
        "eth_high_fee_jan_31_2026",
        "eth_high_fee_feb_05_2026",
        "eth_congestion_mar_22_2026",
        "eth_low_vol_apr_22_2026",
        "eth_low_vol_apr_27_2026",
    ),
    "polygon": (
        "polygon_low_fee_dec_13_2025",
        "polygon_high_vol_dec_31_2025",
        "polygon_high_fee_jan_06_2026",
        "polygon_congestion_mar_18_2026",
        "polygon_low_vol_apr_08_2026",
        "polygon_low_vol_may_17_2026",
    ),
    "avalanche": (
        "avalanche_high_vol_jan_31_2026",
        "avalanche_high_fee_feb_05_2026",
        "avalanche_low_vol_feb_14_2026",
        "avalanche_congestion_dec_18_2025",
        "avalanche_low_vol_apr_28_2026",
        "avalanche_low_fee_may_02_2026",
    ),
}

WINDOW_LABELS = {
    "eth_vol_cluster_dec_08_2025": "Vol\nDec 8",
    "eth_vol_cluster_dec_08_09_2025": "Vol\nDec 8-9",
    "eth_quiet_low_fee_dec_19_2025": "Quiet fee\nDec 19-21",
    "eth_high_fee_jan_31_2026": "High fee\nJan 31",
    "eth_high_fee_feb_05_2026": "High fee\nFeb 5",
    "eth_congestion_mar_22_2026": "Congestion\nMar 22",
    "eth_low_vol_apr_22_2026": "Low vol\nApr 22",
    "eth_low_vol_apr_27_2026": "Low vol\nApr 27",
    "polygon_low_fee_dec_13_2025": "Low fee\nDec 13",
    "polygon_high_vol_dec_31_2025": "High vol\nDec 31",
    "polygon_high_fee_jan_06_2026": "High fee\nJan 6",
    "polygon_congestion_mar_18_2026": "Congestion\nMar 18",
    "polygon_low_vol_apr_08_2026": "Low vol\nApr 8",
    "polygon_low_vol_may_17_2026": "Low vol\nMay 17",
    "avalanche_high_vol_jan_31_2026": "High vol\nJan 31",
    "avalanche_high_fee_feb_05_2026": "High fee\nFeb 5",
    "avalanche_low_vol_feb_14_2026": "Low vol\nFeb 14",
    "avalanche_congestion_dec_18_2025": "Congestion\nDec 18",
    "avalanche_low_vol_apr_28_2026": "Low vol\nApr 28",
    "avalanche_low_fee_may_02_2026": "Low fee\nMay 2",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def y_limits(values: list[float]) -> tuple[float, float]:
    finite = sorted(v for v in values if math.isfinite(v))
    low = min(finite)
    high = max(finite)
    if low >= 0:
        low = 0.0
    span = high - low
    padding = span * 0.16 if span > 0 else max(abs(high) * 0.2, 0.05)
    return low - padding if low < 0 else 0.0, high + padding


def rc_params() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 9,
            "figure.dpi": 160,
            "savefig.dpi": 220,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#9A9A9A",
            "xtick.color": "#333333",
            "ytick.color": "#333333",
        }
    )


def values_by_chain_window_model(
    rows: list[dict[str, str]],
) -> dict[tuple[str, str, str], float]:
    out: dict[tuple[str, str, str], float] = {}
    for row in rows:
        key = (row["chain"], row["evaluation_id"], row["model"])
        out[key] = float(row["profit_over_baseline"]) * 100.0
    return out


def style_axis(ax: plt.Axes, chain: str) -> None:
    ax.set_facecolor(CHAIN_BANDS[chain])
    ax.grid(True, color="#FFFFFF", linewidth=0.9)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.65)
    ax.tick_params(axis="both", labelsize=8)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.55)


def plot_chain_grid(rows: list[dict[str, str]], filename: str) -> None:
    rc_params()
    values = values_by_chain_window_model(rows)
    fig, axes = plt.subplots(1, len(CHAINS), figsize=(12.6, 3.8), squeeze=False)
    handles: list[plt.Line2D] = []
    labels: list[str] = []

    for col_index, chain in enumerate(CHAINS):
        ax = axes[0][col_index]
        style_axis(ax, chain)
        windows = WINDOW_ORDER[chain]
        xs = list(range(len(windows)))
        chain_values: list[float] = []

        for model in MODELS:
            ys = [values.get((chain, window, model), math.nan) for window in windows]
            if all(math.isnan(y) for y in ys):
                continue
            chain_values.extend(y for y in ys if math.isfinite(y))
            (line,) = ax.plot(
                xs,
                ys,
                label=MODEL_LABELS[model],
                color=MODEL_COLORS[model],
                marker=MODEL_MARKERS[model],
                linestyle=MODEL_LINESTYLES[model],
                markersize=4.2,
                markeredgewidth=0.75,
                markeredgecolor="#202020",
                linewidth=1.9,
                alpha=0.95,
            )
            if col_index == 0:
                handles.append(line)
                labels.append(MODEL_LABELS[model])

        ax.set_title(CHAIN_LABELS[chain], pad=9, fontweight="bold")
        ax.set_xticks(xs)
        ax.set_xticklabels(
            [WINDOW_LABELS[w] for w in windows],
            rotation=25,
            ha="right",
            rotation_mode="anchor",
        )
        ax.set_xlabel("Evaluation window")
        if col_index == 0:
            ax.set_ylabel("Profit over baseline (%)")
        ax.set_xlim(-0.35, len(windows) - 0.65)
        ax.set_ylim(*y_limits(chain_values))

    fig.legend(
        handles,
        labels,
        title="Model",
        loc="upper center",
        ncol=len(MODELS),
        frameon=False,
        bbox_to_anchor=(0.5, 1.0),
        borderaxespad=0.0,
        handlelength=2.8,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.88], h_pad=2.2, w_pad=2.4)
    fig.savefig(FIGURE_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def plot_ethereum(rows: list[dict[str, str]], filename: str) -> None:
    rc_params()
    values = values_by_chain_window_model(rows)
    chain = "ethereum"
    windows = WINDOW_ORDER[chain]
    xs = list(range(len(windows)))
    fig, ax = plt.subplots(1, 1, figsize=(12.6, 3.8))
    style_axis(ax, chain)
    all_values: list[float] = []

    for model in MODELS:
        ys = [values.get((chain, window, model), math.nan) for window in windows]
        all_values.extend(y for y in ys if math.isfinite(y))
        ax.plot(
            xs,
            ys,
            label=MODEL_LABELS[model],
            color=MODEL_COLORS[model],
            marker=MODEL_MARKERS[model],
            linestyle=MODEL_LINESTYLES[model],
            markersize=4.2,
            markeredgewidth=0.75,
            markeredgecolor="#202020",
            linewidth=1.9,
            alpha=0.95,
        )

    ax.set_title(
        "Ethereum Pectra edge-case windows",
        loc="left",
        pad=12,
        fontweight="bold",
    )
    ax.set_ylabel("Profit over baseline (%)")
    ax.set_xlabel("Evaluation window")
    ax.set_xticks(xs)
    ax.set_xticklabels(
        [WINDOW_LABELS[w] for w in windows],
        rotation=25,
        ha="right",
        rotation_mode="anchor",
    )
    ax.set_xlim(-0.35, len(windows) - 0.65)
    ax.set_ylim(*y_limits(all_values))
    ax.legend(
        title="Model",
        loc="upper center",
        ncol=len(MODELS),
        frameon=False,
        bbox_to_anchor=(0.5, 1.22),
        borderaxespad=0.0,
        handlelength=2.8,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(FIGURE_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    rows = read_csv(EXPORT_DIR / "edge_case_baseline_36s_evals_merged.csv")
    plot_ethereum(rows, "edge_case_baseline_36s_profit_ethereum_pectra_fig6_style.png")
    plot_chain_grid(rows, "edge_case_baseline_36s_profit_all_chains_fig6_style.png")


if __name__ == "__main__":
    main()
