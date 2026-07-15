# Issue 51 file disposition audit

Status: disposable while unapproved and unpublished. Once approved and published as
Issue 51 evidence, it remains immutable, explicitly nonnormative ticket history and is
never copied into normative authority.

## Audit bound

Question: which current reader files carry a unique responsibility into the approved
layered FABLE documentation set?

Cheapest discriminating observation: classify every tracked root/source
`ARCHITECTURE.md` and `IMPLEMENTATIONS.md` file by its surviving reader-owned facts, then
apply the deep-module deletion test to every proposed local guide.

Budget: one read-only pass over 46 tracked root/source guides and their adjacent reader,
ADR, process, and historical-pointer files; no code execution, model fit, network data,
or normative rewrite. Stop when every file has one exact disposition and every retained
fact has one final owner.

Disposition meanings:

- **Keep**: retain at the same responsibility; factual edits remain owner-driven.
- **Rewrite**: replace the file's contents for one approved current responsibility. A
  later `src/spice` to `src/fable` move is part of the clean identity cut, not a shim.
- **Merge**: move only current facts into named owners, then remove the original file.
- **Retire**: remove after any required historical custody; copy no active guidance.

## Exact 46-file root/source table

| Current file | Disposition | Final owner and reason |
| --- | --- | --- |
| `ARCHITECTURE.md` | Rewrite | Sole system/dependency/deep-interface map. Remove the Generic Seam Pattern, inventories, tutorial prose, and historical narrative. |
| `src/spice/ARCHITECTURE.md` | Merge | Merge the useful package/data-flow overview into root `ARCHITECTURE.md`; a second system map has no distinct reader job. |
| `src/spice/acquisition/ARCHITECTURE.md` | Rewrite | Seed `src/fable/acquisition/ARCHITECTURE.md` for the deep acquire/finalize interface only: ordered ordinary reads, private resumable prefix, validation/finality, and canonical publication. |
| `src/spice/acquisition/rpc/ARCHITECTURE.md` | Merge | Move provider-owned retry and ordinary RPC facts into the acquisition guide or source/API docs. RPC transport is not a separate reader layer. |
| `src/spice/acquisition/rpc/IMPLEMENTATIONS.md` | Merge | Move only current provider/finality constraints into the acquisition guide and concrete source docs; retire controller/batching/catalog history. |
| `src/spice/benchmarks/ARCHITECTURE.md` | Retire | The generic benchmark plan/run/index module is deleted. Exact request-list construction belongs to source and `docs/reference.md`. |
| `src/spice/benchmarks/IMPLEMENTATIONS.md` | Retire | Its ledgers, run state, collection resolver, and result index are removed; preserve no compatibility narrative. |
| `src/spice/cli/ARCHITECTURE.md` | Merge | Put operator orientation in `README.md`, the six exact leaves in `docs/reference.md`, and command ownership in root architecture. |
| `src/spice/cli/commands/ARCHITECTURE.md` | Merge | Merge the small command map into `README.md` and `docs/reference.md`; command folders are shallow. |
| `src/spice/cli/commands/IMPLEMENTATIONS.md` | Retire | Current commands and defaults are superseded. Concrete final signatures come from Typer help and source, not a second catalog. |
| `src/spice/conf/ARCHITECTURE.md` | Retire | Named config-group/surface architecture disappears in the clean request-first design. |
| `src/spice/conf/IMPLEMENTATIONS.md` | Retire | Current IDs and YAML inventories are stale by construction; final fixed request/remote schemas belong in `docs/reference.md`. |
| `src/spice/config/ARCHITECTURE.md` | Merge | Merge strict request/schema ownership and the small explicit unions into root architecture and reference. Retire resolution/hydration machinery. |
| `src/spice/config/IMPLEMENTATIONS.md` | Retire | Surface resolution, snapshots, group loading, and owner coercer inventories do not survive. |
| `src/spice/core/ARCHITECTURE.md` | Retire | Small shared helpers should be self-explanatory in source; `core` has no reader-facing domain interface. |
| `src/spice/corpus/ARCHITECTURE.md` | Merge | Merge acquire/finalize behavior into the acquisition guide and exact corpus address/schema into `docs/reference.md`. |
| `src/spice/corpus/IMPLEMENTATIONS.md` | Retire | Old chunk layout, manifests, materialization outcomes, and repair paths are superseded; concrete row fields live in schemas/source/reference. |
| `src/spice/evaluation/ARCHITECTURE.md` | Rewrite | Seed `src/fable/evaluation/ARCHITECTURE.md` for the deep explicit-path loader, one observation writer/reducer, and all-or-nothing report interface. |
| `src/spice/evaluation/IMPLEMENTATIONS.md` | Merge | Move exact estimands/equations to `docs/theory.md`, exact observation fields to `docs/reference.md`, and reducer ownership to the local evaluation guide. |
| `src/spice/execution/ARCHITECTURE.md` | Merge | Root architecture owns the external seam; the replacement ADR owns rationale; reference owns remote YAML and generated command facts. |
| `src/spice/execution/IMPLEMENTATIONS.md` | Retire | Session, follow, provenance, transfer transaction, and target-registry behavior are deleted. |
| `src/spice/features/ARCHITECTURE.md` | Merge | Exact causal feature formulas/availability belong in `docs/theory.md`; ordered concrete formulas stay with source/API docs. No feature catalog survives. |
| `src/spice/modeling/ARCHITECTURE.md` | Merge | Root architecture owns training flow; theory owns model concepts; reference owns artifact facts. Native Lightning mechanics do not justify a local guide. |
| `src/spice/modeling/IMPLEMENTATIONS.md` | Retire | Old batch plans, masks, generic scoring, artifact manifest, and Optuna descriptions are removed. |
| `src/spice/modeling/dataset_builders/ARCHITECTURE.md` | Merge | Merge causal historical/live preparation into the rewritten temporal guide. The builder abstraction is deleted. |
| `src/spice/modeling/dataset_builders/IMPLEMENTATIONS.md` | Retire | Seconds-derived sequence calibration, split repair, and builder runtime metadata are superseded. |
| `src/spice/modeling/families/ARCHITECTURE.md` | Merge | Three concrete model branches belong in `docs/theory.md` and source; a closed union is not a registry layer. |
| `src/spice/modeling/families/IMPLEMENTATIONS.md` | Merge | Keep only concise LSTM/Transformer/hybrid teaching facts in `docs/theory.md`; construction fields remain source/reference facts. |
| `src/spice/prediction/ARCHITECTURE.md` | Merge | Merge task ownership into the rewritten minimum-block-fee task guide; delete generic prediction contracts and decoded-result ABI prose. |
| `src/spice/prediction/families/ARCHITECTURE.md` | Retire | One task does not justify a family hierarchy or family guide. |
| `src/spice/prediction/families/IMPLEMENTATIONS.md` | Retire | Generic family comparison, masking, and decoded-result descriptions disappear. |
| `src/spice/prediction/families/min_block_fee_multitask/ARCHITECTURE.md` | Rewrite | Seed `src/fable/min_block_fee/ARCHITECTURE.md`: the deep architecture-independent target/loss/scorer/decode interface. |
| `src/spice/prediction/families/min_block_fee_multitask/IMPLEMENTATIONS.md` | Merge | Put equations and task meaning in `docs/theory.md`, exact state fields in `docs/reference.md`, and interface ownership in the task guide. |
| `src/spice/storage/ARCHITECTURE.md` | Merge | Root architecture and the direct-object ADR own authority; `docs/reference.md` owns exact UUID addresses and layouts. Generic storage is deleted. |
| `src/spice/storage/IMPLEMENTATIONS.md` | Retire | SQLite roots, manifests, catalogs, deterministic IDs, codecs, selectors, and lifecycle no longer survive. |
| `src/spice/storage/catalog/ARCHITECTURE.md` | Retire | The catalog/discovery module is deleted without a documentation successor. |
| `src/spice/storage/catalog/IMPLEMENTATIONS.md` | Retire | Catalog tables, refresh, selectors, and delete safety are obsolete implementation inventory. |
| `src/spice/temporal/ARCHITECTURE.md` | Rewrite | Seed `src/fable/temporal/ARCHITECTURE.md` for the deep historical/live preparation seams and tiny shared action arithmetic. |
| `src/spice/temporal/compilers/ARCHITECTURE.md` | Merge | Merge fixed `C/K/h` preparation ownership into the temporal guide; compiler selection is deleted. |
| `src/spice/temporal/compilers/IMPLEMENTATIONS.md` | Retire | Timestamp-window compilation, slot spacing, capabilities, and masks are superseded by fixed block geometry. |
| `src/spice/temporal/execution_policy/ARCHITECTURE.md` | Merge | Merge `require_action` and `target_block` ownership into the temporal guide; no policy interface survives. |
| `src/spice/temporal/execution_policy/IMPLEMENTATIONS.md` | Retire | Deadline overflow, post-window realization, action masks, and policy variants are removed. |
| `src/spice/temporal/input_normalization/ARCHITECTURE.md` | Merge | Put training-only scaler semantics in `docs/theory.md` and direct preparation ownership in the temporal guide. |
| `src/spice/temporal/input_normalization/IMPLEMENTATIONS.md` | Retire | The current scaler behavior conflicts with the strict approved scaler and should not be preserved as implementation guidance. |
| `src/spice/workflows/ARCHITECTURE.md` | Merge | Merge the few direct owner calls into root architecture and public commands into `README.md`; generic workflow preparation is deleted. |
| `src/spice/workflows/IMPLEMENTATIONS.md` | Retire | Root materialization, staged transactions, reporting adapters, and remote-session workflow details are obsolete. |

