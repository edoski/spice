"""Throwaway terminal shell for the census-descriptor logic prototype."""

from __future__ import annotations

import argparse

from census_descriptor_logic import (
    aggregate,
    fee_level,
    fixture,
    outcome_selected_subset,
    representative_window_subset,
    signed_one_block_log_fee_change,
    value_quantile_bins,
)


def percent(value: float) -> str:
    return f"{100 * value:+.3f}%"


def line(name: str, origins) -> str:
    totals = aggregate(tuple(origins))
    return (
        f"{name:<24} n={totals.origins:>2}  "
        f"savings={percent(totals.savings_ratio):>9}  "
        f"opportunity={percent(totals.opportunity_ratio):>9}  "
        f"regret={percent(totals.regret_ratio):>9}"
    )


def frame(descriptor: str) -> str:
    origins = fixture()
    if descriptor == "fee":
        values = tuple(fee_level(origin) for origin in origins)
        descriptor_label = "raw base_fee_per_gas[h] of latest closed parent"
    else:
        values = tuple(signed_one_block_log_fee_change(origin) for origin in origins)
        descriptor_label = "signed log(base_fee[h] / base_fee[h-1])"

    binned = value_quantile_bins(origins, values, 4)
    recombined = tuple(origin for group in binned.groups for origin in group)
    rows = [
        "\x1b[1mPROTOTYPE — exhaustive census conditioning\x1b[0m",
        f"\x1b[2mx-axis: {descriptor_label}\x1b[0m",
        f"\x1b[2mnearest-rank cutpoints: {binned.cutpoints}\x1b[0m",
        "",
        line("full census", origins),
    ]
    rows.extend(
        line(f"descriptor quartile {index + 1}", group) for index, group in enumerate(binned.groups)
    )
    rows.extend(
        [
            line("bins recombined", recombined),
            "",
            line("representative windows", representative_window_subset(origins)),
            line("OUTCOME-PICKED (invalid)", outcome_selected_subset(origins)),
            "",
            "\x1b[2mBins retain every origin and exactly recover the full raw totals.",
            "Representative windows change the population; outcome-picking is "
            "cherry-picking.\x1b[0m",
        ]
    )
    return "\n".join(rows)


def interactive() -> None:
    descriptor = "fee"
    while True:
        print("\033[2J\033[H", end="")
        print(frame(descriptor))
        print("\n[f] parent fee  [r] signed one-block log change  [q] quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        if choice == "f":
            descriptor = "fee"
        elif choice == "r":
            descriptor = "log_change"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        print(frame("fee"))
        print("\n" + "=" * 88 + "\n")
        print(frame("log_change"))
        return
    interactive()


if __name__ == "__main__":
    main()
