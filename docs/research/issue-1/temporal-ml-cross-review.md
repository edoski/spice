# Temporal ML cross-review and correction ledger

**Status:** independent red-team report. It approves no route, ADR, metric, framework, issue, or code change. The current-row target and bounded HPO remain intentional project extensions. They are not to be removed, redefined, or described as mistakes without owner approval.

**Bottom line:** the audit reports agree on the important facts, and their strongest claims survived independent source and data checks. The present results still do not establish one causally identical task across preprocessing, training, replay, and serving. Several implementation defects also affect selection or reported economics. These must be fixed before old benchmark rankings can approve a clean-break design. The paper is the research foundation, not a correctness oracle; the old ADRs are evidence of intent, not authority.

The root decision is the decision clock: what is known at time `tau`, what class zero physically means, and which block a transaction submitted at `tau` can still target. Framework, tensor, metric, and documentation cleanup should follow that decision rather than encode the current ambiguity more neatly.

## Method and evidence boundary

This review independently read the 11-page paper at `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`; the current preprocessing, target, loss, metric, training, tuning, replay, accounting, serving, and chain code; relevant tests; commit `e0b2e68e`; `PROGRESS.md`; `ARCHIVE.md`; current artifact metadata; canonical Parquet corpora; and `benchmarks/results.sqlite`. It then cross-checked the six temporal audit reports and the clean-break Wayfinder graph.

Read-only probes reproduced split overlap, context spans, candidate geometry, ties, metric formulas, serving block arithmetic, Polygon fee recurrence failures, and framework behavior. Official specifications, client source, and framework documentation were used for protocol and API claims. No production file, issue, ADR, artifact, corpus, or database was changed.

Local numerical checks are diagnostic evidence, not publication-ready experiments. If used in the thesis, they need a checked-in reproducible analysis command, frozen input identities, and a declared estimator.

## Cross-report reconciliation

The final reports are substantively consistent after these resolutions:

- **Intent classification is fixed:** current-row offset zero and bounded HPO are intentional extensions. Findings can challenge their correctness or implementation, but cannot reclassify them as accidental drift. Paper divergence alone is not a defect.
- **Macro F1 false alarm is closed:** stock TorchMetrics/scikit-learn behavior is union-active; current SPICE is target-supported only. The audits correctly retain this as a custom-metric discrepancy.
- **Deterministic Poisson claims need scope:** fixed-window expected request means have exact exposure weights. Production also randomizes the window start, so equivalent deterministic evaluation needs the inclusion kernel. Overlapping historical windows do not invalidate conditional Monte Carlo independence; the resulting error bars still describe integration noise, not generalization.
- **Polygon cadence attribution is corrected:** Lisovo changes fee configurability. The observed material 1-second cadence share begins after Giugliano, not immediately after Lisovo. A broad statement that the post-Lisovo suffix “includes” more 1-second rows is technically true but causally misleading.
- **Serving mismatch is stronger than an abstract `+1`:** earlier reports describe training/serving offset divergence. The chain audit's exact default-depth arithmetic establishes the operational defect: two leading targets are already closed.
- **Context-span numbers use different summaries:** approximately 756/609/811 seconds in companion prose correspond to representative median/mean values. The table below reports both mean and median. This is not a data disagreement.
- **Ethereum corpus ids have different scopes:** the chain audit uses the longer `cor_7bea...` for fork coverage; current-artifact reproductions use `cor_2edb...`. Conclusions should name which corpus they use.
- **Economic-objective language remains a candidate:** no report supplies approval to use noisy replay economics for every checkpoint. The frozen A/B evidence and owner decision must separate early stopping, HPO ranking, and final model comparison.

## Correction ledger

### Intent and paper alignment

