# Fixed-block comparability and exhaustive replay

Status: research input for [Choose the temporal decision, action, and protocol-regime contract](https://github.com/edoski/spice/issues/46) and [Prototype and choose temporal evaluation and thesis-evidence semantics](https://github.com/edoski/spice/issues/48). It approves neither a final `K` nor an action unit.

## Recommendation

Use exhaustive replay of every eligible origin as the primary result for each predeclared, protocol-regime-contained evaluation window. The primary unit is one eligible block-origin, weighted equally. At origin `h`, context ends at closed parent `h`; targets are `h+1..h+K`; `k=0` denotes the forming block. Ethereum may use its exact parent-derived forming-fee feature; Polygon and Avalanche retain parent-only inputs. This is a candidate causal geometry, not approval of the open action-unit choice.

Report each chain separately. Equal `K` is fair only for the narrow **block-event opportunity** estimand: conditional on the same declared action width, what is the model's outcome over the next `K` chain-native block opportunities? It normalizes the number of candidate block offsets and the decision/action cardinality. It does **not** normalize elapsed time, request exposure, transaction inclusion probability, fee currency/level, gas-weighted expenditure, market regime, or statistical independence.

Pair the primary table with realized elapsed-time summaries from each origin (median, IQR, and tails to `h+K`) and a named time-defined sensitivity window. Do not collapse chains into one headline. If the thesis instead claims an equal-deadline user experience, choose chain-specific `K_c` from a predeclared time deadline and call that a different estimand. It compares equal wall-clock opportunity, but has unequal action spaces and model difficulty.

Retain Poisson replay only if the thesis has a real request-arrival claim: e.g., requests arrive uniformly in eligible wall-clock time at a stated rate and do not affect the trace. Otherwise it contributes Monte Carlo noise and ambiguity, not information. No simulator framework is warranted.

## Why equal K is limited but valid

Ethereum's EIP-1559 base fee is derived from parent state ([EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)); Polygon's modern rules and Avalanche's post-Granite cadence/fee behavior are not interchangeable parent-known mechanisms ([PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md), [ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times)). Equal `K` therefore does not create like-for-like economics or causality. It is defensible only after each chain has a valid same-geometry corpus and after windows do not cross a fee/protocol regime boundary.

Cadence makes the distinction material: the frozen 36-second artifacts have widths 4 (Ethereum), 19 (Polygon), and 23 (Avalanche), and the prior audit observed post-Granite Avalanche truncation and Polygon cadence drift. Fee autocorrelation and overlapping `K`-target horizons mean adjacent origins are paired observations on one realized trace, not independent replications. Regimes change both cadence and fee process. Equal `K` should thus be described as a within-chain block-opportunity score, with cross-chain comparison as a structured descriptive comparison, not an IID three-chain experiment.

Same-`K` and chain-specific-`K` must not share a metric name. Same-`K` fixes candidate count and changes realized delay; `K_c` fixes a deadline and changes candidate count, oracle opportunity, class balance, and prediction difficulty. Economic results additionally need their unit stated: mean per-origin base-fee saving weights origins equally; ratio of total gas-weighted base-fee spend weights economic exposure. Neither is transaction profit without priority fees, inclusion, gas, and latency utility.

## Old 300- and 1,200-block evidence

The frozen evidence remains useful as an audit of the old artifacts, selected regimes, and sensitivity to **evaluation-window length**. It is not evidence for the proposed fixed-block action contract.

`lstm_36s_block_count_quartile_eval.yaml` selects `block_poisson_replay` (`window_blocks: 1200`, 50 repetitions); `lstm_36s_block300_quartile_eval.yaml` selects `block_poisson_replay_300` (300, 200). Both use `arrival_rate_per_block: 0.3`. Their three artifacts have widths 4/19/23, so neither 300 nor 1,200 is per-decision `K`. The TODO's 06/07 scanner makes contiguous 300/1,200-anchor windows and strata-selects 108 windows per chain. Each suite item itself has exactly that many samples, so `latest_start_offset=0`: the block evaluator does not choose a different subwindow there; it repeatedly Poisson-reweights duplicate decisions within the same selected window. Expected events are about 18,000 per evaluation in both designs (1200×0.3×50; 300×0.3×200). The exports/figures therefore answer selected-window, sampled-event questions, not one prediction at every eligible origin.

The historical claims that Ethereum was positive, Polygon slightly negative, and Avalanche variable remain archived descriptive observations under that old evaluator. They must be relabelled, not promoted as outcomes under the new geometry. Rerun is required for any claim about forming-block validity, fixed `K`, equal deadline, cross-chain superiority, or uncertainty. The 300/1,200 selections can remain as predeclared regime-stratified **evaluation windows** if their selection rule is frozen before the rerun; their duration and realized `K`-horizon time must be reported. Their overlapping/selected windows and one training seed preclude treating plotted repeat CIs or Pearson p-values as deployment, regime, or seed uncertainty.

This trace is from `src/spice/conf/evaluator/{block_poisson_replay,block_poisson_replay_300}.yaml`, the two benchmark configs above, `benchmarks/scripts/scan_block_count_quartile_windows.py`, their `src/spice/conf/evaluations/*block*_quartile.yaml` suites, `benchmarks/exports/*block*_quartile*`, and the 06/07 section of `TODO.md`. The linked figures and exports were already hash-audited in [the TODO 06/07 audit](issue-53/chain-regime-results-audit.md).

## Replay estimands

For a predeclared eligible-origin set `O_W`, deterministic exhaustive replay estimates

`mean_{h in O_W} m(h)`.

Here `m(h)` is the deterministic realized metric from the frozen trace and fixed fitted artifact. It estimates a uniformly selected **eligible block-origin** in `W`. One origin occurs once; duplicated Poisson arrivals are not invented. Rolling-origin evaluation is standard, but overlapping multi-step targets create serially correlated losses ([Hyndman, *Forecasting: Principles and Practice*](https://otexts.robjhyndman.com/fpp3/tscv.html); [Diebold & Mariano](https://www.nber.org/papers/t0169)). Report the finite-window descriptive result, then quantify uncertainty across non-overlapping, predeclared temporal/regime windows or a dependence-respecting block bootstrap if interval estimation is essential. Do not use an IID origin standard error.

Current time Poisson replay samples a start uniformly, simulates exponential interarrivals for two hours at 0.05/s, maps each arrival to the latest sample timestamp, then discards the arrival time (`src/spice/evaluation/poisson_replay.py`). It estimates a random-window, time-arrival-weighted simulator target. Current block Poisson replay samples a 300/1,200-block subwindow and arrivals at 0.3/block (`block_poisson_replay.py`); it estimates a random-window, block-arrival-weighted target. Both can select an origin repeatedly, and window overlap changes their weighting. The paper explicitly used the former simulation—random two-hour trace windows, 50 repetitions, Poisson 0.05/s—and assumed immediate-next-block inclusion (local `ICDCS_2026.pdf`, p. 9). Reproduction is legitimate as a clearly labelled secondary paper-fidelity result, not a reason to retain it as the thesis primary.

For a *fixed* window and independent, non-interacting requests, homogeneous Poisson arrivals have uniform conditional locations ([MIT 6.262, §2.5](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/)). Thus the exact expected event mean is the exposure-weighted deterministic mean; the rate cancels. It does not cancel for workload totals, empty runs, queues, congestion, tail risk, or finite-ratio metrics. Randomizing window starts adds another inclusion kernel; a plain full-corpus mean is not the exact replacement for the old random-start estimator. The lean protocol deliberately changes that estimator to named windows.

## Smallest protocol

1. Freeze valid parent-known features, the forming-block eligibility rule, one `K`, metric denominator, named regime-contained block windows, and one time-defined sensitivity window before looking at outcomes.
2. For every eligible `h` whose `h+K` target is present, predict once and realize the decoded action once. Publish origin count, excluded origins and reason, realized `K`-horizon seconds, base-fee savings and oracle/regret decomposition.
3. Summarize per chain and per window. Keep full outcomes; no outcome-based bulk deletion. Treat windows/regimes, not replay repetitions, as the visible robustness unit.
4. Optionally add exactly one arrival-time replay only if a stated workload contract needs it. Preserve each arrival timestamp, define `tau` (parent close/availability or actual request time), map it to the latest available closed-parent state through a proved forming-block eligibility interval, and retain duplicate-event semantics. Otherwise it cannot validate `k=0` service semantics.

## Limits and red-team checks

Exhaustive replay is not automatically more externally valid: it changes a request-weighted target to an origin-weighted target, weights short and long blocks equally, and can be expensive in proportion to eligible origins (but is linear and removes the present repetition factor). A time-weighted estimand may be preferable for a real arrival process; then exposure intervals must be defined, especially for a forming block. Equal `K` is also unfair if one chain's `K` regularly exceeds the product's tolerable delay, if target availability differs, or if a window crosses a regime boundary. The present trace cannot infer counterfactual inclusion, priority-fee sufficiency, profit, causal upgrade effects, future-regime performance, or training-seed uncertainty.

The independent red-team criterion is therefore: reject the primary proposal if the owner selects a user-arrival/deadline claim, cannot state a valid forming-block eligibility interval, or needs finite-workload/queue behavior. In those cases retain a timestamp-preserving arrival model as primary and label block-origin replay as supplementary.
