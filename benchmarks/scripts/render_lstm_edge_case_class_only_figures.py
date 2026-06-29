from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
FIGURE_DIR = ROOT / "benchmarks" / "figures"
OBSIDIAN_FIGURE_DIR = Path("/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures")

JOINED_CSV = EXPORT_DIR / "lstm_36s_edge_case_all_chains_joined.csv"
CORRELATION_CSV = EXPORT_DIR / "lstm_36s_edge_case_current_pearson_correlations.csv"
CORRELATION_MD = EXPORT_DIR / "lstm_36s_edge_case_current_preliminaries.md"

CHAIN_LABELS = {
    "ethereum": "Ethereum Pectra",
    "polygon": "Polygon Bhilai",
    "avalanche": "Avalanche Octane",
}

FIGURE_PREFIXES = {
    "ethereum": "ethereum_pectra_jun20_lstm",
    "polygon": "polygon_bhilai_large_lstm_edge_case_lstm_36s",
    "avalanche": "avalanche_octane_large_lstm_edge_case_lstm_36s",
}

POINT_COLORS = {
    "low": "#2468A8",
    "high": "#B44E33",
}

NUMERIC_FIELDS = {
    "duration_hours",
    "n_blocks",
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
    "sample_count",
    "total_events",
}


def read_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with JOINED_CSV.open(newline="") as handle:
        for row in csv.DictReader(handle):
            converted: dict[str, object] = {}
            for key, value in row.items():
                if key in NUMERIC_FIELDS:
                    converted[key] = float(value)
                else:
                    converted[key] = value
            rows.append(converted)
    return rows


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
    return [
        multiple * (10**power)
        for power in range(start, stop + 1)
        for multiple in multiples
        if low <= multiple * (10**power) <= high
    ]


def format_tick(value: float, _: int) -> str:
    if value == 0:
        return "0"
    if 0.001 <= abs(value) < 10_000:
        return f"{value:g}"
    return f"{value:.0e}".replace("e-0", "e-").replace("e+0", "e")


def save_figure(fig, filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".pdf", ".svg"):
        fig.savefig(FIGURE_DIR / f"{filename}{suffix}", bbox_inches="tight")
    fig.savefig(OBSIDIAN_FIGURE_DIR / f"{filename}.png", bbox_inches="tight")


def class_only_rows(
    rows: list[dict[str, object]],
    *,
    class_key: str,
    low_value: str,
    high_value: str,
) -> list[dict[str, object]]:
    return [
        row
        for row in rows
        if row[class_key] == low_value or row[class_key] == high_value
    ]


def class_color(row: dict[str, object], *, class_key: str, low_value: str) -> str:
    return POINT_COLORS["low" if row[class_key] == low_value else "high"]


def plot_class_only(
    rows: list[dict[str, object]],
    *,
    chain: str,
    x_key: str,
    y_key: str,
    y_ci_key: str,
    class_key: str,
    low_value: str,
    high_value: str,
    low_label: str,
    high_label: str,
    x_label: str,
    y_label: str,
    title_metric: str,
    filename: str,
    log_x: bool = False,
) -> None:
    rc_params()
    plotted = class_only_rows(
        rows,
        class_key=class_key,
        low_value=low_value,
        high_value=high_value,
    )
    if not plotted:
        raise ValueError(f"no rows for {filename}")

    fig, ax = plt.subplots(figsize=(9.2, 5.45))
    ax.set_facecolor("#F5F7F2")
    ax.grid(True, color="#FFFFFF", linewidth=0.95)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.7)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.6)

    xs = [float(row[x_key]) for row in plotted]
    ys = [float(row[y_key]) * 100.0 for row in plotted]
    yerr = [float(row[y_ci_key]) * 100.0 for row in plotted]
    colors = [
        class_color(row, class_key=class_key, low_value=low_value)
        for row in plotted
    ]

    if log_x:
        ax.set_xscale("log")
        ax.set_xlim(*log_xlim(xs))
        ax.xaxis.set_major_locator(mticker.FixedLocator(log_ticks(xs)))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_tick))
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    else:
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
        s=30.0,
        edgecolors="#222222",
        linewidths=0.35,
        alpha=0.74,
        zorder=3,
    )

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(
        f"{CHAIN_LABELS[chain]} LSTM: {title_metric} class-only view",
        loc="left",
        pad=12,
        fontweight="bold",
    )
    ax.set_ylim(*y_limits(ys, floor_zero=y_key == "exact_optimum_hit_rate"))

    handles = [
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=POINT_COLORS["low"],
            label=low_label,
        ),
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=POINT_COLORS["high"],
            label=high_label,
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        bbox_to_anchor=(0.5, 0.035),
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.88, bottom=0.22)
    save_figure(fig, filename)
    plt.close(fig)


