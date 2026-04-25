# Execution Architecture

## Purpose

`execution` owns remote target models, SSH command execution, Slurm submission, and remote workflow entrypoints. It receives explicit target names from callers.

## Flow

```text
CLI submit command
    |
    v
resolve workflow config locally
    |
    v
serialize resolved config JSON
    |
    v
ssh + sbatch remote command
    |
    v
python -m spice.execution.remote_runner <task> <config_json>
    |
    v
hydrate_model_workflow_config()
    |
    v
train/tune/evaluate workflow
```

Remote execution does not re-resolve surfaces. The local process chooses all named config pieces first. The remote process receives the fully resolved snapshot and reconstructs concrete nested config types through owner coercers.

## Target Rule

Execution APIs require `target_name`. The CLI supplies `DEFAULT_REMOTE_TARGET` when an operator does not pass `--target`.

```text
CLI default allowed here:
  spice train --submit

No hidden default here:
  submit_execution_workflow(task, config=..., target_name=...)
```

This keeps execution reusable for tests, scripts, and future target selection without a hard-coded cluster dependency in the service layer.

## Supported Remote Workflows

The remote runner supports model workflows:

```text
train
tune
evaluate
```

Acquire is not routed through this resolved model-workflow hydration path. Acquisition has provider/RPC behavior and storage commit mechanics that are resolved through the normal acquire workflow path.
