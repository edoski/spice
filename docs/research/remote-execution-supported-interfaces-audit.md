# Remote execution supported-interface audit

Issue: [Audit remote execution against supported OpenSSH, rsync, and Slurm interfaces](https://github.com/edoski/spice/issues/6). Capture date: 2026-07-11. This is evidence for the later owner decision, not that decision.

## Scope and method

No job was submitted, cancelled, modified, copied, or followed. Local and remote facts below come from read-only version/help/configuration/status commands. The remote facts apply only to the configured university login target and its current login-node command environment, not every Slurm node or future deployment. The remote host name, account, paths, and revision are intentionally omitted from this report; their typed target configuration is the source of record.

Evidence labels are strict: **documented** is an owning manual; **local measured** and **remote measured** are commands run in this session; **inference** is a conclusion from those facts.

## Measured surface

| Interface | Local measured | Remote measured | Consequence |
|---|---|---|---|
| OpenSSH | `OpenSSH_10.2p1` | `OpenSSH_9.2p1` | Standard `ssh` subprocess is available at both ends. |
| rsync | macOS `openrsync` 2.6.9, protocol 29 | rsync 3.2.7, protocol 32 | Do not assume local `openrsync` supports every newer rsync option. The current `-a` transfer is within the common basic surface. |
| Slurm client | absent locally | Slurm 22.05.8 | Scheduler control must remain remote. |
| `sbatch --parsable` | n/a | listed by remote `sbatch --help` | Supported for submission; no submitting behavioural test was allowed. |
| `squeue --json` | n/a | successful, exit 0 | Supported on this deployment. |
| `sacct --json` | n/a | exit 1 | Not supported by this 22.05 client invocation; retain a narrow text `sacct` fallback if accounting is required. |
| `squeue --only-job-state` | n/a | exit 1 | Not supported; do not design around it. |
| `slurmrestd` | n/a | command absent; `systemctl is-active slurmrestd` reported inactive | No deployed REST service is evidenced. Rule out REST for this thesis workflow. |
| process argument bound | `ARG_MAX=1,048,576` | `ARG_MAX=2,097,152` | This is an OS aggregate bound, not a safe snapshot limit. Current submission puts the entire resolved JSON in a remote command argument, so its byte size must be validated before submission or reduced by an approved later design. |
| target config | 650 bytes for the current L40 target YAML | same repository revision read remotely | Static target configuration is small; workflow snapshots, not target YAML, are the size risk. |

Remote `squeue --json` and the failed option probes were read-only queries. They demonstrate acceptance by the deployed command, not correctness of every JSON schema field or accounting retention. `sacct --json` and `--only-job-state` must not be inferred from newer Slurm manuals: the installed 22.05.8 CLI is the controlling evidence.

## Supported public interfaces

**Documented — OpenSSH.** `ssh_config` is read by the client; system-wide settings are read before per-user settings, and the first obtained value normally wins ([OpenSSH `ssh_config(5)`](https://man.openbsd.org/ssh_config)). The existing direct `user@host` invocation still receives matching global/wildcard client configuration, but it cannot use a user-defined `Host` alias as its target identity. The current typed target stores host and user separately. **Inference:** retain an `ssh` subprocess so user host-key, proxy, and authentication policy stay in the supported OpenSSH path; do not add an in-process SSH library without a concrete missing capability.

**Documented — rsync.** Rsync's `-a` is archive mode and preserves the normal recursive metadata set; `--files-from` selects an explicit source list ([rsync manual](https://download.samba.org/pub/rsync/rsync.1)). Its remote-shell transport and delta algorithm fit immutable-root staging better than a new SFTP implementation. **Inference:** retain rsync for staged root transfer and consider one exact `--files-from` collection pull later. Do not add a transfer backend.

**Documented — submission.** `sbatch` accepts a script on standard input, returns after transferring it to the controller and assigning a job ID, and does not transfer user files besides the script ([`sbatch(1)`](https://slurm.schedmd.com/sbatch.html)). Its documented `--parsable` option returns only the job ID and optional cluster name. The remote help confirms it. **Inference:** replace the current English regex with an explicit parser for the documented parsable value (job id before an optional `;cluster` suffix). This deletes a brittle human-text contract without changing the workflow.

**Documented — state and accounting.** `squeue` offers `--json` and `--format`; the manual warns that programmatic calls should not run in a loop because they can degrade controller performance ([`squeue(1)`](https://slurm.schedmd.com/squeue.html)). `sacct` reports accounting records, whose availability and fields are deployment-dependent ([`sacct(1)`](https://slurm.schedmd.com/sacct.html)). **Inference:** use remote-supported `squeue --json -j <id>` for active-state lookup, with bounded/backoff polling; use the existing narrow `sacct -n -X --format=State` final lookup because its JSON form failed here. A successful submission followed by a local crash remains a reconciliation problem; no query format alone proves which attempt was submitted.

**Documented — REST.** Slurm's REST API requires `slurmrestd`, authentication, versioned OpenAPI endpoints, and administrator configuration ([Slurm REST API details](https://slurm.schedmd.com/rest.html)). **Remote measured:** no runnable service is evidenced. **Inference:** REST is speculative infrastructure, not a candidate for the bounded thesis workflow.

## Current Session deletion test

The current `ExecutionSession` centralizes SSH quoting/process failures, remote module invocation, rsync, rendered Slurm scripts, provenance, follow/state reads, and remote revision lookup ([session.py](../../src/spice/execution/session.py)). It is called by workflow submission, benchmark submission/revision recording, and root transfer ([submission.py](../../src/spice/execution/submission.py), [benchmark submission](../../src/spice/benchmarks/submission.py), [transfer transaction](../../src/spice/execution/transfer_transaction.py)).

Deleting it now would spread target paths, shell quoting, subprocess error mapping, scheduler lifecycle, transfer staging, and revision/provenance into those callers. It therefore **fails** the deletion test. Replacing it with Submitit, Fabric, Paramiko, or a REST client would not delete those responsibilities and would add a dependency or unavailable service.

It does not justify all present code. These parts have direct deletion candidates:

- Delete `_SBATCH_JOB_ID_PATTERN` and its English-output test after switching to `sbatch --parsable`.
- Replace the active `squeue -o %T` text parse with the deployed `squeue --json` subset. Keep text `sacct` only as the measured accounting fallback.
- Remove the duplicate final-state lookup: `read_job_state()` already calls `sacct` after an absent queue record and `follow_job()` calls it again on `None`.
- Make follow cancellation deterministic. The current tail starts before a state query and waits forever for a never-created log; the job can finish before log creation, and scheduler/accounting visibility can lag. Poll scheduler state first, start/retry tail only while active, make tail optional, and after a final state allow one bounded log-settle read. This is an **inference** from current code and the documented asynchronous submission/log behavior, not a tested cluster race.
- Bound polling. The current five-second loop is 12 controller queries/minute per followed job, plus tail SSH traffic, with no backoff. For one thesis run at a time, a modest capped backoff is simpler and respects Slurm's warning; no persistent SSH connection is justified.

The Session's remote catalog-record exchange and catalog-derived destination behavior are real current ownership in `transfer_transaction.py`; they must not be claimed already deleted. Their survival depends on the separate direct-discovery/storage decision. The current full JSON command argument also has an unmeasured safe threshold; record its encoded byte count and reject over-limit submission rather than silently inventing a compatibility transport.

## Recommendation for the later decision

Amend ADR 0005; do not retain it verbatim and do not supersede the core facade. Keep one small target-bound OpenSSH/rsync/Slurm facade for exactly: remote command/module execution, rsync stage transfer, parsable submission, state/final lookup, bounded follow, and remote revision. Keep script rendering and provenance inside that facade. Do not split transport and scheduler into public interfaces yet: this project has one host and one workflow, and a split would add concepts without a second implementation.

Delete human Slurm parsing and redundant final lookup. Do not adopt Submitit, an SSH library, REST, generic backends, connection pooling, retries beyond the concrete scheduler race, or compatibility layers. Revisit catalog transfer only when its owning storage decision is made.

## Reproduction

```sh
ssh -V
rsync --version
getconf ARG_MAX
# remote, read-only:
ssh -o BatchMode=yes <configured-target> 'scontrol --version; sbatch --help'
ssh -o BatchMode=yes <configured-target> 'squeue --json -u "$USER" >/dev/null'
ssh -o BatchMode=yes <configured-target> 'sacct --json -n -X -S 2026-07-10 -u "$USER" >/dev/null'
```

The last two commands intentionally inspect only command support. They do not submit a job or establish scheduler/log race behavior.
