# Architecture and implementation documentation audit

Research date: 2026-07-10. Repository revision: `b9b9a53f`.

Status: evidence and candidate routing only. No documentation disposition, theory
interpretation, architecture, ADR disposition, or rewrite is approved here.

Scope: every checked-in `ARCHITECTURE.md` and `IMPLEMENTATIONS.md`, checked against
the current source tree, checked-in configuration, recent history, and the companion
ML/paper audits. The paper, current code, progress notes, archive, and ADRs were all
treated as fallible evidence. No production, guide, ADR, issue, or configuration file
was changed by this audit.

## Verdict

The requested inventory is exactly **46 files and 3,659 lines**:

| Kind | Files | Lines |
|---|---:|---:|
| `ARCHITECTURE.md` | 27 | 1,925 |
| `IMPLEMENTATIONS.md` | 19 | 1,734 |
| Total | 46 | 3,659 |

No singular `IMPLEMENTATION.md` file exists in the current tree.

All 19 implementation guides have a same-directory architecture guide. None of the
46 files contains an internal Markdown link. Only four external URLs occur, all in
two ML implementation guides. Twenty-seven files contain a `Theory`, `Beginner`,
`Beginner Context`, `Beginner Theory`, or `Mental Model` section, but only two contain
a references section. The result is broad coverage without a dependable learning
path: concepts are repeated in small fragments, while decisive assumptions, exact
equations, code locations, paper provenance, and limitations are absent.

No file merits an unchanged `retain` disposition. That does not mean all content is
bad. Much is accurate and useful. It means every file fails at least one required
gate: current factual accuracy, navigability, code linkage, source attribution,
beginner pedagogy, low duplication, or stability through the proposed clean break.

The lean route is not to expand all 46 files. It is to:

1. write one beginner journey through the temporal ML pipeline;
2. write one exact semantics/explanation guide and one compact contract reference;
3. keep local architecture guides only for deep modules whose interface, invariants,
   and failure policy are not obvious from source;
4. merge or retire every implementation catalog that restates its neighboring guide
   or the directory tree;
5. generate current config inventories through the CLI instead of hand-maintaining
   lists; and
6. author the final guides only after the owner approves the clean-break semantics.

This would leave roughly 13 existing architecture-guide locations, add three central
learning/reference documents and one currently missing serving guide, and remove the
parallel `IMPLEMENTATIONS.md` taxonomy. The exact count is an owner decision, not an
approved target.

## Method and evidence

Every file was read in full. Claims and module maps were compared with production
Python under `src/spice`, all packaged YAML under `src/spice/conf`, tests where they
clarify intended behavior, and the two commits after the last broad documentation
refresh. `e804880b` is the most recent broad ML/doc refactor; `4b90a951` and
`b9b9a53f` subsequently added block-window evaluation and block-Poisson replay without
updating the guide set.

The current-row history was also checked rather than inferred from current code.
Commit `e0b2e68e`, [`PROGRESS.md`](../../../PROGRESS.md), and
[`ARCHIVE.md`](../../../ARCHIVE.md) show an intentional distinction:

- the removed unsafe comparator exposed finalized facts from block `t` while making
  a decision for that row;
- the retained block-open/current-row path permits `base_fee_per_gas[t]` using a
  parent-derived premise that is exact for Ethereum, fork-dependent on Polygon and
  producer-configurable after Lisovo, and state/timestamp-dependent on Avalanche; and
- finalized block-`t` facts such as gas use and transaction count are lagged to
  `t-1`.

That is important owner context. It means “offset zero uses the current row” and HPO
must be documented as intentional SPICE extensions, not casually declared accidental
paper deviations. The unresolved issue is that the 46 guides do not state the full
decision instant or reconcile the training/replay row meaning with serving's
`target_block = observed_block + offset + 1`. They also treat broad chain/corpus names
as one regime and do not distinguish the last stable **context head** from the current
**actionable head** used to derive the first still-open target. Any semantic change
remains owner-gated.

For information architecture, the audit used the following primary documentation
sources:

- [Diátaxis](https://diataxis.fr/) separates tutorials, how-to guides, reference,
  and explanation by reader need. The current files mix all four.
- [Diátaxis tutorial guidance](https://diataxis.fr/tutorials/) emphasizes a
  concrete, reliable learning journey with visible results. The current beginner
  sections are mostly definitions without an activity or worked result.
- [PyTorch's beginner path](https://docs.pytorch.org/tutorials/beginner/basics/intro)
  presents one complete ML workflow, then links outward to deeper concepts. This is
  a better shape for SPICE than asking a new reader to traverse dozens of local files.
- [scikit-learn's leakage guidance](https://scikit-learn.org/stable/common_pitfalls.html)
  distinguishes fitting transforms on training data from applying them elsewhere.
  SPICE's guides state the scaler rule, but do not provide an end-to-end information
  set and split-horizon proof.
- [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html)
  explicitly scopes reproducibility by platform and release. SPICE needs the same
  precision instead of presenting a seed/determinism flag as a blanket guarantee.

## Confirmed stale, false, or materially incomplete claims

| Guide claim or omission | Current evidence | Documentation consequence |
|---|---|---|
| The top-level guide indexes `src/spice/objectives/ARCHITECTURE.md` and an active objective domain. | `src/spice/objectives` contains only stale `__pycache__`; production objective code was removed in `e804880b`. | Remove the path and explain the still-unapproved total-loss versus economic-selection decision instead of preserving a ghost module. |
| Serving is absent from both top-level architecture maps. | `src/spice/serving` contains config, live-block acquisition, inference, analytics, schemas, and a FastAPI interface. | Add a serving protocol/trust guide after its semantics and storage are approved. |
| Feature/history prose treats “current base fee is deterministic from the parent” as cross-chain. | This is Ethereum-exact. Polygon requires fork-specific parameters and is producer-configurable after Lisovo. Avalanche ACP-176/226 requires dynamic parent state and child timestamp; the canonical schema lacks the exact state and post-Granite millisecond time. | Every retained feature needs `chain_regime`, `available_at`, and `exact_or_estimate`; a chain-generic claim is not sufficient. |
| Broad corpus names imply one fee/cadence regime. | Current Ethereum coverage crosses Pectra/Fusaka, Polygon crosses several forks including Lisovo, and Avalanche crosses Octane/Granite. | Record protocol boundaries in provenance and explain whether experiments split, stratify, or knowingly aggregate regimes. |
| Serving's confirmed context is treated as the target clock. | With `confirmation_depth = 2`, latest head `L` yields context head `L-2`; the reported baseline and offset-zero target are `L-1`, which is already closed. | Serving documentation must separate context head, actionable head, and first actionable target and prove their mapping with a small fixture. |
| `conf/IMPLEMENTATIONS.md` lists one corpus, three chains, one evaluator, and seven benchmarks as the current concrete inventory. | The tree has 6 corpus specs, 4 chains, 3 evaluator configs, 23 benchmark specs, and 22 evaluation suites. | Retire hand-maintained inventories; link to `spice config list` or a generated table. |
| Config implementation says evaluation windows use UTC timestamp ranges. | `BlockWindowSpec` and `RuntimeEvaluationWindowSpec` now support block windows, especially through benchmark resolution. | Explain timestamp and block selection separately, including that the public CLI still authors timestamp windows. |
| Dataset-builder implementation says inference normalizes only an inclusive timestamp coverage to a half-open timestamp window. | `CompiledInferenceDatasetPreparationRequest` now accepts exactly one `SampleTimestampWindow` or `SampleBlockWindow`. | Replace the timestamp-only claim and teach half-open boundaries with one concrete example. |
| Temporal architecture's problem-store field list omits block numbers. | `CompiledProblemStore.block_numbers` and `sample_block_numbers()` were added for block-window replay. | Update the shape/units reference; block number and timestamp are distinct axes. |
| Evaluation architecture says “two concrete evaluator specs” but shows one populated YAML block and one empty block. | Registry behavior is two evaluator semantics: time-Poisson and block-Poisson. Three checked-in ids exist because `block_poisson_replay_300` aliases the block adapter with another recipe. | Explain adapter versus recipe id; remove the malformed empty example. |
| Evaluation implementation describes only time-based `poisson_replay`. | `block_poisson_replay.py`, two configs, tests, and quartile benchmark suites are current. | Add block-index replay semantics, assumptions, and selection shapes only after metric semantics are approved. |
| Execution-policy implementation defines optimum as the minimum-fee row “inside the candidate window.” | `reachable_end_rows = min(candidate_end, candidate_start + action_width)`; `_reachable_optimum()` searches only that reachable prefix. | Use “reachable optimum,” show when the physical time window is shorter or longer than action width, and define overflow separately. |
| Evaluation guides inherit the same broad “optimum” wording. | Temporal accounting receives policy-produced reachable optimum rows, not necessarily the full physical timestamp-window minimum. | Metric names and equations must name the comparison set exactly. |
| `exact_optimum_hit_rate` is described as an exact economic optimum match. | It compares row identity. `np.argmin` chooses the first equal-fee minimum, so another equal-cost row is counted as a miss. | State tie policy and distinguish row hit from equal-cost hit; owner decides which diagnostic survives. |
| Prediction implementation calls the current custom value simply `macro_f1`. | SPICE skips every class with zero target support, even if predicted. TorchMetrics 1.9 uses union-active behavior, so predicted-only classes contribute zero. | The earlier suspected TorchMetrics bug is cleared. Current SPICE is the nonstandard variant. Delete the metric or name/define it exactly; do not imply standard macro F1. |
| Prediction docs describe class-weighted CE and epoch `total_loss` without reduction semantics. | PyTorch's weighted mean divides by summed target weights, while SPICE multiplies each batch mean by batch size before epoch accumulation. The reported value is batch-partition-dependent. | Document exact numerator/denominator only if the formulation survives; current checkpoint/HPO interpretation must not be taught as settled. |
| The fee head is described as a minimum-log-fee scalar. | Its raw model output is trained against a normalized log-fee target and is denormalized only for diagnostics; decode and serving ignore it. | Call it an auxiliary normalized regression output, explain the fitted statistics, and label operational non-use. |
| “Chronological split” is presented as sufficient leakage protection. | Anchor positions are contiguous, but future outcome horizons can cross internal train/validation and validation/test boundaries. The external cutoff does check complete outcomes. | Teach input overlap versus label-horizon overlap. The purge/no-purge decision is theory- and owner-gated. |
| The observed-time compiler is called online-safe without qualification. | `recent_median` spacing is fitted from the complete feature table before the internal split. | State that nominal and fitted spacing have different information sets; remove the absolute claim unless the fitted-statistic timing is approved. |
| Feature guide says the safe catalog “improved the 1M A/B grid” without linking evidence. | The claim lives in progress/benchmark history, not in the guide or a stable result record. | Every experiment-backed design claim needs a named benchmark artifact, revision, scope, and limitation. |
| Feature guide lists groups but not formulas, units, lookback spans, or availability for each output. | The default config selects 45 outputs whose block/time units and warmup rules differ. | A beginner cannot audit causality or effective history. Add one canonical feature table or reduce the feature set; do not repeat formula prose across guides. |
| Fixed-sequence docs describe a seconds lookback as though it remains the model input window. | The builder converts it to a clipped row count using a median cadence, then uses exactly that many inclusive rows. Engineered rolling features can reach further back. | Distinguish authored duration, calibrated row count, actual timestamp span, and total raw-feature history. |
| Modeling docs say deterministic training behavior without defining its scope. | The configured seed is set in runtime planning after model construction; PyTorch itself does not guarantee cross-version/platform reproducibility. | State precisely what is seeded and when. Do not promise reproducible weights until initialization timing is fixed or explicitly accepted. |
| Training docs explain best-state policy but omit exact-resume limits. | A reconstructed DataLoader sampler restarts its epoch counter; native Lightning resume does not recover that custom permutation state. | Separate recoverable fit continuation from bitwise/exact continuation. |
| Storage guides present root-local SQLAlchemy/SQLite, WAL, catalog, and mutable study state as settled architecture. | Those are exactly the clean-break persistence questions under investigation. | Preserve current-state facts in the research record, but write normative storage guides only after root/persistence decisions. |
| None of the 46 files links to code. | Internal Markdown-link count is zero. Module maps are plain text and symbol names are unlinked. | Every surviving guide needs relative links to its interface and principal implementation, without duplicating source listings. |
| Paper facts, SPICE refinements, experiment findings, framework behavior, and hypotheses use the same declarative voice. | Only two files have theory references; no guide cites the ICDCS paper or labels HPO/current-row behavior as extensions. | Add evidence labels and an explicit limitations section. ADR text alone is not proof. |

The companion
[`temporal-paper-alignment-audit.md`](temporal-paper-alignment-audit.md) and
[`temporal-preprocessing-theory-audit.md`](temporal-preprocessing-theory-audit.md),
together with the finalized
[`temporal-chain-fee-protocol-audit.md`](temporal-chain-fee-protocol-audit.md),
contain the detailed ML evidence. Their candidate semantic changes remain subject to
the owner correction above: current-row offset zero and HPO are intentional extensions.
The documentation task is to make their information sets and rationale explicit, then
verify cross-layer parity, not to silently revert them to the paper.

## Why the current split is expensive to learn and maintain

The architecture/implementation distinction sounds clean but does not produce deep
documentation modules. In most pairs, the architecture file describes purpose, flow,
invariants, and extension points; the implementation file repeats the same flow with a
directory catalog, failure table, and slightly more concrete names. Deleting the latter
would usually move little knowledge back into callers because the source already owns the
concrete names. By the codebase-design deletion test, many implementation guides are
shallow pass-through documentation.

The split creates four recurring costs:

1. **Duplicate truth.** Workflow resolution, root facts, temporal facts, and decoded
   results recur at package, subpackage, root, and README levels.
2. **Fragmented prerequisites.** A reader meets `Action Space`, `Temporal Capability`,
   logits, scaling, and replay aggregation in different files without a single ordered
   curriculum.
3. **Unequal volatility.** Current YAML ids and module maps change quickly, while causal
   timing and metric equations should change rarely. They are stored together and age at
   the faster rate.
4. **False confidence.** Short “Theory” paragraphs make custom decisions look standard
   without showing alternatives, exact formulas, evidence, or limitations.

The deep-module rule for documentation should be: one local guide earns its existence
when a caller or maintainer must understand a compact interface plus substantial hidden
behavior. A registry or directory listing alone does not earn another document.

## Candidate layered information architecture

This is a candidate route, not an approved rewrite.

### Layer 1: orientation

`README.md` should answer only: what SPICE studies, what is in scope, how to run one safe
smoke path, and where to learn next. `ARCHITECTURE.md` should show the stable end-to-end
module map, dependency direction, root concepts, and links to surviving local guides.

The adjacent README is outside the 46-file matrix, but it must be included in the final
ticket. It currently advertises removed objective/evaluator/normalization ids and an old
output layout, so a correct architecture rewrite with a stale first page would still fail.

### Layer 2: one beginner journey

Create `docs/learn/temporal-ml-walkthrough.md`. It should follow one tiny example from
canonical rows to a decoded decision and metric. The example must use a final, approved
decision clock; until then it should display the competing interpretations rather than
choose silently.

One useful fixture shape is:

```text
6 chronological block rows
  -> 4 approved causal features per row
  -> one 3-row context
  -> context head + actionable head + first actionable target
  -> one 3-action outcome set
  -> input [B=1, T=3, F=4]
  -> logits [B=1, A=3]
  -> decoded action
  -> baseline / realized / reachable-optimum fees
  -> one exact metric calculation
```

At every arrow, show values, shape, dtype, unit, time availability, and the source
interface. The exercise should produce visible expected output, following the structure
of PyTorch's official complete beginner workflow rather than a glossary-only tour.

### Layer 3: explanation and theory

Create `docs/explanation/temporal-decision-and-learning-semantics.md`. It should answer
the “why” questions that do not belong in a tutorial:

- What exact instant does a sample represent?
- Which facts are available before, during, and after block `t`?
- For each chain and protocol regime, is `base_fee[t]` exact, estimated, or unavailable
  at decision time, and why are finalized gas/transaction facts from `t` excluded?
- What does offset zero mean in training, replay, and serving?
- Why can the stable context head differ from the actionable head, and how is the first
  still-open target derived?
- What is constrained by seconds, blocks, action width, and deadline policy?
- Why are HPO, the current-row target, extra features, and extra metrics SPICE
  extensions rather than paper requirements?
- Why use chronological roles, and what overlap is allowed?
- What objective does each loss and metric estimate?
- Which results measure model uncertainty, event-sampling variation, or only one chosen
  run?

Each substantive statement should carry one provenance label:

| Label | Meaning |
|---|---|
| **Paper fact** | The paper states it; cite section/page. It is not automatically correct. |
| **SPICE extension** | Intentional project behavior beyond the paper; give rationale, evidence, and approval status. |
| **Framework behavior** | Owned by PyTorch, Lightning, scikit-learn, TorchMetrics, Optuna, or another dependency; cite a versioned official source. |
| **Experiment finding** | Supported by a named benchmark/result artifact and revision; state its population and limits. |
| **Open question** | Plausible but unapproved; do not use declarative architecture voice. |

Regardless of label, any feature or decision-time claim must state its chain/protocol
regime and `available_at` point. Corpus provenance must record material upgrade boundaries
rather than treating a broad chain/date name as one data-generating rule.

### Layer 4: compact exact reference

Create `docs/reference/ml-contracts.md`. This is the one source of truth for:

- symbols (`N`, `T`, `F`, `A`, row, sample, event, run);
- `latest_rpc_head`, stable `context_head`, `actionable_head`, and
  `first_actionable_target`, without assuming they are the same block;
- arrays/tensors with shapes, dtypes, units, and alignment key;
- per-feature `physical_source`, `available_at`, `chain_regime`,
  `exact_or_estimate`, offline/live constructors, and parity evidence;
- interval conventions and tie rules;
- split and cutoff rules;
- scaler fit population and transform rule;
- loss formulas, component coefficients, and reduction denominators;
- metric formulas, direction, aggregation population, zero-division policy, and
  limitations;
- artifact facts required to reconstruct inference.

This reference should link to source and official dependency documentation. It should not
teach the workflow or list every current config name.

### Layer 5: local deep-module guides

Keep a local `ARCHITECTURE.md` only where the module hides meaningful behavior behind a
small interface. The candidate survivors are acquisition, benchmarks, config, corpus,
evaluation, execution, features, modeling, prediction, storage, temporal, workflows, and
new serving. Each should contain only:

1. purpose and caller-facing interface;
2. invariants, ordering constraints, and errors;
3. dependencies and genuine seams/adapters;
4. one data-flow diagram if it clarifies behavior;
5. stable links to source and the central theory/reference guide; and
6. what the implementation intentionally hides.

No local `IMPLEMENTATIONS.md` is needed. Current ids should come from config commands;
module maps should come from source links; theory should have one owner.

## Exact 46-file disposition matrix

Definitions:

- `amend`: keep this path as a surviving deep-module guide, but rewrite its scope.
- `merge`: move unique content into the named surviving guide/reference, then delete it.
- `retire`: source, CLI help, or a parent guide is clearer; do not replace one-for-one.
- `create-after-clean-break`: the subject remains important, but current semantic or
  persistence decisions are too unsettled for a normative rewrite now.

| # | File | Candidate disposition | Reason / destination |
|---:|---|---|---|
| 1 | `ARCHITECTURE.md` | `create-after-clean-break` | Rewrite as the linked stable system map; remove ghost objectives and add serving only after approved seams. |
| 2 | `src/spice/ARCHITECTURE.md` | `merge` | Duplicates the root map; move any package-only dependency facts into root architecture. |
| 3 | `src/spice/acquisition/ARCHITECTURE.md` | `amend` | Acquisition/canonicalization is a real external seam; link the pull interface and state capability/finality assumptions. |
| 4 | `src/spice/acquisition/rpc/ARCHITECTURE.md` | `merge` | RPC is one adapter inside acquisition; merge its unique transport contract upward. |
| 5 | `src/spice/acquisition/rpc/IMPLEMENTATIONS.md` | `merge` | Preserve retry/order/failure facts in acquisition guide; source owns class/module catalog. |
| 6 | `src/spice/benchmarks/ARCHITECTURE.md` | `amend` | Planning, persisted run state, dependency edges, collection, and projections form a deep module. |
| 7 | `src/spice/benchmarks/IMPLEMENTATIONS.md` | `merge` | Repeats the plan/ledger/index story; merge exact durable-file contracts into benchmark architecture. |
| 8 | `src/spice/cli/ARCHITECTURE.md` | `merge` | Move the operator-edge/default rule to root architecture and README; CLI help owns commands. |
| 9 | `src/spice/cli/commands/ARCHITECTURE.md` | `retire` | Directory grouping and selector distinction are visible in command modules and root operator docs. |
| 10 | `src/spice/cli/commands/IMPLEMENTATIONS.md` | `retire` | Hand-maintained command tables duplicate `spice --help` and stale quickly. |
| 11 | `src/spice/conf/ARCHITECTURE.md` | `merge` | Declarative-config principles belong in config architecture. |
| 12 | `src/spice/conf/IMPLEMENTATIONS.md` | `retire` | Current inventory is already stale; use config-list commands/generated output. |
| 13 | `src/spice/config/ARCHITECTURE.md` | `amend` | Resolution/hydration/coercion is deep; explain raw, typed, and compiled boundaries once. |
| 14 | `src/spice/config/IMPLEMENTATIONS.md` | `merge` | Substantially repeats config architecture and contains the false timestamp-only evaluation rule. |
| 15 | `src/spice/core/ARCHITECTURE.md` | `retire` | A catalog of small helpers is shallow documentation; root dependency rules plus docstrings suffice. |
| 16 | `src/spice/corpus/ARCHITECTURE.md` | `amend` | Canonical data, capability planning, validation, and committed materialization form a deep module. |
| 17 | `src/spice/corpus/IMPLEMENTATIONS.md` | `merge` | Move schema/validation/coverage facts into one corpus guide or generated schema reference. |
| 18 | `src/spice/evaluation/ARCHITECTURE.md` | `create-after-clean-break` | Keep a future evaluator interface guide only after decision clock, replay, and metric semantics are approved. |
| 19 | `src/spice/evaluation/IMPLEMENTATIONS.md` | `merge` | Move exact approved formulas to ML reference and adapter facts to future evaluation architecture. |
| 20 | `src/spice/execution/ARCHITECTURE.md` | `amend` | SSH/Slurm/transfer are genuine external seams; link supported interfaces and trust assumptions. |
| 21 | `src/spice/execution/IMPLEMENTATIONS.md` | `merge` | Merge target-independent behavior upward; target values stay in checked-in config. |
| 22 | `src/spice/features/ARCHITECTURE.md` | `create-after-clean-break` | Feature causality is central, but outputs/formulas/fingerprints await leanness and compatibility decisions. |
| 23 | `src/spice/modeling/ARCHITECTURE.md` | `create-after-clean-break` | Keep the future runtime/training interface guide after framework, seed, resume, and selection choices. |
| 24 | `src/spice/modeling/IMPLEMENTATIONS.md` | `merge` | Move tensor contracts to ML reference and approved fit behavior to modeling architecture. |
| 25 | `src/spice/modeling/dataset_builders/ARCHITECTURE.md` | `retire` | The public builder abstraction is already gone; one internal path does not earn a package guide. |
| 26 | `src/spice/modeling/dataset_builders/IMPLEMENTATIONS.md` | `retire` | Move split/sequence/scaler semantics to central preprocessing theory/reference. |
| 27 | `src/spice/modeling/families/ARCHITECTURE.md` | `merge` | Family construction is a real adapter set but can live in modeling architecture. |
| 28 | `src/spice/modeling/families/IMPLEMENTATIONS.md` | `merge` | Move minimal beginner architecture theory to the learning guide; link official LSTM/Transformer sources. |
| 29 | `src/spice/prediction/ARCHITECTURE.md` | `create-after-clean-break` | Keep only if the final target/loss/decode module earns a distinct interface after simplification. |
| 30 | `src/spice/prediction/families/ARCHITECTURE.md` | `retire` | One family plus a generic checklist is a hypothetical seam and duplicate layer. |
| 31 | `src/spice/prediction/families/IMPLEMENTATIONS.md` | `merge` | Merge decoded-result and metric facts into prediction architecture/reference. |
| 32 | `src/spice/prediction/families/min_block_fee_multitask/ARCHITECTURE.md` | `retire` | Thirty-one lines add another abstraction level without unique interface knowledge. |
| 33 | `src/spice/prediction/families/min_block_fee_multitask/IMPLEMENTATIONS.md` | `merge` | Move approved target/loss equations and ablation status into one ML reference/explanation owner. |
| 34 | `src/spice/storage/ARCHITECTURE.md` | `create-after-clean-break` | Root identity, layout, mutability, persistence, and discovery are still clean-break decisions. |
| 35 | `src/spice/storage/IMPLEMENTATIONS.md` | `merge` | Preserve current-state migration evidence; write final implementation facts only in future storage architecture. |
| 36 | `src/spice/storage/catalog/ARCHITECTURE.md` | `retire` | Catalog is an implementation candidate, not a durable conceptual domain. |
| 37 | `src/spice/storage/catalog/IMPLEMENTATIONS.md` | `retire` | Source/schema and future storage guide are clearer; do not preserve a projection-specific guide automatically. |
| 38 | `src/spice/temporal/ARCHITECTURE.md` | `create-after-clean-break` | This should become the authoritative temporal decision interface after timing/action semantics are owner-approved. |
| 39 | `src/spice/temporal/compilers/ARCHITECTURE.md` | `merge` | Compiler geometry is part of one temporal module, not a separate reader journey. |
| 40 | `src/spice/temporal/compilers/IMPLEMENTATIONS.md` | `merge` | Move exact interval/action-width rules to temporal guide and ML contract reference. |
| 41 | `src/spice/temporal/execution_policy/ARCHITECTURE.md` | `merge` | Policy is an internal seam whose interface belongs in temporal architecture. |
| 42 | `src/spice/temporal/execution_policy/IMPLEMENTATIONS.md` | `merge` | Move baseline/reachable optimum/overflow equations to one reference owner. |
| 43 | `src/spice/temporal/input_normalization/ARCHITECTURE.md` | `merge` | Scaling is preprocessing theory plus a small interface; centralize it. |
| 44 | `src/spice/temporal/input_normalization/IMPLEMENTATIONS.md` | `merge` | Preserve unique-row fit population and zero-variance rule in ML reference. |
| 45 | `src/spice/workflows/ARCHITECTURE.md` | `amend` | One orchestration/effect-boundary guide is useful if it stays small and links owner modules. |
| 46 | `src/spice/workflows/IMPLEMENTATIONS.md` | `merge` | Repeats the four workflow flows; merge failure/effect facts into workflow architecture. |

## Undergrad-friendly content contract

Every new ML guide should pass this rubric. “Mentions the term” is not a pass.

| Gate | Pass condition |
|---|---|
| Prerequisites | States assumed Python, linear algebra, probability, and deep-learning knowledge; links to focused primary introductions instead of silently assuming it. |
| Learning objective | Starts with what the reader will be able to trace or calculate, not a directory description. |
| Vocabulary | Defines row, block, anchor, context, sample, action, candidate, outcome, event, replay run, epoch, logit, loss, metric, and artifact before use. |
| Time model | Shows one timeline with the exact decision instant, stable context head, actionable head, first actionable target, and facts available at each point. Block-open/current-row rationale and serving parity are explicit. |
| Worked example | Carries the same small numeric example through preprocessing, shapes, targets, loss/decode, and evaluation. Expected values are shown. |
| Shapes, units, and availability | Every array/tensor has named axes, dtype, unit, alignment key, inclusive/exclusive convention, chain/regime scope, and `available_at` point. |
| Equations | Defines symbols, domains, reduction population, numerator, denominator, coefficient, tie rule, zero-division rule, and direction. |
| Leakage argument | Enumerates every fitted or selected value and proves which role/data interval supplies it. Distinguishes causal context overlap from future-label overlap. |
| Paper alignment | Labels exact paper facts, intentional extensions such as HPO/current-row behavior, and unresolved differences. Includes section/page citations. |
| Framework alignment | Links versioned official behavior for library-owned algorithms; states what custom code changes. |
| Evidence | Links every benchmark-backed claim to a named result, corpus/window, protocol regimes, revision, and uncertainty scope. |
| Simplicity rationale | Says why each custom abstraction or metric earns its teaching/maintenance cost and names the simpler rejected candidate. |
| Limitations | States what base fee omits, what replay randomness measures, what one seed/day cannot establish, and what serving does differently. |
| Code navigation | Links the caller-facing interface, concrete implementation, config, and focused tests. No copied source listing. |
| Freshness | Dynamic ids/counts are generated; no manual catalog duplicates CLI/source. |
| Reader verification | A new reader can answer the checkpoint questions below without opening unrelated guides. |

Reader checkpoint questions:

1. At the decision instant, which values for block `t` are exact, estimated, or unavailable
   on each supported chain/regime, and why?
2. What are the context head, actionable head, first actionable target, and offset-zero
   meaning in preprocessing, offline replay, and live serving?
3. For one sample, which rows become input, target candidates, baseline, realized result,
   and reachable optimum?
4. Which statistics are fitted on training data, and which are fixed configuration?
5. Can a training outcome cross a validation boundary under the approved split rule?
6. What exact quantity does `total_loss` average, and is it invariant to batch partition?
7. Which classes contribute to any retained macro metric?
8. Does “profit” mean full transaction profit, base-fee-per-gas savings, or something else?
9. What randomness is repeated in evaluation, and what uncertainty is not measured?
10. Which choices come from the paper, which are intentional SPICE extensions, and
    which remain open?

## Ticket-ready owner gates

These are proposed map nodes. They approve nothing by their existence.

### Approve the documentation information architecture

Decide whether to replace the 46-file pair taxonomy with the layered route above.
Acceptance requires an owner-approved survivor list, merge destinations, and a rule that
current id inventories come from code/CLI. No deletion occurs in this ticket.

### Approve the temporal decision clock and block-open information set

Write and approve one block-by-block example covering training, replay, and serving.
Preserve the intentional current-row extension unless the owner explicitly changes it.
Acceptance requires the decision instant, availability of `base_fee[t]`, lag of finalized
facts, per-chain/regime `available_at` table, offset-zero meaning, context/actionable heads,
first eligible inclusion block, baseline, deadline, and serving mapping. The fixture must
show that `confirmation_depth = 2` cannot target already closed blocks. This blocks all
normative ML documentation.

### Approve preprocessing and split semantics

Choose the unit of context/action, fitted spacing policy, duplicate/invalid-row policy,
feature set/units, scaler population, and label-horizon boundary rule. Acceptance includes
one causal feature table with chain/regime availability and one split example. It must
state how broad corpora crossing protocol upgrades are represented or scoped. HPO remains
an intentional extension and must be described, not removed by implication.

### Approve training and objective semantics

Choose the prediction heads, class weighting, loss coefficients, exact full-epoch
reducers, seed timing, checkpoint/resume guarantee, early stopping, and HPO selection
metric. Acceptance requires a batch-partition invariance result for any retained epoch
loss and an explicit economic-versus-predictive selection rationale.

### Approve metric and replay semantics

For every retained metric, approve the name, formula, unit, aggregation population,
direction, tie/zero rule, and interpretation. Explicitly decide whether to delete custom
macro F1 or adopt a standard implementation. Approve time-Poisson versus block-Poisson
roles and what their repetitions estimate.

### Approve paper/refinement provenance labels

Build a short paper-to-SPICE table with page citations. Mark current-row behavior, HPO,
expanded features, shorter-delay reuse, extra metrics, and block replay as intentional
extensions where applicable. Add the per-chain/regime fee-availability verdict and corpus
upgrade boundaries. Record limitations and evidence. Old ADRs and progress notes may
support history but cannot independently approve the result.

### Rewrite and merge guides after the clean break

Execute the approved 46-file matrix only after the semantic and architecture tickets are
closed. Use relative code links, central equations, and no manually duplicated id catalog.
Preserve historical rationale in one history/provenance location rather than scattering it
through current architecture.

### Synchronize adjacent entry points

Update `README.md`, `CONTEXT.md`, `ARCHIVE.md`, and any surviving ADR references together
with the new map. Acceptance requires no removed objective/evaluator/normalization ids, no
obsolete output layout, and no contradiction between current architecture and historical
evidence.

### Verify with an undergraduate reader and source audit

Have the intended reader follow the tiny end-to-end example and answer all ten checkpoint
questions. Separately check every link, symbol, config example, tensor shape, equation,
`available_at` claim, protocol regime, and context/actionable-head mapping against the
final source. Run the documented commands in a clean environment. Record confusing terms
and revise once. This is the final documentation approval gate, not a rubber-stamp after
writing.

## Recommended sequencing

```text
decision clock / block-open information set
        |
        +--> preprocessing and split semantics
        +--> training and objective semantics
        +--> metric and replay semantics
        |
        v
paper versus SPICE provenance table
        |
        v
documentation information architecture approval
        |
        v
clean-break implementation settles interfaces
        |
        v
guide merge/rewrite + adjacent entry-point sync
        |
        v
source audit + undergraduate reader verification
```

The key ordering rule is simple: do not make polished teaching material out of an
unapproved semantic contract. Keep the current guides as current-state evidence during
the investigation, then replace them in one clean documentation break after the code and
theory choices are approved.
