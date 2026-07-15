# Issue 59: paper and reference-system attribution evidence

Date: 2026-07-14

Scope: primary-source evidence for the naming and attribution decision. This note does not
choose the project's name, paper title, CLI name, package name, or compatibility policy.

Primary sources:

- supplied double-blind manuscript, *SPICE: A Predictive Framework for Cost-Optimization
  in Multichain Environments*,
  `/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`, SHA-256
  `2afa36d5c82cc2f8be854707fad91b86562d399896b9ee163decd75f470d4b5c`;
- supplied reference repository
  [`UniBO-PRISMLab/ICDCS-Model-Training`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/tree/bcf80b92877941e3b05a7dc5138560ffe41df27e)
  at clean commit `bcf80b92877941e3b05a7dc5138560ffe41df27e`;
- this repository at `e00e7fbdf16f536b05615ae0af010081bb38f093`.

## Paper identity and scope

The exact manuscript title is *SPICE: A Predictive Framework for Cost-Optimization in
Multichain Environments*. It expands SPICE as **Spatio-temporal Predictive Inference for
Cost-optimized Execution**. In the paper, unqualified **SPICE** names the full multichain
framework: spatial chain selection, temporal scheduling, their combined flow, and the
distributed-reputation mechanism used for the oracle integration (Abstract and Secs. I,
IV, and V, PDF pp. 1, 4-7).

The paper also uses the qualified terms **SPICE temporal optimization** and **SPICE temporal
module**. It explicitly says the spatial and temporal modules can operate independently, so
a single-chain application may use only the temporal optimization. This supports qualified
attribution to a SPICE temporal component; it does not make the temporal component alone
coextensive with unqualified SPICE (Sec. I, PDF p. 1; Sec. VI-C, PDF p. 9).

The manuscript contains no author line, no PDF `Author` metadata, and no other exact author
list. Footnote 11 says the experiment repository was hidden for double-blind review (Sec.
VI-A, PDF p. 7). The reference repository's two commits are authored by the Git identity
`ivanzy`, but a commit author is not evidence of paper authorship
([history](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/commits/bcf80b92877941e3b05a7dc5138560ffe41df27e)).
The exact paper authors are therefore unresolved in the supplied primary sources; inventing
or inferring them would be false attribution.

## What the paper's temporal module contains

The temporal component is a decision system, not merely one neural model. At time `t`, it
observes the most recent `N` seconds, considers the next `M` seconds, identifies the expected
minimum-cost **future** block (the **min-block**), estimates only the base fee associated with
that minimum, and schedules execution for that block. The paper contrasts this with predicting
the complete future trajectory (Sec. IV-A, PDF pp. 4-5).

Its experimental realization has these named elements (Sec. VI-A, PDF pp. 7-8):

| Element | Paper statement |
| --- | --- |
| Backbones | LSTM, Transformer, and TransformerLSTM |
| Outputs | block-offset classification logits and one scalar fee prediction, through two MLP heads |
| Inputs | 600-second lookback; block metadata; cyclical calendar fields; elapsed-time and trend fields; rolling fee and gas-utilization mean/standard deviation over 10, 50, and 200 blocks |
| Fitting | chronological non-overlapping train/validation/test intervals; train-statistic feature standardization; fee-related log transform; AdamW; early stopping |
| Loss | inverse-frequency weighted cross-entropy plus Smooth L1, combined as `alpha * L_block + beta * L_fee` |
| Conditions | a separate model per chain and 12-, 24-, and 36-second window |
| Simulation | Poisson request rate `0.05/s`; random two-hour windows; 50 repetitions; immediate next-block execution as the no-prediction baseline |

The paper does not define an indexed target-construction formula, tie rule, exact logarithm,
target normalization, candidate-row availability rule, submission/inclusion boundary, or
serving interface (Secs. IV-A and VI-A, PDF pp. 4-5 and 7-8). Those details cannot be
attributed to the paper without qualification.

## What the reference repository proves

