# Issue 27 decision, deletion, and handoff map

This is a prototype result, not production authorization. It consumes the approved root
identity/finality/address, publication, retry-evidence, temporal-boundary, and corpus-geometry
contracts. Issue 27 stays chain-generic; the Ethereum/Polygon distinction is only an approved
Issue 49 downstream invocation plan. Issue 27's old wording is stale where it presumes adaptive
splitting/concurrency, persisted counters, manifest provenance, cross-window extension, or
confirmation-depth finality.

## Approved owner decisions

Edo explicitly approved the four original choices and original complete recap on 2026-07-13.
After the dependent audit and pushback reconciliation, he explicitly approved all three
reconciled choices exactly as recorded below.

| Choice | Recommendation | Rejected alternative |
|---|---|---|
| Partial resume | Add no marker. Treat the exact validated immutable Parquet prefix in the private stage as the checkpoint. | `progress.json`, status, next-block record, chunk ledger, lifecycle, or silent restart. Each duplicates facts already provable from payload files. |
| Retry owner | The public provider alone owns bounded retry/backoff. Acquisition calls each numbered read once at its seam, never reruns a block/range, and cancels siblings after one terminal result. Persist no retry fact. | Acquisition retry, nested provider+acquisition retry, adaptive batch split, concurrency rungs, counters, and provider-specific error taxonomy. |
| Hash placement | Private stage rows carry block hash and parent hash for exact cross-file link validation. Finalized payload rows omit both; the manifest retains only the finalized anchor evidence fixed by Issue 11. | Mandatory per-row hashes or sidecar in the immutable corpus, which Issue 47 rejected; or hashless staging, which cannot prove parent links. |
| Existing Parquet | Run every row through the new fixed validator/finalizer. Hashless existing payload requires a fresh exact source reread to recover and compare hashes/links. Any mismatch means reacquire in a fresh stage. | Legacy reader/importer, conversion, repair, truncation, old-layout reuse, or accepting number-only continuity. |
| Definition binding | Add one constant stage-only `definition_sha256` String column: lowercase full SHA-256 of the complete `CorpusDefinition` JSON using `ensure_ascii=True`, `allow_nan=False`, sorted keys, and compact separators. Require exact equality before resume and strip it from final payload. Readable regime name/start remain trusted request/final-manifest metadata only. | Readable regime columns, a marker file, definition-keyed path, Parquet-footer contract, lifecycle, or final-payload duplication. |
| Chain scope | Keep the acquire/finalize interface generic over one explicit single-chain definition per invocation. Issue 49 later invokes it once for Ethereum and once for Polygon, with no Avalanche invocation under its approved plan. | Ethereum/Polygon/Avalanche branches or suffix policy inside Issue 27. |
| Priority-fee scope | Exclude priority fees from the current baseline and add no Issue 27 machinery. After preprocessing, training, evaluation, and serving stabilize, create a fresh ticket for the bounded Issue 60 probe and a fresh owner decision. | Treating deferral as permanent rejection, prebuilding dormant enrichment, or pretending an active follow-up ticket exists. |

No numeric retry attempt count is added. Issue 7 already approved bounded provider-owned retry;
provider settings remain ephemeral under Issue 10. The old value and the Web3 default are not
project contract facts.

The audit's original failing probe proved why row continuity was insufficient: a completed
`regime-a` stage for blocks 100–103 was accepted as `regime-b` blocks 100–105 and extended.
With the approved digest binding, changed regime and changed last-block probes now fail before
any provider read or stage write.

## Corrected recap status

The original recap remains an approval receipt, but the definition-binding and post-visibility
failure corrections make it obsolete as a resolution text. The complete corrected recap is in
`dependent-completeness-audit.md`; Edo explicitly approved it exactly as recapped on 2026-07-13.
The approved contract changes no production code/config/tests or data. The authorized native
edge `#27 blocks #34` was completed and verified by the orchestrator/map owner; this thread did
not duplicate it. Assuming nothing changes, Edo authorized the final
Resolution/close-only-Issue-27/map-pointer/verification sequence once verification remains green
and the research assets have an immutable published link. He explicitly authorized publishing
only the five Issue 27 research files as one commit directly on synchronized `main`, excluding
all unrelated dirty paths and any branch/PR/merge/tag/release.

