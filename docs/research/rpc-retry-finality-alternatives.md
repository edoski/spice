# RPC retry ownership and acquisition finality alternatives

## Decision

Use bounded ordinary `AsyncWeb3.eth.get_block(number, False)` calls. Configure the public `AsyncHTTPProvider` retry mechanism once; do not subclass its batch transport and do not re-retry the same transport failure in acquisition. Acquisition owns a bounded concurrency semaphore, exact-number validation, ordered persistence, cancellation, and a single terminal error. The provider owns retryable transport exceptions, attempt count, and exponential backoff.

For the thesis corpus, acquire only a fixed historical range whose upper bound is below a declared per-chain confirmation depth at planning time. Persist the chain id, planned head number/hash, final included height, and finality policy in `CorpusDefinition`/the corpus manifest. Do not treat `latest` as final and do not claim one confirmation count has universal finality semantics across the supported chains.

This is the smallest reproducible route. It deletes custom batch retry, adaptive batch splitting, adaptive concurrency recovery, and their counters. Those mechanisms are provider-tuning machinery, not thesis evidence.

## Current ownership and cost

`src/spice/acquisition/rpc/transport.py` subclasses `AsyncHTTPProvider` only to retry a JSON-RPC batch. Ordinary requests already use Web3.py's configured retry loop, but `make_batch_request` bypasses it. `src/spice/acquisition/pull.py` then retries a failed range up to 32 times, reduces concurrency after transient failures, restores it after 64 successes, and splits batches after size failures. `BlockRpcClient` maps a broad collection of transport and text-matched provider failures into that outer retry.

With the shipped provider values (five attempts), a repeatedly failing batch can issue up to `32 × 5 = 160` HTTP posts before terminal failure, plus each split child's attempts. The scheduler's attempt counter is inherited by split children, but it still makes the total request budget difficult to read from configuration. Cancellation also crosses two independent retry owners.

The public Web3.py source shows why the custom subclass exists: ordinary `make_request` checks the method allowlist and retries configured exception classes with exponential backoff, while `make_batch_request` directly posts once. It also sorts a successful batch response by response id. This means a batch override is necessary only if batching itself remains a requirement; it is not a general missing retry capability. [AsyncHTTPProvider v7.15.0 source](https://github.com/ApeWorX/web3.py/blob/v7.15.0/web3/providers/rpc/async_rpc.py) and [retry configuration v7.15.0 source](https://github.com/ApeWorX/web3.py/blob/v7.15.0/web3/providers/rpc/utils.py).

The documented `AsyncHTTPProvider` accepts `exception_retry_configuration`; `None` disables it. The configuration defaults to five retries and a 0.125 backoff factor; its allowlist includes `eth_getBlockByNumber`. [Web3.py provider docs](https://web3py.readthedocs.io/en/stable/providers.html) and [v7.15.0 allowlist/configuration](https://github.com/ApeWorX/web3.py/blob/v7.15.0/web3/providers/rpc/utils.py).

## Real alternatives

| Alternative | Retry owner | Acquisition owner | Finality result | Thesis fit |
|---|---|---|---|---|
| Keep custom JSON-RPC batches | custom batch provider, then outer range scheduler | adaptive size/concurrency, splits, ordering, counters | must be added separately | Reject: two retry owners and a large policy surface for no stated thesis question. |
| Ordinary calls plus provider retry | `AsyncHTTPProvider` only, for configured transport exceptions and allowlisted reads | bounded concurrency, number/order validation, persistence, cancellation | fixed range below declared depth | Choose: one retry budget, public interface, deterministic fixture seam. |
| Ordinary calls plus acquisition retry | acquisition only | retry classification/backoff plus all scheduling | fixed range below declared depth | Reject: duplicates a maintained client facility and requires custom exception taxonomy. |
| Read `safe`/`finalized` tags as corpus boundary | provider retry | ordinary calls after resolving a tag | chain/client-specific guarantee | Reject as cross-chain default: useful only when each selected network and endpoint is explicitly verified to support the tag. |

The chosen module should expose one deep interface: acquire an already-planned inclusive/exclusive block range and either write every validated row in numeric order or fail. Callers need not know retries, semaphore details, response ordering, or HTTP exceptions. A fake ordinary-call adapter gives a deterministic fixture seam without a live provider probe.

## Finality and reorganizations

Ethereum JSON-RPC distinguishes `latest` (most recently proposed), `safe`, and `finalized`; `eth_getBlockByNumber` accepts these tags. [Ethereum JSON-RPC reference](https://ethereum.org/developers/docs/apis/json-rpc/). Ethereum's own application-layer guidance says reorgs at `latest` are expected, a `safe` head can still reorg under major latency/attack conditions, and finalized is the stronger substitute for PoW confirmations. [Ethereum Foundation finality guidance](https://blog.ethereum.org/2021/11/29/how-the-merge-impacts-app-layer).

That establishes the distinction, not a portable contract for Polygon, Avalanche, or every hosted endpoint. Therefore `CorpusDefinition` should record a chain-specific *acquisition finality policy*:

```text
chain_id; planning_head_number; planning_head_hash; confirmation_depth;
included_end_exclusive = planning_head_number - confirmation_depth + 1;
finality_source = "depth" | "verified-finalized-tag";
provider reference and retrieval time
```

For this bounded historical corpus, depth is the default because it remains auditable even where tag support differs. The exact depth is an owner-approved chain value, not a protocol claim. If a later decision elects a verified `finalized` tag for a particular Ethereum endpoint, record that exact tag and endpoint capability; do not silently substitute it for other chains.

After retrieval, validate contiguous numbers and verify each row's block hash and parent-hash linkage if those fields are retained. A number-only check cannot detect a reorganization that occurs during a long pull. Re-read the planning anchor by number and hash before sealing the manifest; on mismatch, discard the disposable pull and re-plan. This is one finite integrity check, not a live reorg monitor.

## Red-team

The chosen route is not "resilient" in the generic sense. It deliberately does not retry HTTP 429/5xx responses unless the public provider exposes them as configured exceptions, and it does not adapt to an endpoint's undocumented batch limits. That is correct only because the deliverable is a reproducible offline thesis corpus: a terminal error is evidence that the chosen endpoint/settings cannot produce the declared corpus, not an invitation to hide the condition with another controller.

Ordinary calls increase request count. Retain a small explicit concurrency value only after a deterministic fixture test and one safe representative read-only probe; no autotuning. If the provider cannot complete the fixed corpus within an owner-approved materiality tolerance, change the fixed configuration or provider and record it, rather than introduce batch/split/recovery machinery.

`eth_feeHistory` remains a separate ordinary RPC call and must use the same final numerical range. Its response must be checked against the requested oldest block and row count, as current code already does. It must not use `latest` while block rows use a sealed range.

## Sources

All external claims above use primary project or protocol-owner sources:

- [Web3.py provider documentation](https://web3py.readthedocs.io/en/stable/providers.html)
- [Web3.py v7.15.0 AsyncHTTPProvider implementation](https://github.com/ApeWorX/web3.py/blob/v7.15.0/web3/providers/rpc/async_rpc.py)
- [Web3.py v7.15.0 retry configuration and allowlist](https://github.com/ApeWorX/web3.py/blob/v7.15.0/web3/providers/rpc/utils.py)
- [Ethereum JSON-RPC reference](https://ethereum.org/developers/docs/apis/json-rpc/)
- [Ethereum Foundation application-layer finality guidance](https://blog.ethereum.org/2021/11/29/how-the-merge-impacts-app-layer)