The closest paper-shaped implementation is
[`train_model_classific.py`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py):
it uses a 600-second context and 10/50/200-block rolling windows
([lines 33-57](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L33-L57)),
consumes precomputed `minBlock` and `minBaseFee` targets
([lines 68-164](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L68-L164)),
implements the three named two-head model families
([lines 259-476](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L259-L476)),
and trains weighted cross-entropy plus Smooth L1 with AdamW and early stopping
([lines 478-595](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L478-L595)).

The repository is not a complete executable specification of the paper. Its committed raw
CSV files omit `minBlock` and `minBaseFee`, while `train_model_classific.py` requires separate
label-bearing train/validation/test files that are absent from the commit
([tree](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/tree/bcf80b92877941e3b05a7dc5138560ffe41df27e),
[required inputs](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L599-L609)).
No target generator is committed, so the reference cannot prove which physical rows belong
to a target window or how ties are resolved.

The three training scripts also preserve incompatible experiments: `train_model.py` regresses
the block offset, `train_model2.py` adds a third elapsed-time head, and
`train_model_classific.py` classifies the offset with two heads
([`train_model.py`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model.py#L323-L399),
[`train_model2.py`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model2.py#L230-L252),
[`train_model_classific.py`](https://github.com/UniBO-PRISMLab/ICDCS-Model-Training/blob/bcf80b92877941e3b05a7dc5138560ffe41df27e/train_model_classific.py#L259-L360)).
The paper resolves the high-level choice in favor of offset classification plus scalar-fee
regression, but neither source supplies a complete reproducibility oracle.

## Evidence for this project's relationship

The pre-break implementation at the recorded repository commit calls itself a "Practical
reproduction of the SPICE temporal module baseline" in
[`pyproject.toml`](../../../pyproject.toml#L5-L14). It has clear lineage
to the paper experiment: the same three model-family names and two output heads
([model-family guide](../../../src/spice/modeling/families/IMPLEMENTATIONS.md#output-heads)),
the same weighted classification plus Smooth-L1 form
([loss](../../../src/spice/prediction/families/min_block_fee_multitask/loss.py#L12-L40)),
the same 600/36-second default
([problem config](../../../src/spice/conf/problem/current_row_nominal.yaml)), and the same
two-hour/50-repetition/`0.05/s` replay protocol
([evaluator config](../../../src/spice/conf/evaluator/poisson_replay.yaml)).

An exact or full reproduction claim is not established by that lineage. The paper's
unqualified SPICE includes spatial routing and distributed reputation, while this repository
describes a temporal fee-timing pipeline
([README](../../../README.md#L1-L5)). Its current offline compiler includes the anchor row in
the candidate set
([compiler](../../../src/spice/temporal/compilers/observed_time_window.py#L352-L364)), whereas
the paper describes a future min-block and a next-block baseline; the recorded serving code
separately maps offset zero to the next block
([serving](../../../src/spice/serving/inference.py#L82-L104)). The project also adds acquisition,
artifact storage, CLI workflows, Optuna tuning, remote execution, and serving beyond the
paper's specified temporal experiment
([README](../../../README.md#L67-L125),
[tuning](../../../src/spice/modeling/tuning_execution.py#L201-L228)).

The evidence therefore supports three bounded statements, without selecting final wording:

- **Full SPICE reproduction** is unsupported: the named paper system has broader modules.
- **Exact temporal-module reproduction** is unsupported by the available artifacts: key paper
  semantics are unspecified, the reference commit is incomplete, and current behavior has
  material divergences and extensions.
- **Paper-temporal lineage, reimplementation, or inspiration** is supported. **Extension** is
  supported for named project additions, but does not by itself claim reproduced scientific
  results.

Any final attribution can remain precise by identifying the paper by exact title, qualifying
the source as its temporal optimization/module, naming concrete reproduced elements, and
separately naming project-owned extensions. Exact author names require a non-anonymous
primary bibliographic source that is not present here.
