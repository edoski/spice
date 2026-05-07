# ADR 0005: Custom Execution Session Retained

## Status

Accepted.

## Context

SPICE remote execution is not only Slurm submission. The current Execution Session owns target-bound SSH command execution, exact `sbatch` script rendering, remote storage-root rewrite, provenance environment variables, log following through `tail`/`squeue`/`sacct`, remote module execution, rsync transfer, and remote catalog record exchange.

Packages such as Submitit, Fabric, and Paramiko cover narrower pieces of that surface. Submitit can submit Slurm jobs, but it does not replace SSH target selection, rsync storage transfer, remote runner invocation, provenance wiring, or catalog transfer behavior. Fabric and Paramiko cover SSH execution, but they do not remove the Slurm and transfer lifecycle; OpenSSH subprocesses also preserve existing user SSH config.

## Decision

Keep the custom SSH/rsync/Slurm Execution Session. Do not replace it with Submitit, Fabric, Paramiko, or another remote-execution framework during cleanup.

Reconsider Submitit only if the control architecture changes so job submission code runs on the cluster host or SPICE adopts a Python-function job model. Reconsider SSH packages only if the project needs programmatic SSH features that OpenSSH subprocesses cannot provide.

## Consequences

Execution cleanup should stay inside the current Session, submission, and transfer modules. Package substitution is not the main lever for this area.

The remote runner contract remains typed workflow config in, workflow function out. Storage transfer continues to use rsync plus catalog materialization and strict remote catalog record envelopes.
