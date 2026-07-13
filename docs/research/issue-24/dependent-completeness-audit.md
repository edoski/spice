# Issue 24 dependent completeness audit

Status: complete read-only audit. The approved contract is internally complete after the five corrections below. No new owner decision remains. Implementation still depends on the fixed contracts owned by issues 10, 11, 21, 22, 23, 34, 43, 46, 47, 48, and 58; this audit does not reopen them.

## Recap-critical corrections

1. **Split preprocessing ownership.** Do not persist or expose the proposed combined `PreparationState`/`fit_preparation` from `issue-24-framework-native-common-path.md:27-63`. The feature owner fits and applies one strict float64 feature-scaler state from unique training-visible physical rows. The target/task owner fits and applies the issue-58 target state from training origins after raw integer labels/minima exist. Temporal preparation selects rows and aligns facts; it fits neither state.
2. **Keep device transfer host-owned.** `HistoricalDataset` returns CPU tensors. Standard `DataLoader` owns batching, shuffle, default collation, workers, and pinning. The training or forward host moves the plain tensor mapping to its selected device. Delete batch `.to_device`/pin protocols and the current no-op Lightning transfer override plus manual batch transfer (`src/spice/modeling/lightning_module.py:66`).
3. **Retain the representation seam, not its old machinery.** ADR 0003's representation responsibility remains useful. Replace variable-length padding/masks in `modeling/representations/sequence_inputs.py` with the one fixed-context map-style `HistoricalDataset`; do not delete the responsibility or create an adapter/registry. Remove input masks from fixed-shape model calls as dependent model work.
4. **Keep issue 34's artifact ownership.** Issue 24 defines direct required facts and strict save/load validation. It does not decide SQLite versus a concrete Pydantic record or the final record layout/serialization. Delete compiler/runtime codecs and duplicated semantic projections; issue 34 places the direct fields.
5. **Store one raw fee vector, not an outcome matrix.** The deletion table's “raw fee matrix” wording is wrong. Keep one canonical raw positive-integer fee vector and origin positions. Slice `[K]` windows lazily; precompute earliest-minimum labels and minima in bounded chunks. Never persist or retain an `N x K` outcome table.

## Closed direct contract

The temporal owner exposes six plain functions and only small immutable results:

- `select_eligible_origins`: validate the already sealed canonical frame, exact issue-47 `C/H/K` geometry, regimes, role windows, purge, complete contexts, and complete future rows; return aligned row positions/block numbers.
- `earliest_minimum`: accept raw positive integer `[N, K]` chunks and return the first exact minimum index and raw minimum. No log, float conversion, tolerance, fallback, overflow action, or mask.
- `select_outcomes`: for aligned `(h, k)`, gather `B=f[h+1]`, `R=f[h+1+k]`, and `O=min(f[h+1:h+K+1])`. Issue 48 derives `S/G/Q` and summaries.
- `require_action`, `target_block`, and `broadcast_after_block`: enforce `0 <= k < K`, then return `h+1+k` and `h+k`. All `K` actions are valid; there is no mask, rescheduling, cancellation, replacement, or late broadcast.

The retained representation seam owns one concrete lazy map-style `HistoricalDataset`. Training, validation, and testing are separate instances sharing prepared row tensors, the raw fee vector, and fitted states. `__getitem__` returns a plain mapping containing fixed `[C,F]` inputs, class label, standardized scalar target, raw `[K]` outcomes, and origin block. It materializes neither overlapping contexts nor outcomes. Ordinary `DataLoader` uses default collation; train alone shuffles with an explicit generator.

Artifact save and every load validate direct chain/regime identity, `C`, `K`, ordered feature formulas, scaler and target-state width/dtype/provenance, role/corpus identity and ranges, model input width, `K`-wide classification head, scalar regression head, and exact state-dict keys/shapes. Consumers also declare and validate their requested chain/regime/`K`/corpus facts. No registry reconstruction, capability object, semantic echo, project version marker, compatibility reader, or alternate mode survives.

