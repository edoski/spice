"""THROWAWAY PROTOTYPE for issue “Prototype the current-block action and cross-layer parity”.

Question: with one decision row, do the proposed action routes keep the offline
label/replay and live serving target on the same block for each supported chain
regime?  The selected route is closed-parent context plus one exact Ethereum
forming-fee feature.  Run:
uv run python docs/research/current_block_action_cross_layer_fixture.py
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Regime:
    name: str
    exact_forming_fee_from_parent: bool
    selected_exact_feature: bool
    block_seconds_equivalent: bool
    reason: str


REGIMES = (
    Regime("Ethereum EIP-1559", True, True, False, "parent recurrence supplies child base fee"),
    Regime(
        "Polygon pre-Lisovo fixed parameters",
        True,
        False,
        False,
        "fork-scoped exact recurrence exists but is not retained for the mixed-era corpus",
    ),
    Regime(
        "Polygon post-Lisovo",
        False,
        False,
        False,
        "producer-configurable fee parameters",
    ),
    Regime(
        "Avalanche Octane/Granite",
        False,
        False,
        False,
        "needs dynamic state and child time",
    ),
)


def forming_block(regime: Regime, parent: int, offset: int) -> dict[str, object]:
    current = parent + 1
    return {
        "route": "forming-block",
        "decision": f"before selection for {current}",
        "context_end": parent,
        "class_target": current + offset,
        "offline_label": current + offset,
        "replay_realization": current + offset,
        "serve_target": current + offset,
        "exact_forming_fee_available": regime.exact_forming_fee_from_parent,
        "status": "PARITY" if regime.exact_forming_fee_from_parent else "UNPROVEN",
    }


def parent_only_forming_block(parent: int, offset: int) -> dict[str, object]:
    current = parent + 1
    return {
        "route": "forming-block, parent-only inputs",
        "decision": f"before selection for {current}",
        "context_end": parent,
        "forming_fee": "prediction target, never an input",
        "class_target": current + offset,
        "offline_label": current + offset,
        "replay_realization": current + offset,
        "serve_target": current + offset,
        "status": "PARITY; eligibility only until cutoff is proved",
    }


def selected_closed_parent(regime: Regime, parent: int, offset: int) -> dict[str, object]:
    current = parent + 1
    return {
        "route": "SELECTED: closed parent plus exact Ethereum forming fee",
        "decision": f"before selection for {current}",
        "context_end": parent,
        "exact_forming_fee_feature": regime.selected_exact_feature,
        "forming_fee_feature": (
            f"exact fee for {current}, computed only from parent {parent}"
            if regime.selected_exact_feature
            else "absent; use uniform closed-parent features"
        ),
        "forming_fee_outcome": current,
        "class_target": current + offset,
        "offline_label": current + offset,
        "replay_realization": current + offset,
        "serve_target": current + offset,
        "status": "PARITY; eligibility only until cutoff is proved",
    }


def closed_parent(route: str, confirmed_head: int, offset: int) -> dict[str, object]:
    target = confirmed_head + 1 + offset
    return {
        "route": route,
        "decision": f"after closed parent {confirmed_head}",
        "context_end": confirmed_head,
        "class_target": target,
        "offline_label": target,
        "replay_realization": target,
        "serve_target": target,
        "status": "PARITY",
    }


def current_implementation(confirmed_head: int, offset: int) -> dict[str, object]:
    return {
        "route": "current implementation (failed comparator)",
        "offline_label_and_replay": confirmed_head + offset,
        "serve_target": confirmed_head + offset + 1,
        "status": "FAIL: different target blocks",
    }


def main() -> None:
    latest_closed, depth, offset = 100, 2, 1
    stale_confirmed_context = latest_closed - depth
    decision_parent = latest_closed
    print(
        f"latest_closed={latest_closed}; confirmation_depth={depth}; "
        f"stale_confirmed_context={stale_confirmed_context}; "
        f"decision_parent={decision_parent}; offset={offset}"
    )
    print(
        "Current service maps target = stale_confirmed_context + offset + 1; "
        "its k=0, k=1 are 99, 100 (already closed)."
    )
    print(current_implementation(stale_confirmed_context, offset))
    for regime in REGIMES:
        print(f"\n{regime.name}: {regime.reason}")
        for state in (
            selected_closed_parent(regime, decision_parent, offset),
            forming_block(regime, decision_parent, offset),
            parent_only_forming_block(decision_parent, offset),
            closed_parent("immediate-action/closed-parent", decision_parent, offset),
            closed_parent("paper-next-block comparator", decision_parent, offset),
        ):
            print(state)
        print(
            {
                "action_units": "block offsets offline; seconds estimate online",
                "equivalent": regime.block_seconds_equivalent,
                "actionability": "UNPROVEN: replay has no cutoff/propagation/eligibility model",
            }
        )

        selected_zero = selected_closed_parent(regime, decision_parent, 0)
        selected_one = selected_closed_parent(regime, decision_parent, 1)
        assert selected_zero["class_target"] == latest_closed + 1
        assert selected_one["class_target"] == latest_closed + 2
        assert selected_zero["offline_label"] == selected_zero["serve_target"]
        assert selected_one["offline_label"] == selected_one["serve_target"]
        assert selected_zero["exact_forming_fee_feature"] is (regime.name == "Ethereum EIP-1559")

    assert current_implementation(stale_confirmed_context, 0)["serve_target"] <= latest_closed
    assert current_implementation(stale_confirmed_context, 1)["serve_target"] <= latest_closed


if __name__ == "__main__":
    main()
