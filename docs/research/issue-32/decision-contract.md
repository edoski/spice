# Issue 32 — dependency, wheel, and package contract

Edo approved this complete planning contract on 2026-07-15. It consumes the
closed clean-break decisions named below and the binding two-host topology. It
authorizes no production, configuration, test, dependency, data, storage, job,
training, evaluation, acquisition, serving, mobile, archive, or cutover change.

## One distribution, two execution roles

Keep one `spice` Python distribution and one codebase.

- Train, operator-supplied Tune candidates, fitting validation, and every
  Evaluate request run only on the university Linux x86_64 L40 environment
  reached through SSH/Slurm.
- The physical Expo app talks only to the FastAPI application on Edo's
  MacBook. The MacBook alone performs serving inference from transferred final
  Lightning artifacts.
- Both roles share one checked-in universal `uv.lock`. Platform markers select
  the correct PyTorch build; there is no role lock, second package, duplicated
  dependency file, CUDA installation on the Mac, or environment abstraction.

The universal lock is ordinary dependency pinning. It is not an application
lock, provenance digest, or artifact identity. uv documents its project lock as
a portable cross-platform resolution
([resolution](https://docs.astral.sh/uv/concepts/resolution/)).

## Dependency ownership

The direct base dependency set is exactly:

```text
numpy
polars
torch
lightning
torchmetrics
pydantic
PyYAML
typer
web3
```

The only project extra is `serve`, containing `fastapi` and plain `uvicorn`.
The standardized `dev` dependency group contains only `pytest`, `ruff`,
`pyright`, and `vulture`. `hatchling` remains build-system-only.

Remove direct `optuna`, `optuna-integration`, `SQLAlchemy`, `Alembic`,
`scikit-learn`, `SciPy`, and `Matplotlib`. Do not directly declare `aiohttp` or
`eth-typing`: Web3 owns its HTTP transport dependency, while the clean serving
contract removes the typed transaction-receipt surface. No old research script
or suite earns a dependency or package resource.

There is no research extra, plugin surface, or dormant dependency for
reinforcement learning, Bayesian methods, calibration, conformal prediction,
uncertainty, future plotting, or hypothetical analysis. A later dependency
requires one concrete owner-approved consumer and evidence that a stock
framework facility or a tiny direct implementation is insufficient.

This set follows the approved deletions and surviving consumers in:

- [Prototype model construction and approved parameter application](https://github.com/edoski/spice/issues/17)
- [Classify research scripts and generated assets](https://github.com/edoski/spice/issues/20)
- [Prototype and choose the lean training host](https://github.com/edoski/spice/issues/26)
- [Prototype exact-root acquisition with one retry owner](https://github.com/edoski/spice/issues/27)
- [Choose the bounded HPO, trial-budget, and study-lifecycle policy](https://github.com/edoski/spice/issues/29)
- [Choose serving scope, durability, lifecycle, and artifact-chain policy](https://github.com/edoski/spice/issues/33)
- [Research the lean single-GPU batch-placement alternatives](https://github.com/edoski/spice/issues/55)
- [Simplify integrity, publication, and submission for one operator](https://github.com/edoski/spice/issues/78)

## Exact Python and framework matrix

Both hosts use `requires-python = ">=3.11,<3.12"`. Python patch versions may
differ. Pin the behavior-critical stack exactly:

```text
torch==2.7.1
lightning==2.6.5
torchmetrics==1.9.0
```

The university role resolves the official Linux x86_64 CUDA 11.8 PyTorch 2.7.1
build. The Mac role resolves the matching native macOS PyTorch 2.7.1 build and
the `serve` extra. Add neither `torchvision` nor `torchaudio`; no surviving
consumer needs them.

This is the newest aligned pair that respects the university's managed CUDA
11.8 environment: PyTorch publishes both macOS and CUDA 11.8 installation
routes for 2.7.1
([official previous versions](https://pytorch.org/get-started/previous-versions/)).
Newer CUDA branches are not a thesis-owned cluster upgrade. The current
different PyTorch versions across lock branches must therefore converge on
2.7.1 rather than remain silently divergent.

Materialize the university environment from locked base dependencies and the
Mac environment from locked base plus `serve`. Later implementation recreates
the currently broken remote virtual environment from the lock; it adds no
repair shim or compatibility package.

Artifact portability is a required observation: save the native weights-only
Lightning artifact on L40, transfer it through the approved owner workflow,
strict-load it on CPU with `map_location="cpu"`, then run Mac inference. Do not
invent a second artifact format, codebase, or dependency route.

## No vulnerability policy

SPICE has no vulnerability policy, gate, documented audit commands, audit
evidence, exception note, CI or scheduled bot, scanner, SBOM, SARIF, ignore
configuration, automatic failure/resurface machinery, runtime security
service, second scanner, or maintained security workflow.

The single operator may run native uv, npm, or ecosystem checks ad hoc and
react in the moment. That activity remains outside the application contract
and thesis evidence. Ordinary dependency resolution, builds, tests, and lock
materialization remain separately owned acceptance mechanics, not a security
policy.

## Code-only wheel

Build one pure-Python `py3-none-any` wheel for both roles. Native and CUDA
dependencies stay resolver-owned and are never vendored. `uv.lock` stays with
the source project and is not wheel content.

The Hatch wheel target selects only Python source:

```toml
[tool.hatch.build.targets.wheel]
include = ["src/spice/**/*.py"]
sources = ["src"]
```

Remove the current recursive `packages = ["src/spice"]` selection and the
global `src/spice/conf/**/*.yaml` inclusion. They currently produce a wheel
with 352 files: 219 Python files, 84 YAML files, and 45 package Markdown files.
The approved target contains only `spice/**/*.py` plus standard `dist-info`.

No bundled YAML survives. Historical benchmark definitions, evaluation
suites, and evaluator definitions leave the active tree under the approved
research classification. `REMOTE.yaml` and authored request/recipe documents
are explicit operator-supplied files. The twelve thesis request lists and the
twelve-artifact serving map are Python constructors or literals. PyYAML remains
only for external YAML parsing.

Ship no package Markdown, research, benchmarks, tests, thesis docs, mobile
source, lockfiles, checkpoints, artifacts, outputs, or data. Add no force
include, build hook, generated resource, or package template. Land this wheel
selection with the clean config implementation that deletes the current
relative package-YAML loader; do not break the existing implementation early.

The bounded thesis needs no source distribution or package-index publication.
The Git repository remains the source authority.

## Entry points and import behavior

Publish exactly one console entry point to `spice.cli.app:main`. The open
[system-name decision](https://github.com/edoski/spice/issues/59) owns its final
display spelling; it remains `spice` unless that decision changes it.

The entry point exposes the one plain Typer application approved by
[Prototype and choose the minimum clean CLI command surface](https://github.com/edoski/spice/issues/63):
six operator leaves plus two hidden Slurm-only worker leaves, with completion
disabled. Delete alternate module CLIs. Add no `python -m` duplicate, second
worker tree, serving command, plugin entry point, or research entry point.

Serving exports only `spice.serving:create_app`. Plain Uvicorn launches that
factory directly; SPICE adds no serving wrapper or module-global application.
FastAPI owns the application and Uvicorn owns the ASGI server process. The
official-role clarification and lay explanation are in
[uvicorn-role.md](uvicorn-role.md).

Keep static `[project].version = "0.1.0"` as the sole package version source.
Make `spice/__init__.py` inert: delete import-time `MPLCONFIGDIR` directory and
environment mutation, `__version__`, `__all__`, dynamic VCS versioning, and all
other import side effects. A real future version consumer may read
`importlib.metadata.version("spice")` at its boundary.

`apps/mobile` remains a separate private Expo/npm package. It contributes no
Python wheel files, build hook, entry point, or shared version machinery.

## Manual packaging observations

Packaging verification is operator work only when packaging or final
acceptance makes it relevant. The operator may directly:

1. run ordinary `uv build --wheel` and inspect the code-only wheel;
2. materialize a temporary locked Python 3.11 base environment, install the
   wheel without re-resolving its dependencies, and check installed import,
   metadata, and the single CLI help surface outside the checkout;
3. repeat with the Mac `serve` extra and resolve
   `spice.serving:create_app` through Uvicorn;
4. use the same wheel with the university base environment.

These are ephemeral observations, not application behavior. Add no permanent
verification code, smoke-test module, test case, script, CI job, build hook,
custom harness, or durable result.

## Implementation boundary

This contract chooses future package metadata, dependencies, lock resolution,
wheel contents, and public launch surfaces. It makes no such implementation in
this ticket. Later specification and implementation owners must consume it as
a clean break: no compatibility shim, legacy extra, parallel lock, hidden
fallback, defensive package machinery, or transition test.
