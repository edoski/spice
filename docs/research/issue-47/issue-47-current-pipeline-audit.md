# Issue 47 current pipeline audit

Status: local code-and-test audit for issue 47. No production code, config, corpus,
artifact, ADR, or remote state changed. Current code is evidence, not authority.

## Verdict

The current offline pipeline is internally consistent with its old “row `t` is both
the last input and candidate zero” design. It is not consistent with the approved
issue-46 contract:

- freeze latest closed parent `(h, hash)` at decision time;
- ordinary context ends at `h`;
- targets and actions are exactly `h+1 .. h+K`, with action `k` targeting
  `h+1+k`;
- `K` is one shared fixed block-opportunity count, not a seconds-derived width;
- Ethereum alone adds one exact forming-base-fee scalar derived from `h`;
- Polygon and Avalanche use parent-only facts;
- every origin needs complete causal context and all in-regime outcomes;
- serving fails closed and uses the same action meaning.

The strongest conflicts are direct:

1. [`_build_timestamp_window_store`](../../../src/spice/temporal/compilers/observed_time_window.py#L332)
   sets `candidate_start_rows = anchor_rows`; sequence tensorization includes the
   anchor. Training therefore consumes feature row `t` and labels candidate zero
   with fee row `t`.
2. [`_action_count_for_delay`](../../../src/spice/temporal/compilers/observed_time_window.py#L313)
   derives action width from seconds and nominal/recent-median spacing. At the
   default 36 seconds this yields 4 Ethereum, 19 Polygon, and 23 Avalanche actions,
   not one shared `K`.
3. The 45- and 77-feature catalogs read finalized `base_fee[t]`, realized
   `timestamp[t]`, and trailing transforms through `t`. No exact Ethereum child-fee
   constructor or scalar exists.
4. Internal train/validation/test boundaries split forecast origins without purging
   earlier origins whose labels cross the next boundary.
5. Historical evaluation and live serving call the same feature formulas but assign
   different meanings to their final row. Serving also anchors at a confirmation-depth
   row and can recommend a target already closed at the current head.

The current 45/77 catalogs and median-derived sequence length therefore do not
survive as contracts. Individual causal formulas may survive only after regrouping
against the approved information set. Old artifacts are archival, as issue 46
already requires; compatibility machinery has no role.

## Exact execution path

Training follows this path:

1. [`run_training`](../../../src/spice/modeling/pipeline.py#L228) loads the canonical
   block frame and calls `prepare_training_dataset`.
2. [`prepare_training_dataset`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L244)
   sorts/deduplicates rows, builds all features globally, compiles timestamp-bounded
   samples, applies an optional training cutoff, makes an 80/10/10 count split,
   calibrates fixed sequence length, filters early rows, repeats the cutoff and split,
   fits the input scaler on train context rows, and materializes target facts for all
   three roles.
3. [`plan_training_runtime`](../../../src/spice/modeling/training_runtime.py#L36) fits
   class weights and target-fee mean/std from train labels only, then builds shuffled
   train and ordered validation batches.
4. [`run_training_fit`](../../../src/spice/modeling/training_runner.py#L43) fits and
   selects the best state on validation loss.
5. [`_evaluate_split_metrics`](../../../src/spice/modeling/persisted_training.py#L93)
   evaluates best-state validation and internal test metrics. Tuning calls the same
   path for every trial; Optuna selects on best validation loss.
6. [`build_training_artifact_manifest`](../../../src/spice/modeling/artifacts.py#L28)
   persists feature semantics, input scaler, sequence metadata, and temporal
   capability. It does not persist fitted target-fee/class-weight state because
   external economic replay needs decoded offsets, not prediction-loss metrics.

External evaluation follows
[`prepare_artifact_inference_context`](../../../src/spice/modeling/artifact_inference.py#L79):
load the artifact, rebuild and fingerprint-check features, require the scenario start
to be at or after the training cutoff, select scenario origins, reuse artifact
sequence length and scaler, decode offsets, then run economic replay. It is a separate
external evaluation role, not the internal test split.

Live serving follows
[`OnlinePredictionService._prepare_online_sample`](../../../src/spice/serving/inference.py#L144):
fetch confirmed blocks, build the same feature table, use the last confirmed row as
the single anchor, reuse artifact scaling, and expose an action mask limited by the
requested wait. This is a separate right-edge algorithm, but it does not share the
offline row meaning.

## Canonical rows: current fail and repair behavior

[`CanonicalBlockRow`](../../../src/spice/corpus/contract.py#L17) stores block number,
timestamp, base fee, gas facts, transaction count, optional size/blob facts, and
optional priority-fee summaries. It does not store block hash, parent hash, or a
protocol-regime identifier. Under the approved split identity contract, offline rows
instead require a content-bound corpus identity plus chain and block number; the
current manifest does not yet provide that content binding. Live decisions
separately require the recorded parent hash.

Current checks are distributed:

| Place | Fails | Repairs or permits |
|---|---|---|
| [`canonicalize_block_frame`](../../../src/spice/corpus/contract.py#L168) | Missing canonical columns or strict cast failure | Selects/casts canonical columns; does not validate order, gaps, duplicates, chain, or timestamps |
| [`validate_block_frame`](../../../src/spice/corpus/contract.py#L172) | Empty frame, null required core facts, duplicate block numbers, multiple chain ids | Permits block gaps and non-increasing/equal timestamps |
| [`validate_contiguous_block_frame`](../../../src/spice/corpus/validation.py#L181) | Reports gaps, duplicates, chain mismatch, and null selected source facts | Sorts by block number before checking; still does not check timestamp monotonicity |
| [`load_block_frame`](../../../src/spice/corpus/io.py#L53) | Delegates the narrower `validate_block_frame` checks | Sorts by block number; reads only canonical columns, so extra stored columns disappear |
| Dataset [`_prepare_blocks`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L31) | Empty input | Sorts by timestamp, silently keeps the first duplicate block number, then sorts by block number |
| Feature [`_build_feature_table`](../../../src/spice/features/core.py#L215) | Missing selected source columns, nonfinite required sources/features | Sorts again by block number |
| Temporal compiler [`_build_timestamp_window_store`](../../../src/spice/temporal/compilers/observed_time_window.py#L332) | Decreasing timestamps, insufficient warmup/history/outcome support | Permits equal timestamps |

Acquisition materialization fails a non-clean contiguous/exact-window report before
publication. Production training usually receives unique loaded rows. The silent
deduplication still exists in the modeling and live paths and can hide malformed or
conflicting input. A clean-break contract should validate once and fail; sorting a
valid frame for deterministic order is the only harmless normalization here.

There is no whole-sample regime containment anywhere in corpus metadata, feature
semantics, temporal capability, sample compilation, artifact compatibility, or
evaluation selection. Corpus names encode historical eras informally; code does not.

## Current sample and action geometry

Let current code row `r` be the sample anchor.

- Context start is the first row with timestamp at least
  `timestamp[r] - lookback_seconds`.
- Candidate start is exactly `r`.
- Candidate end is the first row after `timestamp[r] + delay_seconds`.
- A strict-deadline post-window row must exist.
- Action width is `floor(max_delay_seconds / slot_spacing_seconds) + 1`, with a
  minimum of two under positive default delays.
- Reachable outcomes are the first `min(timestamp-window row count, action width)`
  rows from `r`.
- If an action offset exceeds the observed timestamp-window row count, it realizes
  at the first post-window row. The action mask still marks every fixed-width action
  available.
- The prediction label is the `argmin` of reachable log base fees. Log is monotone,
  and NumPy `argmin` chooses the first tie, so raw-minimum and earliest-tie semantics
  happen to match issue 46.

Relevant symbols are
[`_build_timestamp_window_store`](../../../src/spice/temporal/compilers/observed_time_window.py#L332),
[`CompiledProblemStore.candidate_windows`](../../../src/spice/temporal/problem_store.py#L154),
[`_prepare_outcome_facts`](../../../src/spice/temporal/execution_policy/strict_deadline_miss.py#L59),
and
[`materialize_min_block_fee_targets`](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py#L13).

Sequence tensorization slices `context_start : anchor + 1`; see
[`_fill_dense_sequence_input_rows`](../../../src/spice/modeling/representations/sequence_inputs.py#L200).
Thus offline `r=t` is both the last input and candidate zero. The approved store
geometry should instead be `anchor=h`, `candidate_start=h+1`, with exactly `K`
outcomes. `CompiledProblemStore` already permits `candidate_start_rows >= anchor_rows`,
and many unit fixtures already use `anchor+1`; the contradiction is concentrated in
the concrete compiler and serving preparation, not forced by the shared store.

## Roles, cutoffs, and confirmed forward-label leakage

[`_chronological_split_indices`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L220)
splits the selected origin list by count. Default fractions are 80% train, 10%
validation, and the remainder internal test. It does not inspect any candidate or
outcome row at either internal boundary.

A hand-executable fixture using the production compiler had 23 one-second rows,
two-second delay, three actions, and 20 valid origins:

```text
train origins       0..15   last train outcomes       [15, 16, 17]
validation origins 16..17   last validation outcomes  [17, 18, 19]
test origins       18..19   last test outcomes         [19, 20, 21]

train label rows in validation-origin interval: [16, 17]
validation label rows in test-origin interval:   [18, 19]
```

Training class weights and target-fee mean/std are fitted from these train labels.
They are “train role only” in code, but the train role itself contains outcomes from
the nominal validation period. This is real forward-target leakage, not causal past
context overlap.

The optional external training cutoff is stronger but incomplete.
[`_training_sample_indices`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L102)
keeps a sample when `timestamp[candidate_end - 1] < cutoff`. That excludes the last
timestamp-bounded candidate at or after the cutoff. It ignores the strict-deadline
fallback row at `candidate_end`.

An executable five-row probe with timestamps `[0, 1, 4, 5, 6]`, cutoff `3`, and
three fixed actions produced:

```text
cutoff check row/timestamp:        row 1 / timestamp 1
materialized action outcome rows:  [0, 1, 2]
materialized outcome timestamps:   [0, 1, 4]
overflow mask:                     [false, false, true]
```

The sample passes the cutoff while one action outcome lies after it. Under the
approved fixed-`K` contract, purge against the last of all `K` outcome rows; there is
no seconds-window overflow special case.

Role meanings in current execution:

| Role | Current use | Boundary problem |
|---|---|---|
| Train/fit | Gradient updates; input scaler, class weights, target mean/std | Earlier labels cross validation boundary |
| Validation | Every-epoch best-state selection and early stopping; Optuna objective | Earlier labels cross internal-test boundary |
| Internal test | Best-state prediction metrics after training | Computed for every HPO trial by `run_trial_training`, so it is not operationally sealed even though code does not select on it |
| External evaluation | Separate artifact/corpus scenario and economic replay | Start must be after training cutoff, but scenario selects origins only; outcomes may extend beyond the requested end and no regime compatibility exists |

Timestamp evaluation selects anchors in `[start, end)`. Block evaluation requires one
selected anchor for each requested contiguous block. Neither route requires the full
context and outcome span to remain inside the selected protocol regime or requested
role window. Causal context overlap across roles is fine; forward outcome overlap is
the defect.

## Exact current feature catalogs

All formulas are trailing or shifted. Feature construction over the whole table is
not itself a fit leak: there are no learned feature statistics, and each formula only
reads its row or earlier rows. The problem is which row is called available at the
decision instant.

For this table, `r` means the row passed to the model. Offline training treats `r` as
candidate zero. Live serving treats `r` as the last confirmed parent.

| Outputs | Exact formula at row `r` | Unit | Current availability consequence |
|---|---|---|---|
| `log_base_fee_per_gas` | `ln(max(base_fee[r], 1))` | natural-log wei/gas | Reads finalized `r`; illegal when offline `r` is forming target. Code does not derive Ethereum child fee from `r-1`. |
| `log_prev_gas_used`, `log_prev_gas_limit`, `log_prev_tx_count` | `ln(1 + max(raw[r-1], 0))` | natural-log count | Safe for old offline virtual row, but one row stale in live closed-parent preparation. |
| `prev_gas_utilization` | `gas_used[r-1] / gas_limit[r-1]` | ratio | Same safe-offline/stale-live split. |
| `seconds_since_previous_block` | `timestamp[r] - timestamp[r-1]` | seconds | Uses realized timestamp of forming target offline; only closed-row-safe when `r=h`. |
| `hour_sin`, `hour_cos` | sine/cosine of UTC hour from `timestamp[r]` | unitless | Uses realized target timestamp offline, not decision time or closed parent. |
| `dow_sin`, `dow_cos` | sine/cosine of UTC weekday from `timestamp[r]` | unitless | Same. |
| `roll25/100_{mean,std,min}_logfee` | trailing 25/100 values of `log_base_fee_per_gas` through `r`; std uses `ddof=0` | natural-log wei/gas | Inherits finalized `base_fee[r]` dependency. |
| `dlog_base_fee` | `logfee[r] - logfee[r-1]` | log ratio | Inherits finalized `r`. |
| `base_fee_trend` | `+1` if `dlog >= 0`, else `-1` | unitless | Inherits finalized `r`. |
| `dlog_base_fee_lag1..6` | `dlog_base_fee[r-j]` | log ratio | Block lags; lag 1 and later exclude current `r`, but the catalog exposes them beside illegal current-row fee features. |
| `prev_gas_utilization_lag1..6` | `prev_gas_utilization[r-j]`, hence raw block `r-j-1` | ratio | Causal block lags; stale relative to a direct closed-parent row representation. |
| `roll10/50/200_{mean,std,min}_logfee` | trailing block windows through `r`; std uses `ddof=1` | natural-log wei/gas | Inherits finalized `r`. |
| `roll10/50/200_{mean,std}_prev_gas_utilization` | trailing windows of shifted utilization through `r`, hence raw blocks ending `r-1`; std `ddof=1` | ratio | Causal offline; one-row stale live. |
| `prev_priority_fee_p10/p50/p90` | raw percentile from block `r-1` | wei/gas | Requires `priority_fee_percentiles` enrichment; causal offline, one-row stale live. |
| `prev_priority_fee_spread` | `p90[r-1] - p10[r-1]` | wei/gas | Same. |
| `log_prev_priority_fee_p50`, `log_prev_priority_fee_spread` | `ln(1 + max(value, 0))` | natural-log wei/gas | Same. |
| `dlog_prev_priority_fee_{p50,spread}` | difference between shifted log values at `r` and `r-1`, i.e. raw blocks `r-1` and `r-2` | log ratio | Causal offline; freshest input is still one row stale live. |
| `dlog_prev_priority_fee_{p50,spread}_lag1..6` | prior block lags of those deltas | log ratio | Causal block lags. |
| `roll10/50/200_{mean,std}_log_prev_priority_fee_{p50,spread}` | trailing block windows through shifted value at `r`; std `ddof=1` | natural-log wei/gas | Causal offline; one-row stale live. |
| `elapsed_seconds` | `timestamp[r] - timestamp[first row of supplied table]` | seconds | No future read, but its origin changes with offline corpus/evaluation support/live fetch window, so values lack offline/live parity and encode dataset position. |

Definitions live in
[`_base_fee.py`](../../../src/spice/features/sets/core_fee_dynamics/_base_fee.py),
[`_block_facts.py`](../../../src/spice/features/sets/core_fee_dynamics/_block_facts.py),
[`_fee_context.py`](../../../src/spice/features/sets/core_fee_dynamics/_fee_context.py),
[`_priority_fee.py`](../../../src/spice/features/sets/core_fee_dynamics/_priority_fee.py),
[`_time.py`](../../../src/spice/features/sets/core_fee_dynamics/_time.py), and
[`_transforms.py`](../../../src/spice/features/sets/core_fee_dynamics/_transforms.py).

Catalog composition is exact:

- `core_fee_dynamics`: 45 outputs = fee level 1 + shifted block facts 4 +
  cadence/calendar 5 + 25/100 fee context 6 + fee delta/trend/lags 8 +
  utilization lags 6 + 10/50/200 fee context 9 + utilization rolls 6.
- `core_fee_dynamics_with_priority_fee`: those 45 plus 32 priority-fee outputs = 77.
- `core_fee_dynamics_elapsed_position`: those 45 plus `elapsed_seconds` = 46.
- There is no catalog combining priority fees and elapsed position.
- There is no `exact_forming_base_fee` feature, no chain-specific available-at table,
  and no unit or availability field in `FeatureSpec` or persisted feature semantics.

The full 45/77 configs have global warmup 200 rows. Every feature declares
`history_seconds=0`; temporal lookback supplies the only seconds history. Arbitrary
subsets are allowed, with dependencies and max warmup derived dynamically.

## Sequence context and normalization

The compiler first builds variable seconds-bounded contexts. The dataset builder then
converts them to one fixed block count:

```text
median_dt = median(positive timestamp deltas in raw train calibration rows)
sequence_length = round(lookback_seconds / median_dt)
sequence_length = clip(sequence_length, min_length, max_length)
```

See [`_compute_seq_len`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L41)
and [`_training_calibration_timestamps`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L73).
The default bounds are 64..4096. For nominal cadence and 600 seconds, this means
Ethereum `50 -> 64`, Polygon `300`, and Avalanche `375`; actual artifacts use the
training median, not nominal cadence. The final context is therefore a fixed block
count whose realized seconds vary. The original 600-second containment is discarded
by [`_store_with_fixed_context`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L121).

Calibration uses rows covered by the provisional raw train split only. After fixed
context removes a prefix, the code recomputes the 80/10/10 split, so the final train
boundary is not identical to the calibration boundary. This does not introduce
future-role data—the final train extends later—but it makes “sequence length fitted
on the final train role” inexact.

Input normalization is one per-feature `sklearn.preprocessing.StandardScaler` fit on
the union of rows covered by final train contexts. Each covered row receives one
vote, regardless of how many train windows contain it. Validation, internal test,
external evaluation, and serving reuse the fitted means/scales. This part is
training-only and causal at the feature level.

[`ScalerStats`](../../../src/spice/temporal/input_normalization/scaling.py#L20) persists
only `means` and `scales`. Transform is `(x - mean) / scale` in float32. Current
behavior:

- sklearn uses population variance (`ddof=0`) and scale 1 for a constant feature;
- transform silently replaces zero or negative persisted scales with 1;
- means/scales are not checked for equal length, feature count, or finiteness;
- a one-element scaler can silently broadcast across all features;
- there is no clipping;
- there is no input inverse-transform path.

The prediction family separately fits train-label class weights and scalar minimum-log-fee
mean/std. Regression targets are standardized; metrics invert them with
`prediction * fee_std + fee_mean`. That state is reused for final validation/test
scoring but not persisted for external replay. See
[`_fit_training_state`](../../../src/spice/prediction/families/min_block_fee_multitask/__init__.py#L34)
and
[`compute_batch_loss_and_state`](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py#L168).

Current code supplies no evidence that median-derived context is better than a fixed,
declared block history. The median conversion adds a fitted statistic, clipping rule,
two-stage split, and variable realized meaning. It is causally safer than a full-table
median, but it has no clean-contract preservation claim.

## Offline/live parity

Historical train and external-evaluation preparation share the same feature builder,
fixed sequence length, scaler, and compiler. Their numerical preprocessing is aligned.
Live serving shares feature formulas and scaler but not the decision row:

| Layer | Final input row | Action-zero interpretation |
|---|---|---|
| Offline train/evaluate | historical `t`, including finalized fee and realized timestamp at `t` | candidate row `t` |
| Serving feature preparation | confirmed row `h` | response maps offset 0 to target `h+1` |

Consequences:

- Offline current fee/fee transforms use target `t`; live uses parent fee `h`.
- Offline shifted gas and priority facts at `t` correctly use `h`; live at `h` uses
  `h-1`, losing the freshest closed facts.
- Live has no exact Ethereum `base_fee[h+1]` scalar.
- Live constructs a dummy one-row candidate store at `h` only to satisfy model input;
  response code then adds one to the block target. The shared action/outcome mapper is
  bypassed.

Serving confirmation depth defaults to two. `fetch_confirmed_window` chooses
`observed = latest - 2`; response code defines `target = observed + offset + 1`.
For offset zero, that target is already below the RPC head. The mobile scheduler
returns when `currentBlock >= broadcast_after_block` and signs/sends only then. It
does not freeze and preserve an unchanged signed transaction at decision time. See
[`fetch_confirmed_window`](../../../src/spice/serving/live_blocks.py#L51),
[`predict`](../../../src/spice/serving/inference.py#L63), and
[`waitForBroadcastBlock`](../../../apps/mobile/src/scheduler.ts#L10).

This contradicts issue 46's actionable-head, `k=0` immediate broadcast, and `k>0`
target-parent trigger. Serving must be replaced or fail closed; it cannot be described
as parity-safe.

## Test evidence and missing tests

Focused verification passed:

```text
uv run pytest -q \
  tests/features/test_core_fee_dynamics.py \
  tests/temporal/test_observed_time_window.py \
  tests/temporal/test_input_normalization.py \
  tests/modeling/test_dataset_builders.py \
  tests/serving/test_inference.py \
  tests/serving/test_live_blocks.py

32 passed in 2.42s
```

Tests accurately lock current mechanics:

- [`test_observed_time_window_builds_timestamp_bounded_windows`](../../../tests/temporal/test_observed_time_window.py#L112)
  explicitly asserts `candidate_start_rows == anchor_rows` and Ethereum width 4.
- Feature tests verify shifted facts, trailing lags/rolls, 45/77 config alignment,
  finite warmup behavior, and priority enrichment.
- Dataset tests verify provisional train-only median calibration, explicit training
  cutoff against `candidate_end - 1`, fixed context, and origin-window inference.
- Scaler tests verify unique covered-row fitting, constant scale 1, and the current
  silent repair of nonpositive scales.
- Serving tests cover only max-offset arithmetic, confirmed-window fetching, and
  basic artifact-chain rejection.

Missing acceptance evidence:

- no fixture proves `context_end=h`, outcomes `h+1..h+K`, and zero forward target
  dependency across every role cutoff;
- no test permits causal past-context overlap while purging crossing outcomes;
- no whole-sample protocol-regime containment test;
- no per-feature available-at and unit contract;
- no Ethereum parent-to-forming-fee exactness/parity test;
- no Polygon/Avalanche parent-only assertion;
- no historical-versus-live same-origin feature vector and action mapping test;
- no scaler feature-count/finiteness validation or explicit no-clipping test;
- no sealed internal-test behavior around HPO.

The current-row compiler assertion is a transition-hostile regression test and should
be replaced, not retained. Generic store, execution-policy, prediction, and evaluator
tests already demonstrate `candidate_start = anchor + 1` works structurally.

## Ownership and deletion test

These are genuine seam findings, using the codebase-design vocabulary.

| Module/seam | Deletion test | Finding |
|---|---|---|
| `prepare_training_dataset` / `prepare_inference_dataset` | Deleting it spreads feature build, geometry, role assignment, scaler use, and prepared facts across workflows | Deep module worth retaining. Put complete-sample role assignment and its assertions behind this interface. |
| `CompiledProblemStore` plus its context/candidate views | Deleting it spreads aligned row geometry across representation, labels, replay, and serving | Valuable shared module. Strengthen its approved invariants; do not replace it with parallel arrays in callers. |
| Problem compiler registry and abstract `CompiledProblemContract` methods | One concrete compiler exists; deleting the registry removes dispatch/config/codec plumbing without redistributing competing behavior | Hypothetical seam. Clean break can call one direct sample compiler and one direct metadata codec. |
| Execution-policy registry/config base | One `strict_deadline_miss` Adapter exists | Registry is hypothetical. Keep one deep action/outcome mapping interface shared by labels, replay, and serving; delete one-entry dispatch. |
| Feature catalog dependency graph | Three catalog ids are compositions of one formula family; issue 47 is choosing fixed groups, not runtime plugins | If groups become fixed, one explicit feature-frame builder plus declared output/unit/availability table gives more locality than `SourceSpec`/`FeatureSpec` graph traversal. Do not layer a new feature framework over it. |
| `_train_scaler` and `_scale_store` wrappers | Deleting each removes a pass-through without moving policy | Shallow wrappers. Retain the small normalization module, not the wrappers. |
| `context_row_multiplicities` in row scaling | Multiplicity values are reduced immediately to `> 0`; no weighting survives | Name/interface overstates behavior. Replace with direct covered-row selection unless another caller needs counts. |
| Historical and live preparers | Algorithms differ at the right edge, so deleting either would move distinct behavior | Two implementations are justified. They must consume the same approved information-set and action interfaces; do not hide them behind a mode flag. |

The lean implementation direction exposed by current code is direct:

1. validate one canonical, content-bound, regime-labelled block frame and fail on corruption;
2. build closed-row features at `h`, plus one Ethereum-only exact forming-fee scalar;
3. compile context ending `h` and exactly `K` outcomes `h+1..h+K`;
4. assign roles by complete outcome end, allowing causal past-context overlap;
5. fit input and target statistics on the purged train role only;
6. persist and strictly validate feature order, scaler dimensions, context length,
   regime, and fixed `K`;
7. make historical replay and serving consume the same action mapping, with a focused
   live right-edge preparer.

No compatibility shim, migration reader, registry, or abstraction is needed to reach
that shape.

## Approved three-role deletion consequence

The owner later approved exactly `training / validation / testing` and deleted the
internal-test role. The current internal suffix is not sealed: every tuning trial
scores it, persists `test_total_loss`, and exposes it to benchmark collection even
though Optuna selects only validation loss. It provides no distinct lifecycle or
leakage barrier.

The clean implementation therefore deletes:

- `DatasetSplitIndices.test`, `PreparedTrainingSampleRoles.test`, and the third split
  construction/preparation branch;
- the leftover-fraction-as-test configuration contract;
- per-trial and persisted-training test scoring;
- `test_samples` and `test_total_loss` from runtime summaries, codecs, inspection,
  reporting, and benchmark `training_test` records;
- tests whose only purpose is that internal metric path.

Keep only training and validation inside training preparation. Testing remains the
separate chronological evaluation path with predeclared named reporting windows.
Current evaluation identity omits corpus/window facts; exact evaluator mechanics are
owned by the canonical Issue 48 resolution. No freeze/spent/replacement-data state
machine is required. Clean retraining uses the new artifact shape; no legacy summary
codec or dormant role mode survives.
