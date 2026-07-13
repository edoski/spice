# Issue 15 filesystem publication primitives

> **Historical evidence, not the binding contract.** This note records measured
> primitives and alternatives considered before Edo's final decisions. Its earlier
> active-study, archive, deletion, locking, and lifecycle recommendations were
> superseded by the approved [Issue 15 Resolution](https://github.com/edoski/spice/issues/15#issuecomment-4958096197).
> Use that Resolution as authority.

Research date: 2026-07-13. Scope: primary filesystem, Python, rsync, and Optuna evidence for [Issue 15](https://github.com/edoski/spice/issues/15). This note changes no production code or stored data. Existing target measurements come from [Issue 2's accepted evidence](../target-filesystem-root-journal-constraints.md); this note does not repeat its probes.

## Result

Use direct owner functions, not a lifecycle service or SQLite coordinator. Publish immutable files with a same-filesystem hard link. Publish immutable directories with a capability-checked exclusive rename on local APFS. Linux NFS has no native no-replace directory rename; support there needs one cooperative namespace writer lock or enforced quiescence. In every case, an existing same ID is validated as equal/no-op or conflict.

Keep four guarantees separate:

| Guarantee | Smallest primitive | What it does not prove |
|---|---|---|
| Atomic visibility | hard link for a file; exclusive rename for a directory; exchange for a supported cutover | crash or power-loss durability |
| Durability | flush and sync payloads, sync directories, publish, then sync the changed parent | recovery after an ambiguous error |
| Recovery | inspect and validate canonical and hidden paths before retry or cleanup | that concurrent writers were excluded |
| Consistency | one writer boundary plus direct manifest/hash validation | a durable catalog, index, or lifecycle state |

The direct contract is therefore `publish_file(stage, destination)`, `publish_directory(stage, destination)`, and one whole-operation study/namespace lock used by publication, terminalization, transfer, archive, and deletion. These stay private to corpus, study, artifact, and evaluation owners. No generic reference, registry, database, or lock service is earned.

## Publication and durability

Python's `os.rename` and `os.replace` are atomic on success and may fail across filesystems, but both replace compatible destinations on Unix. They are not no-replace operations ([Python 3.11 `os.rename` and `os.replace`](https://docs.python.org/3.11/library/os.html#os.rename)). Python exposes no `renamex_np` or `renameat2` wrapper. A check followed by either Python rename still races.

For an immutable regular file, write a hidden sibling, flush its Python buffer, `os.fsync` it, then call `os.link(stage, destination)`. A hard link never overwrites, returns `EEXIST`, requires the same mounted filesystem, and cannot target a directory ([POSIX `link`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/link.html), [Linux `link(2)`](https://man7.org/linux/man-pages/man2/link.2.html)). After a successful link, unlink the stage and sync the parent directory. Conservatively inspect and content-validate the destination after an NFS error before retrying.

For an immutable directory on macOS, `renamex_np(..., RENAME_EXCL)` returns `EEXIST` when the destination exists. `RENAME_SWAP` atomically exchanges two existing names. Both depend on filesystem capabilities and must be checked on the mounted volume ([Apple `rename(2)`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/man/man2/rename.2#L55-L145), [Apple volume capabilities](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/man/man2/getattrlist.2#L1362-L1371)). APFS also documents crash-protected metadata and an atomic safe-save rename transaction for bundles/directories, but this does not remove the need to flush newly written payloads first ([Apple File System Guide](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/Features/Features.html)).

For an immutable directory on Linux, `renameat2(..., RENAME_NOREPLACE)` rejects an existing destination and `RENAME_EXCHANGE` atomically swaps two existing names, but filesystem support is required ([Linux `rename(2)`](https://man7.org/linux/man-pages/man2/rename.2.html)). The current Linux NFS client rejects every nonzero rename flag, so neither operation is available through NFS ([Linux NFS `nfs_rename`](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/fs/nfs/dir.c?id=a13c140cc289c0b7b3770bce5b3ad42ab35074aa#n2757)). Plain NFS rename is atomic but overwrite-capable. On NFS, serialize the destination check and plain rename under one cooperative lock, or require writer quiescence. Do not claim native no-replace.

The durable local sequence is:

1. Create the hidden stage on the same mount, preferably under the final parent.
2. Flush and sync every written regular file. Sync nested directories bottom-up after their entries are complete.
3. Perform the no-replace visibility operation.
4. Sync the parent directory after its entries change. If source and destination parents differ, sync both.

Linux explicitly says file `fsync` does not necessarily persist the containing directory entry; the directory needs its own `fsync` ([Linux `fsync(2)`](https://man7.org/linux/man-pages/man2/fsync.2.html)). Python requires `file.flush()` before `os.fsync(file.fileno())` when buffered I/O is used ([Python `os.fsync`](https://docs.python.org/3.11/library/os.html#os.fsync)). Propagate every sync error.

On macOS, ordinary `fsync` moves host buffers to the drive but does not force the drive's volatile cache to permanent media. `F_FULLFSYNC` requests that stronger device flush; `F_BARRIERFSYNC` orders writes but is not a durability guarantee ([Apple `fsync(2)`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/man/man2/fsync.2#L48-L105), [Apple `fcntl(2)`](https://github.com/apple-oss-distributions/xnu/blob/f6217f891ac0bb64f3d375211650a4c1ff8ca1ea/bsd/man/man2/fcntl.2#L207-L245)). Apple does not publish a general APFS directory-`fsync` promise. The local directory-sync observation from Issue 2 proves only that the call succeeded on that path, not power-loss behavior.

NFSv4 namespace-modifying operations are synchronous at the server: successful completion means request-associated data is in stable storage, except explicitly unstable file writes ([RFC 7530 section 14.3](https://www.rfc-editor.org/rfc/rfc7530.html#section-14.3)). Its rename is atomic to the client and same-server-filesystem only, but it replaces a compatible existing target ([RFC 7530 section 16.27](https://www.rfc-editor.org/rfc/rfc7530.html#section-16.27)). Linux NFS directory `fsync` is intentionally a no-op because namespace operations are synchronous; file `fsync` waits for writes and commits the inode ([Linux NFS directory sync](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/fs/nfs/dir.c?id=a13c140cc289c0b7b3770bce5b3ad42ab35074aa#n1366), [Linux NFS file sync](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/fs/nfs/file.c?id=a13c140cc289c0b7b3770bce5b3ad42ab35074aa#n241)). A successful directory `fsync` on NFS therefore adds no extra promise.

NFS failures remain ambiguous. A server can complete a rename, crash before replying, and reject the retry. After any failed publication, inspect both names and validate the canonical destination before retrying, removing, or reporting failure ([Linux rename NFS caveat](https://man7.org/linux/man-pages/man2/rename.2.html#BUGS)).

Hidden stages need no persisted lifecycle record. Recovery uses filesystem evidence:

- valid canonical destination plus equal stage: canonical wins; remove the stage;
- valid canonical destination plus different stage: conflict; preserve both for inspection;
- absent canonical destination plus valid stage: retry publication;
- invalid or partial stage: resume only a declared rsync transfer, otherwise discard;
- ambiguous syscall result: validate both paths before any mutation.

Direct loaders must ignore hidden paths. Cleanup must run under the same writer boundary as publication and deletion.

## Transfer

The measured common surface is local `openrsync` compatible with 2.6.9/protocol 29 and remote rsync 3.2.7. Both support `-a`, `--files-from`, `--partial-dir`, and `--delay-updates`; local openrsync does not expose rsync 3.2.7's `--fsync` ([measured interface audit](../remote-execution-supported-interfaces-audit.md#measured-surface), [OpenBSD `openrsync(1)`](https://man.openbsd.org/openrsync.1), [rsync 3.2.7 option surface](https://github.com/RsyncProject/rsync/blob/v3.2.7/rsync.1.md#L419-L552)).

Transfer into a hidden destination stage with `-a --partial-dir=.rsync-partial`, never the canonical path. `--partial-dir` preserves interrupted file data for a later resume. `--delay-updates` only renames files rapidly at the end and describes itself as “a little more atomic”; it is not a tree transaction ([rsync 3.2.7 partial and delayed updates](https://github.com/RsyncProject/rsync/blob/v3.2.7/rsync.1.md#L3320-L3427)). A hidden whole-tree stage makes it unnecessary. Avoid `--inplace`: it exposes partial files and conflicts with both options ([rsync 3.2.7 `--inplace`](https://github.com/RsyncProject/rsync/blob/v3.2.7/rsync.1.md#L1053-L1093)).

After rsync exits successfully, validate the canonical identity, manifest, and content hashes. Then run the destination's durable-tree function and publish through the same no-replace primitive as a local build. Rsync is transport, not publication, equality, durability, or authority.

An active study must be locked for the whole copy. Transfer becomes a stable snapshot plus explicit writer handoff; source and destination must never resume concurrently. A terminal study transfers like any other immutable package. Exact-file pulls may use `--files-from`, remembering that `-a` does not imply recursion with that option ([rsync 3.2.7 `--files-from`](https://github.com/RsyncProject/rsync/blob/v3.2.7/rsync.1.md#L2367-L2405)).

## Optuna 4.8 Journal

`JournalFileBackend` locks each append, writes newline-delimited JSON, flushes, and calls `os.fsync`. It explicitly does not support high write concurrency ([Optuna 4.8 API](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.storages.journal.JournalFileBackend.html), [Optuna 4.8 source](https://github.com/optuna/optuna/blob/v4.8.0/optuna/storages/journal/_file.py#L59-L111)). That append lock is not a study-operation lock. Transfer, resume, terminal snapshot, archive, or delete can still race between appends.

The default symlink lock and the NFSv3+ open lock both default to a 30-second grace period and forcibly remove an unchanged lock after it expires. A stalled writer can therefore lose exclusion ([Optuna lock source](https://github.com/optuna/optuna/blob/v4.8.0/optuna/storages/journal/_file.py#L124-L194), [Optuna `JournalFileOpenLock`](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.storages.journal.JournalFileOpenLock.html)). For the bounded route, use one study writer, no automatic stale-lock expiry, and explicit recovery only after proving the prior writer dead.

Optuna warns that a signal other than single-job SIGINT may leave the interrupted trial state unmodified. Its public `Study.tell(..., state=FAIL)` can finish a known interrupted trial ([Optuna 4.8 `Study.optimize` and `tell`](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.study.Study.html)). Recovery should open and replay under the whole-study lock, reject malformed journal data, explicitly resolve any `RUNNING` trial, then either resume or write the terminal snapshot. Never infer completion from process absence.

`JournalStorage` describes its snapshot as in-memory; `JournalFileBackend` implements log replay, not a persisted terminal snapshot ([Optuna journal storage source](https://github.com/optuna/optuna/blob/v4.8.0/optuna/storages/journal/_storage.py#L54-L112)). The project still needs one immutable terminal summary written with the regular-file publication sequence. Once that summary exists, owner functions reject further append.

No project SQLite survives this evidence. If the separate HPO choice keeps Optuna, its one Journal file is the mutable study state. If HPO uses direct bounded search, Journal also disappears. The whole-study lock remains a direct owner primitive, not a service.

## Cutover and remaining measurements

A capability-proven APFS `RENAME_SWAP` or Linux `RENAME_EXCHANGE` gives one atomic visibility switch. It does not make unsynced trees durable, coordinate two hosts, authorize rollback after new writes, or remove old readers. Sync the staged tree first, hold reader/writer quiescence through validation, exchange, sync the parent, smoke-test, and exchange back only before writers resume. Final reader removal remains a separate irreversible gate.

Linux NFS cannot use exchange. Its smallest cutover is two durable renames under full quiescence, with recovery determined from the validated canonical, staged, and old paths. This is recoverable, not atomically visible. Re-read paths after every NFS error.

Issue 2 established local journaled APFS and remote writable NFS4, but not the remaining behavioral facts. Before implementation, its target-mount probe must decide:

- APFS `RENAME_EXCL` and `RENAME_SWAP` capability and concurrent behavior on the actual root;
- APFS directory-sync and required `F_FULLFSYNC` behavior for the chosen durability promise;
- remote kernel/client rejection or support of rename flags on the actual NFS mount;
- NFS cooperative-lock exclusion, abrupt-writer death, cache visibility, and manual stale-lock recovery;
- Optuna append interruption, replay, unfinished-trial recovery, and terminal snapshot under that exact mount;
- same-device placement for every hidden stage and canonical parent.

Until those observations exist, approve local APFS publication only. Keep NFS directory publication, active-study writing, and exchange cutover conditional. NFS transport into a hidden stage remains safe to investigate because it does not make the stage canonical.
