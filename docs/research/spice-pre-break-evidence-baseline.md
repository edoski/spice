# SPICE pre-break code, data, environment, and performance baseline

Capture and verification window: 2026-07-10T17:34:10Z–2026-07-11T05:15:01Z

Status: read-only evidence freeze for the Wayfinder ticket **Freeze the pre-break code,
data, environment, and performance baseline**. This report approves no architecture,
metric, migration, deletion, compatibility path, or performance tolerance.

No production file, test, lockfile, mobile file, database, corpus, artifact, benchmark
run, scheduler job, or university root was changed. No raw database was copied. Database
queries used read-only/immutable connections; file hashes of active catalogs are
point-in-time identities, not transactionally frozen backups.

The companion [path/size/content manifest](spice-pre-break-evidence-manifest.tsv)
contains 1,245 relative-path rows: all 830 historical run files, all 145 derived export
files, all 265 figure files, and five local catalog/result-index files. Its SHA-256 is
`213e31475bcd9a56e44385fcc61f9be40ff18d4120adfdf95063d742ccdb143b`.
Corpus and model bytes are deliberately not in that manifest; their non-secret root
identities/counts were frozen, but their data bytes were neither copied nor content-hashed.

## Bottom line

- The committed production baseline is exactly 29,004 physical Python lines in 219
  files at Git revision `b9b9a53f42e3e88855ae5488ffff06d3d334fdee`.
- There are 23 benchmark definitions, not 17. All parse and produce unique run IDs, but
  only 20 fully materialize against the current catalog and only eight reference roots
  that are both catalogued and physically present.
- The current gate is not green: pytest has one stale expectation, the repository-wide
  Ruff command has 68 findings, and Pyright has one error. Vulture, scoped Ruff, CLI
  help, mobile typecheck, lock validation, and installed-package compatibility pass.
- Eight historical collection snapshots preserve 2,609 records. Current code can load
  only the two block-quartile snapshots. The other six still declare schema version 1
  but fail current validation. The derived SQLite index therefore covers only 1,296
  observations and is not a complete historical source.
- Local and university catalogs disagree with simple filesystem-root counts. This is a
  frozen inventory fact, not proof that either side is authoritative.
- The university checkout and lock match the local committed baseline, but the configured
  university virtual environment cannot currently import Torch because
  `typing_extensions` is unavailable. It is not a runnable reproduction environment.
- Representative read-only control-plane timings and historical scheduler envelopes are
  frozen below. Existing records do not contain defensible per-epoch throughput, peak GPU
  memory, inference latency, CUDA/driver identity, or exact remote lock provenance, so no
  ML performance regression threshold can be approved from this snapshot.

## 1. Code and lock identity

| Fact | Frozen value |
|---|---|
| Branch | `main` |
| HEAD | `b9b9a53f42e3e88855ae5488ffff06d3d334fdee` |
| HEAD tree | `c9bc6dc1d06e3f03fc0ac0b0f616674dd4df3875` |
| HEAD commit time | `2026-07-06T11:55:52+02:00` |
| `origin/main` | `e804880b000e03825bd1d859a138b617dd2e2a87` |
| Ahead of `origin/main` | 3 commits: `4b90a951`, `7ce42888`, `b9b9a53f` |
| `uv.lock` | 636,348 bytes; 3,189 lines; 127 package records |
| `uv.lock` SHA-256 | `fc11496546431f718d2ac61f83e5a9f1df41df6373ee9d0860612d2963efe5b0` |
| `uv.lock` Git blob | `5186e30ba35cac1101b4558fe27d21f36757dc84` |
| `pyproject.toml` SHA-256 | `3fcfbb558ed3f25d8c7ffa0d954d82ef9d61508f493b28a627dac74e249ba262` |
| Installed-package freeze | 93 compatible packages; manifest SHA-256 `e831d26e39b36930bb94db1c454a6bf599033bb7a0fcd9f57e4af284bed92892` |
| Mobile lock SHA-256 | `3919314e7a7be1e751945881c9d827eb765ebe880734d5389a9f183eb03bc050` |

`uv lock --check` passes. The local and university `uv.lock` hashes are identical.

