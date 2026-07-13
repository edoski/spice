"""Drive the issue-48 hand fixture and inspect every accounting state."""

from __future__ import annotations

import argparse
import sys
from fractions import Fraction

from fixture_semantics import (
    Evaluation,
    Metric,
    Origin,
    ServingAttempt,
    Weighting,
    evaluate,
    summarize_serving_availability,
)

ACTION_COUNT = 3
WINDOW_END_TIMESTAMP_S = 60


def hand_fixture() -> tuple[Origin, ...]:
    """Five rolling origins with ordinary minima, a duplicate timestamp, and one exclusion."""

    return (
        Origin(
            "A",
            parent_block=100,
            parent_timestamp_s=0,
            candidate_base_fees_per_gas=(100, 80, 90),
            candidate_timestamps_s=(10, 10, 30),
            selected_k=1,
            gas_units=2,
        ),
        Origin(
            "B",
            parent_block=101,
            parent_timestamp_s=10,
            candidate_base_fees_per_gas=(80, 90, 100),
            candidate_timestamps_s=(10, 30, 45),
            selected_k=0,
            gas_units=10,
        ),
        Origin(
            "C",
            parent_block=102,
            parent_timestamp_s=10,
            candidate_base_fees_per_gas=(80, 90, 70),
            candidate_timestamps_s=(30, 45, 50),
            selected_k=2,
            gas_units=1,
        ),
        Origin(
            "D",
            parent_block=103,
            parent_timestamp_s=30,
            candidate_base_fees_per_gas=(90, 70, 100),
            candidate_timestamps_s=(45, 50, 60),
            selected_k=2,
            gas_units=1,
        ),
        Origin(
            "E",
            parent_block=104,
            parent_timestamp_s=45,
            structural_exclusion_reason="symbolic incomplete causal span (#47-owned)",
        ),
    )


def run(weighting: Weighting) -> Evaluation:
    return evaluate(
        hand_fixture(),
        action_count=ACTION_COUNT,
        weighting=weighting,
        window_end_timestamp_s=(
            WINDOW_END_TIMESTAMP_S if weighting == "wall_clock_latest_parent" else None
        ),
    )


def check_hand_fixture() -> None:
    block = run("block_opportunity")
    wall = run("wall_clock_latest_parent")

    assert block.origin_weights == (Fraction(1),) * 5
    assert wall.origin_weights == tuple(map(Fraction, (10, 0, 20, 15, 15)))
    assert block.structural_metrics["structural_eligibility_weight_rate"].value == Fraction(4, 5)
    assert wall.structural_metrics["structural_eligibility_weight_rate"].value == Fraction(3, 4)

    block_metrics = block.decision_metrics
    assert block_metrics["base_fee_savings_per_gas_mean"].value == Fraction(5)
    assert block_metrics["hindsight_opportunity_gap_per_gas_mean"].value == Fraction(25, 2)
    assert block_metrics["hindsight_regret_per_gas_mean"].value == Fraction(15, 2)
    assert block_metrics["gas_weighted_base_fee_savings_ratio_of_sums"].value == Fraction(4, 117)
    assert block_metrics["gas_weighted_hindsight_opportunity_ratio_of_sums"].value == Fraction(
        7, 117
    )
    assert block_metrics["gas_weighted_hindsight_regret_ratio_of_sums"].value == Fraction(3, 117)
    assert block_metrics["mean_origin_base_fee_savings_fraction"].value == Fraction(77, 1440)
    assert block_metrics["harmful_action_rate"].value == Fraction(1, 4)
    assert block_metrics["mean_wait_block_opportunities"].value == Fraction(5, 4)
    assert block_metrics["mean_broadcast_wait_seconds"].value == Fraction(65, 4)
    assert block_metrics["earliest_hindsight_label_accuracy"].value == Fraction(3, 4)

    wall_metrics = wall.decision_metrics
    assert wall_metrics["base_fee_savings_per_gas_mean"].value == Fraction(50, 9)
    assert wall_metrics["gas_weighted_base_fee_savings_ratio_of_sums"].value == Fraction(1, 11)
    assert wall_metrics["harmful_action_rate"].value == Fraction(1, 3)
    assert wall_metrics["mean_broadcast_wait_seconds"].value == Fraction(220, 9)
    assert wall_metrics["earliest_hindsight_label_accuracy"].value == Fraction(2, 3)

    for result in (block, wall):
        metrics = result.decision_metrics
        assert defined_value(metrics["base_fee_savings_per_gas_mean"]) + defined_value(
            metrics["hindsight_regret_per_gas_mean"]
        ) == defined_value(metrics["hindsight_opportunity_gap_per_gas_mean"])
        assert defined_value(
            metrics["gas_weighted_base_fee_savings_ratio_of_sums"]
        ) + defined_value(metrics["gas_weighted_hindsight_regret_ratio_of_sums"]) == defined_value(
            metrics["gas_weighted_hindsight_opportunity_ratio_of_sums"]
        )

    invalid_origin = Origin(
        "missing-action",
        1,
        0,
        candidate_base_fees_per_gas=(1, 1, 1),
        candidate_timestamps_s=(1, 2, 3),
        selected_k=None,
    )
    try:
        evaluate(
            (invalid_origin,),
            action_count=3,
            weighting="block_opportunity",
        )
    except ValueError as error:
        assert "offline evaluation invalid" in str(error)
    else:
        raise AssertionError("eligible missing action must invalidate offline scoring")


