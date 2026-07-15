"""Terminal shell for the disposable Issue 56 placement prototype."""

from __future__ import annotations

import argparse
import json

from placement_logic import run_all


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run the bounded comparison")
    args = parser.parse_args()
    if args.all:
        print(json.dumps(run_all(), indent=2, sort_keys=True))
        return

    state: dict[str, object] = {
        "status": "ready",
        "question": "ordinary versus the authorized compact-source evidence candidate",
        "science": {
            "primary_context": 200,
            "context_grid": [50, 100, 200, 400],
            "primary_horizon": 5,
            "horizon_grid": [2, 3, 4, 5, 10, 15, 30, 50, 100, 200],
            "physical_batch": 64,
            "accumulation": 1,
        },
    }
    while True:
        print("\033[2J\033[H", end="")
        print("\033[1mIssue 56 disposable batch-placement prototype\033[0m")
        print("\033[2mSynthetic/fake local evidence only; no CUDA or thesis outcome.\033[0m")
        print(json.dumps(state, indent=2, sort_keys=True))
        print("\n\033[1m[a]\033[0m run comparison  \033[1m[q]\033[0m quit")
        action = input("> ").strip().lower()
        if action == "q":
            return
        if action == "a":
            state = run_all()
        else:
            state = {"status": "unknown action"}


if __name__ == "__main__":
    main()