The worktree was already dirty. Five tracked files are modified and charting reports are
untracked. The tracked binary diff SHA-256 is
`b687d33013d956dfc36158bd111d81f074aba03071c48888011975ffb7284498`.
There is no tracked diff under `src/spice`, `tests`, `uv.lock`, `pyproject.toml`, or
`apps/mobile`, so production, tests, and dependency inputs correspond to HEAD. The only
dirty Python file is the user-owned benchmark renderer
`benchmarks/scripts/render_lstm_block_count_quartile_results.py`:

- current SHA-256: `0e1aefbe0d20f28ff7417fc37946e4a3210fcdf165b74868a4f43c56ca66c836`;
- HEAD SHA-256: `403cbaa5314cd6c4521a54b947047a6c5bec0f49490ec3f9f7cd34ace7dcedd9`;
- existing diff: 40 insertions and 34 deletions.

Historical derived exports do not universally record their renderer hash. They must not
be attributed automatically to either version.

## 2. Production and test inventory

The counting rule is physical lines, including blanks and comments, in every
`src/spice/**/*.py` file. It excludes tests, YAML, scripts outside `src`, mobile code,
Solidity, documentation, caches, and generated data.

| Subsystem | Python files | Lines |
|---|---:|---:|
| Storage | 36 | 5,429 |
| Modeling | 37 | 5,171 |
| Benchmarks | 18 | 2,891 |
| Config | 10 | 2,333 |
| Corpus | 13 | 2,295 |
| Temporal | 14 | 1,548 |
| CLI | 10 | 1,456 |
| Features | 16 | 1,424 |
| Evaluation | 10 | 1,253 |
| Prediction | 12 | 1,025 |
| Serving | 8 | 983 |
| Execution | 7 | 931 |
| Acquisition | 7 | 889 |
| Workflows | 7 | 690 |
| Core | 10 | 548 |
| Package-level/config initializer | 4 | 138 |
| **Total** | **219** | **29,004** |

Tests contain 81 Python files: 75 `test_*.py` modules plus six top-level support files,
for 15,585 physical lines. The earlier statement “75 test files” was counting only the
test modules.

## 3. Current verification gates

| Gate | Exact result |
|---|---|
| `uv lock --check` | Pass |
| `uv pip check --python .venv/bin/python3` | Pass; 93 compatible packages |
| Full pytest | **427 passed, 1 failed in 7.19 s** |
| Repository-wide Ruff | **Fail; 68 findings in 13 committed benchmark scripts** |
| Ruff on `src tests` | Pass |
| Pyright | **Fail; one `reportOptionalSubscript` error** |
| Vulture | Pass with no output at configured 90% confidence |
| CLI import/help | Pass; ten top-level commands |
| Mobile `npm run typecheck` | Pass against existing `node_modules` |
| `git diff --check` | Pass |

The pytest failure is the evaluator-list expectation in
`tests/cli/test_config_cli.py:170`: the expected list omits the current
`block_poisson_replay_300` configuration.

Repository-wide Ruff findings are 49 `E501`, 13 `I001`, three `F401`, two `F841`, and
one `UP035`. They are in committed benchmark scripts. The dirty renderer passes Ruff by
itself, so it caused none of these findings. The earlier blanket statement “Ruff passes”
was true only for the narrower `src tests` command.

Pyright reports the existing optional `block_numbers` narrowing error at
`src/spice/temporal/problem_store.py:133`. Vulture emitted no candidates; per repository
policy, that is not proof that every symbol is live, only that there was no reported
candidate requiring manual dynamic-use review.

## 4. Benchmark, evaluation-suite, and evaluator definitions

Manifest hashes use SHA-256 over sorted
`relative_path NUL byte_size NUL file_sha256 LF` rows.

| Definition set | Files | Bytes/items | Manifest SHA-256 |
|---|---:|---:|---|
| Benchmarks | 23 | 29,452 bytes; 3,734 expanded plan seeds | `587d98db2ac8ee3ad17478b630e71aba704656231e9d37e65c3f5e572b1f87ea` |
| Evaluation suites | 22 | 410,385 bytes; 3,059 windows | `d70761f916f3808054727cd66aeb45caaa2454c28b965eb640df543df35be977` |
| Evaluators | 3 | 301 bytes | `7601110568c244a5bd1ff409e15840616ca43ea46f006b4800f335d0e252e97c` |

