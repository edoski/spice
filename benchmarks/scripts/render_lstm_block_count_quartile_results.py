from __future__ import annotations

import csv
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
EXPORT_DIR = ROOT / "benchmarks" / "exports"
SCAN_DIR = EXPORT_DIR / "evaluation_window_scans"
FIGURE_DIR = ROOT / "benchmarks" / "figures"
OBSIDIAN_FIGURE_DIR = Path("/Users/edo/Documents/Obsidian/the-vault/notes/benchmark_figures")
RUN_DIR = (
    ROOT
    / "outputs"
    / "benchmarks"
    / "runs"
    / "lstm_36s_block_count_quartile_eval"
    / "20260629T184758Z"
)
COLLECTION_PATH = RUN_DIR / "collection.json"
WINDOW_BLOCK_COUNT = 1200
WINDOW_LABEL = f"{WINDOW_BLOCK_COUNT}-block"


@dataclass(frozen=True)
class ChainConfig:
    chain: str
    label: str
    scan_prefix: str
    figure_prefix: str


CHAIN_CONFIGS = (
    ChainConfig(
        chain="ethereum",
        label="Ethereum Pectra",
        scan_prefix="ethereum_pectra_jun20_block_count_quartile",
        figure_prefix="ethereum_pectra_jun20_lstm_block_count_quartile",
    ),
    ChainConfig(
        chain="polygon",
        label="Polygon Bhilai",
        scan_prefix="polygon_bhilai_large_lstm_block_count_quartile",
        figure_prefix="polygon_bhilai_large_lstm_block_count_quartile",
    ),
    ChainConfig(
        chain="avalanche",
        label="Avalanche Octane",
        scan_prefix="avalanche_octane_large_lstm_block_count_quartile",
        figure_prefix="avalanche_octane_large_lstm_block_count_quartile",
    ),
)

QUARTILE_COLORS = {
    "q1": "#2468A8",
    "q2": "#4F8A66",
    "q3": "#C78A2C",
    "q4": "#B44E33",
}
QUARTILE_LABELS = {
    "q1": "Q1 lowest 25%",
    "q2": "Q2 25-50%",
    "q3": "Q3 50-75%",
    "q4": "Q4 highest 25%",
}
CHAIN_COLORS = {
    "ethereum": "#4F6F52",
    "polygon": "#6D5BD0",
    "avalanche": "#C2413D",
}

CSV_FIELDS = [
    "chain",
    "window_id",
    "run_id",
    "selection_metric",
    "selection_quartile",
    "block_count",
    "start_block",
    "end_block_exclusive",
    "n_blocks",
    "start_iso",
    "end_iso",
    "median_base_fee_gwei",
    "mean_base_fee_gwei",
    "base_fee_volatility_log_change_std",
    "median_fee_percentile",
    "volatility_percentile",
    "fee_quartile",
    "volatility_quartile",
    "profit_over_baseline_percent",
    "profit_over_baseline_ci95_half_width_percent",
    "exact_optimum_hit_rate_percent",
    "exact_optimum_hit_rate_ci95_half_width_percent",
    "cost_over_optimum_percent",
    "baseline_cost_over_optimum_percent",
    "evaluation_job_id",
    "evaluation_target",
]

POLYGON_FEE_BULK_RULE = "log10(median_base_fee_gwei) 1.5*IQR fence"
POLYGON_FEE_BULK_NOTE = (
    "Bulk view excludes fee-selected Polygon windows outside 1.5*IQR Tukey fences "
    "computed on log10 median base fee."
)
POLYGON_VOLATILITY_PROFIT_BULK_RULE = "profit_over_baseline_percent 5*IQR fence"
OUTLIER_FIELDS = [
    "chain",
    "window_id",
    "selection_quartile",
    "median_base_fee_gwei",
    "base_fee_volatility_log_change_std",
    "log10_median_base_fee_gwei",
    "outlier_side",
    "outlier_rule",
    "profit_over_baseline_percent",
    "exact_optimum_hit_rate_percent",
    "start_block",
    "end_block_exclusive",
]


def metric_value(metrics: Iterable[dict[str, object]], metric_id: str) -> float:
    for metric in metrics:
        if metric["metric_id"] == metric_id:
            return float(metric["value"])
    raise KeyError(metric_id)


def window_metric_summary(
    metrics: Iterable[dict[str, object]], metric_id: str
) -> tuple[float, float]:
    for metric in metrics:
        if metric["metric_id"] == metric_id:
            return float(metric["mean"]), float(metric["std"])
    raise KeyError(metric_id)


