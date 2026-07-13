# Ethereum current-row causality and lean retention options

**Status:** supporting research for the forming-block decision. On 2026-07-11,
Edo selected candidate C: closed-parent context plus one exact Ethereum
forming-fee feature. The durable decision and remaining boundaries are recorded
in [the cross-layer parity prototype](current-block-action-cross-layer-parity-prototype.md).
This report does not authorize production implementation or reinterpret an old
artifact.

## Answer in one paragraph

Including Ethereum's exact forming-block base fee is not, by itself, target
leakage. Under EIP-1559, a chosen closed parent `h` fixes the base fee of
forming child `t=h+1`; the current SPICE Ethereum corpus reproduces that
recurrence for all 2,923,987 adjacent block pairs. Most other current features
are either parent facts deliberately shifted by one row or trailing
transformations. However,
the complete pipeline cannot be called leakage-free: the internal
train/validation/test split does not purge forward outcome horizons, the
current-row timestamp contract is implicit and conditions on a non-empty slot,
Poisson replay loses the actual request time, and serving feeds a confirmed old
row while reporting different target blocks. The accurate verdict is therefore
**causal Ethereum feature values under a specific slot-opening interpretation,
but unresolved sample/action semantics and a small confirmed split leak**.

## Three questions that must not be collapsed

Let `h` be the latest closed execution block, `t` the block being built in the
current beacon slot, and `tau` the user's actual decision/submission time.

1. **Row-level leakage:** does an input contain a value that could not be known
   or computed at `tau`?
2. **Decision-time parity:** does offline preprocessing construct exactly the
   same values that live inference constructs at `tau`?
3. **Actionability:** can a transaction submitted at `tau` still be considered
   for `t`?

Ethereum's base fee passes question 1. The current code does not yet prove
questions 2 and 3. A valid feature does not guarantee an actionable policy.

## Why the Ethereum forming fee is causal