All 22 suites validate through the typed loader, match filename to top-level ID, contain
unique item IDs and coordinates, and use only one window type per suite. They contain
1,763 timestamp windows and 1,296 block windows. Three suites are not referenced by a
current benchmark: `avalanche_octane_1p53m_edge_case_recommended`,
`polygon_bhilai_1p53m_edge_case_recommended`, and `ethereum_pectra_smoke`.

Evaluator identities are:

- `poisson_replay`: 7,200 seconds, 50 repetitions, `0.05/s`, seed 2026; SHA-256
  `d2089acf1fc7bd75b563c49f84a1d369c91e8ad9d45f803470f06df90899f25c`;
- `block_poisson_replay`: 1,200 blocks, 50 repetitions, `0.3/block`, seed 2026;
  SHA-256 `d2a6cdcd248abf9677772b49d5d95ef65f2e0963b9454a89b5caca15c45fb233`;
- `block_poisson_replay_300`: 300 blocks, 200 repetitions, `0.3/block`, seed 2026;
  SHA-256 `21461a5a941ec55da06fe6381e44b921ce264366ef50297198173db119ff60f0`.

### All 23 benchmark definitions

| Definition | Seeds | Bytes | SHA-256 |
|---|---:|---:|---|
| `delay_degradation_eth_lstm_beyond_600` | 10 | 968 | `6e2cc2c0e530a994351bbc988d009f288164ff247a1607d22ef1932652004123` |
| `delay_degradation_eth_polygon_lstm_330_900` | 44 | 1,027 | `3d52bcf5d4168adbb80955d787aa0020fe3f8d6e2c8f102e36502efdcc25a3c6` |
| `delay_degradation_extension` | 270 | 1,344 | `3186bdae24fdde2151c10bab778da6b0e170e4c81660b85bfa0d9ec10dff3dd2` |
| `delay_degradation_lstm_long_extension` | 30 | 1,160 | `dbda8e5630563e0b00fd300ca32c127d2d0ff50305459fafc05767172a8af4ab` |
| `delay_degradation_short_window_fillin` | 20 | 1,027 | `c1e5fe85c9b14ab7d836c6bc359ab0da6daf1f135f6e69f6e87cb9919542779b` |
| `delay_degradation_sweep` | 180 | 1,255 | `081dd4056efe697eac1f0a03b2b6e48ae7e5fbf4273a3f26ee826e375df16c66` |
| `edge_case_baseline_36s` | 69 | 2,838 | `9bc6d0563fd1a4afc0ba075f00d0ebcdff40fd8c6e2ecaddfd76f3a237afc6f5` |
| `elapsed_position_ablation` | 36 | 1,267 | `89604b0b5c7a71138f9ce16bf874c76f7a2de8dbd41c45b7d013a9147884af07` |
| `ethereum_pectra_jun20_edge_case_lstm_36s` | 473 | 1,132 | `895449a4b118fdfaa98791e1d6f97cbff420671cf794b445c7827dc8d3858895` |
| `large_capacity_hpo` | 27 | 1,240 | `e4d6afe4b1664377e1f665e868f6c6b1b7b053be658e0ff2ab475d5c371dfcf8` |
| `lookback_window_sweep` | 54 | 1,224 | `476703ae14da392c9172067d700a1e2a2f7b41f1289920f7d1581a70dd496646` |
| `lstm_36s_block300_quartile_eval` | 648 | 1,027 | `533f99a6896ce46aee0b2932451c111baec77694b445793b183a7f351a8af143` |
| `lstm_36s_block_count_quartile_eval` | 648 | 1,033 | `9d6bdc4a3a964fa889144a76eb6732ee76d79520e1f8a040392f2b2e3bf41ccf` |
| `lstm_36s_large_polygon_avalanche_edge_eval` | 423 | 664 | `956c6fdc85d1e3fe5923da77e7b2926a74cb36d4a2509c36b3775ca05ddba529` |
| `lstm_36s_matched_training_budget_polygon_avalanche` | 2 | 838 | `b5a24fdfd2896757dbdb23c6888e0753eb00cbbe736328e497f0453b3bc04f20` |
| `lstm_36s_wall_clock_quartile_eval` | 648 | 1,009 | `4a87bb732a8aefa76f07915452d3f8d25bd5bcccd4d645ad119953ee3f8aaf53` |
| `nov9_cutoff_36s_day_eval` | 9 | 2,973 | `cd1db487829e200a8cda18eb2a741fbb5957e79f6b27cd92d70986ba88f7b6f7` |
| `nov9_cutoff_36s_sweep` | 18 | 1,074 | `a43c284bba4606308d57e1f88a57edb0778316fb22861f2b144644c093a0404a` |
| `nov9_cutoff_36s_warm_hpo` | 27 | 1,212 | `be851f0b7db08d0a5d1211a66a2ef1f3c12ecd925740b30b5b2c09dad7ed324a` |
| `old_window_comparison_36s` | 8 | 1,579 | `700ed2e672159d815c6bb0d5071b2dd5a583b21d49cc8dd6a9526d1f81581d2b` |
| `priority_fee_ablation` | 36 | 1,260 | `a1d6fca806a52894119607b374877f1679b5ed54355374c925913ef4e38d91b8` |
| `safe_baseline_grid` | 18 | 1,130 | `a7043cb0f2789851c530e46639534f51f8cbed23ca324a1672de52722c8cba76` |
| `slot_spacing_sweep` | 36 | 1,171 | `64f15ecf4edd2c7f9180088c61aa44b89df3aec5e8a8972cf8f05f46d2f27eb1` |

