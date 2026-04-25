# Concrete Corpus Builders

Corpus builders materialize history and evaluation parquet data. They reuse clean existing data when possible and download only missing ranges when that is cheaper than rebuilding.

## Range Convention

Block ranges are half-open:

```text
[start_block, end_block)
```

The start block is included. The end block is excluded. This convention avoids off-by-one ambiguity when adjacent ranges are concatenated.

## Shared Build Result

Builders report whether data was created, reused, extended, or rebuilt. The result includes the materialized path, validation report, and any partial download plans.

```text
request range
  -> inspect existing parquet
  -> validate existing range
  -> plan missing pieces
  -> pull missing blocks
  -> write chunks
  -> validate final frame
```

## History Builder

The history builder aims to cover all rows before the evaluation day that are needed for warmup and training.

Reuse rules:

| Existing data | Builder action |
| --- | --- |
| Clean, same end, starts early enough | Reuse. |
| Clean, same end, starts too late | Download prefix and extend. |
| Dirty or wrong end | Rebuild requested range. |

The end boundary matters because history should stop at the evaluation start. Adding rows after that boundary would leak evaluation-period data into training.

## Evaluation Builder

The evaluation builder materializes the evaluation day. It can reuse exact matches or splice partial overlap.

| Existing data | Builder action |
| --- | --- |
| Clean exact range | Reuse. |
| Clean overlapping range | Keep overlap, download prefix and/or suffix. |
| No useful overlap | Rebuild. |

Evaluation reuse is more flexible because the requested day is a fixed interval and partial overlap is safe when final validation proves the exact window.

## Chunk Writing

Blocks are written in chunks named with chain and block range. Chunking keeps large pulls manageable and lets validation reason about exact materialized ranges after all chunks are present.

```text
pull rows
  -> split into chunk_size groups
  -> write parquet files
  -> load combined frame for validation
```

## Validation Callback

Builders delegate block fetching to acquisition code and validation to corpus validation code. This keeps IO policy separate from RPC mechanics.

## Invariants

| Rule | Why |
| --- | --- |
| Final frame must validate cleanly. | Modeling assumes contiguous block rows. |
| History ends at evaluation start. | Prevents evaluation-day leakage. |
| Evaluation covers requested day exactly. | Replay metrics need the selected period. |
| Chunk file names encode range. | Operators can inspect storage layout. |

## Extension Pattern

A new builder should keep the same result shape and validation discipline. Change planning policy only when the final canonical range can still be proven by validation.

