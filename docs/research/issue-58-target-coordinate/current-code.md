# Issue 58 current auxiliary-target code audit

Date: 2026-07-12. Audited revision: `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`.

Scope: current target construction, transform state, scalar output, persistence,
decoding, reporting, and tests. This report does not choose Smooth-L1 `beta`, the
regression coefficient, or head architecture. No production code was changed.

## Finding

Current SPICE predicts one standardized natural-log target: the earliest reachable
minimum base fee in the current candidate window. The transform is fitted from training
origins only, but its mean and scale live only in process. Artifacts persist model
weights and the **input** scaler, not the auxiliary-target transform. Reloaded evaluation
and serving therefore compute the scalar output but cannot interpret it; both decode only
offset logits.

The production target geometry is stale. The timestamp compiler starts candidates at
the anchor row, while the approved contract is closed parent `h` with outcomes
`h+1...h+K`. Tests often hand-build `candidate_start_rows=anchor+1`, so they do not catch
the production off-by-one.

## Exact current flow

| Concern | Current behavior | Evidence |
| --- | --- | --- |
| Canonical fee | RPC `baseFeePerGas` is parsed directly as an integer. Feature preparation converts it to float64, repairs warmup nonfinite values to `1`, clamps every value below `1` to `1`, applies `np.log`, then stores float32. No gwei conversion or `log1p` occurs. The resulting unit is natural-log chain-native base-fee-per-gas, operationally `ln(wei/gas)` for EVM RPC data. | [`corpus/contract.py:40-51,131-163`](../../../src/spice/corpus/contract.py#L40), [`features/core.py:299-324`](../../../src/spice/features/core.py#L299) |
| Production candidate geometry | `candidate_start_rows = anchor_candidates`; the end is the right-inclusive timestamp horizon. Slot zero can therefore be the anchor row itself. | [`observed_time_window.py:352-363`](../../../src/spice/temporal/compilers/observed_time_window.py#L352) |
| Outcome matrix | The strict policy copies logged fees from consecutive candidate rows. Short physical windows receive post-window overflow values, but those slots are not reachable. | [`strict_deadline_miss.py:59-107`](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L59) |
| Raw scalar identity | No raw integer auxiliary scalar is retained. Target materialization replaces unreachable logged fees with `+inf`, takes first `np.argmin`, and gathers that float32 logged fee. For positive fees the monotone log preserves the raw minimum; clipping can collapse values `<=1`. | [`batch.py:13-35`](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L13) |
| Tie rule | `np.argmin` chooses the earliest reachable minimum. The offset label and scalar are derived from the same masked logged-fee row. | [`batch.py:21-30`](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L21) |
| Fit population | Runtime fitting receives only `train_samples.temporal_facts`. It materializes one minimum logged fee per retained training origin. Validation and test facts are built separately and never fit the state. | [`training_runtime.py:36-68`](../../../src/spice/modeling/training_runtime.py#L36), [`fixed_sequence_temporal.py:244-305`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L244) |
| Training normalization | `mean` and population `std` (`correction=0`) are calculated in float32 over those training scalar targets. `1e-8` is then added unconditionally. The loss target is `z=(ln_fee-mean)/std`. | [`min_block_fee_multitask/__init__.py:34-51`](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py#L34), [`loss.py:29-39`](../../../src/spice/prediction/families/min_block_fee_multitask/loss.py#L29) |
| Output coordinate | Head id `min_block_log_fee` has size one, but its unconstrained scalar output is actually `z`, not a logged fee. Every model family builds the same two-layer MLP from the shared encoded state. | [`outputs.py:9-20`](../../../src/spice/prediction/families/min_block_fee_multitask/outputs.py#L9), [`_heads.py:12-57`](../../../src/spice/modeling/families/_heads.py#L12) |
| In-process log view | Metrics invert only the z-score: `predicted_log_fee = output*std+mean`. They report `log_fee_mae` and `log_fee_mse`. There is no exponential/native inverse. | [`metrics.py:133-165,168-207,235-248`](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L133) |
| Action decode | Only masked offset logits determine `DecodedOffsets`. The scalar never changes the selected action. | [`min_block_fee_multitask/__init__.py:71-84`](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py#L71) |

## State, persistence, and consumers

`MinBlockFeeTrainingState` combines unrelated class weights with `fee_mean` and
`fee_std`. It coerces them to CPU float32 and caches device/dtype copies. Validation
requires only scalar rank and `std > 0`; nonfinite means, `NaN` scale, and positive
infinite scale are not rejected. It records no transform identity, log formula, unit,
population count, content identity, or training provenance
([`batch.py:84-145`](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L84)).

The final manifest contains authored config, prediction semantics, input `ScalerStats`,
sequence metadata, and temporal capability. Model parameters are saved separately.
Neither contains `MinBlockFeeTrainingState`
([`results.py:66-132`](../../../src/spice/modeling/results.py#L66),
[`artifacts.py:28-102`](../../../src/spice/modeling/artifacts.py#L28),
[`artifact_codecs.py:165-262`](../../../src/spice/storage/artifact_codecs.py#L165)).
The resumable training checkpoint also omits it; resume recomputes state from current
training facts before loading model/optimizer/policy state
([`persisted_training.py:47-78`](../../../src/spice/modeling/persisted_training.py#L47),
[`training_runner.py:61-90`](../../../src/spice/modeling/training_runner.py#L61)).

In-process final validation and the legacy internal test reuse the live fitted state, so
they can calculate all current diagnostics
([`persisted_training.py:93-124`](../../../src/spice/modeling/persisted_training.py#L93)).
The persisted training summary keeps only validation and internal-test total loss; it
discards component loss and both log errors
([`results.py:135-152,230-248`](../../../src/spice/modeling/results.py#L135)). Benchmark
conversion carries only that internal-test total loss despite named export columns for
the discarded diagnostics
([`result_records.py:101-125`](../../../src/spice/benchmarks/result_records.py#L101),
[`result_index.py:29-61`](../../../src/spice/benchmarks/result_index.py#L29)).

Reloaded offline evaluation reconstructs the model and offset decoder without target
state. It has no frozen-checkpoint regression-loss or log-view path
([`artifact_inference.py:79-192`](../../../src/spice/modeling/artifact_inference.py#L79),
[`scoring.py:55-74,119-152`](../../../src/spice/modeling/scoring.py#L55)). Live serving
does the same and exposes only the selected offset/wait fields
([`serving/inference.py:63-110`](../../../src/spice/serving/inference.py#L63),
[`serving/schemas.py:26-45`](../../../src/spice/serving/schemas.py#L26)). Inference still
requires every head, including the unused scalar, to be finite
([`scoring.py:136-158`](../../../src/spice/modeling/scoring.py#L136)).

## Current repairs and missing coverage

Two silent repairs affect this coordinate:

- raw base fees below `1` are clamped before natural log, with separate warmup
  nonfinite-to-`1` repair;
- a constant target population receives scale `1e-8` instead of failing or applying a
  declared constant-target rule.

There is no validation/test target clipping and no prediction clipping. The target
materializer masks unreachable actions with infinity; this is selection masking, not a
fee repair.

Focused tests cover target/offset agreement, earliest argmin, unreachable masking,
sample-order alignment, normalized loss, z-to-log MAE/MSE, and device-cache stability
([`test_min_block_fee_multitask.py:92-373`](../../../tests/prediction/test_min_block_fee_multitask.py#L92)).
They do not cover the production compiler's same-row candidate start, constant-target
state, nonfinite/malformed transform state, artifact persistence/reload, transform
provenance, or scalar output interpretation after reload. Model-family tests inspect
only offset-logit shape
([`test_models.py:169-195`](../../../tests/modeling/test_models.py#L169)).

## Clean-break recommendation

Place one family-owned deep seam immediately after the approved raw integer outcome
matrix `f[i,k]` is available and before loss/scoring:

```text
approved raw f[i,0:K]
    -> earliest label o[i] and raw hindsight minimum O[i], computed once
    -> fixed target mapping plus optional training-only fitted state
    -> scalar model coordinate z[i]
    -> loss view and z-to-declared-log reporting view
```

Use one concrete transform-state type, not a registry, mode, adapter, or generic scaler.
If normalization is approved, persist its fitted values, target count, dtype/unit, and
content-bound training provenance in the artifact and load the same state for validation
and testing. If normalization is rejected, keep no empty placeholder state. The mapping
formula should be fixed by code and artifact semantics; callers should not reconstruct
it from `fee_mean`/`fee_std` field names.

Keep native inverse absent. Issue 48 removed native-unit regression MAE, and serving has
no scalar consumer. The only needed decode is the exact model-coordinate to declared
log-reporting view required by Issue 21.

Clean-break deletions/replacements:

- replace the ambiguous `min_block_log_fee(s)` names with target-explicit
  hindsight-minimum names that distinguish raw, log-view, and model coordinates; retain
  no aliases;
- split target-transform state from class-weight state, then delete
  `ResolvedMinBlockFeeTrainingState` and its mutable device cache in favor of direct
  tensor conversion of the small frozen state;
- delete the `+1e-8` scale repair and raw-fee clamp from the target path under the
  approved fail-closed domain contract;
- delete duplicate hand-written z-score inversion from metrics; the transform seam
  should own the sole log-view conversion;
- do not add a native inverse, serving field, compatibility loader, transform framework,
  or migration path for archival artifacts.

Lean verification: one exact `h+1...h+K` target/tie fixture through the real compiler
seam, and one training-fit -> artifact round-trip -> validation/testing log-view fixture
that rejects malformed state. These test the interface and replace cache/legacy-shape
tests rather than layering transition coverage.
