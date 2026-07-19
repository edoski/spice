# FABLE (Fee Analysis through Blockchain Learning and Estimation) Architecture

FABLE is organized around strict request values, direct owner functions, native library objects, and UUID-addressed durable objects. Dependencies point from operator edges toward scientific owners.

## System shape

```text
strict JSON request
        |
        v
CLI or direct Python call
        |
        +--> acquisition --> Corpus
        +--> tuning ------> Study
        +--> fitting -----> native Lightning artifact
        +--> evaluation --> observations.parquet
        |
        v
transient reducers and caller-chosen TSV evidence
```

`fable.config` owns frozen Pydantic values and small discriminated unions. `fable.requests` mints fresh UUIDv4 instances. Each owning operation revalidates the complete request at its boundary.

## Dependency direction

```text
CLI / serving / experiment scripts
                |
                v
execution, acquisition, study, evaluation
                |
                v
modeling, temporal, min_block_fee, corpus
                |
                v
strict config values and canonical addresses
```

Each package owns one system seam:

- `corpus` owns canonical completed block data and exact validation.
- `temporal` owns causal feature state, fixed-block context/outcome geometry, and lazy historical examples.
- `min_block_fee` owns target state, classification support, loss, two-head output, and decode.
- `modeling` owns the three concrete neural definitions, Lightning fitting, and native checkpoint loading.
- `study` owns bounded candidate membership, ordered retained results, publication, and selected-result materialization.
- `evaluation` owns canonical observations, one-evaluation reduction, and sealed report composition.
- Top-level `experiments` owns the S16 and S18 experiment protocols.

## Durable object flow

### Corpus

`CorpusRequest` names an inclusive chain block range and its UUID. `acquire_corpus()` reads ordinary block RPC responses in deterministic order into an owner-local hidden sibling. It validates chain identity, links, timestamps, fee and gas domains, proves ancestry to a finalized anchor, writes the exact `corpus.json` and `blocks.parquet`, removes transport-only hashes, then renames the hidden directory to the canonical Corpus address.

### Study and artifact

`TuneRequest` contains one `ExperimentSemantics` and a finite, family-specific `MethodSpace`. `run_candidate()` prepares training state, fits one supplied Method, and appends one successful `RetainedResult` to Study scratch. `publish_study()` renames the ordered result set to its canonical JSON file.

A baseline `TrainRequest` embeds its complete `TrainingDefinition`. A selected-Study request instead names the exact Study UUID and result index while carrying the experiment. Training loads that exact row, reconstructs the definition from its Method, fits through Lightning, and renames the native weights-only best checkpoint to the artifact UUID address. The checkpoint embeds the request, feature and target state, optional classification support, and—only for selected-Study training—the exact result index and Method.

### Evaluation and derived evidence

`EvaluateRequest` names an artifact, same-source Corpus, validation or testing origin window, and evaluation UUID. Evaluation rebuilds historical examples with persisted state, runs the artifact on CUDA, writes one nonnull ordered observation per origin, and publishes `evaluation.json` with `observations.parquet`.

`reduce_evaluation()` reads that durable object and its artifact association to return one transient scientific row. `write_sealed_report()` combines explicit testing evaluation IDs in caller order and publishes a derived TSV. The context-history and fee-condition evidence writers live in `experiments/` with their fixed scientific matrices.

## Training and inference

Historical preparation produces lazy datasets over contiguous feature, fee, and block-number backing.

The model union is closed: LSTM, Transformer, or Transformer-LSTM. Every model consumes float32 `[B,C,F]` and returns action logits `[B,K]` plus a scalar standardized minimum-fee prediction `[B]`. The architecture is independent of target construction and evaluation accounting.

Live serving loads cwd-local `SERVING.yaml` once, selects an exact artifact cell, freezes the latest closed head, reads its `C-1` predecessors, applies the checkpoint's ordered feature state, runs one CPU batch, and returns the decoded target coordinate.

## External boundaries

Acquisition and serving use ordinary Web3 RPC clients supplied at their operator boundaries.

`fable.execution.submit()` is the boundary to native OpenSSH and Slurm execution. [ADR 0007](docs/adr/0007-native-external-execution-boundary.md) records that ownership decision.

Completed objects have direct canonical addresses and own their exact requests once. UUIDs provide instance identity; associations provide meaning. See [ADR 0006](docs/adr/0006-direct-durable-object-authority.md).

## Deep interfaces

Five source guides document the deep interfaces:

- [Acquisition](src/fable/acquisition/ARCHITECTURE.md)
- [Temporal preparation](src/fable/temporal/ARCHITECTURE.md)
- [Minimum-block-fee task](src/fable/min_block_fee/ARCHITECTURE.md)
- [Study](src/fable/study/ARCHITECTURE.md)
- [Evaluation](src/fable/evaluation/ARCHITECTURE.md)

Exact request fields, addresses, commands, remote input, and schemas belong to the [reference](docs/reference.md). Scientific equations and claims belong to the [theory](docs/theory.md).