## Exact clean-break deletion map

The implementation ticket should delete the current implementations below, then write the
small direct module. It should not layer the new path beside them.

| Path | Exact clean-break action |
|---|---|
| `src/spice/acquisition/pull.py` | Entire current scheduler: `AcquisitionPullController`, retry/split request types, 32-attempt range retry, adaptive batch size/concurrency, counters/snapshots, and related helpers. Replace with the bounded ordered ordinary-call pull only. |
| `src/spice/acquisition/errors.py` | `TransientAcquisitionError` and `OversizedAcquisitionRequestError`; no acquisition retry taxonomy survives. Reassess `UnsupportedAcquisitionSourceError` only for fixed finality/schema failure, not enrichment selection. |
| `src/spice/acquisition/rpc/transport.py` | `RetryingBatchAsyncHTTPProvider.make_batch_request`, local exponential loop, batch response types, and batch-only imports. Build the ordinary provider directly with its public retry facility. |
| `src/spice/acquisition/rpc/client.py` | Batch request path; `eth_feeHistory` enrichment path/constants/rows; source-requirement dispatch; latest/timestamp binary-search planning; broad provider-error remapping for outer retries. Keep only fixed ordinary block/header/finalized reads and exact response validation. |
| `src/spice/acquisition/types.py` | `TimestampRange`, half-open `BlockRange`, `BlockPullPlan`, `AcquisitionRuntimeSnapshot`, planning protocols, and `evaluation_range`. Use the approved inclusive definition and one small provider interface. |
| `src/spice/corpus/split_materialization/` | Entire current package: staged/committed candidate modes, `CorpusSplitOutcome`, exact committed reuse, overlap extension, prefix/suffix pulling, chunk copying/trimming, rebuild, target matching, and repair-enabling sort/load helpers. |
| `src/spice/corpus/planning.py` | Entire feature/problem-driven source-requirement and timestamp-window planning path. The caller supplies one explicit definition. |
| `src/spice/corpus/acquisition_stage.py` | Current `.acquire-staging` record, config/corpus echo, split-session wrapper, state-DB staging, run record, and partial selected-path commit. Replace with private exact-prefix staging plus direct finalization. |
| `src/spice/corpus/assembly.py` | Dry-run/timestamp planning, controller creation, requested-window facts, and current stage/publication orchestration. Replace with direct acquire/finalize calls. |
| `src/spice/corpus/metadata.py` | `ProviderMetadata`, validation/materialization reports, source requirements/fingerprint, acquisition settings/runtime/counters, `AcquireRunRecord`, old split/window manifest, and their builders. Issue 34 supplies the new minimal record. |
| `src/spice/corpus/validation.py` | Mutable validation reports, issue counts, sorting before validation, timestamp-window repair semantics, and persisted status. Replace with direct exceptions and exact streaming checks. |
| `src/spice/corpus/io.py` | Recursive hidden-skipping discovery plus load-time sort. The new loader validates the exact manifest inventory and stored order without repair. |
| `src/spice/corpus/contract.py` | Current selectable/optional priority-fee columns and acquisition row builder. Replace the private stage row and finalized fixed payload schemas only after Issue 34 freezes the durable payload fields. |
| `src/spice/storage/corpus.py` | `write_corpus_state`, `load_corpus_manifest`, `list_acquire_runs`, and corpus SQLite use. Direct manifest/package loading replaces them under Issue 34. |
| `src/spice/storage/corpus_codecs.py` | Acquire-run and old corpus-manifest codecs. No codec/version/registry replacement. |
| `src/spice/storage/inspect_dataset.py` | Acquire-run history and provider/runtime rendering. Human listing may render the direct manifest only. |
| `src/spice/workflows/acquire.py` | Source-requirement preparation, planning result reporting, and stage-warning lifecycle wording. Keep one thin direct caller with cancellation propagation. |
| `src/spice/acquisition/__init__.py`, `src/spice/acquisition/rpc/__init__.py` | Delete exports of the removed controller, plans, ranges, batch transport, and old RPC row/source-requirement interfaces. Export only the direct ordinary provider seam and acquire/finalize entry points that survive. |
| `src/spice/storage/ids.py` | Delete `corpus_storage_id`; no `cor_<20hex>` identity exists before final payload bytes and inventory exist. |
| `src/spice/storage/workflow_root_materialization.py` | Delete `produced_corpus_id`, acquire-root pre-materialization, and old catalog/root-fact selection. No stage or canonical corpus address is pre-minted. |
| `src/spice/storage/workflow_roots.py` | Delete `CorpusRootHandle`, `AcquireWorkflowRoots`, chain-qualified corpus addressing, and SQLite manifest loading. Issue 34 supplies one direct typed manifest/package loader. |
| `src/spice/storage/layout.py` | Delete `corpora/<chain>/<corpus_id>` and corpus `.spice/state.sqlite` layout. The canonical address is flat `corpora/<bare-full-sha256>/`; private candidates are hidden siblings only. |
| `src/spice/storage/transactions.py` | Delete `commit_corpus_acquisition` selected-path replacement and reindexing. It can expose mixed payload/SQLite state and cannot satisfy package-level no-replace equality/conflict. |
| `src/spice/storage/lifecycle.py`, `src/spice/storage/sync_cli.py` | Remove corpus use of `prepare_root_stage`, `promote_root_stage`, cleanup, `--replace`, and SQLite reindexing. Reuse Issue 15's typed hidden-sibling publisher; do not create another generic lifecycle. |
| `src/spice/storage/schema.py`, `src/spice/storage/engine.py` | Delete corpus SQLite schema/init/load participation. A direct corpus root is valid without `.spice/state.sqlite`. Keep unrelated study/artifact work only under its owner. |
| `src/spice/storage/catalog/materialization.py`, `src/spice/storage/catalog/index.py`, `src/spice/storage/catalog/registry.py`, `src/spice/storage/catalog/records.py`, `src/spice/storage/catalog/schema.py`, `src/spice/storage/catalog/codecs.py`, `src/spice/storage/catalog/store.py` | Delete corpus discovery/materialization/record/codec branches and corpus registry selectors. Direct typed listing/loading replaces them; no compatibility catalog entry survives. |
| `src/spice/storage/selectors.py`, `src/spice/storage/operator.py`, `src/spice/storage/inspect.py`, `src/spice/storage/inspect_dataset.py`, `src/spice/storage/inspect_artifact.py`, `src/spice/cli/commands/storage.py` | Delete catalog-backed corpus selectors, refresh/show/delete/cascade commands, acquire-run/provider rendering, and artifact dependency lookup through SQLite. Issues 13, 15, 34, and 63 own direct listing/loading and the minimum CLI; no per-record deletion or refresh surface survives. |
| `src/spice/storage/identity.py` | Delete pre-content corpus/study/artifact projections, corpus-name echoes, and recipe-hash identity builders. Consume Issue 11's bare corpus ID and UUID instance identities through Issue 10/34's direct records. |
| `src/spice/corpus/coverage.py` | Delete compiled source-requirement and old split/window coverage checks. Downstream geometry consumes the strict direct manifest and Issue 47's fixed role/regime facts. |
| `src/spice/workflows/preparation.py` | Delete `PreparedAcquireWorkflow`, `prepare_acquire`, pre-minted acquire roots, and old separate manifest/payload loading. Other workflows move to Issue 34's one strict load result. |
| `src/spice/workflows/reporting.py` | Delete acquire provider/problem/feature/window/status/materialization/stage-warning facts. Report only the direct ephemeral operation result; persist none of it. |
| `src/spice/modeling/pipeline.py`, `src/spice/modeling/results.py` | Delete recursive sort-on-load and `source_requirements_fingerprint` propagation. Consume one strict manifest-plus-inventory load from Issue 34. |
| `src/spice/modeling/artifact_inference.py`, `src/spice/modeling/tuning_execution.py` | Replace `CorpusRootHandle`/old manifest/coverage paths with the direct loader; delete source-requirement provenance and any independent payload discovery. |
| `src/spice/modeling/tuning.py` | Replace `CorpusRootHandle` and chain/name-derived study preparation with Issue 34's direct corpus load result and Issue 10's direct request facts. |
| `src/spice/storage/study_manifest.py`, `src/spice/storage/artifact_codecs.py` | Delete old corpus source-requirement fingerprints and duplicated corpus provenance. Persist only the direct corpus identity/facts assigned by the durable-record owner. |
| `src/spice/config/models.py`, `src/spice/config/selections.py`, `src/spice/config/resolution.py`, `src/spice/config/surfaces.py`, `src/spice/config/groups.py`, `src/spice/config/typed_groups.py`, `src/spice/config/group_catalog.py`, `src/spice/config/resolved_workflows.py`, `src/spice/config/workflow_snapshots.py`, `src/spice/config/__init__.py` | Remove the old acquire surface/selection/resolution graph, provider reference/name, feature/problem-driven planning, durable acquisition settings, dry-run, and pre-content corpus identity. Issue 10 exposes the explicit definition plus ephemeral runtime inputs with no parallel schema. |
| `src/spice/conf/corpus/*.yaml`, `src/spice/conf/provider/publicnode.yaml`, `tenderly.yaml`, `src/spice/conf/surface/current_row_fee_dynamics.yaml` | Remove old timestamp-window, provider-name/reference, adaptive batch/concurrency, feature/problem, and dry-run acquisition inputs. Keep no compatibility YAML or loader. Exact suffix definitions wait for Issue 49's authorized execution gate. |
| `src/spice/cli/commands/workflows.py`, `src/spice/cli/app.py` | Delete old acquire arguments/examples and `cor_…` examples. Issue 63 chooses the minimum CLI that passes an explicit definition and ephemeral runtime inputs to the direct owner. |
| `src/spice/execution/transfer_transaction.py`, `src/spice/cli/commands/transfer.py` | Delete generic corpus `RootKind`, `--replace`, catalog envelopes, mixed-root promotion, and cleanup-on-ambiguous-failure. Issue 15 owns direct typed no-replace corpus transfer. |
| `src/spice/serving/live_blocks.py`, `src/spice/serving/runtime.py`, `src/spice/serving/api.py` | Remove old `ResolvedRpcEndpointConfig` and `CorpusAcquisitionSourceRequirements` coupling. Issue 32 reassesses the ordinary maintained Web3 provider for both acquisition and surviving live reads; no provider-specific acquisition abstraction. |
| `src/spice/features/contracts.py`, `src/spice/features/sets/core_fee_dynamics/_priority_fee.py`, `src/spice/features/sets/core_fee_dynamics/with_priority_fee.py`, `src/spice/conf/features/core_fee_dynamics_with_priority_fee.yaml` | Remove the acquisition-enrichment/priority-fee route from the current baseline. Issue 27 and Issue 49 carry no enrichment machinery or dormant alias. This is deferral, not permanent rejection; a future fresh ticket owns any reintroduction after the foundation stabilizes. |
| `src/spice/features/__init__.py`, `src/spice/features/registry.py`, `src/spice/features/sets/__init__.py`, `src/spice/features/sets/core_fee_dynamics/__init__.py`, `src/spice/conf/benchmark/priority_fee_ablation.yaml` | Remove current registrations, exports, and benchmark selection of the deferred route. Issue 20's approved classification controls historical benchmark custody; no active ablation config remains in the clean baseline. |

