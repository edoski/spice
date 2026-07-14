# Minimum clean CLI prototype

## Question and evidence budget

Question: after deleting every leaf that only wraps ordinary filesystem, shell, SSH, rsync, or
library behavior, what is the minimum command surface that still performs the approved thesis
workflow and preserves the L40/MacBook host split?

The cheapest discriminating observation is a pure command-spec simulation. For each proposed leaf,
replace it with an ordinary operator action; retain it only when typed scientific validation,
approved remote-control semantics, or process startup remains impossible. Budget: 45 minutes, zero
RPC calls, zero Slurm calls, zero storage writes outside this research directory, and zero model
execution. Stop when every leaf has a concrete necessity proof and every duplicate wrapper is gone.

Run the disposable terminal prototype:

```console
uv run python docs/research/issue-63/prototype.py
```

The complete current read-only inventory is in [`current-inventory.md`](current-inventory.md).

## Recommended complete surface

`$CLI` is a placeholder; Issue 59 owns the final entry-point/display spelling. Publish exactly one
wheel entry point to one plain Typer application with completion disabled.

```text
$CLI
├── submit REQUEST.json --root ROOT --remote REMOTE.yaml --commit SHA
├── follow JOB_ID --remote REMOTE.yaml
├── corpus
│   ├── acquire REQUEST.json --root ROOT --rpc-url URL
│   └── finalize CORPUS_ID --root ROOT --rpc-url URL
├── study
│   ├── run TUNE_REQUEST.json METHOD.json --root ROOT --remote REMOTE.yaml --commit SHA
│   └── finalize STUDY_ID --root ROOT
└── remote
    ├── workflow --root ROOT       # generated Slurm script only; exact request on stdin
    └── candidate --root ROOT      # generated Slurm script only; private payload on stdin
```

This is six operator leaves plus two Slurm-worker leaves, down from 24 Typer leaves plus
four argparse helper leaves. `remote` stays in the same application/codebase, is absent from normal
help, requires `SLURM_JOB_ID`, and rejects local invocation. It is not a second tree or host
abstraction.

### Necessity proof for every leaf

`submit` accepts only complete strict TrainRequest or EvaluateRequest JSON. It validates and
persists the request through the generic owner, reloads it by typed equality, verifies the explicit
clean remote commit, quotes the same request into the batch script, invokes `sbatch --parsable`
once, and prints the numeric job ID. Combining these steps prevents a second plan, local trainer,
request snapshot, or shell payload codec. Validation is an EvaluateRequest over the frozen
validation role, not another command.

`follow` owns the already-approved `squeue --json` then `sacct` state interpretation, bounded
visibility/backoff, best-effort log following, final drain, and Ctrl-C detach without `scancel`.
Recreating that contract as ad hoc shell commands would duplicate real behavior, so this leaf
survives. It receives an explicit numeric job ID and never reads stored job state.

`corpus acquire` owns provider reads, provider-only retry, bounded concurrency, exact request
persistence, prefix validation, cancellation, and ordered hidden Parquet writes. `corpus finalize`
owns schema/domain/range/order/link validation, finalized ancestry, exact header reread, minimal
manifest construction, and direct rename. Neither can be replaced by `cp`, `mv`, or Polars alone.

`study run` persists/reloads one TuneRequest, validates one complete operator-supplied Method
against its frozen MethodSpace, and submits one private candidate payload. Candidate work is not a
WorkflowRequest, plan, queue, or local fit. `study finalize` validates the current manually curated
snapshot, constructs the immutable Study, and directly renames it. A plain `mv` cannot establish
those study semantics.

`remote workflow` is the one Slurm-only hydration/dispatch entry for Train/Evaluate requests.
`remote candidate` is separate because its ephemeral private payload is intentionally not a
WorkflowRequest. Combining them would create a false generic execution-input union. Neither is a
local training command.

### One direct remote file remains

`REMOTE.yaml` is retained, but it is not a target registry or named target. It is one explicit
runtime file with no ID, lookup, inheritance, aliases, defaults, or persistence. The approved SSH
alias, absolute repository/Python/storage/log paths, and direct Train/Tune/Evaluate Slurm resources
are host facts required together by `submit`, `study run`, and `follow`. Hard-coding Edo's paths,
repeating them as many flags, or hiding them in environment variables is larger and less legible.
The existing mature YAML/Pydantic loaders suffice; no configuration framework survives.

