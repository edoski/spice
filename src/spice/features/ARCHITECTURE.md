# Features Architecture

## Purpose

`features` turns canonical block rows into observable numeric columns. Feature code owns feature-family configs, feature contracts, feature prerequisites, feature graph fingerprints, and table execution.

Features answer: “What information is available to the model?” They should not decide labels, losses, model architecture, evaluator metrics, or storage layout.

## Flow

```text
FeatureSetConfig
  id: same_block_closed_full
  family: {id: same_block_closed}
  outputs: [...]
        |
        v
feature-family config resolution
        |
        v
compile_feature_contract()
        |
        v
CompiledFeatureContract.build_table(blocks)
        |
        v
ResolvedFeatureTable
```

The public API is the contract path. Concrete family registry lookup stays internal to the features package.

## Why Feature Prerequisites Matter

Some features require historical rows before a decision point. For example, a rolling statistic may need a lookback window. Temporal compilers and corpus coverage checks need this requirement before model training starts.

```text
feature family definitions
        |
        v
FeaturePrerequisites(history_seconds, warmup_rows)
        |
        v
coverage validation + temporal problem construction
```

If prerequisites are wrong, the model may train on examples whose required history was not actually available.

## Fingerprints

Feature graph fingerprints hash feature-family identity, selected output names, and source files that define the feature graph. They do not hash output paths. This makes artifacts sensitive to feature logic changes while keeping storage location irrelevant.

```text
family id + selected feature names + implementation sources -> fingerprint
```

## Extension Points

Add a feature family when the observable columns or dependency graph changes. Add a feature output inside a family when it belongs to the same semantic family. Keep shared helpers neutral: if a helper encodes hidden policy that affects available information, it belongs in the concrete family or must be part of the fingerprinted implementation.