def read_selected_rows(config: ChainConfig) -> dict[str, dict[str, str]]:
    path = SCAN_DIR / f"{config.scan_prefix}_windows_recommended.csv"
    with path.open(newline="") as handle:
        rows = {row["window_id"]: row for row in csv.DictReader(handle)}
    if len(rows) != 216:
        raise ValueError(f"expected 216 selected rows for {config.chain}, got {len(rows)}")
    return rows


def read_collection_records() -> list[dict[str, object]]:
    data = json.loads(COLLECTION_PATH.read_text(encoding="utf-8"))
    records = data["records"]
    if len(records) != 648:
        raise ValueError(f"expected 648 collection records, got {len(records)}")
    return records


def joined_rows() -> list[dict[str, object]]:
    selected_by_chain = {config.chain: read_selected_rows(config) for config in CHAIN_CONFIGS}
    rows: list[dict[str, object]] = []
    for record in read_collection_records():
        chain = str(record["chain_name"])
        window_id = str(record["dimension_labels"]["evaluations"])
        scan_row = selected_by_chain[chain][window_id]
        profit_mean, profit_std = window_metric_summary(
            record["window_metrics"], "profit_over_baseline"
        )
        hit_mean, hit_std = window_metric_summary(
            record["window_metrics"], "exact_optimum_hit_rate"
        )
        repetitions = 50.0
        rows.append(
            {
                "chain": chain,
                "window_id": window_id,
                "run_id": record["run_id"],
                "selection_metric": scan_row["selection_metric"],
                "selection_quartile": scan_row["quartile"],
                "block_count": int(scan_row["block_count"]),
                "start_block": int(scan_row["start_block"]),
                "end_block_exclusive": int(scan_row["end_block_exclusive"]),
                "n_blocks": int(scan_row["block_count"]),
                "start_iso": scan_row["start_iso"],
                "end_iso": scan_row["end_iso"],
                "median_base_fee_gwei": float(scan_row["median_base_fee_gwei"]),
                "mean_base_fee_gwei": float(scan_row["mean_base_fee_gwei"]),
                "base_fee_volatility_log_change_std": float(scan_row["base_fee_volatility"]),
                "median_fee_percentile": float(scan_row["median_base_fee_gwei_percentile"]) * 100.0,
                "volatility_percentile": float(scan_row["base_fee_volatility_percentile"]) * 100.0,
                "fee_quartile": scan_row["fee_quartile"],
                "volatility_quartile": scan_row["volatility_quartile"],
                "profit_over_baseline_percent": profit_mean * 100.0,
                "profit_over_baseline_ci95_half_width_percent": (
                    1.96 * profit_std / math.sqrt(repetitions) * 100.0
                ),
                "exact_optimum_hit_rate_percent": hit_mean * 100.0,
                "exact_optimum_hit_rate_ci95_half_width_percent": (
                    1.96 * hit_std / math.sqrt(repetitions) * 100.0
                ),
                "cost_over_optimum_percent": metric_value(record["metrics"], "cost_over_optimum")
                * 100.0,
                "baseline_cost_over_optimum_percent": metric_value(
                    record["metrics"],
                    "baseline_cost_over_optimum",
                )
                * 100.0,
                "evaluation_job_id": record["evaluation_job_id"],
                "evaluation_target": record["evaluation_target"],
            }
        )
    return sorted(
        rows,
        key=lambda row: (
            str(row["chain"]),
            str(row["selection_metric"]),
            int(row["block_count"]),
            str(row["selection_quartile"]),
            int(row["start_block"]),
        ),
    )


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    if not rows:
        raise ValueError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fields or list(rows[0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


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


def save_figure(fig, filename: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    OBSIDIAN_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".png", ".pdf", ".svg"):
        fig.savefig(FIGURE_DIR / f"{filename}{suffix}", bbox_inches="tight", dpi=220)
    fig.savefig(OBSIDIAN_FIGURE_DIR / f"{filename}.png", bbox_inches="tight", dpi=220)


def format_tick(value: float, _: int) -> str:
    if value == 0:
        return "0"
    if 0.001 <= abs(value) < 10_000:
        return f"{value:g}"
    return f"{value:.0e}".replace("e-0", "e-").replace("e+0", "e")


def log_xlim(values: list[float]) -> tuple[float, float]:
    low = min(value for value in values if value > 0)
    high = max(values)
    log_low = math.log10(low)
    log_high = math.log10(high)
    pad = max((log_high - log_low) * 0.06, 0.08)
    return 10 ** (log_low - pad), 10 ** (log_high + pad)


def log_ticks(values: list[float]) -> list[float]:
    low, high = log_xlim(values)
    start = math.floor(math.log10(low))
    stop = math.ceil(math.log10(high))
    ticks = [
        multiple * (10**power)
        for power in range(start, stop + 1)
        for multiple in (1, 2, 5)
        if low <= multiple * (10**power) <= high
    ]
    return ticks


def sparse_log_ticks(values: list[float]) -> list[float]:
    low, high = log_xlim(values)
    start = math.floor(math.log10(low))
    stop = math.ceil(math.log10(high))
    step = 2 if stop - start > 7 else 1
    return [10**power for power in range(start, stop + 1, step) if low <= 10**power <= high]


def readable_log_ticks(values: list[float], *, max_ticks: int = 7) -> list[float]:
    ticks = log_ticks(values)
    if len(ticks) <= max_ticks:
        return ticks
    return sparse_log_ticks(values)


def log_iqr_bounds(values: list[float], *, multiplier: float = 1.5) -> tuple[float, float]:
    log_values = [math.log10(value) for value in values if value > 0]
    q1, q3 = np.percentile(log_values, [25, 75])
    iqr = float(q3 - q1)
    return 10 ** (float(q1) - multiplier * iqr), 10 ** (float(q3) + multiplier * iqr)


def iqr_bounds(values: list[float], *, multiplier: float = 1.5) -> tuple[float, float]:
    q1, q3 = np.percentile(values, [25, 75])
    iqr = float(q3 - q1)
    return float(q1) - multiplier * iqr, float(q3) + multiplier * iqr


def polygon_fee_level_bulk_split(
    rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], tuple[float, float]]:
    fee_rows = [
        row
        for row in rows
        if row["chain"] == "polygon" and row["selection_metric"] == "fee_level"
    ]
    if len(fee_rows) != 108:
        raise ValueError(f"expected 108 Polygon fee rows, got {len(fee_rows)}")
    bounds = log_iqr_bounds([float(row["median_base_fee_gwei"]) for row in fee_rows])
    low, high = bounds
    bulk: list[dict[str, object]] = []
    outliers: list[dict[str, object]] = []
    for row in fee_rows:
        fee = float(row["median_base_fee_gwei"])
        if low <= fee <= high:
            bulk.append(row)
            continue
        outlier = dict(row)
        outlier["log10_median_base_fee_gwei"] = math.log10(fee)
        outlier["outlier_side"] = "low" if fee < low else "high"
        outlier["outlier_rule"] = POLYGON_FEE_BULK_RULE
        outliers.append(outlier)
    return bulk, outliers, bounds


def polygon_volatility_profit_bulk_split(
    rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], tuple[float, float]]:
    volatility_rows = [
        row
        for row in rows
        if row["chain"] == "polygon" and row["selection_metric"] == "volatility"
    ]
    if len(volatility_rows) != 108:
        raise ValueError(f"expected 108 Polygon volatility rows, got {len(volatility_rows)}")
    bounds = iqr_bounds(
        [float(row["profit_over_baseline_percent"]) for row in volatility_rows],
        multiplier=5.0,
    )
    low, high = bounds
    bulk: list[dict[str, object]] = []
    outliers: list[dict[str, object]] = []
    for row in volatility_rows:
        profit = float(row["profit_over_baseline_percent"])
        if low <= profit <= high:
            bulk.append(row)
            continue
        outlier = dict(row)
        outlier["log10_median_base_fee_gwei"] = math.log10(
            float(row["median_base_fee_gwei"])
        )
        outlier["outlier_side"] = "low" if profit < low else "high"
        outlier["outlier_rule"] = POLYGON_VOLATILITY_PROFIT_BULK_RULE
        outliers.append(outlier)
    return bulk, outliers, bounds