def render_figures(rows: list[dict[str, object]]) -> list[str]:
    filenames: list[str] = []
    rows_by_chain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_chain[str(row["chain"])].append(row)

    for chain, chain_rows in rows_by_chain.items():
        prefix = FIGURE_PREFIXES[chain]
        figure_specs = [
            {
                "x_key": "median_base_fee_gwei",
                "y_key": "profit_over_baseline",
                "y_ci_key": "profit_over_baseline_ci95_half_width",
                "class_key": "fee_level_class",
                "low_value": "low_base_fee",
                "high_value": "high_base_fee",
                "low_label": "low fee class (duration-specific <=p10)",
                "high_label": "high fee class (duration-specific >=p90)",
                "x_label": "Median base fee during evaluation window (gwei; log scale)",
                "y_label": "Profit over baseline (%)",
                "title_metric": "profit vs median base fee",
                "filename": f"{prefix}_profit_vs_base_fee_class_only",
                "log_x": True,
            },
            {
                "x_key": "base_fee_volatility_log_change_std",
                "y_key": "profit_over_baseline",
                "y_ci_key": "profit_over_baseline_ci95_half_width",
                "class_key": "volatility_class",
                "low_value": "low_volatility",
                "high_value": "high_volatility",
                "low_label": "low volatility class (duration-specific <=p10)",
                "high_label": "high volatility class (duration-specific >=p90)",
                "x_label": "Base-fee volatility (std. dev. of block-to-block log changes)",
                "y_label": "Profit over baseline (%)",
                "title_metric": "profit vs base-fee volatility",
                "filename": f"{prefix}_profit_vs_base_fee_volatility_class_only",
                "log_x": False,
            },
            {
                "x_key": "median_base_fee_gwei",
                "y_key": "exact_optimum_hit_rate",
                "y_ci_key": "exact_optimum_hit_rate_ci95_half_width",
                "class_key": "fee_level_class",
                "low_value": "low_base_fee",
                "high_value": "high_base_fee",
                "low_label": "low fee class (duration-specific <=p10)",
                "high_label": "high fee class (duration-specific >=p90)",
                "x_label": "Median base fee during evaluation window (gwei; log scale)",
                "y_label": "Exact optimum hit rate (%)",
                "title_metric": "accuracy vs median base fee",
                "filename": f"{prefix}_accuracy_vs_base_fee_class_only",
                "log_x": True,
            },
            {
                "x_key": "base_fee_volatility_log_change_std",
                "y_key": "exact_optimum_hit_rate",
                "y_ci_key": "exact_optimum_hit_rate_ci95_half_width",
                "class_key": "volatility_class",
                "low_value": "low_volatility",
                "high_value": "high_volatility",
                "low_label": "low volatility class (duration-specific <=p10)",
                "high_label": "high volatility class (duration-specific >=p90)",
                "x_label": "Base-fee volatility (std. dev. of block-to-block log changes)",
                "y_label": "Exact optimum hit rate (%)",
                "title_metric": "accuracy vs base-fee volatility",
                "filename": f"{prefix}_accuracy_vs_base_fee_volatility_class_only",
                "log_x": False,
            },
        ]
        for spec in figure_specs:
            plot_class_only(chain_rows, chain=chain, **spec)
            filenames.append(f"{spec['filename']}.png")
    return filenames


