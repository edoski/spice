# Issue 33 — serving deployment contract

Edo approved this complete contract on 2026-07-14. It specifies the clean thesis
baseline only. It authorizes no production, configuration, test, data, storage,
mobile, server, network, or sibling-issue implementation.

## Physical mobile inference demo

The thesis deliverable includes one physical Expo phone using FastAPI/Uvicorn on
one Mac over the already-approved owner-controlled private LAN or personal
hotspot. The phone selects a chain and `K`, sends one inference request, and
displays the typed response. It never loads a model, talks to RPC, prepares the
`C=200` context, selects a head, or performs inference.

The closed serving choices are:

- Ethereum mainnet, chain ID 1;
- Polygon mainnet, chain ID 137;
- Avalanche mainnet, chain ID 43114;
- `K in {2, 3, 4, 5}` using separately trained matching artifacts from the
  selected model family.

The Python serving module contains one checked-in literal mapping from the
closed `Chain` and `K` types to exactly twelve final artifact UUIDs. It resolves
each checkpoint directly as `artifacts/<uuid>.ckpt`. Artifact UUIDs remain
internal and replacing one requires an explicit code edit. There is no separate
mapping file or schema, runtime artifact variable, catalog, discovery, scan,
latest/best lookup, registry, fallback, alias, or compatibility path.

Sepolia, Sepolia-specific acquisition, and Sepolia-specific training are not
part of the final demo.

## Provider and artifact trust

The demo assumes the approved deployed artifact regime remains applicable. It
trusts the configured provider and Web3 for response decoding and block data,
accepts provider, reorganization, and snapshot limitations, and makes no
stronger canonicality or finality claim.

The only live-network guard is Web3's ordinary numeric chain-ID result checked
against the selected chain. Add no regime check, fork table, activation
scheduler, compatibility service, operator confirmation record, hash or
ancestry proof, finality check, continuity framework, or future-fork machinery.

## One request and response

The server exposes one POST inference endpoint. Its strict request is:

```text
chain: ethereum | polygon | avalanche
K: 2 | 3 | 4 | 5
```

Its strict response is exactly:

```text
head_block
selected_action_k
target_block
```

The server computes `target_block = head_block + 1 + selected_action_k`.
The request already owns the selected chain and `K`; chain ID and artifact UUID
remain internal.

Add no auxiliary fee forecast, scores, logits, confidence, savings, request ID,
head hash, timestamp, TTL, support bounds, seconds estimate, broadcast field,
model metadata, health route, model route, analytics route, or observation
route. Ordinary HTTP/Pydantic errors stop the call and the phone displays the
error.

## Stateless per-call lifecycle

Each request performs this server-owned sequence:

1. select the internal `(chain, K)` artifact UUID;
2. load the native Lightning checkpoint;
3. use the configured Web3 client and check its numeric chain ID;
4. freeze one provider head;
5. obtain the ordinary `C=200` context and perform only the structural work
   required to build the model tensor;
6. infer, decode `selected_action_k`, compute `target_block`, and return.

A package, checkpoint, provider, fetch, preparation, or inference error stops
only that request. There is no cross-request application state.

FastAPI lifespan owns only three Web3 clients and closes them at shutdown.
Startup requires the storage-root path and three RPC URLs, constructs the
clients, and begins serving. It performs no provider probe, chain check,
checkpoint load, all-artifact scan, model warmup, or readiness check. A
successful inference is the only readiness signal.

Add no cache, preload, store, history, counter, lock, offload policy, state
machine, retry loop, background task, cleanup worker, admission control,
multiwriter or multiworker claim, `/health` route, or readiness state. If
measured checkpoint latency later harms the demo, address it through a fresh
narrow owner decision rather than a dormant cache seam.

## Deleted serving machinery

Delete the mobile wallet and SecureStore key, signing, funds and gas handling,
block scheduler, broadcast, native transfer, receipt handling, request binding,
pending/observed lifecycle, savings accounting, analytics UI and storage,
serving SQLite, unused demo contract and address, and obsolete API routes and
schemas. Manually discard the old serving SQLite file while the service is
stopped. Add no import, archive, migration, or compatibility code.

Issue 22's one-client trusted-LAN exposure and no-authentication boundary
survive. Its Sepolia, wallet, transaction, observation, and analytics clauses
are superseded for the clean serving baseline. Issue 46's `h`, `k`, and target
arithmetic survives; its Sepolia and transaction-execution clauses do not enter
serving. Issue 78's single-operator and mature-package boundary remains binding.

## Deferred live transaction submission

Live blockchain transaction submission is Wayfinder Fog only. It may graduate
only after the inference-only physical-phone demo is implemented and stable,
through a fresh issue and owner decision. That future decision must reopen
wallet and key custody, signing, funds and gas, exact block scheduling,
broadcast, failure/retry/replacement policy, receipt and observation semantics,
analytics, safety and claim boundaries, and whether submission strengthens the
thesis at all.

The clean baseline retains no dormant interface, schema field, registry, state,
compatibility route, or placeholder for that possibility.
