# Total-loss versus economic-objective A/B evidence freeze

Date: 2026-07-10

Inspection cutoff: `2026-07-10T17:49:08Z`

Scope: evidence for [Freeze the total-loss versus economic-objective A/B evidence](https://github.com/edoski/spice/issues/5). This report freezes the run named in `CLEAN_BREAK_TRACKER.md`. It does not rerun work, treat later jobs as the original run, use the macro-F1 audit as objective evidence, or approve an architecture decision.

## Verdict

The submitted run is incomplete and supports no total-loss-versus-economic-objective A/B conclusion.

The durable local run state has a complete 473-row plan and a one-to-one 473-row submission ledger at revision `d60a5fb546225dd5732fd6128153bb953083b470`. It has no `collection.json`. The original training job was canceled during fitting. Its 236 `afterok` evaluations emitted no logs. Eight independent economic-baseline evaluations started and failed with the same coverage exception. The other 228 independent baseline submissions emitted no logs.

No evaluation summary in either artifact state database carries any original submission execution reference. The current total-loss artifact was created later by job `65028`, which is absent from the original submission ledger; its 212 evaluation summaries belong to later jobs `65029` through `65240`. Those later training and evaluation records are excluded from the A/B result.

| Evidence requested | Frozen result |
| --- | --- |
| Terminal job state | Exact only where logs prove it: training canceled; eight baseline evaluations failed in application code. The remaining exact scheduler labels are unavailable. |
| Submitted revision | Exact and uniform across all 473 submissions. |
| Configs and IDs | Exact in `plan.jsonl`; summarized below. |
| Objective and loss formulas | Exact at the submitted revision; summarized and linked below. |
| Plan/submission/collection joins | Plan and submission join one-to-one; collection is absent. |
| Predictive metrics | Original job produced none. Pre-existing/later artifact metrics are frozen below as context, not original-run output. |
| Economic metrics | No A/B economic metric exists. The pre-existing baseline's training-time objective metric is frozen as context only. |
| Logs | Nine of 473 submitted log paths exist: one train log and eight baseline-evaluation logs. |
| Hashes | Local run state, surviving logs, artifact snapshots, models, and exclusion evidence are hashed below. |

## Run identity and intended comparison

The tracker names benchmark run `ethereum_pectra_jun20_edge_case_lstm_36s/20260627T204310Z`. Its metadata records creation at `2026-06-27T20:43:10Z` and target `disi_l40`.

| Fact | Frozen value |
| --- | --- |
| Benchmark | `ethereum_pectra_jun20_edge_case_lstm_36s` |
| Run directory | `outputs/benchmarks/runs/ethereum_pectra_jun20_edge_case_lstm_36s/20260627T204310Z` |
| Submitted commit | `d60a5fb546225dd5732fd6128153bb953083b470` |
| Commit subject | `chore(benchmarks): add pectra total loss ab plan` |
| Commit tree | `5a2c5a8f1f403c8a1329bb9c7592645cad318e47` |
| Benchmark-config blob | `38108676021f01cd77c562a2a6fc3ca32496906b` |
| Plan rows | 473: one train, 236 total-loss evaluations, 236 economic-baseline evaluations |
| Submission rows | 473 unique run IDs, job IDs, and execution refs |
| Collection | Absent locally; the matching remote run directory is absent |
| Training corpus | `cor_2edb8f7b84a4edf95e2b` |
| Training cutoff | `2025-12-08T00:00:11Z` (`1765152011`) |
| Evaluation corpus | `cor_7bea5a071afaf090c05a` |
| Planned total-loss artifact | `art_956319e1b7a77b77dcfc` |
| Pre-existing economic-objective artifact | `art_c433194c8699a301f7c5` |

The submitted benchmark definition is frozen at [the submitted revision](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/conf/benchmark/ethereum_pectra_jun20_edge_case_lstm_36s.yaml#L1-L40). It trains only the total-loss arm. The economic arm is the existing artifact `art_c433194c8699a301f7c5`; this was not a simultaneous two-arm retraining run.

## Exact planned config

The full resolved configs are the `config` values in the hashed `plan.jsonl`. The training row resolves:

| Config area | Value |
| --- | --- |
| Surface/selection | `current_row_fee_dynamics`; Ethereum chain ID 1; nominal block time 12 seconds |
| Corpus | `cor_2edb8f7b84a4edf95e2b`; corpus recipe `icdcs_2026` |
| Features | `core_fee_dynamics`, 45 ordered outputs frozen in the plan row |
| Prediction | `icdcs_2026`; family `min_block_fee_multitask` |
| Problem | `current_row_nominal`; 600-second lookback; 36-second maximum delay; nominal slot spacing; `strict_deadline_miss` |
| Model | LSTM; hidden size 256; 2 layers; input projection 256; head hidden size 256; dropout 0.2 |
| Split | train 0.8; validation 0.1; remainder test |
| Training | batch 64; learning rate 0.0003; weight decay 0.0001; clip norm 1.0; max 100 epochs; early-stop patience 20 and minimum delta 0.0001; seed 2026; deterministic; sequence length bounds 64–4096 |
| Objective | validation `total_loss`, minimize |
| Produced root fact | `art_956319e1b7a77b77dcfc` from `cor_2edb8f7b84a4edf95e2b` |

The two pre-cleanup artifact manifests are structurally equal except for `artifact_id` and objective identity:

| Field | Planned total-loss arm | Existing economic arm |
| --- | --- | --- |
| Artifact ID | `art_956319e1b7a77b77dcfc` | `art_c433194c8699a301f7c5` |
| Objective ID | `validation` | `evaluation` |
| Metric | `total_loss` | `profit_over_baseline` |
| Direction | minimize | maximize |
| Objective evaluator | none | `poisson_replay` |

No other manifest path differs: corpus, features and ordered outputs, prediction, problem, model, split, scaler, temporal capability, training settings, and training-source window match exactly.

Both evaluation arms use the same resolved static config: batch size 256, corpus `cor_7bea5a071afaf090c05a`, artifact maximum delay 36 seconds, storage root `outputs`, and Poisson replay with arrival rate 0.05/second, 50 repetitions, seed 2026, and 7,200-second replay windows. They contain the same 236 scenario windows with starts from `2025-12-08T00:00:11Z` through `2026-06-03T21:00:11Z`.

Per arm, the scenario-duration counts are `2h:24`, `4h:24`, `6h:24`, `8h:24`, `12h:24`, `16h:23`, `24h:23`, `36h:23`, `48h:23`, and `72h:24`. Comparing the sorted `(start, duration)` pairs proves the arm window sets are equal.

## Objective and metric formulas at the submitted revision

The total-loss objective spec is `id: validation`, `metric_id: total_loss`, `direction: minimize`: [validation_total_loss.yaml](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/conf/objective/validation_total_loss.yaml#L1-L3). The economic objective spec is `id: evaluation`, `metric_id: profit_over_baseline`, `direction: maximize`, evaluator `poisson_replay`: [profit_poisson_replay.yaml](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/conf/objective/profit_poisson_replay.yaml#L1-L4).

For sample `i`, submitted code computes:

```text
classification_loss = weighted_cross_entropy(masked_offset_logits, minimum_block_offset)
normalized_fee_target_i = (minimum_block_log_fee_i - training_fee_mean) / training_fee_std
regression_loss = smooth_l1(predicted_normalized_fee, normalized_fee_target)
total_loss = classification_loss + 0.5 * regression_loss
```

The exact implementation is [loss.py](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/prediction/families/min_block_fee_multitask/loss.py#L12-L41). Classification weights are inverse training-class frequencies, normalized across present classes: [metrics.py](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/prediction/families/min_block_fee_multitask/metrics.py#L217-L235). Epoch reporting multiplies each default-mean batch loss by batch sample count, sums, then divides by total samples: [metrics.py](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/prediction/families/min_block_fee_multitask/metrics.py#L171-L209) and [metrics.py](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/prediction/families/min_block_fee_multitask/metrics.py#L238-L251).

For replay event `i`, submitted economic accounting computes base-fee metrics:

```text
profit_over_baseline_i = (baseline_fee_i - realized_fee_i) / baseline_fee_i
cost_over_optimum_i = (realized_fee_i - optimum_fee_i) / optimum_fee_i
baseline_cost_over_optimum_i = (baseline_fee_i - optimum_fee_i) / optimum_fee_i
exact_optimum_hit_i = 1[realized_row_i == optimum_row_i]
```

The summary metrics are event means over all replay events; fee-sum diagnostics are sums. See [temporal_accounting.py](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/evaluation/temporal_accounting.py#L85-L124) and [the metric catalog](https://github.com/edoski/spice/blob/d60a5fb546225dd5732fd6128153bb953083b470/src/spice/evaluation/_temporal_replay_metric_catalog.py#L32-L83).

`profit_over_baseline` is a base-fee-per-gas relative saving. It is not full transaction profit: gas used, priority fees, inclusion utility, and latency utility are absent.

## Submission and observed job state

Every submission row records the same commit. Job `63334` is the training row. Jobs `63335`–`63570` are the 236 total-loss evaluations and depend on `afterok:63334`. The 236 baseline jobs span `63571`–`63807` with no submission for `63579`; that ID is not part of this run.

| Submitted cohort | Count | Strongest supported state |
| --- | ---: | --- |
| Train job `63334` | 1 | Canceled. The log contains Slurm's `JOB 63334 ... CANCELLED AT 2026-06-28T14:00:59` followed by `SIGTERM`; no `train complete` line exists. |
| Total-loss evaluation jobs `63335`–`63570` | 236 | No log exists for any job. All were gated by `afterok:63334`. This proves no started application output, not an exact scheduler terminal label. |
| Baseline jobs `63571`–`63578` | 8 | Each log reaches preparation, then terminates with `ValueError: Evaluation examples do not cover the requested replay window`. |
| Remaining baseline submissions | 228 | No log exists. There is no dependency in the submission ledger. Exact scheduler terminal labels are unsupported. |

At inspection, none of the sampled job IDs appeared in `squeue`; `scontrol show job` reported `Invalid job id specified`. `sacct` could not query the accounting database because its connection to `slurmng:6819` was refused. The run state contains no status field or scheduler snapshot. Therefore this report does not relabel the 464 no-log jobs as failed, canceled, or dependency-never-satisfied.

The eight surviving baseline logs map to eight 2-hour plan windows. All have the same exception signature. Their individual SHA-256 values are frozen below.

## Join audit and later-run exclusion

The plan/submission join is complete:

- 473 plan rows and 473 submission rows;
- 473 unique plan run IDs and 473 unique submission run IDs;
- no plan row without a submission and no extra submission;
- 473 unique execution refs and job IDs;
- one submitted Git revision.

The collection join does not exist. There is no local `collection.json`, and the exact remote benchmark-run directory is absent. Both active artifact state databases and the June 29 pre-cleanup backups contain zero evaluation summaries whose execution provenance matches any original submitted evaluation job.

The current total-loss artifact cannot repair that gap:

- original job `63334` was canceled without completion;
- later job `63874`, absent from the run ledger, attempted the same artifact and failed with `IndexError` in best-state finalization;
- later job `65028`, also absent from the run ledger, completed training;
- artifact state creation time is `2026-06-28T23:14:02Z`, matching the successful later job and occurring after the original cancellation;
- its 212 current evaluation summaries carry jobs `65029`–`65240`, not jobs `63335`–`63570`.

The later artifact and evaluation summaries may be evidence for a separate run. They are not evidence for this submitted A/B run because their submission ledger and revision are not frozen here.

## Metrics that exist, and what they mean

No predictive or economic metric was persisted by an original submitted job. The values below come from pre-cleanup artifact snapshots and are frozen only to prevent accidental attribution.

The economic artifact existed before this run; its storage creation time is `2026-05-24T08:26:11Z`. The total-loss values come from the later successful job `65028`.

### Predictive snapshots at each artifact's recorded best epoch

Both artifacts record best epoch 6.

| Split metric | Later total-loss artifact | Pre-existing economic artifact |
| --- | ---: | ---: |
| Validation total loss | 1.290840130773 | 1.291828255812 |
| Validation classification loss | 1.288691749719 | 1.289621523023 |
| Validation regression loss | 0.004296762319 | 0.004413464635 |
| Validation offset accuracy | 0.391779678154 | 0.390899069164 |
| Validation macro-F1 | 0.361747261570 | 0.361211406549 |
| Validation log-fee MAE | 0.084885503923 | 0.085759820079 |
| Validation log-fee MSE | 0.012152454514 | 0.012482522175 |
| Test total loss | 1.344697241729 | 1.346273887282 |
| Test classification loss | 1.290250915513 | 1.287586480771 |
| Test regression loss | 0.108892648408 | 0.117374813593 |
| Test offset accuracy | 0.393933661655 | 0.392583412152 |
| Test macro-F1 | 0.373146794948 | 0.370844995631 |
| Test log-fee MAE | 0.415637597621 | 0.429435298695 |
| Test log-fee MSE | 0.308772659797 | 0.333150593956 |

Macro-F1 is a diagnostic in both manifests. It was not either artifact's selection objective and is not objective evidence for this ticket.

### Pre-existing economic artifact's training-time objective snapshot

At its recorded best epoch, the existing economic artifact reports:

| Metric | Value |
| --- | ---: |
| `profit_over_baseline` | 0.012002196180 |
| `cost_over_optimum` | 0.031452355472 |
| `baseline_cost_over_optimum` | 0.045429377195 |
| `exact_optimum_hit_rate` | 0.390720322382 |
| `realized_fee_sum` | 8,125,184,563,360.885 |
| `baseline_fee_sum` | 8,256,077,908,528.969 |
| `optimum_fee_sum` | 7,910,418,257,832.748 |

This is a validation-time model-selection snapshot from the pre-existing artifact. It is not a result over the planned 236-window evaluation suite. There is no corresponding original-run total-loss-arm economic metric and therefore no A/B delta, interval, win rate, or claim of superiority.

## Frozen hashes

Local run-state hashes:

| Evidence | SHA-256 |
| --- | --- |
| `CLEAN_BREAK_TRACKER.md` | `df66bebdb38d47972ea1fc45665a6e4f319e3974396a56bec6cd06a35ff391b3` |
| `metadata.json` | `4a0a362daf23dbc7de25132f44f050e7f3100043f1849e4702a72bbd556aa139` |
| `plan.jsonl` | `495d509510c1b9183f4d661fbd6aeea38ca150c8001b313202de97ad0ae33f8d` |
| `submission.jsonl` | `e2471a9637eef4bbb3b4b7bd283c9ccd6c7c2e6bd0ca026505e1a7ce178f465a` |

Original surviving log hashes:

| Job/log | SHA-256 |
| --- | --- |
| train `63334` | `227b2e88378d53c7816b6bb0e1d487590a23b71e57c8e009f6bc0b869aa38e50` |
| evaluate `63571` | `a985424af1e93ff64f930c661425e70d22a4dd09bb199b77f8a4b9c64d3e56b4` |
| evaluate `63572` | `63b76823a1ac71e17ca2c6bbb72ab255c4a3a7815bc94e1aa0a5d4b004038c2e` |
| evaluate `63573` | `63b76823a1ac71e17ca2c6bbb72ab255c4a3a7815bc94e1aa0a5d4b004038c2e` |
| evaluate `63574` | `ed3a3a3e1e2ba9ddc171753397fddaba1326e3831b9079bda096c78d3b46815b` |
| evaluate `63575` | `429b616b898a9823df4ea32de68c18b5b1d8fc20ae1a1cca01e0314dde7175d9` |
| evaluate `63576` | `63b76823a1ac71e17ca2c6bbb72ab255c4a3a7815bc94e1aa0a5d4b004038c2e` |
| evaluate `63577` | `44079984bfe2b1c138ba29646926b6d10162f3b9071f9c077f370aee217f6449` |
| evaluate `63578` | `d5e1b685ea7f2b7ab955a09fd422ff0f43765944222f5d5736e4c95e772b484e` |

The SHA-256 of a deterministic 473-line manifest in submission order, where each line is `job_id|log_path|sha256` or `job_id|log_path|MISSING`, is `0e5b4ff6f6022545a27a1cd7a890a926c6393da2c404ffd94f437bc19410e67c`.

Artifact and exclusion hashes at the inspection cutoff:

| Evidence | SHA-256 |
| --- | --- |
| total-loss pre-cleanup state backup | `afb91d9f8fb74fc7af3beda2d8f1fd4e8cf3fabe3c4dc499f833e2a70b62ed78` |
| economic pre-cleanup state backup | `397ed0dbb35f428d1684e25e1daebd963069f89c618c2358ebe4cbb4ddde2617` |
| metadata-cleanup inventory | `f5e3d88f495df09130826fb15ba3e3b8a0820e410639a1a6999039cf6b68ea94` |
| later total-loss model | `3e6282c80fbaa52ccc423c1dd3a969f900e6ea4b3769e3509c5305e965274326` |
| pre-existing economic model | `1c247f8989858efbb26833195fa84986d674d6cc4ec2866f22097bff99b5b543` |
| later failed train log `63874` | `b0ecf9e162973c210485c84e725805e2cdcb2bd2be017be10efd597dac491a21` |
| later successful train log `65028` | `aabe7e05abd2af82f65e9c2883cbd3676812251ed706d436c63c3782df77287f` |

The active state-database snapshot hashes were `28c00e448468a7ebc3b06560144a19bbec955900304d53b5f157062aa7edb5ee` for the later total-loss artifact and `b8590c49341ef2ebf095df08e6d4a3c367548c2d19ace87b023cbeff2596706b` for the economic artifact. Active databases can receive later evaluations; the pre-cleanup backups above are the stable metric sources used here.

## Supported and unsupported claims

Supported:

- the exact submitted intent, revision, resolved configs, IDs, dependencies, and evaluation-window symmetry;
- cancellation of original training job `63334`;
- application failure of baseline jobs `63571`–`63578` with one exact exception;
- absence of the other submitted log files and of a collection snapshot at inspection;
- absence of original execution refs from active and pre-cleanup artifact evaluation state;
- later provenance of the currently materialized total-loss artifact;
- the formulas implemented at the submitted revision;
- pre-existing/later artifact training snapshots, only with their provenance labels.

Unsupported:

- exact scheduler terminal labels for the 464 submitted jobs without logs;
- any successful original total-loss training result;
- any predictive or economic metric produced by an original submitted job;
- any 236-window A/B aggregate, paired difference, confidence interval, win rate, or superiority claim;
- attribution of jobs `63874`, `65028`, or `65029`–`65240` to the original run;
- using macro-F1 as either arm's objective evidence;
- an architecture, objective-retention, training-selection, or rerun decision.

The correct downstream fact is: the historical A/B attempt is unrecoverably incomplete as objective evidence. For this bounded bachelor's-thesis project, archive the failed attempt and move on; do not repair operational machinery or repeat the comparison unless a later thesis decision shows concrete need. Any approved future comparison needs a new protocol and run identity and must not overwrite or masquerade as this run.