Canonical acquisition/sealing establishes order once. Validation and every post-seal caller reject gaps, duplicates, wrong order, wrong chain/regime, non-monotone timestamps, invalid domains, non-finite transforms, missing rows, or shape/provenance mismatches. They never sort, deduplicate, fill, clip, pad, truncate, or repair. Current hidden repairs include sorting in `features/core.py:220`, `modeling/dataset_builders/fixed_sequence_temporal.py:37`, `modeling/artifact_inference.py:215`, and `serving/inference.py:207`; validation itself sorts before assessing at `corpus/validation.py:83-89`, while `corpus/contract.py:172-186` checks only emptiness/nulls/uniqueness/one chain. Issue 47's canonical boundary must close those gaps.

## Transitive cleanup closure

| Surface | Required clean-break action | Owner boundary |
|---|---|---|
| Temporal | Delete `temporal/compilers/`, `contracts.py`, `capability.py`, `problem_store.py`, `semantics.py`, and `execution_policy/`. Replace only with direct origin/outcome/action functions and tiny values. | Issue 24 consumes 46/47/48. |
| Feature/target preparation | Delete feature-set selection/config dispatch made obsolete by the fixed ordered features, while retaining the direct formula/dependency catalog that has multiple real formulas. Delete the prediction one-entry registry/contracts and move scaling out of `temporal/input_normalization/`. Remove sort/dedup, warm-up sanitization, clipping, sample-multiplicity fitting, and fallback scales. | Issues 47 and 58 own formulas/states; 21/23 own task/loss/heads. |
| Dataset/model runtime | Delete `modeling/dataset_builders/`, `batch_plan.py`, custom batch protocols, variable padding, input/action masks, signature sorting, sampler/collator wrappers, and delayed-store rebuilding. Build three `HistoricalDataset` instances and direct `DataLoader`s. Keep trainer seed/device/precision and model architecture separate. | Issue 24 owns common preparation/representation; model/trainer owners adapt fixed `[B,C,F]`. |
| Training/tuning | Strip compiled feature/problem/prediction contexts from `modeling/pipeline.py`, `tuned_config.py`, `tuning.py`, workflow preparation, and study creation. `TrainingDefinition` fixed leaves flow directly into trials/training; no tunable lookback/problem group or semantic bundle. | Configuration/HPO owners consume the fixed definition; issue 24 supplies the dataset interface. |
| Evaluation/historical inference | Remove evaluator registry/contracts/config, Poisson/replay adapters, generic decoded/action ABI, sampled replay traversal, log-to-fee recovery, and delay-specific recompilation. Run one exhaustive model traversal over the exact declared eligible origins, then call the direct scorer and raw outcome selector. | Issues 21 and 48 own metrics/accounting. |
| Serving/scheduling | Remove compiler/prediction reconstruction, fake problem store, action masks, seconds-to-action conversion, `max_wait_seconds`, confirmation depth, slot-spacing capability, TTL scheduling, and artifact-chain bypass. Freeze exact closed `(h, hash(h))`, prepare the exact live context with artifact state, decode `k`, and share action arithmetic. Broadcast immediately for `k=0` or only on exact trigger `h+k`; `>=` in `apps/mobile/src/scheduler.ts:28` becomes exact fail-closed handling. | Issues 22/43 own API/storage/mobile transaction flow. |
| Artifacts/storage | Remove `TemporalCapabilityPayload`, runtime-metadata dispatch, generic semantics codecs, selector IDs, and duplicated capability/semantic fields from artifacts, inspection, catalog records/schema/materialization/selectors/operator, transfer, and study manifests/codecs. Remove persisted `serving/analytics.py:18` `SCHEMA_VERSION`; do not migrate it. | Issues 11 and 34 own identity, direct loaders, and record placement. |
| Config/CLI | Delete `ProblemSpec`, `PredictionConfig`, evaluator/delay selectors, compiler/policy fields, sequence min/max lengths, problem tuning parameters, and their group/surface/selection/resolution/snapshot/CLI plumbing. Remove `conf/problem/`, `conf/prediction/`, `conf/evaluator/`, obsolete surface fields, training sequence bounds, and tuning-space lookback entries. Provider/worker/pinning/device polling values remain ephemeral host inputs. | Issue 10 owns selector removal; issue 18 owns final direct definition/config surface. |
| Benchmarks | Rewrite benchmark plans, collectors, run-state/result-index codecs, report fields, scripts, and YAML that key on problem/prediction/evaluator/delay IDs or seconds-derived action horizons. Historical CSV exports remain evidence, not a compatibility contract. | Benchmark owners consume the direct facts. |

