# ADR 0003: Representation Seam Retained

## Status

Accepted.

## Context

Modeling currently uses one concrete Representation Adapter: `sequence_inputs`. By the usual architecture heuristic, one Adapter can mean a hypothetical Seam.

The Representation identity is durable. Study and artifact semantics persist the Representation id, and the modeling runtime depends on the Representation Interface to prepare model-input batches from a compiled problem store, execution-policy contract, and prepared Action Space.

Future Thesis and Internship 2 work may add richer temporal inputs for dynamic prediction windows, uncertainty-aware prediction, cross-chain context, or app urgency. Those changes may need new Representation Adapters even though they are not needed now.

## Decision

Keep `sequence_inputs` behind the Representation Seam. Do not collapse the Representation Interface into Batch Plan or model-family code as cleanup.

Cleanup may simplify the current `sequence_inputs` Implementation, but it must preserve the Representation Interface and persisted semantics.

Batch Plan owns loader policy and host/device storage selection. Representation owns model-input preparation from a temporal Action Space and receives only the host-memory and batch-size facts needed to decide whether to materialize host tensors.

## Consequences

Architecture reviews should not re-suggest deleting the Representation Seam solely because there is one Adapter today.

New Representation Adapters must prove they need a distinct input contract. Execution-policy, evaluator, objective, or prediction-output changes should stay in those Modules when they do not change model input representation.
