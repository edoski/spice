# FABLE (Fee Analysis through Blockchain Learning and Estimation)

FABLE learns from finalized block history to choose a low-base-fee block within a short future [horizon](CONTEXT.md). It compares LSTM, Transformer, and Transformer-LSTM models and can serve a trained model through a small inference API.

Its scientific lineage is the temporal experiment in *SPICE: A Predictive Framework for Cost-Optimization in Multichain Environments*: a future minimum-block decision paired with an auxiliary fee prediction. FABLE's current equations and claim limits are documented in the [manual](FABLE.md#scientific-contract). The [glossary](CONTEXT.md) defines its domain terms.

## Hosts and responsibilities

The repository supports three explicit operating locations:

- A workstation creates requests, acquires finalized block history, submits work, publishes tuning results, and computes transient evaluation reductions.
- A GPU server fits, tunes, and evaluates through Slurm jobs.
- A Mac runs the CPU inference API used by the Expo mobile demo.

The [manual](FABLE.md#remote-submission) defines remote submission and host configuration.

## Install

Python 3.11 and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync
```

Install the serving extra on the inference host:

```bash
uv sync --extra serve
```

## Quick start

Create the required JSON files from the [request reference](FABLE.md#requests-and-definitions).

Acquire an inclusive block range. `STORAGE_ROOT` must be absolute; this Ethereum example uses `--no-poa`:

```bash
STORAGE_ROOT=/absolute/storage \
  fable corpus acquire REQUEST.json --rpc-url URL --no-poa
```

Submit one or more training or evaluation requests:

```bash
fable submit REQUEST.json
```

Run one candidate configuration from a tuning request:

```bash
fable study run TUNE_REQUEST.json METHOD.json
```

Publish the collected tuning results:

```bash
STORAGE_ROOT=/absolute/storage fable study finalize STUDY_ID
```

The [CLI reference](FABLE.md#cli) defines the exact command contracts.

## Serving and mobile demo

Place cwd-local `SERVING.yaml` beside the serving process, then start the factory:

```bash
uv run uvicorn fable.serving:create_app --factory
```

The FABLE Inference API accepts `POST /inference`. The [serving reference](FABLE.md#serving-and-mobile) defines its request, response, and configuration.

The private Expo app lives in `app`. Set its only backend variable to the API origin before starting Expo:

```bash
cd app
EXPO_PUBLIC_FABLE_BACKEND_URL=http://HOST:PORT npm start
```

## Read next

Read the [FABLE manual](FABLE.md) from its worked decision through the scientific contract, architecture, and exact reference. Hard-to-reverse decisions are in [docs/adr](docs/adr/).

## Where do I look?

| Question | Owner |
| --- | --- |
| How does one decision work end to end? | [Worked decision](FABLE.md#one-decision-end-to-end) |
| Why are the inputs causal, and what do the equations mean? | [Scientific contract](FABLE.md#scientific-contract) |
| Which module owns each object and seam? | [Architecture](FABLE.md#architecture-and-deep-interfaces) |
| What are the exact requests, paths, commands, and schemas? | [Exact reference](FABLE.md#exact-reference) |
| What does a domain term mean? | [Context](CONTEXT.md) |
| How does one deep interface work internally? | [Architecture and deep interfaces](FABLE.md#architecture-and-deep-interfaces) |
