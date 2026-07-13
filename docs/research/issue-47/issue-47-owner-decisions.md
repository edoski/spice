# Issue 47 owner decisions

Planning-only decision ledger for
[issue 47](https://github.com/edoski/spice/issues/47). This file records explicit
owner answers relayed through the orchestrator; it is not a normative guide or an
implementation change.

## Decision 1 — offline and live block-hash scope

**Status:** approved by Edo on 2026-07-11.

- Withdraw the inline 32-byte block_hash requirement and its sidecar alternative from the baseline.
- Offline origins use (content-bound corpus_id, chain_id, block_number).
- Seal immutable corpora with exact chain/schema/units/regime/range facts, canonical package/content digest, and per-Parquet-file SHA-256; same ID with different content is rejected.
- Future acquisition validates every adjacent parentHash link across rows and file boundaries plus ordering/chain/finality anchor, then retains only compact boundary/acquisition evidence.
- Live decisions separately persist (h, hash(h)), k, b with parent facts and Ethereum scalar bound to the same frozen response.
- Selected historical hashes are retained/fetched only for a specific physical-header parity, hash join, or reorg claim.
- No mandatory full hash sidecar unless a later concrete thesis claim earns it.
- Existing numeric Parquet remains reusable; no republishing merely to add row hashes.

## Decision 2 — canonical input fail-versus-repair boundary

**Status:** approved by Edo on 2026-07-11.

- Lossless decoding/casting/column selection, chain/regime attachment, and one block-number ordering step belong only to acquisition/sealing.
- The sealed sequence must satisfy exact chain, manifest/schema/unit/regime/range, inclusive row-count, unique contiguous block-number, nondecreasing integer-second timestamp, and selected raw-domain invariants.
- Equal timestamps are valid; block number owns order.
- Selected priority-fee fields, if retained, require complete nonnegative ordered percentiles and exact spread derivation.
- Downstream compiler/features/training/replay/serving never silently sort, deduplicate, drop/fill/interpolate/impute/pad/shorten/clip or sanitize invalid facts.
- Fail with the exact invariant/origin. Recovery is reacquisition/resealing under a new content identity; any lossy/inventive transform needs a separate explicit decision.
- Later implementation deletes current timestamp-sort/keep-first-duplicate repair behavior.
- Keep the no-per-row-hash contract fixed.
- Keep numeric training cap and role cutoffs pending the orchestrator's evidence audit.

## Pending evidence — training-origin bounds

**Status:** historical planning evidence recorded on 2026-07-11. Decisions 21, 22,
and 24 supersede its candidate caps and BPO2/Giugliano/Granite planning assumptions.

- Investigate a predeclared cap around 1–2 million eligible training origins rather than automatically using all roughly 8.06 million provisional Avalanche train origins or all roughly 13.435 million modern eligible origins.
- Rows affect training time and statistical exposure, not model parameter count.
- Reserve sufficiently broad, strictly later validation and sealed testing tails before choosing the training interval.
- Ground boundaries in each chain and protocol regime and choose them without inspecting outcomes.
- Do not force equal counts across chains merely for symmetry.
- Coordinate role cutoffs with issue 48 and regime facts with issue 54. The orchestrator audit is now recorded below; wait for approved `C`, `H`, and `K` before recomputing endpoints or asking the owner to choose a cap.

### Completed bounded-period audit — evidence, not approval

- Granite remains the only defensible material Avalanche anchor: block 72,240,649 at 2025-11-19T16:00:00Z. No meaningful later C-Chain protocol checkpoint exists near +1M, +1.5M, or +2M; any cap is a predeclared ML cutoff, not a network checkpoint.
- Dataset rows affect training time and exposure, not parameter count.
- Under issue 54's provisional `H=200`, `C=600`, `K=20` assumptions only, a planning candidate uses 1.2 million Avalanche training origins at 72,241,449–73,441,448 through December 10, then 300,000 validation origins and a further 200,000 predeclared validation-audit window, leaving roughly 11.735 million later origins from December 18 through May 17.
- A two-million-origin training cap ends around December 22 and still leaves roughly 10.6 million later origins from early January. Exact endpoints must be recomputed under approved `C`, `H`, and `K`.
- Independent red-team recommendation: predeclare at most two million retained Avalanche training origins; either choose two million as a resource cap or compare nested one-million versus two-million training sets using validation only under issue 48's practical-equivalence rule. Testing must remain sealed for that choice.
- Strict post-BPO2 Ethereum has roughly 1.175 million eligible origins in total, so one million for training would starve its later tail. Post-Giugliano Polygon has roughly 1.756 million over only about 39 days. Do not force equal counts; preserve later tails first and acquire suffixes when broader final evidence is required.
- Adjacent origins overlap heavily, so row count is not an IID effective sample size. Issue 49 must separately bound examples, optimization steps, epochs, and seeds.
- A genuinely untouched final testing period likely requires a newly acquired suffix after semantics and windows freeze, especially for Polygon. Existing data remains useful for validation and historical development evidence.

## Decision 3 — whole-sample single-regime containment

**Status:** approved by Edo on 2026-07-11.

- For regime R_start...R_end, visible context C ending at h, maximum extra raw feature history H, and fixed outcome width K, require h-C+1-H >= R_start and h+K <= R_end.
- Eligible count for a positive contiguous N-row regime is N-C-H-K+1.
- Hidden warm-up, visible context, Ethereum parent-derived forming scalar, and every outcome use one regime's semantics.
- Block-number activation boundaries own containment; timestamps do not.
- A content-bound corpus may span regimes, but the compiler excludes crossing origins without rewriting, shortening, or padding.
- Every retained feature later declares its raw history depth.
- This chooses no C, H, K, feature group, date, role cutoff, or Avalanche cap.
- Role-boundary causal-history overlap remains a separate later rule; regime boundaries forbid semantic crossing.
- Keep Decisions 1 and 2 fixed.

## Decision 4 — direct block-count context semantics

**Status:** approved by Edo on 2026-07-11; numeric `C` is deferred.

- Visible context is exactly inclusive rows h-C+1...h ordered by block number.
- C is declared/persisted in the artifact and never derived from seconds, median cadence, training cap, or live observations.
- Extra feature warm-up H remains outside the visible tensor; preparation needs C+H raw rows but model receives C.
- Realized elapsed span is descriptive per chain/period, not context membership or a fixed-seconds claim.
- Timestamps may support later-approved causal features but do not select rows.
- Offline/live preparation share C and block endpoints; insufficient same-regime C+H history makes origin ineligible/not ready with no padding/shortening.
- Later implementation deletes seconds-to-median-to-clipped sequence derivation and compatibility/overflow paths.
- Exact C, shared-vs-chain-specific C, and any validation sweep remain later choices.
- Keep Decisions 1–3 and pending training-cap evidence fixed.

## Decision 5 — complete-outcome purging at role boundaries

**Status:** approved by Edo on 2026-07-11.

- At every later-role start B, retain an earlier-role origin h only when h + K < B.
- Purge equality h + K == B because the complete outcome touches the later period.
- Apply at train→validation, validation→internal-test, and internal-test→external-test boundaries.
- Final external origins also require h + K <= external_end and regime containment.
- Block number owns role membership.
- Causal past context/warm-up may overlap the role boundary.
- Add no arbitrary symmetric gap or embargo.
- This approval chooses no numeric dates, K, C, H, role sizes, or Avalanche cap.

Decision 6 below supersedes only Decision 5's four-role boundary enumeration. The
strict `h + K < B` rule itself remains approved and now applies at the two boundaries
in the three-role contract.

## Decision 6 — three-role academic split

**Status:** approved by Edo on 2026-07-11 after independent theory, code, and red-team checks found no contradiction.

- Use exactly three chronological role names: training, validation, testing. Delete the proposed internal-test role entirely; retain no optional or dormant alias or mode.
- Training alone owns gradients and every fitted or data-dependent preprocessing or target statistic.
- Validation owns every development and selection choice, including features, numeric C, scaler policy, model/HPO settings, early stopping/checkpoint, budget/cap, and any practical-equivalence comparison. It may contain multiple predeclared validation windows without creating another role.
- Testing is the sealed final thesis evaluation corpus role. It may contain multiple broad, predeclared named evaluation and reporting windows without creating another dataset role.
- Test windows and reporting are predeclared and opened only after the pipeline, features, C, scaler, HPO, checkpoint rule, cap/budget, metrics, and claims freeze. No test result may change a choice or emphasized claim.
- The baseline final artifact remains the training-fitted checkpoint selected by validation. Do not refit using validation or testing rows.
- The former mandatory later-suffix consequence is superseded by the narrow cross-ticket
  pointer below.
- Replace the former internal-test purpose with validation audits plus deterministic fixtures, invariants, and offline/live parity checks.
- Apply complete-outcome purging at training→validation and validation→testing only. Final testing origins also require h+K <= test_end and regime containment.
- Exact testing periods, named windows, and evaluator mechanics belong to the temporal-evaluation ticket. This decision infers no 300/1,200-block window or date.
- This chooses no dates, sizes, cap, features, scaler, C/H/K, epoch budget, or windows.
- Keep the no-per-row-hash contract and Decisions 1–4 fixed.

**Canonical testing-source pointer:** [Issue 48 resolution, especially sections 4 and 6](https://github.com/edoski/spice/issues/48#issuecomment-4950650999). Issue 47 adds no duplicate testing-source state or policy.

## Decision 7 — training-only fitted populations

**Status:** approved by Edo on 2026-07-12.

Decision 19 supersedes only this decision's input-scaler population and its
beginner-facing visible-context simplification. The origin-covariate, target,
class-weight, deterministic-transform, validation-policy, and provenance rules below
remain approved.

- Input scaler statistics use the union of unique physical feature rows visible in at least one retained training context; each (content-bound corpus_id, chain_id, block_number) contributes once.
- Do not flatten overlapping context tensors and count reused blocks repeatedly.
- Exclude hidden-warmup-only rows, outcome-only future rows, validation rows, and testing rows unless a physical row separately appears visibly in a retained training context.
- Origin-specific covariate state uses each retained training origin once.
- Target transforms and class weights use only the declared target elements of retained training origins, once as represented by the training loss.
- Deterministic causal transforms are not fitted state.
- Validation may select a policy, but every candidate refits from the same training population.
- Persist and freeze fitted values, population type/counts, feature order/dtype, and content-bound training provenance for validation, testing, replay, and serving.
- This chooses no scaler family, clipping/inversion, features, forming-scalar encoding, C/H/K, dates, sizes, cap, or evaluation windows.
- Beginner-facing simplification: fit the input scaler once on unique block rows actually visible in training contexts. Current effective unique-row behavior may survive, but delete the misleading multiplicity interface.

## Decision 8 — strict project-owned input z-score scaler

**Status:** approved by Edo on 2026-07-12.

Decision 19 supersedes only the first bullet's reference to Decision 7's visible-row
population. The scaler formula, precision, persistence, failure behavior, and all
prohibitions below remain approved.

- Fit an independent per-feature population mean and standard deviation (`ddof=0`) on Decision 7's unique visible training rows only.
- Calculate and persist scaler state in float64; emit float32 model inputs through identical offline and live transform code.
- Persist exact feature names/order, fitted population count and provenance, model dtype, means, and standard deviations.
- Fail clearly on a constant retained feature, empty or malformed state, wrong feature width/order, nonfinite state, nonpositive scale, or nonfinite transformed output.
- Do not silently assign scale 1, repair state, add epsilon, drop or mask a feature, broadcast vectors, or clip held-out values.
- Never update input-scaler state online. Add no scaler modes, registry, or input inverse-transform API.
- Implement the scaler with small NumPy code and remove scikit-learn plus unused sample-weight and context-multiplicity plumbing.
- This owns input scaling only. It infers no regression-target transform, inversion, loss, head, or scorer behavior; those remain with the canonical issue 23, issue 21, and issue 49 owners.

## Decision 9 — two-feature common closed-parent control

**Status:** approved by Edo on 2026-07-12.

- For every visible context row `j` through closed parent `h`, emit ordered features `log_base_fee_per_gas[j] = ln(base_fee_per_gas[j] measured numerically in native wei/gas)` and `gas_utilization[j] = gas_used[j] / gas_limit[j]`.
- Use row `j` itself with zero extra raw history (`H=0`); delete the needless current `j-1` aliases.
- Use identical same-block formulas and feature order offline and live, with a focused parity fixture.
- Corpus, chain, block, timestamp, regime, and hash identity remain metadata rather than baseline model inputs.
- Invalid raw domains fail before log or division. Decision 8 scales the two emitted features.
- This is a common observable control, not a claim that it completely represents Polygon or Avalanche fee-protocol state.
- The old 45- and 77-feature catalogs do not survive atomically. Every optional group and the Ethereum forming scalar remain separate owner choices.

## Decision 10 — ordinary per-row Ethereum exact forming-fee feature

**Status:** approved by Edo on 2026-07-12.

- Approve Option A, the ordinary per-row Ethereum feature. Reject Option B, the separate post-encoder scalar path.
- Every Ethereum row `j` constructs raw `exact_forming_base_fee_per_gas[j]` solely from row-`j` parent facts through the approved stable Python-integer recurrence.
- Emit `log_exact_forming_base_fee_per_gas` as the ordinary third sequence feature and scale it through Decision 8's row-feature path.
- Never read, shift, copy, compare, or require finalized child `j+1`. Add no forward-row dependency, verifier, mismatch state, fallback, extra audit artifact, or runtime check.
- Polygon and Avalanche omit the feature with no placeholder.
- Rely on the existing frozen [selected-modern-Ethereum protocol and corpus evidence](issue-47-chain-schema-feature-availability.md), which reports 1,175,688 matching transitions out of 1,175,688. Issue 47 adds no new proof requirement. Future formula changes are handled only as new regime decisions.
- This decision prescribes no extra dedicated tests. Later implementation follows only the smallest ordinary verification required by its owning acceptance ticket.

## Decision 11 — bounded closed-parent capacity/activity group

**Status:** approved by Edo on 2026-07-12 as one paired validation ablation, not direct baseline inclusion.

- Keep Decision 9's two-feature common closed-parent core as the control baseline.
- Decision 10's mandatory Ethereum forming-fee column remains present in both Ethereum arms; the ablation changes only the paired capacity/activity group.
- Admit one indivisible candidate group named `closed_parent_capacity_activity`: `log_gas_limit[j] = ln(gas_limit[j] measured numerically in gas)` plus `log1p_tx_count[j] = ln(1 + tx_count[j])`.
- Both columns use closed row `j`, have zero extra raw history (`H=0`), use identical offline/live formulas, and follow Decision 8's ordinary row-feature scaling. Delete the stale legacy `j-1` aliases.
- Decide keep or drop through exactly one bounded validation ablation at primary `K=5`, LSTM, one fixed seed, Ethereum, Polygon, and Avalanche, using identical eligible origins and an otherwise frozen configuration.
- Do not multiply this comparison across the ten-`K` sweep, model families, seeds, HPO, or testing.
- If the group passes the already-approved validation leanness and economic gate, freeze both columns into the established feature set for every later thesis-facing study. Otherwise drop both. The result is not a lasting mode.
- `gas_limit` on Avalanche remains the observed closed header limit, not a claim to expose complete ACP-176 fee state. `tx_count` is included closed-block activity, not mempool demand or inclusion probability.
- The canonical ablation/protocol owner records this comparison in the one complete experiment inventory. Issue 47 supplies the decision and narrow handoff only; it creates no duplicate experiment registry.

## Decision 12 — delete explicit lag and difference channels

**Status:** approved by Edo on 2026-07-12 after the stated safety condition was checked and satisfied.

- Delete `dlog_base_fee`, its six explicit lag copies, and the six explicit `gas_utilization` lag copies.
- The complete ordered raw context remains available. All 13 deleted channels are deterministic differences or shifts of that same context, so deletion removes no causal fact and introduces no future dependency or offline/live mismatch.
- Add no feature mode, validation-ablation cell, extra warm-up `H`, compatibility alias, or dedicated redundant-feature test.
- The ordered raw sequence is the single representation of this history. This decision does not choose rolling summaries, calendar/cadence, priority fee, elapsed position, numeric `C`, training cap, loss, or target behavior.

## Decision 13 — delete unstable elapsed-position input

**Status:** approved by Edo on 2026-07-12.

- Remove the frame-relative `elapsed_seconds` column, formula, scaler entry, and frame-start or deployment-origin concept.
- Keep timestamp as metadata.
- Add no compatibility alias, trend replacement, feature mode, validation cell, dedicated test, or raw-history `H`.
- Calendar and cadence features remain separate later choices.

## Decision 14 — omit closed-parent cadence input

**Status:** approved by Edo on 2026-07-12 with the stated limitation.

- Omit `seconds_since_previous_block` and any log-cadence variant from model inputs.
- Add no cadence scaler entry, `H=1` contribution, validation cell, per-chain placeholder, or Avalanche millisecond reacquisition for this purpose.
- Timestamp remains metadata for regime checks and descriptive elapsed-time reporting.
- This deliberately omits a potentially useful causal cadence signal because the selected Avalanche corpus lacks exact millisecond cadence and the bounded thesis does not justify another acquisition or ablation. It does not claim cadence is irrelevant.
- Calendar features remain a separate later choice.

## Decision 15 — delete weekday inputs and bound the UTC-hour pair

**Status:** approved by Edo on 2026-07-12.

- Delete `dow_sin` and `dow_cos` outright. Add no mode, ablation, or replacement.
- Admit `hour_sin` and `hour_cos` only as one indivisible paired validation candidate. They are dimensionless UTC-hour cyclic features derived from closed row `j`, have `H=0`, and follow Decision 8's ordinary row-feature path.
- After Decision 11's capacity/activity comparison freezes its winner, compare that frozen feature set against the same set plus both hour features.
- Use primary `K=5`, LSTM, Ethereum, Polygon, Avalanche, one fixed seed, identical validation origins, otherwise frozen configuration, and unweighted cross-entropy. The comparison has at most six decision cells or artifacts; exact control reuse is permitted only when every identity and provenance fact matches.
- Apply the approved Issue 48 validation-only leanness and economic gate. Freeze keep or drop before the separate loss-weighting ablation, representative HPO, ten-`K` sweep, and testing.
- Do not retain a permanent calendar mode or multiply the pair across other `K` values, models, seeds, HPO, or testing.
- Issue 49's canonical inventory owns the exact entry and execution order. Issue 47 records this feature decision and handoff only, not a duplicate registry.

## Decision 16 — delete binary base-fee trend

**Status:** approved by Edo on 2026-07-12.

- Delete the binary adjacent-fee recoding `base_fee_trend`, its formula, scaler entry, warm-up dependency, zero-change convention, feature name, and parity obligation.
- Add no feature mode, validation cell, `H`, compatibility alias, zero-change branch, or dedicated redundant-feature test.
- The complete ordered `log_base_fee_per_gas` context remains, so deletion removes no causal fact and introduces no future dependency or offline/live mismatch.

## Decision 17 — delete base-fee and utilization rolling inputs

**Status:** approved by Edo on 2026-07-12 for the current contract.

- Remove all 21 legacy base-fee and gas-utilization rolling columns. Do not admit the proposed 12-column replacement.
- Remove their formulas, names, scaler entries, window, minimum, and `ddof` conventions, hidden warm-up, compatibility aliases, feature modes, parity obligations, and ablation cells.
- Set `H=0` for every currently approved or admitted non-priority input.
- Visible `C` becomes the sole model-history length and must later be chosen to expose the intended history directly.
- This decision does not resolve the separate priority-fee research brief or a future transaction-tip heuristic.

### Deferred nonbinding note — paper-relative rolling comparison

After the already-approved bounded ablations, rolling summaries may be revisited against the paper only if a concrete material gap or thesis-comparison need earns a fresh explicit owner decision. This thought is not in the canonical experiment inventory, is not approved to run, and creates no automatic future ablation.

## Decision 18 — one shared cross-chain context length

**Status:** approved by Edo on 2026-07-12; Decision 19 later fixes numeric `C=200` for the primary/default/serving contract.

- Use an identical block-count context length `C` in every Ethereum, Polygon, and Avalanche artifact and in offline/live preparation.
- Add no chain-specific override, seconds conversion, median derivation, fallback, clipping, compatibility path, or context-length Cartesian sweep.
- Realized wall-clock spans remain descriptive per chain and period.
- Context rows affect sequence compute, memory, and eligible-origin counts, not LSTM parameter count.

## Decision 19 — primary C=200 and research-only context sensitivity

**Status:** approved by Edo on 2026-07-12 after bounded statistical, code-seam, and red-team checks.

### Primary context

- Fix `C=200` as the primary, default, headline, and only serving context before any context-study outcome.
- Persist and use `C=200` identically offline/live. Research contexts create no serving mode, dynamic selection, fallback, or compatibility path.

### Research-only context study

- Run exactly `C in {50, 100, 200, 500, 1000}` at `K=5`, LSTM, Ethereum, Polygon, Avalanche, and one fixed seed: 15 independently trained artifacts.
- Freeze features, loss, model, optimizer and effective-batch policy, example/update budget, checkpoint rule, and any approved representative HPO contract. Add no per-`C` tuning.
- Within each already-frozen chronological role/range and regime, each `C` uses its own maximal naturally eligible origins with complete `K=5` outcomes and the approved purging. Larger `C` begins only as late as its own history requirement demands; all contexts otherwise use the same role boundaries and full available range.
- Add no common-`C_max` intersection, paired-origin or suffix machinery, overlap-only secondary view, or pairing claim. Publish exact origin endpoints and counts for every `(chain, role, C)`.
- Differences from `C=200` are descriptive and may include the disclosed boundary-population difference. Do not claim that they isolate a causal context-length effect, identify an optimal `C`, establish seed robustness, or compare equal wall-clock histories.
- Report only the already-required predictive and economic results, descriptive comparison with `C=200`, exact per-`C` origin counts/endpoints, and realized wall-clock context-span summaries by chain and period.
- Add no training-duration, peak-memory, inference-latency/throughput, profiling, or resource-reporting surface.

### One central training-only input scaler

- Supersede Decision 7's input-scaler population. Fit one input-feature scaler after role assignment and cap resolution for each exact `(content-bound corpus, chain, selected regime, frozen feature contract, frozen capped training feature/parent-support interval)`.
- The population is every unique canonical emitted feature row in that interval through the frozen last allowed training parent, once. It is independent of `C`, `K`, model family, seed, and HPO.
- Include declared early training support rows inside the frozen interval even when a shorter context does not use them. Exclude any outcome-only suffix after the last training parent, validation rows, testing rows, and rows structurally outside the selected regime/support.
- If a cap begins as an origin count, resolve it once to exact frozen physical block endpoints before scaler fitting. Never recompute the scaler interval separately by `C`, `K`, model, or trial.
- A selected in-range row with an invalid domain, malformed or nonfinite emitted feature, duplicate identity, or other canonical violation fails closed with its row identity. Never silently exclude, repair, clip, or impute it.
- Reuse the one frozen state across every compatible context, `K`, model, and HPO artifact. Separate chains, corpora, regimes, feature names/order/units/formulas, training ranges, or caps require separate state.
- Persist the same immutable values, feature order, population count/endpoints, content-bound provenance, dtype, and identity fingerprint in every compatible self-contained artifact. Fit through one direct preprocessing function; add no runtime lookup, generic registry, adapter family, scaler mode, or repeated artifact/trial fitting.
- Decision 8 otherwise remains unchanged: per-feature population mean/std with `ddof=0`, float64 fitted state, float32 model inputs, strict failures, no held-out fit or clipping, no online update, no inverse input interface, and no scikit-learn or multiplicity plumbing.
- Decision 7's origin-specific covariate population and target/class-weight populations remain unchanged. Target scaling is separately owned by Issue 58 per `(chain, K)` and is never centralized into the input scaler.

### Funding and ownership

- Sum `C` is 1,850 per chain, close to the ten-`K` sweep's `10 * 200 = 2,000` first-order context-block workload. Treat this as a second substantial thesis study despite its 15 artifacts.
- Issue 49 must predeclare and fund the complete 15-artifact training/validation/testing study before any grid outcome. If unaffordable, return to the owner and revise scope before training; never inspect results and truncate contexts or chains.
- Run only after the bounded feature and loss decisions, model/checkpoint/budget contract, role ranges, metrics, claims, and any representative HPO choice freeze. Testing reports the predeclared sensitivity and cannot select or change `C=200`.
- Put the study in one dedicated downstream evidence task and one canonical Issue 49 inventory entry. Do not put it in Issue 50's decision-ablation matrix or multiply it by `K`, model family, seed, feature, loss, or HPO choices.

## Decision 20 — omit priority-fee model inputs

**Status:** approved by Edo on 2026-07-12 for the current Issue 47 contract.

- Omit every priority-fee model input. Add no priority-fee acquisition or validation ablation inside Issue 47.
- Remove all 32 legacy priority-fee feature outputs and their formulas, prerequisites, scaler entries, lags, rolls, compatibility aliases, feature modes, parity obligations, and experiment cells.
- Do not fill nulls, infer a `Q4`, add mempool, proposer, MEV, bundle, or full-transaction machinery, claim inclusion probability, or create a cross-chain placeholder.
- Keep existing numeric corpora reusable. Unselected optional null columns require no republishing.
- Keep `H=0` for the current model-input contract and add no priority-feature entry to Issue 49's canonical inventory.
- Priority fees are deferred, not dismissed. The linked downstream owner handles that investigation; Issue 47 does not decide or duplicate it.
- Issue 48's base-fee-only headline remains unchanged.

## Decision 21 — two-million-origin Avalanche primary training cap

**Status:** approved by Edo on 2026-07-12 with no cap ablation.

- Freeze the post-Granite Avalanche primary `C=200` training population at exactly 2,000,000 contiguous eligible parent origins: `h=72,240,848...74,240,847` inclusive. The last parent timestamp is `2025-12-22T20:09:49Z`.
- Freeze the central input-scaler feature/parent-support interval at blocks `72,240,649...74,240,847`: 2,000,199 unique physical rows, each fitted once under Decision 19.
- Preserve complete training outcomes for the approved `K_max=200` sweep. A later validation origin therefore cannot start before block `74,241,048`; exact validation/testing boundaries remain separately owned.
- This is a predeclared ML/resource cutoff, not an Avalanche protocol checkpoint or performance optimum. Add no one-million, 1.2-million, or two-million comparison, adaptive extension, outcome-selected cutoff, or cap mode.
- Decision 19's natural context geometry uses the same frozen physical range. Its training-origin counts are `2,000,150` for `C=50`, `2,000,100` for `C=100`, `2,000,000` for `C=200`, `1,999,700` for `C=500`, and `1,999,200` for `C=1000`; do not recompute the cap per `C`.
- Ethereum, Polygon, and Avalanche may use different training population sizes because artifacts and results remain chain-specific. Report exact counts and never equalize them destructively.
- Issue 49 separately owns example, effective-batch, update, epoch, and seed budgets. The eligible-row cap changes data exposure and scaler provenance, not LSTM parameter count.
- This decision does not alter testing semantics.

## Decision 22 — no additional Ethereum or Polygon training-origin cap

**Status:** approved by Edo on 2026-07-12.

- Add no numeric training-origin cap for Ethereum or Polygon beyond each chain's later-frozen chronological training range.
- Within that range, retain every naturally eligible primary `C=200` training parent origin that satisfies `H=0`, selected-regime containment, complete outcome support, and the approved role-boundary purging.
- Add no cap ablation, destructive cross-chain count equalization, adaptive cutoff, or per-artifact cap mode. Report each chain's exact training endpoints and origin count separately.
- Decision 19's central input scaler uses the corresponding chain's own frozen feature contract and training feature/parent-support interval. Research contexts use their natural eligible counts inside that same physical range.
- Issue 49 still owns example, effective-batch, update, epoch, and seed budgets; a larger eligible population changes possible data exposure and compute, not model parameter count.
- This decision chooses no role dates or boundaries, validation/testing sizes, testing windows, or amendment to Issue 48's testing-range contract.

## Decision 23 — exact per-feature causal availability contract

**Status:** approved by Edo on 2026-07-12 after consistency verification against Decisions 8–20.

For every visible sequence row `j <= h`, where `h` is the frozen closed parent:

| Inclusion | Feature | Exact formula and raw unit | `available_at` | Chains | Raw history |
|---|---|---|---|---|---:|
| mandatory common core | `log_base_fee_per_gas` | `ln(base_fee_per_gas[j] measured numerically in native wei/gas)` | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |
| mandatory common core | `gas_utilization` | `gas_used[j] / gas_limit[j]`, dimensionless ratio | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |
| mandatory chain feature | `log_exact_forming_base_fee_per_gas` | `ln(exact_forming_base_fee_per_gas[j] measured numerically in native wei/gas)`, constructed only from row-`j` parent facts | `close(j)` | Ethereum only | `H=0` |
| indivisible validation candidate | `log_gas_limit` | `ln(gas_limit[j] measured numerically in gas)` | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |
| indivisible validation candidate | `log1p_tx_count` | `ln(1 + tx_count[j])`, transaction count | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |
| indivisible validation candidate | `hour_sin` | `sin(2*pi*hour[j]/24)`, where `hour[j] = floor(timestamp[j]/3600) mod 24`; dimensionless | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |
| indivisible validation candidate | `hour_cos` | `cos(2*pi*hour[j]/24)` with the same closed-row UTC hour; dimensionless | `close(j)` | Ethereum, Polygon, Avalanche | `H=0` |

- Compute every listed value from the canonical closed offline row or frozen closed-block RPC facts through the same direct formula. At decision time every row `j <= h` is already available; no feature reads a target or forward row.
- Use stable order: the two common-core columns; the Ethereum forming-fee column when present; the capacity/activity pair when retained; then the UTC-hour pair when retained.
- Decisions 11 and 15 alone determine whether their indivisible candidate pairs survive validation. A rejected pair disappears permanently. Add no placeholder, null column, lasting feature mode, or chain adapter.
- Scale every retained model column through Decisions 8 and 19. Persist exact names, order, formulas, units, dtype, scaler identity, and chain-specific presence in the artifact.
- Keep block number, timestamp, chain identity, regime identity, corpus identity, and hashes as metadata rather than model columns. Timestamp supplies the approved hour formulas and descriptive reporting only.
- Use one smallest ordinary offline/live parity fixture through the shared feature function. Add no availability framework, adapter hierarchy, per-feature fixture family, or edge-case test matrix.
- Every currently approved or admitted model input has `H=0`; visible `C` is the complete model-history requirement. Invalid selected raw domains still fail closed under Decisions 2 and 8.

## Decision 24 — exact selected retained-feature regime anchors

**Status:** approved by Edo on 2026-07-12 under the corrected execution-base-fee and retained-feature reasoning.

- Ethereum starts at Fusaka/Osaka local block `23,935,694`, `2025-12-03T21:49:11Z`.
- Polygon starts at Lisovo block `83,756,500`, `2026-03-04T14:03:51Z`.
- Avalanche starts at Granite block `72,240,649`, `2025-11-19T16:00:00Z`, preserving Decision 21.
- Ethereum BPO1/BPO2 are blob-parameter provenance facts, not containment cuts: the current contract retains no blob input or blob-cost claim. Pectra is too early because the resulting range would cross Fusaka's material transaction-gas, execution-gas-pricing, block-size, and default gas-capacity changes affecting retained/admitted fields and future execution-fee outcomes.
- Polygon Lisovo changes the child-base-fee rule from one deterministic recurrence to producer choice inside a parent-relative bound. Giugliano's early propagation and completed-child, self-reported parameter metadata are unused provenance facts, not containment cuts for the approved closed-row feature and conditional-inclusion claims.
- Granite changes Avalanche protocol time and the ACP-176 gas-capacity/fee process, so it remains material even though cadence is omitted as a model input.
- Apply Decision 3 with these exact block-number starts. For each currently sealed corpus, available coverage ends at its last sealed row unless an earlier material boundary is found. Every later suffix must re-evaluate intervening protocol changes before sealing.
- Record excluded fork activations as provenance. Add no automatic fork inference, regime adapter, compatibility mode, or outcome-selected boundary.
- This decision chooses no training, validation, or testing boundary; no testing size; no acquisition range; no feature-ablation outcome; and no Issue 60 priority-fee requirement. Decisions 21 and 22's chain-specific cap policy remains unchanged.

## Coordination fog — deferred Ethereum and Polygon suffix acquisition

**Status:** owner-approved sequencing intent recorded on 2026-07-12; this is neither a regime-anchor decision nor acquisition authorization.

- Current sealed endpoints are Ethereum block `25,355,071` at `2026-06-19T23:59:59Z`, Polygon block `87,024,566` at `2026-05-17T15:44:59Z`, and Avalanche block `85,676,147` at `2026-05-17T15:44:59Z`.
- Plan one later content-bound suffix acquisition for Ethereum and Polygon only after the selected regime anchors, chronological role and testing ranges, the canonical maximal-testing-range affordability rule, and Issue 60's priority-fee field requirements all freeze.
- Waiting allows one acquisition to use the final exact ranges, fields, units, provenance, continuity checks, and sealing identity instead of repeating acquisition as downstream requirements change.
- Preserve the existing corpora. A suffix is a new content-bound acquisition/sealing result, not an in-place extension or rewrite under the same identity.
- Avalanche needs no suffix absent new evidence. Its abundant approved post-Granite coverage does not justify acquisition by symmetry.
- Ownership recommendation only: the temporal-evaluation owner supplies final range needs; [Research the minimum defensible priority-fee extension](https://github.com/edoski/spice/issues/60) supplies any enrichment fields; [Prototype exact-root acquisition with one retry owner](https://github.com/edoski/spice/issues/27) owns acquisition/sealing mechanics. The orchestrator may graduate one execution task after those inputs freeze. Issue 47 creates no task and acquires nothing.

## Cross-ticket pointer — deferred priority-fee research

Decision 20 owns only omission from the current model-input contract. [Research the
minimum defensible priority-fee extension](https://github.com/edoski/spice/issues/60)
owns the deferred investigation. It is a map child newly unblocked by Issue 47's
closure and still blocks the later baseline/ablation-protocol approval. Issue 47 does
not duplicate or answer its
acquisition, feature, transaction-policy, MEV/mempool, or post-hoc accounting scope.

## Cross-ticket references — auxiliary fee-regression head

These are pointers to canonical tracker records, not Issue 47 decisions:

- [Head existence — issue 23 comment](https://github.com/edoski/spice/issues/23#issuecomment-4950344149)
- [Loss/scorer consequence — issue 21 comment](https://github.com/edoski/spice/issues/21#issuecomment-4950344146)
- [Ablation-protocol consequence — issue 49 comment](https://github.com/edoski/spice/issues/49#issuecomment-4950344147)

Issue 47 does not duplicate or reopen those owners. It records only downstream causal
preprocessing semantics explicitly approved in this work-through. Its map pointer was
added only after the owning ticket closed.

## Standing owner constraint — negligible deterministic edge cases

**Status:** owner-wide constraint recorded on 2026-07-12 for the final Issue 47 contract.

- When an edge case has essentially zero measured recurrence and ordinary deterministic library semantics already define it, add no feature mode, metric, state, branch, fallback, audit, dedicated test matrix, or ablation. Add machinery only when measured frequency or impact is material, or the case threatens causal correctness or data integrity.
- Target-fee labels use the ordinary deterministic earliest `argmin`. Ties are possible, but receive no tie-special preprocessing or validation.
- Selecting a later equal minimum remains an ordinary miss against the earliest action label. Its zero economic regret remains owned by the approved temporal utility and evaluation semantics.
- This simplifies diagnostics only. It does not change the approved earliest-minimum label or utility.

## Final compact-contract approval and closure

**Status:** explicitly approved by Edo and completed on 2026-07-12.

- [Single Issue 47 resolution](https://github.com/edoski/spice/issues/47#issuecomment-4952817627) records the complete approved contract.
- [Choose causal preprocessing, split, feature, and context semantics](https://github.com/edoski/spice/issues/47) is closed as completed; no other ticket was closed.
- The [Wayfinder map](https://github.com/edoski/spice/issues/1) contains exactly one title-linked Decisions-so-far pointer added after closure.
- The deferred Ethereum/Polygon suffix remains coordination only. Closure creates no acquisition or task.
