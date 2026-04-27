# Config Architecture

## Purpose

`config` turns human-facing YAML and CLI selections into typed runtime configs. It is the edge where names become objects. Downstream code should receive explicit, hydrated config models instead of resolving strings again.

## Mental Model

```text
surface YAML + CLI overrides
          |
          v
workflow request model
          |
          v
named YAML groups loaded from conf/
          |
          v
owner coercers rebuild concrete nested configs
          |
          v
AcquireConfig / TrainConfig / TuneConfig / EvaluateConfig
```

Configuration has two jobs:

```text
composition  choose named pieces and apply request overrides
validation   turn those pieces into typed models with clear errors
```

The config package should not train models, evaluate predictions, acquire blocks, or write artifacts. It resolves intent.

## Owner Coercion

Generic Pydantic validation cannot always reconstruct concrete nested types. The owning package knows which selector maps to which concrete type:

```text
evaluation.engine        -> evaluation config type
dataset_builder.id       -> dataset-builder config type
model.id                 -> model-family config type
problem.compiler.id      -> problem compiler config type
problem.execution_policy.id   -> execution-policy config type
```

So config hydration calls owner coercers. This keeps all implementation-selection knowledge in the owning domain.

## Resolved Snapshot Hydration

Remote execution and tuned-parameter reapplication do not re-resolve surfaces. They rehydrate an already resolved config snapshot:

```text
resolved Train/Tune/Evaluate config
        |
        v
model_dump_json()
        |
        v
remote runner or tuned-param materialization
        |
        v
hydrate_model_workflow_config()
        |
        v
owner coercers reconstruct concrete nested configs
```

`hydrate_model_workflow_config()` is intentionally model-workflow-only. It supports train, tune, and evaluate. Acquire has different acquisition/provider concerns and is resolved through normal workflow resolution.

## Public API Boundary

`spice.config` exports resolved config types, workflow request types, `resolve_workflow_config()`, and config-owned coercers such as `coerce_problem_spec()` and `coerce_features_config()`.

It does not re-export dataset-builder coercion. Dataset-builder config coercion belongs to `spice.modeling.dataset_builders`.

## Default Remote Target

The CLI owns the convenience default:

```text
DEFAULT_REMOTE_TARGET = "disi_l40"
```

Resolved configs and execution APIs do not carry a hidden fallback target. Submitted commands pass an explicit target name downstream.

## Extension Points

Add a public config group when users need to name, inspect, or edit that spec. Add a request override only when it is a legitimate workflow selection or runtime control. Add concrete implementation selection in the owner package, not in config.
