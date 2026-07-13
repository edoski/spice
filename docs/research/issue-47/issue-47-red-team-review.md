# Issue 47 leakage and readability red-team

Status: independent planning review. No owner choice is made here. Production,
corpora, artifacts, configuration, ADRs, normative docs, and remote state were not
changed.

## Verdict

The proposed clean direction is causal and substantially smaller than the current
pipeline: closed-parent context through `h`, targets `h+1...h+K`, direct block-count
context, complete-outcome purging, train-only fitted statistics, a small common
closed-parent core, and one Ethereum-only exact forming-fee scalar.

It is not yet a complete contract. Parent-hash scope is now approved; explicit
answers remain for context length and feature history, forming-scalar
encoding/placement, retained feature groups, and scaler ownership. Several evidence
documents also need the exact corrections below.

## Blocking corrections

1. **Use one ordered cutoff definition.** If block `B` is the first origin owned by
   the later role, an earlier origin is retained only when `h + K < B`. This assigns
   outcome block `B` to the later period and matches the executable fixture. The
   theory report's phrase "immediately before the first later decision" can instead
   imply that close(`B`) is already available. Define the cutoff as the start of the
   later block-owned period, before block `B` may influence fitting, to remove that
   ambiguity. Equal Unix timestamps must not decide ownership.

2. **Bound the last role by its full outcome window.** Testing origins require
   `h + K <= test_end_block` and `<= regime_end_block`; checking only corpus end or
   origin membership is insufficient. The owner deleted the internal-test role.
   Current HPO's per-trial test metrics must therefore be removed; testing stays
   sealed until the procedure and claims freeze.

3. **Fix the eligibility off by one.** Let `C` be inclusive context rows and `H` the
   maximum extra raw-row history behind the first context feature. The exact gates
   are:

   ```text
   h - C + 1 - H >= regime_start
   h + K <= regime_end
   ```

   A contiguous `N`-row regime therefore has `N - C - H - K + 1` eligible origins,
   when positive. Issue 54's `N-W-C-K` formula and `first + W + C` start discard one
   valid origin under this inclusive geometry. Use `C` for context and reserve `K`
   for the already-approved action width; the theory report reuses `K` for both.

4. **Keep offline corpus identity separate from live decision identity.** The owner
   approved `(content-bound corpus_id, chain_id, block_number)` for offline origins,
   with no mandatory row hash or full sidecar. Acquisition must still validate every
   returned `parentHash` against the preceding block hash before sealing the corpus,
   then retain compact boundary/acquisition evidence. Live preparation separately
   persists `(h, hash(h)), k, b` and binds all parent facts and the Ethereum
   recurrence to the same frozen response.

5. **Make the forming scalar an exact emitted feature, not an idea.** The schema
   report alternates between raw wei/gas and a possible logged encoding. The final
   table must name the emitted representation and unit. It must also say where the
   sample-level scalar enters the sequence model: repeated static covariate, separate
   decision covariate, or another exact interface. This affects scaling. Row-feature
   statistics use unique train-covered physical rows; a sample-specific scalar must
   be fitted over retained training origins. Prove exact integer parent-to-child fee
   parity before any float/log encoding, then prove identical offline/live encoding.
   Do not create a generic chain adapter or placeholders for Polygon/Avalanche.

6. **The evidence table is not yet literally per-feature.** Rows such as
   `lag1...lag6`, combined priority transforms, and "may encode its log" compress
   multiple emitted values or alternatives. After group selection, enumerate every
   retained emitted feature separately with exact name, formula, numeric unit,
   `available_at`, raw-history depth, endpoint inclusion, `ddof`, supported regimes,
   offline source, live source, and parity fixture. Summarize rejected groups outside
   that acceptance table.

## Corpus and regime attack

The modeling seam should fail on wrong chain/network, duplicate or noncontiguous
heights, decreasing timestamps, null selected fields, nonpositive selected fee/limit,
`gas_used` outside `[0, gas_limit]`, negative counts, invalid priority ordering or
spread, missing regime identity, and invalid hashes. Equal timestamps are valid.
Avalanche has 65,715 equal-second transitions in the selected post-Granite range;
timestamp is not an origin key.

