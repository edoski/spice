"""PROTOTYPE: exact temporal decision accounting for issue 48.

The portable interface is ``evaluate``. It assumes another module has already
decided structural eligibility and supplied a complete fixed-K outcome span.
It performs no I/O and makes no preprocessing or feature-span decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

Weighting = Literal["block_opportunity", "wall_clock_latest_parent"]


@dataclass(frozen=True, slots=True)
class Origin:
    """One declared decision after closed parent ``h``.

    Candidate tuple position ``k`` always denotes target ``h + 1 + k``. Fees
    are raw integer base-fee units per gas. Candidate timestamps describe
    historical target rows; they are not transaction inclusion timestamps.
    """

    origin_id: str
    parent_block: int
    parent_timestamp_s: int
    candidate_base_fees_per_gas: tuple[int, ...] = ()
    candidate_timestamps_s: tuple[int, ...] = ()
    selected_k: int | None = None
    gas_units: int = 1
    structural_exclusion_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ServingAttempt:
    """One serving availability trace, kept outside offline model scoring."""

    attempt_id: str
    snapshot_available: bool
    inference_available: bool
    action_opportunity_available: bool
    broadcast_submitted: bool
    receipt_observed: bool


@dataclass(frozen=True, slots=True)
class Metric:
    """An auditable numerator/denominator pair.

    ``value`` is ``None`` when the denominator is zero. Undefined ratios never
    become zero, infinity, or NaN.
    """

    numerator: Fraction
    denominator: Fraction
    unit: str

    @property
    def value(self) -> Fraction | None:
        if self.denominator == 0:
            return None
        return self.numerator / self.denominator


@dataclass(frozen=True, slots=True)
class OriginAccounting:
    origin_id: str
    weight: Fraction
    parent_block: int
    target_block: int
    selected_k: int
    immediate_base_fee_per_gas: int
    selected_base_fee_per_gas: int
    hindsight_best_base_fee_per_gas: int
    earliest_hindsight_k: int
    base_fee_savings_per_gas: int
    hindsight_opportunity_gap_per_gas: int
    hindsight_regret_per_gas: int
    harmful_action: bool
    earliest_hindsight_label_hit: bool
    broadcast_wait_s: int
    gas_units: int


@dataclass(frozen=True, slots=True)
class Evaluation:
    weighting: Weighting
    action_count: int
    origin_weights: tuple[Fraction, ...]
    candidate_origin_count: int
    structurally_eligible_origin_count: int
    structural_metrics: dict[str, Metric]
    decision_metrics: dict[str, Metric]
    per_origin: tuple[OriginAccounting, ...]


@dataclass(frozen=True, slots=True)
class ServingAvailability:
    attempt_count: int
    stage_metrics: dict[str, Metric]


def evaluate(
    origins: tuple[Origin, ...],
    *,
    action_count: int,
    weighting: Weighting,
    window_end_timestamp_s: int | None = None,
) -> Evaluation:
    """Account for a fixed-K decision set under one explicit estimand.

    ``block_opportunity`` gives every declared origin weight one.
    ``wall_clock_latest_parent`` gives origin ``i`` the half-open interval
    ``[parent_time_i, parent_time_{i+1})`` and the final origin the interval to
    ``window_end_timestamp_s``. With duplicate coarse timestamps, earlier tied
    parents receive zero exposure and the last tied parent receives the later
    interval. That is an explicit latest-parent lookup rule, not recovered
    sub-second truth.
    """

    _validate(origins, action_count=action_count)
    weights = _weights(
        origins,
        weighting=weighting,
        window_end_timestamp_s=window_end_timestamp_s,
    )

    eligible = [
        (origin, weight)
        for origin, weight in zip(origins, weights, strict=True)
        if origin.structural_exclusion_reason is None
    ]
    accounted = tuple(_account_origin(origin, weight) for origin, weight in eligible)

    candidate_weight = sum(weights, Fraction())
    eligible_weight = sum((weight for _, weight in eligible), Fraction())
    structural_metrics = {
        "structural_eligibility_weight_rate": Metric(eligible_weight, candidate_weight, "fraction"),
    }

    return Evaluation(
        weighting=weighting,
        action_count=action_count,
        origin_weights=weights,
        candidate_origin_count=len(origins),
        structurally_eligible_origin_count=len(eligible),
        structural_metrics=structural_metrics,
        decision_metrics=_decision_metrics(accounted),
        per_origin=accounted,
    )


def summarize_serving_availability(
    attempts: tuple[ServingAttempt, ...],
) -> ServingAvailability:
    """Count a serving funnel without changing any offline model denominator.

    Each stage is conditional on the preceding stage. Receipt observation is a
    serving outcome, not proof that an intended target opportunity guaranteed
    transaction inclusion.
    """

    for attempt in attempts:
        stages = (
            attempt.snapshot_available,
            attempt.inference_available,
            attempt.action_opportunity_available,
            attempt.broadcast_submitted,
            attempt.receipt_observed,
        )
        if any(later and not earlier for earlier, later in zip(stages, stages[1:], strict=False)):
            raise ValueError(
                f"{attempt.attempt_id}: downstream serving stage succeeded after a failed stage"
            )

    snapshot = [attempt for attempt in attempts if attempt.snapshot_available]
    inference = [attempt for attempt in snapshot if attempt.inference_available]
    opportunity = [attempt for attempt in inference if attempt.action_opportunity_available]
    broadcast = [attempt for attempt in opportunity if attempt.broadcast_submitted]
    receipt = [attempt for attempt in broadcast if attempt.receipt_observed]
    return ServingAvailability(
        attempt_count=len(attempts),
        stage_metrics={
            "snapshot_availability_rate": Metric(
                Fraction(len(snapshot)), Fraction(len(attempts)), "fraction"
            ),
            "inference_availability_given_snapshot_rate": Metric(
                Fraction(len(inference)), Fraction(len(snapshot)), "fraction"
            ),
            "action_opportunity_availability_given_inference_rate": Metric(
                Fraction(len(opportunity)), Fraction(len(inference)), "fraction"
            ),
            "broadcast_submission_given_action_opportunity_rate": Metric(
                Fraction(len(broadcast)), Fraction(len(opportunity)), "fraction"
            ),
            "receipt_observation_given_broadcast_rate": Metric(
                Fraction(len(receipt)), Fraction(len(broadcast)), "fraction"
            ),
        },
    )


def _account_origin(origin: Origin, weight: Fraction) -> OriginAccounting:
    assert origin.selected_k is not None
    selected_k = origin.selected_k
    fees = origin.candidate_base_fees_per_gas
    best_fee = min(fees)
    earliest_hindsight_k = fees.index(best_fee)
    baseline_fee = fees[0]
    selected_fee = fees[selected_k]
    savings = baseline_fee - selected_fee
    opportunity = baseline_fee - best_fee
    regret = selected_fee - best_fee
    assert savings + regret == opportunity

    return OriginAccounting(
        origin_id=origin.origin_id,
        weight=weight,
        parent_block=origin.parent_block,
        target_block=origin.parent_block + 1 + selected_k,
        selected_k=selected_k,
        immediate_base_fee_per_gas=baseline_fee,
        selected_base_fee_per_gas=selected_fee,
        hindsight_best_base_fee_per_gas=best_fee,
        earliest_hindsight_k=earliest_hindsight_k,
        base_fee_savings_per_gas=savings,
        hindsight_opportunity_gap_per_gas=opportunity,
        hindsight_regret_per_gas=regret,
        harmful_action=selected_fee > baseline_fee,
        earliest_hindsight_label_hit=selected_k == earliest_hindsight_k,
        broadcast_wait_s=(
            0
            if selected_k == 0
            else origin.candidate_timestamps_s[selected_k - 1] - origin.parent_timestamp_s
        ),
        gas_units=origin.gas_units,
    )


def _decision_metrics(rows: tuple[OriginAccounting, ...]) -> dict[str, Metric]:
    total_weight = sum((row.weight for row in rows), Fraction())

    savings = sum((row.weight * row.base_fee_savings_per_gas for row in rows), Fraction())
    opportunity = sum(
        (row.weight * row.hindsight_opportunity_gap_per_gas for row in rows),
        Fraction(),
    )
    regret = sum((row.weight * row.hindsight_regret_per_gas for row in rows), Fraction())
    assert savings + regret == opportunity

    baseline_amount = sum(
        (row.weight * row.gas_units * row.immediate_base_fee_per_gas for row in rows),
        Fraction(),
    )
    gas_weighted_savings = sum(
        (row.weight * row.gas_units * row.base_fee_savings_per_gas for row in rows),
        Fraction(),
    )
    gas_weighted_opportunity = sum(
        (row.weight * row.gas_units * row.hindsight_opportunity_gap_per_gas for row in rows),
        Fraction(),
    )
    gas_weighted_regret = sum(
        (row.weight * row.gas_units * row.hindsight_regret_per_gas for row in rows),
        Fraction(),
    )
    assert gas_weighted_savings + gas_weighted_regret == gas_weighted_opportunity

    positive_baseline_rows = [row for row in rows if row.immediate_base_fee_per_gas > 0]
    finite_ratio_weight = sum((row.weight for row in positive_baseline_rows), Fraction())
    finite_ratio_sum = sum(
        (
            row.weight
            * Fraction(
                row.base_fee_savings_per_gas,
                row.immediate_base_fee_per_gas,
            )
            for row in positive_baseline_rows
        ),
        Fraction(),
    )

    return {
        "base_fee_savings_per_gas_mean": Metric(savings, total_weight, "base-fee units/gas"),
        "hindsight_opportunity_gap_per_gas_mean": Metric(
            opportunity, total_weight, "base-fee units/gas"
        ),
        "hindsight_regret_per_gas_mean": Metric(regret, total_weight, "base-fee units/gas"),
        "gas_weighted_base_fee_savings_ratio_of_sums": Metric(
            gas_weighted_savings, baseline_amount, "fraction"
        ),
        "gas_weighted_hindsight_opportunity_ratio_of_sums": Metric(
            gas_weighted_opportunity, baseline_amount, "fraction"
        ),
        "gas_weighted_hindsight_regret_ratio_of_sums": Metric(
            gas_weighted_regret, baseline_amount, "fraction"
        ),
        "mean_origin_base_fee_savings_fraction": Metric(
            finite_ratio_sum, finite_ratio_weight, "fraction"
        ),
        "harmful_action_rate": Metric(
            sum(
                (row.weight for row in rows if row.harmful_action),
                Fraction(),
            ),
            total_weight,
            "fraction",
        ),
        "mean_wait_block_opportunities": Metric(
            sum(
                (row.weight * row.selected_k for row in rows),
                Fraction(),
            ),
            total_weight,
            "blocks after k0",
        ),
        "mean_broadcast_wait_seconds": Metric(
            sum(
                (row.weight * row.broadcast_wait_s for row in rows),
                Fraction(),
            ),
            total_weight,
            "trace seconds until broadcast trigger",
        ),
        "earliest_hindsight_label_accuracy": Metric(
            sum(
                (row.weight for row in rows if row.earliest_hindsight_label_hit),
                Fraction(),
            ),
            total_weight,
            "fraction",
        ),
    }


def _weights(
    origins: tuple[Origin, ...],
    *,
    weighting: Weighting,
    window_end_timestamp_s: int | None,
) -> tuple[Fraction, ...]:
    if weighting == "block_opportunity":
        return tuple(Fraction(1) for _ in origins)
    if weighting != "wall_clock_latest_parent":
        raise ValueError(f"unknown weighting: {weighting}")
    if window_end_timestamp_s is None:
        raise ValueError("wall-clock weighting requires window_end_timestamp_s")
    if window_end_timestamp_s < origins[-1].parent_timestamp_s:
        raise ValueError("window end precedes the final parent timestamp")

    ends = [origin.parent_timestamp_s for origin in origins[1:]]
    ends.append(window_end_timestamp_s)
    return tuple(
        Fraction(end - origin.parent_timestamp_s) for origin, end in zip(origins, ends, strict=True)
    )


def _validate(origins: tuple[Origin, ...], *, action_count: int) -> None:
    if not origins:
        raise ValueError("at least one origin is required")
    if action_count <= 0:
        raise ValueError("action_count must be positive")

    for previous, current in zip(origins, origins[1:], strict=False):
        if current.parent_block <= previous.parent_block:
            raise ValueError("origins must have strictly increasing parent blocks")
        if current.parent_timestamp_s < previous.parent_timestamp_s:
            raise ValueError("parent timestamps must be nondecreasing")

    for origin in origins:
        if origin.gas_units < 0:
            raise ValueError(f"{origin.origin_id}: gas_units must be nonnegative")
        if origin.structural_exclusion_reason is not None:
            if origin.selected_k is not None:
                raise ValueError(
                    f"{origin.origin_id}: structurally excluded origin has a selection"
                )
            continue

        if len(origin.candidate_base_fees_per_gas) != action_count:
            raise ValueError(
                f"{origin.origin_id}: eligible origin lacks the complete fixed-K fee span"
            )
        if len(origin.candidate_timestamps_s) != action_count:
            raise ValueError(
                f"{origin.origin_id}: eligible origin lacks the complete fixed-K time span"
            )
        if any(fee < 0 for fee in origin.candidate_base_fees_per_gas):
            raise ValueError(f"{origin.origin_id}: base fees must be nonnegative")
        if any(
            later < earlier
            for earlier, later in zip(
                origin.candidate_timestamps_s,
                origin.candidate_timestamps_s[1:],
                strict=False,
            )
        ):
            raise ValueError(f"{origin.origin_id}: candidate timestamps must be nondecreasing")
        if origin.candidate_timestamps_s[0] < origin.parent_timestamp_s:
            raise ValueError(f"{origin.origin_id}: first target predates the decision parent")

        if origin.selected_k is None:
            raise ValueError(
                f"{origin.origin_id}: eligible origin has no action; offline evaluation invalid"
            )
        if not 0 <= origin.selected_k < action_count:
            raise ValueError(f"{origin.origin_id}: selected_k is outside fixed K")
