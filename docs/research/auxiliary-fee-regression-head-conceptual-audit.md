# Auxiliary fee-regression head conceptual audit

Date: 2026-07-12

Status: bounded research evidence only. Edo has fixed retention of the auxiliary
fee-regression head. This report does not reopen that decision or choose the target
transform, loss, weight, checkpoint rule, architecture, or serving use.

Scope: compare the current SPICE implementation, `ICDCS_2026.pdf`, and the messy
`ICDCS-Model-Training` repository. Each is treated as a candidate, not authority. The
approved comparison geometry is the closed-parent origin `h`, exactly `K` actions
`k=0...K-1`, and targets `h+1...h+K`; `k=0` means act now for `h+1`
(`docs/research/issue-48-temporal-evaluation/decision-contract.md:26-71`). The required
diagnostics include frozen-checkpoint regression loss, log-fee MAE/MSE, and
inverse-transformed base-fee-per-gas MAE, but do not infer their transform, loss,
weight, inversion, checkpoint, or architecture (`decision-contract.md:103-165`).

Citation roots: SPICE paths are relative to `/Users/edo/dev/python/spice`; unprefixed
paper-repository paths are relative to `/Users/edo/dev/python/ICDCS-Model-Training`.
Paper page references are to
`/Users/edo/Documents/Obsidian/the-vault/university/Thesis/ICDCS_2026.pdf`.

## Finding

SPICE already contains the cleanest structural implementation: one scalar linear-output
MLP head on the shared representation, a train-only target transform, a multitask loss,
and log-space diagnostics. Its present numerical choices closely match the coherent
classification branch of the paper repository, but that match is evidence of lineage,
not independent justification.

The reusable concept is narrower than either codebase: predict the hindsight minimum fee
over the **same approved `h+1...h+K` action set** as the offset label; optionally transform
and scale it using training-only fitted state; train one simple scalar auxiliary head;
and score the frozen output in loss, log, and chain-native spaces. Do not copy either
repository's old target geometry, minibatch loss reducer, inferred horizon width, or
notebook evaluation path.

## Exact comparison