def serving_fixture() -> tuple[ServingAttempt, ...]:
    return (
        ServingAttempt("served", True, True, True, True, True),
        ServingAttempt("no-snapshot", False, False, False, False, False),
        ServingAttempt("no-inference", True, False, False, False, False),
        ServingAttempt("missed-opportunity", True, True, False, False, False),
        ServingAttempt("no-broadcast", True, True, True, False, False),
        ServingAttempt("no-receipt-observation", True, True, True, True, False),
    )


def check_serving_fixture() -> None:
    summary = summarize_serving_availability(serving_fixture())
    expected = (
        Fraction(5, 6),
        Fraction(4, 5),
        Fraction(3, 4),
        Fraction(2, 3),
        Fraction(1, 2),
    )
    assert tuple(metric.value for metric in summary.stage_metrics.values()) == expected


def ratio_examples() -> tuple[Evaluation, Evaluation]:
    finite = evaluate(
        (
            Origin(
                "cheap",
                1,
                0,
                candidate_base_fees_per_gas=(1, 0),
                candidate_timestamps_s=(1, 2),
                selected_k=1,
            ),
            Origin(
                "expensive",
                2,
                1,
                candidate_base_fees_per_gas=(9, 10),
                candidate_timestamps_s=(2, 3),
                selected_k=0,
            ),
        ),
        action_count=2,
        weighting="block_opportunity",
    )
    zero = evaluate(
        (
            Origin(
                "zero",
                1,
                0,
                candidate_base_fees_per_gas=(0, 1),
                candidate_timestamps_s=(1, 2),
                selected_k=0,
            ),
        ),
        action_count=2,
        weighting="block_opportunity",
    )

    assert finite.decision_metrics["mean_origin_base_fee_savings_fraction"].value == Fraction(1, 2)
    assert finite.decision_metrics["gas_weighted_base_fee_savings_ratio_of_sums"].value == Fraction(
        1, 10
    )
    assert zero.decision_metrics["gas_weighted_base_fee_savings_ratio_of_sums"].value is None
    assert zero.decision_metrics["mean_origin_base_fee_savings_fraction"].value is None
    return finite, zero


def format_metric(metric: Metric) -> str:
    value = metric.value
    rendered_value = "undefined" if value is None else f"{value} ({float(value):.6f})"
    return (
        f"{rendered_value}; numerator={metric.numerator}; "
        f"denominator={metric.denominator}; unit={metric.unit}"
    )


def defined_value(metric: Metric) -> Fraction:
    value = metric.value
    if value is None:
        raise AssertionError("fixture expected a defined metric")
    return value


