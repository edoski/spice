# Spice Architecture Guide

## Purpose

Spice is a modular machine-learning system for blockchain fee-decision research. It turns raw block history into temporal learning examples, trains models, decodes predictions into decisions, evaluates those decisions against fee outcomes, and persists the resulting datasets, studies, and artifacts.

The architecture is intentionally split into generic domains. Concrete implementations exist, but workflows should usually see only configs, contracts, typed runtime objects, and storage roots.

## End-To-End Shape

```text
CLI / benchmark / remote runner
  -> config resolution
  -> workflow orchestration
  -> corpus acquisition or corpus loading
  -> feature table construction
  -> temporal problem store construction
  -> dataset-builder tensorization
  -> model training or model inference
  -> prediction-family loss/decode
  -> evaluator scoring
  -> storage commit / catalog reindex
```

For a beginner: the model does not learn directly from blockchain JSON. Blocks first become canonical rows. Rows become feature columns. Feature columns plus temporal rules become supervised examples. Dataset builders turn examples into tensors. Prediction families define what the model predicts. Evaluators score decoded decisions in economic terms.

## Generic Seam Pattern

Most modular domains follow the same pattern:

```text
human config or payload
        |
        v
owner coercer validates concrete config
        |
        v
local spec table selects implementation
        |
        v
compiled contract exposes behavior
        |
        v
workflow uses contract, not concrete class
```

Each spec table belongs to the package that owns the behavior. Implementation knowledge stays local:

```text
features       -> feature families
temporal       -> compilers, realization policies, input normalization
prediction     -> prediction families
evaluation     -> evaluator adapters
modeling       -> dataset builders and model families
objectives     -> objective contracts
```

Config validation and compile dispatch are separate. Coercers reconstruct concrete config models from YAML or persisted payloads. Compile registries then assert that the config object matches the selected spec type before calling the concrete compiler.

## Boundary Rules

```text
CLI owns user conveniences
  -> config/execution receive explicit values
  -> workflows receive hydrated configs
  -> domains receive contracts and typed state
```

`DEFAULT_REMOTE_TARGET = "disi_l40"` exists only at the CLI edge. Downstream execution and transfer APIs require an explicit target name. This makes the operator default convenient without leaking cluster-specific behavior into core workflow code.

Prediction and evaluation are separate. Prediction families produce decoded-result kinds, such as offset decisions. Evaluators declare which decoded-result id they accept. The modeling scoring service is the bridge that runs inference, checks the accepted result id, and calls the evaluator.

Storage is its own domain. Root kind, layout, root-local SQLite state, catalog indexing, root lifecycle, and persisted payload decoding live there. Remote transfer orchestration lives in execution. Workflows call storage primitives instead of moving directories or opening state databases ad hoc.

## Dependency Direction

```text
core
  ^
  |
domain configs / contracts / registries
  ^
  |
modeling, storage, acquisition services
  ^
  |
workflows
  ^
  |
cli and remote runner
```

Lower layers may define shared vocabulary. Higher layers coordinate. Lower layers should not inspect CLI flags, resolve workflow surfaces, or know execution-target defaults.

## Root Concepts

```text
corpus   raw canonical block data for one chain/dataset identity
study    tuning/search state and provenance
artifact trained model plus runtime summaries and evaluations
```

These are separate storage root kinds because they have different lifecycle rules and state schemas. Root-local state is authoritative; the catalog is a searchable index that can be rebuilt.

`config` describes user intent. `contract` describes executable meaning. `adapter`, `family`, `builder`, and `compiler` are local implementation selectors. A named YAML config may choose an adapter, but the named config is not itself the adapter.

## Guide Index

```text
src/spice/ARCHITECTURE.md                         package-level domain map
src/spice/core/ARCHITECTURE.md                    shared primitives and spec helpers
src/spice/config/ARCHITECTURE.md                  YAML, surfaces, resolved hydration
src/spice/conf/ARCHITECTURE.md                    checked-in declarative specs
src/spice/cli/ARCHITECTURE.md                     command edge and remote default
src/spice/execution/ARCHITECTURE.md               remote targets and resolved execution
src/spice/workflows/ARCHITECTURE.md               task orchestration
src/spice/acquisition/ARCHITECTURE.md             raw block acquisition
src/spice/corpus/ARCHITECTURE.md                  canonical block corpus
src/spice/features/ARCHITECTURE.md                feature contracts and family internals
src/spice/temporal/ARCHITECTURE.md                problem stores and temporal theory
src/spice/modeling/ARCHITECTURE.md                tensorization, training, inference
src/spice/prediction/ARCHITECTURE.md              targets, losses, decoding
src/spice/evaluation/ARCHITECTURE.md              evaluator contracts and metrics
src/spice/objectives/ARCHITECTURE.md              optimization objective selection
src/spice/benchmarks/ARCHITECTURE.md              benchmark specs, plans, runs, collection
src/spice/storage/ARCHITECTURE.md                 root state, catalog, lifecycle
```

Subpackage guides document generic seams and enough theory to understand why the seam exists. Concrete implementation notes may appear where they clarify a generic pattern, but the primary goal is architecture and learning, not a catalog of every experiment setting.
