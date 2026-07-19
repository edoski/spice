# Corpus Acquisition

FABLE (Fee Analysis through Blockchain Learning and Estimation) exposes one acquisition interface: `acquire_corpus(request, *, storage_root, rpc_url, poa)`. It turns one exact `CorpusRequest` into one finalized, canonical Corpus. Transport, resumable work, validation, finality, and publication stay behind that call.

## Contract

The request fixes a UUIDv4, chain ID, and inclusive first/last block. Acquisition publishes to an initially absent destination under the explicit `storage_root`; `rpc_url` and `poa` stay at the invocation boundary.

The completed object contains:

```text
corpora/<corpus_id>/
  corpus.json
  blocks.parquet
```

`corpus.json` stores the exact request and one finalized anchor. `blocks.parquet` stores the requested contiguous rows in block-number order with the exact seven-column canonical schema documented in the [reference](../../../docs/reference.md#corpus-object).

## Hidden resumable prefix

Acquisition works in `corpora/.<corpus_id>/`. A request JSON binds that scratch directory to one request. Complete deterministic checkpoint chunks cover at most 4,096 consecutive blocks, and the chunk list must form an exact prefix from the requested first block. Scratch validation enforces the request binding, expected filenames, prefix continuity, complete chunks, schema, nonnull domains, and parent links.

The scratch prefix records owner-local request binding and checkpoint progress. The completed Corpus directory is the published interface.

## Ordered ordinary reads

The RPC endpoint's chain ID must equal the request. Within a checkpoint, acquisition issues ordinary `eth_getBlockByNumber` reads in batches of four and consumes results in requested-number order. Every block must provide:

- its requested number and normalized block/parent hashes;
- a nonnegative, nondecreasing timestamp;
- positive base fee and gas limit;
- gas used in `[0, gas_limit]`;
- a transaction sequence whose length becomes `tx_count`.

Parent hashes must link across every read and checkpoint boundary. Rows enter the canonical object after all block facts pass validation.

## Finality proof

After the exact range is present, acquisition reads the provider's `finalized` tag. The finalized height must not precede the requested last block. If it is later, numbered headers must prove that the staged last block is its ancestor. The tagged anchor is then reread by number; number, hash, and parent hash must match the tagged response.

Block and parent hashes are proof-only acquisition facts. The completed parquet drops them. The finalized anchor keeps only its number and normalized hash.

## Publication

Checkpoint rows stream into one canonical parquet file. The exact Corpus candidate is reloaded and validated for schema, nonnull domains, row count, requested endpoints, contiguity, chain ID, timestamp order, and finalized coverage. Publication then removes checkpoint metadata and renames the hidden sibling to the canonical directory.
