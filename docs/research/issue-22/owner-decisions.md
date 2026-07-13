# Issue 22 owner decisions

This contract records the choices explicitly approved while resolving
[Choose serving trust, exposure, and observation transitions](https://github.com/edoski/spice/issues/22).
The ticket is resolved; its canonical resolution is
[the single approved GitHub comment](https://github.com/edoski/spice/issues/22#issuecomment-4952451781).

## Decision 1: one-client thesis demo

Approved:

- SPICE serving is a one-user Sepolia thesis demo with one Mac backend process,
  one Uvicorn worker, and exactly one interactive client at a time.
- The client is either Edo's physical phone over an owner-controlled private
  LAN or personal hotspot, or same-host macOS simulator/Expo web over loopback.
  An Android emulator may use its ordinary host alias if later used. Do not
  claim simultaneous phone and simulator support.
- For the phone, bind to the Mac's specific private-interface address when
  practical and set `EXPO_PUBLIC_SPICE_BACKEND_URL` explicitly to that address.
  For a same-host client, configure loopback. Endpoint configuration selects
  the environment; add no runtime client mode, discovery, pairing, tunnel, or
  production deployment service.
- Public, university, hotel, and otherwise untrusted Wi-Fi are outside the
  contract. On the private-network route, anyone admitted to that network can
  call the unauthenticated API and see demo analytics. State this limitation
  once; do not build authentication, bearer/API keys, TLS deployment,
  accounts, roles, quotas, rate limiting, firewall management, multi-user
  ownership, multi-worker coordination, or dormant production modes.
- The burner-wallet key remains only in phone SecureStore. Signing and
  broadcasting remain phone-owned; the backend has no wallet authority.
- Request identifiers are correlation keys, never authorization. Analytics are
  local demo data, not a public evidence service.
- Minimal platform local-network or cleartext-development permission is mobile
  deployment plumbing, not an authentication system.

This narrow exposure decision does not waive correctness. Later decisions must
still define one-way observation and idempotency, honest receipt wording,
simple pending cleanup, and deterministic resource ownership. Academic
correctness, lean code, straightforwardness, and learnability outrank
production security and operations for this bounded undergraduate demo.

Downstream coordination is recorded once on the serving durability/lifecycle
and serving/mobile prototype tickets; this file does not duplicate their
contracts.

## Decision 2: bind one transaction, then observe its receipt once

Approved:

- A request starts `pending` with a nullable transaction hash. The first
  syntactically valid normalized transaction hash is atomically bound before
  receipt lookup and is immutable thereafter.
- A transaction hash is unique across requests. A different hash for the same
  request, or reuse of one hash for another request, is a conflict.
- Polling or retrying the same request/hash pair is idempotent. No receipt or
  an RPC error leaves the request pending with the hash still bound; neither
  permits replacement.
- A receipt from the configured Sepolia view is accepted only when its actual
  inclusion block is at or after the intended target block. An earlier receipt
  is a contract error and does not release the bound hash.
- The first accepted receipt moves the request once from `pending` to
  `observed`. Persist receipt status, actual inclusion block, gas used, and the
  approved receipt-backed accounting.
- Receipt status `0` is still an observed included transaction. Report it as
  reverted or failed execution, never as successful execution. Do not hide it,
  leave it replaceable, or drop it from the observed network outcome.
- After observation, an exact same-pair retry returns the stored result without
  rewriting timestamps or totals.
- Receipt existence, status, and inclusion are RPC-observed facts at that
  moment. The trusted phone asserts the request-to-transaction association;
  SPICE makes no cryptographic ownership or future-finality claim.

This remains one lean record and one store-owned operation: `pending` or
`observed`, one nullable-then-immutable hash, and one uniqueness rule. Add no
generic state machine, idempotency framework, sender/recipient/value checks,
wallet registry, signatures, nonce tracking, smart-contract attestation,
ownership system, or security machinery.

## Decision 3: block-owned pending lifetime

Approved:

- Delete `prediction_ttl_seconds`, `expires_at_unix`, the mobile wall-clock
  expiration timer/state, and expired/deadline statuses and metrics.
- An unbound prediction is actionable only through its approved trigger-parent
  opportunity. Missing that opportunity fails closed: no broadcast, fallback,
  rerun, replacement, or reschedule.
- A missed unbound prediction is operational debris, not analytics. Remove it
  lazily on the next relevant request or service startup. Add no timer,
  background worker, cleanup endpoint, or retained failed-state framework.
- A bound transaction hash never expires or auto-deletes. It remains pending
  under the same-hash-only rule until its receipt is observed.
- Absence of a receipt is reported honestly and triggers no application
  intervention.

The block schedule owns action availability; it is not converted into a
wall-clock or inclusion deadline. Observed-history retention remains a
separate choice.

## Decision 4: complete observed-only demo analytics

Approved:

- Analytics contains only observed transactions. Exclude both unbound and
  hash-bound pending requests.
- Include receipt status `1` and `0` rows, showing receipt status and actual
  inclusion so reverted execution is never presented as success.
- Remove request identifiers from the analytics response. The unique
  transaction hash identifies an observed row.
- Rows and aggregate totals cover the identical complete observed set. Remove
  the current newest-100-rows versus all-history-totals mismatch.
- Retain the complete tiny one-user demo history. Add no age limit, rolling
  cap, pruning, retention setting, delete endpoint, archive scheduler, or
  policy framework.
- A fresh history requires an offline whole-store reset or archive while the
  service is stopped. The serving durability ticket owns the exact mechanism.

This private-network analytics view is demo bookkeeping, not public evidence
or thesis testing data.
