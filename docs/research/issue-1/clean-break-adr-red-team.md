# SPICE clean-break ADR and glossary red-team

Research date: 2026-07-10. Checkout: `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`.

Scope: adversarial review of every accepted ADR, `CONTEXT.md`, the clean-break candidate, current production code, tests, and the git history that introduced or deepened the contested modules. This is evidence for Wayfinder decisions. It does not approve, supersede, or edit an ADR.

## Bottom line

The candidate route is directionally right, but it is not ready to become an implementation plan. It preserves the important behavior while deleting much implementation vocabulary. Four choices still require explicit human approval:

1. root identity, address, and direct-discovery shape;
2. schema-owned config hydration and file loading;
3. removal of one-implementation dispatch while retaining the concrete temporal, execution-policy, tensorization, and prediction modules;
4. retention or replacement of the custom Execution Session.

The old ADRs are not a coherent veto. ADR 0001 contains durable exact-root and manifest-first invariants but binds them to a catalog and deterministic producer identities. ADR 0002 correctly separates fresh resolution from snapshot loading, but its owner-coercer machinery is no longer the leanest way to enforce that distinction. ADR 0003 is factually stale: production code already removed its registry and durable representation identity. ADR 0004's deletion tests assumed the catalog, config-derived producer identity, and benchmark ledgers that the candidate deletes. ADR 0005 still has the strongest deletion-test result, but its catalog-transfer consequence is obsolete and its package comparison should be rerun against current Slurm machine-readable interfaces.

`CONTEXT.md` is mostly an architecture inventory, not a domain glossary. It has 67 defined terms. Git blame ties most of the storage, benchmark-ledger, runtime-plan, and dispatch vocabulary directly to the May 2026 deepening refactors. A clean break should retain behavior and genuine research language, not names for modules that no longer exist.

## Source discipline

Local evidence is cited as current file/line ranges or introducing commits. The main history points are:

