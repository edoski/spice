# Issue 39 ADR, Domain-Language, and Documentation Contract

Status: owner-approved on 2026-07-15.

This planning contract defines the post-break architectural decisions, active
FABLE language, and documentation ownership. It does not rewrite normative
documentation or implement any production change.

## Authority and scope

The contract incorporates the approved decisions in Issues 10, 19, 24, 30,
32, 34, 41, 47, 49, 59, 63, and 78. Later amendments control where they
supersede older resolutions. In particular:

- FABLE uses UUID instances, direct typed addresses and loaders, completed
  objects that own their exact requests once, owner-local hidden scratch,
  direct rename, native Lightning checkpoints, direct Slurm submission,
  external monitoring, and manual operator handling.
- Active authority contains no content-derived identity, digest, payload
  inventory, software revision, plan, attempt, marker, predecessor,
  reconciliation, lock, lease, manifest, catalog, stored metric summary,
  logits, uncertainty state, discovery system, or compatibility layer.
- Protocol-era names may remain human scientific context. They do not enter
  active application records.
- The Generic Seam Pattern is historical architecture. A surviving seam is a
  direct owner function/module, a small explicit union or table for real fixed
  plurality, or an external facade justified by measured operational evidence.
  A hypothetical future implementation does not justify runtime dispatch.

## ADR dispositions

The bodies of ADRs 0001 through 0005 remain readable historical evidence.
Later documentation changes only their status and, for superseded records, a
one-line successor pointer. None remains an active FABLE decision.

| ADR | Disposition | Surviving boundary |
| --- | --- | --- |
| 0001 Root-ID Consumer Workflows | Supersede | Merge UUID instance authority, exact direct addresses/loaders, and completed-object request ownership into **Direct durable object authority**. |
| 0002 Config Resolution, Hydration, and Loading | Retire without an ADR successor | Strict whole request documents, one schema-owned adapter, and explicit fixed unions/tables belong in current module architecture and source contracts. Owner coercers, snapshots, and config groups disappear. |
| 0003 Representation Seam Retained | Retire without an ADR successor | Preserve only the responsibility in current architecture as one concrete lazy `HistoricalDataset` and direct temporal owners. The adapter/interface/registry rationale and persisted representation identity disappear. |
| 0004 Compiler, Materialization, and Existing-Root Vocabulary | Retire without an ADR successor | Direct owner functions and exact typed paths replace compiler, materializer, catalog, and root-handle machinery. |
| 0005 Custom Execution Session Retained | Supersede | Replace the custom Session with **Native external execution boundary**. |

### Direct durable object authority

This future concise ADR records the hard-to-reverse durable boundary:

- `corpora/<corpus_id>/corpus.json` plus `blocks.parquet`;
- `studies/<study_id>.json` with the exact `TuneRequest` and ordered
  `RetainedResult` values;
- `artifacts/<artifact_id>.ckpt` as the unchanged native Lightning weights-only
  best checkpoint with exact `TrainRequest`, minimal fitted state, and the
  selected Study result index plus exact `Method` when applicable;
- `evaluations/<evaluation_id>/evaluation.json` plus `observations.parquet`.

UUIDs identify instances. Typed requests and associations establish authority.
There is no manifest, sidecar, inventory, digest, content identity, database,
catalog, summary, compatibility/version layer, generic provenance envelope, or
discovery system. Derived selection, metrics, gates, TSV rows, and thesis views
are recomputed from the exact durable objects.

### Native external execution boundary

This future concise ADR records the evidenced operational boundary: a narrow
runtime YAML, OpenSSH, generated Slurm scripts, one `sbatch --parsable` call,
the returned numeric job ID, external scheduler monitoring, and ordinary
operator `rsync`/`scp` plus hidden-sibling `mv`. FABLE owns no execution
Session, job ledger, follow command, source/revision gate, reconciliation,
restart, predecessor, receipt, transfer framework, or synchronization state.

Only these two replacement decisions meet the ADR tests: hard to reverse,
surprising, and chosen against real alternatives. Schema mechanics, direct
functions, the concrete temporal dataset, and general locality guidance remain
ordinary architecture. FABLE naming and SPICE attribution are identity and
documentation language, not an architecture ADR.

