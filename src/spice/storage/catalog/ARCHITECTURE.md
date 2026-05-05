# Storage Catalog Architecture

## Purpose

`storage.catalog` contains searchable record models, relational catalog schema, private root-kind dispatch metadata, typed catalog read/write operations, and remote record codecs.

## Theory

The catalog is an index, not the source of truth. Root-local SQLite state owns provenance and runtime state. The catalog lets operators find roots by selectors without scanning every manifest for every command.

## Invariants

Catalog rows point to root paths and state DB paths. Reindexing reads root-local state and upserts catalog rows. Upserts must not rewrite `created_at`. Deleting catalog rows must be coordinated with root deletion in `storage.lifecycle`.

Private root-kind metadata names the table, primary key field, typed record, path fields, nullable fields, parent directory, and default ordering for each catalog root kind. Callers use `catalog.index` for list/resolve/upsert/reindex operations and `catalog.codecs` for remote record envelopes; they do not use registry specs directly.

## Extension Points

Add catalog columns only for stable selector/search fields. Do not store large runtime summaries here; keep those in root-local state.

## Catalog Flow

```text
root-local state DB
        |
        v
catalog record materializer
        |
        v
private root-kind dispatch
        |
        v
catalog record
        |
        v
selector queries
```

## Table Shape

```text
dataset_index   dataset_id, dataset_name, chain_name, root paths, timestamps
study_index     study_id, dataset/model/problem selectors, root paths, timestamps
artifact_index  artifact_id, dataset/model/problem/variant selectors, root paths, timestamps
```

Catalog records are intentionally flat. Flat rows make selector queries simple and make CLI output predictable.

## Timestamp Rule

`created_at` means first catalog insertion time. `updated_at` means latest upsert time. Reindexing or refreshing can update `updated_at`, but it must not rewrite original creation time for the same primary key.
