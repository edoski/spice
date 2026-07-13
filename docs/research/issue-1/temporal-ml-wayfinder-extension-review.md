# Temporal-ML Wayfinder extension review

Date: 2026-07-10

Status: graph review only. No ticket, GitHub relationship, production file, ADR, or
normative guide was changed. No candidate is approved.

## Verdict

Do not add the provisional research-ticket layer. The paper, protocol, preprocessing,
training/evaluation, leanness, statistics, and documentation audits are completed
charting evidence. Repeating them as open issues would create fake work and delay the
first owner decision.

Add **seven** tickets, not twelve or more:

1. prototype the intentional current-block route and its alternatives as one
   cross-layer fixture;
2. choose the temporal decision/action/protocol-regime contract;
3. choose causal preprocessing, split, feature, and context semantics;
4. prototype and choose exact evaluation and thesis-evidence semantics;
5. approve one bounded baseline/ablation protocol;
6. run that matrix; and
7. prototype and approve the layered beginner-documentation plan.

Reuse the existing prediction, fitting, HPO, tensorization, inference, serving,
records, ADR, evidence, and final-acceptance tickets. The result is **50 children and
73 direct blocker edges**. A local graph audit found no cycle, no redundant direct
edge, no orphan, and a seven-ticket initial frontier. Every child reaches **Approve
the final clean-break specification and execution order**.

This graph preserves two corrected premises:

- Offset zero as a current/forming-block action is an intentional SPICE extension.
  It stays a serious candidate. The defect is the missing per-chain information-set
  and actionability proof plus offline/serving disagreement, not an automatic `+1`
  label error.
- Bounded HPO is an intentional SPICE extension. Fixed configurations remain the
  control for structural ablations; the owner later chooses the smallest fair search
  and study lifecycle. Optuna is neither automatically retained nor deleted.

The serving defect is now part of the early fixture. With RPC latest head `L` and the
default confirmation depth two, serving observes `h=L-2`; its baseline and `k=0`
target are `L-1`, and `k=1` targets `L`. All are already closed. `k=2` is the first
future target. This must be fixed through one decision/action mapping, not an
unexplained constant.

## Revised map body

```markdown
## Destination

An owner-approved, dependency-ordered clean-break specification, temporal-ML evidence protocol, beginner-documentation rewrite plan, and implementation/cutover runbook for SPICE. It must define one causal temporal decision from corpus and preprocessing through fitting, evaluation, and serving; retain only complexity with approved evidence; and make the production design materially leaner, idiomatic, and understandable to its undergraduate author. No consequential choice may be left implicit for implementation.

## Notes

Planning only. Production implementation, normative guide rewriting, and active-storage cutover are outside this map; AFK tasks and HITL prototypes exist only to obtain evidence needed for a decision. Every grilling or prototype ticket requires Edo's explicit live approval. No paper statement, current behavior, historical result, progress note, or ADR is presumed correct, retained, or superseded.

Use `/research` for new external facts, `/prototype` for concrete comparisons, `/grilling` one question at a time for decisions, `/domain-modeling` for vocabulary, and `/codebase-design` for seam/depth analysis. Prefer the smallest theory-correct design, standard public APIs, direct owner functions, real alternatives only, and lowest total concept/interface/dependency cost. A slightly slower method may win inside an owner-approved materiality tolerance when it is substantially easier to understand. Clean break means no legacy readers, dual writes, compatibility shims, or transition tests.

Current-row offset zero and bounded HPO are intentional SPICE extensions, not accidental deviations from the paper. The current-row route must prove one per-chain/regime information set and actionable interval; bounded HPO must use common validation origins, sealed tests, correct reducers, declared budget, and a lifecycle that earns its machinery. Neither is automatically removed.

Charting evidence is in the current worktree under `docs/research/issue-1/temporal-paper-alignment-audit.md`, `temporal-chain-fee-protocol-audit.md`, `temporal-preprocessing-theory-audit.md`, `temporal-training-evaluation-theory-audit.md`, `temporal-evaluation-statistics-cross-review.md`, `temporal-ml-lean-alternatives.md`, and `architecture-implementation-docs-audit.md`. These are evidence, not decisions.

The documentation inventory is 46 `ARCHITECTURE.md`/`IMPLEMENTATIONS.md` files and 3,659 lines. Normative ML guides are designed only after semantics and interfaces settle. Prefer one beginner journey, one theory explanation, one exact contract reference, and local guides only for deep modules; do not expand 46 overlapping files by default.

Serving scope remains an owner gate. Compare an in-process/CLI thesis surface with the current FastAPI/Pydantic plus standard-library `sqlite3` demo. If HTTP and persistence remain, the existing stack is the default lean candidate; an ORM, async database wrapper, or replacement web framework must delete more concepts than it adds.

The 29,004-line charting baseline remains evidence. The former 26,100-line cap is a candidate to approve or replace after interfaces and documentation scope are known, not a pre-approved hard constraint.

Macro-F1 and Optuna-lifecycle work are conditional branches. If the metric decision removes macro-F1 and historical impact evidence is unnecessary, close the two macro-audit tickets as out of scope. If the HPO decision chooses a small non-Optuna route, close the Optuna-lifecycle prototype as out of scope. Record either choice explicitly.

## Decisions so far

<!-- Empty until a child ticket is resolved with explicit owner approval. -->

## Not yet specified

- Exact supported protocol eras, feature groups, prediction heads, model capacity, and serving claim depend on the temporal fixture and approved ablation evidence.
- Exact final periods, seed count, practical-equivalence tolerance, and paper-comparison view depend on the evaluation decision.
- Exact HPO sampler, storage, pruning, and preset-promotion route depends on the surviving model/search surface.
- Exact guide survivor list, rewrite order, and undergraduate verification exercise depend on approved semantics, interfaces, ADR language, and the documentation prototype.
- Existing storage, execution, benchmark, conversion, and cutover fog remains as already charted.

## Out of scope

- Production implementation, full normative guide rewriting, or live cutover during wayfinding.
- The paper's spatial-routing and distributed-reputation modules, except where a temporal artifact or serving boundary must name their absence.
- Automatically restoring the paper's next-block formulation, automatically shifting offset zero, or automatically deleting the intentional HPO extension.
- Unbounded architecture, feature, objective, or framework search beyond the named baseline and ablation candidates approved by the owner.
- Permanent compatibility readers, dual writes, dual metrics under one name, migration shims, or architecture-transition tests.
- DDP, multiwriter tuning, or a multi-tenant public serving platform unless the owner redraws the destination.
- Calling base-fee-per-gas savings full transaction profit unless gas, priority fees, inclusion, and latency utility are explicitly added to the approved estimand.
- Hydra, an ORM for a one-table service, or a speculative plugin/registry without two real implementations and distinct contracts.
- Automatic deletion of pre-cutover storage, raw evidence, or historical methods.
```

