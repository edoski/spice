# Temporal preprocessing and learning-semantics audit

**Status:** investigation map; no proposal in this document is approved.

**Scope:** the temporal module's corpus boundary, feature construction, sample compilation, fixed-sequence preparation, normalization, split policy, targets, and the preprocessing assumptions that reach training, evaluation, and serving.

**Primary criterion:** theoretical correctness first, then the smallest implementation an undergraduate reader can explain. A more elaborate method needs measured value, not merely plausibility.

## Verdict

The preprocessing path is not theory-cleared yet. Recovered design history materially changes the interpretation of offset zero: it was intentionally defined as the current/forming block under a block-open information set, not accidentally as an already finalized observed block. Commit `e0b2e68e` removed a genuinely unsafe same-block-closed route, retained current `base_fee[t]` on the theory that it is derivable from parent state before execution, and lagged finalized facts such as gas use and transaction count to `t-1`. `ARCHIVE.md:9-36`, `PROGRESS.md:243-255`, and `src/spice/features/ARCHITECTURE.md:28-51` record that intent.

Several local choices are sound: finalized block facts are deliberately lagged, rolling transforms are trailing, the standard scaler is fitted from training-context rows only, the external training cutoff excludes labels whose outcomes cross that cutoff, and the saved scaler is reused at inference. Those strengths do not resolve the following higher-level blockers and proof gaps:

| Priority | Finding | Why it matters |
|---|---|---|
| Blocker | Offline training/replay instantiate the intentional forming-block action `h+k`, while serving starts from a confirmed head and targets `h+k+1` | Two individually plausible decision clocks are currently presented as one deployed action |
| Blocker | A seconds-bounded outcome window is forced into a block-offset action width derived from one nominal or median interval | Some actions become deadline misses while some valid in-deadline blocks are ignored; the effect is common on current Polygon and Avalanche data |
| Blocker | Adjacent train/validation/test splits do not purge samples whose label horizon crosses the next boundary | Earlier-role targets use outcomes from the later role |
| Major proof gap | Unlagged timestamp/cadence features, Poisson-arrival association, and current-fee availability are not proved at the block-open instant for every chain and fork | Row-causal formulas are not necessarily available or actionable at the transaction decision time |
| Major | The timestamp-derived lookback is overwritten by a globally estimated fixed row count | “600 seconds of history” is not what the model consistently receives |

These are definition problems, not tuning problems. Model comparison is not trustworthy until the decision instant, target block, deadline, action unit, and split ownership are written as one small worked example and implemented identically offline and online.

The leanest promising route is to approve one explicit decision contract—or an explicitly different contract per chain where protocol facts force it—then choose one honest action unit, establish a tiny protocol-grounded feature baseline, and add complexity back only through named ablations. The existing bounded HPO program is an intentional research extension and remains a serious candidate; it cannot decide the semantic contract for the owner.

## Method and limits

This audit read the relevant production code, tests, module architecture and implementation notes, generated artifact manifests, available local corpus metadata, and the temporal sections of *SPICE: A Predictive Framework for Cost-Optimization in Multichain Environments* (`ICDCS_2026.pdf`, especially pp. 5 and 8). It was then amended after reading commit `e0b2e68e`, current `PROGRESS.md` and `ARCHIVE.md`, and the companion `temporal-training-evaluation-theory-audit.md` and `temporal-ml-lean-alternatives.md`. The paper and historical notes are evidence, not authority.

The review also checked primary documentation for EIP-1559, Ethereum slot timing, Polygon PoS fee behavior, Avalanche C-Chain configuration and ACP-176, scikit-learn preprocessing and metrics, PyTorch losses/data APIs, TorchMetrics, Polars rolling expressions, and time-series validation literature. Local numerical diagnostics were read-only. No corpus, artifact, production file, ADR, or issue was modified.

The snapshot counts below describe the artifacts and corpora currently present in this workspace. They are evidence about the current route, not universal chain properties. The candidate-count diagnostic used up to one million evenly spaced eligible training anchors per chain; its exact reconstruction used the current cutoff, fixed context length, timestamp search, and action-width rules. It is sufficiently large to expose a structural mismatch, but the final implementation should turn the same calculation into a reproducible analysis command before an architectural decision is approved. The finalized companion `temporal-chain-fee-protocol-audit.md` owns the Polygon/Avalanche fork citations and exact regime table.

## What the current pipeline means

The effective path is:

1. A corpus frame is sorted and duplicate block numbers are silently reduced to the first occurrence (`src/spice/modeling/dataset_builders/fixed_sequence_temporal.py:31-38`).
2. The feature contract builds a global feature table.
3. `observed_time_window` resolves one slot spacing and sets action width to `max(1, floor(max_delay / spacing)) + 1` (`src/spice/temporal/compilers/observed_time_window.py:170-190,313-319`).
4. Each sample's timestamp context starts at the first row at or after `anchor_timestamp - lookback_seconds`; its candidate outcome starts at the anchor itself and ends at the last timestamp within the delay (`observed_time_window.py:346-375`).
5. The dataset builder estimates one sequence length as `round(lookback / median positive timestamp delta)`, clips it to configured bounds, and replaces every timestamp-derived context with exactly that many rows (`fixed_sequence_temporal.py:41-57,121-155`).
6. Samples are divided into adjacent chronological fractions with no gap or label-horizon purge (`fixed_sequence_temporal.py:204-233`).
7. The scaler is fitted on unique feature rows covered by training contexts, rather than weighting a row once per overlapping window (`src/spice/temporal/input_normalization/scaling.py:51-63`).
8. The execution policy labels the minimum base-fee row among reachable candidate rows; `np.argmin` breaks equal-fee ties toward the earliest row (`src/spice/temporal/execution_policy/strict_deadline_miss.py:48-56`).

