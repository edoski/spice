# Issue 49 temporal baseline and ablation decision contract

Status: amended final complete contract explicitly approved by Edo on 2026-07-14 for
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
the original whole contract. Edo's later paper-alignment review explicitly replaces the
LSTM-only scope with the bounded three-family amendment below. Historical decision comments
and the sole Resolution remain immutable evidence; this clean replacement is authoritative
where it expressly supersedes them.

## Corpus and chronological roles

Use exactly training, validation, and testing. Training alone fits weights and every
data-dependent statistic. Validation may choose features, loss, restored checkpoint,
early stopping, one global architecture family, and HPO candidates. Testing only reports
the already-frozen protocol and cannot change a configuration, range, metric, or claim.
Add no internal-test role, refit, rolling split, cross-chain count equalization, or
data-selected endpoint.

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

`immediate_k0_reference` remains a zero-artifact, zero-evaluation-cell accounting
comparator. Remove majority/persistence, linear/logistic, MLP, small-versus-current LSTM,
one-million-versus-two-million, and every unapproved model-zoo cell. Retain exactly three
concrete architecture families: LSTM, Transformer, and Transformer–LSTM. Do not add a
registry, plugin, adapter, generic family seam, or outcome-responsive family.

Run the feature/loss ladder at `K=5`, `C=200`, three chains, seed 2026, and the fixed LSTM
control. LSTM is the predeclared screening reference for these structural comparisons; it
is not the predetermined final/default architecture family:

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

After features and loss freeze, compare the three fixed architecture controls at the same
`K=5`, `C=200`, seed, selected feature/loss recipe, per-chain origins, optimizer/exposure,
and validation window. Reuse the three exact selected LSTM artifacts and validation
evaluations. Train and evaluate six additions: Transformer and Transformer–LSTM on each
chain. All nine records must be complete, finite, provenance-valid, defined, and have
`sum(G)>0` before selection; any invalid cell stops the stage and freezes no family.

Predeclare the family priority `LSTM -> Transformer -> Transformer–LSTM`. This is a
protocol preference, not a parameter-count or intrinsic-quality claim. Define `passes(A,
B)` when every chain separately satisfies:

- `captured_opportunity_A >= captured_opportunity_B - 0.05`;
- `harmful_action_rate_A <= harmful_action_rate_B`.

Select LSTM only if it passes both Transformer and Transformer–LSTM. Otherwise select
Transformer only if it passes Transformer–LSTM. Otherwise select Transformer–LSTM. Exact
equality passes. Use no pooled/averaged chain score, ranks, `total_loss` tie-break,
auxiliary-scalar criterion, per-chain family mix, backtracking, or testing result. The
selected architecture family is global across chains; later HPO configurations remain
per-chain. Testing never reopens the winner.

## Seed, fixed controls, exposure, and stopping

The ML training seed is integer `2026`. Reset it independently before every model
construction, dropout or other stochastic object, and shuffled loader for every
Issue-49 chain, K, feature, loss, architecture-family, HPO fit, and context artifact. Use
no additional training seeds and make no seed-robustness claim. Issue 29 owns the HPO
candidate-list or sampler seed.

Use these exact architecture controls:

- `LSTM(projection=256, hidden=256, layers=2, head_hidden=256, dropout=0.2)`;
- `Transformer(model_width=256, attention_heads=4, transformer_layers=4,
  feedforward_width=512, head_hidden=256, dropout=0.2)`;
- `TransformerLSTM(model_width=256, attention_heads=4, transformer_layers=4,
  feedforward_width=512, lstm_hidden=256, lstm_layers=1, head_hidden=256,
  dropout=0.2)`.

All use AdamW `lr=3e-4`, `weight_decay=1e-4`, global-norm clipping `1.0`, and no
scheduler. The LSTM values are the approved neutral control. Transformer/hybrid
dimensions follow the pinned paper implementation and map directly to Issue 10's
concrete fields. They are moderate fixed representatives, not optimality,
equal-capacity, exact-paper-reproduction, paper-authority, or permanent-setting claims.
Do not import the paper's seed, epoch count, stale loss weighting, missing clipping, or
extra legacy mechanics. Use LSTM for feature/loss screening and the selected-family fixed
control for descriptive context.

