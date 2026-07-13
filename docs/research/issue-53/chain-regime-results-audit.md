# TODO 29/06 and 06/07 chain-regime results audit

**Status:** evidence audit, not a causal study. No model was trained, no benchmark was rerun, and no production or tracker state was changed.

## Bottom line

The 29/06 and 06/07 results are internally traceable and their broad chain ordering is stable: Ethereum is consistently positive, Polygon is slightly negative, and Avalanche is positive but much less stable than Ethereum. The apparent “erratic” Polygon and Avalanche behavior cannot be attributed cleanly to one network upgrade.

For Polygon, the largest positive and negative profit excursions already occur before Lisovo. Lisovo/Giugliano therefore cannot explain the original scatter. After the fee-rule departure and Giugliano, exact-hit accuracy falls sharply, but profit remains slightly negative and its variance *shrinks*. This is compatible with a modern-regime mismatch, but it is not evidence that the upgrades caused the earlier outliers.

For Avalanche, all external evaluation windows are post-Granite while the fitting split is pre-Granite. Granite's dynamic block-timing mechanism is a plausible contributor because the observed cadence accelerates and a nominal 36-second, 23-slot action is then truncated to about 22 seconds in most recent rows. However, there is no same-model pre/post-Granite evaluation discontinuity here, and time, cadence, fee conditions, and window selection all move together. “Granite caused the result” would overstate the evidence.

The lean conclusion is to preserve the intentional `k = 0` forming-block action, but stop treating a fixed number of future block slots as a chain-independent 36-second horizon. Before retraining anything, report results by explicit protocol regime and disclose the effective represented time horizon.

## Provenance and what was checked

The source notebook is `/Users/edo/Documents/Obsidian/the-vault/notes/TODO.md`. The full `### 29/06` and `### 06/07` sections were audited; `### 22/06` was used only as an older sanity check.

All 32 figures linked from 29/06 and 06/07 exist in both the Obsidian `notes/benchmark_figures` directory and `benchmarks/figures`. Their paired files are byte-identical, and their current hashes match the frozen rows in [`spice-pre-break-evidence-manifest.tsv`](../spice-pre-break-evidence-manifest.tsv). The same check passes for all 26 figures linked by the 22/06 sanity section. Thus none of the conclusions below depends on a missing or silently replaced plot.

| TODO section | Linked figures | Result exports | Benchmark configuration |
|---|---:|---|---|
| 29/06 wall-clock | 14 | `lstm_36s_wall_clock_quartile_correlations.csv` and the three `*_wall_clock_quartile_joined.csv` files | [`lstm_36s_wall_clock_quartile_eval.yaml`](../../../src/spice/conf/benchmark/lstm_36s_wall_clock_quartile_eval.yaml) |
| 06/07, 1,200 blocks | 16 | `lstm_36s_block_count_quartile_correlations.csv`, three `*_block_count_quartile_joined.csv` files, and Polygon bulk/outlier exports | [`lstm_36s_block_count_quartile_eval.yaml`](../../../src/spice/conf/benchmark/lstm_36s_block_count_quartile_eval.yaml) |
| 06/07, 300 blocks | 2 directly linked cross-chain figures; per-chain results remain in the 300-block exports and renderer output | `lstm_36s_block300_quartile_correlations.csv`, three `*_block300_quartile_joined.csv` files, and Polygon bulk/outlier exports | [`lstm_36s_block300_quartile_eval.yaml`](../../../src/spice/conf/benchmark/lstm_36s_block300_quartile_eval.yaml) |

The last row needs one clarification: TODO directly links 18 figures under 06/07—two cross-chain figures for each block count, plus 14 displayed per-chain 1,200-block figures. The 300-block per-chain results are present in the corresponding exports and renderer output even though TODO does not repeat their wikilinks. The audit used the CSVs, not visual estimation from the plots, for numerical and fork-boundary grouping.

The three configurations use the same artifact for each chain across all window constructions:

