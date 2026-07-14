# Current CLI read-only inventory

Observed from the working tree on 2026-07-14. No command with effects was invoked. Typer
introspection found 10 groups, 24 leaf commands, and 120 leaf parameters: 15 required and 105
optional. The wheel has one entry point, `spice = "spice.cli.app:main"`.

## Registered Typer tree

Every node has Typer's generated `--help`. The root also registers `--install-completion` and
`--show-completion`; no-argument groups display help.

| Command | Arguments and options |
| --- | --- |
| `spice acquire` | `--surface --chain --corpus --problem --features --provider --storage-root --dry-run/--no-dry-run` |
| `spice train` | `--surface --chain --problem --features --model --tuning-space --training --split --tuning --study --variant --corpus-id --study-id --dependency --target --detach` |
| `spice tune` | `--surface --chain --problem --features --model --tuning-space --training --split --tuning --study --corpus-id --trial-count --dependency --target --detach` |
| `spice evaluate` | `--artifact-id --corpus-id --evaluator --evaluation-start --evaluation-duration-seconds --delay-seconds --batch-size --dependency --target --detach` |
| `spice benchmark plan` | `NAME --target --runs-root` |
| `spice benchmark submit` | `RUN_DIR` |
| `spice benchmark collect` | `RUN_DIR` |
| `spice benchmark show` | `RUN_DIR` |
| `spice benchmark index rebuild` | `--runs-root --index` |
| `spice benchmark index show` | `--index` |
| `spice benchmark index list` | `--benchmark --chain --model --evaluator --limit --index` |
| `spice benchmark index export` | `--output --benchmark --chain --model --evaluator --index` |
| `spice config list` | `GROUP` |
| `spice config show` | `GROUP NAME` |
| `spice config edit` | `GROUP NAME` |
| `spice show corpus` | `--corpus-id --chain --corpus --storage-root --detail` |
| `spice show study` | `--study-id --chain --corpus --features --prediction --model --problem --study --storage-root --detail` |
| `spice show artifact` | `--artifact-id --corpus-id --study-id --chain --corpus --features --prediction --model --problem --variant --study --storage-root --detail` |
| `spice delete artifact` | `--artifact-id --storage-root` |
| `spice delete study` | `--study-id --storage-root --cascade` |
| `spice delete corpus` | `--corpus-id --storage-root --cascade` |
| `spice transfer push corpus` | `--corpus-id --storage-root --target --replace` |
| `spice transfer pull artifact` | `--artifact-id --storage-root --target --replace` |
| `spice refresh catalog` | `--storage-root` |

`python -m spice.storage.sync_cli` is a second active argparse surface outside the wheel entry
point. It adds four machine commands:

- `prepare-stage --destination-root --staged-root [--replace]`
- `finalize-stage --storage-root --destination-root --staged-root --root-kind [--replace]`
- `cleanup-stage --staged-root`
- `resolve-record --storage-root --root-kind --root-id`

## Registration, output, errors, and help

`spice.cli.app` constructs an `OperatorTyper`, mounts six groups, then registers four workflow
functions. `OperatorTyper.command()` is a command factory that wraps every registered command and
converts `SpiceOperatorError` into `click.ClickException`.

Output is mixed by subsystem: workflow `Reporter` headers, benchmark JSON lines, config names or
YAML, editor process output, storage section tables and diagnostics, transfer key/value lines plus
stderr warnings, catalog-refresh text, and remote catalog envelopes from `sync_cli`. Expected
operator errors use Click's stderr rendering and exit 1. Parser/usage failures use Typer/Click and
exit 2. Help includes root and group prose, per-command examples, Rich panels, completion options,
and every generated node-level `--help` path.

## CLI tests

All 18 active command-facing tests are listed here; 16 exercise the Typer tree and two exercise the
argparse helper.

- `tests/cli/test_benchmark_cli.py`
  - `test_benchmark_plan_creates_run_dir`
  - `test_benchmark_submit_uses_persisted_plan`
  - `test_benchmark_collect_reports_success`
  - `test_benchmark_collect_failure_writes_no_cli_state`
  - `test_benchmark_index_export_uses_selected_index`
  - `test_benchmark_index_commands`
- `tests/cli/test_storage_cli.py`
  - `test_show_writes_success_to_stdout_and_ambiguous_detail_to_stderr`
  - `test_show_detail_uses_unique_filtered_match`
- `tests/cli/test_transfer_cli.py`
  - `test_transfer_push_dataset_command_routes_to_dataset_transfer`
  - `test_transfer_pull_artifact_command_uses_pulled_envelope`
- `tests/cli/test_config_cli.py`
  - `test_acquire_cli_resolves_selection_surface`
  - `test_model_workflow_cli_resolves_and_submits_selection_surface`
  - `test_config_public_commands_only`
  - `test_config_edit_seeds_missing_file_and_uses_editor`
  - `test_train_submit_uses_cli_default_remote_target`
  - `test_train_submit_cli_renders_follow_failure`
- `tests/storage/test_sync_cli.py`
  - `test_sync_cli_resolve_record_emits_remote_catalog_envelope`
  - `test_sync_cli_finalize_stage_uses_root_kind`
