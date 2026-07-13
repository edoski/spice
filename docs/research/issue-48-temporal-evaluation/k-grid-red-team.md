# Fixed-`K` grid compute and statistics red-team

Status: research input with the corrected owner-approved outcome recorded in
[`decision-contract.md`](decision-contract.md). It selects no dates, numeric seed value,
compute budget, HPO policy, or secondary reporting view.

## Corrected approved route

Use exactly this 10-horizon grid:

```text
K = {2,3,4,5,10,15,30,50,100,200}
```

`K` counts available actions. A fixed-`K` model has actions `k=0...K-1` mapped to
targets `h+1...h+K`. Thus `K=2` is already the smallest learned decision: broadcast now
for `h+1`, or wait one block and broadcast for `h+2`. There is no experimental `K=1`
condition. Immediate `k=0` remains the comparator inside every K condition; a synthetic
zero-valued `K=1` plot point is outside this decision unless separately approved later.

Make LSTM the only mandatory dense family. For Ethereum, Polygon, and Avalanche,
independently train one horizon-specific LSTM at every K, using the same K within a
cross-chain condition. Predeclare `K=5` as the primary/default/headline research,
serving, and mobile contract. Serving/mobile also offers `K=2,3,4` as secondary/demo
choices through their separately trained artifacts. No `K>5` artifact is served.

This is bounded but materially denser than the earlier four-point proposal. The
`2...5` prefix resolves the served near-immediate choices one added action at a time,
while the predeclared wider tail spans much larger block-opportunity sets without trying
all 200 integer values. `K=200` means 200 chain-native block opportunities. It is not an equal
number of seconds across chains, an inclusion deadline, or evidence of actual execution.

## Exact workload and seed meaning

The mandatory matrix contains:

```text
10 K conditions * 3 chains * 1 ML training seed = 30 trained artifacts
```

An ML training seed is a pseudorandom seed controlling model initialization, dropout,
and batch order. It is not a blockchain, network, or chain seed. The initial sweep uses
exactly one fixed, predeclared seed; issue 49 owns its numeric value. This yields one
detailed curve conditional on one fitted run. It does not estimate robustness to neural-
network randomness and must not show seed-based intervals or make multi-seed claims.

Complete all 30 cells; do not drop expensive horizons, chains, or failures after
inspecting outcomes. A fixed infrastructure retry reruns the same cell. A numerical/model
failure is reported and is not replaced with a favorable seed. If issue 49 cannot fund
the complete matrix, it must reopen the resource choice before the sweep and before
testing, not truncate the curve while it runs. Resource authorization may assume no
accelerator speedup until that speedup and executor are approved and proved.

Extra-seed work is deferred. It requires a new owner decision and separately named
robustness protocol; it may not selectively rerun interesting K/chain cells from these
testing outcomes or retroactively relabel this curve as confirmatory multi-seed evidence.
A later all-cell or fixed-subset seed study needs a fresh resource/evidence contract. If
it changes claims after testing, preserve the spent-test/fresh-suffix rule.

## Independent training, fixed configuration