## Seven new tickets

The bodies below are exact proposed issue bodies.

### Prototype the current-block action and cross-layer parity

Label: `wayfinder:prototype`

```markdown
## Question

Build one small executable decision record for each materially distinct supported chain/regime and compare three serious routes: the intentional current/forming-block action with universal closed-parent inputs, the smallest chain-aware virtual open row, and the paper-next-block comparator. Trace decision time, every input's availability, request/submission time, eligibility interval, first actionable target, block-versus-seconds action, broadcast-versus-inclusion deadline, ties, fallback, offline label, realized evaluation outcome, and serving response.

Explicitly reproduce the current default serving clock: for RPC head `L` and confirmation depth two, context ends at `L-2`, `k=0` targets `L-1`, `k=1` targets `L`, and only `k=2` is future. Compare repaired mappings without a magic constant. Prefer mature protocol/client/RPC APIs over custom Polygon/Avalanche parsing and state what cannot be proved.

Link the prototype. Do not choose the final contract in this ticket; do not close until the owner reacts explicitly.
```

### Choose the temporal decision, action, and protocol-regime contract

Label: `wayfinder:grilling`

```markdown
## Question

Using the cross-layer prototype, choose whether offset zero means a physical forming block, an immediate submission action whose first eligible block is resolved later, or the paper-next-block comparator. Approve the decision instant, information set, universal versus per-chain/regime contract, corpus-era eligibility/metadata, action unit, submission and inclusion mapping, baseline, feasible oracle, deadline boundary, unavailable-action fallback, equal-fee tie utility, and Sepolia demo claim.

Preserve current-row offset zero as an intentional serious candidate. Do not infer that a finalized historical row is live-available, that EIP-1559 behavior is uniform across chains, or that eligibility guarantees inclusion. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Choose causal preprocessing, split, feature, and context semantics

Label: `wayfinder:grilling`

```markdown
## Question

Using the approved temporal contract, choose the canonical corpus invariants and fail-versus-repair boundary; protocol-era handling; block-count versus true-seconds context; complete-outcome purging at train/validation/test cutoffs; internal-test versus external-test roles; training-only fitted statistics; feature availability and units; protocol-core baseline; calendar/cadence, lag, rolling, priority-fee, and elapsed groups; scaler behavior; and exact feature-history disclosure.

Require one per-feature `available_at` table and one split fixture proving zero forward target dependencies across role cutoffs while allowing causal past-context overlap. Treat the 45/77-feature catalogs, fixed median-derived sequence length, inverse clipping, and scikit-learn scaler as candidates rather than defaults. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Prototype and choose temporal evaluation and thesis-evidence semantics

Label: `wayfinder:prototype`

```markdown
## Question

Prototype exact decision accounting on hand-computable fixtures and representative frozen windows. Compare mean-request base-fee savings, gas-weighted ratio of sums, baseline-normalized feasible-oracle regret, harmful-action rate, deadline/fallback rate, wait, and raw-value tie-aware hit. Ban the generic name `profit` unless the approved utility models profit.

For deterministic evaluation, prove fixed-window exposure reduction and separately either integrate the uniform-random-window-start inclusion kernel or explicitly replace random starts with predeclared named windows. Cover duplicate timestamps, block-versus-wall-clock weighting, finite-ratio versus ratio-of-expectations semantics, and the cases where arrival rate or stochastic replay still matters. Do not claim whole-corpus duration weighting exactly replaces the current random-window estimator.

After reacting to the prototype, approve metric names/formulas/units, paper-comparison views, evaluation periods/regimes, validation and final-test seal, pairing unit, seed protocol, uncertainty labels, and the practical-equivalence tolerance used to prefer a leaner model. Link the prototype; do not close without explicit owner approval.
```

### Approve the temporal baseline and ablation protocol

Label: `wayfinder:grilling`