def y_limits(
    values: list[float], errors: list[float], *, floor_zero: bool = False
) -> tuple[float, float]:
    lows = [value - err for value, err in zip(values, errors, strict=True)]
    highs = [value + err for value, err in zip(values, errors, strict=True)]
    low = min(lows)
    high = max(highs)
    pad = max((high - low) * 0.12, 0.12)
    y_low = low - pad
    if floor_zero:
        y_low = max(0.0, y_low)
    return y_low, high + pad


def setup_axis(ax) -> None:
    ax.set_facecolor("#F5F7F2")
    ax.grid(True, color="#FFFFFF", linewidth=0.95)
    ax.grid(True, which="minor", color="#FFFFFF", linewidth=0.45, alpha=0.7)
    ax.axhline(0, color="#333333", linewidth=0.7, alpha=0.58)


def quartile_handles() -> list[plt.Line2D]:
    return [
        plt.Line2D(
            [],
            [],
            marker="o",
            linestyle="",
            color=QUARTILE_COLORS[quartile],
            label=label,
        )
        for quartile, label in QUARTILE_LABELS.items()
    ]


def scatter_points(
    ax,
    rows: list[dict[str, object]],
    *,
    x_key: str,
    y_key: str,
    y_ci_key: str,
) -> None:
    for quartile in ("q1", "q2", "q3", "q4"):
        group = [row for row in rows if row["selection_quartile"] == quartile]
        if not group:
            continue
        xs = [float(row[x_key]) for row in group]
        ys = [float(row[y_key]) for row in group]
        yerr = [float(row[y_ci_key]) for row in group]
        ax.errorbar(
            xs,
            ys,
            yerr=yerr,
            fmt="none",
            ecolor="#4B5563",
            elinewidth=0.45,
            capsize=1.1,
            alpha=0.22,
            zorder=2,
        )
        ax.scatter(
            xs,
            ys,
            s=31.0,
            c=QUARTILE_COLORS[quartile],
            edgecolors="#222222",
            linewidths=0.34,
            alpha=0.76,
            zorder=3,
        )