| Claim | Verdict | Correction or consequence |
|---|---|---|
| Offset zero/current row is an accidental off-by-one. | **False.** | Commit `e0b2e68e`, [`ARCHIVE.md`](../../../ARCHIVE.md), and [`PROGRESS.md`](../../../PROGRESS.md) record a deliberate block-open design: current base fee may be parent-derived while finalized gas/transaction facts are lagged. Preserve this as a first-class candidate. |
| The paper proves that offset zero must be the next block. | **False.** | The paper describes a future minimum and next-block baseline, but does not fully specify observation, submission, builder cut-off, or inclusion instants. Paper-next-block is a useful comparator, not an automatic replacement. |
| HPO is unexplained machinery and can be deleted for leanness. | **False.** | The bounded 32-trial policy is an intentional thesis extension intended to reduce undocumented hand tuning. Its implementation needs repair; its scientific value remains owner-gated. |
| The paper validates the present deep architectures. | **Unsupported.** | It compares LSTM, Transformer, and their hybrid, but no naive, protocol, linear, or shallow baseline. One Avalanche Transformer 36-second result is negative. Complexity has not earned itself yet. |
| Current SPICE is a direct reproduction of the paper. | **False.** | The paper reports separate 12/24/36-second models, one selected test day, about 400,000 non-overlapping intervals, weighted CE plus SmoothL1, and only deep candidates. Current SPICE uses overlapping per-block samples, a variable timestamp-bounded candidate window, HPO, extra features/metrics, and serving. These can be valid refinements but must be labeled as extensions. |
| Every declarative statement in an ADR or existing architecture note is a settled fact. | **False.** | Historical documents recover intent. Protocol, statistical, framework, and deployment claims require current proof. ADR disposition remains an explicit final owner gate. |

### Preprocessing and target construction

| Claim | Verdict | Correction or consequence |
|---|---|---|
| Chronological splitting alone prevents leakage. | **False.** | Samples immediately before each boundary can have label/outcome rows inside the next role. Purge the earlier role by the actual candidate/outcome reach. Shared past context is causal and need not be purged. |
| Normalization leaks validation/test data. | **False for the current scaler path.** | `fixed_sequence_temporal.py:283-287` fits the scaler on train-covered rows and reuses it. Preserve this clear fit/transform rule. |
| `recent_median` slot spacing is train-only. | **False.** | `observed_time_window.py:170-200,322-329` resolves it from the complete feature table before splitting. Remove the mode or fit it on the training prefix and persist it. |
| A configured action width means every sample has that many within-deadline blocks. | **False.** | Timestamp-bounded physical windows are shorter or longer than nominal widths at material rates, especially Polygon and Avalanche. The current design mixes fixed action count, empirical cadence, a wall-clock deadline, truncation, and overflow. Choose and teach one action geometry. |
| A 600-second lookback is the model's complete receptive field. | **False.** | Current fixed contexts span roughly 10-14 minutes, and rolling features reach up to 199 rows before the first sequence row. “Lookback” currently names neither the final tensor span nor total raw-history reach. |
| Earliest `argmin` ties are negligible. | **False on Polygon.** | About 39% of sampled Polygon training windows tied. Earliest-minimum is a lean, defensible no-extra-wait rule, but it is a target policy and affects class balance. State it and test alternatives only if the economic result warrants complexity. |
| `exact_optimum_hit_rate` is pure fee-optimal accuracy. | **False when fees tie.** | It compares one row identity chosen by earliest `argmin`. A later equal-fee action is fee-optimal but counted wrong. Either name the lexicographic fee-then-delay rule or score membership in the raw-integer minimum-fee action set and report delay separately. |
| Exact current-row fee construction is one cross-chain rule. | **False.** | It is supportable from closed-parent fields on Ethereum. Polygon becomes producer-configurable after Lisovo, and Avalanche ACP-176/Granite needs fee state and child time absent from the canonical schema. |
| Every current feature is needed. | **Unsupported.** | The set has 45 features, overlapping rolling summaries, duplicated time scales, and realized target-row cadence/calendar fields. Start ablation from closed fee/history plus lagged protocol pressure. A feature survives only if live causality and held-out benefit both hold. |

### Training, metrics, and HPO