## FABLE and SPICE attribution

The first substantive mention in current documentation expands **FABLE (Fee
Analysis through Blockchain Learning and Estimation)**; subsequent prose uses
FABLE, never title-case Fable. FABLE is a clean-break temporal fee-analysis
system derived from and extending selected temporal work from the original
SPICE paper. It is neither SPICE nor a SPICE reproduction.

SPICE names only the paper's complete spatial, temporal, and distributed-
reputation framework and immutable historical evidence. Historical research,
paths, commands, reports, Git history, and issue history preserve `SPICE` or
`spice` verbatim when clearly historical. Active durable identities and domain
terms remain neutral and unbranded.

## Active glossary

The replacement `CONTEXT.md` begins with the compact identity and attribution
boundary above, followed by these initial 21 entries. No current entry survives
verbatim.

1. **WorkflowRequest** — the strict `TrainRequest | EvaluateRequest` union used
   for direct remote workflow execution. It is not a plan, queue item,
   selection, snapshot, or identity; `TuneRequest` remains separate.
2. **UUID instance** — a neutral identity minted for one Corpus, Study,
   artifact, or evaluation. It is not content identity.
3. **Typed association** — an exact request/object relationship expressed by
   the owning schema, UUID, embedded request, or selected Study result index
   plus `Method`, not a generic provenance envelope.
4. **CorpusRequest** — the exact request for one corpus UUID and its
   `CorpusDefinition`.
5. **Corpus** — the completed request, finalized anchor, and canonical block
   rows at the corpus UUID's direct address.
6. **TuneRequest** — the complete bounded tuning question. It is not a
   WorkflowRequest or execution identity.
7. **Study** — the exact TuneRequest plus the operator-curated ordered current
   `RetainedResult` list. It stores no winner.
8. **RetainedResult** — one retained successful Method result containing only
   method, validation total loss, earliest best epoch, and completed epochs.
9. **TrainRequest** — the complete typed instruction for one fit, including
   exact input authority and scientific semantics.
10. **Native Lightning artifact** — the unchanged native weights-only best
    checkpoint carrying the exact TrainRequest, minimal fitted state, and any
    selected-Study association.
11. **EvaluateRequest** — the complete typed instruction for one explicit
    post-fit validation or testing evaluation.
12. **Evaluation observation** — one canonical scalar observation row from an
    EvaluateRequest. Aggregate metrics and views are derived, not stored.
13. **Method** — one complete model and training choice.
14. **MethodSpace** — the finite typed set of Methods allowed by a TuneRequest.
15. **Decision origin** — the decision point immediately after closed parent
    block `h`.
16. **Closed parent** — the latest closed block `h` visible at a decision
    origin.
17. **Context** — exactly `C` consecutive closed blocks `h-C+1...h`, selected
    by block number rather than elapsed time.
18. **Horizon** — the exact next `K` blocks `h+1...h+K` whose complete outcomes
    define eligibility.
19. **Action** — zero-based offset `k` selecting target block `b=h+1+k` within
    the horizon.
20. **Role** — one of training, validation, or testing. Training fits weights
    and data-dependent state; validation selects; testing reports and changes
    nothing.
21. **ExperimentSemantics** — the complete scientific role, feature, target,
    loss, and evaluation contract carried where an owning request needs it.

There is no numeric glossary cap. An entry belongs only when it has active
cross-module or domain value, or prevents a known scientific or attribution
ambiguity. Each entry stays compact. Schema fields, algorithms, implementation
owners, commands, paths, libraries, and one-module details remain with their
owning source, API, architecture, or operator documentation. Add no glossary
registry, generator, synchronizer, inventory, or absence test.

`selected_action_wait_seconds` is not glossary or domain vocabulary. This
decision does not amend Issue 34's evaluation schema; any surviving field
definition belongs only to evaluation-owned contract or architecture material.

### Operational language outside the glossary

- **Hidden scratch** is one owner-local sibling before direct rename, not a
  lifecycle state.
- **Direct submission** is one `sbatch --parsable` call returning a numeric ID,
  with no stored job state.