| Concern | Current SPICE | Paper | Paper repository |
| --- | --- | --- | --- |
| Raw target | Canonical fees are `ln(max(base_fee_per_gas, 1))`. The target is the smallest reachable logged fee and its first `argmin` offset (`src/spice/features/core.py:299-324`; `src/spice/prediction/families/min_block_fee_multitask/batch.py:13-35`). | At time `t`, observe history and identify a future `min-block`; estimate only its base fee (Sec. IV-A, PDF p. 5). It gives no executable target-index or tie rule. | The coherent branch consumes precomputed `minBaseFee` and `minBlock`, then applies `log1p(minBaseFee)` (`/Users/edo/dev/python/ICDCS-Model-Training/train_model_classific.py:68-90,159-164`). Label construction is absent; committed raw CSVs do not contain either target (`dataset/eth_block_data.csv:1`). |
| Target geometry | The timestamp compiler currently starts candidates at the anchor row, so an offline target can include `h` (`src/spice/temporal/compilers/observed_time_window.py:352-363`). | Calls the min-block future and describes the next `M` seconds (Sec. IV-A, PDF p. 5), but does not formalize block indices. | Sequences and targets end at the same row `t` (`train_model_classific.py:218-241`). A notebook maps offset `k` to `row+k`, so `k=0` is the same row (`plot.ipynb:1316-1327`). Exact CSV-generation semantics cannot be recovered. |
| Transform and fitted state | Training-only mean and population standard deviation of logged targets, with `1e-8` added to the standard deviation; the head predicts the resulting z-score (`src/spice/prediction/families/min_block_fee_multitask/__init__.py:34-51`; `loss.py:29-39`). | Says fee-related variables use a logarithmic scale and features use train-split standardization (Sec. VI-A, PDF p. 8). It does not state `log` versus `log1p`, target standardization, units, epsilon, clipping, or inversion. | Train-only mean/std z-score with `1e-8`; its saved payload includes those statistics (`train_model_classific.py:174-215,593-595`). Older branches instead use train-range min-max scaling (`train_model.py:119-175`; `train_model2.py:121-186`). |
| Output head | Independent `Linear -> GELU -> Dropout -> Linear(1)` head, with no output activation (`src/spice/modeling/families/_heads.py:12-57`; `src/spice/prediction/families/min_block_fee_multitask/outputs.py:9-20`). | Two task-specific MLPs: offset logits and scalar fee (Sec. VI-A, PDF pp. 7-8). Layer sizes and output constraints are absent. | Same two-layer scalar MLP pattern in the coherent Transformer, LSTM, and hybrid implementations (`train_model_classific.py:259-296,328-360,442-476`). |
| Regression loss | Default mean Smooth L1 on target z-scores. Total batch loss is weighted CE `+ 0.5 *` regression loss (`src/spice/prediction/families/min_block_fee_multitask/loss.py:12-40`). PyTorch's default is `beta=1` and mean reduction, so the quadratic/linear transition is one fitted target standard deviation ([PyTorch SmoothL1Loss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.modules.loss.SmoothL1Loss.html)). | Specifies `alpha * L_block + beta * L_fee`, inverse-frequency weighted cross-entropy, and Smooth L1 (Sec. VI-A, PDF p. 8). It gives neither coefficient nor Smooth L1/reducer details. | Coherent branch uses `alpha=1`, `beta=0.5`, weighted CE, and default Smooth L1 on z-scores (`train_model_classific.py:32-57,480-516,563-566`). Conflicting branches use `0.4/0.6` Smooth L1 or three equal-weight losses with fee MSE (`train_model.py:648-676`; `train_model2.py:656-688`). |
| Checkpoint | Validation `total_loss` is the fixed selection metric. A cloned model state is retained on improvement; configurable `min_delta` and patience stop fitting (`src/spice/modeling/_fit_policy.py:15,92-134,199-210`; `src/spice/modeling/training_runner.py:113-117`). | Monitors validation loss with early stopping, then evaluates test once (Sec. VI-A, PDF p. 8). It gives no exact selection, delta, patience, or restored-state rule. | Coherent branch minimizes combined validation loss, uses patience 8 and any strict improvement, clones the state, then restores it (`train_model_classific.py:43-57,568-595`). Older branches retain a live `state_dict` rather than a clone and can fail to restore the true best epoch (`train_model.py:688-705`; `train_model2.py:700-716`). |
| MAE/MSE | Denormalizes z-scores back to logged fee and accumulates `log_fee_mae` and `log_fee_mse` over samples (`src/spice/prediction/families/min_block_fee_multitask/metrics.py:133-164,168-207,235-248`). It does not exponentiate or report chain-native fee MAE; the final runtime summary persists only validation/test total loss (`src/spice/modeling/results.py:143-151`). | Reports average total loss and offset accuracy only (Sec. VI-A, PDF p. 8). No regression metric or inverse-space decoding is specified. | Training script reports combined loss and offset accuracy only (`train_model_classific.py:573-591`). A notebook separately computes log-space MAE/MSE after z-score inversion, then raw-space MAE/MSE after `expm1` (`testchain2.ipynb:1252-1256,1320-1344`). |
| Evaluation and serving decode | Action decoding masks and argmaxes offset logits only; the fee output is ignored by evaluation and serving (`src/spice/prediction/families/min_block_fee_multitask/__init__.py:71-84`; `src/spice/modeling/scoring.py:119-152`; `src/spice/serving/inference.py:74-105`). | Says the transaction is scheduled at the predicted min-block, but never gives the scalar prediction an independent decision rule (Sec. IV-A, PDF p. 5). | Notebook action decode is logits argmax; fee decode is `z * sd + mean`, then `expm1` (`testchain2.ipynb:1237-1256,1326-1328`). There is no production serving path. |
| Artifact decoding state | Final artifacts persist manifest, input scaler, and model weights, but not fee-target mean/std (`src/spice/modeling/results.py:66-88`; `src/spice/modeling/artifacts.py:22-25,62-102`). Regression metrics work during the training process because the state remains in memory (`src/spice/modeling/persisted_training.py:93-124`). A later loaded artifact cannot reproduce log/raw fee decoding. | No artifact format is specified. | Coherent checkpoint stores weights, preprocessing stats, and config together (`train_model_classific.py:593-595`). This concept is useful even though the surrounding format is not. |

## Confirmed mismatches and defects

The first repair is semantic, not numerical. Current offline SPICE can include anchor `h`
in the minimum, while current serving interprets selected offset `k` as broadcast after
`h+k` for intended target `h+k+1` (`src/spice/serving/inference.py:82-105`). The paper
repository also uses same-row `k=0` evidence. Neither matches the approved
`h+1...h+K` target set. Both the classification label and fee minimum must come from one
shared fixed-K target construction; copying an existing scalar transform first would
preserve the off-by-one.

The reference classifier does not implement approved fixed K. It sets `K=max(training
offset)`, creates `K+1` classes, and clips validation/testing labels into that inferred
range (`train_model_classific.py:196-204,539-547`). Its driver trains seconds-specific
12/24/36 datasets (`train_model_classific.py:598-608`). This changes action width by
chain/cadence, silently relabels unsupported outcomes, and conflicts with exact K-wide
heads and common K conditions.

