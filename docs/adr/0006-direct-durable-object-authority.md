# ADR 0006: Direct Durable Object Authority

## Status

Accepted.

## Context

FABLE (Fee Analysis through Blockchain Learning and Estimation) objects must preserve enough authority to interpret corpora, studies, artifacts, and evaluations directly. Their requests and associations contain that authority at the canonical object address.

## Decision

UUIDv4 values identify instances. Each completed object owns its exact typed request once at a direct canonical address:

- `corpora/<corpus_id>/corpus.json` and `blocks.parquet`;
- `studies/<study_id>.json`;
- `artifacts/<artifact_id>.ckpt`;
- `evaluations/<evaluation_id>/evaluation.json` and `observations.parquet`.

Typed requests, embedded associations, and the selected Study result index plus exact Method establish meaning. Completed objects are loaded directly and validated against the requested UUID and association.

A completed evaluation owns its exact `EvaluateRequest` plus sufficient canonical prediction and outcome observations. Loading it validates the request ID and window together with the observation schema and self-contained facts. Transient evaluation reduction is recomputed directly from that completed evaluation object; Artifact and Corpus availability is not required after evaluation publication. Selection remains recomputed from its canonical Study object.

Owner-local hidden siblings support resumable work and publish canonical objects by direct rename.

## Consequences

Callers supply the typed UUID they intend to use. Durable schemas stay focused, and each transient operation depends only on the completed object that owns its required authority.