- **Manual operator handling** covers external monitoring, ambiguity, transfer,
  deployment, and cutover.
- **Direct owner function**, **explicit fixed union/table**, and
  **evidence-backed external facade** describe architecture, not domain terms.

## Legacy vocabulary disposition

Every one of the 67 current `CONTEXT.md` entries has an explicit destination:

- Merge Workflow Selection, Root Consumer Selection, Workflow Config, Resolved
  Workflow Hydration, Resolved Workflow Snapshot, and Workflow Command
  Selection into the request terms above.
- Retire Surface, Concrete Owner Config, Config Group, Config Group Loading,
  and Problem Spec. Any surviving values live directly inside requests,
  Method/MethodSpace, or ExperimentSemantics.
- Merge Producer Root Identity, Storage Selector, Root Handle, Produced Root
  Handle, Storage Root Materialization, and Artifact Inference Context into
  UUID instance, typed association, exact canonical address, and direct typed
  loader. Retire Storage Operator Outcome.
- Merge Tuning Execution into TuneRequest, Study, RetainedResult, Method, and
  MethodSpace.
- Merge Corpus Assembly, Corpus Acquisition Stage, Corpus Capability Planning,
  Corpus Acquisition Source Requirements, Corpus Split Materialization, Split
  Intent, and Staged Split Resume into CorpusRequest and Corpus at domain
  level. Direct acquisition functions belong only in architecture and source.
- Merge Temporal Dataset Preparation Interface, Action Space, Temporal Outcome
  Facts, and Prediction Target Batch into decision origin, closed parent,
  context, horizon, and action, with the concrete HistoricalDataset and direct
  target/loss owners documented in architecture. Action Space does not survive
  as a glossary term.
- Merge Training Runner, Modeling Runtime Plan, Training Runtime Plan, Training
  Fit Policy, and Objective Runtime into TrainRequest, native Lightning
  artifact, and direct Lightning-owned architecture. Retire Decoded Result ABI.
- Merge Temporal Replay Runner, Temporal Accounting, and Temporal Replay Metric
  Catalog into EvaluateRequest, evaluation observation, and one direct reducer
  in architecture.
- Supersede Execution Session with direct submission, manual operator handling,
  and the native external execution ADR.
- Retire Temporal Problem Compiler, Feature Catalog, Temporal Capability, Root
  Lifecycle, Workflow Preparation, Storage Transaction, Storage Transfer
  Transaction, Remote Catalog Record Codec, and Batch Plan.
- Retire the entire Benchmark vocabulary: Benchmark, Benchmark Case, Benchmark
  Step, Benchmark Plan Entry, Benchmark Selection Ledger, Benchmark Dependency
  Ledger, Benchmark Root Ledger, Benchmark Root Facts, Benchmark Plan
  Materialization, Benchmark Run, Benchmark Plan Execution, Benchmark
  Collection Snapshot, Benchmark Result Record, Benchmark Result Index,
  Benchmark Collection Resolver, and Benchmark Collection Match Facts.
- Retire Evaluation Execution Provenance and Evaluation Config Snapshot.

The old Relationships, Example Dialogue, and Flagged Ambiguities sections are
deleted with the legacy glossary. They describe the retired system.

## Documentation ownership

The final active documentation uses a layered reader journey rather than the
paired `ARCHITECTURE.md`/`IMPLEMENTATIONS.md` taxonomy.

- `README.md` is the sole newcomer/operator orientation: FABLE identity and
  attribution, host split, installation and quick start, four public commands,
  serving/demo route, and links into the remaining layers.
- `CONTEXT.md` contains only the identity preface and active glossary.
- root `ARCHITECTURE.md` is the sole system map: dependency direction, direct
  owners, exact object flow, deep interfaces, and the external execution
  boundary. It contains no Generic Seam Pattern, tutorial, algorithm catalog,
  config inventory, or historical narrative.
- `docs/tutorial.md` is one concrete undergraduate end-to-end temporal-ML
  journey with values, shapes, units, availability, roles, target, loss,
  decoding, economic accounting, bounded HPO, serving parity, limitations, and
  sources.
