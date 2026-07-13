# Slurm 22.05 ambiguous-submission recovery

Date: 2026-07-13. Scope: official Slurm 22.05.8 manuals and the matching SchedMD source only. No Slurm command was run and no job was submitted.

## Finding

A caller can pre-persist one random UUID, submit that exact value as both the job name and comment, and recover an accepted job's numeric ID from `squeue` before the job starts. Use `JobName` as the cross-controller/accounting correlation field. `Comment` is useful only as an extra controller-side equality check: accounting stores it only when `AccountingStoreFlags=job_comment`, sends it in the job-complete message, and permits later modification. `sbatch` documents `--job-name`, `--comment`, and `--parsable`; it returns after the controller has received the script and assigned an ID, while the job may remain pending ([22.05 `sbatch`](https://slurm.schedmd.com/archive/slurm-22.05.8/sbatch.html#SECTION_DESCRIPTION), [`--job-name`](https://slurm.schedmd.com/archive/slurm-22.05.8/sbatch.html#OPT_job-name), [`--comment`](https://slurm.schedmd.com/archive/slurm-22.05.8/sbatch.html#OPT_comment), [`--parsable`](https://slurm.schedmd.com/archive/slurm-22.05.8/sbatch.html#OPT_parsable)).

The marker must be durable before invoking `sbatch`. Use a shell-safe UUID containing no whitespace, comma, or `|`:

```text
sbatch --parsable --job-name=<marker> --comment=<marker> ...
```

After a lost acknowledgement, query the controller's local cluster in text mode:

```text
squeue --local --all --states=all --user=<uid> --name=<marker> \
  --noheader --format='%A|%U|%j|%k|%V'
```

The fields are job ID, numeric user ID, job name, comment, and submit time. `--states=all` matters: without it, `squeue` shows only pending, running, and completing jobs. Parse every row and retain only rows whose UID, name, and comment equal the expected values and whose job ID is strictly numeric. The filters reduce output but do not replace these equality checks. Zero exact distinct IDs is unresolved; one is recovered; more than one is a conflict. Never choose by last line or latest submit time ([22.05 `squeue` filters](https://slurm.schedmd.com/archive/slurm-22.05.8/squeue.html#OPT_name), [`--states`](https://slurm.schedmd.com/archive/slurm-22.05.8/squeue.html#OPT_states), [format fields](https://slurm.schedmd.com/archive/slurm-22.05.8/squeue.html#OPT_format)).

Do not combine those filters with `squeue --json` on 22.05. Its manual says JSON ignores all formatting and filtering arguments. The 22.05.8 source confirms that JSON loads all controller jobs with `SHOW_ALL | SHOW_DETAIL` and emits `job_id`, `user_id`, `name`, `comment`, and `submit_time`; JSON recovery must therefore parse all returned jobs itself. The deployed audit proved only that JSON exits successfully, not that any requested filter applies ([22.05 JSON limitation](https://slurm.schedmd.com/archive/slurm-22.05.8/squeue.html#OPT_json), [22.05.8 source](https://github.com/SchedMD/slurm/blob/slurm-22-05-8-1/src/plugins/openapi/v0.0.38/jobs.c#L678-L1071)). The filtered text query is the narrower recovery operation.

If the job completes and leaves controller memory, query accounting and union results by numeric ID:

```text
sacct --allocations --noheader --parsable2 --user=<uid> --name=<marker> \
  --starttime=<persisted-conservative-lower-bound> --endtime=now \
  --format=JobIDRaw,UID,JobName,Submit
```

`--allocations` excludes step rows. `JobIDRaw`, `UID`, `JobName`, and `Submit` are native 22.05 fields. `--name` filters job names; the 22.05.8 MySQL plugin implements this as equality, but output must still be checked exactly because database collation is deployment-owned. An explicit lower bound is required for cross-day recovery: without `--jobs` or `--state`, `sacct` defaults to midnight today. `sacct` can report pending jobs, but non-eligible held/dependency jobs have an `EligibleTime` limitation; `squeue` remains the immediate pre-start source ([22.05 `sacct`](https://slurm.schedmd.com/archive/slurm-22.05.8/sacct.html#OPT_name), [time-window defaults](https://slurm.schedmd.com/archive/slurm-22.05.8/sacct.html#SECTION_DEFAULT-TIME-WINDOW), [exact-name source](https://github.com/SchedMD/slurm/blob/slurm-22-05-8-1/src/plugins/accounting_storage/mysql/as_mysql_jobacct_process.c#L1536-L1551)).

Controller retention is bounded by `MinJobAge`: completed jobs remain in `slurmctld` memory for at least that many seconds, default 300, then may disappear. Accounting requires a non-`none` `AccountingStorageType`. `PurgeJobAfter` may remove individual job records; its default is never, but the deployment may override it. `ArchiveJobs` is optional and archived files require separate administrative loading, so an archive is not a normal `sacct` recovery source ([22.05 `MinJobAge`](https://slurm.schedmd.com/archive/slurm-22.05.8/slurm.conf.html#OPT_MinJobAge), [`AccountingStorageType`](https://slurm.schedmd.com/archive/slurm-22.05.8/slurm.conf.html#OPT_AccountingStorageType), [`PurgeJobAfter`](https://slurm.schedmd.com/archive/slurm-22.05.8/slurmdbd.conf.html#OPT_PurgeJobAfter), [`ArchiveJobs`](https://slurm.schedmd.com/archive/slurm-22.05.8/slurmdbd.conf.html#OPT_ArchiveJobs)).

## Required deployment gate

Before this can authorize automatic recovery, the target must prove the exact `sbatch` options; the text `squeue` options and fields above; numeric/name/comment round-trip on one controlled job; working text `sacct` with the four fields; accounting visibility for pending and completed own jobs; `MinJobAge`; and accounting purge/retention longer than the supported interruption window. `AccountingStoreFlags=job_comment` is optional because `JobName` is the accounting marker.

Both `JobName` and `Comment` are mutable through `scontrol`; the marker is correlation evidence, not immutable scheduler identity or provenance ([22.05 `scontrol JobName`](https://slurm.schedmd.com/archive/slurm-22.05.8/scontrol.html#OPT_JobName), [`Comment`](https://slurm.schedmd.com/archive/slurm-22.05.8/scontrol.html#OPT_Comment)). An exact one-ID match can recover the acknowledgement. Multiple IDs are a hard conflict. Zero IDs is not proof of rejection because controller purging, accounting lag/unavailability, an incomplete time window, retention, or metadata mutation can all erase visibility. Slurm 22.05 exposes no uniqueness constraint or idempotency key for this marker. Automated resubmission after an ambiguous loss must remain disabled unless the deployed capability gate establishes a complete visibility window; otherwise require operator resolution.