Under the recovered block-open interpretation, the anchor is meant to be a safe/virtual row for the current forming action block, even though the historical table row was materialized after that block finalized. It should therefore not be called “already observed” without first testing whether each value could have been constructed at the intended pre-inclusion instant. The factual pipeline description should also replace terms such as “time-window model” where they imply a guarantee the fixed builder does not maintain.

## 1. Reconcile the intentional block-open task with serving

### 1.1 Offset zero is intentional, not automatically leaked

The compiler assigns `candidate_start_rows = anchor_candidates` (`observed_time_window.py:352-364`). The strict policy uses that row as its baseline and assigns action offset `k` to row `anchor + k` (`strict_deadline_miss.py:76-100`). Read without its history, this resembles a model choosing a block it has already observed. Commit `e0b2e68e` establishes a different intended clock:

```text
parent/finalized facts through             h - 1
safe or virtual block-open row             h
offline class k target / realization      h + k
offline immediate baseline                h
```

The design permits `base_fee[h]` because Ethereum EIP-1559 derives that fee from parent state before block `h` executes. It shifts finalized `gas_used[h]`, `gas_limit[h]`, and `tx_count[h]` to `h-1` in `src/spice/features/sets/core_fee_dynamics/_block_facts.py:27-83`. The archived `same_block_closed` path, which exposed finalized facts from `h`, was the actual leakage route and was deliberately removed (`ARCHIVE.md:9-36`).

This makes current-row offset zero a coherent candidate: “submit for the current/forming block” rather than “choose an already closed block.” It remains a candidate, not a proved deployment contract. A historical finalized row is a valid offline stand-in only for values that can be constructed identically before inclusion, and the transaction must still be able to reach that block.

### 1.2 Offline and serving currently instantiate different clocks

Serving does not synthesize the documented block-open row. It fetches through `latest - confirmation_depth` (`src/spice/serving/live_blocks.py:51-65`), treats the final confirmed row as its anchor (`src/spice/serving/inference.py:144-198`), and maps selected offset `k` to:

```text
broadcast_after_block = confirmed_block + k
target_block          = confirmed_block + k + 1
baseline_block        = confirmed_block + 1
```

This is explicit at `src/spice/serving/inference.py:70-103`. For that post-confirmation information set, `+1` is rational: the confirmed block can no longer include a new transaction. It is not equivalent to offline block-open class `h+k`.

The confirmed defect is therefore cross-layer parity, not that one side is automatically wrong. Offline training/replay describe an intentional pre-inclusion/forming-block task; serving describes a post-confirmation/next-block task. The paper's “future block” and next-block baseline support the latter route, but paper fidelity does not invalidate the deliberate extension.

### 1.3 The complete block-open information set is not yet proved

Lagging finalized block facts is necessary but not sufficient. The default cadence/calendar group still computes `seconds_since_previous_block`, hour, and day of week from realized `timestamp[h]` (`src/spice/features/sets/core_fee_dynamics/_time.py:21-94`). At a forming-block decision instant, the final timestamp and exact interval into `h` are not ordinarily available from the current confirmed-head RPC source. Calendar values could be recomputed from decision wall-clock time, but that is a different offline fact and needs a declared equivalence/error rule. The optional `elapsed_seconds` feature has the same issue plus an arbitrary materialized-corpus origin.

Current-fee availability also needs a chain-and-fork proof rather than the blanket label “EIP-1559-like”:

- Ethereum's EIP-1559 parent recurrence supports deriving `base_fee[h]` before execution, subject to a concrete row-construction and broadcast-timing proof.
- Preliminary chain-audit evidence says the Polygon corpus crosses Lisovo activation at block `83,756,500`; after that transition, Bor's rule no longer supports a blanket exact parent-only child-fee claim. Corpus rows must be classified by protocol regime before the same safe-row argument is used.
- Avalanche ACP-176/Octane fee calculation needs additional parent fee state and the child timestamp; later-regime fields needed to reproduce it may not be present in the current canonical corpus. Reading the finalized child fee is not by itself an ex-ante availability proof.

The companion chain-protocol audit owns the final primary citations and exact regime table. Claims should be “proved for this chain/fork/field set,” “computable with added state,” “estimated,” or “post-close”—not a global safe/unsafe label.

### 1.4 Poisson arrivals are not associated with an actionable decision instant

`poisson_replay` samples arrival timestamps, maps each arrival backward to the most recent sample timestamp using `searchsorted(..., side="right") - 1`, then discards the actual arrival time (`src/spice/evaluation/poisson_replay.py:28-61,79-106`). Economic accounting receives repeated block-row positions, not request-time decisions.

That mapping is not automatically wrong, but it cannot validate either candidate clock:

- For a forming-block route, an arrival after block `h` opened may be too late to target `h`; assigning it to row `h` requires a defined pre-inclusion cutoff and forward eligibility rule.
- For a confirmed-head route, the arrival time determines the latest known head and the first eligible future block; discarding it prevents that proof.

After the owner chooses a clock, either carry arrivals through outcome realization or explicitly define which exposure interval belongs to each block-bound decision row. If normalized independent-request metrics are the only question, deterministic exposure weighting may replace Monte Carlo replay; the companion training/evaluation audit gives the derivation. Request-time Poisson wording and block-row weighting should not remain conflated.