One explicit lossless sort while assembling a partitioned corpus is normalization,
not repair. Record it at import. Downstream feature/model code must not sort again,
keep an arbitrary duplicate, interpolate, fill, pad, shorten, or clip invalid facts.
Current `_prepare_blocks` violates that rule by sorting and silently keeping one
duplicate. Current log helpers also turn invalid nonpositive values into plausible
finite features.

Whole-sample regime containment includes hidden feature history, not only visible
context and targets. With a `C`-row context and a right-aligned unshifted 200-row
roll, `H=199`, so disclosed raw history is `C+199` rows. Role boundaries may share
causal past context; regime boundaries may not under the approved single-regime
evidence rule.

## Feature and live-parity attack

Call the proposed two-feature baseline a **common closed-parent core**, not a complete
protocol core. `ln(base_fee[h])` and `gas_used[h]/gas_limit[h]` are available on all
three chains, but Avalanche's ratio is not ACP-176 fee state and Polygon's child fee
is producer-selectable inside its rule. Ethereum's approved exact forming scalar is
the only retained child-fee fact.

The current 45 features do not survive as a catalog. Under context ending at `h`,
the shifted gas, limit, transaction, utilization, and priority features read `h-1`
and are needlessly stale. Lags and overlapping 10/25/50/100/200 rolls duplicate a
sequence model's history and use inconsistent standard-deviation conventions. They
remain validation-only ablations, not presumed deletions if material signal appears.

The current 77-feature priority catalog is infeasible in the selected modern data:
priority coverage is zero for Ethereum BPO2, post-Giugliano Polygon, and post-Granite
Avalanche. Historical Ethereum priority data ends before BPO2. Do not fill nulls or
silently move regimes; inclusion would require separately approved acquisition and a
new corpus identity.

Calendar semantics need one name. Parent-timestamp hour/day features are causal and
reproducible but are not actual decision-time calendar values. Offline `tau` has no
recorded local wall-clock instant. Keep them as optional **parent calendar** features
or omit them; do not call them decision calendar. Previous closed-block cadence is
causal. On Avalanche it is integer-second-quantized, so zero seconds is valid and the
feature cannot support millisecond-exact cadence claims.

Delete the current `elapsed_seconds = timestamp - first supplied frame timestamp`
candidate unless a stable origin is approved. Offline training, external preparation,
and live fetch windows use different frame starts. The paper instead says blocks since
dataset start, so it does not validate current code. A sequence-relative elapsed
feature would duplicate cumulative cadence; a regime-relative feature would encode
experiment position. Either needs a separate ablation and exact live origin.

No target-row timestamp, cadence, calendar, elapsed fact, realized fee, gas use,
transaction count, or priority statistic may enter ordinary features. Ethereum's
forming fee is the sole approved exception because it is computed from `h`, not read
from finalized `h+1`.

## Split fixture result and exact improvements

`uv run python docs/research/issue_47_complete_outcome_split_fixture.py` passes. It
keeps origins `(5,6)`, `(9,10)`, and `(13...18)` for training, validation, and
testing; purges the last two earlier-role origins at both role cutoffs; proves causal
past overlap; and fits row statistics only on visible training-context rows `1...6`.

The production acceptance fixture should keep this strict inequality and add only:

- explicit regime start/end and external outcome end;
- `earliest_feature_dependency`, not only a warmup arithmetic check;
- train-label/sample IDs used for class weights and any target scaler;
- an assertion that no retained earlier outcome intersects blocks owned by the next
  role;
- one same-second pair to prove block/hash ordering, not timestamps, owns samples.

Do not add a generic gap or purge causal past overlap.

## Scaling, clipping, and inversion