- `docs/theory.md` owns closed-parent causality, `C/K/k` geometry,
  complete-outcome purging, feature availability, targets/losses, evaluation
  estimands, claims, equations, and paper facts versus FABLE extensions.
- `docs/reference.md` is one concise exact reference for current request/object
  layouts, canonical addresses, commands, remote YAML, evaluation
  observations, and fixed schema facts. Dynamic IDs and counts come from code
  or CLI.
- `docs/adr/` contains decision rationale only.
- A local module `ARCHITECTURE.md` survives only for a genuine deep module whose
  small interface hides meaningful internal complexity. Shallow folders and
  single implementations get no local guide.
- Source and API documentation own concrete function, type, and field detail.
- `docs/research/issue-*` is immutable, explicitly nonnormative decision and
  evidence history. Historical SPICE wording remains unchanged.
- `AGENTS.md` and `docs/agents/` own contributor/agent process and sit outside
  the reader journey.

### Current file disposition

- Rewrite `README.md`, root `ARCHITECTURE.md`, and `CONTEXT.md` in place during
  the later documentation implementation slice.
- Retain `AGENTS.md` and `docs/agents/{domain,issue-tracker,triage-labels}.md` as
  project process, updating only facts when their owning implementation occurs.
- Retire `ARCHIVE.md`, `CLEAN_BREAK_TRACKER.md`, `CONFIGURATION.md`, and
  `PROGRESS.md`. They preserve no current interface. Required historical byte
  custody follows Issue 20 before deletion; none becomes an active
  compatibility archive.
- `benchmarks/README.md` and Markdown below benchmark exports/runs leave the
  active repository with Issue 20's frozen benchmark evidence after approved
  capture and verification. No current benchmark documentation survives.
- Retire all 19 tracked `IMPLEMENTATIONS.md` files. Merge only current deep-
  module facts into the owning architecture or source/API documentation.
- Issue 51 maps the 26 tracked `src/**/ARCHITECTURE.md` files plus root
  `ARCHITECTURE.md` to keep, rewrite, merge, or retire against final module
  boundaries. Deleted benchmark, catalog, compiler, config-registry, generic
  workflow/storage, and generic execution owners cannot keep documentation as
  history.
- Ticket-scoped `docs/research/issue-*` remains. A loose
  `docs/research/*.md` file must move unchanged into its owning issue evidence
  directory or retire when redundant; no loose research pile remains.
- Cache, vendor, generated-output, and tool-owned Markdown is not project
  documentation and follows its owning cleanup/archive contract.

## Downstream handoff

### Issue 51

Issue 51 uses this contract as binding input and:

1. prototypes the layered reader journey;
2. compares it with the paired taxonomy and recommends the layered route;
3. gives every one of the 46 current root/source ARCHITECTURE and
   IMPLEMENTATIONS files, plus adjacent README, CONTEXT, and historical
   pointers, an exact keep/rewrite/merge/retire disposition;
4. shows the undergraduate worked tutorial;
5. supplies the reader, source, link, and equation verification checklist; and
6. publishes prototype evidence only, rewriting no normative guide.

### Final specification and implementation

Issue 38 creates one late code-review-sized documentation/repository-hygiene
slice after implementation semantics settle and before Issue 65 integration.
That later slice performs the approved rewrites, merges, and deletions; status-
only historical ADR edits; two new ADRs; link/source/equation checks; and an
ordinary final-tree review.

Issue 44 rejects the final specification unless Issue 51's owner-approved map
is incorporated, the cleanup slice exists in the native DAG, and the end state
has one current documentation story without the Generic Seam Pattern, paired
taxonomy, stale active SPICE identity, benchmark/plan/catalog/session language,
or stray Markdown. Issue 65 verifies the realized tree as ordinary integration
evidence, not a permanent documentation gate.

## Non-authorization

Issue 39 authorizes planning evidence only. It rewrites no README, CONTEXT,
ADR, architecture guide, source, configuration, test, dependency, data,
storage, job, mobile surface, repository identity, sibling issue, or dependency
edge. It adds no compatibility alias, historical reader, documentation
registry, generator, synchronizer, inventory, CI gate, architecture snapshot,
absence test, transition test, or extra verification machinery.
