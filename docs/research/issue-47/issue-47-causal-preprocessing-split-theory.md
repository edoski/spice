# Issue 47: causal preprocessing and split theory

**Status:** planning evidence. No owner choice is approved here.

**Scope:** external statistical and ML theory only. Current SPICE code, corpus contents, historical results, and old design documents are not authority for this report.

Terms below are marked **source fact**, **derived condition**, or **recommendation**. The distinction matters: the literature establishes leakage risks, but it does not choose SPICE's corpus contract, regime policy, context unit, or feature set.

## Lean candidate contract

The smallest defensible contract is:

1. Validate a canonical, ordered corpus at one seam. Fail on semantic defects. Do not silently deduplicate, clip, interpolate, or fill them in the modeling path.
2. Give every raw fact and derived feature an `available_at` instant. A sample is causal only when every feature dependency is available by its decision instant.
3. Keep each sample's complete transitive support—from the earliest raw dependency of its sequence, lags, and rolling features through the last target outcome—inside one declared protocol regime. Treat transition samples separately or exclude them.
4. Use fixed block-count context for a fixed-shape sequence model. Preserve wall-clock information with causal cadence and elapsed-time features. A true seconds context requires variable-length windows or explicit causal resampling.
5. Purge by each sample's actual target availability, not by a guessed row gap. At every role cutoff, remove earlier-role samples whose complete target is not available before the next role starts. Past feature context may overlap an earlier role.
6. Fit all data-dependent preprocessing on the active training set only. Freeze it for validation and every test. Feature, context-length, and scaler choices are model selection and use validation only.
7. Start with protocol-core features. Add calendar/cadence, elapsed time, explicit lags, rolling summaries, and priority-fee features as named ablations. A 45- or 77-feature count has no statistical authority.
8. Use per-feature `StandardScaler` after declared deterministic domain transforms, fitted once on unique training rows. Do not clip. Persist the statistics and inverse-transform scaled targets before reporting original-unit errors.