| Claim | Verdict | Correction or consequence |
|---|---|---|
| Epoch weighted CE is correctly averaged. | **False; confirmed selection defect.** | PyTorch's weighted mean divides by the sum of target weights. SPICE multiplies each batch mean by batch size, then divides by sample count. The result changes with batch partition; batch size is itself tuned. Prefer unweighted CE as the lean control. If weighting survives ablation, accumulate the exact weighted numerator and denominator. |
| Stock macro F1 omits a class absent from targets even when predicted. | **False alarm, cleared.** | TorchMetrics and scikit-learn use the union-active set: only classes with no target **and** no prediction support are inactive. Current SPICE skips every target-absent class. For targets `[0, 0]` and predictions `[0, 1]`, SPICE returns `2/3`; both libraries return `1/3`. Replace the custom reducer if macro F1 survives. |
| Macro F1 is required because it exists. | **Unsupported.** | The paper does not report it, and downstream action quality is primary. Keep it only if it answers a named imbalance question. Cross-entropy, accuracy, and approved economic outcomes may be the leaner teaching set. |
| The configured seed controls model initialization. | **False.** | `pipeline.py:251-255` constructs the model before `runtime_planning.py:73-82` seeds the fit runtime. Seed once before dataset/model construction. |
| A training checkpoint guarantees exact stochastic continuation. | **False.** | It stores model, optimizer, fit-policy state, and epoch, but not global RNG or sampler position/state. Either store enough state and prove equivalence or describe resume as approximate. Deleting within-trial resume is leaner if rerunning a trial is acceptable. |
| Every Optuna trial is validation-only. | **False.** | `run_trial_training()` builds validation and test summaries for every trial. The returned objective uses validation only, so this is not direct objective leakage, but it repeatedly opens the test and wastes work. Trial execution should not compute test metrics. |
| Current pruning saves training work. | **False.** | `trial.report()` and `should_prune()` run only after complete training and summary construction. Report each validation epoch or use `NopPruner`; the present branch adds concepts without savings. |
| Loading an existing Optuna study continues the exact seeded sampler. | **False.** | Fresh creation supplies seeded `TPESampler` and an explicit pruner. `optuna.load_study()` is called without them, so defaults are reconstructed. Stored trials remain usable, but exact seeded continuation is not preserved; a no-pruning study also reloads a default median pruner, currently neutralized only by the config guard. |
| The auxiliary scalar fee head is operationally required. | **Unsupported.** | It contributes SmoothL1 and diagnostics, but decoding and serving use logits only. Ablate it; delete it if it does not improve held-out action economics or robustness. |
| Economic replay should automatically replace predictive validation loss for every epoch. | **Unsupported and risky.** | Replay estimates can be high-variance and invite repeated validation-window overfitting. A lean default is stable, correctly reduced predictive loss for early stopping, then predeclared downstream economics for finalist/HPO selection. The frozen A/B evidence should decide; do not infer the answer from metric names. |

### Evaluation and economic interpretation

