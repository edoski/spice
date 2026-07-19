# Evaluation

FABLE (Fee Analysis through Blockchain Learning and Estimation) separates canonical evaluation observations, transient reductions, sealed reports, and experiment-specific evidence. Explicit UUIDs and paths connect these operations.

## Canonical evaluation

`evaluate(request, storage_root, deployment)` loads the exact Corpus and native artifact, requires the artifact's source Corpus to equal the evaluation Corpus, prepares the authored validation or testing origin window with persisted state, and performs CUDA inference.

For every eligible origin it writes one ordered, nonnull observation containing the decision coordinate, target and decoded actions, scaled classification contribution, auxiliary z prediction, raw fee facts, and elapsed-time descriptions. Work is written under `evaluations/.<evaluation_id>/` and renamed to:

```text
evaluations/<evaluation_id>/
  evaluation.json
  observations.parquet
```

The JSON is exactly the `EvaluateRequest`. The parquet schema is the canonical 13-column S12 contract in the [reference](../../../docs/reference.md#s12-canonical-observations).

## One-evaluation reduction

`reduce_evaluation(storage_root, evaluation_id) -> polars.DataFrame` loads and cross-checks the request, artifact association, window, and ordered observation schema. It returns one transient 43-field row.

The reducer validates exact origin coverage, nonnull inputs, action bounds, positive fee denominators, wait bounds, finite values, and scientific identities. It reconstructs regression target and Smooth-L1 using the artifact's `TargetState` and authored loss. Economic differences begin in raw Int64 before Float64 aggregation. The sole nullable result is captured opportunity when exact total opportunity is zero.

## Derived report composition

`write_sealed_report(storage_root, evaluation_ids, destination)` accepts a nonempty, duplicate-free tuple of testing evaluation UUIDs. In caller order it joins each transient reduction with exact artifact, Corpus, window, model, experiment, and coverage context, then publishes the 62-column S15 TSV through a hidden sibling.

Top-level `experiments` owns two fixed protocols:

- `experiments.context_history.write_context_history_evidence(...)` writes the 71-column S16 context-history sensitivity TSV.
- `experiments.k5_fee_conditions.write_k5_fee_condition_evidence(...)` writes the 27-column S18 primary K=5 fee-condition TSV.

Those functions own their fixed matrices, order, regrouping, and null rules.

Exact equations and claim limits are in the [theory](../../../docs/theory.md#evaluation-estimands); exact signatures and schemas are in the [reference](../../../docs/reference.md#evaluation-api).
