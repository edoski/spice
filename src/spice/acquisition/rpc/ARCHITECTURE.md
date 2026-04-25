# RPC Acquisition Architecture

## Purpose

`acquisition.rpc` implements JSON-RPC block retrieval. It batches block requests, controls concurrency, retries through transport rules, and canonicalizes RPC blocks.

## Theory

RPC providers are latency-bound and failure-prone. The architecture separates transport from block semantics so concurrency and provider behavior can change without changing the canonical corpus format.

## Invariants

RPC types describe provider payloads. The client and controller manage request execution. Pull logic converts fetched blocks into canonical rows. Downstream packages should not know which RPC provider produced a row.

## Extension Points

Tune batching and concurrency in acquisition config. Add provider-specific transport behavior behind the transport/client boundary, not in corpus or workflow code.

## Module Map

```text
rpc/
  types.py       JSON-RPC and block payload types
  transport.py   request transport and retry mechanics
  client.py      typed block-fetch client
  controller.py  batching and concurrency control
  pull.py        canonical block-row pull helpers
```

## RPC Flow

```text
block numbers
    |
    v
batched JSON-RPC calls
    |
    v
provider responses
    |
    v
RpcBlock objects
    |
    v
CanonicalBlockRow
```

The boundary is canonicalization. Once a row is canonical, downstream code should not care whether it came from PublicNode, another RPC endpoint, or a future backend.

## Failure Policy

Transport failures belong in transport/controller code. Data-shape failures belong in canonicalization. Workflow-level failures should mention acquisition context, not low-level HTTP details unless needed for debugging.
