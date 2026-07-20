from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
import pytest
import torch

from fable.min_block_fee import (
    MinBlockFeeOutput,
    TargetState,
    decode_action,
    fit_target_state,
    min_block_fee_loss,
    standardize_target,
)


def test_target_and_native_loss_match_hand_derived_fixture() -> None:
    raw_minima = np.array([1, 4, 16, 64], dtype=np.int64)
    target_state = fit_target_state(raw_minima)
    log_four = math.log(4.0)

    assert target_state.mean == pytest.approx(1.5 * log_four)
    assert target_state.standard_deviation == pytest.approx(math.sqrt(5.0) * log_four / 2.0)

    target_z = standardize_target(raw_minima, target_state)
    expected_z = np.array(
        [-3.0 / math.sqrt(5.0), -1.0 / math.sqrt(5.0), 1.0 / math.sqrt(5.0), 3.0 / math.sqrt(5.0)],
        dtype=np.float32,
    )
    np.testing.assert_allclose(target_z, expected_z)
    assert target_z.dtype == np.float32
    assert target_z.flags.c_contiguous

    labels = torch.tensor([0, 0, 1, 2], dtype=torch.int64)
    targets = torch.from_numpy(target_z)
    logits = torch.zeros((4, 3), dtype=torch.float32, requires_grad=True)
    predictions = (targets + torch.tensor([0.0, 0.5, 1.0, 2.0])).detach().requires_grad_()
    output = MinBlockFeeOutput(action_logits=logits, minimum_fee_z=predictions)

    loss = min_block_fee_loss(
        output,
        label=labels,
        target=targets,
    )
    log_three = math.log(3.0)
    expected_classification = torch.full((4,), log_three)
    expected_regression = torch.tensor([0.0, 0.125, 0.5, 1.5])
    expected_total = expected_classification + expected_regression

    torch.testing.assert_close(loss.classification_by_origin, expected_classification)
    torch.testing.assert_close(loss.regression_by_origin, expected_regression)
    torch.testing.assert_close(loss.total_by_origin, expected_total)
    torch.testing.assert_close(loss.mean_total, expected_total.sum() / 4.0)
    assert loss.mean_total.requires_grad
    assert not loss.total_by_origin.requires_grad
    assert not loss.classification_by_origin.requires_grad
    assert not loss.regression_by_origin.requires_grad

    loss.mean_total.backward()
    assert logits.grad is not None
    assert predictions.grad is not None


def _valid_output() -> MinBlockFeeOutput:
    return MinBlockFeeOutput(
        action_logits=torch.zeros((2, 2), dtype=torch.float32),
        minimum_fee_z=torch.zeros(2, dtype=torch.float32),
    )


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param(
            lambda: fit_target_state(np.array([1, 2], dtype="int32")),
            id="target-int64",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                _valid_output(),
                label=torch.tensor([0.0, 1.0]),
                target=torch.zeros(2),
            ),
            id="label-int64",
        ),
    ],
)
def test_owned_type_contracts_are_enforced(operation: Callable[[], object]) -> None:
    with pytest.raises(TypeError):
        operation()


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param(
            lambda: fit_target_state(np.array([1, 0], dtype=np.int64)),
            id="target-positive",
        ),
        pytest.param(
            lambda: fit_target_state(np.array([2, 2], dtype=np.int64)),
            id="target-nonconstant",
        ),
        pytest.param(
            lambda: standardize_target(
                np.array([1, -1], dtype=np.int64),
                TargetState(mean=0.0, standard_deviation=1.0),
            ),
            id="standardize-positive",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                MinBlockFeeOutput(
                    action_logits=torch.tensor([[math.inf, 0.0], [0.0, 0.0]]),
                    minimum_fee_z=torch.zeros(2),
                ),
                label=torch.tensor([0, 1]),
                target=torch.zeros(2),
            ),
            id="finite-output",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                _valid_output(),
                label=torch.tensor([0, 2]),
                target=torch.zeros(2),
            ),
            id="label-range",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                _valid_output(),
                label=torch.tensor([0, 1]),
                target=torch.tensor([0.0, math.nan]),
            ),
            id="finite-target",
        ),
    ],
)
def test_owned_value_contracts_are_enforced(operation: Callable[[], object]) -> None:
    with pytest.raises(ValueError):
        operation()


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param(
            lambda: min_block_fee_loss(
                MinBlockFeeOutput(
                    action_logits=torch.zeros(2),
                    minimum_fee_z=torch.zeros(2),
                ),
                label=torch.tensor([0, 1]),
                target=torch.zeros(2),
            ),
            id="logit-shape",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                _valid_output(),
                label=torch.tensor([[0, 1]]),
                target=torch.zeros(2),
            ),
            id="label-shape",
        ),
        pytest.param(
            lambda: min_block_fee_loss(
                _valid_output(),
                label=torch.tensor([0, 1]),
                target=torch.zeros(1),
            ),
            id="target-shape",
        ),
    ],
)
def test_loss_shape_contracts_are_enforced(operation: Callable[[], object]) -> None:
    with pytest.raises(ValueError):
        operation()


def test_decode_uses_native_first_index_argmax_and_ignores_auxiliary_values() -> None:
    output = MinBlockFeeOutput(
        torch.tensor([[3.0, 3.0, 2.0], [4.0, 4.0, -1.0]]),
        torch.tensor([math.nan]),
    )

    assert torch.equal(decode_action(output), torch.tensor([0, 0], dtype=torch.int64))
