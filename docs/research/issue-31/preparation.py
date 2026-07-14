"""Disposable Issue 31 logic: distinct historical and live preparation seams."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import NamedTuple

import numpy as np
import torch
from numpy.typing import NDArray

CORE_FEATURES = ("log_base_fee_per_gas", "gas_utilization")
ETHEREUM_FEATURES = CORE_FEATURES + ("log_exact_forming_base_fee_per_gas",)
TARGET_ID = "hindsight_minimum_base_fee_per_gas_within_k"

IntVector = NDArray[np.int64]
FloatMatrix = NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class BlockRef:
    number: int
    hash: str

    def __post_init__(self) -> None:
        if self.number < 0 or not self.hash:
            raise ValueError("block reference requires a nonnegative number and hash")


@dataclass(frozen=True, slots=True)
class BlockFrame:
    corpus_id: str
    chain_id: int
    regime: str
    block_numbers: IntVector
    block_hashes: tuple[str, ...]
    timestamps: IntVector
    base_fees: IntVector
    gas_used: IntVector
    gas_limits: IntVector

    def __post_init__(self) -> None:
        vectors = {
            "block_numbers": self.block_numbers,
            "timestamps": self.timestamps,
            "base_fees": self.base_fees,
            "gas_used": self.gas_used,
            "gas_limits": self.gas_limits,
        }
        if not self.corpus_id or self.chain_id <= 0 or not self.regime:
            raise ValueError("frame identity must be complete")
        lengths = set()
        for name, value in vectors.items():
            if not isinstance(value, np.ndarray) or value.dtype != np.int64 or value.ndim != 1:
                raise ValueError(f"{name} must be a one-dimensional int64 array")
            lengths.add(value.size)
        if lengths == {0} or len(lengths) != 1 or len(self.block_hashes) not in lengths:
            raise ValueError("frame columns must be nonempty and aligned")
        if np.any(np.diff(self.block_numbers) != 1):
            raise ValueError("frame blocks must already be consecutive and ordered")
        if np.any(np.diff(self.timestamps) < 0):
            raise ValueError("frame timestamps must be nondecreasing")
        if np.any(self.base_fees <= 0) or np.any(self.gas_limits <= 0):
            raise ValueError("frame fees and gas limits must be positive")
        if np.any(self.gas_used < 0) or np.any(self.gas_used > self.gas_limits):
            raise ValueError("frame gas used must lie within the gas limit")
        if any(not value for value in self.block_hashes):
            raise ValueError("frame hashes must be nonempty")
        for name, value in vectors.items():
            copied = np.array(value, dtype=np.int64, copy=True, order="C")
            copied.setflags(write=False)
            object.__setattr__(self, name, copied)

    @property
    def first_block(self) -> int:
        return int(self.block_numbers[0])

    @property
    def last_block(self) -> int:
        return int(self.block_numbers[-1])

    def select(self, first_block: int, last_block: int) -> BlockFrame:
        if first_block > last_block:
            raise ValueError("selected block range must be nonempty")
        if first_block < self.first_block or last_block > self.last_block:
            raise ValueError(
                "frame does not cover exact requested support: "
                f"required={first_block}..{last_block} "
                f"available={self.first_block}..{self.last_block}"
            )
        start = first_block - self.first_block
        stop = last_block - self.first_block + 1
        if (
            int(self.block_numbers[start]) != first_block
            or int(self.block_numbers[stop - 1]) != last_block
        ):
            raise ValueError("frame block lookup did not preserve exact endpoints")
        return replace(
            self,
            block_numbers=self.block_numbers[start:stop],
            block_hashes=self.block_hashes[start:stop],
            timestamps=self.timestamps[start:stop],
            base_fees=self.base_fees[start:stop],
            gas_used=self.gas_used[start:stop],
            gas_limits=self.gas_limits[start:stop],
        )


@dataclass(frozen=True, slots=True)
class FeatureState:
    chain_id: int
    regime: str
    names: tuple[str, ...]
    means: NDArray[np.float64]
    scales: NDArray[np.float64]
    training_corpus_id: str

    def __post_init__(self) -> None:
        if self.chain_id <= 0 or not self.regime or not self.training_corpus_id:
            raise ValueError("feature state identity must be complete")
        if not self.names or len(set(self.names)) != len(self.names):
            raise ValueError("feature names must be nonempty and unique")
        for label, value in (("means", self.means), ("scales", self.scales)):
            if not isinstance(value, np.ndarray) or value.dtype != np.float64:
                raise ValueError(f"feature {label} must be float64")
            if value.shape != (len(self.names),) or not np.isfinite(value).all():
                raise ValueError(f"feature {label} must match the finite ordered feature width")
        if np.any(self.scales <= 0.0):
            raise ValueError("feature scales must be strictly positive")

    def transform(self, rows: FloatMatrix) -> NDArray[np.float32]:
        if rows.dtype != np.float64 or rows.ndim != 2 or rows.shape[1] != len(self.names):
            raise ValueError("raw feature rows must match the ordered float64 feature state")
        transformed = (rows - self.means) / self.scales
        result = transformed.astype(np.float32)
        if not np.isfinite(transformed).all() or not np.isfinite(result).all():
            raise ValueError("feature transform must remain finite through float32 emission")
        return np.ascontiguousarray(result)


@dataclass(frozen=True, slots=True)
class TargetState:
    chain_id: int
    regime: str
    k: int
    mean: np.float64
    scale: np.float64
    training_corpus_id: str
    target_id: str = TARGET_ID

    def __post_init__(self) -> None:
        if self.target_id != TARGET_ID:
            raise ValueError(f"target id must equal {TARGET_ID!r}")
        if self.chain_id <= 0 or not self.regime or not self.training_corpus_id or self.k <= 0:
            raise ValueError("target state identity must be complete")
        if not isinstance(self.mean, np.float64) or not isinstance(self.scale, np.float64):
            raise ValueError("target state values must be float64")
        if not np.isfinite(self.mean) or not np.isfinite(self.scale) or self.scale <= 0.0:
            raise ValueError("target state must have finite mean and positive finite scale")

    def transform(self, minima: IntVector) -> NDArray[np.float32]:
        if minima.dtype != np.int64 or minima.ndim != 1 or np.any(minima <= 0):
            raise ValueError("raw minima must be positive int64")
        values = (np.log(minima.astype(np.float64)) - self.mean) / self.scale
        result = values.astype(np.float32)
        if not np.isfinite(values).all() or not np.isfinite(result).all():
            raise ValueError("target transform must remain finite through float32 emission")
        return np.ascontiguousarray(result)


@dataclass(frozen=True, slots=True)
class ArtifactFacts:
    artifact_id: str
    chain_id: int
    regime: str
    c: int
    k: int
    feature_state: FeatureState
    target_state: TargetState
    input_width: int
    action_head_width: int
    auxiliary_head_width: int

    def __post_init__(self) -> None:
        if not self.artifact_id or self.chain_id <= 0 or not self.regime:
            raise ValueError("artifact identity must be complete")
        if self.c <= 0 or self.k <= 0:
            raise ValueError("artifact C and K must be positive")
        if self.input_width != len(self.feature_state.names):
            raise ValueError("artifact input width must equal ordered feature width")
        if self.action_head_width != self.k or self.auxiliary_head_width != 1:
            raise ValueError("artifact must declare one K-wide action head and one scalar head")
        for state in (self.feature_state, self.target_state):
            if (state.chain_id, state.regime) != (self.chain_id, self.regime):
                raise ValueError("artifact state chain/regime must match artifact facts")
        if self.target_state.k != self.k:
            raise ValueError("artifact target-state K must match artifact K")

    def require_frame(self, frame: BlockFrame) -> None:
        if (frame.chain_id, frame.regime) != (self.chain_id, self.regime):
            raise ValueError("frame chain/regime does not match artifact")


@dataclass(frozen=True, slots=True)
class RequestedOriginWindow:
    first_origin_block: int
    last_origin_block: int

    def __post_init__(self) -> None:
        if self.first_origin_block < 0 or self.first_origin_block > self.last_origin_block:
            raise ValueError("requested origin window must be a nonempty inclusive block range")

    @property
    def count(self) -> int:
        return self.last_origin_block - self.first_origin_block + 1


class HistoricalDataset:
    """Small prototype of Issue 28's approved lazy five-tensor mapping."""

    def __init__(
        self,
        *,
        inputs: NDArray[np.float32],
        base_fees: IntVector,
        block_numbers: IntVector,
        origin_positions: IntVector,
        labels: IntVector,
        targets: NDArray[np.float32],
        c: int,
        k: int,
    ) -> None:
        self._inputs = torch.from_numpy(inputs.copy())
        self._base_fees = torch.from_numpy(base_fees.copy())
        self._blocks = torch.from_numpy(block_numbers.copy())
        self._origins = torch.from_numpy(origin_positions.copy())
        self._labels = torch.from_numpy(labels.copy())
        self._targets = torch.from_numpy(targets.copy())
        self._c = c
        self._k = k

    def __len__(self) -> int:
        return self._origins.numel()

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        if index < 0 or index >= len(self):
            raise IndexError("historical item index out of range")
        origin = int(self._origins[index])
        return {
            "inputs": self._inputs[origin - self._c + 1 : origin + 1].clone(),
            "label": self._labels[index].clone(),
            "target": self._targets[index].clone(),
            "base_fees": self._base_fees[origin + 1 : origin + 1 + self._k].clone(),
            "origin_block": self._blocks[origin].clone(),
        }