Configuration cleanup belongs to Issue 10's implementation: remove
`AcquisitionRpcConfig.batch_size`, `min_batch_size`, and `concurrency_rungs`; remove
`AcquisitionConfig.dry_run` and semantic persistence of `chunk_size`; remove provider
name/reference and acquisition tuning from every durable request/snapshot/manifest. One
runtime URL, timeout, finite provider retry/backoff setting, concurrency, and chunk size may
reach the direct call without becoming content or provenance. Delete the adaptive fields from
`src/spice/conf/provider/publicnode.yaml` and `tenderly.yaml`; do not create a second config
path or compatibility loader.

Documentation cleanup should remove or rewrite the stale acquisition sections in
`src/spice/acquisition/ARCHITECTURE.md`, `src/spice/acquisition/rpc/ARCHITECTURE.md`,
`src/spice/acquisition/rpc/IMPLEMENTATIONS.md`, `src/spice/corpus/ARCHITECTURE.md`, and
`src/spice/corpus/IMPLEMENTATIONS.md`; the matching storage, catalog, config, conf, workflow,
CLI, execution, serving, and feature `ARCHITECTURE.md`/`IMPLEMENTATIONS.md` files must be
rewritten by their owners. `docs/adr/0004-compiler-materialization-existing-root-vocabulary.md`
still preserves `Corpus Split Materialization`; Issue 38 must supersede that clause rather
than retain the old module as vocabulary. `CONTEXT.md` terms `Corpus Assembly`, `Corpus
Acquisition Stage`, `Corpus Capability Planning`, `Corpus Acquisition Source Requirements`,
`Corpus Split Materialization`, `Split Intent`, and `Staged Split Resume` describe the removed
design and must not survive as aliases. The finality/provenance portions of
`docs/research/rpc-retry-finality-alternatives.md` are superseded by Issue 11; retain it only
as historical retry evidence, not normative documentation.

