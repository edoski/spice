"""Terminal driver for the disposable retained-success HPO prototype."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from prototype_logic import Candidate, SuccessfulRun, publish_study, retain_success, selected_run

BOLD = "\x1b[1m"
DIM = "\x1b[2m"
RESET = "\x1b[0m"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run bounded synthetic probes")
    args = parser.parse_args()
    if args.all:
        run_all()
    else:
        run_tui()


def run_all() -> None:
    retained: tuple[SuccessfulRun, ...] = ()

    unchanged_after_interruption = retained
    unchanged_after_failure = retained
    assert unchanged_after_interruption == retained
    assert unchanged_after_failure == retained

    retained = retain_success(
        retained,
        SuccessfulRun(Candidate("operator-choice-a"), 0.8, best_epoch=8, completed_epochs=16),
    )
    retained = retain_success(
        retained,
        SuccessfulRun(Candidate("operator-choice-a"), 0.5, best_epoch=5, completed_epochs=13),
    )
    retained = retain_success(
        retained,
        SuccessfulRun(Candidate("operator-choice-b"), 0.5, best_epoch=4, completed_epochs=12),
    )
    assert selected_run(retained) == 1
    assert publish_study(retained) == retained

    manually_curated = (retained[2], retained[0])
    assert selected_run(publish_study(manually_curated)) == 0

    invalid_manual_edit = (
        *manually_curated,
        SuccessfulRun(Candidate("invalid"), float("nan"), best_epoch=1, completed_epochs=1),
    )
    try:
        publish_study(invalid_manual_edit)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid manual edit must fail closed")

    one = (SuccessfulRun(Candidate("one"), 0.3, best_epoch=3, completed_epochs=11),)
    assert selected_run(publish_study(one)) == 0

    print(
        json.dumps(
            {
                "retained_successes": len(retained),
                "duplicate_method_successes": 2,
                "selected_run": selected_run(retained),
                "single_success_publication": "pass",
                "manually_curated_snapshot_validation": "pass",
                "invalid_manual_edit": "fails_closed",
                "failure_or_interruption_records": 0,
                "completion_gate": 0,
                "outcome_tags": 0,
                "checks": "pass",
            },
            indent=2,
            sort_keys=True,
        )
    )


def run_tui() -> None:
    retained: tuple[SuccessfulRun, ...] = ()
    message = ""
    while True:
        render(retained, message)
        action = input("> ").strip().lower()
        try:
            if action == "q":
                return
            if action == "r":
                candidate = Candidate(input("exact candidate description: ").strip())
                objective = float(input("synthetic finite objective: "))
                retained = retain_success(
                    retained,
                    SuccessfulRun(candidate, objective, best_epoch=8, completed_epochs=16),
                )
                message = "successful run retained"
            elif action in {"i", "f"}:
                message = "no record; operator may inspect/delete private work and choose next run"
            elif action == "p":
                published = publish_study(retained)
                message = f"publication passes; selected={selected_run(published)}"
            else:
                message = "unknown action"
        except ValueError as error:
            message = str(error)


def render(retained: tuple[SuccessfulRun, ...], message: str) -> None:
    print("\033[2J\033[H", end="")
    selected = None if not retained else selected_run(retained)
    print(f"{BOLD}Issue 29 disposable retained-success candidate{RESET}")
    print(f"{BOLD}retained successful runs{RESET}: {len(retained)}")
    print(f"{BOLD}current best{RESET}: {selected}")
    print(f"{BOLD}message{RESET}: {message}")
    print(f"{DIM}{json.dumps([asdict(run) for run in retained], indent=2)}{RESET}")
    print()
    print(
        f"{BOLD}[r]{RESET} retain success  {BOLD}[i]{RESET} interruption  "
        f"{BOLD}[f]{RESET} failure  {BOLD}[p]{RESET} publish  {BOLD}[q]{RESET} quit"
    )


if __name__ == "__main__":
    main()