def render_chain_scatter(
    *,
    config: ChainConfig,
    rows: list[dict[str, object]],
    selection_metric: str,
    x_key: str,
    y_key: str,
    y_ci_key: str,
    y_label: str,
    title_metric: str,
    filename_suffix: str,
    expected_rows: int = 108,
    title_suffix: str = "",
    sparse_x_ticks: bool = False,
) -> None:
    plot_rows = [row for row in rows if row["selection_metric"] == selection_metric]
    if len(plot_rows) != expected_rows:
        raise ValueError(
            f"{config.chain} {selection_metric}: expected {expected_rows} rows, "
            f"got {len(plot_rows)}"
        )
    xs = [float(row[x_key]) for row in plot_rows]
    ys = [float(row[y_key]) for row in plot_rows]
    yerr = [float(row[y_ci_key]) for row in plot_rows]

    rc_params()
    fig, ax = plt.subplots(figsize=(9.2, 5.45))
    setup_axis(ax)
    scatter_points(ax, plot_rows, x_key=x_key, y_key=y_key, y_ci_key=y_ci_key)

    if x_key == "median_base_fee_gwei":
        ax.set_xscale("log")
        ax.set_xlim(*log_xlim(xs))
        ticks = readable_log_ticks(xs) if sparse_x_ticks else log_ticks(xs)
        ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_tick))
        ax.xaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_xlabel("Median base fee during evaluation window (gwei; log scale)")
        x_title = "median base-fee level"
    else:
        ax.margins(x=0.08)
        ax.set_xlabel("Base-fee volatility (std. dev. of block-to-block log changes)")
        x_title = "base-fee volatility"

    ax.set_ylabel(y_label)
    ax.set_ylim(*y_limits(ys, yerr, floor_zero=y_key == "exact_optimum_hit_rate_percent"))
    ax.set_title(
        f"{config.label} LSTM ({WINDOW_LABEL}): {title_metric} vs {x_title}{title_suffix}",
        loc="left",
        pad=12,
        fontweight="bold",
    )
    fig.legend(
        handles=quartile_handles(),
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.035),
    )
    fig.subplots_adjust(left=0.105, right=0.985, top=0.88, bottom=0.23)
    save_figure(fig, f"{config.figure_prefix}_{filename_suffix}")
    plt.close(fig)