@dataclass(frozen=True, slots=True)
class PreparedHistoricalWindow:
    requested: RequestedOriginWindow
    support_first_block: int
    support_last_block: int
    dataset: HistoricalDataset


@dataclass(frozen=True, slots=True)
class HeadObservation:
    latest_rpc_head: BlockRef
    last_finalized_context: int
    first_actionable_target: int


@dataclass(frozen=True, slots=True)
class LiveInput:
    parent: BlockRef
    inputs: torch.Tensor


class MinBlockFeeOutput(NamedTuple):
    action_logits: torch.Tensor
    minimum_fee_z: torch.Tensor


@dataclass(frozen=True, slots=True)
class LiveDecision:
    parent: BlockRef
    output: MinBlockFeeOutput
    k: int
    broadcast_after_block: int
    target_block: int


def ethereum_forming_base_fee(
    parent_base_fee: int,
    parent_gas_used: int,
    parent_gas_limit: int,
) -> int:
    """Modern Ethereum EIP-1559 execution-base-fee recurrence."""

    if parent_base_fee <= 0 or parent_gas_limit <= 0:
        raise ValueError("parent fee and gas limit must be positive")
    if parent_gas_used < 0 or parent_gas_used > parent_gas_limit:
        raise ValueError("parent gas used must lie within its limit")
    gas_target = parent_gas_limit // 2
    if gas_target <= 0:
        raise ValueError("parent gas target must be positive")
    if parent_gas_used == gas_target:
        return parent_base_fee
    if parent_gas_used > gas_target:
        delta = parent_base_fee * (parent_gas_used - gas_target) // gas_target // 8
        return parent_base_fee + max(delta, 1)
    delta = parent_base_fee * (gas_target - parent_gas_used) // gas_target // 8
    return parent_base_fee - delta


