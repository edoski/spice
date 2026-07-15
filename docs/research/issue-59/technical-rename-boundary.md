# Issue 59: unified technical-rename boundary audit

Date: 2026-07-15

Status: approved decision evidence. Edo has confirmed **FABLE — Fee Analysis through
Blockchain Learning and Estimation** as the thesis-system/project name, reserved uppercase
**SPICE** for the paper's complete framework, and approved the unified active-boundary rule
and exact `FABLE`/`fable` mapping below. This note authorizes no implementation, repository
renaming, storage mutation, or compatibility work.

## Current active identity surface

Lowercase `spice` is not only a repository label. The current tree uses it as:

- the GitHub repository, Python distribution, `src/spice` import package, and `spice` CLI;
- the remote module protocol (`spice.execution.remote_runner` and
  `spice.storage.sync_cli`), remote checkout/venv/storage paths, and Slurm job/log prefix;
- the `.spice` storage directory, `spice_meta` SQLite table, local serving database path,
  and training-checkpoint location;
- the `SPICE_*` execution, DataLoader, serving, and mobile environment-variable prefix;
- the mobile package, Expo slug/scheme, iOS/Android bundle identifier, secure-storage key,
  display title, and serving API title;
- project-branded source names such as `SpiceOperatorError` and the unused
  `SpiceDemo` contract.

The current blast radius is broad: `src/spice` contains 348 files; 79 test files import or
patch the `spice` namespace; at least 143 non-archival active text files contain a SPICE
identity; six files use `SPICE_*` environment variables; sixteen source/test/doc files use
`.spice` or `spice_meta`; and five mobile files carry SPICE identities. These are audit
counts, not an implementation estimate: much of the current tree is already scheduled for
clean-break deletion or consolidation and should not be renamed prematurely.

## Compatibility and durable-state consequence

A full rename of the current implementation would make old `.spice` SQLite roots and old
remote commands unreadable unless it added migration or compatibility behavior. The
approved clean-break contracts already prohibit that route:

- [Choose root identity, content equality, finality, and canonical addresses](https://github.com/edoski/spice/issues/11#issuecomment-4970483544)
  replaces prefixed IDs, SQLite/catalog lookup, aliases, legacy readers, and migration
  routes with UUID instances at exact typed addresses.
- [Choose publication, study mutability, deletion, transfer, and cutover primitives](https://github.com/edoski/spice/issues/15#issuecomment-4970484710)
  uses owner-local hidden siblings and direct rename without a publication, lock,
  equality, or migration framework.
- [Approve neutral export and raw-backup custody](https://github.com/edoski/spice/issues/14#issuecomment-4948123864)
  keeps old SQLite as untouched evidence rather than a new-code dependency.
- [Choose strict conversion eligibility and recoverable cutover policy](https://github.com/edoski/spice/issues/41#issuecomment-4979776075)
  requires fresh host-local native roots, untouched old runtime roots, and no conversion,
  compatibility, rollback, or cleanup machinery.

Therefore removing the active `.spice` directory/table names requires no legacy support.
Old roots remain archival and no new code reads or translates them. The later native-only
acquisition/execution gates own creation of fresh clean objects; naming makes no claim that
legacy bytes are reused or that reacquisition is unnecessary.

Old model, scaler, evaluation, and private checkpoint state does not constrain the Python
package name. The clean break creates fresh native checkpoints and exact UUID objects; old
runtime roots remain untouched and unread by the new system.

## Coherent unified boundary

The approved human boundary is:

- **FABLE** is the only system/project display form.
- The expansion is exactly **Fee Analysis through Blockchain Learning and Estimation**.
- A document expands FABLE at its first substantive system mention, then uses **FABLE**.
  Title-case **Fable** is not a second display form.
- The mobile display is **FABLE Demo** and the serving display is **FABLE Inference API**.
- **SPICE** remains reserved for the paper's complete spatial, temporal, and reputation
  framework. FABLE is never called SPICE, `SPICE/FABLE`, or “formerly SPICE.” Paper lineage
  is stated in an explicit attribution sentence instead of through shared naming.

The approved technical stem is `fable`. It owns only genuine project identity seams:

- GitHub repository `edoski/fable`, Python distribution/import package `fable`, and the
  installed `fable` CLI, including its hidden remote leaves;
- operator-facing FABLE job/log labels and any surviving project-owned environment prefix
  `FABLE_`; host paths remain runtime configuration but no new active path uses `spice`;
- mobile package `fable-mobile-demo`, Expo slug/scheme `fable-demo`, and iOS/Android bundle
  identifier `dev.edoski.fable.demo`;
- active documentation, thesis prose, report/figure titles, and serving UI that name the
  system.

The name does **not** become a prefix for every internal or durable concept:

- the final UUID corpus/study/artifact/evaluation identities and typed addresses remain
  unprefixed and contain no FABLE branding field;
- `.spice`, `spice_meta`, the old serving SQLite path, wallet secure-storage key, Python
  remote module protocol, and `SpiceDemo` contract are deleted with their obsolete owners;
  they are not translated to `.fable`, `fable_meta`, a FABLE wallet key, a FABLE Python
  launcher, or `FableDemo`;
- internal types use responsibility names such as `OperatorError` where branding adds no
  domain meaning; do not replace `SpiceOperatorError` with `FableOperatorError` by rote;
- filenames and report columns remain descriptive. They gain no mandatory `fable_` prefix.

The final active tree contains no `spice` identity or fallback at project identity seams.
There is no old CLI wrapper, import alias, environment fallback, dual URL scheme, legacy
state reader, or compatibility test. Apply the approved identity only to final survivors
through later specification and implementation tickets; do not mechanically rename code
already scheduled for deletion.

Uppercase **SPICE** and lowercase historical `spice` remain only where they identify the
paper, quote old commands/paths/results, preserve immutable research evidence, or occur in
Git/issue history. Those records are provenance, not active system identity. Git history is
not rewritten.

This boundary does not choose the thesis title/subtitle. The approved complete contract fixes
the attribution classification and canonical attribution paragraph without composing the
thesis narrative around it.