def render_chain_figures(config: ChainConfig, rows: list[dict[str, object]]) -> None:
    sparse_polygon_fee_ticks = config.chain == "polygon"
    render_chain_scatter(
        config=config,
        rows=rows,
        selection_metric="fee_level",
        x_key="median_base_fee_gwei",
        y_key="profit_over_baseline_percent",
        y_ci_key="profit_over_baseline_ci95_half_width_percent",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename_suffix="profit_vs_base_fee",
        sparse_x_ticks=sparse_polygon_fee_ticks,
    )
    render_chain_scatter(
        config=config,
        rows=rows,
        selection_metric="volatility",
        x_key="base_fee_volatility_log_change_std",
        y_key="profit_over_baseline_percent",
        y_ci_key="profit_over_baseline_ci95_half_width_percent",
        y_label="Profit over baseline (%)",
        title_metric="profit",
        filename_suffix="profit_vs_base_fee_volatility",
    )
    render_chain_scatter(
        config=config,
        rows=rows,
        selection_metric="fee_level",
        x_key="median_base_fee_gwei",
        y_key="exact_optimum_hit_rate_percent",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width_percent",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename_suffix="accuracy_vs_base_fee",
        sparse_x_ticks=sparse_polygon_fee_ticks,
    )
    render_chain_scatter(
        config=config,
        rows=rows,
        selection_metric="volatility",
        x_key="base_fee_volatility_log_change_std",
        y_key="exact_optimum_hit_rate_percent",
        y_ci_key="exact_optimum_hit_rate_ci95_half_width_percent",
        y_label="Exact optimum hit rate (%)",
        title_metric="exact optimum hit rate",
        filename_suffix="accuracy_vs_base_fee_volatility",
    )


def render_polygon_fee_level_bulk_figures(rows: list[dict[str, object]]) -> None:
    config = next(config for config in CHAIN_CONFIGS if config.chain == "polygon")
    bulk, outliers, bounds = polygon_fee_level_bulk_split(rows)
    write_csv(
        EXPORT_DIR / "polygon_bhilai_large_lstm_block_count_quartile_fee_level_bulk.csv",
        bulk,
        CSV_FIELDS,
    )
    write_csv(
        EXPORT_DIR / "polygon_bhilai_large_lstm_block_count_quartile_fee_level_outliers.csv",
        outliers,
        OUTLIER_FIELDS,
    )
    title_suffix = " (bulk)"
    for y_key, y_ci_key, y_label, title_metric, suffix in (
        (
            "profit_over_baseline_percent",
            "profit_over_baseline_ci95_half_width_percent",
            "Profit over baseline (%)",
            "profit",
            "profit_vs_base_fee_bulk",
        ),
        (
            "exact_optimum_hit_rate_percent",
            "exact_optimum_hit_rate_ci95_half_width_percent",
            "Exact optimum hit rate (%)",
            "exact optimum hit rate",
            "accuracy_vs_base_fee_bulk",
        ),
    ):
        render_chain_scatter(
            config=config,
            rows=bulk,
            selection_metric="fee_level",
            x_key="median_base_fee_gwei",
            y_key=y_key,
            y_ci_key=y_ci_key,
            y_label=y_label,
            title_metric=title_metric,
            filename_suffix=suffix,
            expected_rows=len(bulk),
            title_suffix=title_suffix,
        )
    print(
        "polygon_fee_level_bulk="
        f"{len(bulk)} outliers={len(outliers)} low={bounds[0]:.12g} high={bounds[1]:.12g}"
    )


def render_cross_chain_profit_facets(
    rows_by_chain: dict[str, list[dict[str, object]]],
    *,
    selection_metric: str,
    x_key: str,
    filename: str,
    title: str = f"LSTM {WINDOW_LABEL} quartile profit comparison",
) -> None:
    rc_params()
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.85), sharey=True)
    for ax, config in zip(axes, CHAIN_CONFIGS, strict=True):
        plot_rows = [
            row
            for row in rows_by_chain[config.chain]
            if row["selection_metric"] == selection_metric
        ]
        setup_axis(ax)
        scatter_points(
            ax,
            plot_rows,
            x_key=x_key,
            y_key="profit_over_baseline_percent",
            y_ci_key="profit_over_baseline_ci95_half_width_percent",
        )
        xs = [float(row[x_key]) for row in plot_rows]
        if x_key == "median_base_fee_gwei":
            ax.set_xscale("log")
            ax.set_xlim(*log_xlim(xs))
            ticks = (
                readable_log_ticks(xs)
                if config.chain in {"polygon", "avalanche"}
                else log_ticks(xs)
            )
            ax.xaxis.set_major_locator(mticker.FixedLocator(ticks))
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(format_tick))
            ax.xaxis.set_minor_formatter(mticker.NullFormatter())
            ax.set_xlabel("Median base fee (gwei; log)")
        else:
            ax.margins(x=0.08)
            if config.chain == "avalanche":
                ax.xaxis.set_major_locator(mticker.MaxNLocator(nbins=4))
                ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
            ax.set_xlabel("Base-fee volatility")
        ax.set_title(config.label, loc="left", fontweight="bold", pad=9)

    all_plot_rows = [
        row
        for rows in rows_by_chain.values()
        for row in rows
        if row["selection_metric"] == selection_metric
    ]
    ys = [float(row["profit_over_baseline_percent"]) for row in all_plot_rows]
    yerr = [float(row["profit_over_baseline_ci95_half_width_percent"]) for row in all_plot_rows]
    axes[0].set_ylim(*y_limits(ys, yerr))
    axes[0].set_ylabel("Profit over baseline (%)")
    fig.suptitle(title, x=0.055, ha="left", fontweight="bold")
    fig.legend(
        handles=quartile_handles(),
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.015),
    )
    fig.subplots_adjust(left=0.065, right=0.99, top=0.83, bottom=0.23, wspace=0.16)
    save_figure(fig, filename)
    plt.close(fig)