| Claim | Verdict | Correction or consequence |
|---|---|---|
| Offline `profit_over_baseline` and serving savings percent are the same estimator. | **False.** | Offline reports the mean of event-relative savings; serving reports the ratio of total savings to total baseline fee. Both are coherent but answer different questions. Historical sign flips show the distinction is material. Choose names and a primary estimand explicitly. |
| The top-level replay mean gives every sampled window equal weight. | **False.** | `temporal_accounting.py:55-65` pools event numerators and divides by total events, so windows with more sampled arrivals receive more weight. `window_metrics` separately summarize per-run means with equal run weight. Under fixed-duration homogeneous arrivals, event count is independent of window start, so both approach the same window-kernel expectation as repetitions grow; their finite-sample estimators and uncertainty summaries still differ. |
| Offline fee sums are full transaction cost. | **False.** | Replay sums repeated base-fee-per-gas values. Serving multiplies the observed block base fee by receipt gas used. Neither includes the full user payment without explicit priority/tip and fee-cap semantics. Use “base-fee component” unless the scope expands. |
| The current Poisson evaluator faithfully simulates arbitrary transaction arrival and inclusion. | **False.** | It samples arrival times, maps each to the most recent prepared block anchor, discards the within-block arrival time, then reuses block-state action outcomes. It is a random exposure weighting of block states, not a mempool/builder simulator. |
| Observed inter-block intervals are automatically the correct exposure weights for the intentional forming-block task. | **False.** | They are correct only for a post-observation state held until the next observation. A forming-block row needs an eligibility interval during which its features are available and a public broadcast can still reach that block. Derive weights from the approved decision clock. |
| Integer-second timestamps represent every block's arrival exposure. | **False on duplicate timestamps.** | `searchsorted(..., side="right")` gives all positive exposure to the last sample in a tied timestamp group; earlier same-second blocks are unreachable by continuous arrivals. Avalanche has same-second canonical rows. Use causal higher-resolution time or an explicitly block-weighted estimand. |
| Time-Poisson and block-Poisson estimate the same workload. | **False.** | Time replay weights elapsed request time; block replay gives each block unit exposure in expectation. The latter assumes workload scales with block production. Keep one only after choosing the workload unit. |
| Poisson arrival RNG is necessary for the fixed-window event mean. | **Usually false.** | Conditional on at least one arrival in a fixed window under a homogeneous independent Poisson process, expected event mean is the duration-weighted mean of mapped block states. This can be computed deterministically. Arrival rate still controls counts/totals. |
| All replay randomness can therefore be deleted without changing the estimand. | **False.** | Each repetition also samples a uniform random window start. The equivalent corpus-level exposure is a boundary-aware window-inclusion kernel: states near the coverage edges occur in fewer possible windows than interior states. Preserve that kernel analytically, or deliberately replace it with predeclared/enumerated windows. A finite-workload or latency-coupled question still needs simulation. |
| Event mean equals the ratio of expected fee sums. | **False in finite samples.** | A ratio of expected sums is a long-run/exposure ratio, not generally the expectation of a random finite-sample ratio. The approved metric must state which object it estimates. |
| Overlapping sampled windows make Monte Carlo repetitions dependent. | **False, conditional on the fixed trace and current independent RNG draws.** | Window starts and Poisson processes are independent simulator draws even when their historical spans overlap. A Monte Carlo standard error can describe numerical integration error for this fixed trace. It cannot be presented as uncertainty across new days, regimes, chains, or fitted models. |
| Current replay error bars are deployment confidence intervals. | **False.** | They use run-level population SD (`ddof=0`) and `1.96*SD/sqrt(repetitions)` on one fixed model/trace. At most they approximate conditional Monte Carlo integration error; sample SD and the actual valid-run count would be the conventional finite-run calculation. Seeds and held-out periods are separate uncertainty units. |
| “Strict deadline” prevents late actions from looking good. | **False.** | The action mask exposes every nominal slot. Short-window overflow resolves to the first post-window row, while the optimum is restricted to reachable rows. A checked-in test expects overflow to produce negative `cost_over_optimum`, so missing the deadline can be rewarded. Mask overflow, assign an explicit miss penalty, or rename the policy; do not retain this ambiguity. |
| One mean is enough to describe scheduler safety. | **Unsupported.** | Keep a small risk surface: primary mean/ratio, harmful-run rate, and one tail-severity statistic. Existing results contain many negative observations; a large positive mean can hide frequent or severe harm. |
| One repeatedly inspected day remains a test set. | **False in practice.** | Once decisions are changed after viewing it, it is validation evidence. Use multiple predeclared forecast origins across protocol regimes and reserve a final untouched test surface if the thesis makes generalization claims. |

### Protocol, serving, frameworks, and documentation

| Claim | Verdict | Correction or consequence |
|---|---|---|
| Live serving differs from offline only by a harmless `+1`. | **False; confirmed blocker.** | With latest chain head `L`, default confirmation depth two yields observed `h=L-2`. Serving targets `h+k+1`; `k=0` targets `L-1` and `k=1` targets `L`, both already closed. Baseline `h+1=L-1` is also closed. Separate the stable context head from the actionable head and share one action mapper with replay. |
| Setting confirmation depth to zero is an automatic fix. | **Unsupported.** | It changes finality/reorg risk and still does not prove forming-row feature parity or transaction cut-off. The correct fix follows the approved decision clock. |
| Polygon's 1-second cadence increase begins at Lisovo. | **Causal attribution corrected.** | The Lisovo-to-Giugliano segment is 99.9997% 2-second deltas with mean 2.000004 seconds. Post-Giugliano, 1-second deltas are 7.7718% and the mean falls to 1.92229 seconds. Lisovo remains the fee-configurability boundary; Giugliano is the observed cadence boundary in this corpus. |
| A custom cross-chain EIP-1559 replayer is the lean default. | **False.** | Ethereum's recurrence is small. Polygon and Avalanche are regime-specific; existing client/RPC estimators may be clearer than custom parsing where they expose the needed **actionable** state. Prototype availability and timing before adding adapters. |
| Replacing FastAPI or `sqlite3` automatically makes serving leaner. | **False.** | The HTTP need is the scope gate. If a loopback HTTP demo remains, FastAPI plus stdlib SQLite is already small; an ORM would add machinery. If HTTP is unnecessary, a CLI/in-process demo can remove the service. Current async endpoints also call synchronous SQLite; offload or bound that work before adding `aiosqlite`. |
| SQLite context managers close connections. | **False.** | `with Connection` commits/rolls back but does not close. Use explicit ownership/closing if the service survives. |
| The current Lightning path is idiomatic Lightning. | **False.** | SPICE disables automatic optimization and framework checkpointing while owning optimizer, backward, clipping, policy, best state, and persistence. Compare one direct-PyTorch loop with one automatic-Lightning loop. Choose measured total code/concepts; framework preference is not evidence. |
| All 46 architecture/implementation notes should be expanded independently. | **Poor teaching architecture.** | The inventory is 27 `ARCHITECTURE.md` plus 19 `IMPLEMENTATIONS.md`, 3,659 lines, no internal Markdown links, stale indexes, and repeated local taxonomies. Put theory, timeline, formulas, and worked examples in a small top-level learning path. Retain local notes only for genuinely deep modules/non-obvious algorithms; merge or retire duplicate `IMPLEMENTATIONS.md` files after semantics are approved. |

