# FABLE (Fee Analysis through Blockchain Learning and Estimation) Context

This glossary defines FABLE's active domain language.

## Active glossary

**WorkflowRequest.** The strict `TrainRequest | EvaluateRequest` union used for remote workflow execution.

**UUID instance.** An identity minted for one Corpus, Study, artifact, or evaluation.

**Typed association.** An exact request/object relationship expressed by the owning schema, UUID, embedded request, or selected Study result index plus Method.

**CorpusRequest.** The exact request for one corpus UUID and its `CorpusDefinition`.

**BlockFrame.** One isolated, validated seven-column value covering an exact contiguous single-chain `CorpusDefinition`; it establishes canonical row facts and range selection, not finality or provenance.

**Corpus.** The completed request, finalized anchor, and canonical `BlockFrame` at the corpus UUID's direct address.

**TuneRequest.** The complete bounded tuning question for one Study.

**Study.** The exact TuneRequest plus its ordered `RetainedResult` list.

**RetainedResult.** One retained successful Method result containing only method, validation total loss, earliest best epoch, and completed epochs.

**TrainRequest.** The complete typed instruction for one fit, including exact input authority and scientific semantics.

**Native Lightning artifact.** A weights-only best checkpoint carrying the exact TrainRequest, fitted state, and any selected-Study association.

**EvaluateRequest.** The complete typed instruction for one explicit post-fit testing evaluation.

**Evaluation observation.** One canonical prediction row containing an origin, decoded action, and standardized natural-log minimum-fee prediction.

**Method.** One complete `ModelDefinition` and `FitMethod` choice.

**Decision origin.** The decision point immediately after closed parent block `h`.

**Closed parent.** The latest closed block `h` visible at a decision origin.

**Context.** Exactly `C` consecutive closed blocks `h-C+1 … h` selected by block number.

**Horizon.** The exact next `K` blocks `h+1 … h+K` whose complete outcomes define eligibility.

**Action.** Zero-based offset `k` selecting target block `b = h+1+k` within the horizon.

**Role.** One of training, validation, or testing. Training fits weights and data-dependent state, validation selects, and testing measures.

**ExperimentSemantics.** The training and validation windows, generic context and horizon lengths, and ordered causal features carried where an owning request needs them.
