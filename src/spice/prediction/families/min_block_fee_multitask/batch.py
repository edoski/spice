"""Paper family target and training-state contracts."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from ....temporal.execution_policy import PreparedTemporalFacts


def materialize_min_block_fee_targets(
    temporal_facts: PreparedTemporalFacts,
) -> PreparedMinBlockFeeTargets:
    action_space = temporal_facts.action_space
    outcome_facts = temporal_facts.outcome_facts
    reachable_mask = outcome_facts.reachable_action_mask
    if reachable_mask.shape[0] > 0 and not bool(np.all(reachable_mask.any(axis=1))):
        raise ValueError("min-block-fee targets require one reachable action per sample")
    masked_log_fees = np.where(
        reachable_mask,
        outcome_facts.action_outcome_log_fees,
        np.inf,
    )
    min_block_offsets = np.argmin(masked_log_fees, axis=1).astype(np.int64, copy=False)
    min_block_log_fees = masked_log_fees[
        np.arange(masked_log_fees.shape[0]),
        min_block_offsets,
    ].astype(np.float32, copy=False)
    return PreparedMinBlockFeeTargets(
        action_mask=torch.from_numpy(action_space.action_mask),
        min_block_offsets=torch.from_numpy(min_block_offsets),
        min_block_log_fees=torch.from_numpy(min_block_log_fees),
    )


@dataclass(slots=True)
class MinBlockFeeTargetBatch:
    action_mask: torch.Tensor
    min_block_offsets: torch.Tensor
    min_block_log_fees: torch.Tensor

    def to_device(self, device: torch.device) -> MinBlockFeeTargetBatch:
        if (
            self.action_mask.device == device
            and self.min_block_offsets.device == device
            and self.min_block_log_fees.device == device
        ):
            return self
        non_blocking = device.type == "cuda"
        return MinBlockFeeTargetBatch(
            action_mask=self.action_mask.to(device, non_blocking=non_blocking),
            min_block_offsets=self.min_block_offsets.to(device, non_blocking=non_blocking),
            min_block_log_fees=self.min_block_log_fees.to(device, non_blocking=non_blocking),
        )

    def pin_memory(self) -> MinBlockFeeTargetBatch:
        if self.action_mask.device.type != "cpu":
            return self
        return MinBlockFeeTargetBatch(
            action_mask=self.action_mask.pin_memory(),
            min_block_offsets=self.min_block_offsets.pin_memory(),
            min_block_log_fees=self.min_block_log_fees.pin_memory(),
        )


@dataclass(frozen=True, slots=True)
class PreparedMinBlockFeeTargets:
    action_mask: torch.Tensor
    min_block_offsets: torch.Tensor
    min_block_log_fees: torch.Tensor

    @property
    def estimated_storage_bytes(self) -> int:
        return (
            self.action_mask.element_size() * self.action_mask.numel()
            + self.min_block_offsets.element_size() * self.min_block_offsets.numel()
            + self.min_block_log_fees.element_size() * self.min_block_log_fees.numel()
        )

    def build_batch(self, sample_positions: torch.Tensor) -> MinBlockFeeTargetBatch:
        positions = sample_positions.detach().cpu().to(dtype=torch.int64, copy=False)
        index = positions.to(device=self.action_mask.device)
        return MinBlockFeeTargetBatch(
            action_mask=self.action_mask.index_select(0, index),
            min_block_offsets=self.min_block_offsets.index_select(0, index),
            min_block_log_fees=self.min_block_log_fees.index_select(0, index),
        )

    def to_device_storage(
        self,
        device: torch.device,
    ) -> PreparedMinBlockFeeTargets:
        if (
            self.action_mask.device == device
            and self.min_block_offsets.device == device
            and self.min_block_log_fees.device == device
        ):
            return self
        non_blocking = device.type == "cuda"
        return PreparedMinBlockFeeTargets(
            action_mask=self.action_mask.to(device, non_blocking=non_blocking),
            min_block_offsets=self.min_block_offsets.to(device, non_blocking=non_blocking),
            min_block_log_fees=self.min_block_log_fees.to(
                device,
                non_blocking=non_blocking,
            ),
        )


@dataclass(frozen=True, slots=True)
class ResolvedMinBlockFeeTrainingState:
    class_weights: torch.Tensor
    fee_mean: torch.Tensor
    fee_std: torch.Tensor


@dataclass(slots=True)
class MinBlockFeeTrainingState:
    class_weights: torch.Tensor
    fee_mean: torch.Tensor = field(
        default_factory=lambda: torch.tensor(0.0, dtype=torch.float32)
    )
    fee_std: torch.Tensor = field(
        default_factory=lambda: torch.tensor(1.0, dtype=torch.float32)
    )
    _resolved: dict[tuple[str, int | None, torch.dtype], ResolvedMinBlockFeeTrainingState] = (
        field(default_factory=dict, init=False, repr=False)
    )

    def __post_init__(self) -> None:
        class_weights = self.class_weights.detach().to(device="cpu", dtype=torch.float32).clone()
        fee_mean = torch.as_tensor(self.fee_mean, dtype=torch.float32).detach().to(device="cpu")
        fee_std = torch.as_tensor(self.fee_std, dtype=torch.float32).detach().to(device="cpu")
        if fee_mean.ndim != 0 or fee_std.ndim != 0:
            raise ValueError("fee_mean and fee_std must be scalar tensors")
        if float(fee_std.item()) <= 0.0:
            raise ValueError("fee_std must be positive")
        self.class_weights = class_weights
        self.fee_mean = fee_mean.reshape(()).clone()
        self.fee_std = fee_std.reshape(()).clone()

    def resolve(
        self,
        *,
        device: torch.device,
        dtype: torch.dtype,
    ) -> ResolvedMinBlockFeeTrainingState:
        key = (device.type, device.index, dtype)
        resolved = self._resolved.get(key)
        if resolved is not None:
            return resolved
        non_blocking = device.type == "cuda"
        resolved = ResolvedMinBlockFeeTrainingState(
            class_weights=self.class_weights.to(
                device=device,
                dtype=dtype,
                non_blocking=non_blocking,
            ),
            fee_mean=self.fee_mean.to(
                device=device,
                dtype=dtype,
                non_blocking=non_blocking,
            ),
            fee_std=self.fee_std.to(
                device=device,
                dtype=dtype,
                non_blocking=non_blocking,
            ),
        )
        self._resolved[key] = resolved
        return resolved