def raw_feature_rows(frame: BlockFrame, names: tuple[str, ...]) -> FloatMatrix:
    core = np.column_stack(
        (
            np.log(frame.base_fees.astype(np.float64)),
            frame.gas_used.astype(np.float64) / frame.gas_limits.astype(np.float64),
        )
    )
    if names == CORE_FEATURES:
        if frame.chain_id == 1:
            raise ValueError("Ethereum artifact must retain its exact forming-fee feature")
        return np.ascontiguousarray(core, dtype=np.float64)
    if names == ETHEREUM_FEATURES:
        if frame.chain_id != 1:
            raise ValueError("non-Ethereum artifact must omit the forming-fee feature")
        forming = np.fromiter(
            (
                ethereum_forming_base_fee(int(fee), int(used), int(limit))
                for fee, used, limit in zip(
                    frame.base_fees,
                    frame.gas_used,
                    frame.gas_limits,
                    strict=True,
                )
            ),
            dtype=np.int64,
            count=frame.block_numbers.size,
        )
        return np.ascontiguousarray(
            np.column_stack((core, np.log(forming.astype(np.float64)))),
            dtype=np.float64,
        )
    raise ValueError("prototype supports only the approved mandatory feature tuples")


def prepare_historical_window(
    frame: BlockFrame,
    artifact: ArtifactFacts,
    requested: RequestedOriginWindow,
) -> PreparedHistoricalWindow:
    """Prepare exactly one requested inclusive origin window from one canonical frame."""

    artifact.require_frame(frame)
    support_first = requested.first_origin_block - artifact.c + 1
    support_last = requested.last_origin_block + artifact.k
    support = frame.select(support_first, support_last)
    raw = raw_feature_rows(support, artifact.feature_state.names)
    inputs = artifact.feature_state.transform(raw)
    origins = np.arange(
        requested.first_origin_block - support_first,
        requested.last_origin_block - support_first + 1,
        dtype=np.int64,
    )
    offsets = np.arange(1, artifact.k + 1, dtype=np.int64)
    windows = support.base_fees[origins[:, None] + offsets[None, :]]
    labels = windows.argmin(axis=1).astype(np.int64, copy=False)
    minima = windows[np.arange(origins.size), labels].astype(np.int64, copy=False)
    targets = artifact.target_state.transform(minima)
    dataset = HistoricalDataset(
        inputs=inputs,
        base_fees=support.base_fees,
        block_numbers=support.block_numbers,
        origin_positions=origins,
        labels=labels,
        targets=targets,
        c=artifact.c,
        k=artifact.k,
    )
    if len(dataset) != requested.count:
        raise AssertionError("historical preparation changed the exact requested origin count")
    return PreparedHistoricalWindow(
        requested=requested,
        support_first_block=support_first,
        support_last_block=support_last,
        dataset=dataset,
    )