All definitions parse and generate unique run IDs. Current full materialization fails
for `lstm_36s_large_polygon_avalanche_edge_eval`, `nov9_cutoff_36s_day_eval`, and
`old_window_comparison_36s` because no matching artifact exists. Twelve more reference
three pruned historical corpora for which only small manifest backups remain. Only eight
definitions currently have every explicit corpus/artifact both catalogued and physically
present. Successful plan materialization is therefore not proof of executability.

## 5. Historical runs and results

The local ignored run tree contains 195 run directories across 27 path groups, 830 files,
and 35,069,893 bytes. Its manifest SHA-256 is
`2ef591fcf479240fb87b6dfdde1feca4e6f116d8aeab339a3d177bd283428b8f`.
The same sorted path/size/content recipe used for definition manifests produced this
digest. Of the directories, 151 are `submit_case` development debris, one is a
`plan_case`, and 43 are other historical runs. Metadata names 189 L40 targets and six
RTX 2080 Ti targets.

Eight collection snapshots preserve 2,609 result records:

| Historical run | Records | Target class | Recorded commit(s) | Collection SHA-256 |
|---|---:|---|---|---|
| `delay_degradation_eth_lstm_beyond_600/20260514T181204Z` | 5 | L40 | `ce503d6…` | `ba2b7f5943cca9e304f7587108f648a6ab193cb1684d36da9e8101c838125f5d` |
| `delay_degradation_lstm_long_extension/20260513T114105Z` | 15 | L40 | `ce503d6…` | `8e736ad4b8646ee47a46336c7d5b7363fff9a59a2c964866492efff26f6c5b0e` |
| `delay_degradation_short_window_fillin/20260513T113030Z` | 10 | L40 | `ce503d6…` | `df361797214735964fcf03c3c22d463203c20fad7e9fa454000ed96fc40295bf` |
| `ethereum_pectra_jun20_edge_case_lstm_36s/20260620T161342Z_4h_plus_completed` | 212 | L40 | `f59817d…` | `6b70b5fc7098772976d19aecbe326a25e3edddd980d4ab9afe43e12b1a78ae91` |
| `lstm_36s_block300_quartile_eval/20260706T095710Z` | 648 | RTX 2080 Ti | `b9b9a53…` | `d201806364493f6ed9d32ad9162982e8bc988ad56a7e64c287c3c150ff38fd1c` |
| `lstm_36s_block_count_quartile_eval/20260629T184758Z` | 648 | RTX 2080 Ti | `4b90a95…` | `b03e8ac7914456eeda848515e100dbbade52abc7f02602f190f952b8a6ee9acf` |
| `lstm_36s_large_polygon_avalanche_edge_eval/20260622T091628Z` | 423 | RTX 2080 Ti | `f59817d…` | `30c82ffe91ca624d6d7c9c570e898764cedff756643e2ad603b645eba4e9bef6` |
| `lstm_36s_wall_clock_quartile_eval/20260628T131456Z` | 648 | RTX 2080 Ti | `74cdabf…`, `efad41d…` | `3ac0a12a4fddced7a7c03472f38013c1bc61fe45d3e0cec27b87a7a056694d56` |

