# Feature Families Architecture

## Purpose

`features.families` owns concrete feature-family implementations behind the generic feature contract.

## Theory

Feature families are the correct place to encode "what could be known when." For example, same-block and lagged-block features can use similar raw data but represent different information assumptions.

## Invariants

Each family should expose a stable id, explicit feature names, and deterministic computation. Implementation fingerprints should change when feature behavior changes. Families may share helper functions, but they should not share hidden mutable state.

## Extension Points

Create a new family when the information set or calculation style changes. Extend an existing family when adding columns under the same information semantics.

## Family Contract Shape

```text
family id
  -> available feature names
  -> prerequisites
  -> compute function
  -> implementation fingerprint sources
```

## Beginner Context

Feature engineering is not just arithmetic. It defines the input space the model is allowed to learn from. Two features with similar names may encode different assumptions about timing. The family boundary keeps those assumptions grouped and documented.

## Shared Helpers

Shared helpers should implement neutral calculations, not hidden family policy. If a helper changes what information is available, it belongs in a specific family or must be reflected in each using family's fingerprint.