def pearson_record(
    rows: list[dict[str, object]],
    *,
    chain: str,
    x_metric: str,
    x_label: str,
) -> dict[str, object]:
    if x_metric == "log10_median_base_fee_gwei":
        xs = np.log10(
            np.asarray(
                [float(row["median_base_fee_gwei"]) for row in rows],
                dtype=np.float64,
            )
        )
    else:
        xs = np.asarray([float(row[x_metric]) for row in rows], dtype=np.float64)
    ys = np.asarray(
        [float(row["profit_over_baseline"]) * 100.0 for row in rows],
        dtype=np.float64,
    )
    result = stats.pearsonr(xs, ys)
    return {
        "chain": chain,
        "x_metric": x_metric,
        "x_label": x_label,
        "target_metric": "profit_over_baseline_percent",
        "n": int(xs.shape[0]),
        "pearson_r": float(result.statistic),
        "p_value": float(result.pvalue),
        "x_min": float(np.min(xs)),
        "x_max": float(np.max(xs)),
        "profit_mean_percent": float(np.mean(ys)),
    }


def correlation_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows_by_chain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        rows_by_chain[str(row["chain"])].append(row)
    rows_by_chain["all_chains"] = rows

    x_metrics = [
        ("median_base_fee_gwei", "median base fee"),
        ("log10_median_base_fee_gwei", "log10 median base fee"),
        ("base_fee_volatility_log_change_std", "base-fee volatility"),
    ]

    records: list[dict[str, object]] = []
    for chain in ("ethereum", "polygon", "avalanche", "all_chains"):
        for x_metric, x_label in x_metrics:
            records.append(
                pearson_record(
                    rows_by_chain[chain],
                    chain=chain,
                    x_metric=x_metric,
                    x_label=x_label,
                )
            )
    return records


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def p_value_text(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def markdown_table(records: list[dict[str, object]]) -> str:
    lines = [
        "| Chain | X metric | n | Pearson r | p-value |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for row in records:
        chain = str(row["chain"]).replace("_", " ").title()
        metric = str(row["x_label"])
        lines.append(
            "| "
            f"{chain} | {metric} | {int(row['n'])} | "
            f"{float(row['pearson_r']):.3f} | {p_value_text(float(row['p_value']))} |"
        )
    return "\n".join(lines)


def write_markdown(figures: list[str], records: list[dict[str, object]]) -> None:
    by_chain: dict[str, list[str]] = defaultdict(list)
    for figure in figures:
        for chain, prefix in FIGURE_PREFIXES.items():
            if figure.startswith(prefix):
                by_chain[chain].append(figure)

    lines = [
        "### 28/06 current wall-clock class-only preliminaries",
        "",
        "These use the existing wall-clock Poisson replay evaluations. They do not include the future block-based evaluator.",
        "",
        "Class-only figures remove the p10-p90 middle windows. Fee plots show only windows tagged low/high base fee. Volatility plots show only windows tagged low/high volatility. Class tags are duration-specific.",
        "",
        "#### Class-only figures",
    ]
    for chain in ("ethereum", "polygon", "avalanche"):
        lines.append(f"##### {CHAIN_LABELS[chain]}")
        for figure in by_chain[chain]:
            lines.append(f"![[{figure}]]")
        lines.append("")
    lines.extend(
        [
            "#### Pearson correlations",
            "",
            "Target variable: profit over baseline (%). Current correlations are preliminary because the evaluated windows are tail-selected, not uniformly sampled across all quartiles.",
            "",
            markdown_table(records),
            "",
            f"CSV: `{CORRELATION_CSV}`",
            "",
        ]
    )
    CORRELATION_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rows = read_rows()
    figures = render_figures(rows)
    correlations = correlation_rows(rows)
    write_csv(CORRELATION_CSV, correlations)
    write_markdown(figures, correlations)
    print(f"figures={len(figures)}")
    print(f"correlations={CORRELATION_CSV}")
    print(f"markdown={CORRELATION_MD}")


if __name__ == "__main__":
    main()