`benchmarks/scripts/merge_ethereum_pectra_jun20_corpus.py` is a forbidden old-layout
converter: it copies chunks, trusts number adjacency, reuses old metadata, pre-mints an intent
ID, and writes SQLite. Never adapt or execute it. Its active-tree removal and archival custody
follow the already-approved Issue 20 procedure, not an Issue-27 deletion inference. Other
Issue-20 archival scanners/renderers that glob the old chain-qualified layout are historical
evidence only and earn no compatibility reader.

Delete the obsolete behavior tests instead of preserving them as transition checks:

- Rewrite `tests/acquisition/test_pull.py`; remove oversized splitting, acquisition retry
  limit, adaptive controller backoff/recovery, and old half-open-plan tests.
- Rewrite `tests/acquisition/test_rpc_client.py`; remove batch-transport retry and priority-fee
  enrichment selection tests.
- Delete current `tests/corpus/test_assembly.py`, `tests/corpus/test_contract.py`,
  `tests/corpus/test_split_materialization.py`, `tests/corpus/test_corpus_planning.py`, and
  `tests/corpus/test_metadata.py` with their removed modules.
- Rewrite `tests/corpus/test_validation.py` and `tests/workflows/test_acquire.py` against the
  direct fail-closed interface; remove metadata/run-history expectations.
