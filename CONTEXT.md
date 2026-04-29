# Spice

Spice is a temporal fee-decision research pipeline for EVM chains. This context names the project concepts used when config selections become executable workflow configs.

## Language

**Surface**:
A named recipe that groups default config choices for one workflow family.
_Avoid_: preset, profile

**Workflow Selection**:
Unresolved workflow intent made of a surface plus optional overrides.
_Avoid_: request

**Workflow Config**:
Executable typed configuration produced by resolving a workflow selection.
_Avoid_: resolved request

**Config Group**:
A named collection of YAML specs for one kind of selectable configuration.
_Avoid_: config bucket, config folder

**Problem Spec**:
The typed temporal problem definition selected by a workflow.
_Avoid_: problem config, problem preset

**Benchmark**:
A named matrix of workflow selections used to compare experiment variants.
_Avoid_: experiment batch

**Benchmark Case**:
A benchmark subdivision that shares base selection values and dimensions.
_Avoid_: scenario

**Benchmark Step**:
One workflow action inside a benchmark case.
_Avoid_: task

**Benchmark Workflow Selection**:
One expanded workflow selection plus benchmark metadata such as run id and dependencies.
_Avoid_: benchmark row

**Benchmark Run**:
One submitted benchmark plan with local run-state files for plan, submission, collection, and ledger projection.
_Avoid_: ad hoc benchmark output folder

**Storage Selector**:
A typed query for one existing catalog record: dataset, study, or artifact.
_Avoid_: workflow selector

**Root Lifecycle**:
Validation, staging, promotion, partial commit, reindex, and delete behavior for storage roots.
_Avoid_: storage sync

**Corpus Assembly**:
Acquisition-to-corpus policy that plans block windows, materializes history/evaluation splits, writes corpus provenance, and publishes a corpus root.
_Avoid_: corpus builders

**Artifact Inference Context**:
Trusted inference inputs reconstructed from a trained artifact and an active evaluate workflow config.
_Avoid_: evaluation setup, scoring setup

**Batch Plan**:
Executable model-batch iteration plan with sample ordering, target binding, and host/device storage placement.
_Avoid_: batch source

**Training Runner**:
Fit execution module that owns runtime setup, epoch execution, objective tracking, checkpoint selection, and split metric evaluation.
_Avoid_: training loop helper

**Decoded Result ABI**:
Typed prediction output contract consumed by evaluators after model inference.
_Avoid_: logits, prediction tensor

**Objective Metric Source**:
Modeling-owned module that produces the metric set used by a policy-only objective during training.
_Avoid_: objective evaluator, objective callback

**CLI Selection Layer**:
Operator-edge module that turns explicit CLI values into workflow selections and local-or-submitted workflow command plans.
_Avoid_: CLI request builder

**Benchmark Collection Resolver**:
Benchmark module that makes one submitted evaluate result local and selects its matching evaluation summary.
_Avoid_: benchmark artifact loader

**Execution Session**:
Target-bound SSH/SLURM session for remote commands, module execution, rsync transfer, workflow submission, job following, and remote metadata lookup.
_Avoid_: execution backend

## Relationships

- A **Workflow Selection** references exactly one **Surface**.
- A **Surface** references one or more **Config Groups**.
- A **Workflow Selection** may override values from its **Surface**.
- A **Workflow Config** is produced from exactly one **Workflow Selection**.
- A **Problem Spec** can be selected by name or supplied inline by benchmark problem grids.
- A **Benchmark** contains one or more **Benchmark Cases**.
- A **Benchmark Case** contains one or more **Benchmark Steps**.
- A **Benchmark Step** expands into one or more **Benchmark Workflow Selections**.
- A **Benchmark Run** records submitted **Benchmark Workflow Selections** and collection results.
- A **Storage Selector** resolves existing persisted roots through the catalog.
- **Root Lifecycle** changes storage roots and keeps the catalog index current.
- **Corpus Assembly** consumes a block source and produces a dry-run plan or committed corpus root.
- An **Artifact Inference Context** validates a trained artifact against an evaluate **Workflow Config** and prepares model scoring inputs.
- A **Training Runner** consumes prepared training data and produces fitted model state plus runtime training metrics.
- A **Batch Plan** is built by the **Training Runner** and inference paths after runtime memory budget is known.
- A **Decoded Result ABI** is produced by a prediction contract and accepted by evaluator contracts by decoded-result id.
- An **Objective Metric Source** turns validation metrics or model-bound evaluator scoring into objective metrics for the **Training Runner**.
- The **CLI Selection Layer** builds **Workflow Selections** from operator options and resolves local-or-submitted command plans.
- A **Benchmark Collection Resolver** consumes an evaluate **Workflow Config** and an **Execution Session** to produce a collected benchmark evaluation.
- An **Execution Session** is opened for one explicit execution target and used by submission, following, remote transfer, and benchmark collection.

## Example Dialogue

> **Dev:** "Should the benchmark create temporary YAML files for every lookback window?"
> **Domain expert:** "No. The benchmark builds a **Workflow Selection** with an inline **Problem Spec**, then config resolution produces the **Workflow Config**."

## Flagged Ambiguities

- "request" previously meant unresolved workflow intent. Use **Workflow Selection** for that concept.