[EIP-1559](https://eips.ethereum.org/EIPS/eip-1559#specification) validates a
child's base fee from only the parent's base fee, gas used, and gas target,
where the target is the parent gas limit divided by the elasticity multiplier.
The specification fixes the integer rounding rule and minimum increase. The
child producer cannot choose another valid execution base fee.

For the post-London range in SPICE, the recurrence is:

```text
target = parent.gas_limit // 2

if parent.gas_used == target:
    child.base_fee = parent.base_fee
elif parent.gas_used > target:
    delta = max(
        parent.base_fee * (parent.gas_used - target) // target // 8,
        1,
    )
    child.base_fee = parent.base_fee + delta
else:
    delta = parent.base_fee * (target - parent.gas_used) // target // 8
    child.base_fee = parent.base_fee - delta
```

The one-off London activation rule is irrelevant to the present corpus, which
begins years later. A read-only replay over
`outputs/corpora/ethereum/cor_7bea5a071afaf090c05a` checked every consecutive
pair from block 22,431,084 through 25,355,071: **zero of 2,923,987 pairs
disagreed**. This is stronger evidence for this corpus than assuming a later
fork retained the rule merely because its documentation did not mention a
change.

Implementation warning: the multiplication can exceed signed 64-bit range at
real fee levels even when the final answer fits. A pure constructor should use
Python integers or a proven client implementation, not an unchecked NumPy
`int64` expression.

The fee is exact **conditional on the parent head**. Ethereum's validator
specification has the proposer choose its parent from fork choice at the start
of the slot and permits proposer-head behavior
([block proposal](https://ethereum.github.io/consensus-specs/phase0/validator/#block-proposal)).
An offline canonical row knows retrospectively which parent won. A public user
has a local head and cannot guarantee that the proposer builds on that same
head. This is a head-selection/reorg risk, not freedom to choose a different
fee for one fixed parent. A deployable contract must record the decision-time
parent hash and call the derived fee exact only relative to that hash.

Ethereum's execution timestamp is also protocol-bound to the beacon slot. The
stable consensus specification rejects an execution payload whose timestamp
does not equal
[`compute_time_at_slot(state, block.slot)`](https://ethereum.github.io/consensus-specs/fulu/p2p-interface/#modified-beacon_block).
Ethereum uses scheduled slots and permits skipped slots; an empty slot has no
execution block. The corpus confirms this shape: all timestamps share one
residue modulo 12, while adjacent deltas are 12 seconds for 2,906,387 pairs,
24 seconds for 17,427, 36 seconds for 162, 48 seconds for 8, and 60 seconds for
3. See Ethereum's first-party explanation of
[slots and occasionally empty slots](https://ethereum.org/developers/docs/blocks/#block-time).

Consequently, `timestamp[t]` is knowable at the start of *a specified current
slot*. It is not derivable from parent `h` alone because one cannot know which
future slot will be the next non-empty one. Offline rows are causal only under
the explicit interpretation, “make the decision at the opening of the slot in
which historical block `t` was proposed.” That conditioning omits decisions in
empty slots and must be named in evaluation.

## What SPICE currently gives the model

The compiler sets the anchor row as candidate zero
([`observed_time_window.py`](../../src/spice/temporal/compilers/observed_time_window.py#L346-L379)),
and sequence tensorization includes the anchor itself
([`sequence_inputs.py`](../../src/spice/modeling/representations/sequence_inputs.py#L202-L216)).
For an offline sample anchored at `t`, the final sequence row and candidate zero
are therefore the same physical corpus row.

That overlap is not automatically leakage. The task is “choose the minimum-fee
action among `t, t+1, ...`,” not “predict the unknown fee of `t`.” A currently
known alternative may legitimately be compared with future alternatives. The
auxiliary minimum-fee target is likewise partly known whenever `t` is the
minimum; this makes that auxiliary regression easier, but does not violate the
decision-time information set if the current fee is genuinely available.

### Feature-by-feature availability

| Current output group | Value at final row `t` | Ethereum verdict at slot opening | Qualification |
|---|---|---|---|
| `log_base_fee_per_gas` | Finalized `base_fee[t]` is read directly | Causal in value | Must be constructed from `h`, not learned later from finalized `t`; current code does not enforce the provenance ([`_base_fee.py`](../../src/spice/features/sets/core_fee_dynamics/_base_fee.py#L16-L39)). |
| Fee deltas, trend, rolling mean/std/min | Trailing transforms through exact fee `t` | Causal | Every member is a deterministic trailing transform once the derived fee is available; none reads `t+1`. |
| `prev_gas_used`, `prev_gas_limit`, utilization, `prev_tx_count` and their lags/rolls | Source columns are shifted, so row `t` uses finalized `h` | Causal | This is the intentional one-row lag ([`_block_facts.py`](../../src/spice/features/sets/core_fee_dynamics/_block_facts.py#L27-L83)). |
| Priority-fee percentiles/spread and their transforms | Also shifted, so row `t` uses transactions in `h` | Causal after `h` closes | Exact live parity still requires the enrichment to be fetched/computed before the action cutoff; the row formula itself is safe ([`_priority_fee.py`](../../src/spice/features/sets/core_fee_dynamics/_priority_fee.py#L35-L65)). |
| `seconds_since_previous_block` | Uses realized `timestamp[t] - timestamp[h]` | Conditional | Exact if `tau` is tied to the known current slot. It is not a parent-only fact and it silently conditions on that slot producing `t`. |
| hour/day sine and cosine | Use realized `timestamp[t]` | Conditional but cheaply reconstructible | Use the current slot timestamp or decision clock, never wait for the child header ([`_time.py`](../../src/spice/features/sets/core_fee_dynamics/_time.py#L57-L94)). |
| Optional `elapsed_seconds` | `timestamp[t] - corpus_start` | Known, not target leakage | It is a corpus-position/non-stationarity proxy and may generalize poorly; retain only on ablation evidence. |

The safe catalog's 45 outputs therefore contain no identified `gas_used[t]`,
`tx_count[t]`, or priority-fee outcome from `t`. Its questionable values are
not hidden transaction outcomes; they are the unproved provenance of the
forming fee and slot-time row. For Ethereum, both can be reconstructed
causally. That statement does **not** extend to modern Polygon or Avalanche.

### Other preprocessing facts

- Rolling features are trailing; they do not use future rows.
- Sequence length is calibrated from training timestamps, and the scaler is
  fitted on rows covered by training contexts
  ([`fixed_sequence_temporal.py`](../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L244-L287)).
- The nominal 12-second compiler avoids whole-table cadence fitting. The
  optional `recent_median` compiler resolves its interval from the complete
  feature table before splitting, so artifacts using that option have a
  separate unsupervised preprocessing leak.

## Confirmed problems outside the feature values

### Forward labels cross internal role boundaries

SPICE makes adjacent chronological fractions but does not remove samples whose
candidate outcomes extend beyond the next role's first anchor
([`fixed_sequence_temporal.py`](../../src/spice/modeling/dataset_builders/fixed_sequence_temporal.py#L204-L233)).
The prior full preprocessing audit reproduced three Ethereum training samples
whose outcomes enter validation and three validation samples whose outcomes
enter test. The percentage is tiny, but it is actual target leakage. The lean
fix is to purge only earlier-role samples whose real candidate/outcome end
crosses the boundary; shared backward context is causal and should remain.

### Replay does not preserve the decision instant

Poisson replay maps each continuous arrival to the latest sample timestamp and
then retains only the sample position
([`poisson_replay.py`](../../src/spice/evaluation/poisson_replay.py#L54-L105)).
For an arrival several seconds after block timestamp `t`, it may reuse the
slot-opening sample even though `t` has already been built. It cannot test the
forming-block cutoff, and measuring the 36-second deadline from `timestamp[t]`
is not necessarily measuring it from request time `tau`.

### Serving is not the trained Ethereum task

Serving fetches `latest - confirmation_depth`
([`live_blocks.py`](../../src/spice/serving/live_blocks.py#L51-L65)), feeds that
closed row as the final model input, and maps class `k` to
`observed + k + 1`
([`inference.py`](../../src/spice/serving/inference.py#L63-L108)). Offline
training instead feeds the virtual/open row and maps `k` to that row plus `k`.
At the default depth of two, the first two serving targets are already closed.
This is a decision-contract defect, not evidence that the Ethereum forming fee
itself leaks.

### Eligibility remains weaker than inclusion

Knowing `base_fee[t]` determines the protocol minimum burned fee, not whether a
new public transaction reaches the producer in time or is selected. Its fee cap
must cover the base fee; nonce, balance, propagation, priority fee, capacity,
and proposer/builder policy still matter. EIP-1559's
[transaction validity and effective-priority rules](https://eips.ethereum.org/EIPS/eip-1559#specification)
show why exact base fee knowledge is necessary but insufficient. SPICE can
claim an immediate attempt or eligibility under stated conditions, never
guaranteed same-block inclusion.

## Lean design candidates

| Candidate | Information retained | Code/design cost | Existing Ethereum artifacts | Cross-chain meaning |
|---|---|---|---|---|
| **A. Explicit Ethereum virtual forming row** | Numerically preserves the current fee, slot time, fee transforms, and shifted parent facts | One pure EIP-1559 function, one slot-clock row constructor, and offline/live parity tests; replay/action cutoff still needs repair | In principle reusable if the constructed row is proven numerically identical; final reported evidence still needs the split/evaluation defects addressed | Exact only for proved regimes; not one universal information set |
| **B. Uniform closed-parent baseline** | Only facts through `h`; model predicts all candidate fees | Smallest universal geometry; direct closed facts replace confusing lags | New feature matrix, scaler, fit, and evaluation | Clean apples-to-apples baseline for every chain |
| **C. Closed parent plus one exact derived forming-fee feature** | Retains Ethereum's valuable `base_fee[t]` while context/candidates remain clearly separated | One named pure feature such as `exact_forming_base_fee`; no virtual child gas/transaction placeholders | Requires retraining, but avoids making the network learn a known protocol equation | Uniform base plus a clearly labeled Ethereum enhancement |
| **D. Universal chain-estimator/virtual-header framework** | Attempts to fill analogous values on every chain | Fork adapters, estimates, acquisition state, missingness, and parity rules | New artifacts | Values would still have different exact/estimated meanings; reject unless experiments show material value |

Candidate A is less complex than the earlier discussion implied. For Ethereum,
the existing finalized row can act as an offline oracle for values that a very
small live constructor can reproduce. It is a defensible performance-preserving
route if the thesis explicitly scopes that information contract to Ethereum.
It does not solve Polygon/Avalanche by analogy.

Candidate C is the deepest lean module if a clean sample geometry is more
important than artifact compatibility. The interface can be a pure
`ethereum_forming_base_fee(parent)` calculation used by both preprocessing and
live inference. Keep the seam concrete: with only one exact implementation, a
generic `ChainFeeAdapter` would be hypothetical. The temporal compiler should
own the separate `context_end=h` and `candidate_start=t`; callers should not
repeat offset arithmetic.

The useful information is not necessarily lost under B or C. Once context ends
at `h`, the last row can expose `base_fee[h]`, `gas_used[h]`, and `gas_limit[h]`
directly. These are the complete EIP-1559 inputs. A neural network could learn
an approximation; candidate C supplies the exact result so it does not have to.

## Post-selection validation

The route is selected, but its performance cost and surviving feature groups
still need falsification. Run one small paired Ethereum comparison after fixing
the split and decision fixture:

1. Freeze identical forecast origins, outcome rows, purged roles, model
   configuration, and seeds.
2. Compare the uniform closed-parent feature set with the same set plus exactly
   one derived forming-fee feature.
3. Add the reconstructed current virtual row as a parity control. First prove
   its entire final feature vector equals the historical row for Ethereum.
4. Report action economics, harmful delays, class metrics, and the performance
   difference with a predeclared practical-equivalence margin. Do not rerun HPO
   for every cell.
5. If the exact scalar fails the predeclared value/cost gate, return that
   evidence to Edo rather than silently switching routes. If only the full
   virtual row helps, identify which additional causal group—slot time or
   fee-derived rolling transforms—caused the difference; retaining any such
   group requires separate approval.

For cross-chain claims, always report the uniform baseline. A separate
Ethereum-enhanced result is scientifically useful, but its advantage must be
described as an advantage of exact protocol information, not as evidence that
Ethereum is intrinsically easier or that another chain's model is worse.

## Sources and local evidence

- [EIP-1559 specification](https://eips.ethereum.org/EIPS/eip-1559#specification)
- [Ethereum consensus Fulu payload timestamp validation](https://ethereum.github.io/consensus-specs/fulu/p2p-interface/#modified-beacon_block)
- [Ethereum.org block slots and empty-slot explanation](https://ethereum.org/developers/docs/blocks/#block-time)
- [`core_fee_dynamics` configured outputs](../../src/spice/conf/features/core_fee_dynamics.yaml)
- [Temporal preprocessing theory audit](issue-1/temporal-preprocessing-theory-audit.md)
- [Temporal chain fee-protocol audit](issue-1/temporal-chain-fee-protocol-audit.md)
- [Current-block action parity prototype](current-block-action-cross-layer-parity-prototype.md)