## Independent numerical reproductions

The following uses the current artifact corpora: Ethereum `cor_2edb8f7b84a4edf95e2b`, Polygon `cor_61fb33e47c948a9cebd0`, and Avalanche `cor_3ef359c91addcab77e9f`.

| Chain | Corpus rows | Prepared samples | Sequence length | Mean / median context span | Earlier-role samples whose outcome crosses train→validation / validation→test |
|---|---:|---:|---:|---:|---:|
| Ethereum | 2,665,736 | 1,533,036 | 64 | 760.77 s / 756 s | 3 / 3 |
| Polygon | 13,584,311 | 6,827,317 | 300 | 609.10 s / 598 s | 18 / 18 |
| Avalanche | 25,776,042 | 14,065,826 | 600 | 811.22 s / 813 s | 28 / 15 |

The crossing counts are small because the future horizon is short, but leakage is categorical rather than percentage-based: those labels use future rows at or beyond the next role's first anchor. The fix is a short exact purge, not a large arbitrary gap.

One million evenly spaced training anchors per chain produced:

| Chain | Nominal action width | Mean physical candidates | Shorter than width | Longer than width | Tied minima |
|---|---:|---:|---:|---:|---:|
| Ethereum | 4 | 3.979410 | 2.0407% | 0.0000% | 0.0000% |
| Polygon | 19 | 18.113953 | 72.8041% | 0.0000% | 39.0277% |
| Avalanche | 23 | 24.254183 | 37.1251% | 54.1569% | 0.0028% |

These values explain why overflow and tie policy are not edge-case-only implementation details.

A read-only recomputation over all 1,296 historical rows in `benchmarks/results.sqlite` compared the stored mean of per-event relative savings with each observation's `sum(baseline-realized) / sum(baseline)`:

| Chain | Stored event mean | Mean per-observation ratio of fee sums | Negative stored observations | Sign flips |
|---|---:|---:|---:|---:|
| Avalanche | +0.384616% | +0.535235% | 139 | 28 |
| Ethereum | +1.181614% | +1.314268% | 2 | 2 |
| Polygon | -0.060895% | +0.046088% | 276 | 50 |

There were 80 sign flips and 417 negative stored observations overall. The database holds two 648-observation collections using the same three trained artifacts, so these are not 1,296 independent trials. The rows mix historical configurations and unresolved semantics. They demonstrate estimator materiality and tail risk; they do **not** prove model efficacy or select a route. A ratio pooled across all observations is a third weighting and should not be conflated with the table's mean per-observation ratio.

Polygon recurrence replay supplied another high-impact cross-check. Across 3,268,067 post-Lisovo children, 2,945,908 (90.1422%) differ from the fixed post-Dandeli recurrence. The first observed departure is block 84,072,256 at 2026-03-11 21:29:05 UTC; maximum parent-relative change is 5%. This confirms that a universal fixed recurrence is materially wrong for the corpus suffix. It does not make that first departure a protocol fork: Lisovo is the rule boundary.

## Smallest coherent route candidates

None is approved. Every route first needs one three-block worked fixture per chain/regime containing the closed context head, live/actionable head, decision time, available fields, class-zero action, first eligible target, deadline, and offline/serving outcome.

### A. Preserve physical forming-block offset zero

