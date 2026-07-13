# Lean precision and update mechanics

Research date: 2026-07-13. This is bounded primary-source evidence for [Issue 62](https://github.com/edoski/spice/issues/62). It freezes a precision comparison for the later training-host prototype; it does not choose the final host, train a thesis model, inspect predictive or economic outcomes, or change production code.

The lock selects PyTorch `2.7.1+cu118`, CUDA runtime 11.8, cuDNN 9.1, Triton 3.3.1, and Lightning 2.6.5 on Linux x86-64. The local environment was Python 3.11.15, PyTorch 2.11.0, and Lightning 2.6.5 on Apple arm64 with MPS but no CUDA or cuDNN runtime. See [uv.lock](../../../uv.lock) and [pyproject.toml](../../../pyproject.toml).

The configured accelerator targets are an NVIDIA L40 and GeForce RTX 2080 Ti. NVIDIA identifies the L40 as Ada compute capability 8.9 with 48 GiB and native TF32, BF16, and FP16 Tensor Core formats; the RTX 2080 Ti is Turing compute capability 7.5 with 11 GiB and native FP16, but not native TF32 or BF16 ([NVIDIA CUDA GPU list](https://developer.nvidia.com/cuda/gpus), [L40 data sheet](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/support-guide/NVIDIA-L40-Datasheet-January-2023.pdf), [RTX 2080 Ti specifications](https://www.nvidia.com/en-us/geforce/graphics-cards/compare/?section=compare-specs), [Turing architecture](https://developer.nvidia.com/blog/?p=11872)). These are product capabilities, not verified properties of the configured hosts. The approved remote environment currently cannot import PyTorch, and no safe accelerator endpoint was available. Driver, visible device, actual VRAM, runtime CUDA/cuDNN, kernel coverage, speed, and memory therefore remain prototype facts. This report invents none of them.

## Result

Keep one strict reference and at most two hardware-gated performance candidates:

| Route | Exact gate | Arithmetic and state | Scaling | Status |
| --- | --- | --- | --- | --- |
| Strict FP32 | Any supported CUDA device | FP32 inputs, parameters, eligible arithmetic, loss, gradients, and optimizer moments | None | Required semantic reference |
| TF32-enabled FP32 | `torch.cuda.is_tf32_supported()` and representative operations pass | FP32 storage and outputs; TensorFloat-32 may be used inside CUDA FP32 matrix multiplications and cuDNN operations | None | L40 performance candidate; unsupported on RTX 2080 Ti |
| Mixed BF16 | `torch.cuda.is_bf16_supported(including_emulation=False)` and representative full/tail LSTM steps pass | FP32 parameters, loss, gradients, and AdamW moments; eligible forward operations use BF16 | None | Preferred L40 reduced-precision candidate |
| Mixed FP16 | Native representative full/tail steps pass; admit only when native BF16 is absent or fails the representative operations | FP32 parameters, loss, gradients after unscale, and AdamW moments; eligible forward operations use FP16 | Dynamic `GradScaler` | Conditional fallback, not an additional default |

This yields three prototype routes on the L40: strict FP32, TF32-enabled FP32, and mixed BF16. It yields strict FP32 plus mixed FP16 on the RTX 2080 Ti. Do not measure four routes merely because four names exist. FP16 on the L40 is rejected unless its actual BF16 LSTM gate fails.

For strict FP32 set `torch.set_float32_matmul_precision("highest")`, `torch.backends.cuda.matmul.allow_tf32 = False`, and `torch.backends.cudnn.allow_tf32 = False`. On the L40 performance routes, set the FP32 residual-matmul policy once to `"high"` with CUDA matmul and cuDNN TF32 enabled. Thus BF16 is one declared composite policy, not a hidden BF16-by-TF32 factorial experiment. Keep `"highest"` and both flags false for the RTX 2080 Ti FP16 route. PyTorch documents that `"highest"` uses full FP32 internally, while `"high"` may use TensorFloat-32 on CUDA; the output dtype remains FP32 and cuDNN convolution has a separate switch ([PyTorch matmul precision](https://docs.pytorch.org/docs/2.7/generated/torch.set_float32_matmul_precision.html)).

Reject unsupported candidates instead of silently falling back. In particular, PyTorch's default `is_bf16_supported()` may accept emulation; the native gate must pass `including_emulation=False`. In the locked PyTorch source, native BF16 requires CUDA compute capability 8 or newer, and `is_tf32_supported()` uses that native capability test ([PyTorch 2.7.1 CUDA capability source](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/cuda/__init__.py#L177-L221)). NVIDIA likewise documents BF16 and TensorFloat-32 Tensor Core support from compute capability 8.0 ([CUDA 11.8 alternate floating point](https://docs.nvidia.com/cuda/archive/11.8.0/cuda-c-programming-guide/index.html#alternate-floating-point)). Capability is necessary, not sufficient: the prototype must exercise the actual model operations and shapes.

## Dtype contract

| Meaning | Canonical dtype | Precision-route behavior |
| --- | --- | --- |
| RPC/source integer truth | Python `int`, range-checked before storage | Python integers have unlimited precision; never round source truth through float ([Python numeric types](https://docs.python.org/3.11/library/stdtypes.html#numeric-types-int-float-complex)) |
| Canonical corpus integer facts | Signed `int64` | Reject out-of-range values instead of approximating them |
| Row/sample positions, block numbers, timestamps, class labels | `int64` | Never autocast |
| Masks | `bool` | Never autocast |
| Scaler fitting and persisted scalar statistics | Float64 computation; Python `float` at the serialization seam | Python `float` is normally a C double; transformed arrays are explicitly narrowed once |
| Prepared model features and regression targets | FP32 at rest and transfer | Autocast chooses eligible operation dtypes; callers do not call `.half()` or `.bfloat16()` |
| Model parameters | FP32 | Remain FP32 under mixed autocast |
| Transformer positional buffer | FP32, non-persistent | Adding it to a lower-precision activation promotes that expression to FP32; later eligible operations may autocast again |
| Forward activations | FP32 for strict/TF32; operation-selected BF16 or FP16 for mixed routes | Autocast is operation-specific, not a blanket tensor conversion |
| Cross-entropy and Smooth L1 loss | FP32 | CUDA autocast lists both among operations forced to FP32 |
| Leaf parameter gradients | FP32 because parameters are FP32 | FP16 gradients are unscaled before inspection, clipping, or stepping |
| Gradient norm | Framework/PyTorch native reduction over FP32 gradients | Must be finite before an accepted step |
| AdamW first/second moments | FP32, matching FP32 parameters | PyTorch initializes both with `zeros_like(parameter)` ([PyTorch 2.7.1 Adam source](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/optim/adam.py#L155-L188)) |
| FP16 loss-scale state | FP32 scalar scale plus growth/backoff counters | Exists only for FP16 and belongs in a resumable training checkpoint ([PyTorch 2.7.1 GradScaler source](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/amp/grad_scaler.py#L603-L630)) |
| Complete-map reducer sums | Float64, with exact integer counts | Detach and upcast each contribution *before* summing; converting an already BF16/FP16 sum cannot recover lost bits |
| Decoded class output | CPU `int64` | Independent of arithmetic route |
| Final model artifact | CPU FP32 model `state_dict` | Runtime precision is selected when loading; it is not baked into weights |
| Resumable optimizer checkpoint | CPU-portable FP32 model and AdamW state; FP16 adds scaler state | Recreate the identical model and optimizer structure before loading |

The local code already uses the core integer/bool distinctions in [problem_store.py](../../../src/spice/temporal/problem_store.py), [sequence_inputs.py](../../../src/spice/modeling/representations/sequence_inputs.py), and [batch.py](../../../src/spice/prediction/families/min_block_fee_multitask/batch.py). [scaling.py](../../../src/spice/temporal/input_normalization/scaling.py) fits in float64 and returns float32 transformed features. [metrics.py](../../../src/spice/prediction/families/min_block_fee_multitask/metrics.py) currently performs some diagnostic arithmetic and sums in the model-output dtype before `.item()`; mixed precision therefore requires a direct clean-break change so every complete-map contribution is upcast before reduction. Issue 40 retains ownership of the later final parity gate.

PyTorch autocast should wrap the forward pass and loss only; backward runs outside it. Eligible CUDA linear/matrix operations may use the lower dtype, while `cross_entropy`, `smooth_l1_loss`, `layer_norm`, and `sum` are among operations forced to FP32. Float64 and non-floating tensors are not autocast-eligible, and mixed-type binary operations promote to the wider listed dtype ([PyTorch 2.7 AMP](https://docs.pytorch.org/docs/2.7/amp.html#cuda-op-specific-behavior)). NVIDIA documents BF16 as having FP32's exponent range but less stored precision; FP16 has a much smaller range. This is why BF16 needs no loss scaler and FP16 does ([CUDA 11.8 alternate floating point](https://docs.nvidia.com/cuda/archive/11.8.0/cuda-c-programming-guide/index.html#alternate-floating-point), [PyTorch AMP gradient scaling](https://docs.pytorch.org/docs/2.7/amp.html#gradient-scaling)).

## Deterministic comparison boundary

Hold these controls constant across every route:

1. At process launch set `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
2. Seed Python `random`, NumPy, and PyTorch; use one GPU and one CUDA stream for the evidence run.
3. Call `torch.use_deterministic_algorithms(True, warn_only=False)`.
4. Set `torch.backends.cudnn.benchmark = False` and `torch.backends.cudnn.deterministic = True`.
5. Freeze data order, full and tail batches, initialized weights, model mode, update count, optimizer settings, and synchronization/timing procedure before measurement.

The current [runtime backend configuration](../../../src/spice/modeling/_runtime.py) seeds the three random sources and controls cuDNN benchmarking/determinism, but it does not enable PyTorch's global deterministic-algorithm guard or establish the cuBLAS workspace setting. The prototype must close both gaps without adding a project-owned determinism registry.

PyTorch explicitly does not promise reproducibility across releases, commits, platforms, or CPU versus GPU even with identical seeds. Its deterministic-algorithm guard selects deterministic implementations where available and errors otherwise; CUDA RNN/LSTM operations may require extra CUDA controls ([PyTorch reproducibility](https://docs.pytorch.org/docs/2.7/notes/randomness.html), [deterministic algorithms](https://docs.pytorch.org/docs/2.7/generated/torch.use_deterministic_algorithms.html)). cuBLAS limits bitwise guarantees to the same toolkit version, GPU architecture, and number of streaming multiprocessors; concurrent streams require separate workspaces or `CUBLAS_WORKSPACE_CONFIG`, and `:4096:8` costs about 24 MiB ([cuBLAS 11.8 reproducibility](https://docs.nvidia.com/cuda/archive/11.8.0/cublas/index.html#results-reproducibility)). cuDNN similarly limits most bitwise guarantees to the same version and architecture and names exceptions ([cuDNN reproducibility](https://docs.nvidia.com/deeplearning/cudnn/archives/cudnn-891/developer-guide/index.html#reproducibility-determinism)).

The valid claim is therefore narrow: repeated execution of one frozen route on the same GPU and locked software/runtime should reproduce or fail loudly. It is not a cross-device, cross-release, or cross-precision bitwise claim. TF32 is a numerical-format choice, not a relaxation of determinism.

## One update, clipping, and nonfinite behavior

Use one owner for the update sequence. If Lightning is the selected host, prefer its automatic optimization, clipping, accumulation, autocast, and validation contexts; do not preserve the current manual loop beside it. If direct PyTorch is selected, keep the same native order explicitly:

1. Clear gradients with `optimizer.zero_grad(set_to_none=True)`.
2. Run forward and loss inside the route's autocast context.
3. Backward outside autocast.
4. For FP16 only, call `scaler.unscale_(optimizer)` exactly once.
5. Compute the global norm and clip the unscaled FP32 gradients.
6. Step AdamW. FP16 uses `scaler.step(optimizer)` and then `scaler.update()`.

PyTorch requires unscaling before clipping and requires the scale to remain constant through an accumulated effective batch ([AMP examples](https://docs.pytorch.org/docs/2.7/notes/amp_examples.html#gradient-clipping), [AMP accumulation](https://docs.pytorch.org/docs/2.7/notes/amp_examples.html#gradient-accumulation)). `clip_grad_norm_` computes one global norm and can raise on a nonfinite result ([gradient clipping](https://docs.pytorch.org/docs/2.7/generated/torch.nn.utils.clip_grad_norm_.html)). `set_to_none=True` lowers memory use and changes a missing gradient from a zero-gradient update to a skipped parameter update; that exact behavior is appropriate here and must stay explicit ([AdamW `zero_grad`](https://docs.pytorch.org/docs/2.7/generated/torch.optim.AdamW.html#torch.optim.AdamW.zero_grad)).

For strict FP32, TF32, and BF16, a nonfinite loss or gradient norm fails before the optimizer step. For the bounded FP16 semantic probe, any nonfinite gradient or `GradScaler`-skipped step rejects the candidate: native scaling is not evidence when the declared one-step update did not occur. A later accepted FP16 training policy may use native skipped-step recovery, but it must record skips, checkpoint the scaler after `update()`, and never silently switch precision. OOM also fails the candidate; there is no automatic precision fallback.

Keep gradient accumulation at one unless the actual VRAM measurement requires it. If required, let the selected framework own loss normalization, the effective-batch boundary, and the final partial accumulation flush, then include that tail boundary in the semantic probe. Issue 55 retains batch placement and transfer ownership.

Use ordinary AdamW with its native defaults and the selected learning rate/weight decay. On CUDA, PyTorch normally chooses the foreach implementation when `foreach` and `fused` are left unset; foreach costs roughly one additional parameter-sized peak tensor list. Fused AdamW supports FP64/FP32/FP16/BF16 but remains opt-in in the locked documentation ([AdamW](https://docs.pytorch.org/docs/2.7/generated/torch.optim.AdamW.html)). Do not add a fused/foreach configuration axis unless the frozen profile shows the optimizer is material. It adds code and version surface without changing the research question.

## Lightning-native candidate

If Issue 26 selects Lightning, use automatic optimization. `training_step` returns the loss; the Trainer owns zeroing, autocast, backward, FP16 scaling and unscaling, norm clipping, optimizer step, scaler update, and the validation inference context. Expose only Lightning's native `32-true`, `bf16-mixed`, or `16-mixed` value selected by the hardware route. Remove the current manual optimizer path and nested project precision context instead of retaining two loops or adding a framework-neutral wrapper.

This is a correctness requirement for mixed precision, not just a style preference. The current manual path requests the raw optimizer, so an FP16 loss may be scaled by `manual_backward` while project clipping sees scaled gradients and the raw step bypasses scaler step/update. Lightning 2.6.5's mixed-precision plugin uses `torch.autocast`; FP16 owns a `GradScaler`, unscales before clipping, and performs scaler step/update, while BF16 has no scaler ([Lightning 2.6.5 mixed precision source](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/plugins/precision/amp.py), [automatic optimization](https://lightning.ai/docs/pytorch/stable/common/optimization.html)).

Keep `accumulate_grad_batches=1`. Lightning steps on the final batch, but a final partial accumulation group would still have each constituent loss divided by the fixed accumulation count. No VRAM evidence currently earns that complication ([Lightning 2.6.5 epoch loop](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/loops/training_epoch_loop.py), [automatic loop](https://github.com/Lightning-AI/pytorch-lightning/blob/2.6.5/src/lightning/pytorch/loops/optimization/automatic.py)). Let Lightning use the optimizer's default `zero_grad()`, which is `set_to_none=True` in the locked PyTorch. Keep Trainer validation under its default inference context ([Lightning Trainer](https://lightning.ai/docs/pytorch/stable/common/trainer.html)). Issue 55 still owns where the batch moves; precision does not justify a custom transfer path.

The direct-PyTorch host remains a real Issue 26 alternative. It uses the six native steps above without a copied Lightning abstraction. This report recommends no shared training-host interface.

## `torch.compile` does not enter the candidate set

The evaluated challenger was the inner model call with Inductor, `mode="default"`, `dynamic=None`, and `fullgraph=False`; the whole Lightning module, private `allow_rnn`, `suppress_errors`, custom cache handling, and project fallback modes were excluded. PyTorch documents that `dynamic=None` begins static and may recompile/generalize after a shape change, while graph breaks resume eager execution; compilation and cache warm-up make early calls unrepresentative ([`torch.compile`](https://docs.pytorch.org/docs/2.7/generated/torch.compile.html), [dynamic shapes](https://docs.pytorch.org/docs/2.7/torch.compiler_dynamic_shapes.html), [compiler troubleshooting](https://docs.pytorch.org/docs/2.7/torch.compiler_troubleshooting.html)). A compiled wrapper does not belong in a portable checkpoint; save the ordinary model state.

The locked PyTorch 2.7.1 defaults `torch._dynamo.config.allow_rnn` to false and deliberately graph-breaks on RNN, GRU, and LSTM modules ([2.7.1 configuration](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/_dynamo/config.py), [2.7.1 graph-break source](https://github.com/pytorch/pytorch/blob/v2.7.1/torch/_dynamo/variables/builder.py#L1542-L1547)). Local `fullgraph=True` failed both representative shapes at the LSTM. The partial-graph diagnostic produced six graphs and left the LSTM plus tensor-dependent mask checks eager.

Local partial capture reduced steady MPS/Torch 2.11 one-step time by about 15%, but the first full call cost 2.91 times eager and the first tail call cost 4.86 times eager. Same-seed, cloned-state first losses differed under compiled dropout scheduling, so semantic parity was not established. This evidence cannot predict locked CUDA/Torch 2.7.1 behavior. Partial recurrence capture, material cold and shape costs, unresolved same-seed semantics, compiler/cache concepts, and no target evidence outweigh that local steady improvement. Reject `torch.compile` from the lean Issue 26 candidate set. Issue 40 retains the final same-weight accelerator parity gate; it is not a reason to keep a compiler option alive.

## Checkpoint and artifact portability

Mixed autocast does not convert FP32 model parameters, so the final artifact remains a CPU FP32 `state_dict`. Save state dictionaries, not module objects, and load with an explicit `map_location`; PyTorch identifies model state as parameters plus persistent buffers and recommends state dictionaries for compatibility ([serialization semantics](https://docs.pytorch.org/docs/2.7/notes/serialization.html), [`torch.load`](https://docs.pytorch.org/docs/2.7/generated/torch.load.html)). The non-persistent positional buffer is rebuilt by the model and is not part of this artifact.

A final inference artifact needs model state and its already-owned model/config identity, not optimizer or precision state. Precision is a runtime execution choice. A resumable training checkpoint additionally needs AdamW state, parameter groups, epoch/global-step boundary, and the selected precision policy. FP16 adds the complete `GradScaler.state_dict`; BF16 does not. Exact mid-run continuation would also need RNG and data-order state. Prefer an epoch/update boundary with no partial accumulation. Issue 34 owns durable provenance and publication, and Issue 26 owns the final host decision.

Optimizer state dictionaries associate state with parameter IDs/order without verifying names, so portability requires reconstructing the same model and optimizer parameter ordering before load ([AdamW state dictionary](https://docs.pytorch.org/docs/2.7/generated/torch.optim.AdamW.html#torch.optim.AdamW.state_dict)). Save CPU-portable tensors and let the selected host restore them to the chosen device. Do not introduce a precision-version marker, converter, compatibility reader, or parallel artifact format.

## Frozen prototype evidence

The comparison was frozen before timing. It uses the approved neutral LSTM: input width 7, context 200, five classes, two 256-unit projected LSTM layers, 256-unit head, dropout 0.2, batch 64, and tail batch 7. The synthetic inputs and standardized regression targets are FP32; labels are `int64`. The model has 1,187,846 parameters occupying 4,751,384 FP32 bytes. Seed 2026, cloned initial state, inputs, labels, targets, CE plus Smooth L1 sample reduction, AdamW `lr=3e-4`/`weight_decay=1e-4`, global norm clip 1.0, and accumulation one are identical across candidates.

Candidate order is strict FP32, TF32-enabled FP32, BF16 mixed, then FP16 mixed only where the hardware gate admits it. Compile is a separate strict-FP32 eager challenger, not a precision Cartesian product. Each shape gets a first-call observation, three warm-ups, and ten synchronized steady iterations. The local budget was 15 minutes. Unsupported operations, nonfinite values, OOM, semantic mismatch, fallback ambiguity, or budget exhaustion stop a route. No thesis data, predictive/economic result, profiler framework, permanent harness, or remote job is permitted.

On the local M2 Max MPS environment, strict FP32 eager completed finite one-step updates, produced correctly shaped FP32 outputs, and reloaded the model state strictly on CPU:

| Shape | Loss | Pre-clip norm | First call | Steady median |
| --- | ---: | ---: | ---: | ---: |
| Full, 64 | 1.7837398 | 0.0856968 | 1,590.43 ms | 39.63 ms |
| Tail, 7 | 1.8289087 | 0.2210199 | 1,001.71 ms | 25.03 ms |

These timings are exploratory MPS facts, not accelerator thresholds. TF32 was unavailable because CUDA was absent. BF16 and FP16 autocast both failed the representative MPS LSTM because the autocast input dtype did not match the FP32 recurrent weights. Construction of a precision plugin was therefore not accepted as operation support. The mixed routes have no local same-weight delta, memory, or update claim.

For each admitted CUDA route, Issue 26 must record:

- capability and representative-operation gate result;
- forward output dtypes, loss dtype, gradient dtypes, optimizer-state dtypes, and checkpoint dtypes;
- finite loss, finite global norm, actual optimizer step, and any scaler skip;
- maximum and aggregate output/loss/gradient/one-step parameter deltas from strict FP32, with float64 reducers;
- synchronized CUDA cold-start and steady-state timing, plus peak allocated and reserved memory; and
- deterministic repeat hashes/results on the identical host and software stack.

Run strict FP32 first and clone its initial state into every candidate. Synchronize CUDA before and after timed regions. Validation uses model evaluation mode, framework-native inference context, the same route as training, and float64 complete-map reducers outside autocast. No separate validation precision is earned.

The prototype must report, not assume: GPU model, compute capability, VRAM, SM count, driver, runtime CUDA and cuDNN versions, native BF16/TF32 results, actual LSTM autocast and deterministic coverage, other workload/clock/power conditions, synchronized cold and steady timings, and peak memory. It must then ask whether either challenger earns its extra numerical concepts over strict FP32 and whether the selected host earns Lightning over direct PyTorch. These are the exact remaining questions. Their absence does not block this research decision; it prevents a fabricated host-performance conclusion.

## Rejected alternatives and cost

- `"medium"` matmul precision is rejected: it creates a third FP32-internal policy without a thesis need.
- True FP16/BF16 model conversion is rejected: it downcasts parameters and artifacts, adds optimizer/checkpoint portability burden, and is not autocast.
- FP64 training is rejected: float64 belongs in fitting/reducers, not the model comparison.
- FP16 beside native BF16 is rejected by default: BF16 preserves FP32's range and removes scaler, skip, and resume-state concepts.
- `torch.compile` is rejected for this LSTM: partial capture leaves the recurrence eager, cold and tail-shape costs are material, same-seed parity is unproved, and local Torch 2.11 MPS timing cannot stand in for locked Torch 2.7.1 CUDA evidence.
- Automatic capability fallback is rejected: it makes candidate identity depend silently on the host.
- A precision registry, compatibility alias, permanent benchmark harness, profiler framework, or dual manual/framework loop is rejected: direct framework settings and one bounded prototype answer the question.

Strict FP32 and TF32 cost one explicit matmul/cuDNN policy. BF16 adds one autocast precision setting and dtype verification. FP16 additionally adds scaler lifecycle, unscale-before-clip order, skipped-step evidence, and checkpoint state. That concept difference is material; it is why FP16 remains a conditional fallback.

Keep the implementation and tests equally small. Use direct PyTorch settings or one Lightning Trainer precision value; add no precision class, registry, alias, version marker, or compiler configuration. The selected host needs only focused full/tail tests for dtype, finiteness, one actual update, unscaled clipping where relevant, float64 complete-map reduction, and CPU FP32 artifact reload. CUDA timing, memory, and deterministic repeatability remain a bounded evidence artifact, not a permanent profiler or ordinary test. An undergraduate should be able to explain the storage/arithmetic distinction, why BF16 avoids scaling, why FP16 must unscale before clipping, why TF32 can still be deterministic, why reproducibility is host/version-bounded, and why portable weights remain FP32.