Acquisition planning currently compiles features and a problem solely to discover source requirements; it should request the fixed ordered raw columns directly. `corpus/coverage.py:50-88` validates compiled contracts and seconds spans; replace that with direct block-range sufficiency for feature support, `C`, `H`, `K`, role/regime bounds, and purge. Timestamps remain factual/descriptive, never geometry.

Serving must select and validate the exact-`K` artifact before freezing the snapshot. A changed head/hash, reorg, missing row, stale snapshot, wrong artifact, or already-passed trigger fails closed. Historical inference may reuse `HistoricalDataset` only when complete future rows exist; live preparation stays a separate function because it has no outcomes or labels.

## Stale documentation and tests

ADR 0002, ADR 0004, and `CONTEXT.md` still require owner registries, the compiler registry, `CompiledProblemContract`, `TemporalCapability`, action-space/policy, target-batch, batch-plan, and replay vocabulary; supersede those clauses with the direct contract. Keep ADR 0003's representation responsibility, but remove its adapter/variable-input and persisted-representation-id claims. Rewrite or delete the matching architecture/implementation documents under `temporal/`, `features/`, `prediction/`, `evaluation/`, `modeling/`, `modeling/dataset_builders/`, `storage/`, `config/`, `conf/`, `workflows/`, and serving. Do not preserve old terms as aliases.

The issue body is also stale where it asks to preserve action masks, stochastic evaluation, fallback/deadline behavior, and persisted versions. The approved contract supersedes those phrases with complete exact-`K` actions, exhaustive evaluation, exact block triggers with fail-closed misses/reorgs and no fallback, and strict direct validation with no project-owned version marker.

Delete tests whose subject disappears: temporal compiler/store/capability/execution-policy/realization tests; custom batch-plan, old dataset-builder, variable representation, decoded-offset, evaluator, replay, and old accounting tests. Retarget scaler, task/head, model runtime, training, inference, artifact, serving, config, corpus/workflow, storage/study, CLI, and benchmark tests to their direct owners.

Keep replacement coverage lean:

1. One canonical hand-written frame proves role/regime geometry, purge, raw earliest ties, `B/R/O`, and target/trigger arithmetic.
2. One preprocessing/dataset test proves separate training-only states, lazy fixed slices, default-collation shapes, role order, and train-only deterministic shuffle.
3. One artifact-validator mismatch table covers chain/regime/`C/K`, formula/state provenance, tensor widths, head shapes, corpus identity, and strict state dict.
4. Sibling-owner fixtures cover one exhaustive post-fit scorer pass and exact hash-bound serving triggers, including immediate `k=0` and no late broadcast.

No compatibility, migration, registry/codec round-trip, old/new parity, architecture-transition, or duplicated caller-arithmetic tests.

## Verdict

The whole-contract recap is ready for explicit approval once it includes the five corrections above and the transitive cleanup table. The completeness audit found no unresolved consequential decision inside issue 24. Remaining work is implementation sequencing across named owners, not a new design choice; issue 24 must not close before Edo approves the corrected compact recap.
