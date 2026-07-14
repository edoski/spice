# Issue 43 backend-to-Expo seam prototype

Status: complete contract explicitly approved by Edo on 2026-07-14. No production, configuration,
test, dependency, data, storage, job, training, evaluation, acquisition, server, or mobile
implementation is authorized or included.

## Question and bound

Can one strict stateless inference call replace the current timed-transfer lifecycle while preserving
the approved chain/horizon selection, full two-head validation, actionable-head arithmetic, and an
honest physical-phone display?

The cheapest discriminating observation is one synthetic trace across all twelve closed `Chain × K`
choices, the depth-two stale-clock counterexample, server mismatch failures, malformed successful
model outputs, and the complete phone interaction. Budget: one local CPU process, no network, no
artifact,
and under 20 seconds. Stop when the trace proves one exact request/response and phone state need no
transfer, scheduler, receipt, wallet, persistence, analytics, finality, or auxiliary-fee field. It
must not inspect model quality or real chain data.

Run the bounded trace:

```text
uv run python docs/research/issue-43/prototype.py --all
```

Drive the interaction by hand:

```text
uv run python docs/research/issue-43/prototype.py
```

The pure seam is in `seam.py`; the terminal shell is disposable.

## Binding inputs

This prototype consumes the approved contracts without reopening them:

- Issue 33 freezes one physical Expo phone, one FastAPI Mac process, three server-owned Web3 clients,
  the internal twelve-artifact mapping, per-call checkpoint load, chain-ID check, latest provider
  head, `C=200` preparation and inference, and an exact three-field response. It deletes transaction,
  wallet, scheduling, receipt, analytics, persistence, cache, health, and readiness behavior.
- Issue 31 freezes the latest provider head as `h`, exact live context through `h`, full finite
  `MinBlockFeeOutput`, first-index argmax, and `target_block=h+1+k`. Finalized context is not a serving
  field or action clock.
- Issue 46 supplies the same `h/k/target` arithmetic. Its transaction/broadcast clauses are outside
  the inference-only serving baseline.
- Issues 23, 24, and 47 supply the full two-head task validation, every valid exact-`K` action,
  direct action arithmetic, strict artifact facts, `C=200`, and the chain-specific feature shapes.
  The auxiliary scalar is validated inside Python and never enters this API or phone display.
- Issue 48 and Issue 33 freeze serving `K={2,3,4,5}`; `K=5` is the default. There is no seconds
  conversion, dynamic mask, or research-only horizon.

The ticket body's latest/finalized/TTL/cancellation/receipt/timed-transfer scope is stale. Closed
Issue 33 supersedes it. The surviving backend-to-Expo question is only the HTTP/type/error/display
seam.

## Candidate exact contract

The prototype recommends one unversioned endpoint because this is one clean-break demo, not a public
compatibility surface:

```text
POST /inference
```

Request JSON:

```text
chain: ethereum | polygon | avalanche
K: 2 | 3 | 4 | 5
```

Success JSON, with no additional keys:

```text
head_block: non-negative integer
selected_action_k: integer in [0, K)
target_block: head_block + 1 + selected_action_k
```

The corresponding closed Expo types are:

```ts
type Chain = "ethereum" | "polygon" | "avalanche";
type Horizon = 2 | 3 | 4 | 5;
type InferenceRequest = { chain: Chain; K: Horizon };
type InferenceResponse = {
  head_block: number;
  selected_action_k: number;
  target_block: number;
};
```

Successful response handling is deliberately only:

```ts
return (await response.json()) as InferenceResponse;
```

Edo rejected both a custom runtime response parser and a generated OpenAPI client. Expo duplicates
no exact-key, safe-integer, submitted-K, or target-arithmetic validation. FastAPI/Pydantic owns the
controlled server response contract.

Python owns the chain-ID check, internal artifact choice and validation, parent snapshot, context,
full model output, decode, and target calculation. Expo owns only the selected chain/K, one loading
boolean, result or error, and rendering. The in-flight request is an ordinary local value; it is not
persisted as separate state. Expo does not recompute a target or infer meaning from the auxiliary
head.

Default selection is Ethereum and `K=5`. While the request is in flight, selectors and the button are
disabled. A successful result displays exactly `Head block`, `Selected action k`, and `Target block`.
The visible selectors supply chain and K. Changing either selector after completion clears the prior
result and error, preventing a result from being shown under a different selection. The button says
`Run inference`; no UI text says submit, transfer, wait, schedule, broadcast, receipt, fee, savings,
or confirmation.

The physical phone requires `EXPO_PUBLIC_SPICE_BACKEND_URL` for the Mac's private-LAN HTTP address.
There is no loopback fallback for the physical-phone contract, backend discovery, mobile RPC URL, or
runtime connection mode.

FastAPI/Pydantic rejects unknown fields and invalid literals through its ordinary `422` response.
Server-side package/checkpoint/provider/fetch/preparation/inference failures use FastAPI's ordinary
failed-request behavior and stop only that call. Expo performs no retry. For non-2xx responses it
shows `HTTP <status>: <trimmed response text>`; for fetch failure it shows
`Network error: <runtime message>`. The user may tap `Run inference` again manually.

## Prototype observation

The bounded trace passes all twelve requests. Each response contains only the approved three keys,
and every target is strictly later than its response head. In the depth-two counterexample,
`latest_rpc_head=1210`; the stale finalized-context `k=0` target is `1209`, while the response target
is `1211`. No finalized-context field or correction enters the API.

The trace rejects unsupported chain/K values, extra request fields, provider chain mismatch,
artifact chain/K/C mismatch, malformed logits, and nonfinite auxiliary output. Changing selection
clears the old result; selection is locked during the one in-flight call. The phone state contains
only selection, loading, result, and error.

Edo approved ordinary successful JSON decoding plus a TypeScript cast and then explicitly approved
the complete contract. No further consequential prototype choice remains.
