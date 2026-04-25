# Concrete CLI Commands

CLI commands are the user-facing edge. They resolve named configs, own command defaults, submit remote jobs, inspect storage, and start transfers.

## Mental Model

```text
terminal command
  -> Typer command parser
  -> config/surface resolution
  -> local workflow or remote submission
```

The CLI should be ergonomic. Lower layers should stay explicit and typed.

## Workflow Commands

Commands:

| Command | Behavior |
| --- | --- |
| `acquire` | Run acquisition locally. |
| `train` | Train locally or submit remotely. |
| `tune` | Tune locally or submit remotely. |
| `evaluate` | Evaluate locally or submit remotely. |

`train`, `tune`, and `evaluate` support `--submit`, `--dependency`, `--target`, and `--detach`. `--storage-root` is not accepted with `--submit`, because remote execution rewrites storage root from the selected target config.

Default remote target is `disi_l40` at the CLI layer.

## Storage Show Commands

`show dataset`, `show study`, and `show artifact` query the catalog. With broad filters, they list matches. With one exact match and detail options, they render root-specific state.

Detail panels:

| Root | Detail views |
| --- | --- |
| Dataset | Manifest and acquire runs. |
| Study | Manifest, trials, config. |
| Artifact | Manifest, training epochs, evaluation runs. |

## Delete Commands

Delete commands require one resolved root. Dataset and study deletes protect dependent roots unless cascade is explicitly requested.

```text
selector
  -> exactly one catalog match
  -> dependency check
  -> root-kind validation
  -> remove root
  -> refresh/reindex catalog
```

## Refresh Command

`refresh catalog` rebuilds the derived catalog from root state DBs. This is useful after manual file movement or transfer completion.

## Transfer Commands

Supported commands:

| Command | Direction |
| --- | --- |
| `push dataset` | Local corpus to cluster. |
| `push study` | Local study to cluster. |
| `pull study` | Cluster study to local. |
| `pull artifact` | Cluster artifact to local. |

All transfer commands use selector filters and explicit target resolution. `--replace` controls destination replacement.

## Config And Benchmark Commands

Config commands inspect resolved config and available specs. Benchmark commands run benchmark-oriented utilities through the same config resolution stack.

## Invariants

| Rule | Why |
| --- | --- |
| Remote target fallback lives only here. | Execution and sync APIs stay explicit. |
| Dependency and detach require submit. | They only make sense for scheduled jobs. |
| Detail views require one match. | Avoids rendering mixed root state. |
| Delete validates root kind. | Protects storage layout. |

## Extension Pattern

New commands should parse user intent, resolve typed config or selectors, then delegate to workflow/storage/execution functions. Keep business logic in owner packages.

