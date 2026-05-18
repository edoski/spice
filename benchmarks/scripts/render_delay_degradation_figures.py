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
    "ethereum": "Ethereum",
    "polygon": "Polygon",
    "avalanche": "Avalanche",
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def numeric(value: str | float | int | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def series_by_chain_model(
    rows: list[dict[str, str]],
    metric: str,
    *,
    model_ids: tuple[str, ...],
    percent: bool = False,
) -> dict[tuple[str, str], list[tuple[int, float]]]:
    out: dict[tuple[str, str], list[tuple[int, float]]] = defaultdict(list)
    selected_models = set(model_ids)
    scale = 100.0 if percent else 1.0
    for row in rows:
        if row["model"] not in selected_models:
            continue
        value = numeric(row.get(metric))
        if value is None:
            continue
        out[(row["chain"], row["model"])].append(
            (int(row["delay_seconds"]), value * scale)
        )
    for points in out.values():
        points.sort()
    return out


def y_limits(values: list[float]) -> tuple[float, float] | None:
    finite = sorted(v for v in values if math.isfinite(v))
    if not finite:
        return None
    low = min(finite)
    high = max(finite)
    if low >= 0:
        low = 0.0
    span = high - low
    padding = span * 0.14 if span > 0 else max(abs(high) * 0.2, 0.05)
    return low - padding if low < 0 else 0.0, high + padding


def x_limit_for_chain(
    rows: list[dict[str, str]],
    chain: str,
    *,
    model_ids: tuple[str, ...],
) -> int:
    selected_models = set(model_ids)
    values = [
        int(row["delay_seconds"])
        for row in rows
        if row["chain"] == chain and row["model"] in selected_models
    ]
    return max(values) if values else 120


def style_chain_axis(ax: plt.Axes, chain: str, *, show_ylabel: bool) -> None:
    ax.set_facecolor(CHAIN_BANDS[chain])
    ax.grid(True, color="#FFFFFF", linewidth=0.9)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.65)
    ax.tick_params(axis="both", labelsize=8)
    if not show_ylabel:
        ax.set_ylabel("")


def plot_grid(
    rows: list[dict[str, str]],
    metrics: tuple[str, ...],
    titles: tuple[str, ...],
    filename: str,
    *,
    model_ids: tuple[str, ...] = MODELS,
    ylabel: str | None = None,
    percent: bool = False,
) -> None:
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

    figure_height = 3.35 * len(metrics) + 0.35
    fig, axes = plt.subplots(
        len(metrics),
        len(CHAINS),
        figsize=(12.6, figure_height),
        squeeze=False,
    )

    handles: list[plt.Line2D] = []
    labels: list[str] = []

    for row_index, metric in enumerate(metrics):
        data = series_by_chain_model(
            rows,
            metric,
            model_ids=model_ids,
            percent=percent,
        )
        for col_index, chain in enumerate(CHAINS):
            ax = axes[row_index][col_index]
            style_chain_axis(ax, chain, show_ylabel=col_index == 0)
            chain_values: list[float] = []

            for model in model_ids:
                points = data.get((chain, model), [])
                if not points:
                    continue
                xs = [x for x, _ in points]
                ys = [y for _, y in points]
                chain_values.extend(ys)
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
                if row_index == 0 and col_index == 0:
                    handles.append(line)
                    labels.append(MODEL_LABELS[model])

            title = CHAIN_LABELS[chain]
            if len(metrics) > 1:
                title = f"{title}: {titles[row_index]}"
            ax.set_title(title, pad=9, fontweight="bold")
            ax.set_xlabel("Prediction window (seconds)")
            if col_index == 0:
                ax.set_ylabel(ylabel or titles[row_index])
            ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.55)
            ax.set_xlim(0, x_limit_for_chain(rows, chain, model_ids=model_ids) * 1.03)
            limits = y_limits(chain_values)
            if limits is not None:
                ax.set_ylim(*limits)

    fig.legend(
        handles,
        labels,
        title="Model" if len(model_ids) > 1 else None,
        loc="upper center",
        ncol=len(model_ids),
        frameon=False,
        bbox_to_anchor=(0.5, 1.0),
        borderaxespad=0.0,
        handlelength=2.8,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91], h_pad=2.2, w_pad=2.0)
    fig.savefig(FIGURE_DIR / filename, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    profit_rows = read_csv(EXPORT_DIR / "delay_degradation_completed_evals_merged.csv")
    metric_rows = read_csv(EXPORT_DIR / "delay_degradation_completed_ml_metrics_merged.csv")
    model_ids = ("lstm",)

    plot_grid(
        profit_rows,
        ("profit_over_baseline",),
        ("Profit over baseline",),
        "delay_degradation_completed_profit_fig6_style.png",
        model_ids=model_ids,
        ylabel="Profit over baseline (%)",
        percent=True,
    )
    plot_grid(
        metric_rows,
        ("offset_accuracy", "macro_f1"),
        ("Offset accuracy", "Macro F1"),
        "delay_degradation_completed_classification_metrics_fig6_style.png",
        model_ids=model_ids,
    )
    plot_grid(
        metric_rows,
        ("log_fee_mae", "log_fee_mse"),
        ("Log fee MAE", "Log fee MSE"),
        "delay_degradation_completed_fee_regression_metrics_fig6_style.png",
        model_ids=model_ids,
    )
    plot_grid(
        metric_rows,
        ("total_loss", "classification_loss", "regression_loss"),
        ("Total loss", "Classification loss", "Regression loss"),
        "delay_degradation_completed_loss_diagnostics_fig6_style.png",
        model_ids=model_ids,
    )


if __name__ == "__main__":
    main()