Count check: 27 `ARCHITECTURE.md` files (including root) plus 19
`IMPLEMENTATIONS.md` files equals 46.

## Adjacent reader, process, ADR, and historical-pointer files

| Current file | Disposition | Final owner and reason |
| --- | --- | --- |
| `README.md` | Rewrite | Sole newcomer/operator orientation and entry into the layered journey. |
| `CONTEXT.md` | Rewrite | FABLE identity preface plus the approved initial 21 active glossary entries only; no numeric cap and no `selected_action_wait_seconds` entry. |
| `ARCHIVE.md` | Retire | Preserve required bytes through Issue 20 custody, then remove from the active reader tree. Historical SPICE evidence remains unchanged in its evidence owner. |
| `CLEAN_BREAK_TRACKER.md` | Retire | Stale mutable project status is neither current system authority nor historical evidence owner. |
| `CONFIGURATION.md` | Retire | Current surface/benchmark/config details are superseded; final exact request and remote schemas are rewritten in `docs/reference.md` from code. |
| `PROGRESS.md` | Retire | Move any required immutable evidence through Issue 20 custody; keep no active status ledger. |
| `benchmarks/README.md` | Retire | Current benchmark-run/index contract is removed; historical benchmark evidence stays under its frozen research owner. |
| `docs/adr/0001-root-id-consumer-workflows.md` | Keep | Preserve body unchanged as history; change status to superseded and add one pointer to **Direct durable object authority**. |
| `docs/adr/0002-config-resolution-hydration-loading.md` | Keep | Preserve body unchanged as history; change status to retired with no successor. |
| `docs/adr/0003-representation-seam-retained.md` | Keep | Preserve body unchanged as history; change status to retired with no successor. |
| `docs/adr/0004-compiler-materialization-existing-root-vocabulary.md` | Keep | Preserve body unchanged as history; change status to retired with no successor. |
| `docs/adr/0005-custom-execution-session-retained.md` | Keep | Preserve body unchanged as history; change status to superseded and point to **Native external execution boundary**. |
| `AGENTS.md` | Keep | Contributor/agent process, outside the reader journey. Update only process facts through their owner. |
| `docs/agents/domain.md` | Keep | Project process. It continues to point agents to the single-context glossary and ADRs. |
| `docs/agents/issue-tracker.md` | Keep | Project process and Wayfinder tracker operations. |
| `docs/agents/triage-labels.md` | Keep | Project process and canonical triage-label mapping. |