Each run's `plan.jsonl` is the strongest exact configuration identity because metadata
and collection rows do not retain the source YAML hash.

### Historical codec and projection status

Current code loads only the two block-quartile collections. The other six fail strict
`BenchmarkCollectionSnapshot` validation while still declaring schema version 1:

- three delay collections: 75, 225, and 150 validation errors;
- Ethereum edge collection: 424;
- Polygon/Avalanche edge collection: 846;
- wall-clock quartile collection: 1,296.

Consequences:

- `spice benchmark index rebuild` cannot rebuild from all eight snapshots;
- `benchmarks/results.sqlite` covers only the two readable collections;
- older exports preserve observations absent from the current index and not recoverable
  through the current strict codec;
- this does not justify a compatibility shim. Immutable source preservation and explicit
  archival classification are the clean-break route.

`benchmarks/results.sqlite` is 8,577,024 bytes, has SHA-256
`ba70a8f65e9210edc2cfee63243d69e46f55235f5b78f39d7dd5cdd83bf724b0`,
and passes `PRAGMA integrity_check`. It contains two benchmark runs, 1,296 observations,
and 10,368 metric values. Each run contributes 648 observations; each chain contributes
432. It is an ignored rebuildable projection, not durable audit state.

The derived trees are larger but have incomplete provenance:

| Tree | Inventory | Manifest SHA-256 |
|---|---|---|
| `benchmarks/exports` | 145 files; 231,911,606 bytes; 718,359 CSV rows; 121,131 Parquet rows | `3fa9b351cda34052ab71e0f0ed0635f71d9cb0c01770c4f9eb75eb49b66d239d` |
| `benchmarks/figures` | 265 files; 33,206,764 bytes; 99 PNG, 83 SVG, 83 PDF | `3d13652355a93abac965b2a22f67472a20359ff5355e6e35c2101c69001c069f` |

Neither tree universally records generator/config/renderer identity. For example, merged
delay exports contain 183 rows while the three preserved delay collections contain only
30 records. Existing exports must be frozen as archival evidence, not silently
regenerated or reinterpreted.

## 6. Non-secret storage-root inventory

Identifiers, usernames, hostnames, and absolute university paths are intentionally
omitted. Counts include point-in-time catalog and filesystem observations; discrepancies
are not repaired here.

### Local workstation

The workspace is on local journaled APFS solid-state storage. `outputs` occupies about
1.2 GiB and contains 10,539 files. Major components are: corpora 697 MiB/9,526 files,
artifacts 268 MiB/39 files, benchmark runs 36 MiB/830 files, and state-database backups
169 MiB/11 files.

| Root kind | Catalog rows | Final filesystem roots | Qualification |
|---|---:|---:|---|
| Corpora | 5 | 5 | Plus one acquisition staging directory and manifest backups |
| Studies | 0 | 0 | No local study root exists |
| Artifacts | 38 | 8 | Thirty catalog entries have no matching simple local root count |

The local catalog is 36,864 bytes, passes `PRAGMA integrity_check`, and had point-in-time
SHA-256 `8b52141a32d3e0de952757046a95291cfe3b15e3ad038bcdfd6db9385cd5ae34`.
It used WAL mode; its WAL was zero bytes and its SHM companion was 32,768 bytes during
the final capture. No backup was made.

### University execution environment