Per-feature standard scaling with population variance and training-only fitting is a
defensible lean default. An exactly constant retained feature must fail by name and
return to the explicit feature-contract decision: centered training inputs give its
model weight no training signal, so a later change would activate an unlearned weight.
Do not silently assign scale `1`, drop it, add epsilon, or invent a near-constant
threshold. Persist feature order, means, scales, dtype, training identity, and the
approved population semantics. Validate finite equal-length vectors, strictly
positive representable scales, and exact feature width before transform.

Current `ScalerStats` fails that contract. A one-element scaler broadcasts across all
features; NaN means produce NaN outputs; zero or negative scales are silently replaced
with `1`. Held-out feature values are not clipped. Preserve no-clipping by default:
out-of-range values are shift evidence and possible signal. Any future clipping rule
must be fitted on training only and report saturation.

An input inverse-transform interface has no consumer and fails the deletion test; do
not add one. The canonical head-existence decision is recorded in
[issue 23](https://github.com/edoski/spice/issues/23#issuecomment-4950344149), with
loss/scorer ownership in
[issue 21](https://github.com/edoski/spice/issues/21#issuecomment-4950344146) and the
ablation consequence in
[issue 49](https://github.com/edoski/spice/issues/49#issuecomment-4950344147). Issue 47
does not duplicate those choices. If the owned target uses scaling, its separate
training-only inverse belongs to that contract, not the input scaler. The deletion
test supports a small project-owned NumPy input-scaler fit: scikit-learn is used
nowhere else in production, while SPICE already owns persistence and transform
behavior. Add no scaler registry or alternative mode.

## Paper and deletion test

The professor paper does not settle these choices. Page 8 states non-overlapping
anchor intervals but does not specify complete-outcome purging. It uses
`600 / nominal block time`, while current code uses a training-prefix median plus
64...4096 clipping; Ethereum's nominal 50 rows are forced to 64. Its feature table is
narrower, describes elapsed time in blocks rather than current seconds, and gives no
point-in-time availability table. Issue 46's fixed-block action is an intentional
extension, so paper fidelity cannot restore seconds-derived action or context widths.

The beginner-readable implementation has one deep sample-preparation interface that
validates regime-contained causal support, compiles `context_end=h` and exactly `K`
outcomes, assigns purged roles, and fits frozen training statistics. Historical and
live right-edge preparation remain distinct implementations consuming the same
feature/action contracts. Keep `CompiledProblemStore`-like aligned geometry if it
enforces those invariants.

Delete median/min/max sequence conversion, seconds-window overflow semantics,
downstream deduplication and clipping repairs, shifted closed-row aliases, unavailable
priority catalogs, unstable elapsed position, and one-option registries where no real
alternative remains. Do not add an availability framework, regime adapter hierarchy,
generic fee adapter, compatibility reader, or migration shim. A short static feature
table plus direct formulas and focused parity tests gives more locality.

## Owner-gated choices still required

- exact `C` and whether it is shared across chains or selected per-chain on validation;
- the common closed-parent core and each optional cadence/calendar, lag, rolling, and
  elapsed group; priority is unavailable under current evidence;
- exact Ethereum forming-scalar encoding, placement, and scaling population;
- final retained-feature table and exact `C+H` raw-history disclosure.

These choices must be approved one at a time, then recapped together. Nothing in this
review approves closing issue 47.

## Evidence reviewed

- [Current pipeline audit](issue-47-current-pipeline-audit.md)
- [Causal preprocessing and split theory](issue-47-causal-preprocessing-split-theory.md)
- [Chain schema and feature availability](issue-47-chain-schema-feature-availability.md)
- [Issue 45 parity prototype](../current-block-action-cross-layer-parity-prototype.md)
- [Issue 54 modern-regime coverage](../modern-regime-coverage-and-evidence-periods.md)
- [Temporal preprocessing audit](../issue-1/temporal-preprocessing-theory-audit.md)
- [Executable split fixture](../issue_47_complete_outcome_split_fixture.py)
- `ICDCS_2026.pdf`, especially pages 5, 7, and 8
