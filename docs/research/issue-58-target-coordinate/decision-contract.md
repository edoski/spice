# Issue 58 target-coordinate decision contract

Date: 2026-07-12

Status: resolved by Edo on 2026-07-12. Canonical resolution:
https://github.com/edoski/spice/issues/58#issuecomment-4951832231. Planning evidence
only; no production or artifact change.

## Fixed context

For an eligible closed-parent origin `h`, the approved action outcomes are the `K`
positive raw integer base fees per gas at `h+1...h+K`. The auxiliary scalar is an
offline training outcome, never an input or serving action. The action label remains
the deterministic earliest raw-integer minimum. This ticket owns only the scalar
target coordinate and frozen transform state.

## Decision 1 — exact target coordinate and state

**Status:** approved by Edo on 2026-07-12.

Use one exact target contract with no modes:

```text
target_id = hindsight_minimum_base_fee_per_gas_within_k

O_i     = min_{k=0,...,K-1} f_i,k
ell_i   = ln(O_i / (1 native wei/gas))
mu      = mean_training(ell_i)
sigma   = sqrt(mean_training((ell_i - mu)^2))
z_i     = (ell_i - mu) / sigma
ellhat_i = mu + sigma * zhat_i
```

- `O_i` is constructed from the complete raw integer outcome row before floating
  conversion. Require exactly `K` outcomes and `O_i > 0`. Never clip, replace, or use
  `log1p`.
- `ell_i` is the natural-log reporting view in `nat`; division by the declared unit
  makes the logarithm dimensionless.
- Fit `mu` and population `sigma` (`ddof=0`) in float64 from the declared target of each
  retained training origin exactly once. Require a nonempty population and finite
  `mu`, finite `sigma`, and `sigma > 0`. Add no epsilon or constant-target fallback.
- The model emits one finite scalar `zhat_i` in the standardized, dimensionless
  coordinate. Model dtype is float32 under the ordinary contract; this ticket does not
  choose the head implementation.
- Validation and testing consume the frozen training state. Issue 21's Smooth-L1 loss
  consumes `(zhat_i, z_i)`. Its log MAE/MSE consume `(ellhat_i, ell_i)` after the one
  affine decode above.
- Do not exponentiate, round, clip, or expose a native-fee prediction. Raw integer
  outcomes already own economic accounting, and serving has no scalar consumer.

Persist one concrete target-state record per independently trained `(chain, K)`
artifact. It contains the fixed target id, raw unit, natural-log reference, `ddof=0`,
float64 `mu` and `sigma`, target count, model dtype, chain and `K`, and content-bound
training-origin/corpus provenance. These are fixed fields, not a registry, transform
mode, generic scaler, or compatibility payload.

Use target-explicit report ids:

- `hindsight_minimum_base_fee_per_gas_within_k_smooth_l1_loss`;
- `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mae`;
- `hindsight_minimum_base_fee_per_gas_within_k_natural_log_mse`.

Issue 21 still owns numeric Smooth-L1 `beta`, the regression coefficient, exact
reducers, and report serialization. Issue 23 still owns the later concrete head/task
module. Issue 47 owns which training origins fit this state.

## Why this candidate

- The paper requires only a future minimum fee, logarithmic fee variables, a scalar
  head, and Smooth L1. It does not specify target mapping, normalization, unit, or loss
  constants.
- The coherent reference branch uses `log1p` plus training z-score, but conflicting
  branches use min-max state and the target generator is absent. It is lineage evidence,
  not authority.
- Selected modern K=5 outcomes are strictly positive. Across Ethereum, Polygon, and
  Avalanche, the largest observed `log1p(x)-ln(x)` was about `4.2e-5`; adding one wei
  buys no useful domain behavior.
- K=5 natural-log target population standard deviations were about `1.08`, `0.59`, and
  `1.40` for Ethereum, Polygon, and Avalanche. A frozen per-artifact z-score removes
  this arbitrary chain/K scale before Issue 21 chooses common loss numerics.
- Current SPICE already fits a float32 log-target z-score, but adds `1e-8`, names the
  z-output as a log fee, uses stale same-row geometry, and never persists its transform
  state. Reloaded artifacts cannot interpret the scalar. The clean contract replaces
  those defects rather than wrapping them.

Evidence:

- [Current-code audit](current-code.md)
- [Paper/reference red-team](paper-redteam.md)
- [Auxiliary-head conceptual audit](../auxiliary-fee-regression-head-conceptual-audit.md)
- [NumPy natural logarithm](https://numpy.org/doc/stable/reference/generated/numpy.log.html)
- [NumPy population standard deviation](https://numpy.org/doc/2.3/reference/generated/numpy.std.html)
- [PyTorch Smooth L1](https://docs.pytorch.org/docs/stable/generated/torch.nn.modules.loss.SmoothL1Loss.html)

## Resolution

Edo approved the complete contract. The canonical tracker resolution owns the decision.
Issue 21 may now choose Smooth-L1 `beta` and the regression coefficient; this ticket
authorizes no production change and infers neither numeric.
