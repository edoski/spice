# Issue 19 remote-control contract audit

Date: 2026-07-13. Status: approved decision checkpoint and dependent completeness audit for [Choose the remote execution control architecture](https://github.com/edoski/spice/issues/19). This is not the Resolution comment and does not authorize production implementation.

## Approved decisions

Edo explicitly approved all six decisions:

1. Use split concrete OpenSSH/rsync and Slurm functions. Keep shared process helpers private. Add no `Session`, transport/scheduler protocol, adapter, backend, or framework.
2. Submit only the approved typed `WorkflowRequest`. Serialize with its one schema-owned `TypeAdapter`, carry the JSON through the batch script, hydrate it from standard input, and reject oversized requests conservatively. Add no task argument, snapshot codec, or remote request-file lifecycle.
3. Accept only `afterok` predecessor job IDs. Use `--kill-on-invalid-dep=yes` only after the target proves support; fail preflight if the required behavior is unavailable.
4. Follow with deployed `squeue --json`, narrow `sacct` parsable-text fallback, capped-backoff polling, best-effort `tail -F`, and Ctrl-C detach without cancellation.
5. Require an exact clean remote commit before submission and recheck it at job start. Never pull, checkout, update, or repair the remote checkout automatically.
6. Load one runtime-only target YAML with an OpenSSH alias, direct absolute paths, and direct per-workflow Slurm resources. Add no target id, registry, persisted target identity, or follow policy.

Framework evidence remains in [issue-19-remote-control-frameworks.md](../issue-19-remote-control-frameworks.md). Submitit, Fabric/Paramiko, Parsl, `slurmrestd`, and DRMAA all fail the whole-seam deletion test.

## Complete contract draft

### External interface and module depth

The execution interface is concrete and owner-shaped:

```python
load_target(path) -> Target
revision(target) -> str
submit(target, request, expected_revision, *, after_ok=()) -> str
follow(target, job_id) -> str
```

`submit` returns the numeric Slurm job ID only. The log path is derived as `<log_root>/<job_id>.out`. The request already carries its workflow discriminator and object IDs; execution must not repeat them in a job/provenance envelope.

OpenSSH command execution and rsync invocation are private implementation functions shared by Slurm and typed transfer operations. CLI, direct-plan, benchmark, collection, storage, and workflow callers never receive raw SSH, shell, rsync, or scheduler primitives. Tests cross the concrete owner interface rather than injecting a public fake transport.

### Runtime target

One strict YAML value is selected explicitly for an invocation. It has no embedded id:

```text
ssh: OpenSSH destination alias
repo_root: absolute remote repository path
python: absolute remote Python executable
storage_root: absolute remote clean storage root
log_root: absolute remote Slurm log root
train | tune | evaluate:
  partition
  gpus
  cpus_per_task
  memory_gb
  time_limit
```

Resource selection is one direct match on `request.workflow`, not a registry. OpenSSH owns user, hostname, proxy, key, host-key, and connection policy through its normal configuration. Commands use noninteractive OpenSSH without a pseudo-terminal. Target loading and read-only preflight validate contained absolute paths, the expected tools, required Slurm options, and that the repository, Python, storage, and log locations already exist with the required type/access. Execution does not create or repair storage roots or deployment directories.

The target value and its file path are runtime facts. Execution does not copy them into `WorkflowRequest`, transfer records, result records, or durable provenance. Issue 30 owns any separately approved attempt fact; Issue 34 owns exact durable provenance fields.

### Revision and submission

`revision(target)` reads `git -C <repo_root> rev-parse --verify HEAD`, requires one full commit hash, and requires empty `git status --porcelain --untracked-files=all`. Submission receives that exact expected commit. The batch script repeats the commit and clean-check immediately before the remote runner starts. Mismatch or dirt fails before request hydration or workflow side effects.

There is no pull, checkout, fetch, worktree creation, code rsync, package install, or repair path. Concurrent mutation after the job-start check remains an explicit single-operator limitation; solving it requires a separately approved immutable deployment mechanism.

The approved request adapter emits compact JSON. JSON bytes over 1,048,576 bytes fail locally with the measured size before SSH. The JSON is one quoted-heredoc body in the script and becomes the remote runner's standard input. The runner performs exactly:

```python
request = WORKFLOW_REQUEST_ADAPTER.validate_json(sys.stdin.buffer.read())
run(request, storage_root=runtime_storage_root)
```

The runner receives the storage root as runtime input. It does not receive a repeated task, ID, target, log path, execution reference, resolved-field record, or snapshot. It dispatches directly on `request.workflow`.

The script uses the absolute Python executable, repository working directory, direct Slurm resources, and `<log_root>/%j.out`. Issue 26 owns any explicit training-host environment/module setup; execution adds no arbitrary preamble, hook, environment registry, or framework-neutral host machinery.

Submission uses script standard input and `sbatch --parsable`. It accepts an optional semicolon-delimited cluster suffix but requires one numeric job ID and no other output. It never retries `sbatch`. A transport failure after the controller may have accepted the job is reported as an ambiguous outcome; Issue 30 owns reconciliation and attempt persistence.

### Dependencies

The caller supplies only validated predecessor job IDs. Execution renders one `afterok:<id>:<id>` dependency and no other dependency language. The target must prove `--kill-on-invalid-dep=yes` support during read-only preflight; unsupported targets fail rather than silently creating indefinitely pending dependents.

Issue 18 owns experiment enumeration. Issue 30 owns attempt selection, recovered job IDs, submission order, crash reconciliation, retries, and the authoritative attempt. Execution only maps exact predecessor job IDs to Slurm.

### State and follow

Active lookup uses `squeue --json -j <job_id>`. The parser requires the expected top-level shape, rejects reported errors, matches the exact job ID, and reads its Slurm-owned state. Empty jobs means “not visible in the queue,” not completion.

Queue absence triggers `sacct -X -n -P -j <job_id> --format=JobIDRaw,State`. The parser matches the exact allocation job ID. Nonzero commands, malformed JSON/text, multiple exact matches, and unknown shapes are contextual errors. Valid empty accounting output or a nonterminal accounting state receives a 60-second visibility grace. It is never guessed as success or failure.

Polling waits 5, 10, 20, then at most 30 seconds between active queries. The 30-second cadence continues while the job is visible; following has no artificial wall-clock limit. `COMPLETED` is the only success. Other terminal Slurm states return as failures. Slurm state strings are external scheduler facts, not a persisted project enum or versioned schema.

After first scheduler visibility, live output uses one separate OpenSSH process running `tail -n +1 -F <derived_log_path>`. Terminal state allows a two-second output drain before local tail termination. Log display is best effort; scheduler state is authoritative. Every exit path terminates and reaps the local SSH/tail process. Ctrl-C reports the job ID/log path and detaches; it never calls `scancel`. There is no cancellation interface in this boundary.

### Typed immutable transfer

Issue 15 controls transfer semantics. The initial bounded workflow requires exactly these public directions:

- push a finalized corpus;
- pull a terminal study;
- pull an immutable artifact;
- pull an immutable evaluation.

Add a symmetric direction only when a real approved caller needs it. Public names are object-specific. There is no generic kind, reference, descriptor, record envelope, transfer result, mapping, replace flag, or adapter.

Each operation:

1. loads and fully validates the canonical source through its direct owner loader;
2. derives the canonical destination and an operation-owned hidden sibling stage from the typed ID and runtime roots;
3. handles an existing canonical destination only through the approved equality/no-op or conflict rule;
4. prepares the hidden stage exclusively;
5. runs basic supported `rsync -a` into that stage;
6. validates the staged bytes, exact inventory/record, embedded ID, and parents at the destination;
7. syncs files/directories, invokes the same no-replace publisher, syncs the parent, and reloads the canonical result;
8. preserves the primary error if stage cleanup also fails.

Active studies fail before transfer. Stages and paths are ephemeral and never persisted. No remote catalog lookup, scan, kind switch, host/path envelope, import mode, delete lifecycle, rollback, or replacement survives.

### Errors and runtime provenance

Operator errors include action, tool, target alias, exit status, and job ID where present. They prefer trimmed stderr, then stdout. They never include the request JSON, batch script, credentials, full command payload, or target-file contents. Scheduler query failure is not “missing”; transfer validation failure is not cleanup success; ambiguous submission is never retried.

Execution introduces no custom provenance envelope or environment vocabulary. Runtime identity comes from the exact `WorkflowRequest`, native `SLURM_JOB_ID`, the verified commit, and the derived log location. Issues 30 and 34 decide which of those facts become durable and where; this issue does not duplicate task, IDs, target, path, or execution reference.

### Lean verification

Implementation tests should stay at the concrete interfaces:

- one target-load/read-only-preflight behavior group;
- one submit-script group covering one request payload, the 1 MiB rejection, parsable job ID, exact revision check, and `afterok` rendering;
- one scheduler-query group covering `squeue` JSON, `sacct` fallback, visibility grace, and malformed/error output;
- one follow group covering success, terminal failure, Ctrl-C detach, and tail cleanup;
- one revision dirty/mismatch group;
- one directory-transfer and one file-transfer behavior, with object validators/publishers tested by their owners.

Delete tests for the handwritten snapshot codec, repeated task argument, Session internals, generic adapters, catalog envelopes, replacement, execution-ref duplication, and architectural transition. Add no compatibility, old/new parallel-contract, registry-deletion, or framework-neutral tests.

## Dependent completeness audit

| Required concern | Contract owner/result | Status |
| --- | --- | --- |
| Smallest control architecture | Split concrete functions with private process helpers; no Session/framework/protocol | Complete |
| Exact request hydration | One approved `WorkflowRequest` adapter, script stdin, no repeated task/snapshot | Complete |
| Request size | Exact 1 MiB local rejection; no remote request-file lifecycle | Complete |
| Target paths/resources | One runtime YAML, OpenSSH alias, absolute paths, direct workflow resource match | Complete |
| Remote revision | Clean exact commit before submit and at job start; no automation | Complete |
| Dependencies | `afterok` job IDs only; required kill-on-invalid support | Complete |
| Machine scheduler state | Deployed `squeue` JSON plus `sacct -P` allocation fallback | Complete |
| Follow/interruption | Capped-backoff state polling, best-effort tail, Ctrl-C detach/no cancel | Complete |
| Transfer | Four initial direction-specific operations, hidden stage, validation, no-replace publish | Complete |
| Error context | Tool/action/target/exit/job, payload redaction, ambiguous outcome preserved | Complete |
| Runtime provenance | Request + native job ID + verified commit; persistence deferred to Issues 30/34 | Complete |
| Experiment enumeration | Remains Issue 18; execution accepts already chosen calls/dependencies | Preserved |
| Training host/environment | Remains Issue 26; no generic hook or environment layer added | Preserved |
| Plan/attempt persistence | Remains Issue 30; no reconciliation or state machine absorbed | Preserved |
| Lifecycle/publication | Remains Issue 15; no catalog/delete/rollback behavior restored | Preserved |
| Identity/address/loading | Remains Issue 11; exact typed IDs and direct loaders only | Preserved |
| Config/request algebra | Remains Issue 10; same request value before work and remotely | Preserved |

The audit found no unresolved Issue 19 decision. It closed two previously implicit dependent edges for recap approval: required target locations are pre-existing rather than created by execution, and only the four real initial transfer directions exist. The whole contract still requires Edo's separate explicit approval before the single Resolution comment and closure.