- Rewrite or delete `tests/corpus/test_coverage.py`, `tests/storage/test_staging.py`,
  `tests/storage/test_workflow_roots.py`, `tests/storage/test_catalog.py`,
  `tests/storage/test_catalog_codecs.py`, `tests/storage/test_read_only_loads.py`,
  `tests/storage/test_identity.py`, `tests/storage/test_study_manifest.py`, and
  `tests/storage/test_sync_cli.py`, `tests/storage/test_operator.py`,
  `tests/cli/test_storage_cli.py`, `tests/catalog_helpers.py`, and
  `tests/root_handle_helpers.py` as their removed SQLite/catalog/replace/source-requirement
  subjects disappear.
- Rewrite `tests/config/test_resolution.py`, `tests/config/test_selections.py`,
  `tests/config/test_workflow_snapshots.py`, `tests/conftest.py`,
  `tests/cli/test_config_cli.py`, `tests/cli/test_transfer_cli.py`,
  `tests/execution/test_transfer.py`, `tests/workflows/test_preparation.py`, and
  `tests/workflows/test_reporting.py` under Issues 10, 15, 34, and 63; preserve no old acquire
  selection, `--replace`, root-handle, or lifecycle fixture.
- Remove old corpus/source-requirement fixtures from
  `tests/modeling/test_artifact_inference.py`, `tests/modeling/test_dataset_builders.py`,
  `tests/modeling/test_tuning_execution.py`, `tests/serving/test_live_blocks.py`,
  `tests/serving/test_serving_runtime.py`, `tests/serving/test_api.py`, and
  `tests/features/test_core_fee_dynamics.py` when their owning clean-break tickets replace the
  records and priority-fee route.