One completed epoch is one seed-shuffled pass over every retained unique training origin
exactly once, including the final short batch. For `N` origins, one epoch has `N`
optimization examples. Do not sample, cycle, truncate, equal-count, or normalize updates
across chains, architecture families, or context cells. Feature/loss and family pairs use
identical per-chain origins; chains stay separate.

All 30 fixed-control artifacts use physical batch 64, accumulation 1, and effective
batch 64. One epoch has `ceil(N/64)` minibatches and optimizer updates. For artifact `i`
with `E_i` completed epochs, report unique origins, `E_i*N_i` optimization examples,
`E_i*ceil(N_i/64)` minibatches/updates, and `E_i` separately.

For all 30 fixed-control artifacts and all 30 final-K artifacts:

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

After the global architecture family freezes, run exactly one bounded `K=5` Tune study
per chain for that family: three studies total. Issue 29 owns engine, all three
predeclared family-specific search spaces, candidate seed, finite trial budget, pruning,
HPO stopping/batch, recovery, selection, and promotion. All three family branches and
spaces must freeze before validation outcomes; only the selected branch executes. Family
is never a tunable parameter inside a mixed study. HPO uses finite complete-validation
`total_loss` only and cannot reopen family, features, loss, C, or K. Freeze each selected
per-chain model, optimizer, physical/effective batch, accumulation, and native tail-update
policy for all ten K values. Run no feature, loss, context, family, or per-K HPO.

The context matrix `C={50,100,200,500,1000}` varies a model input hyperparameter in a
broad technical sense but is not HPO or selection. It is a `K=5`, three-chain,
single-seed descriptive sensitivity study. Reuse the three exact selected-feature/loss
fixed controls for the globally selected family at `C=200` and train 12 additions with
natural per-C origins. Report all 15 cells, exact counts/endpoints, realized context
spans, and descriptive deltas. It cannot select or retune `C=200`. Context may run in
parallel with the three Tune studies after the family freezes because it does not consume
their outcomes.

The final horizon grid is
`K={2,3,4,5,10,15,30,50,100,200}` across three chains: 30 independently trained
artifacts. Use `C=200`, seed 2026, the frozen per-chain HPO configuration, and the
globally selected architecture family on per-chain origins complete through `K_max=200`.
Use no per-K HPO, stopping variation, sampling, update normalization, family-by-K matrix,
or best-K selection. `K=5` stays primary/default/headline.
Serving may expose only separately trained `K={2,3,4,5}` artifacts. A K=5 HPO result
selects the K=5 recipe but does not make inventory outcome-dependent: construct all 30
final-K TrainRequests under the final-K contract and preserve Issue 29's selected-study
provenance.

The final-K grid has at most 1,080 completed artifact-epochs. Final-K minibatches and
optimizer updates derive from the exact per-chain batch/accumulation/tail policy frozen
by Issue 29 and must be reported separately.

## Artifact inventory, requests, and execution order

There are exactly 30 unique fixed-control artifacts:

- capacity/activity: six;
- UTC: three reused controls plus three additions, nine cumulative;
- CE: three reused controls plus three additions, 12 cumulative;
- architecture family: three reused selected LSTM controls plus six Transformer/hybrid
  additions, 18 cumulative;
- context: three reused selected-family `C=200` controls plus 12 additions, 30 cumulative.

Reuse requires exact identity of corpus, roles/origins, K, C, features, loss,
model/optimizer, seed, training budget, and selected checkpoint. HPO candidates are
outside this count. With 30 distinct final-K artifacts, the durable non-HPO inventory is
60.

The canonical ready topology has twelve explicit deterministic lists:

1. capacity/activity Train: 6;
2. capacity/activity validation Evaluate: 6;
3. UTC Train additions: 3;
4. UTC validation Evaluate additions: 3, reusing three exact selected control
   evaluations from list 2;
5. CE Train additions: 3;
6. CE validation Evaluate additions: 3, reusing three exact unweighted
   selected-feature evaluations from lists 2 or 4;
7. architecture-family Train additions: 6;
8. architecture-family validation Evaluate additions: 6, reusing the three exact
   selected LSTM evaluations to complete nine family cells;
9. selected-family per-chain K=5 Tune: 3;
10. selected-family context Train additions: 12;
11. selected-family final-K Train: 30;
12. sealed-test Evaluate: 51.