def render_cross_chain_bulk_profit_facets(
    rows_by_chain: dict[str, list[dict[str, object]]],
) -> None:
    polygon_rows = rows_by_chain["polygon"]
    fee_bulk, fee_outliers, fee_bounds = polygon_fee_level_bulk_split(polygon_rows)
    volatility_bulk, volatility_outliers, volatility_bounds = polygon_volatility_profit_bulk_split(
        polygon_rows
    )
    write_csv(
        EXPORT_DIR / "polygon_bhilai_large_lstm_block_count_quartile_volatility_profit_bulk.csv",
        volatility_bulk,
        CSV_FIELDS,
    )
    write_csv(
        EXPORT_DIR
        / "polygon_bhilai_large_lstm_block_count_quartile_volatility_profit_outliers.csv",
        volatility_outliers,
        OUTLIER_FIELDS,
    )

    fee_rows_by_chain = dict(rows_by_chain)
    fee_rows_by_chain["polygon"] = fee_bulk
    render_cross_chain_profit_facets(
        fee_rows_by_chain,
        selection_metric="fee_level",
        x_key="median_base_fee_gwei",
        filename="lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee_bulk",
        title=f"LSTM {WINDOW_LABEL} quartile profit comparison (Polygon bulk)",
    )

    volatility_rows_by_chain = dict(rows_by_chain)
    volatility_rows_by_chain["polygon"] = volatility_bulk
    render_cross_chain_profit_facets(
        volatility_rows_by_chain,
        selection_metric="volatility",
        x_key="base_fee_volatility_log_change_std",
        filename="lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee_volatility_bulk",
        title=f"LSTM {WINDOW_LABEL} quartile profit comparison (Polygon bulk)",
    )
    print(
        "cross_chain_polygon_bulk="
        f"fee_keep={len(fee_bulk)} fee_outliers={len(fee_outliers)} "
        f"fee_low={fee_bounds[0]:.12g} fee_high={fee_bounds[1]:.12g} "
        f"volatility_keep={len(volatility_bulk)} "
        f"volatility_profit_outliers={len(volatility_outliers)} "
        f"profit_low={volatility_bounds[0]:.12g} profit_high={volatility_bounds[1]:.12g}"
    )