All `docs/research/issue-*` evidence remains nonnormative and unchanged. Loose
`docs/research/*.md` files move unchanged to their owning issue directory or retire when
redundant, under the later custody slice. No research prose is rewritten into active
history.

## Proposed final active reader set

The always-present reader path is exactly:

1. `README.md`
2. `docs/tutorial.md`
3. `docs/theory.md`
4. root `ARCHITECTURE.md`
5. `docs/reference.md`

Side references are `CONTEXT.md`, `docs/adr/`, source/API docs, and these five local
deep-module guides:

- `src/fable/acquisition/ARCHITECTURE.md`
- `src/fable/temporal/ARCHITECTURE.md`
- `src/fable/min_block_fee/ARCHITECTURE.md`
- `src/fable/study/ARCHITECTURE.md`
- `src/fable/evaluation/ARCHITECTURE.md`

Each local guide passes the deletion test: removing it would scatter a nontrivial
interface contract across multiple callers. No local guide is created for config, CLI,
core, model families, generic workflows, execution, storage, or catalogs because their
facts already have one owner in the five reader layers, ADRs, reference, or source.

## Rewrite and retirement order

1. Freeze final implementation semantics, FABLE package/CLI identity, and realized module
   paths. Do not draft around transitional names.
2. Complete Issue 20 historical custody. Relocate loose research unchanged and identify
   the root/benchmark historical pointers safe to retire.
3. Rewrite `CONTEXT.md`; apply status-only changes to ADRs 0001–0005; add only the two
   approved successor ADRs.
4. Write `docs/reference.md` from strict schemas, direct paths, Typer help, and protocol
   constructors. Never hand-maintain dynamic IDs or counts.
5. Write `docs/theory.md` from approved equations, causal availability, roles, claims,
   and primary sources.
6. Write the five local deep-module guides from the final interfaces. Keep concrete
   field/function details in source/API docs.
7. Rewrite root `ARCHITECTURE.md` from the realized dependency graph and exact durable
   object flow.
8. Write `docs/tutorial.md` against the frozen reference, theory, and interfaces.
9. Rewrite `README.md` last so every quick-start command and link points to a final owner.
10. Merge any unique surviving facts, retire every superseded file in the tables, and
    perform one ordinary final-tree review.

Add no documentation registry, generator, synchronizer, inventory, CI/absence test,
architecture snapshot, compatibility archive, or transition test.
