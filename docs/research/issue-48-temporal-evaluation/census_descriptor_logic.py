"""PROTOTYPE: full-census conditioning without evaluation-window selection.

Question: can direct one-block per-origin descriptors produce readable strata while
preserving the exact full-census accounting?
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from math import ceil, log


@dataclass(frozen=True)
class Origin:
    block: int
    previous_parent_fee: int
    parent_fee: int
    immediate_fee: int
    selected_fee: int
    hindsight_fee: int


@dataclass(frozen=True)
class Totals:
    origins: int
    savings: int
    opportunity: int
    regret: int
    immediate: int

    @property
    def savings_ratio(self) -> float:
        return self.savings / self.immediate

    @property
    def opportunity_ratio(self) -> float:
        return self.opportunity / self.immediate

    @property
    def regret_ratio(self) -> float:
        return self.regret / self.immediate


def aggregate(origins: tuple[Origin, ...]) -> Totals:
    return Totals(
        origins=len(origins),
        savings=sum(origin.immediate_fee - origin.selected_fee for origin in origins),
        opportunity=sum(origin.immediate_fee - origin.hindsight_fee for origin in origins),
        regret=sum(origin.selected_fee - origin.hindsight_fee for origin in origins),
        immediate=sum(origin.immediate_fee for origin in origins),
    )


@dataclass(frozen=True)
class ValueBins:
    groups: tuple[tuple[Origin, ...], ...]
    cutpoints: tuple[float, ...]


def fee_level(origin: Origin) -> float:
    """Raw fee of the latest closed parent h."""

    return float(origin.parent_fee)


def signed_one_block_log_fee_change(origin: Origin) -> float:
    """Signed log(base_fee[h] / base_fee[h-1]), known at origin h."""

    return log(origin.parent_fee / origin.previous_parent_fee)


def value_quantile_bins(
    origins: tuple[Origin, ...],
    values: tuple[float, ...],
    count: int,
) -> ValueBins:
    """Nearest-rank value bins that retain every origin and keep ties together."""

    ordered_values = sorted(values)
    cutpoints = tuple(
        ordered_values[ceil(len(ordered_values) * part / count) - 1] for part in range(1, count)
    )
    bins: list[list[Origin]] = [[] for _ in range(count)]
    for value, origin in zip(values, origins, strict=True):
        index = bisect_left(cutpoints, value)
        bins[index].append(origin)
    return ValueBins(
        groups=tuple(tuple(group) for group in bins),
        cutpoints=cutpoints,
    )


def representative_window_subset(
    origins: tuple[Origin, ...], window_size: int = 3
) -> tuple[Origin, ...]:
    """Legacy-shaped subset: retain only lowest/highest-median contiguous windows."""

    windows = tuple(
        origins[start : start + window_size]
        for start in range(0, len(origins) - window_size + 1, window_size)
    )
    ordered = sorted(
        windows,
        key=lambda window: sum(origin.parent_fee for origin in window) / len(window),
    )
    return ordered[0] + ordered[-1]


def outcome_selected_subset(origins: tuple[Origin, ...]) -> tuple[Origin, ...]:
    """Deliberately invalid contrast: choose origins after reading economic outcomes."""

    return tuple(origin for origin in origins if origin.immediate_fee - origin.selected_fee > 0)


def fixture() -> tuple[Origin, ...]:
    parent_fees = (80, 82, 79, 85, 90, 105, 98, 120, 115, 150, 130, 170, 160, 210, 180)
    immediate = (92, 110, 101, 125, 119, 155, 136, 176, 165, 218, 188)
    selected = (88, 113, 96, 133, 112, 144, 143, 160, 171, 205, 196)
    hindsight = (84, 102, 94, 116, 109, 138, 128, 154, 158, 198, 180)
    return tuple(
        Origin(
            block=1_000 + index,
            previous_parent_fee=parent_fees[index + 3],
            parent_fee=parent_fees[index + 4],
            immediate_fee=immediate[index],
            selected_fee=selected[index],
            hindsight_fee=hindsight[index],
        )
        for index in range(len(immediate))
    )
