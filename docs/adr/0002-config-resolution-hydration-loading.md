# ADR 0002: Config Resolution, Hydration, And Loading Seams

## Status

Retired.

## Context

Workflow Selection resolution, Resolved Workflow Snapshot hydration, and Config Group loading all turn raw configuration into typed objects. Keeping those paths behind one generic workflow-config coercer made the Interface shallow: fresh resolution passed already typed pieces through raw hydration logic, while snapshot hydration needed the same owner coercers for a different reason.

Named Config Groups also serve two different callers. Operators need raw canonical payloads for show/edit/template workflows. Workflow resolution needs typed owner configs.

Abstract owner config bases such as `ModelConfig`, `EvaluatorConfig`, or `ExecutionPolicyConfig` are not enough for execution. The owner registry must redispatch them by id and validate the concrete local-spec config type before runtime code sees them.

## Decision

Fresh Workflow Selection resolution constructs `AcquireConfig`, `TrainConfig`, `TuneConfig`, and `EvaluateConfig` directly from already typed resolved pieces.

Resolved Workflow Hydration lives with the snapshot codec. It accepts raw Resolved Workflow Snapshot payloads for train, tune, and evaluate, validates the workflow marker, and calls owner coercers to rebuild concrete nested configs. Acquire remains unsupported for snapshots.

Concrete Owner Config means the concrete local-spec config selected by an owner id. Owner coercers preserve identity only for Concrete Owner Config instances. Abstract typed selector configs are dumped to a mapping, redispatched by id, and validated as the concrete type. Invalid or incomplete selector configs fail at the owner boundary with `ConfigResolutionError`.

Config Group Loading has separate Interfaces:

- raw canonical payload loading for display, editing, fixture mutation, seed/template creation, benchmark raw specs, and canonical YAML output
- typed owner config loading for context-free groups used by resolution

Both interfaces may share group catalog metadata and validators, but raw loading still returns canonical dictionaries while typed loading returns concrete typed configs.

Contextual tuning-space loading stays in resolution because its validity depends on the selected model and problem. Benchmark typed loading stays in the benchmark module.

Tuned-parameter application is a typed Workflow Config transform, not a Resolved Workflow Hydration caller. It applies tuned params by constructing validated concrete nested configs and rebuilding the train or tune config directly.

Runtime evaluator contracts and training policy fields carry typed configs. Durable payloads are produced only by storage codecs and snapshot codecs.

## Consequences

Raw JSON/dict handling is localized to Resolved Workflow Hydration, raw Config Group loading, benchmark typed ledgers with benchmark-local run-state codecs, and storage codecs. Surface resolution stays typed after selection overrides. Owner packages keep concrete dispatch for nested configs. There are no compatibility shims for deleted shallow Interfaces.
