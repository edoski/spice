# Concrete Dataset Builders

Dataset builders decide which temporal samples become train, validation, test, and inference examples. They also own builder-specific runtime metadata that must be reused when evaluating a persisted artifact.

## Mental Model

The temporal compiler creates all valid samples. A dataset builder selects and splits those samples.

```text
canonical rows
  -> feature contract
  -> problem contract
  -> compiled problem store
  -> dataset builder
  -> train/validation/test sample indices
```

The builder must preserve temporal ordering. Random train/test splitting would leak future data into training.

## `standard_temporal`

`standard_temporal` builds the full feature/problem store first, then selects the last `sample_count` valid samples.

Training flow:

```text
sort rows by block_number
  -> compile feature matrix
  -> compile problem store
  -> take tail valid samples
  -> chronological split
  -> fit scaler on train windows
```

The split is chronological over selected samples. Earlier samples train the model; later samples validate and test it.

Inference flow concatenates sorted history and optional evaluation rows, rebuilds the delay store from persisted compiler metadata, and filters anchors to the requested evaluation timestamp window.

## `fixed_context_temporal`

`fixed_context_temporal` derives a fixed sequence length from training data and stores it in runtime metadata.

Training preparation:

```text
sort by timestamp
  -> dedupe block_number
  -> sort by block_number
  -> tail raw rows by sample_count
  -> compile feature/problem store
  -> derive sequence length from train segment
```

Sequence length:

```text
median_dt = median positive timestamp delta in train segment
raw_length = round(lookback_seconds / median_dt)
sequence_length = clip(raw_length, min_sequence_length, max_sequence_length)
```

The builder then applies fixed context length to samples. Runtime metadata stores sequence length, median delta, row bounds, and compiler metadata. Inference requires this metadata and reuses the trained sequence length.

## Comparison

| Builder | Selection unit | Context length | Runtime metadata |
| --- | --- | --- | --- |
| `standard_temporal` | Tail valid samples | Variable by compiler geometry | Compiler metadata. |
| `fixed_context_temporal` | Tail raw rows before compile | Fixed from train median delta | Sequence length plus compiler metadata. |

## Scaler Ownership

Both builders fit input normalization on training windows only. The scaler is persisted in the artifact and reused at inference.

```text
train indices
  -> scaler fit
  -> transform all splits with same scaler
```

## Inference Dataset Construction

Inference must recreate the same sample geometry used during training. The artifact supplies builder runtime metadata and compiler runtime metadata. The requested delay can be shorter than the trained max delay but cannot exceed it.

## Failure Modes

| Failure | Meaning |
| --- | --- |
| Too few valid samples | Corpus/history does not satisfy requested sample count. |
| Empty train/validation/test split | Split fractions or sample count produce no rows. |
| No positive timestamp deltas | Fixed-context length cannot be derived. |
| Missing runtime metadata | Persisted artifact cannot recreate inference geometry. |
| Delay exceeds trained capability | Evaluation asks for unsupported action horizon. |

## Extension Pattern

A new builder should own all sample selection and runtime metadata for its strategy. Model families should receive only batch tensors, not builder-specific logic.