### Owners without CLI leaves

Not every owner function becomes a command.

- No request persist/load leaf. `submit` and `study run` persist and reload before work. `cat` or
  `jq` inspects a request.
- No corpus/study/artifact/evaluation listing. `find` or `ls` enumerates the single-operator root;
  exact consumers validate the UUID they use. There is no invalid-entry JSON/error policy.
- No transfer command. The operator uses ordinary `rsync` into the owner-local hidden sibling and
  `mv` after inspection. The next exact consumer's normal loader validates the object. There is no
  generic kind, direction, result, receipt, replacement, or recovery layer.
- No serving wrapper. On the MacBook, four direct environment values feed the application factory,
  and mature Uvicorn launches it:

  ```console
  STORAGE_ROOT=ROOT ETHEREUM_RPC_URL=URL POLYGON_RPC_URL=URL AVALANCHE_RPC_URL=URL \
    uv run uvicorn --factory spice.serving:create_app --host 0.0.0.0 --port 8000
  ```

  The factory owns only the fixed twelve-artifact stateless FastAPI application and three RPC
  clients. It has no target, commit, GPU, CUDA, precision, Slurm, worker, wallet, transaction,
  cache, health, readiness, analytics, or artifact-selection input. Expo remains presentation only.
- No standalone validate/show/query/filter/export command. Direct consumers validate; ordinary
  filesystem tools inspect.

The twelve approved thesis lists remain twelve named pure constructors: capacity/activity Train
and validation Evaluate; UTC Train additions and validation Evaluate additions; CE Train additions
and validation Evaluate additions; family Train additions and validation Evaluate additions;
selected-family Tune; selected-family context Train additions; selected-family final-K Train; and
sealed-test Evaluate. They construct and persist the ordered exact requests directly. They are not
CLI commands and create no selector, batch file, runner, plan, list state, or benchmark vocabulary.
Totals remain 60 Train, 3 Tune, and 69 Evaluate requests.

Operator-only archive custody and one-way cutover remain external ticket-owned filesystem
procedures. They receive no wheel commands, imports, readers, converters, or compatibility paths.

## Native output, errors, help, and framework

There is no output or exit abstraction. `submit` and `study run` print the bare numeric Slurm job
ID required by the next `follow` invocation. `follow` and owner functions stream their existing
plain logs. Finalizers may print their resulting canonical path. Uvicorn uses its native CLI/logs.
Typer handles syntax/help; owner/library exceptions and process exit status remain native. Ctrl-C
during `follow` detaches without canceling and returns the ordinary interrupted status. No JSON,
JSONL, Rich panel, reporter, warning formatter, `OperatorTyper`, command factory, error adapter, or
shared output helper survives.

Keep Typer. Even with nine leaves, nested `argparse` subparsers would recreate path conversion,
command help, and registration in more code; Click direct keeps Click while losing annotations.
Plain Typer with explicit signatures remains smaller. No completion command is registered.

No tests belong to this disposable prototype. Later implementation needs one focused CLI routing
test for the public/Slurm/MacBook boundary; owner modules test their own semantics. Delete the 18
current command-facing tests with their obsolete commands instead of replacing them one-for-one.

## Clean-break deletion

Delete request load/show, all typed scans/listing/invalid-entry rendering, every typed push/pull
wrapper, generic benchmark, config registry/editor, selector query/filter, generic export,
per-record delete/cascade, refresh/catalog, replacement, local train/tune/evaluate wrappers,
dependency/detach, trial-count, plan, restart, reconcile, marker, lock, archive, conversion,
root-kind, sync helper, serving wrapper, plugin, alias, compatibility, output, reporter, and
error-adapter surfaces.
Add no legacy reader, shim, dual tree, version marker, transition test, or forwarding command.

The prototype audit reports eight commands, zero missing required capabilities, zero forbidden
command words, zero local training commands, and zero project serving wrappers. This is planning
evidence only; it changes no production code, configuration, tests, dependency, data, storage, job,
training, evaluation, acquisition, or serving implementation.