Each `(chain, K)` cell gets its own independently initialized and trained LSTM and
its own K-wide output head. A `K=200` artifact masked to smaller actions is not a
substitute. K changes the target set, class distribution, class weighting, loss,
representation learned during fitting, and output-head width. The historical standard
sweeps used distinct horizon-specific train jobs too
([sweep config](../../../src/spice/conf/benchmark/delay_degradation_sweep.yaml),
[alignment audit](../issue-1/temporal-paper-alignment-audit.md#paper-to-code-alignment-map)).
Their old seconds geometry, Poisson replay, selected period, and generic metric label do
not transfer to the clean fixed-block contract.

Freeze one approved LSTM architecture/configuration under the later family protocol.
Across K, keep features, context, role ranges, optimizer, fitting budget, checkpoint and
early-stopping rule, and every hyperparameter fixed except dimensions inherently required
by K. Early stopping may choose a different epoch under the same frozen rule. Report
parameter count because the output-head width changes.

Do not run HPO separately at every K. That would multiply the matrix by the trial count
and change the question from fixed-method horizon response to separately optimized
performance at each horizon. Exact HPO eligibility remains a later issue-29/issue-49
HITL decision. HPO only for `K=5` or other finalists is a plausible later candidate, not
an approval in issue 48 and not part of this sweep.

## Pairing and testing safeguards

Within each chain, use the common origin population eligible under `K_max=200` for every
K in training, validation, and testing:

```text
O_common = intersection[K in grid] O_K = O_200.
```

Every origin must satisfy issue-47 history, feature, regime, role, and purge rules and
have the complete target span through `h+200`. Exact endpoints remain dependent on issue
47. Pair by `(content_bound_corpus_id, chain_id, block_number)`, never timestamp. Preserve
same-second Avalanche blocks. Use the same feature/context definitions, metric
definitions, one fixed ML seed, and compute/stopping rule across K. Do not equalize counts
across chains; report each chain separately.

Approved Decision 1 remains unchanged. Testing is sealed, strictly later, and exhaustive:
score every common eligible origin exactly once in every predeclared named range, with
equal block-opportunity weight. No Poisson arrivals, replay repetitions, random starts,
wall-clock weighting, or Monte Carlo intervals return through the K sweep.

For each K, report the later-approved exact reducers for:

```text
model saving versus immediate = B_h - R_h(K)
hindsight opportunity         = B_h - O_h(K)
oracle gap / regret           = R_h(K) - O_h(K)
```

where `O_h(K)` is the hindsight minimum over `h+1...h+K`. Report the approved captured-
opportunity and action diagnostics beside parameter count and realized `h -> h+K`
elapsed time by chain/regime. Hindsight opportunity can only stay equal or grow as K
grows, so a rising saving curve alone does not prove improved forecasting. Larger K also
creates more action classes. Never call target opportunity generic profit, transaction
inclusion, or actual execution.

Testing cannot select a visually best K. `K=5` remains primary regardless of the curve.
Any later replacement needs a validation-only rule fixed before opening a fresh sealed
test. Serving/mobile maps its discrete `K in {2,3,4,5}` choice to the matching
chain-by-K artifact before inference and persists K, artifact identity, `(h, hash(h))`,
action, and intended target. It never converts seconds to blocks, masks a larger model,
or serves `K>5`. Use an explicit mapping, not a plugin/registry or research-sweep UI.

Other model families are deferred. Extending this same dense grid to another
surviving family requires a later explicit owner decision after measured LSTM cost; it
cannot be triggered by favorable LSTM results. Build no all-family sweep controller or
serving machinery now.

## Ownership

- **Issue 48** freezes the 10 K estimands, LSTM-only mandatory scope, one-seed descriptive
  boundary, `K=5` primary/default/headline status, the four served block-horizon choices,
  common-pairing interpretation, exhaustive testing, and the ban on test-time K
  selection.
- **Issue 49** freezes common-origin construction, the fixed LSTM configurations, the one
  numeric ML seed value, examples/steps/epochs, compute and retry budgets, and stopping
  rules.
- **Issue 29/49 HITL** later decides whether any finalist HPO earns its cost. It does not
  retune every horizon cell.
- **Issue 50** runs only its approved structural-ablation matrix. It is not multiplied by
  the dense K grid.
- A dedicated downstream Wayfinder task should execute the approved 30-cell
  LSTM horizon matrix after the required configuration and resource rules freeze. It
  uses the executor explicitly approved by the accelerator-placement route at execution
  time: ordinary main if acceleration is rejected or not yet approved, or the later
  reconstructed, parity-proved, materially faster executor only if issues 55, 56, 40,
  and 57 approve it. Never use the current stale `codex/fast-ab-training` branch or its
  obsolete configurations.
- If an execution-only branch wins, pin both semantic-main and fast-execution commits,
  use only a temporary checkout/worktree, transfer complete hashed artifacts, and prove
  that main code independently loads and evaluates them. If lean main integration wins,
  use that single main path. Do not maintain two production paths or let executor choice
  change model semantics or configuration.

This decision does not approve exact dates, role sizes, numeric seed value, compute
budget, HPO, metric denominators, secondary time/strata views, or any `K>5` serving
option.
