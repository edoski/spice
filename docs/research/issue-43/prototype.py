"""Interactive disposable prototype for the Issue 43 backend-to-Expo seam.

Run interactively:
    uv run python docs/research/issue-43/prototype.py

Run the bounded synthetic probe:
    uv run python docs/research/issue-43/prototype.py --all
"""

from __future__ import annotations

import argparse
import json
from dataclasses import fields, replace
from typing import TypeVar

from pydantic import ValidationError
from seam import (
    ENDPOINT,
    Chain,
    Horizon,
    InferenceRequest,
    PhoneState,
    finish_http_error,
    finish_network_error,
    finish_success,
    infer,
    result_rows,
    select_chain,
    select_horizon,
    start_request,
    synthetic_observation,
    with_artifact,
)

CHAINS: tuple[Chain, ...] = ("ethereum", "polygon", "avalanche")
HORIZONS: tuple[Horizon, ...] = (2, 3, 4, 5)
T = TypeVar("T")


def _expect_failure(label: str, operation) -> str:
    try:
        operation()
    except (TypeError, ValueError, ValidationError) as error:
        return f"{label}: {error}"
    raise AssertionError(f"{label} did not fail")


def run_probes() -> dict[str, object]:
    matrix: list[dict[str, object]] = []
    for chain in CHAINS:
        for horizon in HORIZONS:
            request = InferenceRequest(chain=chain, K=horizon)
            response = infer(request, synthetic_observation(request))
            assert response.selected_action_k == horizon - 1
            assert response.target_block == response.head_block + horizon
            assert set(request.model_dump()) == {"chain", "K"}
            assert set(response.model_dump()) == {
                "head_block",
                "selected_action_k",
                "target_block",
            }
            matrix.append(
                {
                    "request": request.model_dump(),
                    "response": response.model_dump(),
                }
            )

    depth_two_request = InferenceRequest(chain="ethereum", K=5)
    depth_two_response = infer(
        depth_two_request,
        synthetic_observation(depth_two_request, selected_action_k=0),
    )
    latest_rpc_head = depth_two_response.head_block
    last_finalized_context = latest_rpc_head - 2
    stale_target = last_finalized_context + 1
    assert stale_target <= latest_rpc_head
    assert depth_two_response.target_block == latest_rpc_head + 1
    assert depth_two_response.target_block > latest_rpc_head

    state = PhoneState(selection=InferenceRequest(chain="ethereum", K=5))
    state = start_request(state)
    server_response = infer(state.selection, synthetic_observation(state.selection))
    state = finish_success(state, server_response)
    assert state.result == server_response
    assert not state.loading
    assert state.error is None
    state = select_chain(state, "polygon")
    assert state.result is None
    assert state.error is None

    loading = start_request(state)
    failures = [
        _expect_failure(
            "selection during request",
            lambda: select_horizon(loading, 2),
        ),
        _expect_failure(
            "unknown chain",
            lambda: InferenceRequest.model_validate({"chain": "sepolia", "K": 5}),
        ),
        _expect_failure(
            "research-only horizon",
            lambda: InferenceRequest.model_validate({"chain": "ethereum", "K": 10}),
        ),
        _expect_failure(
            "extra request field",
            lambda: InferenceRequest.model_validate(
                {"chain": "ethereum", "K": 5, "artifact_id": "leak"}
            ),
        ),
        _expect_failure(
            "provider chain mismatch",
            lambda: infer(
                loading.selection,
                replace(synthetic_observation(loading.selection), provider_chain_id=1),
            ),
        ),
        _expect_failure(
            "artifact horizon mismatch",
            lambda: infer(
                loading.selection,
                with_artifact(synthetic_observation(loading.selection), K=2),
            ),
        ),
        _expect_failure(
            "artifact context mismatch",
            lambda: infer(
                loading.selection,
                with_artifact(synthetic_observation(loading.selection), context_blocks=199),
            ),
        ),
        _expect_failure(
            "malformed output",
            lambda: infer(
                loading.selection,
                replace(
                    synthetic_observation(loading.selection),
                    action_logits=(0.0,),
                ),
            ),
        ),
        _expect_failure(
            "nonfinite auxiliary output",
            lambda: infer(
                loading.selection,
                replace(
                    synthetic_observation(loading.selection),
                    minimum_fee_z=float("nan"),
                ),
            ),
        ),
    ]

    http_error = finish_http_error(loading, 422, '{"detail":"invalid request"}')
    network_error = finish_network_error(loading, "Failed to fetch")
    assert http_error.error == 'HTTP 422: {"detail":"invalid request"}'
    assert network_error.error == "Network error: Failed to fetch"

    phone_fields = {field.name for field in fields(PhoneState)}
    forbidden = {
        "wallet",
        "transaction",
        "broadcast",
        "receipt",
        "schedule",
        "ttl",
        "analytics",
        "minimum_fee_z",
    }
    assert phone_fields.isdisjoint(forbidden)

    return {
        "question": "smallest exact stateless FastAPI-to-Expo inference seam",
        "endpoint": f"POST {ENDPOINT}",
        "matrix_count": len(matrix),
        "matrix": matrix,
        "depth_two": {
            "latest_rpc_head": latest_rpc_head,
            "stale_last_finalized_context": last_finalized_context,
            "stale_k0_target": stale_target,
            "response": depth_two_response.model_dump(),
        },
        "phone": {
            "state_fields": sorted(phone_fields),
            "result_rows": result_rows(server_response),
            "selection_change_clears_result": True,
            "selection_locked_while_loading": True,
            "manual_retry_only": True,
        },
        "errors": {
            "server_failures": failures,
            "http": http_error.error,
            "network": network_error.error,
        },
        "successful_response_handling": "ordinary JSON decode plus TypeScript cast",
        "forbidden_phone_fields": sorted(forbidden),
        "checks": "pass",
    }