```markdown
## Question

Freeze one affordable paired protocol before running new model evidence. Choose common purged origins, named validation periods, exploration/finalist seeds, resource budget, stopping/ranking rules, and a practical-equivalence threshold. Include immediate execution, majority offset, chain/regime-aware protocol or persistence forecast, logistic/linear, shallow MLP, small one-layer LSTM, current LSTM, and Transformer/hybrid only if simpler candidates leave a material gap.

Approve named feature rungs and objective ablations: protocol-core versus engineered features; unweighted classification control; correctly reduced weighted classification; current auxiliary fee head; and fee-vector regression only if it can delete more concepts than it adds. Use fixed declared configurations for structural comparisons. Preserve bounded HPO as a later calibration extension rather than retuning every ablation cell. Work live one question at a time and do not close without explicit owner approval.
```

### Run the temporal baseline and ablation matrix

Label: `wayfinder:task`

```markdown
## Question

Execute only the approved paired matrix on the approved common origins and seeds. Record every configuration, feature and parameter count, train time, source/concept surface, validation loss, approved economic/safety metrics, all seed-period points, failures, revision, lock, device, corpus/regime identity, and hashes. Do not open the final test, expand the matrix after seeing results, select a lucky seed, or run bounded HPO inside structural ablations.

Link the immutable evidence report and raw result location. Do not infer the winning feature, objective, model, framework, or dependency from task completion.
```

### Prototype and approve the layered beginner documentation plan

Label: `wayfinder:prototype`

```markdown
## Question

Using only approved semantics, interfaces, evidence, ADR dispositions, and domain language, prototype one end-to-end undergraduate journey plus the exact rewrite/merge/retire plan for all 46 current `ARCHITECTURE.md`/`IMPLEMENTATIONS.md` files and adjacent `README.md`, `CONTEXT.md`, and historical pointers. Compare the layered route—orientation, one worked temporal-ML tutorial, one theory explanation, one exact contract reference, and local guides only for deep modules—with retaining the current paired taxonomy.

The worked example must show values, shapes, units, availability, split ownership, target, loss reduction, decoding, economic accounting, HPO's bounded role, serving parity, paper facts versus SPICE extensions, limitations, and source links. Dynamic ids/counts must come from code or CLI. Include a rewrite order after implementation semantics settle and an undergraduate-reader/source/link/equation verification checklist.

Link the prototype. Do not rewrite the normative guide set in this ticket; do not close until the owner explicitly approves the information architecture and rewrite/verification runbook.
```

## Existing-ticket reuse edits

Unlisted issue bodies stay unchanged. These bodies replace the current text exactly.

Renamed existing issues:

| Existing issue | Replacement title |
|---|---|
| [Choose training and tuning selection, best-state, nonfinite, and resume semantics](https://github.com/edoski/spice/issues/16) | Choose selection, reproducibility, best-state, nonfinite, and resume semantics |
| [Prototype model construction and typed Optuna parameter application](https://github.com/edoski/spice/issues/17) | Prototype model construction and approved parameter application |
| [Choose metric and exact loss semantics](https://github.com/edoski/spice/issues/21) | Choose predictive diagnostics and exact loss/scorer semantics |
| [Prototype the concrete Min-Block-Fee task interface](https://github.com/edoski/spice/issues/23) | Choose and prototype the minimum justified Min-Block-Fee task |
| [Choose concrete temporal and action-policy interfaces](https://github.com/edoski/spice/issues/24) | Choose temporal compilation and action/outcome module boundaries |
| [Prototype Journal locking, pruning, and coherent tuned snapshots](https://github.com/edoski/spice/issues/25) | Prototype the approved bounded Optuna lifecycle |
| [Prototype idiomatic Lightning fit, checkpoint, and resume](https://github.com/edoski/spice/issues/26) | Prototype and choose the lean training host |
| [Prototype fixed-context tensorization and DataLoader behavior](https://github.com/edoski/spice/issues/28) | Prototype causal fixed-context tensorization and DataLoader behavior |
| [Choose Optuna trial-budget and abandonment semantics](https://github.com/edoski/spice/issues/29) | Choose the bounded HPO, trial-budget, and study-lifecycle policy |
| [Prototype historical and online inference boundaries](https://github.com/edoski/spice/issues/31) | Prototype historical and online preparation with actionable-head parity |
| [Choose serving durability, lifecycle, and artifact-chain policy](https://github.com/edoski/spice/issues/33) | Choose serving scope, durability, lifecycle, and artifact-chain policy |
| [Freeze durable record, feature-compatibility, weight-ABI, and provenance contracts](https://github.com/edoski/spice/issues/34) | Freeze durable ML, evaluation, weight-ABI, and provenance contracts |
| [Approve the implementation budget, replacement verification suite, and final acceptance contract](https://github.com/edoski/spice/issues/37) | Approve the implementation budget, verification suite, and final acceptance contract |
| [Run the same-weight CUDA evidence gate](https://github.com/edoski/spice/issues/40) | Run the approved same-weight accelerator evidence gate |

The serving/mobile title remains unchanged; its body and dependencies change.

### Approve the 648-window macro-F1 audit protocol

```markdown
## Question

Work this branch only if **Choose predictive diagnostics and exact loss/scorer semantics** retains macro-F1 or requires historical impact evidence. Approve the old-code revision, non-mutating historical-plan normalization, raw and normalized hashes, target-supported and union-active formulas, per-class counts, caching, array shape, environment provenance, expected sample checks, root-hash guarantees, and immutable result format. The audit must create a separate dataset and never reinterpret or rewrite the historical collection.

If macro-F1 and its historical audit are rejected, close this ticket and its execution child as out of scope with the reason. Otherwise work live one question at a time and do not close without explicit owner approval.
```

### Choose configuration identities and the schema-owned workflow algebra

```markdown
## Question

Using the approved temporal decision/action contract, classify recipe names, executable discriminators, and domain identities, then choose one compact config-file module for safe YAML/raw show-edit-seed and typed loading. Specify Literal-tagged train/tune/evaluate requests, nested baseline/study training source, complete root addresses, output minting, tagged windows, protocol-regime and action units, strict TypeAdapter hydration, and config-only model alternatives. Remove owner coercers, SerializeAsAny, resolved-field records, structural guessing, and one-entry registries unless a concrete requirement survives.

Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Choose selection, reproducibility, best-state, nonfinite, and resume semantics

Label remains `wayfinder:grilling`.

```markdown
## Question

Using the frozen objective evidence, approved evaluation protocol, and exact scorer, choose corrected validation loss for epoch stopping/pruning versus the approved deterministic economic score for bounded configuration ranking. Seed before model construction; define exploration and finalist seeds; prohibit per-trial test scoring; and decide raw finite minimum versus min-delta patience, one-based epochs, fail versus retain-prior-best on nonfinite maps, and exact continuation versus explicitly restarted stochastic resume.

State what reproducibility is promised within the pinned environment and what is not promised across releases/devices. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Prototype model construction and approved parameter application

Label remains `wayfinder:prototype`.

```markdown
## Question

For the approved minimum task and bounded search route, compare config-only model/model-space unions plus a small constructor table with the current generic ModelSpec/lazy-loader/tuned-record stack. Define stable flat parameter names and one pure allowlisted application operation that rejects unknowns, revalidates cross-field constraints, and derives dependent dimensions. If a small explicit design replaces Optuna, do not preserve Optuna-shaped types merely for compatibility; avoid an untyped dotted-path language in every route.

Link the prototype; do not close until the owner reacts and explicitly approves.
```

### Choose predictive diagnostics and exact loss/scorer semantics

Label remains `wayfinder:grilling`.

```markdown
## Question

Using the approved decision/evaluation contract, choose the minimal predictive diagnostics and exact full-map reducers used by experiments: tie-aware hit, paper-comparison accuracy, optional conventional union-active macro-F1, and any retained regression errors. Decide whether macro-F1 answers a thesis or archival question; if not, close its audit branch as out of scope.

Define exact numerators and denominators for unweighted cross-entropy, corrected weighted cross-entropy, Smooth L1, and composed candidate losses so results are invariant to batch partition. Keep candidate variants for the approved ablation; do not decide the final head/weighting/task before that evidence. Require one finite scorer shared by fitting, standalone validation, conversion, and evaluation, with metric ids, units, direction, phase, zero/tie rule, and provenance explicit.

Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Choose and prototype the minimum justified Min-Block-Fee task

Label remains `wayfinder:prototype`.

```markdown
## Question

Using the approved temporal/tensor interfaces and frozen baseline-ablation evidence, choose the smallest feature, target, head, loss, and model-family surface inside the approved practical-equivalence tolerance. Compare the surviving classification-only, corrected weighted, current multitask, and fee-vector candidates without presuming the paper or current two-head task wins.

Prototype one concrete task module covering fitted target state, target batches, exact loss/scorer, decoding, model construction, evaluator input, and serving. Remove one-family registries and generic target/accumulator/result protocols; keep model/feature alternatives only where the evidence leaves real alternatives. Link the prototype; do not close until the owner reacts and explicitly approves.
```

### Choose temporal compilation and action/outcome module boundaries

Label remains `wayfinder:grilling`.

```markdown
## Question

Using the approved temporal and preprocessing contracts, choose direct interfaces for sample compilation and one action/outcome mapper shared by labels, deterministic/stochastic evaluation, historical inference, and serving. Preserve only approved geometry, action masks, capability/regime metadata, fallback/deadline behavior, feasible oracle, validation, and fail-closed persisted versions.

Remove one-entry compiler/policy registries and abstract config bases unless a second approved implementation has a distinct contract. Do not combine unrelated tensor, prediction, evaluator, or serving ownership merely to reduce file count. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Prototype the approved bounded Optuna lifecycle

Label remains `wayfinder:prototype`.

```markdown
## Question

Work this conditional branch only if the bounded-HPO decision retains Optuna and a persistent study lifecycle. On approved storage, prove fresh/resumed sampler and pruner construction, real per-epoch loss reporting/pruning or explicit no-pruning, validation-only trial summaries, common origins, terminal budget/recovery, writer exclusion, definition integrity, and coherent best-trial/config/count snapshots. Trials must emit no test score, artifact, checkpoint, or artifact stage.

Use RDB, Journal, or another approved backend; do not assume Journal is leaner. If Optuna persistence is rejected, close this ticket as out of scope. Link the prototype; do not close until the owner reacts explicitly.
```

### Prototype and choose the lean training host

Label remains `wayfinder:prototype`.

```markdown
## Question

Implement the same approved tiny task once as a short direct-PyTorch fit and once as idiomatic Lightning automatic optimization. Compare the whole boundary: seeded initialization, exact validation reduction, device/precision, clipping, nonfinite behavior, raw-best/patience semantics, interruption and approved resume, checkpoint contents, full/tail batches, and the approved bounded-HPO epoch hook. Measure production/test/config lines and concepts an undergraduate must learn.

Choose one host and one narrow `fit(...) -> FitResult` boundary; do not keep a framework-neutral adapter over both. Lightning wins only if stock lifecycle deletes the custom fit/checkpoint machinery; PyTorch wins only if the complete lifecycle remains small and correct. Link the prototype; do not close until the owner reacts and explicitly approves.
```

### Prototype causal fixed-context tensorization and DataLoader behavior

Label remains `wayfinder:prototype`.

```markdown
## Question

Implement the approved context and scaling semantics with one focused training/inference preparation boundary. If fixed block contexts win, prove uniform length before workers, strict population scaling, contiguous vectorized tensorization, one action-mask owner, CPU inference positions, standard seeded DataLoader shuffling/collation, full/tail batches, transfer/pinning, and measured worker settings; delete padding, input masks, signatures, BatchPlan, and the custom sampler only when behavior and approved resume are covered.

If true variable seconds contexts win, prototype the smallest honest length/mask path instead of retaining fixed-row claims. Link the prototype; do not close until the owner reacts and explicitly approves.
```

### Choose the bounded HPO, trial-budget, and study-lifecycle policy

Label remains `wayfinder:grilling`.

```markdown
## Question

Treat bounded HPO as an intentional research extension. For the surviving minimum task, choose the smallest fair calibration route: a small explicit design, seeded random search, or Optuna for a genuinely wide conditional space. Approve common validation origins, one exploration seed, finalist multi-seed confirmation, validation-loss pruning, deterministic economic trial ranking, sealed tests, trial-state budget/retry rules, fresh/resumed sampler state, storage, and explicit preset promotion before reuse.

Fixed configurations remain mandatory for structural ablations. Do not retain Optuna merely for historical compatibility and do not delete the HPO extension merely because the control model needs no search. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Prototype historical and online preparation with actionable-head parity

Label remains `wayfinder:prototype`.

```markdown
## Question

Prototype one-frame historical requested-window preparation and a focused online right-edge preparer under the approved decision contract. Preserve coverage, no-future inputs, scaling, context selection, action masks, artifact compatibility, and exact requested windows while separating `latest_rpc_head`, `last_finalized_context`, and `first_actionable_target`.

Prove the default confirmation-depth-two case does not map any recommendation to a closed block. Construct an approved virtual current row only if the temporal contract requires it; otherwise map the immediate action from closed-parent inputs through the shared action/outcome function. Do not hide distinct historical and live algorithms behind a mode flag merely to claim reuse. Link the prototype; do not close until the owner reacts explicitly.
```

### Choose serving scope, durability, lifecycle, and artifact-chain policy

Label remains `wayfinder:grilling`.

```markdown
## Question

First choose whether the thesis needs only an in-process/CLI inference surface or a live HTTP demo with persistent analytics. If the HTTP demo remains, treat FastAPI/Pydantic plus standard-library `sqlite3` as the lean default and require measured concept deletion before adopting an ORM, async database wrapper, or replacement framework.

From the approved trust/process/host and actionable-head contracts, specify bounds, expiry, exact observation transitions/counters, corruption, transaction/connection closure, lock/offload policy, FastAPI lifespan readiness/cleanup, RPC/model/store ownership, artifact address/chain/regime compatibility, Sepolia's demo-only or performance-claim status, and old-store import/archive/discard. Work live one question at a time and do not close without explicit owner approval.
```

### Freeze durable ML, evaluation, weight-ABI, and provenance contracts

Label remains `wayfinder:grilling`.

```markdown
## Question

Specify strict corpus, study, artifact, evaluation, and benchmark records as one coherent set after the approved HPO and serving prototypes. Include identity/address, effective temporal decision contract, protocol regime and information set, source/range/content facts, study snapshot, feature compatibility, scaler/context/action capability, strict best-weight ABI, complete metric maps with estimand ids, evaluation parent/corpus/window/provenance/typed totals, serving action fields, and one minimal secret-free software/runtime provenance record.

Remove duplicated recipes, runtime controls, completed-run resume state, and any field whose only purpose is legacy compatibility. Work live one question at a time, give a recommendation, and do not close without explicit owner approval.
```

### Approve the implementation budget, verification suite, and final acceptance contract

Label remains `wayfinder:grilling`.

```markdown
## Question

Re-estimate gross deletions/additions and final production/test/documentation surface from approved interfaces. Treat 26,100 production lines as a candidate target to approve or replace, not an inherited hard gate. Map every invariant to the smallest deepest-interface test; delete shallow tests with their removed modules; separate pytest from hardware/filesystem/performance/conversion evidence; and define truthful dependency, wheel, CLI/mobile/serving/Slurm, security, documentation, archive, rollback, and manual Vulture-review gates.

Require the approved documentation runbook, worked-example source audit, and undergraduate-reader verification in final acceptance. Work live one question at a time and do not close without explicit owner approval.
```

### Run the approved same-weight accelerator evidence gate

Label remains `wayfinder:task`.

```markdown
## Question

For every model family and tensor/training path that survives the approved minimum-task decision, run old/new same-weight accelerator comparisons on full and tail batches where a behavior-preserving comparison exists. Require exact positions/masks, zero decoded-action mismatches, approved raw-output tolerances, and retained device/driver/CUDA/cuDNN/Torch/dtype/config/sample/artifact hashes. Do not spend evidence budget preserving discarded families or a deliberately changed target under a false equivalence claim.

Remove every temporary dual path after freezing the evidence. Link the resulting report; do not infer approval from task completion.
```

### Prototype the serving and mobile timed-transfer contract

Label remains `wayfinder:prototype`.

```markdown
## Question

Exercise the backend and Expo client together using the approved actionable-head mapper. Define RPC latest head, finalized context head, first actionable target, selected action, broadcast threshold, inclusion target, TTL, cancellation, receipt observation, RPC disagreement, chain/regime/artifact metadata, request authority, and API compatibility. Include the default confirmation-depth-two fixture proving no response instructs a wait for a closed block.

Use provisional schemas in this prototype so it does not wait on final durable records; the durable-record ticket must absorb the approved result afterward. Choose generated OpenAPI types or one lean schema test and delete the unused SpiceDemo contract/address unless an exact event protocol is approved. Link the prototype; do not close until the owner reacts explicitly.
```

## Complete direct-blocker DAG

Only the titles below are authoritative. “None” means initial frontier. This is the
minimal direct graph; no listed blocker is already implied by another blocker on the
same row.

| Ticket | Direct blockers |
|---|---|
| Measure target filesystem, root-inventory, and Optuna Journal constraints | None |
| Freeze the pre-break code, data, environment, and performance baseline | None |
| Freeze the total-loss versus economic-objective A/B evidence | None |
| Audit remote execution against supported OpenSSH, rsync, and Slurm interfaces | None |
| Compare RPC retry ownership and acquisition finality alternatives | None |
| Inventory research scripts, evaluation-suite data, and publication assets | None |
| Prototype the current-block action and cross-layer parity | None |
| Choose the temporal decision, action, and protocol-regime contract | Prototype the current-block action and cross-layer parity |
| Choose serving trust, exposure, and observation transitions | Freeze the pre-break code, data, environment, and performance baseline |
| Approve neutral export and raw-backup custody | Measure target filesystem, root-inventory, and Optuna Journal constraints; Freeze the pre-break code, data, environment, and performance baseline |
| Create the sanitized neutral pre-break export | Approve neutral export and raw-backup custody |
| Choose root identity, content equality, finality, and canonical addresses | Create the sanitized neutral pre-break export; Compare RPC retry ownership and acquisition finality alternatives |
| Choose publication, study mutability, deletion, transfer, and cutover primitives | Choose root identity, content equality, finality, and canonical addresses |
| Prototype the direct-discovery and lifecycle seam | Choose publication, study mutability, deletion, transfer, and cutover primitives |
| Choose configuration identities and the schema-owned workflow algebra | Choose root identity, content equality, finality, and canonical addresses; Choose the temporal decision, action, and protocol-regime contract |
| Choose causal preprocessing, split, feature, and context semantics | Choose the temporal decision, action, and protocol-regime contract |
| Prototype and choose temporal evaluation and thesis-evidence semantics | Choose the temporal decision, action, and protocol-regime contract |
| Choose predictive diagnostics and exact loss/scorer semantics | Prototype and choose temporal evaluation and thesis-evidence semantics |
| Approve the 648-window macro-F1 audit protocol | Freeze the pre-break code, data, environment, and performance baseline; Choose predictive diagnostics and exact loss/scorer semantics |
| Run and freeze the 648-window macro-F1 impact audit | Approve the 648-window macro-F1 audit protocol |
| Choose selection, reproducibility, best-state, nonfinite, and resume semantics | Choose predictive diagnostics and exact loss/scorer semantics; Freeze the total-loss versus economic-objective A/B evidence |
| Approve the temporal baseline and ablation protocol | Choose causal preprocessing, split, feature, and context semantics; Choose selection, reproducibility, best-state, nonfinite, and resume semantics |
| Run the temporal baseline and ablation matrix | Approve the temporal baseline and ablation protocol |
| Choose temporal compilation and action/outcome module boundaries | Choose configuration identities and the schema-owned workflow algebra; Choose causal preprocessing, split, feature, and context semantics |
| Prototype causal fixed-context tensorization and DataLoader behavior | Choose temporal compilation and action/outcome module boundaries; Choose selection, reproducibility, best-state, nonfinite, and resume semantics |
| Choose and prototype the minimum justified Min-Block-Fee task | Run the temporal baseline and ablation matrix; Run and freeze the 648-window macro-F1 impact audit; Prototype causal fixed-context tensorization and DataLoader behavior |
| Choose the bounded HPO, trial-budget, and study-lifecycle policy | Choose and prototype the minimum justified Min-Block-Fee task |
| Prototype model construction and approved parameter application | Choose the bounded HPO, trial-budget, and study-lifecycle policy |
| Prototype and choose the lean training host | Choose the bounded HPO, trial-budget, and study-lifecycle policy; Choose publication, study mutability, deletion, transfer, and cutover primitives |
| Prototype the approved bounded Optuna lifecycle | Prototype model construction and approved parameter application; Prototype and choose the lean training host |
| Prototype exact-root acquisition with one retry owner | Choose temporal compilation and action/outcome module boundaries; Choose publication, study mutability, deletion, transfer, and cutover primitives |
| Prototype the labelled Cartesian benchmark language | Choose configuration identities and the schema-owned workflow algebra |
| Classify research scripts and generated assets | Prototype the labelled Cartesian benchmark language; Inventory research scripts, evaluation-suite data, and publication assets |
| Choose the remote execution control architecture | Choose publication, study mutability, deletion, transfer, and cutover primitives; Audit remote execution against supported OpenSSH, rsync, and Slurm interfaces |
| Choose benchmark data-flow and scheduling semantics | Prototype the labelled Cartesian benchmark language |
| Specify atomic plans and resumable submissions | Choose benchmark data-flow and scheduling semantics; Choose the remote execution control architecture |
| Prototype historical and online preparation with actionable-head parity | Choose and prototype the minimum justified Min-Block-Fee task |
| Choose serving scope, durability, lifecycle, and artifact-chain policy | Choose serving trust, exposure, and observation transitions; Prototype the direct-discovery and lifecycle seam; Prototype and choose the lean training host; Prototype historical and online preparation with actionable-head parity |
| Prototype the serving and mobile timed-transfer contract | Choose serving scope, durability, lifecycle, and artifact-chain policy |
| Freeze durable ML, evaluation, weight-ABI, and provenance contracts | Prototype the approved bounded Optuna lifecycle; Prototype the serving and mobile timed-transfer contract |
| Prototype exact collection and maintained research consumers | Freeze durable ML, evaluation, weight-ABI, and provenance contracts; Specify atomic plans and resumable submissions; Classify research scripts and generated assets |
| Set dependency, wheel, research-extra, and vulnerability policy | Choose serving scope, durability, lifecycle, and artifact-chain policy; Prototype exact-root acquisition with one retry owner; Prototype the approved bounded Optuna lifecycle; Classify research scripts and generated assets; Choose the remote execution control architecture |
| Run the approved same-weight accelerator evidence gate | Freeze durable ML, evaluation, weight-ABI, and provenance contracts |
| Choose strict conversion eligibility and recoverable cutover policy | Prototype exact collection and maintained research consumers; Set dependency, wheel, research-extra, and vulnerability policy |
| Rehearse strict conversion and recoverable cutover | Choose strict conversion eligibility and recoverable cutover policy; Run the approved same-weight accelerator evidence gate |
| Approve ADR dispositions and post-break domain language | Specify atomic plans and resumable submissions; Freeze durable ML, evaluation, weight-ABI, and provenance contracts |
| Prototype and approve the layered beginner documentation plan | Approve ADR dispositions and post-break domain language |
| Approve the implementation budget, verification suite, and final acceptance contract | Prototype and approve the layered beginner documentation plan; Rehearse strict conversion and recoverable cutover |
| Specify the implementation order and acceptance/cutover runbook | Approve the implementation budget, verification suite, and final acceptance contract |
| Approve the final clean-break specification and execution order | Specify the implementation order and acceptance/cutover runbook |

## Desired topological child order

This order keeps the initial frontier first and places each child after every direct
blocker. Existing issue links are included so the GitHub reorder can be applied without
title matching ambiguity.

1. [Freeze the pre-break code, data, environment, and performance baseline](https://github.com/edoski/spice/issues/3)
2. [Freeze the total-loss versus economic-objective A/B evidence](https://github.com/edoski/spice/issues/5)
3. [Measure target filesystem, root-inventory, and Optuna Journal constraints](https://github.com/edoski/spice/issues/2)
4. [Audit remote execution against supported OpenSSH, rsync, and Slurm interfaces](https://github.com/edoski/spice/issues/6)
5. [Compare RPC retry ownership and acquisition finality alternatives](https://github.com/edoski/spice/issues/7)
6. [Inventory research scripts, evaluation-suite data, and publication assets](https://github.com/edoski/spice/issues/8)
7. **Prototype the current-block action and cross-layer parity**
8. **Choose the temporal decision, action, and protocol-regime contract**
9. [Choose serving trust, exposure, and observation transitions](https://github.com/edoski/spice/issues/22)
10. [Approve neutral export and raw-backup custody](https://github.com/edoski/spice/issues/14)
11. [Create the sanitized neutral pre-break export](https://github.com/edoski/spice/issues/12)
12. [Choose root identity, content equality, finality, and canonical addresses](https://github.com/edoski/spice/issues/11)
13. [Choose publication, study mutability, deletion, transfer, and cutover primitives](https://github.com/edoski/spice/issues/15)
14. [Prototype the direct-discovery and lifecycle seam](https://github.com/edoski/spice/issues/13)
15. [Choose configuration identities and the schema-owned workflow algebra](https://github.com/edoski/spice/issues/10)
16. **Choose causal preprocessing, split, feature, and context semantics**
17. **Prototype and choose temporal evaluation and thesis-evidence semantics**
18. [Choose predictive diagnostics and exact loss/scorer semantics](https://github.com/edoski/spice/issues/21)
19. [Approve the 648-window macro-F1 audit protocol](https://github.com/edoski/spice/issues/4)
20. [Run and freeze the 648-window macro-F1 impact audit](https://github.com/edoski/spice/issues/9)
21. [Choose selection, reproducibility, best-state, nonfinite, and resume semantics](https://github.com/edoski/spice/issues/16)
22. **Approve the temporal baseline and ablation protocol**
23. **Run the temporal baseline and ablation matrix**
24. [Choose temporal compilation and action/outcome module boundaries](https://github.com/edoski/spice/issues/24)
25. [Prototype causal fixed-context tensorization and DataLoader behavior](https://github.com/edoski/spice/issues/28)
26. [Choose and prototype the minimum justified Min-Block-Fee task](https://github.com/edoski/spice/issues/23)
27. [Choose the bounded HPO, trial-budget, and study-lifecycle policy](https://github.com/edoski/spice/issues/29)
28. [Prototype model construction and approved parameter application](https://github.com/edoski/spice/issues/17)
29. [Prototype and choose the lean training host](https://github.com/edoski/spice/issues/26)
30. [Prototype the approved bounded Optuna lifecycle](https://github.com/edoski/spice/issues/25)
31. [Prototype exact-root acquisition with one retry owner](https://github.com/edoski/spice/issues/27)
32. [Prototype the labelled Cartesian benchmark language](https://github.com/edoski/spice/issues/18)
33. [Classify research scripts and generated assets](https://github.com/edoski/spice/issues/20)
34. [Choose the remote execution control architecture](https://github.com/edoski/spice/issues/19)
35. [Choose benchmark data-flow and scheduling semantics](https://github.com/edoski/spice/issues/36)
36. [Specify atomic plans and resumable submissions](https://github.com/edoski/spice/issues/30)
37. [Prototype historical and online preparation with actionable-head parity](https://github.com/edoski/spice/issues/31)
38. [Choose serving scope, durability, lifecycle, and artifact-chain policy](https://github.com/edoski/spice/issues/33)
39. [Prototype the serving and mobile timed-transfer contract](https://github.com/edoski/spice/issues/43)
40. [Freeze durable ML, evaluation, weight-ABI, and provenance contracts](https://github.com/edoski/spice/issues/34)
41. [Prototype exact collection and maintained research consumers](https://github.com/edoski/spice/issues/35)
42. [Set dependency, wheel, research-extra, and vulnerability policy](https://github.com/edoski/spice/issues/32)
43. [Run the approved same-weight accelerator evidence gate](https://github.com/edoski/spice/issues/40)
44. [Choose strict conversion eligibility and recoverable cutover policy](https://github.com/edoski/spice/issues/41)
45. [Rehearse strict conversion and recoverable cutover](https://github.com/edoski/spice/issues/42)
46. [Approve ADR dispositions and post-break domain language](https://github.com/edoski/spice/issues/39)
47. **Prototype and approve the layered beginner documentation plan**
48. [Approve the implementation budget, verification suite, and final acceptance contract](https://github.com/edoski/spice/issues/37)
49. [Specify the implementation order and acceptance/cutover runbook](https://github.com/edoski/spice/issues/38)
50. [Approve the final clean-break specification and execution order](https://github.com/edoski/spice/issues/44)

## Existing edge changes

For application, set each affected existing ticket to the complete blocker set in the
DAG above. Relative to the live graph, the important semantic rewires are:

- **Choose predictive diagnostics and exact loss/scorer semantics** no longer waits on
  the macro audit; it is blocked by the evaluation prototype. The macro branch moves
  after this decision.
- **Choose and prototype the minimum justified Min-Block-Fee task** waits on ablation
  evidence, conditional macro resolution, and tensorization rather than presuming the
  current task.
- **Choose the bounded HPO, trial-budget, and study-lifecycle policy** moves after the
  minimum task. The Optuna lifecycle remains a conditional downstream prototype.
- **Prototype and choose the lean training host** compares two hosts after the task/HPO
  shape and no longer presumes Lightning.
- **Prototype historical and online preparation with actionable-head parity** moves
  before serving durability. **Prototype the serving and mobile timed-transfer
  contract** no longer waits for final durable records; final records wait for it.
- **Freeze durable ML, evaluation, weight-ABI, and provenance contracts** joins only
  the approved HPO lifecycle and serving/mobile result. This removes the possible
  durable-record/serving cycle.
- Existing redundant edges are removed, including direct blockers already implied by
  another blocker on the same ticket. This reduces the live 103-edge graph to 73 edges
  despite seven added nodes.

## Frontier and audit checklist

Expected initial frontier, in order:

1. **Freeze the pre-break code, data, environment, and performance baseline**
2. **Freeze the total-loss versus economic-objective A/B evidence**
3. **Measure target filesystem, root-inventory, and Optuna Journal constraints**
4. **Audit remote execution against supported OpenSSH, rsync, and Slurm interfaces**
5. **Compare RPC retry ownership and acquisition finality alternatives**
6. **Inventory research scripts, evaluation-suite data, and publication assets**
7. **Prototype the current-block action and cross-layer parity**

Before publishing the graph:

- create all seven issues first, then attach all 50 as children and wire dependencies;
- apply exactly one `wayfinder:*` type label per child;
- confirm the map remains the sole `wayfinder:map` issue;
- confirm all children are open and unassigned;
- query every child's native `blockedBy` relationship, not body text;
- topologically sort the native graph and compare it with the 50-title order above;
- reject any self-edge, missing child, duplicate child, cycle, or direct blocker already
  implied through another direct blocker;
- reverse-walk from final approval and require all 50 children reachable;
- verify the frontier is exactly the seven titles above;
- verify **Approve the 648-window macro-F1 audit protocol** waits on the metric decision;
- verify **Prototype the approved bounded Optuna lifecycle** waits on the HPO decision
  through model construction/training-host prototypes and is documented as conditional;
- verify serving/mobile does not depend on durable records, while durable records do
  depend on serving/mobile;
- verify the documentation prototype is after ADR/domain-language approval and final
  acceptance is after the documentation prototype;
- verify the map body removes the old hard 26,100-line assertion and the blanket ban on
  named target/objective/feature experiments;
- verify no ticket is closed, assigned, or described as owner-approved during charting.

Graph audit: 50 children; 25 grilling, 14 prototype, 8 task, 3 research; 73 direct
edges; 7 initial-frontier tickets; maximum direct blockers 5 on **Set dependency,
wheel, research-extra, and vulnerability policy**; acyclic; all children reach final
approval; no transitive-only direct blockers.