Keep the intentional interpretation: class zero targets the currently forming block. Build a virtual open row offline and live from facts available before transaction selection closes. Ethereum can derive the child fee from closed-parent EIP-1559 fields. Polygon configurable eras and Avalanche require additional state or a causal estimate; realized child timestamp/cadence cannot be copied into the input.

This preserves intent most directly. It also has the largest actionability and protocol burden. Reject per-chain machinery that cannot prove the public transaction can still reach the block.

### B. Preserve immediate action, separate it from the physical feature row

End input at a universally closed parent. Define class zero as “submit now at `tau`”; one shared outcome function maps that action to the first eligible realized inclusion block. This removes the claim that a finalized target row was observable and can keep immediate-action behavior across chains.

This is probably the smallest universal contract, but it changes the user's physical-current-row interpretation. It therefore requires explicit approval and must not be smuggled in as cleanup.

### C. Paper-next-block comparator

End context at closed block `h`; class zero and baseline target the first future eligible block. This is easiest to compare with the paper. Keep it as an explicit experimental comparator unless the owner chooses it as the project task. Prior current-row results cannot be relabeled as this route.

### Lean control stack for any route

Before comparing LSTM, Transformer, and hybrid, establish:

1. immediate-action and most-frequent-class rules;
2. an exact protocol/native-estimator baseline where available;
3. a scalable linear classifier on a compact last-row/summary representation using the already-installed scikit-learn [`DummyClassifier`](https://scikit-learn.org/stable/modules/generated/sklearn.dummy.DummyClassifier.html) and [`SGDClassifier(loss="log_loss")`](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html); and
4. one small LSTM with unweighted CE and a single action head.

Only then should attention, a hybrid, class weights, the scalar auxiliary head, long rolling features, or chain-specific virtual rows earn their extra concepts through predeclared held-out economics. A simple baseline losing slightly can still be the right thesis model if the difference is practically small and the explanation cost is materially lower.

For the training host, prototype the same tiny fit in direct PyTorch and automatic Lightning. Count production lines, concepts the thesis must teach, checkpoint/reproducibility guarantees, and dependencies. Do not count a framework call as free if custom callbacks and persistence recreate its internals.

## Wayfinder amendments and dependency edges

The existing clean-break graph should add or strengthen the following owner-gated nodes. These are investigation/decision tickets, not approved implementation work.

1. **Choose the temporal decision clock and class-zero contract.** Blocked by none. This precedes compiler, feature, evaluation, serving, and paper-alignment decisions.
2. **Prove chain/regime feature availability and actionability.** Blocked by the decision clock. Cover Ethereum, Polygon fixed/configurable eras, Avalanche ACP-176/Granite, and Sepolia deployment. Compare native RPC/client estimates with custom reconstruction.
3. **Repair the scientific data boundary.** Blocked by the decision clock. Purge forward outcomes, fit every learned statistic on train only, declare forecast origins/protocol regimes, and reserve a final test surface.
4. **Choose one action/deadline geometry.** Blocked by the decision clock and chain proof. Resolve wall-clock horizon versus fixed block offsets, candidate truncation, ties, overflow, and miss penalty.
5. **Define loss and metric estimands.** Blocked by action geometry. Fix weighted reduction, decide whether weights/F1/scalar head survive, and name event mean versus ratio-of-sums and base-fee scope.
6. **Prototype deterministic exposure evaluation.** Blocked by the metric estimand. Remove only arrival RNG that is analytically redundant; retain or replace random-window policy explicitly. Compare against finite Poisson simulation when workload totals or latency matter.
7. **Run the lean baseline/model/feature ablation.** Blocked by corrected data and metrics. Compare rules, protocol estimator, scalable linear model, small LSTM, then optional deep/auxiliary/feature additions under one budget.
8. **Repair the intentional bounded HPO extension.** Blocked by stable loss, split, and selected model space. Validation-only trials, epoch reporting or `NopPruner`, explicit resumed sampler/pruner, seed before construction, a frozen finalist across at least three declared seeds, and one final test.
9. **Reconcile stable-head context with actionable-head serving.** Blocked by the decision clock and chain proof. Share one action/outcome mapper; do not patch with a constant offset.
10. **Choose the training host and interruption promise.** Blocked by the small-model prototype. Direct PyTorch versus automatic Lightning; exact stochastic resume versus a documented rerun policy.
11. **Rewrite the ML learning path and module docs.** Blocked by approved semantics and framework. Teach the decision timeline, data construction, leakage boundary, loss math, fit/HPO lifecycle, evaluation estimands, limitations, and one worked example. Then shorten local module notes and add links.
12. **Cross-verify the whole temporal contract.** Blocked by all above decisions. One reviewer should trace the same example from raw blocks through features, label, fit, replay, API response, and observed economics before ADR disposition.

Two explicit non-tickets: “revert offset zero” and “delete HPO.” Either can become a candidate only through an owner decision, not as an inferred cleanup.

## Documentation shape for an undergraduate reader

Expansion should add explanation once, not repeat it in every directory. A lean target is:

- one temporal-ML guide: problem statement, symbols, decision timeline, paper-versus-extension table, preprocessing, model, training, evaluation, and limitations;
- one worked three-block example carried end-to-end with actual numbers;
- one experiment guide: splits, HPO, baselines, final test discipline, and how to interpret each metric;
- one system map linking to short module ownership/invariant notes; and
- one evidence glossary distinguishing protocol fact, paper claim, SPICE extension, empirical result, hypothesis, and owner decision.

Every formula should state its aggregation unit and denominator. Every feature should state when it becomes available. Every metric should include one tiny numerical example and failure mode. Retained local `ARCHITECTURE.md` files should explain stable boundaries only for genuinely deep modules. Non-obvious algorithm notes can be merged there or retained in a local `IMPLEMENTATIONS.md` only when separation adds teaching value; duplicate catalog/tree prose should be retired. Remove stale paths such as the root index entry for the absent `src/spice/objectives/ARCHITECTURE.md` rather than preserving historical topology.

## Primary references and companion audits

- Project foundation: `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`.
- Intent: commit `e0b2e68e`, [`PROGRESS.md`](../../../PROGRESS.md), and [`ARCHIVE.md`](../../../ARCHIVE.md).
- Companion investigations: [paper alignment](temporal-paper-alignment-audit.md), [preprocessing theory](temporal-preprocessing-theory-audit.md), [training/evaluation theory](temporal-training-evaluation-theory-audit.md), [evaluation/statistics cross-review](temporal-evaluation-statistics-cross-review.md), [lean alternatives](temporal-ml-lean-alternatives.md), [chain protocol](temporal-chain-fee-protocol-audit.md), and [documentation](architecture-implementation-docs-audit.md).
- Ethereum: [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559).
- Polygon: [PIP-79](https://forum.polygon.technology/t/pip-79-bounded-range-validation-for-configurable-eip-1559-parameters/21711), [Bor v2.6 verifier](https://github.com/0xPolygon/bor/blob/v2.6.0/consensus/misc/eip1559/eip1559.go), and [Giugliano announcement](https://polygon.technology/blog/giugliano-upgrade-faster-confirmations-predictable-fees-and-a-more-resilient-network-for-polygon-chain).
- Avalanche: [ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates), [Coreth v0.15.1 base-fee source](https://github.com/ava-labs/coreth/blob/v0.15.1/plugin/evm/header/base_fee.go), and [Granite](https://build.avax.network/blog/granite-upgrade).
- Loss semantics: [PyTorch `CrossEntropyLoss`](https://docs.pytorch.org/docs/stable/generated/torch.nn.CrossEntropyLoss.html).
- Macro F1: [TorchMetrics `MulticlassF1Score`](https://lightning.ai/docs/torchmetrics/stable/classification/f1_score.html), [TorchMetrics reduction source](https://github.com/Lightning-AI/torchmetrics/blob/v1.9.0/src/torchmetrics/utilities/compute.py#L82-L93), and [scikit-learn `f1_score`](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html).
- Time-series leakage: [scikit-learn `TimeSeriesSplit`](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) and [preprocessing pitfalls](https://scikit-learn.org/stable/common_pitfalls.html).
- Training/HPO: [PyTorch reproducibility](https://docs.pytorch.org/docs/stable/notes/randomness.html), [Lightning optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html), [Optuna pruning](https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/003_efficient_optimization_algorithms.html), and [`optuna.load_study`](https://optuna.readthedocs.io/en/stable/reference/generated/optuna.load_study.html).
- Poisson theory: [MIT 6.262 Poisson-process notes](https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/resources/mit6_262s11_chap02/).
