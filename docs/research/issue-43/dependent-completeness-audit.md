# Issue 43 dependent completeness audit

Status: complete read-only contract and caller audit for the final contract explicitly approved by
Edo on 2026-07-14. No production, configuration, test, dependency, data, storage, mobile, server,
training, evaluation, acquisition, job, archive, or sibling issue changed.

## Verdict

No hidden consequential Issue 43 choice remains. Closed Issue 33 deletes the old timed-transfer
system and fixes every server-side lifecycle choice. The approved contract closes the remaining
backend-to-Expo seam with one request, one response, one loading interaction, and ordinary errors.

Edo's latest decision removes both runtime response parsing and OpenAPI generation. The controlled
FastAPI/Pydantic server is the response authority; Expo performs ordinary JSON decoding plus a
TypeScript cast.

## Consumed contracts

- **Issue 33:** physical Expo phone, trusted private LAN, stateless FastAPI server, three Web3 clients,
  internal exact 3×4 artifact mapping, per-call load/check/prepare/infer, exact request/response
  field inventory, and deletion of all transaction/durability/analytics/readiness machinery.
- **Issue 31:** latest provider head `h`, exact live right edge, `C=200`, full two-head validation,
  first-index decode, and target arithmetic; finalized context is not an API fact.
- **Issue 46:** `h`, `k`, and target semantics survive; transaction scheduling does not enter the
  inference-only baseline.
- **Issues 23 and 24:** the full finite `MinBlockFeeOutput`, direct exact-K action, no action mask,
  auxiliary scalar validation without scheduling or display authority, and direct target function.
- **Issue 47:** shared `C=200`, chain-specific feature facts, strict no-repair input, and no
  target-row information.
- **Issue 48:** separately trained serving K values `{2,3,4,5}`, with K=5 headline/default and no
  seconds conversion, masking, or research-horizon UI.
- **Issues 22 and 78:** only the trusted one-client private-LAN and single-operator/mature-library
  boundaries survive serving supersession.

## Current caller disposition

| Current surface | Final disposition |
| --- | --- |
| `serving/api.py` | Replace health, model, transaction-observation, and analytics routes with only `POST /inference`; use lifespan-owned clients from Issue 33. |
| `serving/schemas.py` | Replace metadata, timed prediction, observation, and analytics DTOs with the strict two-field request and three-field response. |
| `serving/inference.py` | Delete seconds masking, request IDs, TTL, timestamps, scheduling fields, persistence, receipt/accounting, and generic compiled task machinery; consume the approved artifact/live preparation/task owners. |
| `serving/live_blocks.py` | Delete Sepolia, confirmation-depth, transaction-receipt, and fee-accounting behavior; provider head and exact context remain server-owned. |
| `serving/config.py` and runtime | Consume the Issue 33 storage root and three RPC URLs; delete runtime artifact choice, Sepolia, SQLite, TTL, confirmation-depth, and demo-contract fields. |
| `mobile/src/api.ts` | Keep one POST fetch, ordinary non-2xx text error, successful JSON cast, and no other route. |
| `mobile/src/types.ts` | Keep only closed Chain/Horizon request/response types plus no generic run-state union. |
| mobile screen | Keep chain/K controls, loading, result/error, and three result rows; delete wallet, transfer form, scheduler, receipt, modal, savings, and analytics navigation. |
| mobile RPC/wallet/scheduler modules | Delete without replacement. Expo never talks to a blockchain. |

This is a disposition map for later implementation planning, not authorization to edit those files.

## Error and race completeness

Pydantic rejects unsupported chain/K and extra request fields before inference. Server-owned direct
checks stop provider/artifact/context/output failures. Expo reports non-2xx response text and fetch
exceptions. A failure produces no result and changes no server state.

The client disables selectors and submission while its one fetch is active. Therefore the selected
chain/K cannot change during the request, a second request cannot start, and no request ID, pending
record, cancellation token, or response-binding protocol is required. Changing selection after
completion clears the old result. This closes the only relevant single-client race without adding a
state machine or server coordination.

The accepted controlled-server risk is that a malformed successful JSON body could be trusted by the
TypeScript cast. Edo explicitly chose that smaller boundary. FastAPI/Pydantic response construction
and the focused endpoint fixture are sufficient for this thesis demo; Expo duplicates no validation.

## Scope and map effects

No new ticket or fog graduates. The map already records optional transaction submission as fog after
the inference-only demo is implemented and stable. No fog correction, sibling issue change, or ADR
edit is needed. Existing broad domain documentation is not authority for this clean serving seam and
remains with its later normative-documentation owner.
