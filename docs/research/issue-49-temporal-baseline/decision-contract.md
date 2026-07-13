# Issue 49 temporal baseline and ablation decision contract

Status: final complete contract explicitly approved by Edo on 2026-07-13 for
[Approve the temporal baseline and ablation protocol](https://github.com/edoski/spice/issues/49).
This is planning and decision evidence only. It authorizes no acquisition, corpus or
storage mutation, training, evaluation, remote job, production/configuration/test change,
or edit to a sibling issue.

The issue's fifteen approved decision comments remain the canonical decision ledger:
[1](https://github.com/edoski/spice/issues/49#issuecomment-4952952058),
[2](https://github.com/edoski/spice/issues/49#issuecomment-4952958514),
[3](https://github.com/edoski/spice/issues/49#issuecomment-4955480011),
[4](https://github.com/edoski/spice/issues/49#issuecomment-4955550419),
[5](https://github.com/edoski/spice/issues/49#issuecomment-4955629663),
[6](https://github.com/edoski/spice/issues/49#issuecomment-4955723336),
[7](https://github.com/edoski/spice/issues/49#issuecomment-4955739793),
[8](https://github.com/edoski/spice/issues/49#issuecomment-4955769544),
[9](https://github.com/edoski/spice/issues/49#issuecomment-4955864269),
[10](https://github.com/edoski/spice/issues/49#issuecomment-4955864416),
[10 clarification](https://github.com/edoski/spice/issues/49#issuecomment-4955867602),
[11](https://github.com/edoski/spice/issues/49#issuecomment-4956001997),
[12](https://github.com/edoski/spice/issues/49#issuecomment-4956002091),
[13](https://github.com/edoski/spice/issues/49#issuecomment-4960383023),
[14](https://github.com/edoski/spice/issues/49#issuecomment-4960533838), and
[15](https://github.com/edoski/spice/issues/49#issuecomment-4960611678).
This document incorporates the final dependent-audit corrections that Edo approved with
the whole contract.

## Corpus and chronological roles

Use exactly training, validation, and testing. Training alone fits weights and every
data-dependent statistic. Validation may choose features, loss, restored checkpoint,
early stopping, and HPO candidates. Testing only reports the already-frozen protocol and
cannot change a configuration, range, metric, or claim. Add no internal-test role, refit,
rolling split, cross-chain count equalization, or data-selected endpoint.

Acquire one content-bound Ethereum suffix and one content-bound Polygon suffix when the
Issue-27 acquisition path is ready during July 2026. Do not wait for July 31. Do not
extend Avalanche and do not add priority-fee fields. At each acquisition start, resolve
one current finalized anchor, freeze the complete inclusive definition, and never chase a
newer head during interruption or resume. Continuity, intervening-protocol, schema,
finality, or later role-sufficiency failure publishes nothing and returns to Edo.

The two Decision-13 block numbers are suffix-payload and validation starts, not corpus
first blocks. Each Train or Tune source has one `corpus_id`, so Ethereum and Polygon each
need one new full role-covering corpus:

| Chain | Regime | `regime.start_block` and `first_block` | Freshly validated imported prefix | Newly acquired payload suffix | `last_block` |
| --- | --- | ---: | ---: | ---: | --- |
| Ethereum | Fusaka | 23,935,694 | 23,935,694…25,355,071 | starts 25,355,072 | one runtime-frozen finalized anchor |
| Polygon | Lisovo | 83,756,500 | 83,756,500…87,024,566 | starts 87,024,567 | one runtime-frozen finalized anchor |

Only missing payload rows are the suffix. Existing hashless prefix bytes are not trusted
or blindly copied: Issue 27 imports them into a fresh full-definition stage and performs
one fresh exact source read and hash/link validation per row. Any mismatch requires
reacquisition.

The frozen endpoint block belongs to `CorpusDefinition`. Its timestamp is only the
canonical timestamp already present in the hashed endpoint payload row and a report/role
fact. Add no duplicate endpoint-timestamp definition, manifest, identity, resume, status,
or lifecycle field. It can affect `corpus_id` only through the canonical payload bytes.
Resume remains bound to the complete frozen definition. This is the approved narrow
interpretation of Decision 13's earlier broader end-block-and-timestamp wording.

Primary training origins are:

- Ethereum `23,935,893…25,354,871`;
- Polygon `83,756,699…87,024,366`;
- Avalanche `72,240,848…74,240,847`.

Validation starts at Ethereum `25,355,072`, Polygon `87,024,567`, and Avalanche
`74,241,048`. Each chain has one contiguous seven-day validation interval. After the
corpora freeze, testing starts at the first canonical block at or after
`validation_start_timestamp + 604800` seconds. Apply the approved `K_max=200`
complete-outcome purge at both transitions. Equality at the next role start is purged.

Primary `C=200` ladder, HPO, and final-K work use the same frozen per-chain origin sets
with complete support through `K_max=200`. The context study uses natural per-C
eligibility inside the same frozen role boundaries. Testing uses every eligible origin
from its frozen start through the corpus endpoint with complete `K_max=200` support.
Require at least seven elapsed days of testing data per chain; otherwise stop before
training and return to Edo.

The one-week validation period is a deliberate data-constrained thesis allocation that
covers one weekly/hour cycle. It is not IID, statistically optimal, or universally
sufficient.

## Features, context, targets, and loss

Preserve Issue 47's exact regimes, eligibility, purge, feature formulas/order/units,
training-only input scaler, and failure rules. The common core is
`log_base_fee_per_gas` and `gas_utilization`; Ethereum also has the exact parent-derived
`log_exact_forming_base_fee_per_gas`. The capacity/activity candidate is the indivisible
pair `log_gas_limit` plus `log1p_tx_count`. The later UTC candidate is the indivisible
pair `hour_sin` plus `hour_cos`. Every candidate has `H=0`.

Primary, default, headline, and only-serving context is `C=200`, fixed before outcomes.
Avalanche has exactly 2,000,000 primary training origins. Ethereum and Polygon have no
extra numeric training-origin cap beyond the frozen chronological ranges. Do not sample,
truncate, equalize, or create a common-C intersection.

Retain the auxiliary regression head and the exact Issue-58 target coordinate: the
positive within-K hindsight minimum, natural log, strict training-only per-chain/K
population z-score, scalar standardized output, and affine log-view report state. Use
Issue 21's exact classification/regression reducers, predictive scorer, and temporal
economic accounting. Complete-validation `total_loss` alone selects checkpoints, early
stopping, and HPO. Post-fit predictive and economic diagnostics do not affect training
selection.

## Finite non-Cartesian validation ladder

Use only LSTM artifacts. `immediate_k0_reference` is a zero-artifact, zero-evaluation-cell
accounting comparator. Remove majority/persistence, linear/logistic, MLP,
small-versus-current LSTM, Transformer/hybrid, and one-million-versus-two-million cells
from the current inventory.

Transformer, Transformer–LSTM hybrid, and possibly one small bounded model-size question
may be reconsidered only after the clean-break implementation is stable. They create no
current artifact, mode, configuration seam, or execution obligation.

Run the ladder at `K=5`, `C=200`, three chains, seed 2026, and the fixed neutral control:

1. capacity/activity: train six artifacts, compare absence versus presence of the pair,
   and freeze one global winner;
2. UTC hour: reuse the three exact selected controls, train three additions with the UTC
   pair, and freeze one global winner;
3. CE weighting: reuse the three exact unweighted selected-feature controls, train three
   corrected-weighted additions, and freeze one global winner.

Each stage uses post-fit validation EvaluateRequests. Compare chains separately on
identical eligible origins; never pool or average chains. The lean/default candidate wins
one global feature or loss contract only when every valid chain satisfies both:

- `captured_opportunity_lean >= captured_opportunity_complex - 0.05`, where captured
  opportunity is `sum(S)/sum(G)` and `sum(G)>0`;
- `harmful_action_rate_lean <= harmful_action_rate_complex`.

For feature stages, lean omits the candidate pair. For CE, unweighted is lean/default.
If all cells are valid but any chain misses either gate, the complex candidate wins
globally. If any required cell is failed, nonfinite, provenance-invalid, or undefined,
the stage stops and no winner freezes. Add no per-chain feature/loss hybrid. Testing never
selects.

This five-point rule is a finite-validation owner tolerance, not a statistical
equivalence test.

## Seed, neutral control, exposure, and stopping

The ML training seed is integer `2026`. Reset it independently before every model
construction, dropout or other stochastic object, and shuffled loader for every
Issue-49 chain, K, feature, loss, and context artifact. Use no additional training seeds
and make no seed-robustness claim. Issue 29 owns the HPO candidate-list or sampler seed.

The neutral control is
`LSTM(projection=256, hidden=256, layers=2, head_hidden=256, dropout=0.2)` with AdamW
`lr=3e-4`, `weight_decay=1e-4`, gradient clipping `1.0`, and no scheduler. These are
moderate control values, not an optimality, paper-authority, or permanent-setting claim.
Use them only for feature, loss, and descriptive context comparisons.

One completed epoch is one seed-shuffled pass over every retained unique training origin
exactly once, including the final short batch. For `N` origins, one epoch has `N`
optimization examples. Do not sample, cycle, truncate, equal-count, or normalize updates
across chains or context cells. Feature/loss pairs use identical origins; chains stay
separate.

All 24 neutral-control artifacts use physical batch 64, accumulation 1, and effective
batch 64. One epoch has `ceil(N/64)` minibatches and optimizer updates. For artifact `i`
with `E_i` completed epochs, report unique origins, `E_i*N_i` optimization examples,
`E_i*ceil(N_i/64)` minibatches/updates, and `E_i` separately.

For all 24 neutral-control artifacts and all 30 final-K artifacts:

- `max_epochs=36`;
- validate after every completed epoch;
- stop after patience 8 consecutive non-improving completed validations;
- semantic `min_delta=0.0`: only strictly lower complete-validation `total_loss`
  improves; equality does not;
- retain and restore the earliest strict best; no minimum-epoch floor;
- if epoch 1 stays best, stop after epoch 9;
- a cap hit is a completed fit: restore the earliest best among epochs 1…36, report the
  cap, and do not extend after inspecting outcomes;
- any required nonfinite training or complete-validation loss fails the fit under Issue
  16.

Prefer the selected host's verified native zero-delta/early-stopping/checkpoint mechanics
and add no project tolerance field or comparison adapter when native behavior exactly
matches.

Create no project retry policy, counter, quota, state machine, or automatic loop. An
externally interrupted non-HPO run may relaunch the identical frozen definition through
the eventual host's native resume path only from the latest completed-validation
boundary. Discard partial-epoch work. If there is no completed validation, restart from
seed 2026. Resume cannot repair nonfinite loss, bad data/provenance/invariants,
code/config errors, deterministic OOM, or semantic failure. HPO recovery remains Issue
29 ownership.

## HPO, context sensitivity, and final K

After features and loss freeze, run exactly one bounded `K=5` LSTM Tune study per chain.
Issue 29 owns engine, search space, candidate seed, finite trial budget, pruning, HPO
stopping/batch, recovery, selection, and promotion. Freeze each selected per-chain model,
optimizer, physical/effective batch, accumulation, and native tail-update policy for all
ten K values. Run no feature, loss, context, or per-K HPO.

The context matrix `C={50,100,200,500,1000}` varies a model input hyperparameter in a
broad technical sense but is not HPO or selection. It is a `K=5`, three-chain,
single-seed descriptive sensitivity study. Reuse the three exact selected-feature/loss
neutral `C=200` artifacts and train 12 additions with natural per-C origins. Report all
15 cells, exact counts/endpoints, realized context spans, and descriptive deltas. It
cannot select or retune `C=200`.

The final horizon grid is
`K={2,3,4,5,10,15,30,50,100,200}` across three chains: 30 independently trained
artifacts. Use `C=200`, seed 2026, the frozen per-chain HPO configuration, and the same
per-chain origins complete through `K_max=200`. Use no per-K HPO, stopping variation,
sampling, update normalization, or best-K selection. `K=5` stays primary/default/headline.
Serving may expose only separately trained `K={2,3,4,5}` artifacts. A K=5 HPO result
fills the final artifact slot only when Issue 29 proves exact promotion identity;
otherwise retrain it under the final-K contract.

The final-K grid has at most 1,080 completed artifact-epochs. Final-K minibatches and
optimizer updates derive from the exact per-chain batch/accumulation/tail policy frozen
by Issue 29 and must be reported separately.

## Artifact inventory, requests, and execution order

There are exactly 24 unique neutral-control artifacts:

- capacity/activity: six;
- UTC: three reused controls plus three additions, nine cumulative;
- CE: three reused controls plus three additions, 12 cumulative;
- context: three reused `C=200` controls plus 12 additions, 24 cumulative.

Reuse requires exact identity of corpus, roles/origins, K, C, features, loss,
model/optimizer, seed, training budget, and selected checkpoint. HPO candidates are
outside this count. With 30 final-K artifacts, the fixed durable non-HPO inventory is 54.

The canonical ready topology has ten explicit deterministic lists:

1. capacity/activity Train: 6;
2. capacity/activity validation Evaluate: 6;
3. UTC Train additions: 3;
4. UTC validation Evaluate additions: 3, reusing three exact selected control
   evaluations from list 2;
5. CE Train additions: 3;
6. CE validation Evaluate additions: 3, reusing three exact unweighted
   selected-feature evaluations from lists 2 or 4;
7. per-chain K=5 Tune: 3;
8. context Train additions: 12;
9. final-K Train: 30;
10. sealed-test Evaluate: 45.

Lists 8 and 9 are parallel sibling branches after HPO, not serialized by numbering.
They must both complete and freeze before list 10 begins.

Totals are 54 Train, 3 Tune, and 57 Evaluate: 114 exact requests. The 57 evaluations
are 12 ladder validation records plus 45 sealed-test records. Train owns only
complete-validation `total_loss`, checkpointing, and restoration; the range-driven
Evaluate workflow alone produces the captured-opportunity and harmful-action evidence
needed by the ladder. The final all-or-nothing TSV contains only the ordered 45 sealed
test records.

Issue 50 executes lists 1…6: 12 ladder Train artifacts plus 12 explicit post-fit
validation evaluations. It applies the frozen rule; it does not redefine the protocol.
Issue 29 executes list 7. Dedicated downstream tasks execute context, final K, and sealed
testing. Core request/workflow/report functions remain count-agnostic and accept any
valid exact request or list length. Add no benchmark scheduler, plan/DAG/array language,
registry, watcher, callback, matching layer, or benchmark resume state.

## Sealed testing and claims

After both branches freeze every protocol, configuration, checkpoint, range, and claim,
open exhaustive testing for exactly 15 context artifacts and 30 final-K artifacts. Do
not test rejected ladder alternatives or unpromoted HPO candidates. The selected neutral
`C=200` artifacts are tested only as predeclared context cells and cannot reopen prior
choices. `immediate_k0_reference` creates no artifact or evaluation cell.

Testing scores every eligible finite chain-native block opportunity once in each maximal
frozen post-validation range. It may not change scope, `C=200`, the `K=5` headline,
features, loss, HPO, frozen exposure/stopping, ranges, metrics, or emphasized claims. No partial matrix,
curve, or official test claim is valid.

Claims are limited to one finite chronological validation window, one frozen exhaustive
finite testing census, and one ML seed. Make no IID, population, confidence-interval,
statistical-equivalence, causal, future-period, or seed-robustness claim. Keep chains,
ranges, lifecycle roles, seeds, and K-specific descriptive problems separate. Add no
cross-chain pooling, chance correction, strict-monotonicity claim, context optimality, or
best-K claim. Results concern chain-native target base-fee opportunities, not random
users, equal seconds, transaction inclusion, execution, full transaction cost, or generic
profit.

## No affordability protocol

Decision 15 deletes affordability planning without shrinking the scientific contract.
Persist no runtime, throughput, memory, quota, deadline, GPU-hour, money, projection,
preflight, threshold, estimate, budget state, configuration, report, or lifecycle. Exact
origin, example, batch, update, artifact, request, and evaluation counts remain required
scientific accounting.

Supersede these exact stale clauses:

- Decision 12: delete “fully funded,” the metrics-blind affordability gate, “if
  affordable,” and both projection/unaffordable stop bullets.
- Issue 47: delete pre-score affordability ownership, complete-grid funding/return
  wording, and maximal-range affordability dependency. Preserve the full grid/counts and
  ban on resource-reporting surfaces.
- Issue 48: preserve exact origin/batch counting; delete the contiguous-prefix preflight,
  throughput/memory/resource persistence, matrix projection, projected-budget/cap gate,
  and affordability ownership. Preserve maximal exhaustive testing and no partial claim.
- Issue 36: delete only the affordability-gate phrase and narrow “Issue 49 gates” to
  scientific prerequisites. Independently replace seven lists/102 requests with the ten
  lists/114 requests above and add the three validation Evaluate lists. Preserve its
  count-agnostic exact-ID flow, zero benchmark dependency edges, ordinary evaluation jobs,
  and all-or-nothing writer.
- Wayfinder map: its maximum-time/compute rule remains for research/prototypes but not
  outcome-bearing Issue-49 execution; “fixed task and experiment budget” becomes “fixed
  task and experiment inventory”; its Issue-36 pointer becomes ten lists/114 requests.
  Issue 29's declared finite trial budget remains HPO search scope, not runtime/GPU/money
  planning.

Begin a protocol stage when its scientific and implementation prerequisites are ready.
If execution proves too slow or costly, an operator may pause/cancel and return to Edo.
Any scope change is a fresh explicit amendment before continuing. Add no automatic
truncation, subsampling, fallback, adaptive matrix reduction, or partial-completion claim.

## Execution gate and ownership

No outcome-bearing acquisition, training, HPO, context, K, or testing run begins until
every blocking clean-break decision/specification and implementation ticket for that
stage is completed, integrated, reviewed, and verified, with required corpora,
artifacts, and contracts frozen. Do not run against stale or half-migrated semantics.

This gate does not wait for unrelated or explicitly deferred work. Priority-fee
follow-up, Transformer/hybrid, uncertainty, future decision-making, naming, and other
nonblocking future work do not delay the base thesis pipeline unless the native graph
later makes one a blocker.

Issue 49 owns this finite protocol, roles, origin geometry, inventory, reuse, ordering,
selection gates, seed, neutral training budget, final-K stopping, claim boundary, and no-
affordability rule. It does not own Issue 27 acquisition/finality/staging mechanics,
Issue 29 HPO mechanics, Issue 36 runner implementation, Issue 48 scorer/test mechanics,
Issue 50 execution, production code/config/tests, or any actual data/model/job run.

Sibling Issues 36, 47, and 48 retain their historical resolution comments. Their stale
phrases above are explicit downstream handoffs; this ticket does not edit or comment on
those issues.

## Immutable supporting evidence

The dependent audit reused these accepted repository assets at full commit
`cf63a91e2693c7778c3b03b6a1b48f5827a4baf4`:

- [Issue 27 exact-definition acquisition contract](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-27/README.md)
  and [dependent audit](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-27/dependent-completeness-audit.md);
- [Issue 47 preprocessing and split decisions](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-47/issue-47-owner-decisions.md);
- [Issue 48 temporal-evaluation contract](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-48-temporal-evaluation/decision-contract.md);
- [Issue 21 predictive/loss contract](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-21-predictive-diagnostics/decision-contract.md);
- [Issue 58 target-coordinate contract](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-58-target-coordinate/decision-contract.md);
- [Issue 18 runner audit](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-18-benchmark-runner/audit-and-decision-evidence.md);
- [Issue 61 HPO comparison](https://github.com/edoski/spice/blob/cf63a91e2693c7778c3b03b6a1b48f5827a4baf4/docs/research/issue-61-hpo-framework-comparison/README.md).

The audit found no unresolved consequential Issue-49 choice. Edo explicitly approved
this corrected whole contract. Normal Issue-49 research publication, one Resolution,
close-only-Issue-49, the approved map pointer/text corrections, and verification are
authorized. Nothing in this document authorizes production or sibling-issue mutation.