def observe_heads(latest_rpc_head: BlockRef, confirmation_depth: int) -> HeadObservation:
    if confirmation_depth < 0 or confirmation_depth > latest_rpc_head.number:
        raise ValueError("confirmation depth must identify an existing older block")
    return HeadObservation(
        latest_rpc_head=latest_rpc_head,
        last_finalized_context=latest_rpc_head.number - confirmation_depth,
        first_actionable_target=latest_rpc_head.number + 1,
    )


def prepare_live(
    closed_rows: BlockFrame,
    artifact: ArtifactFacts,
    parent: BlockRef,
) -> LiveInput:
    """Prepare the live right edge; no outcome, target, mask, or mode flag exists."""

    artifact.require_frame(closed_rows)
    if closed_rows.block_numbers.size != artifact.c:
        raise ValueError("live preparation requires exactly C closed rows")
    if closed_rows.last_block != parent.number or closed_rows.block_hashes[-1] != parent.hash:
        raise ValueError("live rows must end at the exact frozen parent number and hash")
    if closed_rows.first_block != parent.number - artifact.c + 1:
        raise ValueError("live rows must be the exact consecutive C-row context")
    raw = raw_feature_rows(closed_rows, artifact.feature_state.names)
    inputs = torch.from_numpy(artifact.feature_state.transform(raw).copy()).unsqueeze(0)
    if inputs.shape != (1, artifact.c, artifact.input_width):
        raise AssertionError("live input shape does not match artifact facts")
    return LiveInput(parent=parent, inputs=inputs)


def require_action(k: int, K: int) -> int:
    if isinstance(k, bool) or not isinstance(k, int) or not 0 <= k < K:
        raise ValueError("action must be an integer in [0,K)")
    return k


def target_block(h: int, k: int, K: int) -> int:
    return h + 1 + require_action(k, K)


def broadcast_after_block(h: int, k: int, K: int) -> int:
    return h + require_action(k, K)


def validate_output(output: MinBlockFeeOutput, *, batch_size: int, k: int) -> None:
    if output.action_logits.shape != (batch_size, k):
        raise ValueError("action logits must have exact [B,K] shape")
    if output.minimum_fee_z.shape != (batch_size,):
        raise ValueError("auxiliary output must have exact [B] shape")
    if not torch.is_floating_point(output.action_logits) or not torch.is_floating_point(
        output.minimum_fee_z
    ):
        raise ValueError("both model outputs must be floating point")
    if (
        not torch.isfinite(output.action_logits).all()
        or not torch.isfinite(output.minimum_fee_z).all()
    ):
        raise ValueError("both model outputs must be finite")


def decide_live(
    prepared: LiveInput,
    artifact: ArtifactFacts,
    output: MinBlockFeeOutput,
) -> LiveDecision:
    validate_output(output, batch_size=1, k=artifact.k)
    selected = int(output.action_logits.argmax(dim=-1)[0])
    return LiveDecision(
        parent=prepared.parent,
        output=output,
        k=selected,
        broadcast_after_block=broadcast_after_block(prepared.parent.number, selected, artifact.k),
        target_block=target_block(prepared.parent.number, selected, artifact.k),
    )