Replacement verification stays lean: one approved identity golden vector; one exact
pull/resume/cancel/finality/publication fixture; one invalid-stage/package table; and one
existing-Parquet validation/reacquire case. The first fixture must prove that runtime stage
chunk sizes produce the same fixed canonical inventory/ID and that any definition fact change
rejects resume before reads or writes. The invalid table covers symlink/escape/extra entry,
wrong schema/domain/range/order, anchor-before-last, parent break, and post-rename ambiguity.
When one `asyncio.wait` completion set contains both success and terminal failure, inspect all
terminal outcomes before writing any success from that set, then cancel every sibling. Add no
old/new parity, migration, registry, codec, architecture-transition, adaptive-counter, or
legacy-layout test.

## Handoffs

| Owner | Exact handoff |
|---|---|
| Issue 10 — configuration/workflow algebra | Replace the whole acquire config/selection/resolution/CLI/YAML surface. Keep provider URL/name/reference, timeout, retry/backoff, concurrency, chunk tuning, host/path, and observations outside durable requests and recipe identity. The direct caller receives an explicit definition plus ephemeral runtime values and mints no identity before content finalization. |
| Issue 15 — publication/transfer | Reuse its hidden-sibling sync, exclusive no-replace directory publication, equality/no-op/conflict inspection, ambiguous-failure recovery, canonical reload, and owner-only unpublished-stage cleanup. Delete corpus `--replace`/generic lifecycle paths; do not duplicate the publisher. NFS remains disabled until its exact-mount gate passes. |
| Issue 20 — archival custody | Remove the old corpus merge script and other old-layout research consumers from the active tree only through its approved hash-verified custody sequence. Never run, port, or treat them as a migration path. |
| Issue 32 — dependencies | Reassess direct `aiohttp` and related transport imports after deleting the custom batch provider/error taxonomy. Retain Web3 only for an ordinary maintained provider used consistently by acquisition and surviving live reads. Add no retry, Parquet, storage, or plugin framework. |
| Issue 34 — durable records | Freeze the final payload columns, fixed canonical writer geometry/settings, and exact readable manifest serialization; own one strict manifest-plus-inventory-plus-payload loader. Consume Issue 11's definition, inventory, bare ID, and anchor evidence. Persist no provider/runtime/retry/chunk/status/report/version/compatibility field, source-requirement fingerprint, or SQLite corpus record. The orchestrator/map owner connector-first wired and verified the authorized derived edge `#27 blocks #34`; this thread did not duplicate it. |
| Issue 38 — implementation order/runbook | Order the clean replacement as durable schema/identity, ordinary provider seam, definition-bound private prefix pull, finalizer, Decision-A publication, direct loader/caller, then all transitive deletion/verification. Include exports, reporting, docs, ADR 0004 supersession, prototype disposal, full `uv` gates, and manual Vulture review; no parallel old path or rollback mode. |
| Issue 42 — disposable rehearsal | Exercise fresh-root creation; definition mismatch and cross-window-extension rejection; existing-Parquet validation; fixed-geometry identity across runtime chunk settings; anchor mismatch; symlink/escape/extra-file rejection; interruption after every sync/publication step; ambiguous post-visibility inspection; no-op/conflict; and reacquire-on-invalid on each host. Use fake/ordinary new data only; never feed sanitized exports or old SQLite. |
| Issue 49 — suffix execution gate | Issue 27 remains chain-generic. After all blocking decisions/implementation freeze, Issue 49 checks for intervening material protocol changes, freezes exact regime facts/endpoints/fields/role ranges, then invokes this path for one explicit contiguous Ethereum definition and one Polygon definition. Its approved plan invokes no Avalanche suffix and no priority-fee enrichment; it does not permanently reject either future scope. No old-layout reuse or outcome-bearing run occurs here. |
| Issue 63 — minimum CLI | Replace the old acquire/transfer/storage command graph with the minimum explicit command that calls the direct owner. No catalog refresh, root kind, `--replace`, alias, converter, or pre-content `cor_…` address. |

Priority fees have no active owner ticket or native gate. On a later authorized Wayfinder map
pass, retain one fog line and remove the contradictory out-of-scope duplicate. Only after
preprocessing, training, evaluation, and serving stabilize should a fresh concrete ticket be
created. Closed Issue 60 scopes its first evidence step: one bounded Ethereum
`eth_feeHistory` provider/range/provenance probe, followed by a fresh owner decision.