| Chain | Artifact | Corpus | Training action width | Nominal interval |
|---|---|---|---:|---:|
| Ethereum | `art_c433194c8699a301f7c5` | `cor_7bea5a071afaf090c05a` | 4 | 12 s |
| Polygon | `art_9cdfcc1f75aadb355673` | `cor_61fb33e47c948a9cebd0` | 19 | 2 s |
| Avalanche | `art_4a91b895e756192c4106` | `cor_3ef359c91addcab77e9f` | 23 | 1.6 s |

Artifact metadata was read from each artifact's `.spice/state.sqlite` in
read-only mode. All three are one-seed (`2026`) baseline LSTMs using
`current_row_nominal`, a configured 600-second lookback, a 36-second maximum
delay, and the same 45-feature schema. Their realized fixed sequence lengths
are chain-specific. The dataset builder makes chronological
train/validation/test splits
([`fixed_sequence_temporal.py`](../../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py));
this matters because upgrade regimes are not randomly mixed across roles.

There is one reproducibility caveat. The frozen outputs and hashes are reliable evidence, but [`render_lstm_block_count_quartile_results.py`](../../../benchmarks/scripts/render_lstm_block_count_quartile_results.py) currently has uncommitted generalization changes. The exact historical renderer identity therefore cannot be inferred from the working tree alone. This is already recorded in [`research-evaluation-publication-assets-inventory.md`](../research-evaluation-publication-assets-inventory.md), [`evaluation-suite-data-findings.md`](../issue-8/evaluation-suite-data-findings.md), and [`ticket-8-research-script-inventory.md`](../issue-8/ticket-8-research-script-inventory.md). It does not change the exported numbers audited here.

## What the comparisons actually estimate

The three constructions are related, but they do not differ only in “window length.”

- Wall-clock selection finds 4–72-hour market regimes, but [`poisson_replay.py`](../../../src/spice/evaluation/poisson_replay.py) averages 50 randomized **two-hour** replay episodes inside each selected regime at 0.05 arrivals per second. A point labelled by a 72-hour window is therefore not a continuous 72-hour replay result.
- The 1,200-block evaluator draws 50 fixed-block subwindows at 0.3 arrivals per block ([`block_poisson_replay.py`](../../../src/spice/evaluation/block_poisson_replay.py)).
- The 300-block evaluator uses 200 repeats at the same per-block arrival rate. More repeats narrow Monte Carlo error, but do not add model seeds or independent protocol regimes.

Consequently, changes across the three plots mix selection geometry, real-time exposure, arrival process, and replay length. Their confidence intervals measure repeat-to-repeat replay variability conditional on one trained model and one selected window. They are not uncertainty intervals over training seeds, upgrade regimes, or future deployments; see [`temporal-training-evaluation-theory-audit.md`](../issue-1/temporal-training-evaluation-theory-audit.md).

## Full 29/06 versus 06/07 result

The chain-level mean is much more stable than individual short-window outcomes:

| Chain | Wall-clock mean ± SD | 1,200-block mean ± SD | 300-block mean ± SD | Negative windows |
|---|---:|---:|---:|---:|
| Ethereum | +1.199% ± 0.393 | +1.169% ± 0.466 | +1.194% ± 0.640 | 0%, 0%, 0.9% |
| Polygon | -0.126% ± 0.339 | -0.071% ± 1.140 | -0.051% ± 2.306 | 87.5%, 71.8%, 56.9% |
| Avalanche | +0.367% ± 0.536 | +0.407% ± 0.953 | +0.362% ± 1.868 | 28.7%, 27.3%, 36.6% |

Shorter fixed-block windows chiefly increase dispersion, especially on faster chains. They do not reverse the overall chain ordering.

The volatility correlation is the clearest example of what does and does not persist:

| Chain | 22/06 tail-selected sanity | 29/06 wall-clock | 06/07 1,200 blocks | 06/07 300 blocks | Interpretation |
|---|---:|---:|---:|---:|---|
| Ethereum | 0.874 | 0.721 | 0.676 | 0.589 | positive relation persists |
| Polygon | 0.008 | 0.033 | -0.064 | -0.048 | consistently near zero |
| Avalanche | 0.307 | 0.659 | 0.219 | -0.095 | sign/magnitude not robust |

