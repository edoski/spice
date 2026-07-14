"""Disposable terminal driver for the Issue 63 command-surface model."""

from __future__ import annotations

import sys

from surface import COMMANDS, REMOVALS, SCENARIOS, State, View, audit, reduce

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


def _clear() -> None:
    if sys.stdout.isatty():
        print("\x1b[2J\x1b[H", end="")


def _render_scenario(state: State) -> None:
    scenario = SCENARIOS[state.scenario_index]
    print(f"{BOLD}Scenario{RESET}  {scenario.name}")
    print(f"{DIM}{scenario.question}{RESET}\n")
    for index, step in enumerate(scenario.steps):
        if index < state.completed_steps:
            status = "done"
        elif index == state.completed_steps:
            status = "next"
        else:
            status = "wait"
        print(f"{status:>4}  {step.invocation}")
        print(f"      {DIM}{step.observation}{RESET}")


def _render_tree() -> None:
    print(f"{BOLD}Candidate tree{RESET}  6 operator leaves + 2 Slurm leaves\n")
    for command in COMMANDS:
        print(f"{command.path:<20} {DIM}{command.audience:<12}{RESET} {command.owner}")


def _render_audit() -> None:
    missing, forbidden = audit()
    print(f"{BOLD}Coverage and deletion audit{RESET}\n")
    print("current Typer leaves        24")
    print("current helper leaves        4")
    print("candidate public leaves      6")
    print("candidate Slurm leaves       2")
    print(f"required owners missing      {len(missing)}")
    print(f"forbidden command words      {len(forbidden)}")
    print("local training commands      0")
    print("project serving wrappers     0")
    print(f"removed duplicate leaves     {len(REMOVALS)} classes")
    if missing:
        print(f"\nmissing: {', '.join(missing)}")
    if forbidden:
        print(f"\nforbidden: {', '.join(forbidden)}")


def _render(state: State) -> None:
    _clear()
    print(f"{BOLD}Issue 63 — minimum clean CLI prototype{RESET}")
    print(
        f"{DIM}Pure simulation. No owner function, RPC, Slurm, storage, "
        f"or server is called.{RESET}\n"
    )
    if state.view is View.SCENARIO:
        _render_scenario(state)
    elif state.view is View.TREE:
        _render_tree()
    else:
        _render_audit()
    print(
        f"\n{BOLD}[n]{RESET} next  {BOLD}[p]{RESET} previous  {BOLD}[x]{RESET} advance  "
        f"{BOLD}[r]{RESET} reset  {BOLD}[s]{RESET} scenario  {BOLD}[t]{RESET} tree  "
        f"{BOLD}[a]{RESET} audit  {BOLD}[q]{RESET} quit"
    )


def main() -> None:
    state = State()
    actions = {
        "n": "next",
        "p": "previous",
        "x": "advance",
        "r": "reset",
        "s": "scenario",
        "t": "tree",
        "a": "audit",
    }
    while True:
        _render(state)
        try:
            key = input("> ").strip().lower()[:1]
        except EOFError:
            return
        if key == "q":
            return
        state = reduce(state, actions.get(key, ""))


if __name__ == "__main__":
    main()