The clean university checkout is at the same HEAD and has the same `uv.lock` hash as the
local baseline. All four configured roots are on read-write NFS4. The repository mount
is on a different device from the NFS4
virtual-environment/storage/log mount; the latter three share a device. This is only
topology evidence. Observed options included `hard` and `local_lock=none`; they do not
prove rename durability, SQLite safety, or lock correctness. Those require the separate
filesystem ticket.

| Root kind | Catalog | Physical | Intersection | Catalog-only | Physical-only |
|---|---:|---:|---:|---:|---:|
| Corpora | 4 | 5 | 4 | 0 | 1 |
| Studies | 21 | 22 | 18 | 3 | 4 |
| Artifacts | 221 | 179 | 22 | 199 | 157 |

The university catalog is 77,824 bytes, passes `PRAGMA integrity_check`, and had
point-in-time SHA-256
`122060e4ae01c7dc60795334fc54fb064b5856bd5bac01f9dd3da39a32bc18a1`.
It reported delete-journal mode; its WAL was zero bytes and its SHM companion was
32,768 bytes. The benchmark root contained one canonical-depth run directory and 240
files; the log root contained 4,402 files. Venv/storage size and total-file scans timed
out, so no partial totals are reported. No raw file was copied and no active state was
changed.

Canonical root-set fingerprints use SHA-256 over sorted
`chain_name NUL root_id LF` tuples:

| Set | Catalog digest | Physical digest |
|---|---|---|
| Local corpus | `f9721f991d094b164dc701fa5b09bbbcf8bec7d4e51955e35604cb74d01033b4` | same |
| Local study | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same |
| Local artifact | `2ca474accca91e7c8c0b7384edfb18bed316bb633b93ea013d7229c9ab6898e2` | `155ec0f173d0576022510274e351f03df7cbf61d04f15c98d1060cc98b41b23b` |
| University corpus | `6abc6982579afe339318f065f8b5af447bc5c615683258dd182cfa3fd02a8e35` | `2bb48c86280ae121da05c62963b32b29da20d13e15ccf1538031a244359253b5` |
| University study | `e680cbe4679c589593f69490591e9473c65e80af72c7c4fe824d40b6c8ceb43c` | `9a4390aa52229c168c9161365b543036b572058ce5e96a4af64e2d1c9ef0a32d` |
| University artifact | `32853d32a43d3bedca7e9d8896dc2d3fc72ae4a86a38653fd6d9f663c63bf7d6` | `57fcc801a2843bc656678587344c85b60933cdda1532430a132cbe8e8351c44d` |

## 7. Runtime facts

| Fact | Local workstation | University login/configured runtime |
|---|---|---|
| OS | macOS 26.5 build 25F71 | Debian 12, Linux 6.1.0-47 |
| Architecture | arm64 | x86_64 |
| CPU/memory | Apple M2 Max, 12 CPU cores, 96 GiB | Login-node hardware not used as a benchmark |
| Python | 3.11.15 | System and configured venv: 3.11.2 |
| SQLite | 3.53.3, threadsafety 3 | 3.40.1, threadsafety 3 |
| Torch | 2.11.0; MPS available; no CUDA | Metadata says 2.7.1+cu118; import currently fails |
| Lightning | 2.6.5 | 2.6.5 |
| TorchMetrics | 1.9.0 | 1.9.0 |
| NumPy / Polars | 2.4.4 / 1.39.3 | 2.4.4 / 1.39.3 |
| Optuna / scikit-learn | 4.8.0 / 1.8.0 | Distribution metadata returns no usable version |
| Pydantic / FastAPI | 2.12.5 / 0.138.0 | 2.12.5 / 0.138.0 |
| SQLAlchemy | 2.0.49 | 2.0.49 |
| Node/npm | 24.11.1 / 11.10.0 | Not required for recorded GPU runs |
| Scheduler | n/a | Slurm 22.05.8 |

The configured university environment is not healthy: `typing_extensions` is absent;
Torch, Pydantic, SQLAlchemy, and Lightning imports fail; Typer/FastAPI and Web3 encounter
incomplete dependency APIs; and PyYAML, Optuna, and scikit-learn expose missing version
metadata/API-incomplete namespace-like modules. `python -m pip check` is unavailable
because the environment's pip package has no executable module, and `uv` is not on the
login shell path. This is current-runtime evidence, not evidence about the environments
that produced older runs.