Both coherent implementations inherit the same checkpoint-scoring defect. Weighted
cross-entropy with default mean reduction divides by the sum of target-class weights,
not batch size ([PyTorch CrossEntropyLoss](https://docs.pytorch.org/docs/2.11/generated/torch.nn.CrossEntropyLoss.html)). SPICE then multiplies each batch mean by sample count
before epoch aggregation (`src/spice/prediction/families/min_block_fee_multitask/metrics.py:168-207,235-248`);
the reference branch does the same (`train_model_classific.py:487-523`). Classification
and combined validation loss therefore depend on minibatch class composition. Exact
checkpoint choice cannot be approved on that reducer. The scalar Smooth L1 aggregation
itself is sample-correct because there is one fee element per example.

The current/reference scalar target is the hindsight minimum fee, not the fee at the
model-selected action. That is coherent for the approved auxiliary hindsight-minimum
diagnostics, but the two outputs need not describe one predicted action when the offset
is wrong. Do not label the scalar as a selected-action fee or use it for action/chain
selection without a separate owner contract.

Raw decoding also needs a declared domain rule. A linear z-score output followed by
`expm1` can produce a negative fee. The coherent notebook applies no clipping; an older
notebook contains inconsistent clipping and even double-applies transforms in one path.
Only the inverse-transform concept is reusable, not that notebook code.

## Reusable candidate bundle

- Materialize the offset label and scalar hindsight-minimum fee from the same exact
  `h+1...h+K` raw integer fee matrix. Preserve raw targets for audit and physical metrics.
- Keep a small independent scalar linear-output MLP on the shared LSTM representation.
  This matches both sources without coupling action decoding to the auxiliary output.
- Treat a monotone logarithm, a training-only fitted scalar normalization, and Smooth L1
  as coherent candidates. Their exact forms are one coupled choice: transform, target
  scale, Smooth L1 `beta`, and fee-loss weight jointly determine gradient magnitude.
- Persist the complete target transform and inverse contract with training population,
  counts, dtype/units, and content-bound provenance. Use that same frozen state for
  validation, testing, artifact reload, and any serving display.
- Compute regression loss with an exact element numerator/denominator; compute log MAE
  and MSE only after normalization inversion; compute chain-native MAE only after the
  declared nonlinear inverse. Publish eligible/condition counts for each.
- Continue decoding actions from fixed-K offset logits unless an owner later assigns a
  consumer to the scalar output. Retention as an auxiliary head does not require it to
  change serving actions.

## Do not copy

- Precomputed targets whose generator, window membership, ties, and provenance are
  absent from the repository.
- Same-row `k=0`, seconds-derived/inferred width, `K+1` notation, or validation/test label
  clipping from `train_model_classific.py`.
- The conflicting `train_model.py`/`train_model2.py` target scalers, weights, third head,
  MSE choice, or broken checkpoint capture.
- Notebook-only decoding, clipping, row lookup, and plotting as an evaluation contract.
- The numerical `0.5` coefficient as a paper requirement. It exists in current SPICE and
  the coherent reference script, but the paper leaves `alpha` and `beta` unspecified.

## Exact open owner decisions

Head existence is closed. These choices remain open and coupled:

1. Formal raw scalar target contract under fixed K: exact chain-native unit/dtype, valid
   fee domain, and whether any target clipping occurs before the deterministic transform.
2. Transform and inverse: `ln(x)`, `log1p(x)`, or another declared mapping; zero policy;
   optional target normalization; fitted population; standard-deviation convention and
   epsilon; inverse precision, clipping, and rounding.
3. Regression loss: Smooth L1 or another loss; its `beta`; exact numerator, denominator,
   and reduction; and behavior for non-finite/out-of-domain predictions.
4. Loss composition: classification coefficient, regression coefficient, whether they
   are fixed across chain/K, and how their scale remains interpretable when target
   distributions change.
5. Frozen-checkpoint rule: selection metric, reducer, improvement delta, patience/stopping,
   and the validation surface. Current combined-loss selection and `0.5` weight are
   candidates only.
6. Head architecture: shared representation tap, hidden width, dropout, bias, output
   activation/domain constraint, and whether one common pattern is fixed across K.
7. Artifact/scorer contract: persisted transform-state schema and provenance; exact
   log/raw diagnostic names, units, counts, and precision; whether the scalar remains
   internal-only or is exposed as a non-actionable serving diagnostic.