def mean_ci95(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return math.nan, math.nan, math.nan
    mean = float(np.mean(values))
    if len(values) == 1:
        return mean, mean, mean
    half = 1.96 * float(np.std(values, ddof=1)) / math.sqrt(len(values))
    return mean, mean - half, mean + half


def summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    chain_values = [config.chain for config in CHAIN_CONFIGS] + ["all_chains"]
    for chain in chain_values:
        chain_rows = (
            rows if chain == "all_chains" else [row for row in rows if row["chain"] == chain]
        )
        for selection_metric in ("fee_level", "volatility"):
            metric_rows = [row for row in chain_rows if row["selection_metric"] == selection_metric]
            for quartile in ("q1", "q2", "q3", "q4", "all"):
                group = (
                    metric_rows
                    if quartile == "all"
                    else [row for row in metric_rows if row["selection_quartile"] == quartile]
                )
                if not group:
                    continue
                profit_mean, profit_low, profit_high = mean_ci95(
                    [float(row["profit_over_baseline_percent"]) for row in group]
                )
                acc_mean, acc_low, acc_high = mean_ci95(
                    [float(row["exact_optimum_hit_rate_percent"]) for row in group]
                )
                output.append(
                    {
                        "chain": chain,
                        "selection_metric": selection_metric,
                        "quartile": quartile,
                        "windows": len(group),
                        "mean_profit_percent": profit_mean,
                        "ci95_profit_low_percent": profit_low,
                        "ci95_profit_high_percent": profit_high,
                        "mean_exact_optimum_hit_rate_percent": acc_mean,
                        "ci95_accuracy_low_percent": acc_low,
                        "ci95_accuracy_high_percent": acc_high,
                        "mean_median_base_fee_gwei": float(
                            np.mean([float(row["median_base_fee_gwei"]) for row in group])
                        ),
                        "mean_base_fee_volatility_log_change_std": float(
                            np.mean(
                                [float(row["base_fee_volatility_log_change_std"]) for row in group]
                            )
                        ),
                    }
                )
    return output


def pearson_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    chain_values = [config.chain for config in CHAIN_CONFIGS] + ["all_chains"]
    specs = (
        ("fee_level", "median_base_fee_gwei", "median base fee"),
        ("fee_level", "log10_median_base_fee_gwei", "log10 median base fee"),
        ("volatility", "base_fee_volatility_log_change_std", "base-fee volatility"),
    )
    for chain in chain_values:
        chain_rows = (
            rows if chain == "all_chains" else [row for row in rows if row["chain"] == chain]
        )
        for selection_metric, x_key, x_label in specs:
            group = [row for row in chain_rows if row["selection_metric"] == selection_metric]
            if x_key == "log10_median_base_fee_gwei":
                xs = [math.log10(float(row["median_base_fee_gwei"])) for row in group]
            else:
                xs = [float(row[x_key]) for row in group]
            ys = [float(row["profit_over_baseline_percent"]) for row in group]
            result = stats.pearsonr(xs, ys)
            output.append(
                {
                    "chain": chain,
                    "selection_metric": selection_metric,
                    "x_metric": x_label,
                    "y_metric": "profit_over_baseline_percent",
                    "windows": len(group),
                    "pearson_r": float(result.statistic),
                    "p_value": float(result.pvalue),
                }
            )
    return output


def p_value_text(value: float) -> str:
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def markdown_report(
    correlations: list[dict[str, object]], summaries: list[dict[str, object]]
) -> str:
    config_by_chain = {config.chain: config for config in CHAIN_CONFIGS}
    lines: list[str] = []
    lines.append(f"### 29/06 {WINDOW_LABEL} quartile LSTM results")
    lines.append("")
    lines.append(
        f"{WINDOW_LABEL} quartile rerun: 648 evaluation windows, 216 per chain. "
        f"Each window has exactly {WINDOW_BLOCK_COUNT} contiguous anchor blocks. Each chain has "
        "108 fee-level quartile windows and 108 volatility quartile windows."
    )
    lines.append("")
    lines.append(
        "Figures use only the windows selected for the plotted x-axis: fee-selected "
        "windows for base-fee plots, volatility-selected windows for volatility plots. "
        "Point whiskers are 95% CI over the 50 Poisson replay repetitions."
    )
    lines.append("")
    for config in CHAIN_CONFIGS:
        lines.append(f"#### {config.label}")
        lines.append(f"![[{config.figure_prefix}_profit_vs_base_fee.png]]")
        lines.append(f"![[{config.figure_prefix}_profit_vs_base_fee_volatility.png]]")
        lines.append(f"![[{config.figure_prefix}_accuracy_vs_base_fee.png]]")
        lines.append(f"![[{config.figure_prefix}_accuracy_vs_base_fee_volatility.png]]")
        lines.append("")
    lines.append("#### Cross-chain profit facets")
    lines.append("![[lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee.png]]")
    lines.append("![[lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee_volatility.png]]")
    lines.append("")
    lines.append("#### Pearson correlations")
    lines.append("")
    lines.append("| Chain | X metric | Windows | Pearson r | p-value |")
    lines.append("| --- | --- | ---: | ---: | ---: |")
    for row in correlations:
        chain = str(row["chain"])
        label = "All Chains" if chain == "all_chains" else config_by_chain[chain].label
        lines.append(
            f"| {label} | {row['x_metric']} | {row['windows']} | "
            f"{float(row['pearson_r']):.3f} | {p_value_text(float(row['p_value']))} |"
        )
    lines.append("")
    lines.append("#### Quartile class averages")
    lines.append("")
    lines.append(
        "These CIs are over selected evaluation windows in each quartile class, "
        "not over individual Poisson arrivals."
    )
    lines.append("")
    lines.append(
        "| Chain | Class axis | Quartile | Windows | Mean profit | 95% CI | "
        "Mean accuracy | 95% CI |"
    )
    lines.append("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for row in summaries:
        if row["chain"] == "all_chains" or row["quartile"] == "all":
            continue
        chain = str(row["chain"])
        label = config_by_chain[chain].label
        axis = "base fee" if row["selection_metric"] == "fee_level" else "volatility"
        quartile = str(row["quartile"]).upper()
        profit_ci = (
            f"[{float(row['ci95_profit_low_percent']):.3f}, "
            f"{float(row['ci95_profit_high_percent']):.3f}]"
        )
        accuracy_ci = (
            f"[{float(row['ci95_accuracy_low_percent']):.2f}, "
            f"{float(row['ci95_accuracy_high_percent']):.2f}]"
        )
        lines.append(
            f"| {label} | {axis} | {quartile} | {row['windows']} | "
            f"{float(row['mean_profit_percent']):.3f}% | "
            f"{profit_ci} | "
            f"{float(row['mean_exact_optimum_hit_rate_percent']):.2f}% | "
            f"{accuracy_ci} |"
        )
    lines.append("")
    lines.append("Exports:")
    lines.append(f"- `{EXPORT_DIR / 'lstm_36s_block_count_quartile_joined.csv'}`")
    lines.append(f"- `{EXPORT_DIR / 'lstm_36s_block_count_quartile_correlations.csv'}`")
    lines.append(f"- `{EXPORT_DIR / 'lstm_36s_block_count_quartile_summary.csv'}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    rows = joined_rows()
    write_csv(EXPORT_DIR / "lstm_36s_block_count_quartile_joined.csv", rows, CSV_FIELDS)

    rows_by_chain = {
        config.chain: [row for row in rows if row["chain"] == config.chain]
        for config in CHAIN_CONFIGS
    }
    for config in CHAIN_CONFIGS:
        write_csv(
            EXPORT_DIR / f"{config.figure_prefix}_joined.csv",
            rows_by_chain[config.chain],
            CSV_FIELDS,
        )
        render_chain_figures(config, rows_by_chain[config.chain])
    render_polygon_fee_level_bulk_figures(rows)

    render_cross_chain_profit_facets(
        rows_by_chain,
        selection_metric="fee_level",
        x_key="median_base_fee_gwei",
        filename="lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee",
    )
    render_cross_chain_profit_facets(
        rows_by_chain,
        selection_metric="volatility",
        x_key="base_fee_volatility_log_change_std",
        filename="lstm_36s_block_count_quartile_cross_chain_profit_vs_base_fee_volatility",
    )
    render_cross_chain_bulk_profit_facets(rows_by_chain)

    correlations = pearson_rows(rows)
    summaries = summary_rows(rows)
    write_csv(EXPORT_DIR / "lstm_36s_block_count_quartile_correlations.csv", correlations)
    write_csv(EXPORT_DIR / "lstm_36s_block_count_quartile_summary.csv", summaries)

    report = markdown_report(correlations, summaries)
    (EXPORT_DIR / "lstm_36s_block_count_quartile_report.md").write_text(report, encoding="utf-8")

    print(f"joined_rows={len(rows)}")
    for config in CHAIN_CONFIGS:
        chain_rows = rows_by_chain[config.chain]
        fee_rows = sum(1 for row in chain_rows if row["selection_metric"] == "fee_level")
        volatility_rows = sum(1 for row in chain_rows if row["selection_metric"] == "volatility")
        print(
            f"{config.chain}: total={len(chain_rows)} fee={fee_rows} volatility={volatility_rows}"
        )
    print(f"correlations={EXPORT_DIR / 'lstm_36s_block_count_quartile_correlations.csv'}")
    print(f"summary={EXPORT_DIR / 'lstm_36s_block_count_quartile_summary.csv'}")
    print(f"report={EXPORT_DIR / 'lstm_36s_block_count_quartile_report.md'}")
    print(f"figures={FIGURE_DIR}")
    print(f"obsidian={OBSIDIAN_FIGURE_DIR}")


if __name__ == "__main__":
    main()