Lists 7 and 8 begin only after feature/loss freeze. The global family freezes only after
list 8. Lists 9 and 10 may then run in parallel. List 11 waits for list 9. Lists 10 and 11
must both complete and freeze before list 12 begins. Numbering expresses canonical list
order, not benchmark dependency edges.

Totals are 60 Train, 3 Tune, and 69 Evaluate: 132 exact requests. The 69 evaluations
are 18 validation records plus 51 sealed-test records. Train owns only
complete-validation `total_loss`, checkpointing, and restoration; the range-driven
Evaluate workflow alone produces the captured-opportunity and harmful-action evidence
needed by the feature/loss and family gates. The final all-or-nothing TSV contains only
the ordered 51 sealed test records.

Issue 50 executes lists 1…6: 12 ladder Train artifacts plus 12 explicit post-fit
validation evaluations. It applies the frozen rule; it does not redefine the protocol.
A dedicated downstream family-comparison task executes lists 7 and 8. Issue 29 executes
list 9. Dedicated downstream tasks execute context, final K, and sealed testing. Core
request/workflow/report functions remain count-agnostic and accept any valid exact
request or list length. Add no benchmark scheduler, plan/DAG/array language, registry,
watcher, callback, matching layer, or benchmark resume state.

## Sealed testing and claims

After both branches freeze every protocol, configuration, checkpoint, range, and claim,
open exhaustive testing for the unique union of nine fixed family representatives, 15
selected-family context cells, and 30 selected-family final-K cells. Test all nine family
representatives, including the six rejected-family controls, but do not test rejected
feature/loss alternatives or unpromoted HPO candidates. The three selected-family fixed
`C=200` records occur once in the family segment and are referenced by the context view,
so the union contains exactly 51 EvaluateRequests and TSV rows. The fixed family evidence
cannot reopen the validation-selected family. `immediate_k0_reference` creates no artifact
or evaluation cell.

Order sealed requests as nine fixed family representatives chain-major with family inner
`LSTM, Transformer, TransformerLSTM`; then 12 selected-family context additions
chain-major with `C={50,100,500,1000}`; then 30 selected-family final-K artifacts
chain-major in the approved K order. One artifact/corpus/window creates one evaluation
record even when multiple report views reference it.

Testing scores every eligible finite chain-native block opportunity once in each maximal
frozen post-validation range. It may not change scope, `C=200`, the `K=5` headline,
features, loss, family, HPO, frozen exposure/stopping, ranges, metrics, or emphasized
claims. No partial family/context/K matrix, curve, or official test claim is valid.

Claims are limited to one finite chronological validation window, one frozen exhaustive
finite testing census, and one ML seed. Make no IID, population, confidence-interval,
statistical-equivalence, causal, future-period, or seed-robustness claim. Keep chains,
ranges, lifecycle roles, seeds, and K-specific descriptive problems separate. Add no
cross-chain pooling, chance correction, strict-monotonicity claim, context optimality, or
best-K claim. Architecture claims concern only the three predeclared fixed controls under
the LSTM-reference-selected feature/loss recipe. Make no intrinsic/universal family,
equal-capacity, global-optimum, or family-by-feature/context/K interaction claim. HPO of
the winner cannot strengthen claims about rejected controls. Results concern chain-native
target base-fee opportunities, not random users, equal seconds, transaction inclusion,
execution, full transaction cost, or generic profit.

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
  scientific prerequisites. Independently replace seven lists/102 requests with the
  twelve lists/132 requests above and add the feature/loss and family validation Evaluate
  lists. Preserve its
  count-agnostic exact-ID flow, zero benchmark dependency edges, ordinary evaluation jobs,
  and all-or-nothing writer.
- Wayfinder map: its maximum-time/compute rule remains for research/prototypes but not
  outcome-bearing Issue-49 execution; “fixed task and experiment budget” becomes “fixed
  task and experiment inventory”; its Issue-36 pointer becomes twelve lists/132 requests.
  Issue 29's declared finite trial budget remains HPO search scope, not runtime/GPU/money
  planning.

Begin a protocol stage when its scientific and implementation prerequisites are ready.
If execution proves too slow or costly, an operator may pause/cancel and return to Edo.
Any scope change is a fresh explicit amendment before continuing. Add no automatic
truncation, subsampling, fallback, adaptive matrix reduction, or partial-completion claim.

