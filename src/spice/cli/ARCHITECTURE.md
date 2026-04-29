# CLI Architecture

## Purpose

`cli` is the operator edge. It translates command-line options into workflow selections, config-inspection actions, storage inspection/deletion, benchmark expansion, and remote transfer operations.

The CLI may provide user conveniences. It should not own model training, evaluator logic, storage layout internals, or YAML hydration rules.

## Command Flow

```text
operator command
    |
    v
Typer option parsing
    |
    v
workflow selection / storage selector
    |
    v
config resolution or storage service
    |
    v
workflow/service result rendered to stdout
```

Workflow commands either run locally or submit a resolved config snapshot to remote execution. Transfer commands call execution transfer services. Config commands call config registry APIs.

`cli.selection` is the **CLI Selection Layer**. It turns explicit operator values into typed **Workflow Selections**, validates local-vs-submitted command rules, and resolves the **Workflow Config** handed to workflow execution or an **Execution Session**.

## Remote Target Boundary

```text
CLI option default:
  DEFAULT_REMOTE_TARGET = "disi_l40"

Downstream APIs:
  open_execution_session(target_name)
  transfer(..., session=...)
```

The default exists once, at the CLI edge. This lets the common cluster stay convenient without making lower layers cluster-aware.

## Shared Options

`cli.options` owns common option aliases such as filters, storage-root options, and `RemoteTargetOption`. Workflow submit commands and transfer commands use the same target option so help text and behavior stay consistent.

Within workflow commands, generic execution-panel options share one helper. Selection options, output options, and execution options are distinct because they represent different operator decisions.

## Local Versus Submitted Runs

```text
local run:
  may use --storage-root
  resolves config and runs workflow in current process

submitted run:
  may use --target, --dependency, --detach
  may not use --storage-root
  remote storage comes from the execution target spec
```

This prevents a local filesystem override from accidentally leaking into a remote job.
