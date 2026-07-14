"""Pure command-surface model for the disposable Issue 63 prototype."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum


@dataclass(frozen=True, slots=True)
class Command:
    path: str
    audience: str
    inputs: str
    owner: str
    necessity: str


COMMANDS = (
    Command(
        "submit",
        "operator",
        "REQUEST.json --root ROOT --remote REMOTE.yaml --commit SHA",
        "persist/load request -> revision -> submit",
        "Typed persistence, remote revision proof, quoted payload, and sbatch parsing are one act.",
    ),
    Command(
        "follow",
        "operator",
        "JOB_ID --remote REMOTE.yaml",
        "follow",
        (
            "Approved scheduler-state, log-tail, timeout, and Ctrl-C detach semantics "
            "are not one shell call."
        ),
    ),
    Command(
        "corpus acquire",
        "operator",
        "REQUEST.json --root ROOT --rpc-url URL",
        "acquire_corpus",
        (
            "Provider reads, bounded concurrency, resume validation, and ordered "
            "Parquet writes are domain work."
        ),
    ),
    Command(
        "corpus finalize",
        "operator",
        "CORPUS_ID --root ROOT --rpc-url URL",
        "finalize_corpus",
        "Schema, range, order, ancestry, and finality validation cannot be replaced by mv.",
    ),
    Command(
        "study run",
        "operator",
        (
            "TUNE_REQUEST.json METHOD.json --root ROOT --remote REMOTE.yaml "
            "--commit SHA"
        ),
        "persist/load TuneRequest -> validate Method -> submit candidate",
        "A candidate is private execution input, not a WorkflowRequest or ordinary submit call.",
    ),
    Command(
        "study finalize",
        "operator",
        "STUDY_ID --root ROOT",
        "publish_study",
        "Snapshot validation and immutable Study construction must precede direct rename.",
    ),
    Command(
        "remote workflow",
        "Slurm worker",
        "--root ROOT; WorkflowRequest JSON on stdin",
        "run_train_request | run_evaluate_request",
        "The batch script needs one same-wheel hydration/dispatch entry and no local trainer.",
    ),
    Command(
        "remote candidate",
        "Slurm worker",
        "--root ROOT; private candidate payload on stdin",
        "run_candidate",
        "Keeping candidate input distinct avoids a false generic execution-input union.",
    ),
)


@dataclass(frozen=True, slots=True)
class Removal:
    surface: str
    replacement: str


REMOVALS = (
    Removal(
        "request persist/load",
        "submit and study run persist/load internally; inspect JSON with cat/jq",
    ),
    Removal(
        "corpus/study/artifact/evaluation list",
        "find/ls; consumers validate exact known UUIDs",
    ),
    Removal(
        "corpus push and study/artifact/evaluation pull",
        "ordinary rsync into hidden sibling, then mv",
    ),
    Removal("typed listing JSON/errors", "ordinary shell output and native consumer validation"),
    Removal("shared JSON/output helpers", "numeric job ID, native logs, paths, and process status"),
    Removal(
        "custom error/exit adapter",
        "Typer usage handling plus native exceptions and exit status",
    ),
    Removal(
        "serve wrapper",
        "Uvicorn --factory launches the MacBook application directly",
    ),
)


@dataclass(frozen=True, slots=True)
class Step:
    invocation: str
    observation: str


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    question: str
    steps: tuple[Step, ...]


SCENARIOS = (
    Scenario(
        "Exact Train/Evaluate request",
        "Can one command persist and submit exact work without a plan or local trainer?",
        (
            Step(
                "$CLI submit train.json --root ROOT --remote remote.yaml --commit SHA",
                "persist, typed reload, revision check, one sbatch, numeric job ID",
            ),
            Step("$CLI follow 12345 --remote remote.yaml", "bounded remote follow"),
            Step("$CLI remote workflow --root REMOTE_ROOT", "Slurm-only owner execution"),
        ),
    ),
    Scenario(
        "Manual Tune candidate",
        "Can Tune stay private and manually serialized without request or scheduler subcommands?",
        (
            Step(
                (
                    "$CLI study run tune.json method.json --root ROOT "
                    "--remote remote.yaml --commit SHA"
                ),
                "persist TuneRequest, validate one Method, submit private payload",
            ),
            Step("$CLI remote candidate --root REMOTE_ROOT", "Slurm-only candidate fit"),
            Step("$CLI study finalize STUDY_UUID --root ROOT", "validated direct publication"),
        ),
    ),
    Scenario(
        "Corpus acquisition",
        "Which corpus actions contain domain logic that ordinary files cannot replace?",
        (
            Step(
                "$CLI corpus acquire corpus.json --root ROOT --rpc-url URL",
                "provider reads and validated resumable prefix",
            ),
            Step(
                "$CLI corpus finalize CORPUS_UUID --root ROOT --rpc-url URL",
                "domain/finality validation and direct publication",
            ),
        ),
    ),
    Scenario(
        "Ordinary operator acts",
        "Do discovery, inspection, and transfer need application commands?",
        (
            Step("find ROOT/artifacts -maxdepth 1 -type f", "ordinary enumeration"),
            Step("jq . ROOT/requests/train/UUID.json", "ordinary request inspection"),
            Step("rsync -a HOST:SOURCE ROOT/artifacts/.UUID.ckpt", "ordinary transfer"),
            Step(
                "mv ROOT/artifacts/.UUID.ckpt ROOT/artifacts/UUID.ckpt",
                "manual direct publication",
            ),
        ),
    ),
    Scenario(
        "MacBook serving",
        "Does serving need an application CLI wrapper around Uvicorn?",
        (
            Step(
                (
                    "STORAGE_ROOT=ROOT ETHEREUM_RPC_URL=URL POLYGON_RPC_URL=URL "
                    "AVALANCHE_RPC_URL=URL uv run uvicorn --factory "
                    "spice.serving:create_app --host 0.0.0.0 --port 8000"
                ),
                "mature CPU-only FastAPI/Uvicorn startup; no project wrapper",
            ),
            Step("POST / with {chain, K}", "head_block, selected_action_k, target_block"),
        ),
    ),
)


class View(Enum):
    SCENARIO = "scenario"
    TREE = "tree"
    AUDIT = "audit"


@dataclass(frozen=True, slots=True)
class State:
    scenario_index: int = 0
    completed_steps: int = 0
    view: View = View.SCENARIO


def reduce(state: State, action: str) -> State:
    if action == "next":
        return State((state.scenario_index + 1) % len(SCENARIOS))
    if action == "previous":
        return State((state.scenario_index - 1) % len(SCENARIOS))
    if action == "advance":
        count = len(SCENARIOS[state.scenario_index].steps)
        return replace(state, completed_steps=min(count, state.completed_steps + 1))
    if action == "reset":
        return replace(state, completed_steps=0)
    if action == "tree":
        return replace(state, view=View.TREE)
    if action == "audit":
        return replace(state, view=View.AUDIT)
    if action == "scenario":
        return replace(state, view=View.SCENARIO)
    return state


REQUIRED_CAPABILITIES = {
    "persist/load request",
    "revision",
    "submit",
    "follow",
    "acquire_corpus",
    "finalize_corpus",
    "run_candidate",
    "publish_study",
}
FORBIDDEN_PATH_WORDS = {
    "alias",
    "archive",
    "benchmark",
    "catalog",
    "compatibility",
    "convert",
    "delete",
    "dependency",
    "list",
    "load",
    "lock",
    "marker",
    "persist",
    "plan",
    "plugin",
    "pull",
    "push",
    "reconcile",
    "refresh",
    "restart",
}


def audit() -> tuple[tuple[str, ...], tuple[str, ...]]:
    owner_text = " ".join(command.owner for command in COMMANDS)
    missing = tuple(
        sorted(capability for capability in REQUIRED_CAPABILITIES if capability not in owner_text)
    )
    forbidden = tuple(
        sorted(
            word
            for word in FORBIDDEN_PATH_WORDS
            if any(word in command.path.split() for command in COMMANDS)
        )
    )
    return missing, forbidden
