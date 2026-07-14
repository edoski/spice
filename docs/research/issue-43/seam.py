"""Disposable backend-to-Expo inference seam for Issue 43.

Question: can one strict request, one exact response, and one small phone interaction
replace the current timed-transfer lifecycle without losing actionable-head correctness?

Synthetic values only. This is planning evidence, not production implementation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Annotated, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

ENDPOINT = "/inference"
C = 200

Chain: TypeAlias = Literal["ethereum", "polygon", "avalanche"]
Horizon: TypeAlias = Literal[2, 3, 4, 5]

CHAIN_IDS: dict[Chain, int] = {
    "ethereum": 1,
    "polygon": 137,
    "avalanche": 43114,
}

NonNegativeInt: TypeAlias = Annotated[int, Field(strict=True, ge=0)]


class _StrictMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class InferenceRequest(_StrictMessage):
    chain: Chain
    K: Horizon


class InferenceResponse(_StrictMessage):
    head_block: NonNegativeInt
    selected_action_k: NonNegativeInt
    target_block: NonNegativeInt


@dataclass(frozen=True, slots=True)
class ArtifactFacts:
    """Only facts needed to prove the already-approved server-side selection."""

    internal_artifact_id: str
    chain: Chain
    K: Horizon
    context_blocks: int = C


@dataclass(frozen=True, slots=True)
class ServerObservation:
    provider_chain_id: int
    head_block: int
    artifact: ArtifactFacts
    action_logits: tuple[float, ...]
    minimum_fee_z: float


@dataclass(frozen=True, slots=True)
class PhoneState:
    """Exact local interaction facts; no transfer or scheduling state exists."""

    selection: InferenceRequest
    loading: bool = False
    result: InferenceResponse | None = None
    error: str | None = None


def infer(request: InferenceRequest, observation: ServerObservation) -> InferenceResponse:
    """Exercise the server-owned chain/artifact/head/output checks and response."""

    artifact = observation.artifact
    expected_chain_id = CHAIN_IDS[request.chain]
    if observation.provider_chain_id != expected_chain_id:
        raise ValueError(
            f"provider chain_id {observation.provider_chain_id} does not match {expected_chain_id}"
        )
    if artifact.chain != request.chain:
        raise ValueError(f"artifact chain {artifact.chain!r} does not match {request.chain!r}")
    if artifact.K != request.K:
        raise ValueError(f"artifact K={artifact.K} does not match K={request.K}")
    if artifact.context_blocks != C:
        raise ValueError(f"artifact C={artifact.context_blocks} does not match C={C}")
    if observation.head_block < 0:
        raise ValueError("head_block must be non-negative")
    if len(observation.action_logits) != request.K:
        raise ValueError(
            f"action logits width {len(observation.action_logits)} does not match K={request.K}"
        )
    if not all(math.isfinite(value) for value in observation.action_logits):
        raise ValueError("action logits must be finite")
    if not math.isfinite(observation.minimum_fee_z):
        raise ValueError("minimum_fee_z must be finite")

    selected_action_k = max(
        range(request.K),
        key=lambda index: observation.action_logits[index],
    )
    return InferenceResponse(
        head_block=observation.head_block,
        selected_action_k=selected_action_k,
        target_block=observation.head_block + 1 + selected_action_k,
    )


def select_chain(state: PhoneState, chain: Chain) -> PhoneState:
    if state.loading:
        raise ValueError("selection is disabled while inference is running")
    return PhoneState(selection=InferenceRequest(chain=chain, K=state.selection.K))


def select_horizon(state: PhoneState, horizon: Horizon) -> PhoneState:
    if state.loading:
        raise ValueError("selection is disabled while inference is running")
    return PhoneState(selection=InferenceRequest(chain=state.selection.chain, K=horizon))


def start_request(state: PhoneState) -> PhoneState:
    if state.loading:
        raise ValueError("one inference request is already running")
    return PhoneState(selection=state.selection, loading=True)


def finish_success(state: PhoneState, response: InferenceResponse) -> PhoneState:
    _require_loading(state)
    return PhoneState(selection=state.selection, result=response)


def finish_http_error(state: PhoneState, status: int, body: str) -> PhoneState:
    _require_loading(state)
    detail = body.strip() or "request failed"
    return PhoneState(selection=state.selection, error=f"HTTP {status}: {detail}")


def finish_network_error(state: PhoneState, message: str) -> PhoneState:
    _require_loading(state)
    detail = message.strip() or "request failed"
    return PhoneState(selection=state.selection, error=f"Network error: {detail}")


def result_rows(result: InferenceResponse) -> tuple[tuple[str, str], ...]:
    """The complete result display. Selection controls already show chain and K."""

    return (
        ("Head block", str(result.head_block)),
        ("Selected action k", str(result.selected_action_k)),
        ("Target block", str(result.target_block)),
    )


def synthetic_observation(
    request: InferenceRequest,
    *,
    head_block: int = 1_210,
    selected_action_k: int | None = None,
) -> ServerObservation:
    selected = request.K - 1 if selected_action_k is None else selected_action_k
    logits = tuple(1.0 if index == selected else 0.0 for index in range(request.K))
    return ServerObservation(
        provider_chain_id=CHAIN_IDS[request.chain],
        head_block=head_block,
        artifact=ArtifactFacts(
            internal_artifact_id=f"synthetic-{request.chain}-k{request.K}",
            chain=request.chain,
            K=request.K,
        ),
        action_logits=logits,
        minimum_fee_z=0.375,
    )


def with_artifact(observation: ServerObservation, **changes: object) -> ServerObservation:
    return replace(observation, artifact=replace(observation.artifact, **changes))


def _require_loading(state: PhoneState) -> None:
    if not state.loading:
        raise ValueError("no inference request is running")