### 1.5 Three owner-gated routes remain

1. **Preserve and reconcile block-open/current-forming semantics.** Keep `h` as offset zero. Build the same safe/virtual row offline and live from parent state, lagged finalized facts, and decision-time replacements for timestamp/cadence. Map arrivals to the next still-actionable block opening and prove that broadcast can reach `h` on every supported chain/regime.
2. **Adopt confirmed-head/next-block semantics.** Keep the current serving information set. Let row `h` be finalized context only; shift offline class zero and baseline to `h+1`; retain request time long enough to identify the first eligible future block. Preserve old block-open results as archival evidence rather than relabeling them.
3. **Use explicit per-chain/per-regime contracts.** Preserve block-open only where all fee state, timestamp facts, and actionability are proved; use next-block elsewhere. This may be the scientifically honest route if protocol rules differ, but it adds artifact, evaluator, documentation, and comparison concepts. Choose it only if one shared route would be false.

All routes require a three-block fixture per chain/regime containing decision time, confirmed/forming/virtual row status, every input's `available_at`, action `k`, broadcast time, first eligible inclusion block, deadline, fallback, baseline, and realized fee. The fixture must agree across feature construction, labels, offline realization, Poisson/exposure association, and serving. No route is approved by this audit.

### 1.6 “Wait seconds” and “choose block offset” are not interchangeable

The compiler first forms a physical candidate window by timestamp, then caps reachable rows at a fixed block count (`src/spice/temporal/problem_store.py:154-179`). The count comes from one spacing estimate rather than the actual future intervals. This creates two behaviors:

- If fewer blocks arrive than the width predicts, later class indices overflow past the deadline.
- If more blocks arrive, valid in-deadline rows after the width are ignored by the target and oracle optimum.

The behavior is deliberate in `strict_deadline_miss`, but its frequency means it is not merely defensive edge handling. On the current 36-second configurations, the diagnostic found:

| Chain | Action width | Mean physical candidates | Shorter than width | Longer than width |
|---|---:|---:|---:|---:|
| Ethereum | 4 | 3.979 | 2.04% | 0% |
| Polygon | 19 | 18.114 | 72.80% | 0% |
| Avalanche | 23 | 24.254 | 37.13% | 54.16% |

These numbers also make class meaning chain- and regime-dependent. “Class 18” is a row offset, not a stable physical wait. `recommended_wait_seconds = round(offset * slot_spacing)` in serving (`inference.py:85-86`) reports an estimate as if it were the selected physical delay.

Two coherent candidate definitions exist:

1. **Block-offset problem.** Pick one of `K` consecutive eligible action blocks—starting at the forming block under route 1 or after the confirmed head under route 2. Configure `K` directly. Express the service guarantee and experiments in blocks. Timestamp duration is descriptive, not the label boundary.
2. **Time-bin problem.** Pick a wait/deadline bin in seconds. Define how a bin maps to a broadcast instant and its first eligible realized inclusion block. Labels and masks are time-based; variable block counts are expected.

For leanness, the block-offset problem is the stronger starting candidate because the model already emits categorical offsets and serving acts in block order. It removes nominal-spacing conversion, overflow classes, and the hybrid window. It does change the product claim from an exact seconds deadline, so it needs explicit owner/professor approval. If an exact seconds tolerance is a hard domain constraint, keep time semantics and redesign the action representation honestly rather than retaining the hybrid.

### 1.7 Chain “nominal time” is not one unambiguous fact

The current Avalanche configuration uses `1.6` seconds. Avalanche's current C-Chain configuration documentation lists `targetBlockRate = 1`, and ACP-176 describes fee dynamics using gas consumption over a rolling ten-second window. The paper also says one second. An empirical median may still be useful, but then it must be named and fitted as an empirical statistic rather than called the protocol nominal time.

