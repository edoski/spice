# Acquisition Architecture

## Purpose

`acquisition` owns data collection mechanics. It turns an acquisition plan into canonical block rows that the rest of the system can treat as raw corpus data.

## Theory

Training quality begins with data provenance. Raw acquisition must keep enough metadata to answer: which chain, which provider, which time windows, which blocks, and which validation status produced this corpus.

## Boundaries

Acquisition does not define ML targets, train models, or score predictions. It gathers canonical data and reports runtime facts. The acquire workflow decides when to commit acquired data into storage.

## Invariants

Raw block rows must be canonical before persistence. Provider-specific transport details stay in provider-specific modules. Storage commit mechanics stay in storage staging primitives and the acquire workflow.

## Extension Points

Add a new acquisition backend by keeping transport, provider client, and canonical row conversion separate. Preserve the same corpus contract so features and temporal compilers remain unchanged.

## Data Flow

```text
AcquireConfig
    |
    v
provider/chain endpoint
    |
    v
block range plans
    |
    v
backend fetch
    |
    v
canonical block rows
    |
    v
corpus builders and storage commit
```

## Beginner Context

The model eventually trains on examples, but examples are only as trustworthy as the raw data underneath them. Acquisition is where external uncertainty enters the system: RPC latency, provider failures, missing blocks, and chain-specific payload shape. That uncertainty should be resolved before feature construction starts.

## Separation From Workflows

The acquisition package should answer "how do I fetch and canonicalize blocks?" The acquire workflow answers "which windows do I fetch, how do I validate them, and how do I commit the result?" This keeps backend mechanics reusable.