- [Root-ID consumer workflows](https://github.com/edoski/spice/commit/1c987f3a2) introduced ADR 0001 and exact existing-root intent.
- [Centralize workflow root materialization](https://github.com/edoski/spice/commit/2c0929b9) and [complete root materialization locality](https://github.com/edoski/spice/commit/81dcace1) concentrated catalog lookup, identity derivation, and handle construction.
- [Split resolved workflow hydration](https://github.com/edoski/spice/commit/a96e31f4) introduced ADR 0002 after deleting a generic coercion path.
- [Consolidate typed config group loading](https://github.com/edoski/spice/commit/ff63f507) introduced the shared group catalog plus a separate typed facade.
- [Representation seam retained](https://github.com/edoski/spice/commit/5fde266d) introduced ADR 0003. [Split representation adapter](https://github.com/edoski/spice/commit/ce503d6b) then added its protocol and registry.
- [Clean-break core training stack](https://github.com/edoski/spice/commit/725c9156) later deleted that protocol, registry, and persisted representation semantics without spreading tensorization into model families.
- [Localize compiler geometry](https://github.com/edoski/spice/commit/d6413320) moved temporal-window construction into the observed-time-window implementation.
- [Clarify prediction target ownership](https://github.com/edoski/spice/commit/ce9277fe) concentrated Action Space, temporal outcomes, prediction targets, and decode ownership.
- [Deepen execution provenance and transfer](https://github.com/edoski/spice/commit/c94018a2) concentrated job provenance and root-shaped transfer behavior.
- [Custom Execution Session retained](https://github.com/edoski/spice/commit/0d8a5a1b) introduced ADR 0005.

External claims use owning documentation: [Pydantic discriminated unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions), [Pydantic `TypeAdapter`](https://docs.pydantic.dev/latest/api/type_adapter/), [Submitit](https://github.com/facebookincubator/submitit), [Fabric connections](https://docs.fabfile.org/en/stable/api/connection.html), [AsyncSSH](https://asyncssh.readthedocs.io/en/stable/), [Slurm REST](https://slurm.schedmd.com/rest.html), [`sbatch --parsable`](https://slurm.schedmd.com/sbatch.html#OPT_parsable), [`squeue` JSON and polling guidance](https://slurm.schedmd.com/squeue.html), [`sacct` JSON](https://slurm.schedmd.com/sacct.html), [OpenSSH client configuration](https://man.openbsd.org/ssh_config), and [rsync archive/incremental behavior](https://download.samba.org/pub/rsync/rsync.1).

Recommendations below are proposals. Every section ends with the human decision still required.

## Behavioral invariant ledger

### Root identity, materialization, and persistence

Evidence:

- Existing-root consumers use exact IDs instead of reconstructing producer configuration. This was the useful change in ADR 0001 and remains visible in tune, train, and evaluate config fields.
- Evaluation is manifest-first. `prepare_artifact_inference_context` loads the artifact and corpus manifests, rejects a chain mismatch, rebuilds feature/problem/prediction contracts from artifact semantics, validates feature fingerprints and prerequisites, checks delay capability, training cutoff, and corpus coverage, then prepares scoring (`src/spice/modeling/artifact_inference.py:79-192`).
- The current materializer does more than path building. It derives config-hashed producer IDs, resolves catalog records, constructs handles, and emits benchmark-only scalar facts (`src/spice/storage/workflow_root_materialization.py:37-442`). Its supporting handle types duplicate storage root, ID, name, chain, root path, state DB path, and derived child paths (`src/spice/storage/workflow_roots.py:25-217`).
- Canonical paths are already pure functions of storage root, chain, and ID (`src/spice/storage/layout.py:19-32`). Catalog materialization exists to reject catalog/path/manifest disagreement, not because the path formula is complex (`src/spice/storage/catalog/materialization.py:37-98`).
- Current identity machinery is large because study and artifact IDs hash broad config payloads (`src/spice/storage/identity.py:31-272`; `src/spice/storage/ids.py:13-47`). The candidate removes that premise for study, artifact, and evaluation outputs.
- Root publication and deletion also enforce canonical layout, staged promotion, conflict behavior, validation, reindexing, dependency checks, and cleanup. These behaviors must survive even if catalog records, SQL schemas, and handles disappear. The companion persistence review details no-replace, crash durability, dependency races, transfer conflicts, and conversion limits (`docs/research/issue-1/clean-break-persistence-semantics.md`).

Recovered invariants:

- A consumer names an exact existing root; it never reproduces the producer recipe.
- The loaded manifest is authoritative for trained semantics and provenance.
- Cross-corpus evaluation is allowed only when artifact and corpus chains match.
- A workflow output ID exists before benchmark dependencies and submission are frozen.
- Hydration preserves an already-minted output ID; it never mints again.
- Canonical address, manifest kind, ID, chain, and path containment are validated together.
- Hidden stages are not discoverable as promoted roots.
- Publication rejects or proves equality with an existing immutable destination; it never silently replaces it.
- Failed writers preserve only valid resumable stage state.
- Dependency-aware deletion accounts for promoted and active staged consumers.
- Transfer validates source and destination and preserves the primary failure when cleanup also fails.

These invariants do not require a catalog, selector objects, root handles, deterministic study/artifact IDs, or benchmark root ledgers.

### Configuration

Evidence:

- ADR 0002 fixed a real shallow module. Before commit `a96e31f4`, fresh resolution sent already-typed values through the same generic raw coercer used for snapshots. The commit made fresh resolution construct workflow models directly while snapshot loading remained a raw-input boundary.
- Current snapshot loading manually checks workflow markers and allowed fields, selects one of three field dataclasses, reconstructs every nested owner config, and assembles the final model (`src/spice/config/workflow_snapshots.py:83-341`; `src/spice/config/resolved_workflows.py:39-202`). Tests show the actual contract: strict round-trip, concrete nested variant restoration, workflow mismatch rejection, extra-field rejection, and storage-root override (`tests/config/test_workflow_snapshots.py:52-178`).
- Config groups have two caller needs. Operators need mappings for show/edit/seed/YAML; resolution needs validated models. That behavioral distinction is real. The implementation now spans a 267-line metadata/validator catalog, 214-line raw loader/canonicalizer, and 51-line typed alias facade (`src/spice/config/group_catalog.py`, `groups.py`, `typed_groups.py`).
- Pydantic recommends discriminated unions because one member is selected predictably by a literal discriminator. `TypeAdapter` validates and serializes standalone unions. Pydantic also states that a one-variant discriminated union is impossible because Python collapses `Union[T]` to `T`. This supports unions for model/evaluator/workflow alternatives and direct concrete types for single implementations.

Recovered invariants:

- Fresh recipe resolution and durable snapshot hydration are distinct operations.
- Snapshot hydration never re-resolves a Surface and never changes exact root/output IDs.
- Raw persisted input is strictly validated once into the correct concrete workflow and nested variants.
- Config file show/edit/seed paths can obtain canonical mappings without pretending those mappings are executable configs.
- Executable callers receive typed values, not partially validated abstract bases.
- File name and embedded recipe identity agree where the format carries both.
- Contextual tuning-space validity is checked with the selected model and problem.

These invariants do not require owner coercers, `SerializeAsAny`, resolved-field dataclasses, `core.specs`, a typed-groups facade, or handwritten snapshot field assembly.

### Representation, temporal compilation, execution policy, and prediction

Evidence:

- Fixed-sequence tensorization has real locality. `sequence_inputs.py` owns context layout, dense tensor construction, sample-position alignment, and masks (`src/spice/modeling/representations/sequence_inputs.py:19-221`). It is directly called by `batch_plan.py`; no representation registry or persisted representation ID remains in production.
- Commit `725c9156` is a completed deletion test against ADR 0003. It deleted `CompiledRepresentationContract`, `PreparedRepresentation`, `RepresentationRuntimeContext`, the registry, device-storage variants, and representation semantics. Complexity did not reappear in model families. The concrete tensorization module remained.
- Observed-time-window compilation is deep. It owns slot-spacing resolution, capability geometry, history requirements, valid-anchor selection, action width, delay-store reconstruction, and runtime metadata (`src/spice/temporal/compilers/observed_time_window.py`). Commit `d6413320` deleted a generic shared helper and moved geometry into this owner, reducing code while improving locality.
- The temporal compiler registry is 148 lines for one entry and three redispatch operations: config type, compile function, and runtime-metadata codec (`src/spice/temporal/compilers/registry.py`). Deleting that table does not delete the 402-line concrete algorithm.
- Strict-deadline action/outcome behavior is domain logic: full action availability, reachable-action masks, overflow-to-post-window outcomes, optimum rows, and decoded selection validation (`src/spice/temporal/execution_policy/base.py:36-233`; `strict_deadline_miss.py:33-165`). Its dispatch handles one ID (`base.py:235-271`).
- Min-block-fee prediction owns output heads, fitted class/fee state, targets, loss, metrics, and decoding. The current generic contract is an 11-callback bundle used by one family (`src/spice/prediction/contracts.py:105-176`; `families/min_block_fee_multitask/__init__.py:34-104`). The registry validates one family ID with an `if` branch (`src/spice/prediction/registry.py:8-37`).

Recovered invariants:

- Temporal window geometry stays in one temporal-owned module and is reused by acquisition, training, evaluation, and serving.
- The artifact carries enough temporal capability to rebuild compatible evaluation windows and reject action-width/delay mismatches.
- Action availability and strict-deadline overflow semantics are prepared once and shared by targets, decoding, and evaluation.
- Prediction owns target construction, fitted loss state, metrics, output heads, and decoded offsets.
- Tensorization owns model-input layout and copying; model families only consume tensors.
- Unknown persisted algorithms or manifest formats fail closed.

These invariants require deep concrete modules. They do not require registries, abstract config bases, callable contract bundles, or speculative adapters.

### Remote execution

Evidence:

- The current Session owns target configuration, OpenSSH command invocation, remote Python-module execution, rsync, exact Slurm script rendering, job-ID parsing, provenance environment variables, log following, state lookup, and remote revision lookup (`src/spice/execution/session.py:51-357`). Submission and transfer call that interface from several places (`src/spice/execution/submission.py`; `transfer_transaction.py`; `benchmarks/submission.py`).
- Deleting the Session today would spread quoting, target paths, command failure mapping, Slurm provenance, and process cleanup across those callers. It passes the deletion test better than the registries.
- Submitit is a Python-function/command submission abstraction intended to run from an environment with Slurm access. It does not supply SPICE's remote SSH target, rsync staging/promotion, manifest validation, or typed config rewrite. Fabric and AsyncSSH cover SSH commands and SFTP, not Slurm or rsync's incremental/archive semantics. Slurm REST covers scheduler operations only and requires `slurmrestd` deployment and authentication.
- The current implementation still leaves cheap native simplifications unused. `sbatch --parsable` returns a machine-readable job ID, avoiding the regex over `Submitted batch job ...`. Current Slurm exposes JSON for `squeue` and `sacct`, and `squeue --only-job-state` narrows a status query. Slurm warns against tight programmatic `squeue` loops; SPICE currently polls every five seconds (`session.py:208-266`).
- OpenSSH CLI automatically consumes user and system client configuration. Replacing it with an in-process SSH library changes connection lifecycle, host-key handling, and config behavior. rsync's archive mode and delta transfer are stronger matches for immutable root transfer than naive recursive SFTP.

Recovered invariants:

- One explicit target owns remote host identity and remote repo, Python, storage, and log paths.
- Remote commands and arguments are quoted safely and failures include the attempted operator action.
- Submitted jobs return exact job ID, target, task, execution reference, and log path.
- The remote runner receives the exact hydrated workflow snapshot with the remote storage root.
- Benchmark dependencies are forwarded unchanged to Slurm.
- Following is interruptible without canceling the job and cleans up the tail process.
- Root transfer stages, validates, promotes, and cleans up around rsync.
- Benchmark submission records the remote git revision.

No evidence says these invariants must live in one 357-line class or that raw human Slurm output must be parsed.

## ADR verdicts

### ADR 0001: Root-ID Consumer Workflows

Evidence verdict: partly correct, partly obsolete.

Keep the exact-ID consumer, manifest-first evaluation, independent artifact/corpus selection, same-chain rule, and tune-to-tuned-train dependency. Reject its assumption that producer study/artifact identity must be deterministic from broad config, that exact IDs require a catalog, and that old roots should always be regenerated. The candidate explicitly introduces one-shot conversion.

Recommendation: supersede ADR 0001 with a narrower decision after root identity and address are approved. The new ADR should distinguish semantic corpus identity from minted workflow-instance identity and distinguish a root address from a loaded manifest.

Human decision: approve the identity/address alternatives below and explicitly mark ADR 0001 as superseded, amended, or retained. No implementation should infer that disposition.

### ADR 0002: Config Resolution, Hydration, And Loading Seams

Evidence verdict: invariant sound, mechanism overbuilt.

Fresh resolution must remain distinct from hydration. Raw config-file mappings must remain distinct from executable typed configs. Pydantic discriminated unions can now enforce the concrete nested types directly and make most owner coercion and manual field assembly vanish.

Recommendation: retain the behavioral decision but supersede its owner-coercer and separate-module implementation notes. One compact config-file module may expose both raw and typed operations; separate interface behavior does not require separate packages.

Human decision: approve schema-owned discriminated unions and decide whether ADR 0002 is amended or superseded.

### ADR 0003: Representation Seam Retained

Evidence verdict: contradicted by current production code and local history.

The ADR says the registry and persisted representation identity are mandatory. Commit `725c9156` removed both. Repository search finds only the direct fixed-sequence module and its callers. This is not approval to delete further code; it proves that the ADR and implementation have diverged and that its deletion-test claim failed.

Recommendation: retire ADR 0003. Keep fixed tensorization as a focused module. Do not recreate a protocol, registry, or persisted representation ID until a second input representation with a genuinely different contract exists.

Human decision: explicitly approve retirement or require restoration. Do not silently treat the existing code drift as a decision.

### ADR 0004: Compiler, Materialization, And Existing-Root Selection Vocabulary

Evidence verdict: historically coherent, conditional on premises the candidate removes.

Its temporal-locality argument survives: deleting observed-time-window geometry would spread behavior. Its Storage Root Materialization argument does not automatically survive removal of catalog lookup, config-hashed output identity, root handles, and benchmark root ledgers. The current 442-line materializer is deep relative to the current architecture, but much of that implementation disappears when its dependencies disappear. Depth is not inherited across a clean break.

Recommendation: split the decision. Retain owner-local temporal compilation as a concrete module. Retire Storage Selector, Storage Root Materialization, and generic root-handle vocabulary if direct discovery is approved. Keep benchmark planning owner-qualified only if the simplified planner still earns a name.

Human decision: approve the post-break storage seam and then supersede or split ADR 0004.

### ADR 0005: Custom Execution Session Retained

Evidence verdict: strongest old ADR, but not final.

The Session still earns locality across SSH, Slurm, transfer, provenance, and following. Package substitution alone does not remove the whole problem. The catalog-envelope consequence is obsolete under direct discovery, and current Slurm machine-readable CLI/REST options create alternatives not reflected in the ADR.

Recommendation: provisionally retain a smaller OpenSSH/rsync/Slurm facade, use native machine-readable Slurm output, and remove catalog transfer behavior. Reconsider Fabric/AsyncSSH only if persistent concurrent connections or SFTP are required. Reconsider Submitit only with cluster-side control or a Python-function job model. Reconsider Slurm REST only if the university provides and supports it.

Human decision: inspect remote capabilities, compare measured code/operations, then explicitly retain, amend, or supersede ADR 0005.

## Competing architectures

### Root identity and address

#### Architecture A: chain-qualified direct owner functions

Use the candidate's `<kind>/<chain>/<id>` layout. Every existing-root input and transfer carries a small address containing kind, chain, and ID; evaluation also carries its parent artifact ID if evaluations stay nested. Corpus, study, artifact, and evaluation modules each expose direct load/validate/publish/delete functions. Workflows pass manifests and canonical paths, not Root Handles.

Depth: good owner locality, small interfaces. Deletion of a generic storage module does not spread root-kind branching.

Cost: `chain` becomes mandatory address data everywhere. Current `EvaluateConfig` has only artifact and corpus IDs, so the candidate cannot directly compute its proposed paths without adding chain, scanning directories, or restoring an index. `{kind,id,chain}` is also insufficient for `evaluations/<chain>/<artifact_id>/<evaluation_id>.json`.

#### Architecture B: globally unique flat roots

Use `corpora/<corpus_id>`, `studies/<study_id>`, `artifacts/<artifact_id>`, and `evaluations/<evaluation_id>.json`. Chain remains a strict manifest field and part of the semantic corpus hash. Study, artifact, and evaluation UUIDs are globally unique. Exact IDs directly locate every root; evaluation manifests name artifact and corpus dependencies.

Depth: smallest address and transfer interface. It removes chain lookup, parent lookup, duplicate-ID ambiguity, and a reason for a catalog/index.

Cost: less convenient human grouping by chain. Imported legacy IDs must be checked for cross-host collisions or remapped. The human must accept UUID-global identity as the namespace rule.

#### Architecture C: small generic `RootStore`

Keep the chain-qualified layout but centralize `resolve`, `validate`, `publish`, `scan_dependencies`, and `delete` behind `RootRef` and `RootStore`. This is credible if uniform lifecycle behavior materially dominates owner differences.

Depth: one place for containment, hidden-stage filtering, atomic publication, and conflict policy.

Cost: risk of recreating the root-kind registry, generic payload dispatch, and path-bag handles. With one filesystem adapter, its seam is hypothetical. It should be chosen only if a concrete interface sketch is smaller than owner functions.

Recommendation: choose Architecture B for maximum leanness unless chain-grouped paths are an operator requirement. If chain grouping is required, choose A. Do not default to C.

Identity policy is a separate decision. The strongest candidate remains deterministic semantic corpus IDs plus UUID4 study/artifact/evaluation instance IDs. Deterministic all-root IDs conflate reruns and make collision/equality rules harder. UUID corpus IDs make exact reuse require scanning or an index. Output IDs can be minted during fresh workflow-instance resolution, but the operation must be named as instance creation because repeated resolution intentionally produces distinct runs.

Human decision: choose identity policy, minting point, imported-ID policy, and A/B/C. Also decide flat versus parent-nested evaluations.

### Configuration hydration and loading

#### Architecture A: schema-owned unions plus one file module

Define workflow, model, evaluator, and real config alternatives as `Literal`-tagged Pydantic unions. Use one `TypeAdapter` for resolved workflow snapshots. Let each workflow model contain its concrete nested union types. Put config group metadata, path resolution, safe YAML loading, canonical dump, show/edit/seed, and optional typed validation in one file-oriented module.

Depth: Pydantic owns variant dispatch, strict fields, errors, JSON serialization, and round-trip behavior. SPICE owns only domain validation and recipe-file policy.

Locality: adding a real model/evaluator updates its union and constructor table. One-implementation fields use concrete models or literals, not fake unions.

#### Architecture B: runtime group/spec registry

Retain a `GroupSpec`/owner-spec table containing validators and loaders. Snapshots call owner coercers selected at runtime. Raw and typed callers share the table.

Depth: useful only if configuration owners are dynamically extensible or cannot be represented as a closed union.

Cost: current code demonstrates repeated abstract-to-concrete redispatch, `SerializeAsAny`, generic bases, casts, lazy imports, and duplicated validation paths. SPICE's alternatives are a fixed in-repo set.

#### Architecture C: add Hydra or another configuration framework

Hydra would add composition, defaults lists, override syntax, plugin behavior, and its own naming semantics. SPICE already has checked-in YAML recipes and a small override model. No evidence shows a need for Hydra's larger language. `pydantic-settings` targets settings sources rather than a named research-recipe catalog.

Recommendation: A. It directly follows Pydantic's supported union and `TypeAdapter` model and adds no dependency.

Human decision: approve A, B, or C and decide whether recipe names remain outside implementation IDs. The candidate's separation is recommended.

### Representation, temporal, execution-policy, and prediction dispatch

#### Architecture A: direct concrete modules

- `ProblemSpec` directly carries lookback, delay, and a small slot-spacing literal/enum.
- One concrete temporal module compiles observed-time windows and serializes its strict runtime metadata.
- One concrete strict-deadline module prepares Action Space/outcomes and realizes decoded offsets.
- One fixed-sequence tensorization module builds model inputs.
- One min-block-fee prediction module owns heads, targets, fitted state, loss, metrics, and decoded offsets.
- Artifact `format_version` and strict literal fields fail closed. They do not imply runtime plugin registries.

Depth: the algorithms remain deep; only generic dispatch disappears. This matches the completed representation deletion test.

#### Architecture B: keep separate protocols and registries

Keep compiler, execution-policy, representation, and prediction contracts, IDs, runtime metadata codecs, and registry tables. This supports independently varying algorithms.

Depth: justified only when at least two adapters have materially different contracts. Today temporal compiler, execution policy, representation, and prediction each have one implementation. The interface currently mirrors their implementations and forces redispatch at config, compile, persistence, and inference boundaries.

#### Architecture C: one unified temporal-decision strategy

Bundle temporal geometry, action/outcome rules, tensorization, and prediction into one strategy selected by a single ID.

Depth: fewer top-level lookups.

Cost: poor locality. These concerns change for different reasons and have different consumers. Feature/evaluator/model alternatives would couple to a large strategy. This fails the leverage test despite a small nominal interface.

Recommendation: A. Retain module ownership; delete speculative seams. Keep direct dispatch only where alternatives are real: model families, feature sets, and evaluators. A future second temporal or prediction implementation should trigger a new design decision, not prepayment now.

Human decision: approve the exact direct interfaces and formal disposition of ADR 0003/0004.

### Execution Session

#### Architecture A: reduced standard-tool facade

Retain OpenSSH and rsync subprocesses. Expose only workflow-level operations: remote module execution, submit, follow, transfer, and remote revision. Keep Slurm script rendering and provenance internal. Use `sbatch --parsable`; prefer supported JSON or narrow state output; reduce polling. Delete catalog-envelope operations.

Depth: high. Callers learn one target-bound interface while quoting, paths, process cleanup, provenance, and tool errors remain local. No dependency added.

#### Architecture B: split remote transport and scheduler

Create a narrow `RemoteHost` around OpenSSH/rsync and a `SlurmClient` that runs through it. Submission composes them. Tests use fakes for both.

Depth: clearer independent seams if transfer and scheduler really vary. It may help if Slurm REST later replaces CLI while SSH/rsync stays.

Cost: two interfaces and a coordinator for one production adapter each. This can be shallower than the current facade and expose ordering constraints to callers.

#### Architecture C: cluster-side or in-process frameworks

- Submitit becomes credible if SPICE submits from the login node or adopts its Python-function/command job and result-folder model.
- Slurm REST becomes credible if `slurmrestd`, authentication, API versioning, and operations are provided by the university.
- Fabric/AsyncSSH become credible if persistent connections, concurrent remote work, SFTP, or programmatic SSH features are requirements.

None alone replaces root transfer validation, remote environment/provenance, or benchmark collection.

Recommendation: A unless the remote capability inventory proves REST is supported or current subprocess connection overhead is material. B is an internal refactor option, not an automatic improvement. C requires an operational architecture change.

Human decision: choose after the remote capability ticket. ADR 0005 must not decide by inertia.

## Glossary red-team

Evidence: `CONTEXT.md` grew to 67 terms during the April-May architecture deepening. Git blame ties terms such as Storage Root Materialization, four benchmark ledgers/facts, Modeling Runtime Plan, Training Runtime Plan, Temporal Replay Metric Catalog, and Collection Match Facts to the commits that created those modules. This makes the glossary circular evidence: a refactor added a module, then the glossary named it, then the glossary was used to defend the module.

Candidate disposition, pending approval:

Retain as genuine domain/workflow language:

- Surface, Workflow Selection, Workflow Config, Resolved Workflow Snapshot, Config Group, Problem Spec;
- Temporal Capability, Benchmark, Benchmark Case, Benchmark Step, Benchmark Plan Entry, Benchmark Run, Benchmark Collection Snapshot;
- Evaluation Execution Provenance, Corpus Assembly, Artifact Inference Context;
- Action Space, Temporal Outcome Facts, Prediction Target Batch, Decoded Result;
- Temporal Replay and Temporal Accounting;
- Execution Session only if its decision survives.

Redefine because the clean break changes the concept:

- Root Consumer Selection -> exact Root Address or exact existing-root reference, including every field needed to locate it;
- Producer Root Identity -> split into Corpus Definition/Corpus ID and minted Workflow Output ID;
- Temporal Problem Compiler -> concrete observed-time temporal compilation, without implying adapters;
- Feature Catalog -> Feature Set or Feature Contract if those are the actual domain concepts;
- Root Lifecycle -> immutable publication, hidden resume stage, discovery, dependency protection, and archive/delete policy;
- Config Group Loading and Resolved Workflow Hydration -> keep as operations only if repeated discussion needs names, not because files exist;
- Training Runner/Runtime -> name Lightning-owned behavior only where SPICE adds domain policy.

Retire if the candidate route is approved:

- Storage Operator Outcome, Concrete Owner Config;
- Benchmark Selection Ledger, Dependency Ledger, Root Ledger, Root Facts, and current Plan Materialization definition;
- Benchmark Result Index;
- Storage Selector, Root Handle, Produced Root Handle, Storage Root Materialization;
- Storage Transaction, Storage Transfer Transaction, Remote Catalog Record Codec;
- Corpus Capability Planning's bounded-refill definition, Corpus Split Materialization, Split Intent, Staged Split Resume;
- generic Temporal Dataset Preparation Interface if only the concrete fixed preparation remains;
- Batch Plan, Modeling Runtime Plan, Training Runtime Plan, Training Fit Policy, Objective Runtime;
- Temporal Replay Metric Catalog;
- Workflow Command Selection, Benchmark Collection Resolver, Benchmark Collection Match Facts.

Recommendation: do not edit the glossary piecemeal before seam decisions. After approval, rewrite it from observable research/workflow concepts and invariants. Implementation module names belong in architecture docs, not the ubiquitous-language glossary.

Human decision: approve every retained/redefined/retired group as one final glossary/ADR disposition ticket. No term is automatically removed by this review.

## Missed candidates worth adding to the route

1. **Flatten globally unique root paths.** UUID outputs and a chain-bearing corpus hash make `<chain>` redundant for addressing. This removes chain from exact references and fixes direct discovery for ID-only consumers.
2. **Flatten evaluation files.** A globally unique evaluation ID can locate `evaluations/<evaluation_id>.json`; the record carries artifact/corpus references. The candidate's parent-nested layout contradicts its three-field transfer descriptor.
3. **Name exact root addresses explicitly.** If chain-qualified paths stay, every consumer needs chain and evaluation may need parent artifact ID. Plain IDs are not complete addresses.
4. **Use manifest format/version literals instead of plugin identities.** A persisted algorithm literal can fail closed without funding a registry. One top-level manifest format version may be enough for the clean break.
5. **Separate workflow-instance creation from recipe resolution.** Minted UUID output IDs make fresh resolution intentionally nondeterministic. Naming this operation prevents callers from assuming pure resolution.
6. **Prefer owner functions over a generic `RootStore`.** Start with the smallest direct corpus/study/artifact/evaluation modules. Introduce a shared store only after duplicate lifecycle behavior is measured.
7. **Archive-to-trash before destructive GC.** The persistence review's reversible archive candidate may simplify operator deletion and narrow immediate race consequences.
8. **Use Slurm's machine interfaces before adding a package.** `sbatch --parsable`, `squeue --only-job-state`/JSON, and `sacct` JSON can delete parsing code while retaining existing operations.
9. **Measure REST rather than speculate.** If university operations expose `slurmrestd`, compare a tiny REST scheduler adapter with CLI. Otherwise rule it out explicitly.
10. **Make future extensibility evidence-based.** No registry should exist solely for thesis/internship possibilities. A second implementation and a distinct contract are the trigger.
11. **Add a glossary budget/rule.** `CONTEXT.md` should name domain language and durable workflow concepts, not every internal module, record, codec, or ledger.

## Exact Wayfinder tickets

The following are ticket-ready questions. Titles are part of the proposal; dependencies refer to titles, not numbers.

### Choose clean-break root identity and minting semantics

Type: grilling. Initial frontier.

```markdown
## Question

Which identity contract should SPICE adopt for corpus, study, artifact, and evaluation roots: deterministic semantic corpus IDs plus UUID4 workflow-instance IDs, deterministic IDs for every root, or UUIDs for every root; when exactly are output IDs minted and preserved; and must imported legacy study/artifact IDs be remapped or accepted as opaque IDs?
```

### Choose canonical root and evaluation addresses

Type: grilling. Blocked by **Choose clean-break root identity and minting semantics**.

```markdown
## Question

Should canonical storage be chain-qualified (`<kind>/<chain>/<id>`) with chain and any parent IDs present in every exact root address, flat by globally unique ID (`<kind>/<id>`), or mediated by a small index; and should evaluations be flat by evaluation ID or nested under their artifact?
```

### Choose the direct-discovery and lifecycle module seam

Type: grilling. Blocked by **Choose canonical root and evaluation addresses** and the persistence-semantic decisions on atomic publication/deletion.

```markdown
## Question

Should direct discovery, validation, publication, dependency scanning, transfer, and deletion live in root-owner functions or a small generic RootStore; what is the smallest interface that preserves canonical-path validation, hidden-stage exclusion, immutable conflicts, dependency safety, and cleanup without recreating selectors, handles, codecs, or a catalog?
```

### Choose schema-owned workflow and config-file loading

Type: grilling. Initial frontier.

```markdown
## Question

Should SPICE replace owner coercers and handwritten Resolved Workflow Hydration with Literal-tagged Pydantic unions and one TypeAdapter, and consolidate group metadata, YAML IO, canonical raw show/edit/seed, and typed loading into one config-file module; if not, which concrete requirement justifies retaining runtime registries or adding a configuration framework?
```

### Choose concrete temporal-decision module interfaces

Type: grilling. Initial frontier.

```markdown
## Question

What direct interfaces should the single observed-time temporal compiler, strict-deadline execution policy, fixed-sequence tensorizer, and min-block-fee prediction module expose after their registries and abstract bases are removed, and which persisted literals or format versions are needed to fail closed without restoring speculative adapters?
```

### Inventory remote execution capabilities and constraints

Type: research. Initial frontier.

```markdown
## Question

On every supported execution target, which OpenSSH/rsync/Slurm versions and features are available (`sbatch --parsable`, `squeue --only-job-state`/JSON, `sacct` JSON, slurmrestd and authentication), what user SSH-config behavior is required, and do connection or polling costs justify an in-process SSH or REST client?
```

### Choose the remote execution control architecture

Type: grilling. Blocked by **Inventory remote execution capabilities and constraints**.

```markdown
## Question

Should SPICE keep a reduced OpenSSH/rsync/Slurm Execution Session, split remote transport from scheduler control, or adopt a supported cluster-side/REST/SSH framework; which option gives the smallest interface while preserving exact config submission, provenance, dependency forwarding, following, transfer staging, and remote revision lookup?
```

### Approve ADR dispositions and the post-break glossary

Type: grilling. Blocked by all preceding decision tickets.

```markdown
## Question

For each accepted ADR, should it be retained, amended, split, superseded, or retired based on the approved clean-break seams, and which CONTEXT.md terms remain genuine domain/workflow language versus implementation vocabulary that must be removed or redefined?
```

### Freeze the approved invariant and verification contract

Type: grilling. Blocked by **Approve ADR dispositions and the post-break glossary** plus the persistence, framework, metric, benchmark, and conversion decisions from the wider map.

```markdown
## Question

Which observable invariants and lean interface-level tests constitute human approval for the final clean-break specification, and which historical implementation-shaped tests should be deleted rather than carried into the new architecture?
```

Initial frontier from this review:

- **Choose clean-break root identity and minting semantics**
- **Choose schema-owned workflow and config-file loading**
- **Choose concrete temporal-decision module interfaces**
- **Inventory remote execution capabilities and constraints**

## Fog of war

These areas are in scope but depend on wider-map facts before sharper tickets can be written:

- actual duplicate legacy IDs across local and university roots, and old-to-new corpus many-to-one collisions;
- whether imported IDs can remain globally unique if flat storage is selected;
- university filesystem no-replace, directory-fsync, NFS, and Optuna journal-lock behavior;
- eligible artifact/evaluation/study counts after strict conversion proof;
- whether any near-term second representation, temporal compiler, execution policy, or prediction family has an approved distinct contract rather than speculative roadmap status;
- whether slurmrestd is operated and supported, not merely installed;
- operator need for chain-grouped directory browsing versus flat globally addressable roots;
- archive capacity, retention owner, and rollback authority.

## Recommendation to the map owner

Chart the four initial frontier tickets. Do not encode the candidate's chain-qualified layout, owner-coercer removal, registry removal, or custom Session retention as settled decisions. The evidence favors mixed semantic/instance identity, flat globally addressable roots, schema-owned Pydantic unions, direct concrete temporal-decision modules, and a reduced standard-tool Execution Session. Those remain recommendations until the named tickets close with human approval.