This contract follows the operational definition of leakage: information unavailable at prediction time must not influence fitting or model choice ([Kaufman et al., 2012](https://doi.org/10.1145/2382577.2382579); [scikit-learn leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)). Forecasting work shows that whole-series normalization, smoothing, feature extraction, and the wrong availability horizon can produce optimistic results ([Hewamalage, Ackermann, and Bergmeir, 2023](https://doi.org/10.1007/s10618-022-00894-5)).

## The point-in-time model

For sample `s`, define:

- `d(s)`: the instant the prediction/action is made;
- `X*(s)`: every transitive raw dependency of its model input, including history used inside lags and rolling features;
- `a(z)`: when fact `z` is knowable to the predictor, not its nominal event timestamp;
- `Y*(s)`: every raw outcome needed to form the target;
- `A_y(s) = max(a(z) for z in Y*(s))`: when the complete target becomes knowable.

**Derived condition — feature causality:**

```text
max(a(z) for z in X*(s)) <= d(s)
```

An event timestamp is insufficient. Delayed publication, finalization, receipt availability, and forming-versus-closed block state can make `available_at` later than event time. First-party point-in-time join documentation uses the same rule: retrieve the latest feature value available at the label/prediction time, never a later value ([Databricks point-in-time joins](https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series)). A backward as-of join selects a right-side key less than or equal to the left key; forward or nearest joins can select future values ([pandas `merge_asof`](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html)).

**Derived condition — complete-outcome fitting:** a sample may influence fitting or a selection decision made at cutoff `C` only if `A_y(s) <= C`. A decision-time split alone does not establish this.

## Canonical corpus: fail versus repair

These are project recommendations, not statistical theorems.

| Invariant at the canonical modeling seam | Response | Reason |
|---|---|---|
| Chain/network identity, source range, and regime tag are present and unambiguous | Fail | Otherwise feature and target meaning cannot be reconstructed. |
| Canonical row key is unique and strictly increasing; serialization order already matches it | Fail | Silent sorting or first/last duplicate choice hides upstream provenance defects. |
| If the artifact claims a complete block range, block keys are contiguous | Fail | Missing blocks change block-count lags, windows, targets, and context length. An intentionally sampled corpus needs an explicit different contract. |
| Timestamps are valid and nondecreasing | Fail | Same-resolution timestamps may tie; reversal breaks temporal support. |
| Required fields are present, finite, and in one declared native unit | Fail | A finite transformed value must not hide an invalid raw fact. |
| Protocol domains hold: positive fee/limit fields, nonnegative counts, bounded utilization facts, ordered percentiles where applicable | Fail | Clipping an impossible value creates plausible false data. |
| Known regime boundaries and feature-definition versions are recorded | Fail | A sample cannot prove one semantic definition without them. |
| Provenance and exact conversion rules are recorded | Fail | Offline replay and later audits need the original information set. |

Allowed canonicalization belongs in a separate explicit import step: lossless parsing, checked unit conversion, and deterministic representation normalization. It should produce a new identified artifact. The modeling compiler should consume canonical data and fail, not repair it again.

Do not treat statistical outliers as corrupt by default. Impossible values fail against protocol/schema rules. Distribution-based removal, winsorization, quantile thresholds, and imputation are fitted transformations and therefore training-only. Backfill and two-sided interpolation use future observations. Forward fill is causal only when the feature is explicitly defined as “last known value”; carry staleness/age and a missingness rule. Incomplete labels at the corpus tail are excluded, never shortened into a different target.

## Regime containment

**Source fact:** concept drift means the input/target relation changes over time ([Gama et al., 2014](https://doi.org/10.1145/2523813)). That fact does not itself require deleting boundary samples.

**Recommendation:** for a clean protocol-regime experiment, require one regime over `X*(s) union Y*(s)`. This includes hidden feature history. If a displayed sequence has `K` rows and its earliest row contains a trailing `W`-row statistic, the raw support reaches up to `K + W - 1` rows back. Merely checking the visible tensor and target window is insufficient.

Whole-sample containment is an estimand choice, not a leakage theorem. A live post-fork decision can causally observe pre-fork history. Excluding it creates a burn-in period but gives every retained sample one protocol definition. If transition behavior is scientifically important, analyze those samples as a named transition regime rather than mixing them silently into either side.

This rule concerns protocol regimes. An ordinary train/validation boundary is not a regime boundary. Causal validation context may reach backward into training time.

## Split roles and complete-outcome purging

Let `T_v` and `T_t` be the instants immediately before the first validation and testing decisions. Let `T_end` be the final analysis instant after all retained testing outcomes mature. The approved project contract has exactly three roles.

| Role | Decision-time candidates | Retain only when | Permitted use |
|---|---|---|---|
| Training | `d(s) < T_v` | `A_y(s) <= T_v` | Fit model parameters and every fitted transform. |
| Validation | `T_v < d(s) < T_t` | `A_y(s) <= T_t` | Every development choice, including feature/context/scaler choice, HPO, and early stopping. Never fit on validation rows. |
| Testing | `d(s) > T_t` | `A_y(s) <= T_end` and the full outcome lies inside the declared testing window | Final thesis evaluation only after the procedure and claims freeze. |

Use strict `< first_next_decision_timestamp` when timestamps cannot express within-timestamp ordering. Prefer explicit ordered instants so `<= cutoff` has one meaning.

This is **purging**: remove a training/selection sample whose forward outcome is not complete at the applicable information cutoff. A fixed row `gap` is only a proxy. Scikit-learn's `TimeSeriesSplit.gap` excludes a fixed number of samples and separately warns that equal sample spacing is required for equal-duration fold metrics ([`TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)). Variable label horizons or irregular block cadence need the actual `A_y(s)` check.

An **embargo** is different: it removes observations after an evaluation block before later observations return to training in non-forward or combinatorial splits. In one monotone training → validation → testing path, testing observations never return to an earlier fit, so a generic post-test embargo adds no causal guarantee. Add one only for a separately stated dependence/inference goal or real publication latency. Encode known latency in `available_at` first.

Autocorrelation is not itself target leakage. Nor does an arbitrary gap make observations independent. Bergmeir, Hyndman, and Koo show that ordinary K-fold can be valid for a restricted purely autoregressive setting with uncorrelated errors; those assumptions cannot be presumed for a nonstationary protocol task ([2018 paper](https://doi.org/10.1016/j.csda.2017.11.003)). Forward evaluation remains the closer operational estimand. Multiple rolling origins improve information over one arbitrary holdout but must preserve the same fit/selection boundary ([Tashman, 2000](https://doi.org/10.1016/S0169-2070(00)00065-0)).

Past overlap is allowed. A validation input may use already available rows from training time. A retained training target may use those same historical rows, provided its target was complete before validation began. This mirrors online prediction. It does mean anchor-level errors are dependent, so the number of overlapping windows is not an IID sample size.

## Fitted statistics and role changes

**Source fact:** even unsupervised, data-dependent preprocessing—including rescaling and variance-based feature selection—can bias cross-validation when computed before the split ([Moscovich and Rosset, 2022](https://doi.org/10.1111/rssb.12537)). Model-selection criteria can themselves be overfit, with effects comparable to differences between algorithms ([Cawley and Talbot, 2010](https://www.jmlr.org/papers/v11/cawley10a.html)).

Fit on the active training set only:

- means, variances, medians, IQRs, min/max, quantiles, clipping/outlier limits;
- imputers, category vocabularies, feature selection, PCA, learned encoders;
- empirical cadence used to derive a sequence length;
- target transforms and class weights.

Deterministic unit conversions, protocol recurrences, predeclared logarithms with validated domains, and calendar formulas are not fitted statistics. Trailing lag/rolling calculations are also not global fits, but every operand must satisfy `available_at <= decision`.

The approved baseline does not refit on validation or testing. Training remains the
only fitted population, and one persisted scaler/state serves validation, testing,
and replay. Testing reports rather than selects. If testing later guides development,
the resulting selection-bias limitation is disclosed; the valuable range is retained
and no replacement-data state machine is introduced.

## Feature availability and parity contract

The project-specific inventory must contain one row per emitted feature. This table gives the required semantics, not a substitute for that inventory.

| Feature kind | Exact unit | Earliest valid `available_at` | Causal rule |
|---|---|---|---|
| Finalized block fee | base unit/gas; for EVM chains, wei/gas | After the declared block-close/finality condition | A forming decision cannot read the finalized current row. |
| Protocol-derived forming value | Same native unit as the protocol field | When every parent/state input to the exact recurrence is available | Recompute from the earlier information snapshot. If equality is not proved for that chain/regime, call it unavailable or give an estimate a different feature name. |
| Gas used / gas limit / transaction count | gas / gas / count | After the source block closes | Current-forming values are future facts. Past values are valid. |
| Utilization | dimensionless ratio | Maximum availability of numerator and denominator | Validate domains before division. |
| Decision calendar | UTC timestamp components or dimensionless cyclic encoding | At the actual decision instant | Do not substitute the later realized block timestamp. |
| Cadence | seconds | After both referenced closed-block timestamps are known | Previous cadence is causal; current forming-block duration is not complete. |
| Lag `k` | Same unit as source | Availability of the source value at `t-k` | Positive past lag only. A negative lag is future leakage. |
| Trailing rolling mean/min/max/std | Source unit; variance uses squared unit; normalized variants dimensionless | Maximum availability of every member | Right-align. Shift or use an open right endpoint when the current source is unavailable. Centered or forward windows leak. Declare width unit, endpoint inclusion, `min_periods`, and `ddof`. |
| Priority-fee percentile | wei/gas for these EVM corpora | After all receipts/transactions in the source block needed by the percentile are available | Historical percentiles are valid; current-forming realized percentiles are not. |
| Elapsed time | seconds | Decision instant, if both endpoints are already known | State the origin: previous block, sequence start, regime start, or experiment start. They are different features. |
| Scaled value | dimensionless | After its raw feature is available, using frozen training statistics | Offline and online must use identical formula, feature order, and stored statistics. |

Pandas documents that a time-sized rolling window contains a variable number of observations, while an integer window has a fixed observation count; `center=True` labels at the center and therefore includes later observations relative to that label ([`DataFrame.rolling`](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html)). Its open-right endpoint exists specifically to compute “up to” but not including the present ([window guide](https://pandas.pydata.org/docs/user_guide/window.html#rolling-window-endpoints)).

Offline/online parity means the same information snapshot produces the same feature value and unit. Shared implementation is the leanest proof; Google recommends reusing feature code and directly measuring training/serving skew ([Rules of ML, rules 29, 32, and 37](https://developers.google.com/machine-learning/guides/rules-of-ml#training-serving_skew)). A historical finalized row is not a valid shortcut for a forming feature unless the value is exactly reconstructible from earlier state. Approximation error needs its own feature contract and fixture.

## Feature groups: baseline first, signal must earn complexity

**Recommendation:** start with the smallest protocol-core fee level and pressure facts whose decision-time availability is proved per chain/regime. Then evaluate named groups on the same purged validation origins:

1. elapsed time and previous cadence, to retain wall-clock information under block-count context;
2. decision-time calendar;
3. explicit past lags;
4. trailing rolling summaries;
5. priority-fee facts, only when the objective and corpus support them.

Sequence models already receive past rows, so explicit lags and rolling summaries may duplicate their receptive field. They may still improve a small model. Keep them only for stable, material held-out benefit. Every added lag/window expands raw history, warmup, and regime-containment requirements.

Existing 45- and 77-feature catalogs do not survive by default. Neither does a paper catalog. Catalog membership is a hyperparameter chosen on validation, with a protocol-core control. Testing cannot justify additions or deletions.

## Block-count versus seconds context

| Choice | Meaning | Benefit | Cost/risk |
|---|---|---|---|
| Fixed `K` blocks | Last `K` causally available event rows | Fixed tensor, direct block semantics, lean batching | Wall-clock span varies with cadence. |
| Fixed `S` seconds | All causal rows in `(d-S, d]` | Stable physical horizon | Variable row count, masks/packing, and explicit empty/gap behavior. |
| Resampled seconds grid | Causal state on regular time bins | Fixed tensor and physical-time semantics | Imputation policy becomes model semantics; nearest/two-sided interpolation can use future data. |

Irregularly sampled series do not naturally produce fixed-dimensional inputs ([Li and Marlin, 2020](https://proceedings.mlr.press/v119/li20k.html)). Time-aware recurrent work also notes that ordinary LSTM steps assume comparable elapsed intervals and adds elapsed-time handling for irregular observations ([Baytas et al., 2017](https://www.kdd.org/kdd2017/papers/view/patient-subtyping-via-time-aware-lstm-networks)).

**Recommendation:** configure a direct block count `K`, then include causal elapsed-time/cadence features and report the observed seconds-span distribution. Do not claim `K` blocks equals a fixed number of seconds.

Sequence length is a model hyperparameter. Choose it with a small predeclared validation-only grid, then freeze it. A corpus-wide median cadence used to derive `K` leaks future distribution information. A training-only median avoids that leak but still changes the meaning to “approximately `S` seconds under past median cadence” and can drift by chain/regime. Direct `K` is clearer. No exact value follows from theory.

Track feature history separately from sequence length. A `K`-row tensor containing `W`-row trailing features has up to `K + W - 1` raw rows of history. Median-derived sequence length and long engineered windows must not be described as one nominal lookback.

## Scaler choice, clipping, and inversion

`StandardScaler` stores per-feature training mean and population variance (`ddof=0`), uses scale `1` for a zero-variance feature, is sensitive to outliers, and supports `inverse_transform` ([official API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)). `RobustScaler` stores training median and IQR and is less influenced by outliers ([official API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html)). `MinMaxScaler` anchors to training extrema, does not reduce outlier influence, and can map later values outside its configured range; clipping destroys exact inversion ([official API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html)).

**Recommendation:** use fixed per-feature z-score scaling after explicit domain
transforms. Fit each feature on unique physical rows covered by retained training
contexts, once per row, with population variance. Persist feature order, mean, scale,
dtype, and training identity. Transform validation, testing, replay, and serving with
the same frozen state. Do not update it during evaluation. If a retained feature has
exactly zero training variance, fail by feature name and require an explicit feature
contract decision; do not silently retain, drop, mask, or epsilon-adjust it.

Do not clip held-out values by default. Values beyond the training range are distribution-shift evidence and may contain useful signal. If numerical instability forces clipping, fit thresholds on training only, name the transform, count/report saturation, and accept that inversion is many-to-one.

Scale a regression target with separate training-only state only when optimization
needs it. Inverse-transform predictions with that same state before original-unit
metrics or economic accounting. Add no input inverse interface and no dormant robust,
min-max, or no-scaling alternative; a later alternative requires concrete optimization
evidence and a separate decision.

## Minimal executable split fixture

Each row `i` publishes feature `x_i` at time `i`. Prediction occurs at `i + 0.1`. Target `y_i` uses outcome rows `i+1` and `i+2`; the complete target is available when row `i+2` closes at `i+2.9`. Context length is three rows.

| Role | Candidate anchors | Next information cutoff | Retained | Purged |
|---|---|---:|---|---|
| Training | `2, 3, 4` | `5.1` | `2` | `3, 4` |
| Validation | `5, 6, 7` | `8.1` | `5` | `6, 7` |
| Testing | `8, 9, 10, 11` | analysis complete at `14.0` | `8, 9, 10, 11` | none |

Validation anchor `5` uses context rows `{3,4,5}`. Rows `{3,4}` are also the outcome rows of retained training anchor `2`. This overlap is allowed: both are historical before decision `5.1`, while no retained training target reaches row `5`.

```python
HORIZON = 2
CONTEXT = 3

def decision(i: int) -> float:
    return i + 0.1

def context_rows(i: int) -> set[int]:
    return set(range(i - CONTEXT + 1, i + 1))

def outcome_rows(i: int) -> set[int]:
    return set(range(i + 1, i + HORIZON + 1))

def target_available_at(i: int) -> float:
    return i + HORIZON + 0.9

roles = {
    "training": (range(2, 5), 5.1),
    "validation": (range(5, 8), 8.1),
    "testing": (range(8, 12), 14.0),
}

kept = {
    role: [i for i in candidates if target_available_at(i) <= cutoff]
    for role, (candidates, cutoff) in roles.items()
}

assert kept == {
    "training": [2],
    "validation": [5],
    "testing": [8, 9, 10, 11],
}
assert max(context_rows(5)) < decision(5)       # all validation inputs exist
assert context_rows(5) & outcome_rows(2) == {3, 4}  # causal past overlap
assert max(outcome_rows(2)) < 5                 # no train target reaches validation
assert target_available_at(2) <= 5.1
```

The production fixture should replace synthetic floats with ordered decision/open/close instants, exact `available_at` fields, regime IDs, and the approved target geometry. Its key assertions should remain this small.

## Claims common practice does not justify

- “Chronological anchors are enough.” False when earlier labels mature in a later role.
- “Any train/test overlap is leakage.” False. Causal past context overlap mirrors online use; forward target dependence is the defect.
- “Add a gap to be safe.” A guessed gap can be too short, wastefully long, or irrelevant. Check actual target availability.
- “Autocorrelation requires an embargo.” Not by itself. Embargo serves a declared resampling/dependence purpose; it is not a substitute for point-in-time correctness.
- “Unsupervised preprocessing on all data is safe.” False; rescaling and feature selection can bias evaluation.
- “A robust or min-max scaler is safer.” Not universally. They choose different statistics; clipping can destroy signal and inversion.
- “Median block time turns blocks into seconds.” Only approximately under the fitted cadence distribution.
- “A large feature catalog is conservative because it keeps signal.” It also enlarges model selection, history support, leakage surface, and explanation cost. Stable held-out benefit must decide.

## Primary sources

- Shachar Kaufman et al., [“Leakage in Data Mining: Formulation, Detection, and Avoidance”](https://doi.org/10.1145/2382577.2382579), 2012.
- Hansika Hewamalage, Klaus Ackermann, and Christoph Bergmeir, [“Forecast Evaluation for Data Scientists: Common Pitfalls and Best Practices”](https://doi.org/10.1007/s10618-022-00894-5), 2023.
- Amit Moscovich and Saharon Rosset, [“On the Cross-Validation Bias due to Unsupervised Preprocessing”](https://doi.org/10.1111/rssb.12537), 2022.
- Gavin Cawley and Nicola Talbot, [“On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation”](https://www.jmlr.org/papers/v11/cawley10a.html), 2010.
- Christoph Bergmeir, Rob Hyndman, and Bonsoo Koo, [“A Note on the Validity of Cross-Validation for Evaluating Autoregressive Time Series Prediction”](https://doi.org/10.1016/j.csda.2017.11.003), 2018.
- Leonard Tashman, [“Out-of-sample Tests of Forecasting Accuracy: An Analysis and Review”](https://doi.org/10.1016/S0169-2070(00)00065-0), 2000.
- João Gama et al., [“A Survey on Concept Drift Adaptation”](https://doi.org/10.1145/2523813), 2014.
- Steven Cheng-Xian Li and Benjamin Marlin, [“Learning from Irregularly-Sampled Time Series: A Missing Data Perspective”](https://proceedings.mlr.press/v119/li20k.html), ICML 2020.
- Inci Baytas et al., [“Patient Subtyping via Time-Aware LSTM Networks”](https://www.kdd.org/kdd2017/papers/view/patient-subtyping-via-time-aware-lstm-networks), KDD 2017.
- First-party implementation references: [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), [`TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html), [`StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html), [`RobustScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.RobustScaler.html), [`MinMaxScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html), [pandas rolling windows](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.rolling.html), and [pandas as-of joins](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html).