Both configured GPU partitions were up during capture. The L40 partition advertised
four one-GPU nodes, all allocated. The RTX 2080 Ti partition advertised ten one-GPU
nodes, four allocated and six idle. Both had a three-day configured limit. No compute
job or `nvidia-smi` probe was submitted, so CUDA, driver, GPU memory, and cuDNN facts
remain unverified at capture time.

## 8. Representative old-path performance

These measurements are descriptive controls, not acceptance thresholds. Local CLI
measurements used seven fresh processes on the M2 Max with the frozen environment.

| Read-only path | Repetitions | Median | Min–max |
|---|---:|---:|---:|
| `spice --help` | 7 | 2,597.931 ms | 2,511.739–2,698.008 ms |
| `spice config list benchmark` | 7 | 2,485.151 ms | 2,341.439–3,311.004 ms |
| `spice show corpus` | 7 | 2,686.912 ms | 2,615.015–2,742.594 ms |
| `spice show artifact` | 7 | 2,812.866 ms | 2,664.061–2,987.847 ms |
| Parse the 648-record, 3,534,752-byte wall-clock collection JSON | 25 | 12.586 ms | 11.433–15.790 ms |

The full pytest duration was 7.19 seconds; it is a verification-runtime fact, not an ML
performance measure.

Existing completion-record envelopes were 4.09 hours for the 300-block quartile run and
4.63 hours for the 1,200-block quartile run. They include scheduling, concurrency,
retries, and evaluation work. They are not per-evaluation latency or GPU-throughput
measurements.

Historical state records target names and Git commits, but not a complete remote lock,
Python, CUDA, driver, cuDNN, GPU, or per-process resource record. No trustworthy baseline
exists here for training samples/second, peak GPU memory, inference latency, serving
latency, acquisition throughput, or interruption/resume cost. Those values must be
measured by later approved evidence tickets before old implementations disappear.

## 9. Interpretation limits

- Historical ML values retain the known weighted-loss reduction, temporal-action,
  economic-estimand, and custom macro-F1 semantics. They are archival behavior, not proof
  that those definitions should survive.
- Artifact-level total loss is repeated into each evaluation observation. It is not 216
  independent loss measurements per chain.
- Broad scheduler completion envelopes cannot be decomposed into model speed.
- Point-in-time active-catalog hashes are not coherent export snapshots and must not be
  used as conversion inputs.
- Catalog/filesystem count mismatches are preservation blockers, not deletion lists.
- Missing historical codec compatibility does not authorize a legacy reader in the
  clean-break production design.
- The report freezes absent provenance as absent. It does not reconstruct or guess it.

## 10. Reproduction commands

Representative commands used during the read-only capture:

```sh
git rev-parse HEAD HEAD^{tree} origin/main
git status --short
git diff --binary | shasum -a 256
shasum -a 256 uv.lock pyproject.toml
uv lock --check
uv pip check --python .venv/bin/python3
find src/spice -type f -name '*.py' -print0 | xargs -0 wc -l
uv run --frozen --no-sync pytest -q -p no:cacheprovider
uv run --frozen --no-sync ruff check --no-cache .
uv run --frozen --no-sync ruff check --no-cache src tests
uv run --frozen --no-sync pyright
uv run --frozen --no-sync vulture
NO_COLOR=1 COLUMNS=120 uv run --frozen --no-sync spice --help
uv run --frozen --no-sync spice config list benchmark
uv run --frozen --no-sync spice show corpus
uv run --frozen --no-sync spice show artifact
sqlite3 'file:benchmarks/results.sqlite?immutable=1' 'PRAGMA integrity_check;'
shasum -a 256 <historical-file>
```

University commands were restricted to noninteractive SSH metadata reads: OS/runtime
versions, Git/lock identity, `stat`/`find` counts, read-only SQLite counts/integrity,
scheduler partition summaries, and package metadata. No command installed, submitted,
copied, deleted, locked, repaired, or rewrote anything.
