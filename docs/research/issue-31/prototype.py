"""Interactive disposable prototype for Issue 31.

Question: can one exact historical origin-window preparer and one distinct live
right-edge preparer share only feature transformation and action arithmetic while
keeping the full two-head task output and never targeting a closed block?

Run all bounded probes:
    uv run python docs/research/issue-31/prototype.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace

import numpy as np
import torch
from preparation import (
    CORE_FEATURES,
    ETHEREUM_FEATURES,
    ArtifactFacts,
    BlockFrame,
    BlockRef,
    FeatureState,
    MinBlockFeeOutput,
    RequestedOriginWindow,
    TargetState,
    decide_live,
    ethereum_forming_base_fee,
    observe_heads,
    prepare_historical_window,
    prepare_live,
    raw_feature_rows,
    target_block,
)

C = 200
K = 5
LATEST = 1_210
REQUESTED = RequestedOriginWindow(LATEST - 2, LATEST)


def synthetic_ethereum_frame(first: int, last: int) -> BlockFrame:
    count = last - first + 1
    blocks = np.arange(first, last + 1, dtype=np.int64)
    gas_limits = np.full(count, 30_000_000, dtype=np.int64)
    deviations = np.array((-2_000_000, -1_000_000, 0, 1_000_000, 2_000_000), dtype=np.int64)
    gas_used = 15_000_000 + deviations[np.arange(count) % deviations.size]
    fees = np.empty(count, dtype=np.int64)
    fees[0] = 1_000_000_000
    for index in range(1, count):
        fees[index] = ethereum_forming_base_fee(
            int(fees[index - 1]),
            int(gas_used[index - 1]),
            int(gas_limits[index - 1]),
        )
    return BlockFrame(
        corpus_id="sha256:synthetic-evaluation-frame",
        chain_id=1,
        regime="fusaka",
        block_numbers=blocks,
        block_hashes=tuple(f"0x{block:064x}" for block in blocks),
        timestamps=np.arange(1_800_000_000, 1_800_000_000 + 12 * count, 12, dtype=np.int64),
        base_fees=fees,
        gas_used=gas_used.astype(np.int64),
        gas_limits=gas_limits,
    )


def synthetic_artifact() -> ArtifactFacts:
    feature_state = FeatureState(
        chain_id=1,
        regime="fusaka",
        names=ETHEREUM_FEATURES,
        means=np.array([20.70, 0.50, 20.70], dtype=np.float64),
        scales=np.array([0.25, 0.10, 0.25], dtype=np.float64),
        training_corpus_id="sha256:synthetic-training-frame",
    )
    target_state = TargetState(
        chain_id=1,
        regime="fusaka",
        k=K,
        mean=np.float64(20.70),
        scale=np.float64(0.25),
        training_corpus_id="sha256:synthetic-training-frame",
    )
    return ArtifactFacts(
        artifact_id="synthetic-ethereum-k5",
        chain_id=1,
        regime="fusaka",
        c=C,
        k=K,
        feature_state=feature_state,
        target_state=target_state,
        input_width=3,
        action_head_width=K,
        auxiliary_head_width=1,
    )


def synthetic_parent_only_artifact() -> ArtifactFacts:
    feature_state = FeatureState(
        chain_id=137,
        regime="lisovo",
        names=CORE_FEATURES,
        means=np.array([20.70, 0.50], dtype=np.float64),
        scales=np.array([0.25, 0.10], dtype=np.float64),
        training_corpus_id="sha256:synthetic-polygon-training-frame",
    )
    target_state = TargetState(
        chain_id=137,
        regime="lisovo",
        k=K,
        mean=np.float64(20.70),
        scale=np.float64(0.25),
        training_corpus_id="sha256:synthetic-polygon-training-frame",
    )
    return ArtifactFacts(
        artifact_id="synthetic-polygon-k5",
        chain_id=137,
        regime="lisovo",
        c=C,
        k=K,
        feature_state=feature_state,
        target_state=target_state,
        input_width=2,
        action_head_width=K,
        auxiliary_head_width=1,
    )


def _expect_failure(label: str, fn) -> str:
    try:
        fn()
    except (ValueError, IndexError) as error:
        return f"{label}: {error}"
    raise AssertionError(f"{label} did not fail closed")


def run_probes() -> dict[str, object]:
    artifact = synthetic_artifact()
    support_first = REQUESTED.first_origin_block - C + 1
    full = synthetic_ethereum_frame(support_first, LATEST + K)
    historical = prepare_historical_window(full, artifact, REQUESTED)
    historical_last = historical.dataset[len(historical.dataset) - 1]

    latest_ref = BlockRef(LATEST, full.block_hashes[LATEST - full.first_block])
    heads = observe_heads(latest_ref, confirmation_depth=2)
    live_rows = full.select(LATEST - C + 1, LATEST)
    live = prepare_live(live_rows, artifact, latest_ref)

    forming = np.array(
        [
            ethereum_forming_base_fee(int(fee), int(used), int(limit))
            for fee, used, limit in zip(
                full.base_fees[:-1],
                full.gas_used[:-1],
                full.gas_limits[:-1],
                strict=True,
            )
        ],
        dtype=np.int64,
    )
    np.testing.assert_array_equal(forming, full.base_fees[1:])

    torch.testing.assert_close(historical_last["inputs"], live.inputs[0], rtol=0, atol=0)
    assert int(historical_last["origin_block"]) == LATEST
    assert len(historical.dataset) == REQUESTED.count
    assert historical.support_first_block == support_first
    assert historical.support_last_block == LATEST + K
    assert live_rows.last_block == LATEST
    assert full.last_block == LATEST + K

    logits = torch.tensor([[0.1, 0.2, 0.9, -0.1, 0.0]], dtype=torch.float32)
    output = MinBlockFeeOutput(logits, torch.tensor([0.375], dtype=torch.float32))
    decision = decide_live(live, artifact, output)
    altered_aux = decide_live(
        live,
        artifact,
        MinBlockFeeOutput(logits.clone(), torch.tensor([-8.0], dtype=torch.float32)),
    )
    assert decision.output.minimum_fee_z.item() == output.minimum_fee_z.item()
    assert decision.k == altered_aux.k
    assert decision.target_block == altered_aux.target_block
    assert decision.broadcast_after_block == altered_aux.broadcast_after_block

    assert heads.last_finalized_context == LATEST - 2
    assert heads.first_actionable_target == LATEST + 1
    stale_k0_target = heads.last_finalized_context + 1
    assert stale_k0_target <= LATEST
    for k in range(K):
        assert target_block(heads.latest_rpc_head.number, k, K) > LATEST

    polygon_frame = replace(
        full,
        corpus_id="sha256:synthetic-polygon-evaluation-frame",
        chain_id=137,
        regime="lisovo",
    )
    polygon_artifact = synthetic_parent_only_artifact()
    polygon_historical = prepare_historical_window(polygon_frame, polygon_artifact, REQUESTED)
    polygon_live_rows = polygon_frame.select(LATEST - C + 1, LATEST)
    polygon_ref = BlockRef(LATEST, polygon_live_rows.block_hashes[-1])
    polygon_live = prepare_live(polygon_live_rows, polygon_artifact, polygon_ref)
    torch.testing.assert_close(
        polygon_historical.dataset[len(polygon_historical.dataset) - 1]["inputs"],
        polygon_live.inputs[0],
        rtol=0,
        atol=0,
    )
    assert raw_feature_rows(polygon_live_rows, CORE_FEATURES).shape[1] == 2

    failures = [
        _expect_failure(
            "insufficient historical support",
            lambda: prepare_historical_window(
                full.select(support_first + 1, full.last_block),
                artifact,
                REQUESTED,
            ),
        ),
        _expect_failure(
            "stale live right edge",
            lambda: prepare_live(full.select(LATEST - C - 1, LATEST - 2), artifact, latest_ref),
        ),
        _expect_failure(
            "wrong auxiliary head width",
            lambda: replace(artifact, auxiliary_head_width=2),
        ),
        _expect_failure(
            "malformed auxiliary output",
            lambda: decide_live(
                live,
                artifact,
                MinBlockFeeOutput(logits, torch.tensor([[0.375]], dtype=torch.float32)),
            ),
        ),
    ]

    return {
        "question": (
            "distinct historical/live preparation with exact actionable-head and two-head parity"
        ),
        "historical": {
            "requested_origin_blocks": [
                REQUESTED.first_origin_block,
                REQUESTED.last_origin_block,
            ],
            "requested_count": REQUESTED.count,
            "prepared_origin_blocks": [
                int(historical.dataset[index]["origin_block"])
                for index in range(len(historical.dataset))
            ],
            "minimal_support": [
                historical.support_first_block,
                historical.support_last_block,
            ],
            "item_shapes": {name: list(value.shape) for name, value in historical_last.items()},
        },
        "live": {
            "latest_rpc_head": heads.latest_rpc_head.number,
            "last_finalized_context": heads.last_finalized_context,
            "first_actionable_target": heads.first_actionable_target,
            "input_shape": list(live.inputs.shape),
            "historical_live_input_bit_equal": True,
            "ethereum_parent_fee_transitions_exact": int(forming.size),
            "future_rows_supplied_to_live": False,
        },
        "parent_only": {
            "chain": "Polygon Lisovo",
            "feature_names": list(CORE_FEATURES),
            "input_shape": list(polygon_live.inputs.shape),
            "forming_fee_placeholder_present": False,
            "historical_live_input_bit_equal": True,
            "structurally_shared_with": "Avalanche parent-only route",
        },
        "output": {
            "action_logits_shape": list(decision.output.action_logits.shape),
            "minimum_fee_z_shape": list(decision.output.minimum_fee_z.shape),
            "minimum_fee_z_preserved": decision.output.minimum_fee_z.item(),
            "decoded_k": decision.k,
            "broadcast_after_block": decision.broadcast_after_block,
            "target_block": decision.target_block,
            "auxiliary_changes_action": False,
        },
        "depth_two_comparator": {
            "stale_k0_target": stale_k0_target,
            "stale_target_is_closed": stale_k0_target <= LATEST,
            "selected_k0_target": heads.first_actionable_target,
            "all_selected_targets_are_future": True,
        },
        "fail_closed": failures,
    }


def render(state: dict[str, object], section: str) -> None:
    print("\033[2J\033[H", end="")
    print("\033[1mIssue 31 preparation prototype\033[0m")
    print("\033[2mSynthetic only; C=200, K=5, Ethereum Fusaka.\033[0m\n")
    value = state if section == "all" else state[section]
    print(json.dumps(value, indent=2, sort_keys=True))
    print(
        "\n\033[1m[h]\033[0m historical  \033[1m[l]\033[0m live  "
        "\033[1m[o]\033[0m output  \033[1m[a]\033[0m all  \033[1m[q]\033[0m quit"
    )


def interactive(state: dict[str, object]) -> None:
    section = "all"
    while True:
        render(state, section)
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        section = {"h": "historical", "l": "live", "o": "output", "a": "all"}.get(
            choice,
            section,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run probes and print JSON")
    args = parser.parse_args()
    state = run_probes()
    if args.all or not sys.stdin.isatty():
        print(json.dumps(state, indent=2, sort_keys=True))
        return
    interactive(state)


if __name__ == "__main__":
    main()
