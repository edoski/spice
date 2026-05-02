# ADR 0002: Config Resolution, Hydration, And Loading Seams

## Status

Accepted.

## Context

Workflow Selection resolution, Resolved Workflow Snapshot hydration, and Config Group loading all turn raw configuration into typed objects. Keeping those paths behind one generic workflow-config coercer made the Interface shallow: fresh resolution passed already typed pieces through raw hydration logic, while snapshot hydration needed the same owner coercers for a different reason.

Named Config Groups also serve two different callers. Operators need raw canonical payloads for show/edit/template workflows. Workflow resolution needs typed owner configs.

## Decision

Fresh Workflow Selection resolution constructs `AcquireConfig`, `TrainConfig`, `TuneConfig`, and `EvaluateConfig` directly from already typed resolved pieces.

Resolved Workflow Hydration lives with the snapshot codec. It accepts raw Resolved Workflow Snapshot payloads for train, tune, and evaluate, validates the workflow marker, and calls owner coercers to rebuild concrete nested configs. Acquire remains unsupported for snapshots.

Config Group Loading has separate Interfaces:

- raw canonical payload loading for display, editing, fixture mutation, seed/template creation, benchmark raw specs, and canonical YAML output
- typed owner config loading for context-free groups used by resolution

Contextual tuning-space loading stays in resolution because its validity depends on the selected model and problem. Benchmark typed loading stays in the benchmark module.

## Consequences

Raw JSON/dict handling is localized to Resolved Workflow Hydration and raw Config Group loading. Surface resolution stays typed after selection overrides. Owner packages keep concrete dispatch for nested configs. There are no compatibility shims for deleted shallow Interfaces.
