# Target filesystem, root inventory, and Optuna Journal constraints

Research date: 2026-07-11. This AFK note resolves [Measure target filesystem, root-inventory, and Optuna Journal constraints](https://github.com/edoski/spice/issues/2). It changes no active root, venv, catalog, database, or remote environment.

## Result

If bounded HPO survives, use one local-APFS writer and one Journal in its mutable study root. Archive or discard old RDB studies explicitly. Do not use a shared university-NFS Journal until a disposable target-mount lock/interruption probe succeeds; the configured remote venv cannot run it. Do not use `/scratch.hpc` as sole thesis custody: the university's January 2025 instructions say unaccessed files are deleted after 40 days ([PDF](https://disi.unibo.it/it/dipartimento/servizi-tecnici-e-amministrativi/servizi-informatici/utilizzo-cluster-hpc/unibo.tiles.multi.links_attachments/e7809f6f52644346a912b99dd2280788/%40%40objects-download/b0b12b9784e142a8b87503d2e5fa5818/file/IstruzioniUsoClusterGPUGennaio2025.pdf)).

This bounded route needs no multi-host writers, catalog reconciliation, automatic stale-lock recovery, compatibility reader, migration, or generic storage module.

## Filesystem and publishing evidence

The local checkout, `outputs`, and `.venv` are on `/dev/disk3s5`, local journaled APFS. `df -h outputs` observed 1.8 TiB total, 440 GiB used, and 1.4 TiB available; `diskutil info /System/Volumes/Data` identifies APFS. APFS documents copy-on-write metadata and atomic safe-save rename transactions for bundles/directories ([Apple APFS features](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/Features/Features.html)).

An isolated `mktemp -d .spice-fs-probe.XXXXXX` directory verified same-device directory rename, payload visibility, and directory `fsync`, then was removed. This only proves that local path. It does not prove crash durability, no-replace behavior, or NFS behavior. Python defines `fsync` as flushing a file descriptor ([Python docs](https://docs.python.org/3/library/os.html#os.fsync)), not an NFS commit guarantee.

Use same-device staging. If a destination exists, validate equality or fail as conflict; do not pre-check then replace. A future owner module should hide staging, validation, visibility, and durability behind `publish(stage, destination)`. Do not generalize the seam until the remote target is a second verified adapter.

## Inventory

Physical root means canonical corpus/artifact/study directory with `.spice/state.sqlite`; hidden stages and backups are excluded. It is not a semantic-validity check.

| Kind | Catalog | Physical | Equal | Catalog-only |
|---|---:|---:|---:|---:|
| Corpus | 5 | 5 | yes | 0 |
| Study | 0 | 0 | yes | 0 |
| Artifact | 38 | 8 | no | 30 |

The active physical path-list digest is `e92e505dfb543abc51bf3d55215c0744f963d53900563a50f1a32c037b42abee` (13 rows). Catalog SHA-256 is `8b52141a32d3e0de952757046a95291cfe3b15e3ad038bcdfd6db9385cd5ae34`; corpus and study ID sets match, artifact does not. Thus the catalog is not a physical inventory. Existing architecture makes root-local state/manifest authoritative and catalog derived ([storage architecture](../../src/spice/storage/ARCHITECTURE.md)). Do not refresh it as research: refresh writes it.

The 2026-07-10 university snapshot found all configured roots on writable NFS4; checkout was on another device while venv, storage, and logs shared one NFS device. It recorded catalog/physical corpus 4/5, study 21/22, artifact 221/179, with only 22 artifact intersections. This is topology evidence, not lock, SQLite, rename, or durability proof. The remote venv lacked usable `typing_extensions`/Torch and usable Optuna metadata; repair is outside this ticket. Full non-secret counts, set digests, commands, and limitations are in the [baseline](spice-pre-break-evidence-baseline.md#6-non-secret-storage-root-inventory).

## Optuna 4.8 Journal

Pinned Optuna is 4.8.0. `JournalFileBackend` says it does not support high write concurrency ([official docs](https://optuna.readthedocs.io/en/v4.8.0/reference/generated/optuna.storages.journal.JournalFileBackend.html)). Its implementation locks each append, flushes and `fsync`s, but does not provide an application-wide optimize/recovery lock ([v4.8 source](https://github.com/optuna/optuna/blob/v4.8.0/optuna/storages/journal/_file.py)).

`JournalFileSymlinkLock` is default and documented for NFSv2+; `JournalFileOpenLock` uses `O_CREAT|O_EXCL` and is documented for NFSv3+ on Linux 2.6+. Both default to a 30-second stale-lock grace. A paused writer or delayed NFS metadata can therefore cause unsafe forced removal. Require one study writer, low write frequency, no concurrent resume/transfer/delete, and manual quiescence. Journal is not a generic distributed-HPO backend.

Current SPICE uses `RDBStorage` in [study_optuna.py](../../src/spice/storage/study_optuna.py). Journal is a clean break, not a backend swap: historic studies must be archived/read-only or discarded, not made compatible.

## Commands and limits

```sh
sw_vers; uname -a; mount; df -h . outputs .venv
diskutil info /System/Volumes/Data
find outputs -type f -path '*/.spice/state.sqlite' | LC_ALL=C sort | shasum -a 256
# local .venv Python: SQLite URI mode=ro&immutable=1; count *_index tables
shasum -a 256 outputs/.spice/catalog.sqlite
probe=$(mktemp -d .spice-fs-probe.XXXXXX)
# tiny write -> file fsync -> directory rename -> parent fsync -> read
rm -rf "$probe"
```

The local inventory can race writers; no raw database was copied. Before any remote Journal decision, use only a disposable target-mount directory: concurrent append, abrupt writer kill, reopen/replay, exclusion check, mount/kernel/Optuna capture, then removal. If that probe cannot run, NFS Journal remains conditional.
