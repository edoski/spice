"""Typed contracts for boundary data structures."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any, NamedTuple, NotRequired, Protocol, Self, TypeAlias, TypedDict, overload

import torch
from torch import Tensor, nn

BlockScalar: TypeAlias = int | str
NullableBlockScalar: TypeAlias = BlockScalar | None


class RawBlockRow(TypedDict):
    block_number: BlockScalar
    timestamp: BlockScalar
    base_fee_per_gas: BlockScalar
    gas_used: BlockScalar
    chain_id: BlockScalar
    gas_limit: NotRequired[NullableBlockScalar]


class EnrichedBlockRow(TypedDict):
    block_number: BlockScalar
    timestamp: BlockScalar
    base_fee_per_gas: BlockScalar
    gas_used: BlockScalar
    chain_id: BlockScalar
    gas_limit: BlockScalar


BlockRow: TypeAlias = RawBlockRow | EnrichedBlockRow


class SequenceBatch(TypedDict):
    inputs: Tensor
    class_label: Tensor
    target_log_fee: Tensor
    candidate_log_fees: Tensor
    next_block_log_fee: Tensor
    optimal_log_fee: Tensor


class ModelOutputs(NamedTuple):
    logits: Tensor
    fee_hat: Tensor


class TemporalModel(Protocol):
    def __call__(self, inputs: Tensor, /) -> ModelOutputs: ...

    @overload
    def to(
        self,
        device: torch.device | str | None = ...,
        dtype: torch.dtype | None = ...,
        non_blocking: bool = ...,
    ) -> Self: ...

    @overload
    def to(self, dtype: torch.dtype, non_blocking: bool = ...) -> Self: ...

    @overload
    def to(self, tensor: Tensor, non_blocking: bool = ...) -> Self: ...

    def to(self, *args: Any, **kwargs: Any) -> Self: ...

    def eval(self) -> Self: ...

    def train(self, mode: bool = True) -> Self: ...

    def parameters(self, recurse: bool = True) -> Iterator[nn.Parameter]: ...

    @overload
    def state_dict(
        self,
        *,
        destination: dict[str, Any],
        prefix: str = ...,
        keep_vars: bool = ...,
    ) -> dict[str, Any]: ...

    @overload
    def state_dict(
        self,
        *,
        prefix: str = ...,
        keep_vars: bool = ...,
    ) -> dict[str, Any]: ...

    def state_dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]: ...

    def load_state_dict(
        self,
        state_dict: Mapping[str, Any],
        strict: bool = True,
        assign: bool = False,
    ) -> object: ...