def render(result: Evaluation) -> str:
    origins = hand_fixture()
    lines = [
        f"WEIGHTING: {result.weighting}",
        f"K/action count: {result.action_count}",
        (
            "Counts: "
            f"candidate={result.candidate_origin_count}, "
            f"structurally eligible/scored={result.structurally_eligible_origin_count}"
        ),
        "",
        "DECLARED ORIGINS",
    ]
    for origin, weight in zip(origins, result.origin_weights, strict=True):
        if origin.structural_exclusion_reason is not None:
            status = f"excluded: {origin.structural_exclusion_reason}"
        else:
            status = f"selected k={origin.selected_k}"
        lines.append(
            f"  {origin.origin_id}: h={origin.parent_block}, "
            f"time={origin.parent_timestamp_s}, weight={weight}, {status}"
        )

    lines.extend(("", "EVALUATED ORIGINS"))
    for row in result.per_origin:
        lines.append(
            f"  {row.origin_id}: target=h+1+k={row.target_block}, "
            f"fees B/R/O={row.immediate_base_fee_per_gas}/"
            f"{row.selected_base_fee_per_gas}/"
            f"{row.hindsight_best_base_fee_per_gas}, "
            f"S/G/R={row.base_fee_savings_per_gas}/"
            f"{row.hindsight_opportunity_gap_per_gas}/"
            f"{row.hindsight_regret_per_gas}, "
            f"earliest-label k={row.earliest_hindsight_k}, "
            f"earliest-label-hit={row.earliest_hindsight_label_hit}, "
            f"harmful={row.harmful_action}, wait={row.selected_k} blocks/"
            f"{row.broadcast_wait_s}s-to-broadcast-trigger"
        )

    lines.extend(("", "STRUCTURAL ELIGIBILITY"))
    lines.extend(
        f"  {name}: {format_metric(metric)}" for name, metric in result.structural_metrics.items()
    )
    lines.extend(("", "DECISION METRICS"))
    lines.extend(
        f"  {name}: {format_metric(metric)}" for name, metric in result.decision_metrics.items()
    )
    return "\n".join(lines)


def render_serving_fixture() -> str:
    summary = summarize_serving_availability(serving_fixture())
    lines = [
        "SEPARATE SERVING AVAILABILITY FUNNEL",
        f"Attempts: {summary.attempt_count}",
        "These conditional counts never alter an offline model-score denominator.",
    ]
    lines.extend(
        f"  {name}: {format_metric(metric)}" for name, metric in summary.stage_metrics.items()
    )
    return "\n".join(lines)


def render_ratio_examples() -> str:
    finite, zero = ratio_examples()
    finite_metrics = finite.decision_metrics
    zero_metrics = zero.decision_metrics
    return "\n".join(
        (
            "FINITE-RATIO CHECK",
            "  Equal-origin one-request expected ratio: "
            + format_metric(finite_metrics["mean_origin_base_fee_savings_fraction"]),
            "  Long-run ratio of expected sums: "
            + format_metric(finite_metrics["gas_weighted_base_fee_savings_ratio_of_sums"]),
            "  These are 1/2 and 1/10: different estimands.",
            "",
            "ZERO-DENOMINATOR CHECK",
            "  Aggregate base-fee ratio: "
            + format_metric(zero_metrics["gas_weighted_base_fee_savings_ratio_of_sums"]),
            "  Mean origin ratio: "
            + format_metric(zero_metrics["mean_origin_base_fee_savings_fraction"]),
        )
    )


def interactive() -> None:
    weighting = "block_opportunity"
    while True:
        print("\033[2J\033[H", end="")
        print(render(run(weighting)))
        print("\n" + render_serving_fixture())
        print("\n[b] block weights  [w] wall-clock weights  [r] ratio cases  [q] quit")
        key = input("> ").strip().lower()[:1]
        if key == "q":
            return
        if key == "b":
            weighting = "block_opportunity"
        elif key == "w":
            weighting = "wall_clock_latest_parent"
        elif key == "r":
            print("\033[2J\033[H", end="")
            print(render_ratio_examples())
            input("\n[enter] return")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="switch estimands in a one-screen terminal loop",
    )
    args = parser.parse_args()
    check_hand_fixture()
    check_serving_fixture()
    ratio_examples()
    if args.interactive and sys.stdin.isatty():
        interactive()
        return
    print(render(run("block_opportunity")))
    print("\n" + "=" * 88 + "\n")
    print(render(run("wall_clock_latest_parent")))
    print("\n" + "=" * 88 + "\n")
    print(render_ratio_examples())
    print("\n" + "=" * 88 + "\n")
    print(render_serving_fixture())


if __name__ == "__main__":
    main()
