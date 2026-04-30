# Execution Architecture

## Purpose

`execution` owns remote target models, **Execution Session** creation, SSH command execution, Slurm submission, remote workflow entrypoints, and SSH/rsync transfer orchestration. It receives explicit target names from operator edges.

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
hydrate_resolved_workflow_config()
    |
    v
train/tune/evaluate workflow
```

Remote execution does not re-resolve surfaces. The local process chooses all named config pieces first. The remote process receives the fully resolved snapshot and reconstructs concrete nested config types through owner coercers.

## Target Rule

Execution sessions require an explicit target name. The CLI supplies `DEFAULT_REMOTE_TARGET` when an operator does not pass `--target`.

```text
CLI default allowed here:
  spice train --submit

No hidden default here:
  session = open_execution_session(target_name)
```

This keeps execution reusable for tests, scripts, and future target selection without a hard-coded cluster dependency in the service layer.

## Supported Resolved Workflows

The remote runner supports already resolved workflow snapshots:

```text
train
tune
evaluate
```

Acquire is not routed through this resolved-snapshot hydration path. Acquisition has provider/RPC behavior and storage commit mechanics that are resolved through the normal acquire workflow path.

## Transfer Boundary

`execution.transfer` owns cluster push/pull orchestration. It receives an **Execution Session**, runs remote helper commands, invokes rsync, and delegates local path/root-kind operations to storage lifecycle and catalog services. The remote helper remains `spice.storage.sync_cli` because it performs local storage operations on the remote machine, not workflow execution.
