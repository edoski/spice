# Issue 43 serving/mobile seam contract

Status: complete contract explicitly approved by Edo on 2026-07-14. This is disposable planning
evidence, not implementation.

## Scope and supersession

The clean baseline is an inference-only physical-phone demo. Closed Issue 33 supersedes the ticket
body's transaction, scheduling, TTL, cancellation, receipt, observation, analytics, finality, and
RPC-disagreement scope. Issue 43 owns only the remaining FastAPI-to-Expo request, response, error,
and display seam.

Issue 31 supplies the decision-time latest provider head `h`, live `C=200` context ending at `h`,
full finite two-head output validation, first-index argmax `k`, and
`target_block = h + 1 + k`. Issue 46 supplies the same arithmetic; its transaction path does not
enter serving. Issues 23, 24, 47, and 48 supply the task output, direct action checks, context, feature
shape, and closed serving horizons. Issue 33 supplies every provider, artifact, lifecycle, and trust
choice outside this seam.

## One HTTP operation

Expose one unversioned operation:

```text
POST /inference
```

Use strict Pydantic request and response models with unknown fields forbidden. Request JSON is
exactly:

```text
chain: ethereum | polygon | avalanche
K: 2 | 3 | 4 | 5
```

Success JSON is exactly:

```text
head_block: non-negative integer
selected_action_k: non-negative integer
target_block: non-negative integer
```

The server already knows the request K. Its `K`-wide validated model output makes
`selected_action_k` an integer in `[0,K)`, and it directly computes
`target_block = head_block + 1 + selected_action_k`. Add no response cross-field validator merely to
recheck those direct computations.

Chain ID, K, C, ordered feature and fitted states, model facts, artifact UUID, regime assumptions,
logits, auxiliary scalar, parent hash, timestamps, and provider details stay inside Python. Return no
echoed chain/K, request ID, metadata, quote, score, confidence, wait, timing, finality, or status field.

## Server authority

For each request Python performs Issue 33's fixed sequence: select the literal `(chain,K)` artifact,
load its native Lightning checkpoint, use the selected configured Web3 client, check numeric chain
ID, freeze the latest provider head, fetch and prepare exactly `C=200` rows, validate the full
`MinBlockFeeOutput`, decode `k`, compute the target, and return.

The provider head is the displayed `head_block`. No finalized or confirmation-depth head is fetched,
returned, or used as an action clock. In the depth-two counterexample, latest head 1210 and `k=0`
return target 1211; the stale finalized-context target 1209 never enters the response.

## Closed Expo types and successful decoding

Keep one handwritten closed type set:

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

For a successful response, decode JSON and use the ordinary TypeScript cast:

```ts
return (await response.json()) as InferenceResponse;
```

Edo explicitly chose this controlled-server trust boundary. Add no custom runtime response parser,
generated OpenAPI client, response schema dependency, exact-key check, safe-integer check,
`selected_action_k < K` check, or target-arithmetic check in Expo. Add no schema-generation or
cross-language compatibility workflow.

## Expo interaction and display

The single screen owns only selected chain, selected K, one `loading` boolean, a nullable response,
and a nullable error. Default to Ethereum and headline `K=5`. Use the existing discrete integer
horizon control with `min=2`, `max=5`, and `step=1`; label it in blocks, never seconds. Chain is one
closed three-choice control.

`Run inference` clears the prior result/error, captures the selected request as an ordinary local
value, sets loading, and performs one fetch. Disable both selectors and the button while loading, so
no separate pending-request state or response binding is needed. Double submission is impossible at
the client edge; add no server admission control.

On success, clear loading/error and display only:

```text
Head block          <head_block>
Selected action k   <selected_action_k>
Target block        <target_block>
```

The visible controls continue to show chain and K. Changing either selection after completion clears
the old result and error, so a response is never displayed under a new selection. There is no result
history, detail modal, analytics screen, model screen, or hidden metadata view.

Use `EXPO_PUBLIC_SPICE_BACKEND_URL` as the required build/runtime endpoint for the Mac's explicit
private-LAN HTTP address. Add no physical-phone loopback default, discovery, pairing, backend picker,
mobile RPC URL, or connection mode.

## Ordinary failures

Invalid request JSON uses FastAPI/Pydantic's ordinary `422` response. Package, checkpoint, provider,
chain-ID, block fetch, preparation, or inference failure stops that request through FastAPI's
ordinary failed-request behavior. Add no error enum, custom response envelope, translation table,
retry policy, fallback result, alternate artifact, or recovery state.

Expo treats every non-success status as failure, reads the response text, and displays
`HTTP <status>: <trimmed response text>`. A fetch exception displays
`Network error: <runtime message>`. Both clear any old result and loading state. There is no automatic
retry; Edo may press `Run inference` again.

## No timed transfer

The action and target are displayed inference facts, not a command executed by the phone. The client
does not poll blocks, wait for a trigger, schedule, sign, broadcast, transfer, cancel, expire, replace,
observe a receipt, or calculate a fee/saving. Remove every wallet, SecureStore, Ethers, transaction,
recipient/value, scheduler, foreground-expiry, receipt, analytics, SQLite, and demo-contract surface
under the later implementation tickets. Retain no placeholder for future transaction submission.

The map's existing transaction-submission fog remains accurate and needs no correction: a future
transaction path requires a fresh owner decision after the inference-only demo is implemented and
stable.

## Lean implementation verification

Later implementation needs one focused FastAPI endpoint fixture covering one successful call,
strict request rejection, and propagated serving failure, plus ordinary Expo TypeScript checking.
Reuse task, preparation, artifact, and chain/K mapping fixtures owned elsewhere. Add no generated
schema test, runtime response-validation test, twelve-case UI matrix, old/new route parity,
transition test, real provider call, model-quality test, or transaction-deletion regression suite.

The disposable synthetic trace covers all twelve closed request choices and the depth-two
counterexample only to validate the contract. It is not production verification.

Approval authorizes only ticket-scoped evidence publication, exactly one Resolution, closing Issue
43, one context pointer on the Wayfinder map, and verification. It authorizes no production,
configuration, test, dependency, data, storage, mobile, server, training, evaluation, acquisition,
job, archive, cutover, or sibling-issue mutation.