The owner needs to define whether each configured interval means protocol target, recent empirical median, long-run empirical mean, or a presentation estimate. They are not interchangeable. Relevant primary sources are the [Avalanche EVM configuration reference](https://build.avax.network/docs/avalanche-l1s/evm-configuration/customize-avalanche-l1), [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates), [Ethereum block documentation](https://ethereum.org/developers/docs/blocks/), and [Polygon PoS EIP-1559 documentation](https://docs.polygon.technology/pos/concepts/transactions/eip-1559).

## 2. Split labels, not only anchors

### 2.1 The external cutoff is handled correctly

When `training_cutoff_timestamp` exists, the builder retains only samples whose last outcome timestamp is before the cutoff (`fixed_sequence_temporal.py:102-118`). That is the correct form of guard: sample ownership is based on every row used to create its target, not just its anchor.

### 2.2 Internal boundaries lack the same guard

Train, validation, and test are adjacent slices of anchor indices. A final training anchor can therefore use candidate outcomes whose timestamps are at or after the first validation anchor; the same occurs at validation/test. Exact reconstruction of current artifacts found crossing samples:

| Chain | Train labels crossing into validation | Validation labels crossing into test |
|---|---:|---:|
| Ethereum | 3 | 3 |
| Polygon | 18 | 18 |
| Avalanche | 28 | 15 |

This is target leakage across roles. It is small in row count for Ethereum but conceptually direct, and it grows with higher block frequency and the effective horizon.

**Lean correction:** after choosing boundaries, purge from the earlier role every sample whose complete candidate/outcome dependency reaches the first anchor of the next role. A generic configurable `gap` is less clear than checking the actual outcome end, although scikit-learn's [`TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) demonstrates the standard idea of preserving order and leaving a gap. Do not purge overlapping *past* contexts merely because adjacent samples share history: that overlap is causal and normal. Purge the forward label horizon.

The paper's phrase “non-overlapping intervals” should not be interpreted as statistical independence. With stride-one sliding windows, neighboring examples share almost all input rows. The number of samples is therefore not the number of independent observations, and IID confidence calculations at anchor level would be misleading.

### 2.3 Validation and final evaluation need distinct roles

The present 80/10/10 split is chronological, which is preferable to random shuffling, but one latest contiguous test period can reflect one fee regime. Current artifacts span approximately:

| Chain | Train | Validation | Test |
|---|---|---|---|
| Ethereum | May 7–Oct 25, 2025 | Oct 25–Nov 16 | Nov 16–Dec 7 |
| Polygon | Jul 1–Nov 12, 2025 | Nov 12–Nov 27 | Nov 27–Dec 13 |
| Avalanche | Apr 8–Oct 30, 2025 | Oct 30–Nov 25 | Nov 25–Dec 18 |

The paper instead reports roughly 400,000 samples immediately preceding each evaluation day (p. 8). Neither choice is automatically correct. The current multi-month route changes the estimand and may average over protocol or demand regimes; the paper's shorter route may be less representative.

A lean thesis workflow has two defensible candidates:

- Keep a purged chronological train/validation split and treat the existing independent post-cutoff replay windows as the tests. This could delete the internal-test role and its machinery.
- Keep a purged 80/10/10 development split, freeze all choices after validation, then run several fixed-origin post-cutoff windows once as final evaluation.

Repeatedly changing features or architecture after viewing “external evaluation” makes those windows validation data in practice. Name the role honestly and reserve unseen final windows if final claims are required. Multiple forecast origins are a better robustness check than one arbitrary day; see Tashman's review of [out-of-sample forecast evaluation](https://doi.org/10.1016/S0169-2070(00)00065-0) and Bergmeir, Hyndman, and Koo on [cross-validation for dependent data](https://robjhyndman.com/publications/cv-time-series/).

## 3. Make context semantics honest

The compiler initially computes a true time lookback through timestamp search. The builder then discards those starts and derives one global row count from the median positive delta. This has three consequences:

- An `N`-row inclusive sequence spans `N - 1` intervals, so `round(lookback / dt)` is off by one even under perfectly regular timing.
- Variable intervals make the actual context duration change from sample to sample.
- Configured min/max bounds can dominate the requested duration.

Current artifact context lengths are 64 rows for Ethereum, 300 for Polygon, and 600 for Avalanche. Representative spans are roughly 756 seconds for Ethereum, 609 seconds for Polygon, and 811 seconds on average for Avalanche—not uniformly 600 seconds. The exact range varies with local cadence.

This does not mean fixed row sequences are bad. They are much simpler for an LSTM and make batching easy. It means the project must choose what it promises:

- **Recommended candidate:** after the decision clock is chosen, define context as exactly `K` causally available block rows and configure `K` directly per chain or experiment. Under a forming-block route, the final row may be virtual; under a confirmed-head route, it is finalized. Rename/remove `lookback_seconds` in this path.
- **Alternative:** preserve a true seconds lookback and support variable lengths/masks. This is semantically faithful but adds batching complexity.

For the project's stated readability priority, fixed blocks are likely the better route if the thesis does not require an exact 600-second receptive field. The paper's formula `600 / nominal block time` is an approximation, not proof that one globally median-fitted length is theoretically preferable.

`recent_median` has an additional leakage problem: `_resolve_slot_spacing_seconds` runs against the complete feature table before splitting, and `_recent_median_positive_timestamp_delta_seconds` reads every timestamp (`observed_time_window.py:170-190,322-329`). Any fitted statistic should use training data only, as described in scikit-learn's [preprocessing leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html). The smallest correction is to remove this mode if direct block counts are adopted. If retained, fit it on the training prefix, persist it, and reuse it online.

## 4. Strengthen the corpus boundary, then simplify feature math

### 4.1 Invalid values are currently repaired into plausible features

The corpus layer checks schema, nulls, and block continuity, and the feature layer checks non-finite active outputs after warmup. It does not consistently enforce the physical domain before transforms. Feature helpers then clip negative counts to zero before `log1p` and clip non-positive fee-like inputs to one before `log` (`src/spice/features/sets/core_fee_dynamics/_transforms.py:17-22`). A corrupt negative value can therefore become a valid-looking finite number.

The builder also silently sorts and removes duplicate block numbers even though the corpus contract already rejects duplicates. Silent repair in a later layer makes data provenance harder to explain.

**Candidate corpus invariants:** validate once at the modeling-corpus seam and fail with row/block context:

- block numbers are unique, sorted, and contiguous for the selected range;
- timestamps are nondecreasing; do not demand strictly increasing because legitimate same-second blocks occur;
- `base_fee_per_gas > 0` and `gas_limit > 0`;
- `0 <= gas_used <= gas_limit`;
- transaction count is nonnegative;
- when priority-fee percentiles are active, `0 <= p10 <= p50 <= p90`, with any stored spread consistent with its definition;
- every selected raw source is finite.

Then delete clipping that masks violations and let formulas express their theory directly. Remove `_prepare_blocks` deduplication and sort repair after the upstream contract guarantees canonical order. This creates a deeper module: the feature builder receives trustworthy block facts and need not defend itself repeatedly.

Warmup rows currently survive as placeholders even though they can never become model input. A clean-break implementation can crop the unavailable prefix after features are built, rebase indices once, and remove placeholder handling if that measurably reduces complexity. It is optional; explicit NaNs during feature construction are also pedagogically useful when the boundary remains small.

### 4.2 Timestamp assumptions should be stated by transform

Block-index rolling windows are causal, but their physical durations differ by chain and by local cadence. “Rolling 50” means 50 blocks, not a stable number of seconds. Calendar features such as hour/day use timestamp time; elapsed and deadline logic use seconds; most lags use blocks. The mix is valid only when documented.

If time-based feature windows are scientifically important, Polars supports dynamic temporal rolling through [`Expr.rolling`](https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.rolling.html). Adopting it would be a semantic change and could make the code harder to teach, so it should not be done merely for API modernity. Fixed block windows are the lean default; name their unit.

## 5. Start with protocol facts, then earn engineered features

The default family currently emits 45 features, with optional groups reaching 77 priority-fee and 46 elapsed-time outputs. It contains raw or transformed block facts, multiple explicit lags, and overlapping rolling windows. The sequence model already receives a history of rows, so many engineered lag/rolling columns repeat information the LSTM can in principle derive.

Ethereum's [EIP-1559 specification](https://eips.ethereum.org/EIPS/eip-1559) gives a protocol-grounded baseline: the child base fee is mechanically derived from parent state. That supports current log base fee plus the parent utilization facts needed by the recurrence. It does not generalize unchanged. Polygon's rule is fork-dependent, and the current corpus crosses Lisovo. Avalanche ACP-176 uses additional fee state and a rolling ten-second gas-consumption mechanism. The minimal feature core may therefore need an explicitly different formula per chain/regime, even if every model receives the same small conceptual categories such as fee level and protocol pressure.

The current feature family raises specific concerns:

- `prev_gas_used`, `prev_gas_limit`, and `prev_gas_utilization` are algebraically redundant when all are valid.
- Six explicit lags of fee change/utilization and overlapping rolling windows duplicate the temporal sequence representation.
- Base-fee rolling windows 10/25/50/100/200 and gas windows 10/50/200 have no documented hypothesis explaining each receptive field.
- Standard-deviation features use inconsistent `ddof`: some use the helper default `0`, while others explicitly use `1`. For a fully observed descriptive window rather than a sample estimating an unseen population, `ddof=0` is the clearer default. The choice should be approved and uniform. Polars documents the parameter in [`rolling_std`](https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.rolling_std.html).
- `base_fee_trend` maps a zero delta to `+1`, so its real meaning is “nondecreasing versus decreasing,” not neutral/up/down trend (`_transforms.py:32-36`). Rename it or remove it.
- The paper's feature table is not the current feature set: it names hour/day, elapsed time, trend, and selected 10/50/200 rolling fee/gas statistics. Current additions and the removal of elapsed time from the baseline are refinements that need evidence, not automatic preservation or automatic rollback.

### Candidate ablation ladder

Run the smallest experiment that can answer whether each layer earns its code:

1. **Protocol core:** log current base fee and previous utilization (adjust exact facts for each chain's mechanism).
2. **Simple observed facts:** add cadence/calendar/activity facts only where a hypothesis exists.
3. **Engineered history:** add the present lag and rolling family.
4. **Optional priority-fee family:** only if the deployed economic objective includes priority fees and corpus coverage is trustworthy.

Compare validation economic regret/savings first, then accuracy and calibration/diagnostics. Record parameter count, feature count, preprocessing time, training time, and source lines or conceptual surface. Prefer the smaller rung when benefit is absent, unstable across chains/windows, or too small to matter to the thesis conclusion.

This experiment may show that engineered statistics improve a small LSTM. It may also show that a two-to-six-feature input is sufficient. The audit does not assume either outcome.

## 6. Normalization is mostly sound and can become smaller

Fitting `StandardScaler` only on rows covered by training contexts is correct. Counting each physical row once, rather than once for every overlapping sequence containing it, gives the scaler a clear time-row estimand. Saving means/scales and applying them unchanged to validation, test, and serving prevents leakage. [`StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) uses training mean and variance with `ddof=0`; that convention is appropriate here.

Two improvements remain:

- `ScalerStats` does not validate finite values, equal mean/scale lengths, positive/nonnegative scales, or agreement with the model feature width. A malformed one-element scaler can broadcast over every column. Validate the artifact at load/compile time.
- This is the only scikit-learn use in `src`. A NumPy mean/std implementation would be a few transparent lines and could remove a direct runtime dependency. Conversely, keeping the well-known scaler avoids home-grown edge semantics. Decide using total dependency cost; do not add a scikit-learn `Pipeline`, because the project already needs explicit temporal compilation and artifact serialization and a pipeline would add indirection rather than delete it.

Robust scaling is not a free best-practice upgrade. Base-fee distributions can be heavy-tailed, but inputs are already logged and the current scaler is easy to teach. Adopt another scaler only if diagnostics show StandardScaler causes optimization instability or materially worse held-out economics.

## 7. Targets and loss choices are assumptions, not defaults

### 7.1 Earliest minimum is a lexicographic utility

`np.argmin` selects the earliest row when several candidate blocks have the same minimum base fee. In a one-million-anchor training snapshot, exact minimum ties occurred for approximately 0% of Ethereum, 39.03% of Polygon, and 0.003% of Avalanche samples. Polygon's tie rate is large enough to affect interpretation.

Choosing the earliest equally cheap block is rational if the utility is explicitly:

1. minimize base fee;
2. among equal fees, minimize delay.

But exact offset accuracy and F1 then penalize a prediction of another economically equal minimum as fully wrong. Keep the earliest label if that lexicographic policy is desired, while making economic regret/savings and perhaps “selected a minimum-fee tie” the primary evaluation. A tie-aware soft classification target is possible—PyTorch cross entropy accepts probability targets—but it complicates the explanation. For this thesis, hard earliest labels plus economic metrics are probably the leaner route.

### 7.2 Inverse-frequency class weights change the estimand

Full inverse-frequency weights make every offset class contribute approximately equally to the classification loss. They do not merely “fix imbalance”; they optimize a different objective from average per-transaction loss. The current training-label snapshot's largest-class shares were about 31.00% for Ethereum, 24.35% for Polygon, and 8.02% for Avalanche, so severe collapse should be demonstrated rather than assumed.

PyTorch documents the exact weighted mean denominator in [`CrossEntropyLoss`](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html), and scikit-learn documents the conventional balanced heuristic in [`compute_class_weight`](https://scikit-learn.org/stable/modules/generated/sklearn.utils.class_weight.compute_class_weight.html). Neither makes weighting mandatory.

Run an unweighted-cross-entropy baseline. Keep weighting only if it improves held-out economic outcomes or a separately approved fairness-across-delays objective. If the practical objective is fee regret, direct class frequency is not itself a harm.

### 7.3 The auxiliary regression head has to earn its existence

The minimum-fee regression output is used during training and diagnostics but not by serving's action decision. Multi-task learning can regularize a shared representation, but it can also produce negative transfer. The classic rationale is Caruana's [multitask learning paper](https://doi.org/10.1023/A:1007379606734); it is a hypothesis for this dataset, not evidence that this head helps.

Compare classification-only against the present multi-task model under matched seeds and selection criteria. If the auxiliary head does not reliably improve deployed economic metrics across chains/windows, remove the head, fee normalization state, regression loss/metrics, and loss-weight configuration. Also avoid selecting checkpoints by a total loss that includes an undeployed task unless validation proves that total loss ranks deployed behavior well.

## 8. Correct the macro-F1 claim, then question whether F1 is needed

The earlier conclusion that stock TorchMetrics matches SPICE's target-supported macro averaging was incorrect. Current SPICE explicitly skips every class with `target_count == 0` (`src/spice/prediction/families/min_block_fee_multitask/metrics.py:76-94`). Standard scikit-learn macro F1 uses the union of labels present in targets and predictions by default, and TorchMetrics 1.9.0 matches that behavior for an active prediction-only class.

A local counterexample makes the difference concrete:

```text
targets:     [0, 0]
predictions: [0, 1]

SPICE macro F1:       2/3
scikit-learn 1.8.0:   1/3
TorchMetrics 1.9.0:   1/3
```

Class `1` has no target but does have an incorrect prediction. SPICE omits it; the stock metrics include its zero F1. This difference arises only for prediction-only classes, which is why ordinary examples can miss it. The relevant public contracts are scikit-learn's [`f1_score`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html) and TorchMetrics' [`MulticlassF1Score`](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html).

If macro F1 remains, use the conventional union-active behavior and state zero-division policy. TorchMetrics could also delete manual accumulation boilerplate because it handles state accumulation and distributed synchronization; see its [overview](https://lightning.ai/docs/torchmetrics/stable/). Before adding that dependency directly, note that it is already transitive through Lightning and confirm it remains in the chosen lean training stack.

More fundamentally, offset classes are ordered actions with unequal economic consequences. A one-block error and an overflow error are both simply wrong to accuracy/F1. Primary reporting should be economic regret/savings against immediate execution and the reachable oracle, deadline-miss rate, and exact offset accuracy. A confusion matrix can explain behavior. Macro F1 may be deleted if it does not answer a thesis question.

## 9. HPO is intentional; preprocessing must make its comparisons fair

Hyperparameter optimization is a purposeful extension beyond the paper, not accidental machinery. Current `PROGRESS.md:135-147,213-226` defines one bounded 32-trial calibration per chain/model cell, forbids retuning every structural ablation, and requires explicit presets before selected parameters are transplanted across study identities. That policy can reduce undocumented hand tuning and preserve a reproducible trial record. Optuna therefore remains a serious retain candidate.

Preprocessing still constrains whether its comparisons are meaningful. Tuning lookback or sequence geometry can change which anchors survive and therefore move validation boundaries; candidate configurations should share predeclared validation origins or declare an explicit common eligible subset. Split purging, decision semantics, metric reduction, seed timing, validation-only trials, and real epoch pruning must be repaired before HPO results support model selection; the companion training/evaluation audit owns those implementation findings.

The clean order is fixed baseline and feature/target ablations first, bounded HPO after the task and feature surface stabilize, then multi-seed finalist confirmation. Do not delete HPO merely because a minimal control does not need it, and do not use HPO to choose among unresolved definitions of the action.

## 10. Simplify the feature and sequence interfaces only after semantics settle

The feature subsystem has a generic source/spec/catalog/registry architecture around one main static feature family. The temporal path likewise has registries for one compiler, one execution policy, one fixed builder, and one scaler. These seams may have been useful during exploration, but they impose many concepts on a new reader without current variation paying for them.

Polars already provides native `shift`, rolling mean/std/min, and expression composition through its [expression API](https://docs.pola.rs/api/python/stable/reference/expressions/index.html). If the approved feature family becomes small and static, one explicit `build_feature_frame(blocks)` function plus a declared `FEATURE_COLUMNS` tuple can replace much of the feature catalog. Keep a contract only where it hides genuine volatility: validating canonical inputs and returning ordered finite model features with known warmup.

Fixed contexts also imply every training/inference input has the same length. Yet the batching path still pads, builds masks, loops per sample, and groups by context signature. A clean fixed-block design can potentially use vectorized row-index construction, NumPy's [`sliding_window_view`](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html), or PyTorch [`Tensor.unfold`](https://docs.pytorch.org/docs/stable/generated/torch.Tensor.unfold.html), with no padding mask and the final position used directly. These views can have memory/contiguity trade-offs, so prototype and benchmark before choosing. Continue using PyTorch's standard [`Dataset`/`DataLoader`](https://docs.pytorch.org/docs/stable/data.html); adding another data framework is unlikely to make this path smaller.

Do not consolidate before the decision/action-unit redesign. Prematurely flattening unstable semantics would only make the next correction harder. Once one route is approved, delete unused strategy IDs and one-option metadata rather than preserving clean-break compatibility shims.

## 11. Paper alignment: explain differences, do not restore them blindly

The paper is foundational in goal and terminology, but the implementation has materially evolved:

- The paper describes choosing a future block and an immediate next-block baseline; offline code intentionally defines its anchor as the current/forming block under the recovered block-open extension. This is a deliberate divergence whose live information set and actionability remain unproved, not an accidental inclusion of an observed closed block.
- The paper derives fixed sequence length from a 600-second history and nominal block time; code derives one length from the raw training prefix's empirical median and clips it.
- The paper reports roughly 400,000 pre-evaluation samples; current artifacts use 1.5M to 14.1M selected samples across months.
- The paper lists a narrower/different feature family, including elapsed time; the default code has added lags/windows and excludes elapsed time.
- Both paper and code use inverse-frequency class weighting and multi-task loss, but neither fact proves those choices improve the deployed temporal action.
- The paper assumes a next-block base fee can stand for transaction cost and treats priority fee as negligible. The code also targets base fee. Economic conclusions must scope that assumption, especially if optional priority-fee features exist but the target still ignores priority fees.
- Polygon and Avalanche protocol timing/fee mechanics are fork- and state-dependent: the Polygon corpus crosses Lisovo, while Avalanche's current fee rule needs state/timestamp facts beyond a simple Ethereum-style parent recurrence. The companion chain audit classifies the exact corpus ranges; one causal claim must not be applied to all rows.

Each difference should be classified as bug, deliberate refinement with evidence, changed protocol/environment, or unresolved experiment. “Matches the paper” is not an acceptance criterion. The strongest fundamental discrepancy is that offline block-open training/replay, Poisson arrival association, and confirmed-head serving do not yet implement one decision record; neither the block-open nor next-block definition is automatically selected by that mismatch.

## 12. Documentation modernization plan

The architecture and implementation files should be rewritten after—not before—the semantic decisions. Current documentation often describes mechanisms but does not teach why the problem is defined this way, what unit each value uses, or what alternatives were rejected.

Every ML-core module note should use a common beginner-facing structure:

1. **Question answered:** one sentence in domain language.
2. **Worked example:** a tiny timeline with block numbers, timestamps, observed rows, candidate rows, deadline, target, and split ownership.
3. **Theory:** why this construction is causal and what statistical objective it estimates.
4. **Contract:** inputs, outputs, units, shapes, inclusive/exclusive boundaries, and invariants.
5. **Algorithm:** compact pseudocode before implementation detail.
6. **Assumptions and failure modes:** irregular cadence, ties, missing rows, regime change, overflow, and leakage.
7. **Evidence:** ablations or protocol source supporting non-obvious complexity.
8. **Code map:** only the few files a reader must open next.

Specific corrections:

- **Corpus docs:** add physical-domain constraints, ordering/deduplication ownership, timestamp policy, provenance, and why invalid rows fail instead of being clipped.
- **Feature docs:** show each feature formula and unit, causal receptive field, warmup, chain/fork protocol rationale, `available_at` instant, redundancy/ablation status, and `ddof` convention. Distinguish virtual decision-time timestamp/cadence from finalized row fields, and separate block-count windows from seconds windows.
- **Temporal compiler docs:** teach the intentional block-open history and the exact forming/confirmed/virtual-row timeline; explain inclusivity, post-window row, overflow, fitted spacing, and the alternative next-block route. Until resolved, flag cross-layer parity, Poisson association, per-chain availability, and full-table `recent_median` leakage without calling offset zero automatically wrong.
- **Dataset-builder docs:** state that current fixed row contexts override timestamp context and quantify what min/max clipping means. After a clean break, document either blocks or seconds, not both as though equivalent.
- **Normalization docs:** retain the training-only explanation and add why each physical row is counted once, how constant columns are treated, artifact validation, and a numeric two-feature example.
- **Prediction-family docs:** explain earliest-tie utility, class-weight estimand, auxiliary-task hypothesis, checkpoint criterion, ordered-action limitations, and why economic metrics dominate F1.
- **Training docs:** teach gradient/loss aggregation, early stopping/checkpoint ownership, determinism limits, and the difference between optimization loss and thesis evaluation objective.
- **Evaluation docs:** define every baseline/oracle and denominator, explain fixed-origin windows and repeated experimentation, and show how deadline misses affect cost.
- **Serving docs:** add the missing offline-to-online parity table. Every model offset must map to one decision instant, confirmed/forming/virtual row, broadcast point, first eligible target block, estimated wait, and evaluator outcome in exactly one way.

Avoid encyclopedic files. Teach the theory closest to the module that owns it, link once to a shared glossary for recurring terms, and remove statements that simply narrate class names. Expanded documentation should reduce interpretation work, not mirror every implementation branch.

## Candidate clean-break route and approval gates

The following ordering minimizes wasted experiments:

1. **Approve the temporal contract.** Choose preserve-and-reconcile block-open, confirmed-head/next-block, or an explicit per-chain/per-regime route. Decide the decision instant, virtual versus finalized row, first eligible action/inclusion block, right-boundary inclusivity, block versus seconds action unit, baseline, deadline-miss behavior, and tie utility. Add a per-chain offline/replay/serving parity fixture.
2. **Repair evaluation ownership.** Purge label horizons at all role boundaries. Decide whether internal test remains or external replay is the only test. Freeze final windows.
3. **Make context use the same honest unit.** Prefer configured fixed block count for the fixed LSTM; remove global median/min/max conversion and unused variable-length machinery if approved.
4. **Harden the corpus seam.** Add physical invariants; remove downstream sort/dedup and clipping repairs.
5. **Establish the tiny baseline.** Per-chain protocol-core features, unweighted classification-only loss, standard scaling, and economic validation metrics. This is the understandable reference model.
6. **Run named ablations.** Engineered features, class weights, auxiliary regression, optional priority features, and alternative context sizes each enter separately. Retain only stable economic gains worth their conceptual cost.
7. **Run the intentional bounded HPO phase.** Only after the task and canonical feature surface stabilize; use common validation origins, validation-only trials, corrected reduction/seed/pruning, and multi-seed finalist confirmation.
8. **Flatten one-option architecture.** Consolidate registries/spec layers, vectorize fixed sequences, delete padding masks and unused metadata where the approved design makes them impossible.
9. **Rewrite architecture and implementation notes.** Use the approved contract, experiment evidence, formulas, examples, and failure modes. Mark deviations from the paper explicitly.

Minimum evidence for approval should include at least three seeds for stochastic comparisons, per-chain and per-evaluation-window results rather than only pooled averages, immediate and reachable-oracle economic baselines, deadline-miss rate, exact/tie-aware decision diagnostics, and total code/concept reduction. A candidate wins when its performance is not materially worse for the thesis claim and its behavior is substantially easier to explain—not merely when one mean score is slightly higher.

## Decisions required from the owner

1. Does the project preserve and operationally reconcile the intentional block-open route, adopt confirmed-head/next-block semantics, or allow an explicit chain/regime-specific choice?
2. For every block-open chain/regime, can `base_fee[h]`, timestamp/cadence, and every selected feature be constructed before inclusion, and can a request still reach `h`?
3. Is the product promise fundamentally “choose one of the next `K` blocks” or “may wait at most `M` wall-clock seconds,” and does the deadline constrain broadcast or achieved inclusion?
4. Which request-arrival interval owns each decision row, and must actual arrival timestamps survive into realization?
5. Is earliest among equal minimum fees the intended secondary objective?
6. May external replay windows become the sole test surface, eliminating the internal test split?
7. Is base fee alone the intended economic target, with priority fee explicitly out of scope, or must total inclusion fee be modeled?
8. What amount of held-out economic degradation counts as “no material cost” when choosing the leaner model?
9. Should protocol-specific feature cores and decision contracts be allowed, or must one identical schema/task serve all chains?
10. Does bounded Optuna HPO remain after the task stabilizes, and what common validation-origin, sampler, pruning, seed, and preset-materialization policy is approved?

Until questions 1–4 are answered, no ADR should be superseded and no broad preprocessing rewrite should be approved. The immediate output should be a route-neutral temporal decision record and per-chain parity fixtures, not an automatic `+1` target shift or framework migration.

## Primary references

- Local recovered intent: commit `e0b2e68e` (`fix(features): enforce safe current-row fee dynamics`), `ARCHIVE.md:9-36`, `PROGRESS.md:135-147,213-255`, and `src/spice/features/ARCHITECTURE.md:28-51`
- Companion cross-checks: `docs/research/issue-1/temporal-training-evaluation-theory-audit.md`, `docs/research/issue-1/temporal-ml-lean-alternatives.md`, and `docs/research/issue-1/temporal-paper-alignment-audit.md`
- [EIP-1559 specification](https://eips.ethereum.org/EIPS/eip-1559)
- [Ethereum blocks and 12-second slots](https://ethereum.org/developers/docs/blocks/)
- [Polygon PoS EIP-1559](https://docs.polygon.technology/pos/concepts/transactions/eip-1559)
- [Avalanche EVM configuration and C-Chain target block rate](https://build.avax.network/docs/avalanche-l1s/evm-configuration/customize-avalanche-l1)
- [Avalanche ACP-176 fee and gas-limit update](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates)
- [scikit-learn: common preprocessing pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)
- [scikit-learn: `StandardScaler`](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
- [scikit-learn: `TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [PyTorch: cross-entropy loss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html)
- [TorchMetrics: multiclass F1](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html)
- [Polars expression API](https://docs.pola.rs/api/python/stable/reference/expressions/index.html)
- [NumPy: `sliding_window_view`](https://numpy.org/doc/stable/reference/generated/numpy.lib.stride_tricks.sliding_window_view.html)
- Tashman, [*Out-of-sample tests of forecasting accuracy*](https://doi.org/10.1016/S0169-2070(00)00065-0)
- Bergmeir, Hyndman, and Koo, [*A note on the validity of cross-validation for evaluating autoregressive time series prediction*](https://robjhyndman.com/publications/cv-time-series/)
- Caruana, [*Multitask Learning*](https://doi.org/10.1023/A:1007379606734)