def run_interactive() -> None:
    state = PhoneState(selection=InferenceRequest(chain="ethereum", K=5))
    while True:
        _render(state)
        key = input("\n> ").strip().lower()[:1]
        try:
            if key == "q":
                return
            if key == "c":
                state = select_chain(state, _next(CHAINS, state.selection.chain))
            elif key == "k":
                state = select_horizon(state, _next(HORIZONS, state.selection.K))
            elif key == "r":
                state = start_request(state)
            elif key == "s" and state.loading:
                response = infer(state.selection, synthetic_observation(state.selection))
                state = finish_success(state, response)
            elif key == "h" and state.loading:
                state = finish_http_error(state, 500, '{"detail":"Internal Server Error"}')
            elif key == "n" and state.loading:
                state = finish_network_error(state, "Failed to fetch")
        except (TypeError, ValueError, ValidationError) as error:
            if state.loading:
                state = finish_network_error(state, str(error))
            else:
                state = replace(state, error=str(error))


def _render(state: PhoneState) -> None:
    print("\033[2J\033[H", end="")
    print("\033[1mIssue 43 — backend ↔ Expo inference seam\033[0m")
    print("\033[2mDisposable synthetic prototype; no transfer or scheduling.\033[0m\n")
    print(f"\033[1mEndpoint\033[0m  POST {ENDPOINT}")
    print(f"\033[1mChain\033[0m     {state.selection.chain}")
    print(f"\033[1mK\033[0m         {state.selection.K}")
    print(f"\033[1mLoading\033[0m   {state.loading}")
    if state.result is not None:
        print("\n\033[1mResult\033[0m")
        for label, value in result_rows(state.result):
            print(f"{label:<20} {value}")
    elif state.error is not None:
        print(f"\n\033[1mError\033[0m  {state.error}")
    else:
        print("\n\033[2mNo result.\033[0m")
    print("\n\033[1mKeys\033[0m")
    if state.loading:
        print(
            "\033[1ms\033[0m success  \033[1mh\033[0m HTTP error  "
            "\033[1mn\033[0m network error  \033[1mq\033[0m quit"
        )
    else:
        print(
            "\033[1mc\033[0m chain  \033[1mk\033[0m horizon  "
            "\033[1mr\033[0m run inference  \033[1mq\033[0m quit"
        )


def _next(values: tuple[T, ...], value: T) -> T:
    return values[(values.index(value) + 1) % len(values)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if args.all:
        print(json.dumps(run_probes(), indent=2))
    else:
        run_interactive()


if __name__ == "__main__":
    main()
