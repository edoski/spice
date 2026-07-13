# Issue 58 paper/reference target-coordinate red team

Date: 2026-07-12

Scope: evidence for Issue 58 only. This report does not choose Smooth-L1 `beta`, the
regression coefficient, head architecture, serving exposure, features, or context.

Evidence roots:

- professor paper
  `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`, SHA-256
  `2afa36d5c82cc2f8be854707fad91b86562d399896b9ee163decd75f470d4b5c`;
- paper reference repository `/Users/edo/dev/python/ICDCS-Model-Training` at clean commit
  `bcf80b92877941e3b05a7dc5138560ffe41df27e`;
- [auxiliary conceptual audit](../auxiliary-fee-regression-head-conceptual-audit.md).

None of these three sources is authority for the unresolved coordinate. The paper is
underspecified, the repository contains conflicting experiments, and the audit explicitly
treats both codebases as candidates rather than authority
([audit lines 5-16](../auxiliary-fee-regression-head-conceptual-audit.md#L5-L16)). The
approved SPICE contracts do fix the raw future geometry and raw unit: for each origin,
`f[i,k]` is the raw integer chain-native target base fee per gas at `h+1+k`, and
`O[i]=min_k f[i,k]`
([Issue 48 lines 110-115](../issue-48-temporal-evaluation/decision-contract.md#L110-L115)).
Issue 58 must choose only the coordinate built from that fixed truth.

## What the sources actually specify

| Concern | Professor paper | Reference repository | Result |
| --- | --- | --- | --- |
| Raw scalar | The temporal task identifies the future minimum-cost block in the next bounded interval and estimates only the associated base fee (Sec. IV-A, PDF p. 5). It gives no indexed target formula, tie rule, raw unit, or target builder. | The coherent classifier consumes precomputed `minBaseFee`; it does not construct it (`train_model_classific.py:68-90`, `:159-164`). Committed raw CSVs contain neither `minBaseFee` nor `minBlock` (Ethereum header (`ICDCS-Model-Training/dataset/eth_block_data.csv#L1`)). | The semantic idea supports the approved hindsight minimum. It cannot validate exact `h+1...h+K` construction or provenance. |
| Log mapping | The paper says fee-related variables use “a logarithmic scale” (Sec. VI-A, PDF p. 8). It does not name base, offset, zero policy, numerical unit, or inverse. | The coherent branch applies `np.log1p` to `minBaseFee` (`train_model_classific.py:159-164`). | `log1p` is lineage evidence, not a paper requirement. |
| Target normalization | The paper explicitly assigns train-split standardization to features, not to the regression target (Sec. VI-A, PDF p. 8). | The coherent branch fits target mean and population standard deviation on training `log1p` targets and adds `1e-8` (`train_model_classific.py:174-215`). Older branches instead fit train-range min-max state and silently protect a zero range with `1e-8` (`train_model.py:119-175`; `train_model2.py:121-186`). | Training-only z-scoring is coherent, but the repository contradicts itself and its epsilon repair violates the clean failure rule. |
| Output coordinate | The paper says a task-specific MLP predicts a scalar fee (Sec. VI-A, PDF p. 8), without coordinate or output-domain semantics. | The coherent heads emit one unconstrained scalar (`train_model_classific.py:275-296`, `:327-360`). | A scalar linear output is compatible with a standardized log coordinate, but does not select it. |
| Decode and persistence | The paper defines neither. | The notebook first applies `prediction * fee_sd + fee_mu` to recover the log view, then separately applies `expm1` for a native-looking view (`testchain2.ipynb:1252-1256`, `:1320-1344`). The coherent checkpoint saves weights, all stats, and config (`train_model_classific.py:587-595`). | The affine log-view decode and co-persisted fitted state are reusable. Notebook native inversion is not required. |
| Unit | The paper alternates conceptual base fee with a spatial USD chart; it never declares the temporal regression target unit. | Raw datasets carry separate `base_fee_per_gas`, token price, and `base_fee_usd_per_gas` columns, while the unavailable target files prevent verification of `minBaseFee` units (Ethereum header (`ICDCS-Model-Training/dataset/eth_block_data.csv#L1`)). | Use the already-approved SPICE raw unit, native wei/gas. Do not infer USD conversion or cross-chain pooling. |

The existing audit reaches the same narrow conclusion: retain the hindsight minimum over
the approved action set, but do not copy old geometry, inferred horizons, clipping, or
notebook decoding
([audit lines 31-36](../auxiliary-fee-regression-head-conceptual-audit.md#L31-L36),
[54-67](../auxiliary-fee-regression-head-conceptual-audit.md#L54-L67),
[108-118](../auxiliary-fee-regression-head-conceptual-audit.md#L108-L118)).

## Red-team findings

**Future leakage.** `O[i]` legitimately uses `h+1...h+K` as a training outcome, never as
an input. Compute the raw integer minimum before any floating conversion. Fit target state
only from the declared target element of each retained training origin, once per origin;
freeze it for validation and testing. This follows the approved training-only population
rule ([Issue 47 lines 122-134](../issue-47/issue-47-owner-decisions.md#L122-L134)). The reference
repository cannot prove this because its target generator and target-bearing splits are
absent. Copying its precomputed columns would preserve an unverifiable same-row or
cross-boundary dependency.

**Log and unit ambiguity.** Prefer `ln`, not `log1p`. The raw domain is strictly positive;
invalid zero or negative fees must fail. `log1p` adds an arbitrary one wei/gas and exists
mainly to accept zero. Natural log also matches the approved closed-parent base-fee feature
mapping ([Issue 47 lines 150-159](../issue-47/issue-47-owner-decisions.md#L150-L159)). Define the
argument as a ratio to `1 native wei/gas`; the log view is then dimensionless and its
error unit is a natural-log unit (`nat`). The numerical mapping remains `ln(O[i])` when
`O[i]` is represented in native wei/gas.

**Cross-chain and horizon scale.** Never pool target state across chains. Native wei on
Ethereum, Polygon, and Avalanche denotes different native assets even though the numerical
denomination is atomic units per gas. `O[i]` also shifts with `K`. Fit one state for each
independently trained `(chain, K)` artifact. Training-only z-scoring costs two scalars and
makes the Smooth-L1 coordinate finite and dimensionless across these distinct cells; this
avoids forcing Issue 21 to compensate for arbitrary unit and distribution scale. This
does not choose its numeric `beta` or regression coefficient.

**Silent repair.** Require a positive target count, finite mean, and finite strictly
positive population standard deviation. Fail otherwise. Do not add epsilon, clip targets
or predictions, replace a scale, drop origins, or refit on held-out data. The reference
repository's `+1e-8` and min-max fallbacks are examples to reject.

**Output meaning.** The scalar predicts the hindsight minimum fee, not the fee at the
offset head's selected action. The outputs can disagree when classification is wrong
([audit lines 78-82](../auxiliary-fee-regression-head-conceptual-audit.md#L78-L82)). Keep
the scalar auxiliary: no action decode, chain selection, confidence gate, or serving claim
follows from it.

**Unnecessary inverse and state.** Issue 21 requires only target-coordinate loss and an
affinely decoded log view; it explicitly requires no native inverse merely for scoring
([Issue 21 lines 181-225](../issue-21-predictive-diagnostics/decision-contract.md#L181-L225)).
Do not implement `exp`, `expm1`, rounding, clipping, or a predicted native-fee view. Raw
future integers already supply economic truth. Persist only the two fitted scalars and
their population provenance, not a transform framework, mode, registry, raw-target array,
or compatibility path.

## Lean candidate contract

Use literal target id `hindsight_minimum_target_base_fee_per_gas_within_k`, log-view id
`natural_log`, and raw unit `native_wei_per_gas`. For each `(chain, K)` artifact:

```text
O_i     = min_{k=0,...,K-1} f_i,k                     integer native wei/gas
ell_i   = ln(O_i / (1 native wei/gas))                natural-log view, unit nat
mu      = mean_training(ell_i)
sigma   = sqrt(mean_training((ell_i - mu)^2))         population std, ddof=0
z_i     = (ell_i - mu) / sigma                        training target coordinate
ellhat_i = mu + sigma * zhat_i                        required log-reporting decode
```

The model emits one finite unconstrained scalar `zhat_i` per origin. Smooth L1 consumes
`(zhat_i, z_i)`; Issue 21 owns `beta` and the regression coefficient. Log MAE/MSE consume
`(ellhat_i, ell_i)`. No target-row value enters inputs. No native prediction or inverse
exists.

Fit and persist `mu` and `sigma` in float64, plus training target count and content-bound
training-origin provenance identifying chain and `K`. The fixed schema declares target
id, raw unit, log reference, `ddof=0`, and model coordinate; do not turn those constants
into runtime modes. Emit the model coordinate in the model dtype and perform the frozen
log-view decode/metric accumulation in float64.

Issue 21 can substitute the literal ids once:

- `hindsight_minimum_target_base_fee_per_gas_within_k_smooth_l1_loss`, dimensionless;
- `hindsight_minimum_target_base_fee_per_gas_within_k_natural_log_mae`, unit `nat`;
- `hindsight_minimum_target_base_fee_per_gas_within_k_natural_log_mse`, unit `nat^2`.

This is the smallest coherent synthesis: exact approved raw truth, one standard log,
two training-fitted scalars, one scalar output, one affine reporting decode, and no native
inverse.
