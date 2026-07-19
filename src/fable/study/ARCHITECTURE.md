# Study

FABLE (Fee Analysis through Blockchain Learning and Estimation) treats tuning as a bounded question over a finite typed MethodSpace. A Study contains the exact `TuneRequest` and its ordered successful results.

## Request and membership

`TuneRequest` fixes a Study UUID, Corpus UUID, `ExperimentSemantics`, and one family-specific nonempty tuple of unique Methods. Each Method is complete: architecture capacity, dropout, AdamW values, training batch size, and fit policy.

`apply_method(request, method)` requires exact membership in the request's MethodSpace, then composes one `TrainingDefinition`. `training_definition_from_method(experiment, method)` performs the same family-specific composition for a Method supplied by an authoritative association.

## Candidate run

`run_candidate(storage_root, request, method, deployment)` loads the request's Corpus, prepares training history and state, fits the exact Method through native Lightning, and retains one successful result. Candidate checkpoints stay in Study scratch; training publishes artifacts.

`RetainedResult` has four fields:

- the exact Method;
- finite complete-validation total-loss objective;
- one-based earliest selected epoch;
- one-based completed epoch count.

The selected epoch cannot exceed completed epochs, and completed epochs cannot exceed the Method maximum.

## Ordered progress and publication

Candidate success appends to `studies/.<study_id>/progress.json`. Existing progress must contain the identical request. Appends preserve caller completion order and directly replace the progress file through one hidden temporary sibling.

`publish_study(storage_root, study_id)` validates progress and renames it to `studies/<study_id>.json`, preserving completion order. An existing canonical Study is an error.

## Selected training

A selected-Study `TrainRequest` supplies the exact Study UUID and zero-based `study_result_index`. `materialize_selected_training()` loads the canonical Study, verifies Study and Corpus associations, selects that ordered row, and reconstructs its `TrainingDefinition` from the embedded experiment and Method.

The resulting native artifact embeds the same result index and Method for later loading and reporting.