Fee-level correlations are also construction-sensitive: on 29/06, log-fee/profit `r` is -0.242, +0.395, and +0.534 for Ethereum, Polygon, and Avalanche; on 06/07 it is -0.505/-0.098/+0.449 at 1,200 blocks and -0.216/+0.028/+0.278 at 300 blocks. These are descriptive associations across deliberately selected windows. Time and protocol regime are not controlled, so the `p` values do not establish fee level or volatility as causes of profit.

## Polygon: upgrades explain a regime mismatch, not the original outliers

The Polygon artifact's fitting role is wholly pre-Lisovo. External evaluation spans Dandeli, Lisovo, the first observed departure from the earlier exact recurrence, and Giugliano:

| Boundary | Mainnet block / UTC | Relevance |
|---|---|---|
| Dandeli | 81,424,000 / 2026-01-09 14:01:02 | Bor changed the target-gas calculation; this is an important omitted confounder ([official Bor release notice](https://forum.polygon.technology/t/bor-v2-5-6-and-erigon-v3-3-6/21547)) |
| Lisovo | 83,756,500 / 2026-03-04 14:03:51 | PIP-79 relaxes validity to a bounded child-fee change rather than one mandatory parent-only recurrence ([PIP-79](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/c65ce300229593bea17ff21f569c259121b4dd11/PIPs/PIP-79.md#L50-L58)) |
| First observed recurrence departure | 84,072,256 / 2026-03-11 21:29:05 | empirical boundary in this corpus; it is later than fork activation and must not be relabelled as the fork itself |
| Giugliano | 85,268,500 / 2026-04-08 14:03:57 | PIP-83 publishes the child block's gas target and denominator in Bor extra data ([PIP-83](https://github.com/0xPolygon/Polygon-Improvement-Proposals/blob/9a7feed01afdf6923bfac3dd10bbb4631ed50099/PIPs/PIP-83.md#L28-L44)) |

Bor's post-Lisovo verifier accepts any child base fee within the permitted bound; it does not require the old exact recurrence ([Bor verifier](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/consensus/misc/eip1559/eip1559.go#L38-L108)). A stock producer still calculates a fee from parent state plus producer-local gas parameters ([Bor calculation](https://github.com/0xPolygon/bor/blob/920556e8f7859526ad33fca57ef3f2f42ee91fff/consensus/misc/eip1559/eip1559.go#L110-L199)), but those child parameters become public with the child header, not as a protocol-guaranteed parent preannouncement. A recent subset can therefore reconstruct the realized child fee retrospectively; it cannot generally recover an exact parent-known target merely by choosing “modern” blocks.

Strict, fully contained evaluation windows show the following around the empirical departure and Giugliano:

| Method | Exact-hit accuracy: before / departure→Giugliano / after | Mean profit: before / middle / after | Profit SD: before / after |
|---|---:|---:|---:|
| Wall-clock | 30.37% / 13.71% / 9.30% | -0.179% / -0.050% / -0.057% | 0.418 / 0.190 |
| 1,200 blocks | 29.81% / 16.29% / 10.65% | -0.085% / -0.061% / -0.052% | 1.568 / 0.083 |
| 300 blocks | 31.54% / 15.38% / 8.77% | -0.055% / -0.078% / -0.022% | 2.963 / 0.075 |

Two wall-clock windows cross a boundary and are excluded from that strict grouping. The result is not “post-upgrade became erratic.” Exact hits degrade, but post-Giugliano profit is tightly concentrated near zero. The exported 300- and 1,200-block outlier rows all end before block 83.65 million, hence before Lisovo. Those earlier outliers need an earlier explanation: Dandeli, fee/capacity regimes, sampling, model error, or their interaction.

The fixed-width horizon also begins to drift after Giugliano. The 19-slot Polygon action was derived from `floor(36 / 2) + 1`. In the full post-cutoff corpus, 31.1% of post-Giugliano rows contain more than 19 physically reachable candidates inside 36 seconds; by May, 69.3% do. The 19th represented candidate remains near 36 seconds in the median but can be around 31 seconds at the fifth percentile. That can lower exact-hit accuracy without implying that the intentional forming-block action is wrong.

Finally, the Polygon “bulk” plots are not neutral robustness filters. The fee bulk rule removes 10 of 108 selected fee windows outside a log-IQR range (about 19.74–1,485.05 gwei), which also removes real temporal regimes. The volatility bulk rule filters on the *outcome* `profit_over_baseline_percent` (two 1,200-block and three 300-block points). Outcome-based deletion must not be used to support a correlation claim; full results should be primary and bulk plots descriptive only.

## Avalanche: Granite is plausible, but the current data cannot isolate it

Avalanche Granite activated on mainnet on 2025-11-19 at 16:00 UTC ([Avalanche Foundation announcement](https://build.avax.network/blog/granite-upgrade)). The artifact fitting rows are entirely pre-Granite; Granite enters late in validation, and all external benchmark windows are post-Granite.

Granite's ACP-226 adds millisecond timestamps and a dynamically updated minimum block delay ([ACP-226](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times)). ACP-176 also changes dynamic EVM gas-limit and fee discovery ([ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates)). These mechanisms make a cadence shift theoretically credible.

The local corpus exhibits that shift. Before Granite, a 36-second interval contains a median of 24 candidates; in post-cutoff evaluation it contains 35, with 98.0% of rows exceeding the model's 23 available action slots. The last represented slot is only about 22 seconds ahead in the median. Monthly mean inter-block time falls from 1.368 seconds in December to roughly 1.03–1.05 seconds in April–May, while wall-clock mean profit and exact-hit accuracy decline from about +1.17%/18.1% in December to around +0.02%/7.5% in April and -0.05%/13.0% in May.

That joint movement is **consistent with** cadence-driven horizon truncation and a pre-/post-Granite distribution shift. It is not a causal estimate: all evaluation is already post-Granite, calendar time, load, fee regime, and cadence co-vary, and there is only one trained seed. Avalanche's volatility/profit correlation changing from +0.659 to +0.219 to -0.095 across selection constructions reinforces that its simple bivariate relation is not robust.

Ethereum is a useful empirical control for overclaiming. Its evaluation also follows a temporally earlier training split, yet its 4-slot action still covers the physical 36-second candidates almost exactly (98.7% of rows have four candidates; none has more) and its profit/volatility relationship remains positive across every construction. A generic “trained before a network change” explanation is therefore insufficient; the action-horizon/cadence interaction is the more specific hypothesis worth testing.

## Lean next check

No new framework or model is needed to resolve the immediate interpretation problem. The smallest defensible follow-up is one frozen table from the existing joined CSVs that:

1. uses only windows fully contained inside named protocol regimes;
2. reports full results without deleting profit outliers;
3. adds median physical candidates in 36 seconds and median time reached by the last representable action slot;
4. reports accuracy and profit together; and
5. labels wall-clock outcomes as mean two-hour replay episodes conditional on the selected longer regime.

If a later experiment is approved, retrain one model on a single recent regime with the action boundary derived from observed time rather than a fixed nominal slot count, while keeping `k = 0` as the forming block. Compare that one model against the current artifact on the same fully contained windows. More HPO, more seeds, or a new evaluation framework would add machinery before answering the narrower mismatch question.

## Evidence limits

The fork grouping is observational. Selected windows are not randomized over protocol regimes, adjacent windows can share surrounding market conditions, exact-hit accuracy is sensitive to ties and discrete targets, and one seed cannot quantify training uncertainty. The report therefore supports three claims only:

- Polygon's pre-Lisovo excursions rule out Lisovo/Giugliano as their sole cause.
- Polygon's modern exact-hit collapse and Avalanche's post-Granite cadence/truncation are genuine measured regime mismatches worth isolating.
- Neither mismatch currently proves that a specific upgrade caused profit behavior.
