# Modern Avalanche C-Chain forming-block fee

Status: primary-source research for [Prototype the current-block action and
cross-layer parity](https://github.com/edoski/spice/issues/45). This report
does not close the HITL ticket or select a production design.

## Short answer

SPICE can preserve **`k = 0` means the forming block** on modern Avalanche.
What it cannot honestly preserve is the stronger claim that the forming
block's *exact realized base fee* is already present in ordinary closed-parent
columns.

After Octane/Fortuna, Avalanche does not use Ethereum's one-step
`parent base fee + parent utilization -> child base fee` recurrence. The
parent carries a small fee-market state. That state continues to change while
the network waits for the child block. The exact child fee therefore needs
both:

1. the price-relevant state committed by the parent (`excess` and
   `targetExcess`); and
2. the timestamp eventually chosen for the child.

Granite keeps the same idea but measures that waiting time in milliseconds.
The parent's dynamic minimum-delay field supplies the **earliest permitted**
child time, not the time at which the child will actually be built. The public
`eth_baseFee` call uses the latest parent plus the node's current clock and is
explicitly an estimate of a block produced now, not a promise about the next
accepted block ([C-Chain API](https://build.avax.network/docs/rpcs/c-chain/api#eth_basefee),
[Coreth estimator](https://github.com/ava-labs/coreth/blob/v0.16.0/eth/gasprice/gasprice.go#L207-L235),
[fee guide](https://build.avax.network/docs/rpcs/other/guides/txn-fees#dynamic-fee-transactions)).

There is no post-Octane or post-Granite date range that restores the Ethereum
recurrence. A recent subset can be valid only if its membership is decided
from parent-known information. Selecting blocks after seeing that their
realized timestamp or fee happened to match an estimate is target leakage.

## Layman's model

Think of Avalanche's fee market as a tank with three readings saved in every
parent block:

- **capacity**: how much gas the next block is currently allowed to consume;
- **excess**: accumulated demand pressure, which drives the price; and
- **target excess**: a dial that determines the network's target gas rate.

While no block is produced, the tank refills and demand pressure drains. A
child built 1.0 seconds after its parent can therefore have a different base
fee from one built 1.2 seconds after the same parent. The parent tells us the
starting readings, but it does not tell a public transaction sender exactly
when the next proposer will stamp its block.

This is why the fee is not unknowable in principle. Once the parent state and
the child's actual millisecond timestamp are both supplied, the result is
deterministic. The missing fact is simply not causal at the earlier decision
point.

## Exact modern transition

ACP-176 defines the dynamic target and gas-price mechanism. Its activated
reference implementation serializes three unsigned 64-bit values at the start
of the parent's `extraData`: `capacity`, `excess`, and `targetExcess`
([ACP-176 specification](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates),
[AvalancheGo state parser](https://github.com/ava-labs/avalanchego/blob/6afe371e3b86/vms/evm/acp176/acp176.go#L43-L71)).

Let the parent state be `(r, x, q)`. The implementation derives:

```text
T = fake_exp(P=1,000,000, q, D=33,554,432)  # target gas/second
K = 87 * T                                  # price-update denominator
C = 10 * T                                  # maximum capacity
```

`fake_exp` is the integer EIP-4844-style exponential approximation used by the
protocol, not floating-point `exp` ([price implementation](https://github.com/ava-labs/avalanchego/blob/6afe371e3b86/vms/components/gas/gas.go#L52-L110)).

Capacity `r` advances alongside excess, but it is **not** an argument to
`GasPrice`. It constrains how much gas the child may consume. Likewise, the
child's conventional `gasLimit` does not set its base fee. The exact price
inputs are parent excess, parent target excess, elapsed child time, and the
fixed protocol constants.

For a Granite child whose timestamp is `delta_ms` after its parent, Coreth
advances the parent state as follows:

```text
target_per_ms = floor(T / 1000)
r_before      = min(r + 2 * target_per_ms * delta_ms, C)
x_before      = max(x - target_per_ms * delta_ms, 0)
child_basefee = fake_exp(M=1 wei, x_before, K)
```

Before Granite, the same transition advances in whole seconds with rates `2T`
and `T`. The code chooses the millisecond path after Granite and the second
path from Fortuna through Granite
([Coreth state transition](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/dynamic_fee_state.go#L16-L44),
[AvalancheGo time advancement](https://github.com/ava-labs/avalanchego/blob/6afe371e3b86/vms/evm/acp176/acp176.go#L103-L137)).

The price is fixed **before** child transactions execute. Child gas use and
atomic gas use then consume capacity and add to excess; the child proposer may
move `targetExcess` by a bounded amount; and the resulting state is stored for
the grandchild. ACP-176 explicitly says a target change made in block `b`
takes effect for the fee of `b+1`, not `b`
([ACP-176](https://build.avax.network/docs/acps/176-dynamic-evm-gas-limit-and-price-discovery-updates#making-t-dynamic),
[Coreth post-block transition](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/dynamic_fee_state.go#L46-L75)).

The displayed block `gasLimit` is not the current amount of available gas.
Coreth writes the maximum capacity `C` into that conventional header field to
remain close to upstream Geth, while separately checking actual child gas use
against `r_before`. Thus SPICE's ordinary `gas_limit` column cannot substitute
for the serialized capacity state
([Coreth gas-limit and capacity validation](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/gas_limit.go#L28-L49),
[same file](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/gas_limit.go#L100-L181)).

## What is known when the parent closes

| Fact | Known from the closed parent? | Relevance to the child's own base fee |
| --- | --- | --- |
| Capacity `r`, excess `x`, target excess `q` | Yes, in the first 24 bytes of `extraData` | `x` and `q` determine price; `r` separately constrains consumption. |
| Parent timestamp | Yes | Required starting time. After Granite, use `timestampMilliseconds`, not the rounded seconds field. |
| Parent `minDelayExcess` | Yes after Granite | Determines the earliest legal child timestamp. |
| Parent and child `gasLimit` | Parent yes; child derivable from `q` | The conventional child limit is maximum capacity, not the live capacity used in the fee transition. |
| Child timestamp | No | Required for the exact time advancement and therefore usually the exact fee. |
| Child gas used and transactions | No | Do not determine that child's base fee; they update state for its child. |
| Child proposer's target preference | No | Does not change that child's own fee; its bounded update affects the following block. |

ACP-226 requires post-Granite headers to carry `timestampMilliseconds` and
`minimumBlockDelayExcess`. The latter determines a lower bound on the next
timestamp. It does not schedule an exact timestamp
([ACP-226 header fields](https://build.avax.network/docs/acps/226-dynamic-minimum-block-times#block-header-changes),
[Coreth time verification](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customheader/time.go#L48-L109),
[header JSON fields](https://github.com/ava-labs/coreth/blob/v0.16.0/plugin/evm/customtypes/header_ext.go#L160-L205)).

Protocol validation rejects a proposed child earlier than the parent's dynamic
minimum delay. It also rejects a timestamp more than ten seconds ahead of a
verifier's *current* clock. That moving future-clock check is not a fixed
maximum delay after the parent: if block production pauses, a later child can
still be valid. Parent state therefore gives an earliest time but no single
future time at which its child must appear.

## Which subsets can be exact without leakage?

The fee falls monotonically as more idle time is applied to a fixed parent
state: time advancement only subtracts from excess, and the price is monotonic
in excess. This gives three materially different cases.

### Parent-provable exact case

If the price calculated at the earliest legal child time is already the
protocol minimum, any later child on that parent has the same minimum price.
That subset is legitimate because membership is knowable from the parent
before the child exists.

A second legitimate experiment could predeclare a finite transaction deadline
and retain a parent only when the integer `fake_exp` result is constant for
*every* permitted timestamp in that deadline. The deadline and filter must be
fixed before outcomes are inspected. This establishes exactness only for the
declared interval, not for an arbitrarily delayed child.

### Causal estimate or bound

At any query time, parent state plus the query clock gives the fee of a
hypothetical child stamped at that moment. That is exactly what Coreth's
`eth_baseFee` estimator computes. It is a causal feature but remains an
estimate because the accepted child may use a later timestamp or another block
may be accepted first.

Parent state plus the earliest legal child time gives a causal **upper bound**
for the first child on that parent. Waiting can drain excess and reduce the
price, but cannot increase it before that first child executes. Calling this an
upper bound is accurate; calling it the exact current fee is not.

### Retrospective coincidence

After downloading the child, its timestamp can be inserted into the transition
to reconstruct its fee exactly. This is useful for label validation and
protocol tests. It does not make the timestamp available at the earlier
transaction decision.

The following filters leak target information and are not valid ways to rescue
the forming-block feature:

- keep rows where the realized child timestamp equals a chosen estimate time;
- keep rows where the estimated and realized fees happen to match;
- search several timing rules, then retain the one that matches most outcomes;
- use the child's `timestampMilliseconds`, base fee, gas used, or capacity as a
  model input for predicting that same child.

Filtering only by a modern activation date also does not help. Octane activated
Fortuna/ACP-176 on Avalanche Mainnet on 8 April 2025; Granite activated
ACP-226 on 19 November 2025. All blocks after the first date use the dynamic
fee state, and blocks after the second use millisecond advancement
([Octane announcement](https://build.avax.network/blog/octane-optimizing-c-chain-gas-fees),
[Granite activation](https://build.avax.network/blog/granite-upgrade)).

If “the fee metric” means the exponential ACP-176 price curve, then yes: all
post-Octane C-Chain blocks follow it. The curve still consumes elapsed child
time, so following the same curve does not imply parent-only predictability.

## Small recent-mainnet check

A read-only check queried the official public C-Chain JSON-RPC endpoint for
1,001 consecutive Granite-era blocks, heights **90,015,418–90,016,418**, from
2026-07-11 05:23:04 UTC through 05:42:08 UTC. Boundary hashes were
`0xd1e57dc5ac02afa069c242f6f04102e88a0b8a29a32c87cdfdbc6d0006bc114e`
and
`0x5760e969f3e08ae6c4afb6d8c448427b26ad5478c55fc0ff1575949cde59f47b`.
The probe parsed each parent's first 24 `extraData` bytes and applied the tagged
AvalancheGo/Coreth transition above.

| Check | Result |
| --- | ---: |
| Actual child fee reproduced from parent state **plus realized child millisecond time** | 1,001 / 1,001 |
| Parent-only earliest-valid upper bound happened to equal the realized fee | 802 / 1,001 |
| Parent state was already in the timestamp-independent minimum-price case | 0 / 1,001 |
| Realized parent-to-child delay | min 992 ms; median 993 ms; max 4,968 ms |
| Earliest-valid upper bound minus realized fee | median 0 wei; max 1,177,495 wei |

The 802 equalities are empirical coincidences caused by typical timing and
integer price steps. They are not 802 causally identifiable exact rows: one
learns which rows matched only after reading the child. The zero
timestamp-independent cases also show why a recent “minimum-price plateau”
subset cannot be assumed to contain useful data. This one short slice is a
diagnostic, not a population estimate.

The public endpoint and method contract are documented by Avalanche's
[C-Chain API](https://build.avax.network/docs/rpcs/c-chain/api#endpoints).

## Lean routes that preserve `k = 0`

Preserving the action definition does **not** require pretending that every
chain exposes the same current-fee feature. Three routes remain honest:

1. **Leanest and easiest to teach:** make the latest closed parent's base fee
   the fee input on every chain, while `k = 0` remains the forming child label.
   This gives up an exactly derived Ethereum child-fee feature, but produces one
   simple causal information contract and needs no Avalanche protocol parser.
2. **Causal estimate:** use a clearly named `next_base_fee_estimate` from
   `eth_baseFee`. To evaluate it honestly, capture parent hash, query timestamp,
   estimate, and subsequent accepted child online. Historical child headers
   alone cannot recreate when an old RPC query would have occurred.
3. **Protocol upper bound:** parse parent fee state and calculate the
   earliest-valid child fee. This is deterministic offline and live, but adds a
   fork-aware Avalanche adapter and is more code to explain.

For this bounded undergraduate project, route 1 best matches the stated
priority of leanness unless an ablation shows that the chain-specific estimate
earns its complexity. Route 2 is the smallest honest way to retain a
forming-fee-like live signal. Route 3 is scientifically precise but is not the
default merely because it is possible.

The key wording change is small but important: on Avalanche, the realized fee
of the forming block is the **`k = 0` outcome**. The information available when
choosing that action is the closed parent, optionally augmented by a causal
estimate or bound. No date-based exclusion of modern Avalanche is required for
the action itself; only the false claim of exact pre-selection fee availability
must be excluded.