## Execution gate and ownership

No outcome-bearing acquisition, training, family comparison, HPO, context, K, or testing
run begins until
every blocking clean-break decision/specification and implementation ticket for that
stage is completed, integrated, reviewed, and verified, with required corpora,
artifacts, and contracts frozen. Do not run against stale or half-migrated semantics.

The architecture-neutral Issue-23 task, all three concrete Issue-10 family branches, and
the direct family-specific HPO construction needed for the selected branch must be fully
specified, implemented, independently reviewed, and integrated before Issue 50. The
post-integration target-hardware synthetic full/tail gate must verify all three family
paths, not only LSTM. Failure of any required path stops before outcome work and returns
to Edo; do not fall back to another family or shrink the matrix.

This gate does not wait for unrelated or explicitly deferred work. Priority-fee
follow-up, uncertainty, future decision-making, naming, and other nonblocking future work
do not delay the base thesis pipeline unless the native graph later makes one a blocker.

Issue 49 owns this finite protocol, roles, origin geometry, inventory, reuse, ordering,
selection gates, fixed architecture controls, seed, fixed-control training budget,
final-K stopping, claim boundary, and no-affordability rule. It does not own Issue 27
acquisition/finality/staging mechanics,
Issue 10's schema/concrete family modules, Issue 23's shared task math, Issue 29 HPO
mechanics/spaces, Issue 36 runner implementation, Issue 48 scorer/test mechanics, Issue
50 execution, production code/config/tests, or any actual data/model/job run.

Sibling Issues 23, 29, 36, 47, 48, 50, 62, 64, and 76 retain their historical bodies,
comments, and assets. Their stale LSTM/count wording is an explicit downstream handoff;
this amendment does not edit or comment on those issues.

## Architecture-amendment supersession ledger

The amendment changes only these original decisions:

- Decision 2 extends seed 2026 to architecture-family controls and HPO fits.
- Decision 3 runs three Tune studies for the validation-selected family, not a
  preselected LSTM; the C matrix remains descriptive rather than HPO.
- Decision 4 keeps the stale majority/persistence, linear/logistic, MLP, sample-size, and
  model-zoo deletions but reverses the deferral of the two named Transformer families.
- Decision 5 retains the LSTM control for feature/loss screening, adds the two exact fixed
  family controls, and makes the selected fixed family the context control.
- Decisions 6, 8, and 10 change 24 neutral artifacts to 30 fixed-control artifacts while
  preserving batch 64, accumulation 1, and 36/8 semantics.
- Decision 11 preserves 30 final-K artifacts and 36/8 semantics but uses the global
  validation-selected family and its per-chain HPO configurations.
- Decision 12 becomes the twelve-list/132-request/60-artifact/51-sealed-row topology.
- Decision 14 adds architecture family to validation ownership and keeps identical
  per-chain family-comparison origins.
- Decision 15's no-affordability substance is unchanged; only its required scientific
  accounting uses the amended counts.

Decisions 1, 7, 9, and 13 and every other unchanged clause survive. The historical
decision comments and sole Resolution are not edited or deleted. The Wayfinder map must
insert fixed-family comparison between Issue 50 and HPO, update the Issue-36 and Issue-49
gists to twelve lists/132 requests, replace Issue 48's fixed-LSTM gist with
selected-family K evidence, and add family to the result-dependent choices. Preserve the
full-code-first progression and ban on unbounded architecture search. Add no
project-owned version marker, compatibility path, parallel old/new mode, or migration
reader.

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

The architecture amendment also consumes:

- [Issue 10's direct three-family union](https://github.com/edoski/spice/issues/10#issuecomment-4957991242);
- the pinned paper-training source at commit
  [`bcf80b92877941e3b05a7dc5138560ffe41df27e`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/commit/bcf80b92877941e3b05a7dc5138560ffe41df27e),
  whose fixed Transformer, LSTM, and Transformer–LSTM constructors supply only the stated
  control dimensions, not superseded paper training semantics.

The audit found no unresolved consequential Issue-49 choice. Edo explicitly approved
this amended whole contract. Publication may replace this same research path, add one
`## Amendment` comment while preserving the historical sole Resolution and closed issue
state, apply the approved map pointer/text corrections, and verify the result. Nothing in
this document authorizes production or sibling-issue mutation.
